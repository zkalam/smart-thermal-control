"""
Safety monitoring system for blood storage thermal control.

Provides automated safety checking, alarm management, and fail-safe operations
with medical-grade accuracy and FDA compliance considerations.
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import time
import warnings

from ..thermal_model.heat_transfer_data import BloodProperties
from ..thermal_model.heat_transfer import validate_blood_temperature


class AlarmSeverity(Enum):
    """Alarm severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlarmState(Enum):
    """Alarm state management"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    CLEARED = "cleared"


@dataclass
class SafetyLimits:
    """Safety limit parameters for temperature monitoring"""
    # Temperature limits (°C)
    critical_temp_high: float
    critical_temp_low: float
    warning_temp_high: float
    warning_temp_low: float
    
    # Rate limits (°C/min)
    max_heating_rate: float = 2.0
    max_cooling_rate: float = 5.0
    
    # Time limits (seconds)
    max_time_outside_warning: float = 300.0  # 5 minutes
    max_time_outside_critical: float = 60.0   # 1 minute
    
    # Power limits (W)
    max_emergency_power: float = 200.0
    
    def __post_init__(self):
        """Validate safety limit parameters"""
        if self.critical_temp_low >= self.critical_temp_high:
            raise ValueError("Critical low temperature must be less than critical high")
        
        if self.warning_temp_low >= self.warning_temp_high:
            raise ValueError("Warning low temperature must be less than warning high")
        
        if not (self.critical_temp_low <= self.warning_temp_low <= 
                self.warning_temp_high <= self.critical_temp_high):
            raise ValueError("Safety limits must be properly ordered: critical_low ≤ warning_low ≤ warning_high ≤ critical_high")


@dataclass
class AlarmEvent:
    """Individual alarm event record"""
    alarm_id: str
    severity: AlarmSeverity
    message: str
    timestamp: datetime
    temperature: float
    state: AlarmState = AlarmState.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_time: Optional[datetime] = None
    cleared_time: Optional[datetime] = None
    
    def acknowledge(self, user: str = "system") -> None:
        """Acknowledge the alarm"""
        if self.state == AlarmState.ACTIVE:
            self.state = AlarmState.ACKNOWLEDGED
            self.acknowledged_by = user
            self.acknowledged_time = datetime.now()
    
    def clear(self) -> None:
        """Clear the alarm"""
        self.state = AlarmState.CLEARED
        self.cleared_time = datetime.now()
    
    def get_duration(self) -> float:
        """Get alarm duration in seconds"""
        end_time = self.cleared_time or datetime.now()
        return (end_time - self.timestamp).total_seconds()


class SafetyMonitor:
    """
    Comprehensive safety monitoring system for blood storage
    
    Provides real-time temperature monitoring, alarm management,
    and automatic safety responses.
    """
    
    def __init__(self, blood_product: BloodProperties, safety_limits: Optional[SafetyLimits] = None):
        self.blood_product = blood_product
        
        # Use provided limits or create from blood product properties
        if safety_limits is None:
            self.safety_limits = self._create_default_limits(blood_product)
        else:
            self.safety_limits = safety_limits
        
        # Monitoring state
        self.current_temperature = None
        self.last_temperature = None
        self.last_update_time = None
        self.temperature_history = []
        
        # Alarm management
        self.active_alarms: Dict[str, AlarmEvent] = {}
        self.alarm_history: List[AlarmEvent] = []
        self.alarm_callbacks: List[Callable[[AlarmEvent], None]] = []
        
        # Safety status tracking
        self.time_outside_warning = 0.0
        self.time_outside_critical = 0.0
        self.emergency_mode = False
        self.system_enabled = True
        
        # Performance metrics
        self.total_alarms = 0
        self.critical_alarms = 0
        self.false_alarms = 0
    
    def _create_default_limits(self, blood_product: BloodProperties) -> SafetyLimits:
        """Create default safety limits based on blood product properties"""
        # Use blood product critical limits as base
        critical_high = blood_product.critical_temp_high_c
        critical_low = blood_product.critical_temp_low_c
        
        # Create warning limits with 1°C buffer from critical
        warning_high = critical_high - 1.0
        warning_low = critical_low + 1.0
        
        return SafetyLimits(
            critical_temp_high=critical_high,
            critical_temp_low=critical_low,
            warning_temp_high=warning_high,
            warning_temp_low=warning_low
        )
    
    def update_temperature(self, temperature: float, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Update current temperature and perform safety checks
        
        Args:
            temperature: Current temperature (°C)
            timestamp: Optional timestamp (defaults to current time)
            
        Returns:
            Safety status dictionary
        """
        if not self.system_enabled:
            return self._get_safety_status()
        
        # Update temperature state
        self.last_temperature = self.current_temperature
        self.current_temperature = temperature
        current_time = timestamp or datetime.now()
        
        # Calculate time delta
        if self.last_update_time is not None:
            dt = (current_time - self.last_update_time).total_seconds()
        else:
            dt = 0.0
        
        self.last_update_time = current_time
        
        # Store temperature history (limit to last 100 readings)
        self.temperature_history.append((current_time, temperature))
        if len(self.temperature_history) > 100:
            self.temperature_history.pop(0)
        
        # Perform all safety checks
        self._check_temperature_limits(temperature, current_time)
        self._check_rate_of_change(temperature, dt, current_time)
        self._check_time_limits(temperature, dt, current_time)
        self._update_emergency_mode(current_time)
        
        return self._get_safety_status()
    
    def _check_temperature_limits(self, temperature: float, timestamp: datetime) -> None:
        """Check temperature against safety limits"""
        # Critical temperature violations
        if temperature > self.safety_limits.critical_temp_high:
            self._raise_alarm(
                "TEMP_CRITICAL_HIGH",
                AlarmSeverity.CRITICAL,
                f"Temperature {temperature:.1f}°C exceeds critical high limit {self.safety_limits.critical_temp_high:.1f}°C",
                temperature,
                timestamp
            )
        elif temperature < self.safety_limits.critical_temp_low:
            self._raise_alarm(
                "TEMP_CRITICAL_LOW",
                AlarmSeverity.CRITICAL,
                f"Temperature {temperature:.1f}°C below critical low limit {self.safety_limits.critical_temp_low:.1f}°C",
                temperature,
                timestamp
            )
        else:
            # Clear critical alarms if temperature is back in range
            self._clear_alarm("TEMP_CRITICAL_HIGH")
            self._clear_alarm("TEMP_CRITICAL_LOW")
        
        # Warning temperature violations
        if temperature > self.safety_limits.warning_temp_high:
            self._raise_alarm(
                "TEMP_WARNING_HIGH",
                AlarmSeverity.WARNING,
                f"Temperature {temperature:.1f}°C exceeds warning high limit {self.safety_limits.warning_temp_high:.1f}°C",
                temperature,
                timestamp
            )
        elif temperature < self.safety_limits.warning_temp_low:
            self._raise_alarm(
                "TEMP_WARNING_LOW",
                AlarmSeverity.WARNING,
                f"Temperature {temperature:.1f}°C below warning low limit {self.safety_limits.warning_temp_low:.1f}°C",
                temperature,
                timestamp
            )
        else:
            # Clear warning alarms if temperature is back in range
            self._clear_alarm("TEMP_WARNING_HIGH")
            self._clear_alarm("TEMP_WARNING_LOW")
    
    def _check_rate_of_change(self, temperature: float, dt: float, timestamp: datetime) -> None:
        """Check temperature rate of change limits"""
        if self.last_temperature is None or dt <= 0:
            return
        
        # Calculate rate in °C/min
        rate_per_second = (temperature - self.last_temperature) / dt
        rate_per_minute = rate_per_second * 60.0
        
        # Check heating rate
        if rate_per_minute > self.safety_limits.max_heating_rate:
            self._raise_alarm(
                "RATE_HEATING_HIGH",
                AlarmSeverity.WARNING,
                f"Heating rate {rate_per_minute:.1f}°C/min exceeds limit {self.safety_limits.max_heating_rate:.1f}°C/min",
                temperature,
                timestamp
            )
        else:
            self._clear_alarm("RATE_HEATING_HIGH")
        
        # Check cooling rate
        if rate_per_minute < -self.safety_limits.max_cooling_rate:
            self._raise_alarm(
                "RATE_COOLING_HIGH",
                AlarmSeverity.WARNING,
                f"Cooling rate {abs(rate_per_minute):.1f}°C/min exceeds limit {self.safety_limits.max_cooling_rate:.1f}°C/min",
                temperature,
                timestamp
            )
        else:
            self._clear_alarm("RATE_COOLING_HIGH")
    
    def _check_time_limits(self, temperature: float, dt: float, timestamp: datetime) -> None:
        """Check time spent outside safe ranges"""
        # Check if outside warning range
        outside_warning = (temperature < self.safety_limits.warning_temp_low or 
                          temperature > self.safety_limits.warning_temp_high)
        
        # Check if outside critical range
        outside_critical = (temperature < self.safety_limits.critical_temp_low or 
                           temperature > self.safety_limits.critical_temp_high)
        
        # Update time counters
        if outside_warning:
            self.time_outside_warning += dt
        else:
            self.time_outside_warning = 0.0
        
        if outside_critical:
            self.time_outside_critical += dt
        else:
            self.time_outside_critical = 0.0
        
        # Check time limits
        if self.time_outside_critical > self.safety_limits.max_time_outside_critical:
            self._raise_alarm(
                "TIME_CRITICAL_EXCEEDED",
                AlarmSeverity.EMERGENCY,
                f"Temperature outside critical range for {self.time_outside_critical:.0f}s (limit: {self.safety_limits.max_time_outside_critical:.0f}s)",
                temperature,
                timestamp
            )
        
        if self.time_outside_warning > self.safety_limits.max_time_outside_warning:
            self._raise_alarm(
                "TIME_WARNING_EXCEEDED",
                AlarmSeverity.CRITICAL,
                f"Temperature outside warning range for {self.time_outside_warning:.0f}s (limit: {self.safety_limits.max_time_outside_warning:.0f}s)",
                temperature,
                timestamp
            )
    
    def _update_emergency_mode(self, timestamp: datetime) -> None:
        """Update emergency mode status"""
        # Enter emergency mode if critical conditions exist
        critical_alarms = [alarm for alarm in self.active_alarms.values() 
                          if alarm.severity in [AlarmSeverity.CRITICAL, AlarmSeverity.EMERGENCY]]
        
        if critical_alarms and not self.emergency_mode:
            self.emergency_mode = True
            self._raise_alarm(
                "EMERGENCY_MODE",
                AlarmSeverity.EMERGENCY,
                "System entered emergency mode due to critical safety violations",
                self.current_temperature or 0.0,
                timestamp
            )
        elif not critical_alarms and self.emergency_mode:
            self.emergency_mode = False
            self._clear_alarm("EMERGENCY_MODE")
    
    def _raise_alarm(self, alarm_id: str, severity: AlarmSeverity, message: str, 
                    temperature: float, timestamp: datetime) -> None:
        """Raise a new alarm or update existing alarm"""
        if alarm_id not in self.active_alarms:
            # Create new alarm
            alarm = AlarmEvent(
                alarm_id=alarm_id,
                severity=severity,
                message=message,
                timestamp=timestamp,
                temperature=temperature
            )
            
            self.active_alarms[alarm_id] = alarm
            self.alarm_history.append(alarm)
            self.total_alarms += 1
            
            if severity in [AlarmSeverity.CRITICAL, AlarmSeverity.EMERGENCY]:
                self.critical_alarms += 1
            
            # Notify callbacks
            for callback in self.alarm_callbacks:
                try:
                    callback(alarm)
                except Exception as e:
                    warnings.warn(f"Alarm callback failed: {e}")
    
    def _clear_alarm(self, alarm_id: str) -> None:
        """Clear an active alarm"""
        if alarm_id in self.active_alarms:
            alarm = self.active_alarms[alarm_id]
            alarm.clear()
            del self.active_alarms[alarm_id]
    
    def acknowledge_alarm(self, alarm_id: str, user: str = "operator") -> bool:
        """Acknowledge an active alarm"""
        if alarm_id in self.active_alarms:
            self.active_alarms[alarm_id].acknowledge(user)
            return True
        return False
    
    def acknowledge_all_alarms(self, user: str = "operator") -> int:
        """Acknowledge all active alarms"""
        count = 0
        for alarm in self.active_alarms.values():
            if alarm.state == AlarmState.ACTIVE:
                alarm.acknowledge(user)
                count += 1
        return count
    
    def add_alarm_callback(self, callback: Callable[[AlarmEvent], None]) -> None:
        """Add callback function for alarm notifications"""
        self.alarm_callbacks.append(callback)
    
    def remove_alarm_callback(self, callback: Callable[[AlarmEvent], None]) -> None:
        """Remove alarm callback function"""
        if callback in self.alarm_callbacks:
            self.alarm_callbacks.remove(callback)
    
    def get_safety_override_power(self) -> Optional[float]:
        """
        Get emergency power override for safety protection
        
        Returns:
            Emergency power setting (W) or None if no override needed
        """
        if not self.emergency_mode or self.current_temperature is None:
            return None
        
        # Emergency cooling if too hot
        if self.current_temperature > self.safety_limits.critical_temp_high:
            return -self.safety_limits.max_emergency_power
        
        # Emergency heating if too cold
        if self.current_temperature < self.safety_limits.critical_temp_low:
            return self.safety_limits.max_emergency_power
        
        return None
    
    def _get_safety_status(self) -> Dict[str, Any]:
        """Get comprehensive safety status"""
        # Determine overall safety level
        if self.emergency_mode:
            safety_level = "EMERGENCY"
        elif any(alarm.severity == AlarmSeverity.CRITICAL for alarm in self.active_alarms.values()):
            safety_level = "CRITICAL"
        elif any(alarm.severity == AlarmSeverity.WARNING for alarm in self.active_alarms.values()):
            safety_level = "WARNING"
        else:
            safety_level = "SAFE"
        
        # Get blood product validation
        blood_status = {}
        if self.current_temperature is not None:
            blood_status = validate_blood_temperature(self.blood_product, self.current_temperature)
        
        return {
            'safety_level': safety_level,
            'emergency_mode': self.emergency_mode,
            'system_enabled': self.system_enabled,
            'current_temperature': self.current_temperature,
            'active_alarms': len(self.active_alarms),
            'critical_alarms': len([a for a in self.active_alarms.values() 
                                   if a.severity in [AlarmSeverity.CRITICAL, AlarmSeverity.EMERGENCY]]),
            'time_outside_warning': self.time_outside_warning,
            'time_outside_critical': self.time_outside_critical,
            'blood_product_status': blood_status,
            'safety_override_power': self.get_safety_override_power(),
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None
        }
    
    def get_alarm_summary(self) -> Dict[str, Any]:
        """Get alarm system summary"""
        active_by_severity = {}
        for severity in AlarmSeverity:
            active_by_severity[severity.value] = len([
                a for a in self.active_alarms.values() if a.severity == severity
            ])
        
        return {
            'total_active_alarms': len(self.active_alarms),
            'active_by_severity': active_by_severity,
            'total_historical_alarms': self.total_alarms,
            'critical_alarms_total': self.critical_alarms,
            'false_alarms': self.false_alarms,
            'active_alarm_details': [
                {
                    'id': alarm.alarm_id,
                    'severity': alarm.severity.value,
                    'message': alarm.message,
                    'duration': alarm.get_duration(),
                    'acknowledged': alarm.state == AlarmState.ACKNOWLEDGED
                }
                for alarm in self.active_alarms.values()
            ]
        }
    
    def enable_system(self) -> None:
        """Enable safety monitoring system"""
        self.system_enabled = True
    
    def disable_system(self) -> None:
        """Disable safety monitoring system (use with extreme caution)"""
        self.system_enabled = False
        warnings.warn("Safety monitoring system disabled - use extreme caution!")
    
    def reset_monitoring(self) -> None:
        """Reset monitoring state (clear non-critical alarms and counters)"""
        # Clear warning alarms but keep critical ones
        to_clear = [alarm_id for alarm_id, alarm in self.active_alarms.items() 
                   if alarm.severity == AlarmSeverity.WARNING]
        
        for alarm_id in to_clear:
            self._clear_alarm(alarm_id)
        
        # Reset time counters
        self.time_outside_warning = 0.0
        self.time_outside_critical = 0.0
        
        # Clear temperature history
        self.temperature_history.clear()
    
    def export_alarm_log(self, start_time: Optional[datetime] = None, 
                        end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Export alarm history for analysis"""
        filtered_alarms = self.alarm_history
        
        if start_time:
            filtered_alarms = [a for a in filtered_alarms if a.timestamp >= start_time]
        
        if end_time:
            filtered_alarms = [a for a in filtered_alarms if a.timestamp <= end_time]
        
        return [
            {
                'alarm_id': alarm.alarm_id,
                'severity': alarm.severity.value,
                'message': alarm.message,
                'timestamp': alarm.timestamp.isoformat(),
                'temperature': alarm.temperature,
                'state': alarm.state.value,
                'duration': alarm.get_duration(),
                'acknowledged_by': alarm.acknowledged_by,
                'acknowledged_time': alarm.acknowledged_time.isoformat() if alarm.acknowledged_time else None
            }
            for alarm in filtered_alarms
        ]


# Convenience functions for common blood storage safety configurations

def create_blood_safety_monitor(blood_product: BloodProperties) -> SafetyMonitor:
    """Create safety monitor optimized for blood storage"""
    return SafetyMonitor(blood_product)


def create_plasma_safety_monitor(blood_product: BloodProperties) -> SafetyMonitor:
    """Create safety monitor optimized for plasma storage with tighter limits"""
    limits = SafetyLimits(
        critical_temp_high=blood_product.critical_temp_high_c,
        critical_temp_low=blood_product.critical_temp_low_c,
        warning_temp_high=blood_product.critical_temp_high_c - 0.5,  # Tighter warning
        warning_temp_low=blood_product.critical_temp_low_c + 0.5,
        max_heating_rate=1.0,  # Slower rates for plasma
        max_cooling_rate=3.0,
        max_time_outside_warning=180.0,  # 3 minutes
        max_time_outside_critical=30.0   # 30 seconds
    )
    
    return SafetyMonitor(blood_product, limits)


def create_emergency_safety_monitor(blood_product: BloodProperties) -> SafetyMonitor:
    """Create safety monitor with very strict limits for emergency use"""
    limits = SafetyLimits(
        critical_temp_high=blood_product.critical_temp_high_c,
        critical_temp_low=blood_product.critical_temp_low_c,
        warning_temp_high=blood_product.target_temp_c + 0.5,  # Very tight warnings
        warning_temp_low=blood_product.target_temp_c - 0.5,
        max_heating_rate=0.5,  # Very slow rates
        max_cooling_rate=1.0,
        max_time_outside_warning=60.0,   # 1 minute
        max_time_outside_critical=15.0   # 15 seconds
    )
    
    return SafetyMonitor(blood_product, limits)