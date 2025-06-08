"""

This module is a library and implements heat transfer mechanisms:
- Conduction (Fourier's Law)
- Convection (Newton's Law of Cooling)
- Radiation (Stefan-Boltzmann Law)

"""

import numpy as np
from typing import Optional, Union
from dataclasses import dataclass
import warnings


@dataclass
class MaterialProperties:
    # Physical properties of materials for heat transfer calculations
    thermal_conductivity: float  # W/mK - ability to conduct heat
    density: float              # kg/m³ - mass density
    specific_heat: float        # J/kgK - energy to raise temp by 1K
    emissivity: float     # 0-1, surface emissivity for radiation
    
    @property
    def thermal_diffusivity(self) -> float:
        # Calculate thermal diffusivity
        return self.thermal_conductivity / (self.density * self.specific_heat)
    
    @property
    def volumetric_heat_capacity(self) -> float:
        # Calculate volumetric heat capacity
        return self.density * self.specific_heat

@dataclass
class GeometricProperties:
    # Geometric properties for heat transfer calculations
    length: float              # m - characteristic length
    area: float                # m² - heat transfer area
    volume: float              # m³ - volume for thermal mass
    thickness: Optional[float] = None  # m - wall thickness for conduction

# Predefined material properties for common medical device materials
class MaterialLibrary:
    
    # Metals
    ALUMINUM = MaterialProperties(
        thermal_conductivity=205.0,
        density=2700.0,
        specific_heat=900.0,
        emissivity=0.1  # Polished aluminum
    )
    
    STAINLESS_STEEL = MaterialProperties(
        thermal_conductivity=16.0,
        density=8000.0,
        specific_heat=500.0,
        emissivity=0.6
    )
    
    # Plastics
    ABS_PLASTIC = MaterialProperties(
        thermal_conductivity=0.2,
        density=1050.0,
        specific_heat=1400.0,
        emissivity=0.9
    )
    
    POLYSTYRENE = MaterialProperties(
        thermal_conductivity=0.13,
        density=1050.0,
        specific_heat=1300.0,
        emissivity=0.9
    )
    
    # Insulation
    POLYURETHANE_FOAM = MaterialProperties(
        thermal_conductivity=0.025,
        density=30.0,
        specific_heat=1400.0,
        emissivity=0.95
    )
    
    # Electronics
    SILICON = MaterialProperties(
        thermal_conductivity=150.0,
        density=2330.0,
        specific_heat=700.0,
        emissivity=0.7
    )
