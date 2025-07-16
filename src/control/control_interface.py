"""

This module provides the main control interface that integrates PID temperature control,
safety monitoring, and thermal simulation into a unified control system for medical-grade
blood storage applications.

"""

from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import time
import warnings

from .pid_controller import PIDController, PIDGains, ControllerMode, create_blood_storage_controller
from .safety_monitor import SafetyMonitor, AlarmEvent, AlarmSeverity, create_blood_safety_monitor
from ..simulation.thermal_system import ThermalSystem, ActuatorLimits, ActuatorMode
from ..thermal_model.heat_transfer_data import BloodProperties, MaterialProperties


class ControlMode(Enum):
    """Overall control system operating modes"""
    STARTUP = "startup"           # System initialization
    AUTOMATIC = "automatic"       # Normal PID control with safety monitoring
    MANUAL = "manual"            # Manual power control (safety monitoring active)
    EMERGENCY = "emergency"       # Emergency mode (safety override active)
    MAINTENANCE = "maintenance"   # Maintenance mode (reduced safety monitoring)
    SHUTDOWN = "shutdown"         # System shutdown


@dataclass
class ControlConfiguration:
    """Configuration parameters for the control system"""
    # PID Controller settings
    pid_gains: PIDGains
    target_temperature: float
    
    # Safety monitoring settings
    enable_safety_monitoring: bool = True
    safety_callback_enabled: bool = True
    
    # Control loop timing
    control_update_interval: float = 10.0  # seconds
    safety_update_interval: float = 5.0    # seconds
    
    # Integration settings
    max_control_output_override: float = 50.0  # % - how much safety can override PID
    enable_emergency_override: bool = True
    
    # Logging and monitoring
    enable_performance_logging: bool = True
    log_history_length: int = 1000


