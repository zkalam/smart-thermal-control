"""
Heat Transfer Physics Module

This module implements heat transfer mechanisms:
- Conduction (Fourier's Law)
- Convection (Newton's Law of Cooling)
- Radiation (Stefan-Boltzmann Law)

"""

import numpy as np
from typing import Optional, Union
from dataclasses import data
import warnings


@data
class MaterialProperties:
    # Physical properties of materials for heat transfer calculations
    thermal_conductivity: float  # W/mK - ability to conduct heat
    density: float              # kg/m³ - mass density
    specific_heat: float        # J/kgK - energy to raise temp by 1K
    emissivity: float = 0.9     # 0-1, surface emissivity for radiation
    
    @property
    def thermal_diffusivity(self) -> float:
        # Calculate thermal diffusivity
        return self.thermal_conductivity / (self.density * self.specific_heat)
    
    @property
    def volumetric_heat_capacity(self) -> float:
        # Calculate volumetric heat capacity
        return self.density * self.specific_heat