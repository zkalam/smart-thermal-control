"""

This module provides a clean interface between controllers and the thermal simulation,
encapsulating the integration of system state and time stepping.

"""
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from .system_state import *
from .time_step import *
from ..thermal_model.heat_transfer_data import *

@dataclass
class ActuatorLimits:
    max_heating_power: float = 50.0    # W
    max_cooling_power: float = 100.0   # W  
    min_power_increment: float = 1.0   # W (control resolution)
    response_time: float = 30.0        # seconds (actuator lag)

"""Current actuator operating mode"""
class ActuatorMode(Enum):
    OFF = "off"
    HEATING = "heating"
    COOLING = "cooling"
    DEADBAND = "deadband" 

"""High-level thermal system that controllers will interact with"""
class ThermalSystem:

    def __init__(self, blood_product, container_material, volume_liters, container_mass_kg, actuator_limits: Optional[ActuatorLimits] = None):
        # Setup system configuration
        self.integrator = Integrator()
        self.current_state = SystemState(
            time=0.0, blood_temp=20.0, ambient_temp=4.0, air_velocity=1.0,
            blood_product=blood_product, container_material=container_material,
            volume_liters=volume_liters, container_mass_kg=container_mass_kg, applied_power=0.0
        )
        # Actuator configuration
        self.actuator_limits = actuator_limits or ActuatorLimits()
        self.current_thermal_power = 0.0
        self.commanded_power = 0.0  # What controller requested
        self.actuator_mode = ActuatorMode.OFF

    def _apply_actuator_limits(self, commanded_power: float) -> float:

        # Apply power limits
        max_heat = self.actuator_limits.max_heating_power
        max_cool = -self.actuator_limits.max_cooling_power  # Negative for cooling
        
        limited_power = max(max_cool, min(max_heat, commanded_power))
        
        # Apply minimum power threshold (deadband)
        if abs(limited_power) < self.actuator_limits.min_power_increment:
            limited_power = 0.0
            self.actuator_mode = ActuatorMode.DEADBAND if commanded_power != 0.0 else ActuatorMode.OFF
        elif limited_power > 0:
            self.actuator_mode = ActuatorMode.HEATING
        else:
            self.actuator_mode = ActuatorMode.COOLING
            
        # Quantize to available power increments
        if limited_power != 0:
            increment = self.actuator_limits.min_power_increment
            limited_power = round(limited_power / increment) * increment
            
        return limited_power

    def get_system_state(self) -> SystemState:
        # Full state for monitoring
        return self.current_state

    def get_current_temperature(self) -> float:
        # Controller needs to READ temperature
        return self.current_state.blood_temperature

    def apply_thermal_power(self, power_watts: float) -> float:
        # Controller needs to APPLY power
        self.commanded_power = power_watts
        self.current_thermal_power = self._apply_actuator_limits(power_watts)
        return self.current_thermal_power

    def get_actuator_status(self) -> dict:
        utilization_pct = 0.0
        if self.actuator_mode == ActuatorMode.HEATING:
            utilization_pct = (self.current_thermal_power / self.actuator_limits.max_heating_power) * 100
        elif self.actuator_mode == ActuatorMode.COOLING:
            utilization_pct = (abs(self.current_thermal_power) / self.actuator_limits.max_cooling_power) * 100
            
        is_saturated = False
        if self.commanded_power > 0:  # Heating command
            is_saturated = self.commanded_power > self.actuator_limits.max_heating_power
        elif self.commanded_power < 0:  # Cooling command  
            is_saturated = abs(self.commanded_power) > self.actuator_limits.max_cooling_power
            
        return {
            'mode': self.actuator_mode.value,
            'commanded_power_w': self.commanded_power,
            'actual_power_w': self.current_thermal_power,
            'power_utilization_pct': utilization_pct,
            'is_saturated': is_saturated, 
            'in_deadband': self.actuator_mode == ActuatorMode.DEADBAND,
            'max_heating_w': self.actuator_limits.max_heating_power,
            'max_cooling_w': self.actuator_limits.max_cooling_power
        }

    def step(self, dt: float) -> SystemState:
        # Advance simulation one step
        self.current_state = self.integrator.step(self.current_state, dt, self.current_thermal_power)
        return self.current_state

    def reset(self, initial_temperature: float = 20.0, ambient_temperature: float = 4.0):

        self.current_state = SystemState(
            time=0.0, 
            blood_temp=initial_temperature, 
            ambient_temp=ambient_temperature, 
            air_velocity=1.0,
            blood_product=self.current_state.blood_product,
            container_material=self.current_state.container_material,
            volume_liters=self.current_state.volume_liters,
            container_mass_kg=self.current_state.container_mass_kg,
            applied_power=0.0
        )
        self.current_thermal_power = 0.0
        self.commanded_power = 0.0
        self.actuator_mode = ActuatorMode.OFF
        self.integrator.reset()


        