class ControlInterface:
    """
    Main control interface that coordinates PID control, safety monitoring, and thermal simulation
    
    This class provides a unified interface for:
    - Temperature control using PID controller
    - Safety monitoring with automatic emergency responses
    - Integration with thermal simulation system
    - Performance monitoring and logging
    """
    
    def __init__(self, 
                 blood_product: BloodProperties,
                 container_material: MaterialProperties,
                 volume_liters: float,
                 container_mass_kg: float,
                 config: Optional[ControlConfiguration] = None,
                 actuator_limits: Optional[ActuatorLimits] = None):
        
        # Store system configuration
        self.blood_product = blood_product
        self.container_material = container_material
        self.volume_liters = volume_liters
        self.container_mass_kg = container_mass_kg
        
        # Use provided config or create default
        if config is None:
            config = ControlConfiguration(
                pid_gains=PIDGains(kp=1.0, ki=0.1, kd=0.05),
                target_temperature=blood_product.target_temp_c
            )
        self.config = config
        
        # Initialize core components
        self.thermal_system = ThermalSystem(
            blood_product=blood_product,
            container_material=container_material,
            volume_liters=volume_liters,
            container_mass_kg=container_mass_kg,
            actuator_limits=actuator_limits
        )
        
        self.pid_controller = PIDController(
            gains=config.pid_gains,
            setpoint=config.target_temperature,
            output_limits=(-actuator_limits.max_cooling_power if actuator_limits else -100.0,
                          actuator_limits.max_heating_power if actuator_limits else 50.0)
        )
        
        self.safety_monitor = create_blood_safety_monitor(blood_product)
        
        # Control system state
        self.control_mode = ControlMode.STARTUP
        self.system_enabled = True
        self.last_control_update = None
        self.last_safety_update = None
        
        # Performance tracking
        self.control_history = []
        self.safety_events = []
        self.performance_metrics = {}
        
        # Manual control state
        self.manual_power_command = 0.0
        
        # Emergency state tracking
        self.emergency_start_time = None
        self.emergency_reason = None
        
        # Callbacks for external notifications
        self.status_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.alarm_callbacks: List[Callable[[AlarmEvent], None]] = []
        
        # Setup safety monitor callback
        if config.safety_callback_enabled:
            self.safety_monitor.add_alarm_callback(self._handle_safety_alarm)
    
    def _handle_safety_alarm(self, alarm: AlarmEvent) -> None:
        """Internal handler for safety alarms"""
        # Log the alarm
        self.safety_events.append({
            'timestamp': alarm.timestamp,
            'alarm_id': alarm.alarm_id,
            'severity': alarm.severity.value,
            'message': alarm.message,
            'temperature': alarm.temperature
        })
        
        # Check if we need to enter emergency mode
        if alarm.severity in [AlarmSeverity.CRITICAL, AlarmSeverity.EMERGENCY]:
            if self.control_mode != ControlMode.EMERGENCY:
                self._enter_emergency_mode(f"Safety alarm: {alarm.alarm_id}")
        
        # Notify external callbacks
        for callback in self.alarm_callbacks:
            try:
                callback(alarm)
            except Exception as e:
                warnings.warn(f"Alarm callback failed: {e}")
    
    def _enter_emergency_mode(self, reason: str) -> None:
        """Enter emergency control mode"""
        self.control_mode = ControlMode.EMERGENCY
        self.emergency_start_time = datetime.now()
        self.emergency_reason = reason
        
        # Disable PID controller in emergency mode
        self.pid_controller.set_mode(ControllerMode.DISABLED)
        
        # Log emergency entry
        self.safety_events.append({
            'timestamp': datetime.now(),
            'alarm_id': 'EMERGENCY_MODE_ENTRY',
            'severity': 'emergency',
            'message': f"Entered emergency mode: {reason}",
            'temperature': self.get_current_temperature()
        })
    
    def _exit_emergency_mode(self) -> None:
        """Exit emergency mode and return to automatic control"""
        if self.control_mode == ControlMode.EMERGENCY:
            self.control_mode = ControlMode.AUTOMATIC
            self.pid_controller.set_mode(ControllerMode.AUTOMATIC)
            
            # Log emergency exit
            self.safety_events.append({
                'timestamp': datetime.now(),
                'alarm_id': 'EMERGENCY_MODE_EXIT',
                'severity': 'info',
                'message': "Exited emergency mode - returning to automatic control",
                'temperature': self.get_current_temperature()
            })
            
            self.emergency_start_time = None
            self.emergency_reason = None
    
    def start_system(self, initial_temperature: Optional[float] = None) -> Dict[str, Any]:
        """
        Start the control system
        
        Args:
            initial_temperature: Optional initial temperature (defaults to ambient)
        
        Returns:
            System startup status
        """
        # Reset thermal system
        if initial_temperature is not None:
            self.thermal_system.reset(initial_temperature)
        else:
            self.thermal_system.reset()
        
        # Reset controllers
        self.pid_controller.reset()
        self.pid_controller.set_mode(ControllerMode.AUTOMATIC)
        
        # Enable safety monitoring
        self.safety_monitor.enable_system()
        
        # Set system state
        self.system_enabled = True
        self.control_mode = ControlMode.AUTOMATIC
        
        # Initialize timing
        self.last_control_update = time.time()
        self.last_safety_update = time.time()
        
        # Clear history
        self.control_history.clear()
        self.safety_events.clear()
        
        return {
            'status': 'started',
            'control_mode': self.control_mode.value,
            'initial_temperature': self.get_current_temperature(),
            'target_temperature': self.config.target_temperature,
            'system_enabled': self.system_enabled
        }
    
    def stop_system(self) -> Dict[str, Any]:
        """
        Stop the control system safely
        
        Returns:
            System shutdown status
        """
        # Set shutdown mode
        self.control_mode = ControlMode.SHUTDOWN
        
        # Turn off heating/cooling
        self.thermal_system.apply_thermal_power(0.0)
        
        # Disable PID controller
        self.pid_controller.set_mode(ControllerMode.DISABLED)
        
        # Disable system
        self.system_enabled = False
        
        return {
            'status': 'stopped',
            'final_temperature': self.get_current_temperature(),
            'total_runtime': time.time() - (self.last_control_update or time.time()),
            'safety_events': len(self.safety_events)
        }
    
    def update(self, dt: Optional[float] = None) -> Dict[str, Any]:
        """
        Main control loop update - call this regularly (e.g., every 5-10 seconds)
        
        Args:
            dt: Time step for simulation (seconds). If None, uses real time.
        
        Returns:
            Complete system status
        """
        if not self.system_enabled:
            return self.get_status()
        
        current_time = time.time()
        
        # Calculate time steps
        if dt is None:
            if self.last_control_update:
                control_dt = current_time - self.last_control_update
            else:
                control_dt = self.config.control_update_interval
            
            if self.last_safety_update:
                safety_dt = current_time - self.last_safety_update
            else:
                safety_dt = self.config.safety_update_interval
        else:
            control_dt = dt
            safety_dt = dt
        
        # Update safety monitoring first (always active)
        current_temp = self.get_current_temperature()
        safety_status = self.safety_monitor.update_temperature(current_temp)
        self.last_safety_update = current_time
        
        # Determine control action based on mode
        thermal_power = 0.0
        
        if self.control_mode == ControlMode.AUTOMATIC:
            # Normal PID control
            thermal_power = self._update_automatic_control(control_dt)
            
        elif self.control_mode == ControlMode.MANUAL:
            # Manual power control (safety monitoring still active)
            thermal_power = self.manual_power_command
            
        elif self.control_mode == ControlMode.EMERGENCY:
            # Emergency safety override
            thermal_power = self._update_emergency_control()
            
        elif self.control_mode == ControlMode.MAINTENANCE:
            # Maintenance mode - minimal control
            thermal_power = 0.0
        
        # Apply safety overrides if needed
        safety_override = safety_status.get('safety_override_power')
        if safety_override is not None and self.config.enable_emergency_override:
            # Safety system can override control output
            override_strength = min(self.config.max_control_output_override / 100.0, 1.0)
            thermal_power = thermal_power * (1 - override_strength) + safety_override * override_strength
        
        # Apply power to thermal system
        actual_power = self.thermal_system.apply_thermal_power(thermal_power)
        
        # Advance thermal simulation
        new_state = self.thermal_system.step(control_dt)
        
        # Update timing
        self.last_control_update = current_time
        
        # Log performance data
        if self.config.enable_performance_logging:
            self._log_performance_data(thermal_power, actual_power, safety_status)
        
        # Check if we can exit emergency mode
        if (self.control_mode == ControlMode.EMERGENCY and 
            safety_status['safety_level'] == 'SAFE' and 
            len(self.safety_monitor.active_alarms) == 0):
            self._exit_emergency_mode()
        
        # Notify status callbacks
        status = self.get_status()
        for callback in self.status_callbacks:
            try:
                callback(status)
            except Exception as e:
                warnings.warn(f"Status callback failed: {e}")
        
        return status
    
    def _update_automatic_control(self, dt: float) -> float:
        """Update PID controller in automatic mode"""
        current_temp = self.get_current_temperature()
        thermal_power = self.pid_controller.update(current_temp, dt)
        return thermal_power
    
    def _update_emergency_control(self) -> float:
        """Update control in emergency mode (safety override)"""
        # Let safety monitor determine emergency power
        safety_override = self.safety_monitor.get_safety_override_power()
        return safety_override if safety_override is not None else 0.0
    
    def _log_performance_data(self, commanded_power: float, actual_power: float, 
                             safety_status: Dict[str, Any]) -> None:
        """Log performance data for analysis"""
        data = {
            'timestamp': datetime.now(),
            'temperature': self.get_current_temperature(),
            'target_temperature': self.config.target_temperature,
            'commanded_power': commanded_power,
            'actual_power': actual_power,
            'control_mode': self.control_mode.value,
            'safety_level': safety_status['safety_level'],
            'active_alarms': safety_status['active_alarms'],
            'pid_error': self.pid_controller.last_error,
            'pid_output': self.pid_controller.last_output
        }
        
        self.control_history.append(data)
        
        # Limit history size
        if len(self.control_history) > self.config.log_history_length:
            self.control_history.pop(0)
    
    # Public API methods
    
    def get_current_temperature(self) -> float:
        """Get current temperature measurement"""
        return self.thermal_system.get_current_temperature()
    
    def set_target_temperature(self, target_temp: float) -> bool:
        """
        Set new target temperature
        
        Args:
            target_temp: New target temperature (°C)
        
        Returns:
            True if successful, False if invalid
        """
        # Validate temperature is reasonable for blood product
        if (target_temp < self.blood_product.critical_temp_low_c - 5.0 or 
            target_temp > self.blood_product.critical_temp_high_c + 5.0):
            return False
        
        self.config.target_temperature = target_temp
        self.pid_controller.set_setpoint(target_temp)
        return True
    
    def set_control_mode(self, mode: ControlMode) -> bool:
        """
        Set control system operating mode
        
        Args:
            mode: New control mode
        
        Returns:
            True if mode change successful
        """
        if mode == ControlMode.EMERGENCY:
            # Cannot manually enter emergency mode
            return False
        
        if self.control_mode == ControlMode.EMERGENCY and mode != ControlMode.AUTOMATIC:
            # Can only exit emergency mode to automatic
            return False
        
        # Update control mode
        previous_mode = self.control_mode
        self.control_mode = mode
        
        # Update PID controller mode
        if mode == ControlMode.AUTOMATIC:
            self.pid_controller.set_mode(ControllerMode.AUTOMATIC)
        elif mode == ControlMode.MANUAL:
            self.pid_controller.set_mode(ControllerMode.MANUAL)
        elif mode in [ControlMode.MAINTENANCE, ControlMode.SHUTDOWN]:
            self.pid_controller.set_mode(ControllerMode.DISABLED)
        
        # Log mode change
        self.safety_events.append({
            'timestamp': datetime.now(),
            'alarm_id': 'MODE_CHANGE',
            'severity': 'info',
            'message': f"Control mode changed from {previous_mode.value} to {mode.value}",
            'temperature': self.get_current_temperature()
        })
        
        return True
    
    def set_manual_power(self, power_watts: float) -> bool:
        """
        Set manual power output (only active in manual mode)
        
        Args:
            power_watts: Manual power command (W)
        
        Returns:
            True if successful
        """
        # Apply actuator limits
        actuator_limits = self.thermal_system.actuator_limits
        max_power = actuator_limits.max_heating_power
        min_power = -actuator_limits.max_cooling_power
        
        self.manual_power_command = max(min_power, min(max_power, power_watts))
        return True
    
    def acknowledge_alarm(self, alarm_id: str) -> bool:
        """Acknowledge a specific alarm"""
        return self.safety_monitor.acknowledge_alarm(alarm_id)
    
    def acknowledge_all_alarms(self) -> int:
        """Acknowledge all active alarms"""
        return self.safety_monitor.acknowledge_all_alarms()
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        current_temp = self.get_current_temperature()
        pid_status = self.pid_controller.get_status()
        safety_status = self.safety_monitor._get_safety_status()
        actuator_status = self.thermal_system.get_actuator_status()
        
        # Calculate performance metrics
        performance = self._calculate_performance_metrics()
        
        return {
            # Overall system status
            'system_enabled': self.system_enabled,
            'control_mode': self.control_mode.value,
            'current_temperature_c': current_temp,
            'target_temperature_c': self.config.target_temperature,
            
            # Control system status
            'pid_controller': pid_status,
            'actuator': actuator_status,
            'manual_power_command_w': self.manual_power_command,
            
            # Safety system status
            'safety': safety_status,
            'emergency_mode': self.control_mode == ControlMode.EMERGENCY,
            'emergency_reason': self.emergency_reason,
            'emergency_duration_s': (
                (datetime.now() - self.emergency_start_time).total_seconds() 
                if self.emergency_start_time else None
            ),
            
            # Performance metrics
            'performance': performance,
            
            # System timing
            'last_update': datetime.now().isoformat(),
            'control_update_interval_s': self.config.control_update_interval,
            'safety_update_interval_s': self.config.safety_update_interval
        }
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate system performance metrics"""
        if not self.control_history:
            return {}
        
        # Recent temperature data (last 10 readings)
        recent_data = self.control_history[-10:]
        temps = [d['temperature'] for d in recent_data]
        target = self.config.target_temperature
        
        # Temperature stability metrics
        if len(temps) > 1:
            temp_std = (sum((t - sum(temps)/len(temps))**2 for t in temps) / len(temps))**0.5
            avg_error = sum(abs(t - target) for t in temps) / len(temps)
            max_error = max(abs(t - target) for t in temps)
        else:
            temp_std = 0.0
            avg_error = abs(temps[0] - target) if temps else 0.0
            max_error = avg_error
        
        # Control performance
        recent_powers = [d['actual_power'] for d in recent_data]
        avg_power = sum(abs(p) for p in recent_powers) / len(recent_powers) if recent_powers else 0.0
        
        # Safety metrics
        total_alarms = len(self.safety_events)
        critical_alarms = len([e for e in self.safety_events if e['severity'] in ['critical', 'emergency']])
        
        return {
            'temperature_stability_c': temp_std,
            'average_error_c': avg_error,
            'maximum_error_c': max_error,
            'average_power_usage_w': avg_power,
            'total_alarms': total_alarms,
            'critical_alarms': critical_alarms,
            'control_data_points': len(self.control_history),
            'uptime_hours': (
                (time.time() - self.last_control_update) / 3600.0 
                if self.last_control_update else 0.0
            )
        }
    
    def get_alarm_summary(self) -> Dict[str, Any]:
        """Get alarm system summary"""
        return self.safety_monitor.get_alarm_summary()
    
    def get_control_history(self, num_points: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get control system history
        
        Args:
            num_points: Number of recent points to return (None for all)
        
        Returns:
            List of historical control data points
        """
        if num_points is None:
            return list(self.control_history)
        else:
            return list(self.control_history[-num_points:])
    
    def add_status_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add callback for status updates"""
        self.status_callbacks.append(callback)
    
    def add_alarm_callback(self, callback: Callable[[AlarmEvent], None]) -> None:
        """Add callback for alarm notifications"""
        self.alarm_callbacks.append(callback)
    
    def export_log_data(self, start_time: Optional[datetime] = None, 
                       end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Export comprehensive log data for analysis
        
        Args:
            start_time: Start time for data export (None for all)
            end_time: End time for data export (None for all)
        
        Returns:
            Complete log data including control history, alarms, and performance
        """
        # Filter control history by time if specified
        control_data = self.control_history
        if start_time or end_time:
            control_data = [
                d for d in control_data
                if (start_time is None or d['timestamp'] >= start_time) and
                   (end_time is None or d['timestamp'] <= end_time)
            ]
        
        # Export alarm data
        alarm_data = self.safety_monitor.export_alarm_log(start_time, end_time)
        
        return {
            'system_info': {
                'blood_product': self.blood_product.name,
                'target_temperature_c': self.config.target_temperature,
                'volume_liters': self.volume_liters,
                'container_material': self.container_material.name
            },
            'control_history': control_data,
            'alarm_history': alarm_data,
            'safety_events': self.safety_events,
            'performance_summary': self._calculate_performance_metrics(),
            'export_timestamp': datetime.now().isoformat(),
            'total_data_points': len(control_data)
        }


