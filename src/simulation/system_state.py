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

"""Manages historical states with thermal model integration"""
class StateHistory:
    def __init__(self, blood_product: BloodProperties):
        self.states: list[SystemState] = []
        self.blood_product = blood_product  


"""Validates states using your thermal model functions"""
class StateValidator:
    def __init__(self, blood_product: BloodProperties):
        self.blood_product = blood_product