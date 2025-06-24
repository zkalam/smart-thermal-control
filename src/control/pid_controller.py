"""

This modeule mplements proportional-integral-derivative control for precise temperature regulation
with medical-grade accuracy and safety considerations.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import time


@dataclass
class PIDGains:
    # PID controller gain parameters
    kp: float = 1.0    # Proportional gain
    ki: float = 0.1    # Integral gain  
    kd: float = 0.05   # Derivative gain


class ControllerMode(Enum):
    """Controller operating modes"""
    MANUAL = "manual"      # Manual power control
    AUTOMATIC = "automatic" # PID control active
    DISABLED = "disabled"   # Controller disabled


"""
PID temperature controller for blood storage applications

Provides precise temperature control with configurable gains,
integral windup protection, and safety limits.
"""
class PIDController:
    
    """
    Initialize PID controller
    
    Args:
        gains: PID gain parameters (Kp, Ki, Kd)
        setpoint: Target temperature (°C)
        output_limits: (min_power, max_power) in Watts
    """
    def __init__(self, gains: PIDGains, setpoint: float = 4.0, 
                 output_limits: tuple = (-100.0, 50.0)):
        self.gains = gains
        self.setpoint = setpoint
        self.output_min, self.output_max = output_limits
        
        # Controller state
        self.mode = ControllerMode.AUTOMATIC
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = None
        self.last_output = 0.0
        
        # Performance tracking
        self.error_history = []
        self.output_history = []
        
    def set_setpoint(self, new_setpoint: float) -> None:
        # Update target temperature setpoint
        self.setpoint = new_setpoint
        
    def set_gains(self, gains: PIDGains) -> None:
        # Update PID gain parameters
        self.gains = gains
        
    def set_mode(self, mode: ControllerMode) -> None:
        # Set controller operating mode
        self.mode = mode
        if mode == ControllerMode.DISABLED:
            self.reset()
    

    """
    Update PID controller and calculate control output
    
    Args:
        current_temp: Current temperature measurement (°C)
        dt: Time step (seconds). If None, calculated from system time
        
    Returns:
        Control output (thermal power in Watts)
    """
    def update(self, current_temp: float, dt: Optional[float] = None) -> float:

        if self.mode != ControllerMode.AUTOMATIC:
            return 0.0
            
        # Calculate time step
        current_time = time.time()
        if dt is None:
            if self.last_time is None:
                self.last_time = current_time
                return 0.0
            dt = current_time - self.last_time
        self.last_time = current_time
        
        # Prevent division by zero or negative time steps
        if dt <= 0:
            return self.last_output
            
        # Calculate error
        error = self.setpoint - current_temp
        
        # Proportional term
        proportional = self.gains.kp * error
        
        # Integral term with windup protection
        self.integral += error * dt
        self._apply_integral_limits()
        integral = self.gains.ki * self.integral
        
        # Derivative term
        derivative = self.gains.kd * (error - self.last_error) / dt
        
        # Calculate total output
        output = proportional + integral + derivative
        
        # Apply output limits
        output = max(self.output_min, min(self.output_max, output))
        
        # Store for next iteration
        self.last_error = error
        self.last_output = output
        
        # Track performance
        self.error_history.append(error)
        self.output_history.append(output)
        
        # Limit history size
        if len(self.error_history) > 1000:
            self.error_history.pop(0)
            self.output_history.pop(0)
            
        return output
    
    def _apply_integral_limits(self) -> None:
        # Prevent integral windup by limiting integral term
        # Calculate maximum integral contribution
        max_integral = self.output_max / self.gains.ki if self.gains.ki != 0 else float('inf')
        min_integral = self.output_min / self.gains.ki if self.gains.ki != 0 else float('-inf')
        
        # Clamp integral term
        self.integral = max(min_integral, min(max_integral, self.integral))
    
    def reset(self) -> None:
        # Reset controller state (clear integral, derivative history)
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = None
        self.last_output = 0.0
        self.error_history.clear()
        self.output_history.clear()
    
    def get_status(self) -> Dict[str, Any]:
        # Get current controller status and performance metrics
        recent_errors = self.error_history[-10:] if self.error_history else [0.0]
        
        return {
            'mode': self.mode.value,
            'setpoint_c': self.setpoint,
            'last_error_c': self.last_error,
            'integral_term': self.integral,
            'last_output_w': self.last_output,
            'gains': {
                'kp': self.gains.kp,
                'ki': self.gains.ki,
                'kd': self.gains.kd
            },
            'output_limits_w': (self.output_min, self.output_max),
            'avg_recent_error_c': sum(recent_errors) / len(recent_errors),
            'performance': self._calculate_performance_metrics()
        }
    
    def _calculate_performance_metrics(self) -> Dict[str, float]:
        # Calculate controller performance metrics
        if not self.error_history:
            return {'sse': 0.0, 'ise': 0.0, 'max_error': 0.0}
            
        # Sum of squared errors
        sse = sum(e**2 for e in self.error_history)
        
        # Integral of squared error (approximated)
        ise = sse  # Simplified - would need time integration for true ISE
        
        # Maximum absolute error
        max_error = max(abs(e) for e in self.error_history)
        
        return {
            'sse': sse,
            'ise': ise,
            'max_error': max_error
        }
    
    def tune_aggressive(self) -> None:
        # Set aggressive tuning for fast response (use with caution)
        self.gains = PIDGains(kp=3.0, ki=0.5, kd=0.2)
        
    def tune_conservative(self) -> None:
        # Set conservative tuning for stable, slow response
        self.gains = PIDGains(kp=0.5, ki=0.05, kd=0.01)
        
    def tune_blood_storage(self) -> None:
        # Set tuning optimized for blood storage applications
        # Conservative tuning appropriate for medical applications
        self.gains = PIDGains(kp=1.0, ki=0.1, kd=0.05)


"""
Create PID controller optimized for blood storage

Args:
    target_temp: Target storage temperature (°C)
    
Returns:
    Configured PID controller
"""
# Convenience functions for common blood storage scenarios
def create_blood_storage_controller(target_temp: float = 4.0) -> PIDController:

    gains = PIDGains(kp=1.0, ki=0.1, kd=0.05)  # Conservative medical-grade tuning
    output_limits = (-100.0, 50.0)  # Stronger cooling than heating
    
    controller = PIDController(gains, target_temp, output_limits)
    return controller

"""
Create PID controller optimized for plasma freezing

Args:
    target_temp: Target plasma temperature (°C)
    
Returns:
    Configured PID controller for plasma applications
"""
def create_plasma_controller(target_temp: float = -18.0) -> PIDController:

    gains = PIDGains(kp=2.0, ki=0.2, kd=0.1)  # More aggressive for large temperature changes
    output_limits = (-200.0, 100.0)  # Higher power for freezing applications
    
    controller = PIDController(gains, target_temp, output_limits)
    return controller


"""
Create PID controller optimized for platelet storage

Args:
    target_temp: Target platelet temperature (°C)
    
Returns:
    Configured PID controller for platelet applications
"""
def create_platelet_controller(target_temp: float = 22.0) -> PIDController:

    gains = PIDGains(kp=1.5, ki=0.15, kd=0.075)  # Moderate response for room temperature
    output_limits = (-75.0, 75.0)  # Balanced heating/cooling
    
    controller = PIDController(gains, target_temp, output_limits)
    return controller