# Convenience functions for common blood storage applications

def create_blood_storage_control_system(
    blood_product: BloodProperties,
    container_material: MaterialProperties,
    volume_liters: float,
    container_mass_kg: float,
    target_temperature: Optional[float] = None
) -> ControlInterface:
    """
    Create a control system optimized for blood storage
    
    Args:
        blood_product: Blood product properties
        container_material: Container material properties
        volume_liters: Storage volume
        container_mass_kg: Container mass
        target_temperature: Target temperature (defaults to blood product target)
    
    Returns:
        Configured control interface
    """
    target_temp = target_temperature or blood_product.target_temp_c
    
    config = ControlConfiguration(
        pid_gains=PIDGains(kp=1.0, ki=0.1, kd=0.05),  # Conservative for medical use
        target_temperature=target_temp,
        control_update_interval=10.0,  # 10 second control updates
        safety_update_interval=5.0,    # 5 second safety checks
        enable_emergency_override=True
    )
    
    actuator_limits = ActuatorLimits(
        max_heating_power=50.0,    # Conservative heating
        max_cooling_power=100.0,   # More aggressive cooling
        min_power_increment=1.0,
        response_time=30.0
    )
    
    return ControlInterface(
        blood_product=blood_product,
        container_material=container_material,
        volume_liters=volume_liters,
        container_mass_kg=container_mass_kg,
        config=config,
        actuator_limits=actuator_limits
    )


def create_plasma_control_system(
    blood_product: BloodProperties,
    container_material: MaterialProperties,
    volume_liters: float,
    container_mass_kg: float
) -> ControlInterface:
    """
    Create a control system optimized for plasma freezing
    
    Returns:
        Configured control interface for plasma applications
    """
    config = ControlConfiguration(
        pid_gains=PIDGains(kp=2.0, ki=0.2, kd=0.1),  # More aggressive for freezing
        target_temperature=-18.0,  # Standard plasma freezing temperature
        control_update_interval=5.0,   # Faster updates for freezing
        safety_update_interval=3.0,    # More frequent safety checks
        enable_emergency_override=True
    )
    
    actuator_limits = ActuatorLimits(
        max_heating_power=100.0,   # Higher power for temperature changes
        max_cooling_power=200.0,   # High cooling power for freezing
        min_power_increment=2.0,
        response_time=20.0         # Faster response for freezing
    )
    
    return ControlInterface(
        blood_product=blood_product,
        container_material=container_material,
        volume_liters=volume_liters,
        container_mass_kg=container_mass_kg,
        config=config,
        actuator_limits=actuator_limits
    )