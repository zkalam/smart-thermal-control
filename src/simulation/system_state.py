"""

This module handles current system state, historical tracking, and validation
using the static thermal physics model.

"""

from typing import Optional, List, Tuple, Dict
from copy import deepcopy
import warnings
from ..thermal_model.heat_transfer_data import *
from ..thermal_model.heat_transfer import *


"""Represents thermal system at one moment in time"""
class SystemState:

    def __init__(self, time: float, blood_temp: float, ambient_temp: float,
                 blood_product: BloodProperties, container_material: MaterialProperties,
                 volume_liters: float, container_mass_kg: float,
                 applied_power: float = 0.0):
        
        # Core state variables
        self.time = time
        self.blood_temperature = blood_temp
        self.ambient_temperature = ambient_temp
        self.applied_power = applied_power  # External heating/cooling (W)
        
        # System configuration (needed for physics calculations)
        self.blood_product = blood_product
        self.container_material = container_material
        self.volume_liters = volume_liters
        self.container_mass_kg = container_mass_kg
        
        # Calculate thermal properties using your model
        self._thermal_data = calculate_blood_thermal_mass(
            blood_product, volume_liters, container_material, container_mass_kg
        )

    def get_thermal_mass(self) -> float:
        # Get total thermal mass using your thermal model
        return self._thermal_data['total_thermal_mass']
    
    def get_safety_status(self) -> dict:
        # Validate temperature using your thermal model
        return validate_blood_temperature(self.blood_product, self.blood_temperature)
    
    def is_safe(self) -> bool:
        # Quick safety check
        return self.get_safety_status()['is_safe']
    
    def copy(self) -> 'SystemState':
        # Create a copy of current state
        return deepcopy(self)
        
    def __str__(self) -> str:
        safety = "SAFE" if self.is_safe() else "CRITICAL"
        return f"t={self.time:.1f}s, T_blood={self.blood_temperature:.1f}°C, {safety}" 

"""Manages historical states with thermal model integration"""
class StateHistory:

    def __init__(self, blood_product: BloodProperties):
        self.states: list[SystemState] = []
        self.blood_product = blood_product 

    def add_state(self, state: SystemState):
        
        # validate
        if self.states and state.time <= self.states[-1].time:
            raise ValueError("State time must be monotonically increasing")
        
        # check safety
        safety_status = state.get_safety_status()
        if not safety_status['is_safe']:
            print(f"WARNING: Temperature safety violation at t={state.time:.1f}s")
        
        # Store a copy so original can be modified safely
        self.states.append(deepcopy(state)) 

    def get_temperature_series(self) -> tuple[list, list]:

        # Get time and temperature arrays for plotting
        times = [state.time for state in self.states]
        temps = [state.blood_temperature for state in self.states]
        return times, temps

    def get_safety_events(self) -> list[dict]:

        # Find all safety violations using your validation
        violations = []
        for state in self.states:
            safety = state.get_safety_status()
            if not safety['is_safe']:
                violations.append({
                    'time': state.time,
                    'temperature': state.blood_temperature,
                    'violation_type': safety['status'],
                    'deviation': safety['deviation_from_target']
                })
        return violations
    
    def get_statistics(self) -> dict:
        # Calculate temperature statistics
        if not self.states:
            return {}
            
        temps = [s.blood_temperature for s in self.states]
        target_temp = self.blood_product.target_temp_c
        
        return {
            'min_temperature': min(temps),
            'max_temperature': max(temps),
            'avg_temperature': sum(temps) / len(temps),
            'target_temperature': target_temp,
            'avg_deviation_from_target': sum(abs(t - target_temp) for t in temps) / len(temps),
            'total_simulation_time': self.states[-1].time - self.states[0].time,
            'safety_violations': len(self.get_safety_events())
        }

"""Validates states using your thermal model functions"""
class StateValidator:
    def __init__(self, blood_product: BloodProperties):
        self.blood_product = blood_product

    def validate_state(self, state: SystemState) -> dict:
        # Comprehensive state validation
        results = {
            'is_valid': True,
            'violations': [],
            'warnings': []
        }
        
        safety_status = validate_blood_temperature(self.blood_product, state.blood_temperature)
        
        if not safety_status['is_safe']:
            results['is_valid'] = False
            results['violations'].append({
                'type': 'temperature_safety',
                'message': f"Temperature {state.blood_temperature:.1f}°C outside safe range",
                'severity': 'critical'
            })
        
        if not safety_status['is_within_tolerance']:
            results['warnings'].append({
                'type': 'temperature_tolerance', 
                'message': f"Temperature {state.blood_temperature:.1f}°C outside tolerance",
                'severity': 'warning'
            })
        
        # TODO: Need to add other validations (time consistency, physical constraints, etc.)
        
        return results
    
    def check_rate_of_change(self, current_state: SystemState, previous_state: SystemState) -> bool:
        # Check if temperature change rate is physically reasonable
        dt = current_state.time - previous_state.time
        dT = current_state.blood_temperature - previous_state.blood_temperature
        
        if dt <= 0:
            return False
            
        dT_dt = abs(dT / dt)  # °C/s
        
        # Calculate maximum possible rate based on thermal mass
        thermal_mass = current_state.get_thermal_mass()
        max_power = 1000.0  # Assume 1kW max heating/cooling (conservative)
        max_rate = max_power / thermal_mass  # °C/s
        
        return dT_dt <= max_rate * 2  # Allow 2x safety margin