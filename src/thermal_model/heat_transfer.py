"""

This module is a library and implements heat transfer mechanisms:
- Conduction (Fourier's Law)
- Convection (Newton's Law of Cooling)
- Radiation (Stefan-Boltzmann Law)

"""

import numpy as np
from typing import Optional, NamedTuple
from dataclasses import dataclass
import warnings


# Immutable physical constants
class PhysicalConstantsType(NamedTuple):
    
    stefan_boltzmann: float    # W/(m²·K⁴) - Stefan-Boltzmann constant for radiation
    boltzmann: float          # J/K - Boltzmann constant
    gas_constant: float       # J/(mol·K) - Universal gas constant
    gravity: float            # m/s² - Standard gravity for natural convection
    atm_pressure: float       # Pa - Standard atmospheric pressure
    
    # Temperature reference points
    absolute_zero: float      # K - 0 K in Kelvin
    water_freezing: float     # K - 273.15 K (0°C)
    water_boiling: float      # K - 373.15 K (100°C)
    room_temperature: float   # K - 293.15 K (20°C)

CONSTANTS = PhysicalConstantsType(
    stefan_boltzmann=5.670374419e-8,
    boltzmann=1.380649e-23,
    gas_constant=8.314462618,
    gravity=9.80665,
    atm_pressure=101325.0,
    absolute_zero=0.0,
    water_freezing=273.15,
    water_boiling=373.15,
    room_temperature=293.15
)

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

@dataclass
class BloodProperties:
    # Thermal properties specific to blood products
    blood_type: str            # Type of blood product
    target_temp: float         # °C - target storage temperature
    temp_tolerance: float      # °C - allowable temperature deviation
    thermal_mass_factor: float # Multiplier for effective thermal mass
    phase_change_temp: Optional[float] = None  # °C - freezing point if applicable

# Predefined material properties for common materials used in blood storage
class MaterialLibrary:
    
    # Metals commonly used in medical equipment
    ALUMINUM = MaterialProperties(
        thermal_conductivity=205.0,
        density=2700.0,
        specific_heat=900.0,
        emissivity=0.1  # Polished aluminum
    )
    
    STAINLESS_STEEL_316 = MaterialProperties(
        thermal_conductivity=16.3,
        density=8000.0,
        specific_heat=500.0,
        emissivity=0.6  # Medical grade stainless steel
    )
    
    # Plastics for medical containers
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
    
    # Medical grade plastics
    MEDICAL_GRADE_PVC = MaterialProperties(
        thermal_conductivity=0.16,
        density=1380.0,
        specific_heat=1000.0,
        emissivity=0.9
    )
    
    PETG = MaterialProperties(
        thermal_conductivity=0.2,
        density=1270.0,
        specific_heat=1200.0,
        emissivity=0.85
    )
    
    # Insulation materials
    POLYURETHANE_FOAM = MaterialProperties(
        thermal_conductivity=0.025,
        density=30.0,
        specific_heat=1400.0,
        emissivity=0.95
    )
    
    VACUUM_INSULATION = MaterialProperties(
        thermal_conductivity=0.004,  # Very low for vacuum panels
        density=200.0,
        specific_heat=1000.0,
        emissivity=0.05
    )
    
    # Phase change materials for thermal buffering
    PARAFFIN_WAX = MaterialProperties(
        thermal_conductivity=0.24,
        density=900.0,
        specific_heat=2000.0,  # Effective including latent heat
        emissivity=0.95
    )
    
    # Electronics and sensors
    SILICON = MaterialProperties(
        thermal_conductivity=150.0,
        density=2330.0,
        specific_heat=700.0,
        emissivity=0.7
    )

    WHOLE_BLOOD = BloodProperties(
        blood_type="Whole Blood",
        target_temp=4.0,           # 1-6°C range, 4°C typical
        temp_tolerance=1.0,        # ±1°C maximum deviation
        thermal_mass_factor=1.2,   # Higher than water due to cellular content
        phase_change_temp=-0.6     # Approximate freezing point
    )
    
    RED_BLOOD_CELLS = BloodProperties(
        blood_type="Red Blood Cells",
        target_temp=4.0,
        temp_tolerance=1.0,
        thermal_mass_factor=1.15,
        phase_change_temp=-0.6
    )
    
    PLASMA = BloodProperties(
        blood_type="Fresh Frozen Plasma",
        target_temp=-18.0,         # Must be -18°C or below
        temp_tolerance=2.0,        # Some tolerance for frozen storage
        thermal_mass_factor=0.95,  # Lower than whole blood
        phase_change_temp=0.0      # Freezes at 0°C
    )
    
    PLATELETS = BloodProperties(
        blood_type="Platelets",
        target_temp=22.0,          # 20-24°C with constant agitation
        temp_tolerance=2.0,
        thermal_mass_factor=1.0,
        phase_change_temp=None     # No freezing concerns
    )
    
    CRYOPRECIPITATE = BloodProperties(
        blood_type="Cryoprecipitate",
        target_temp=-18.0,
        temp_tolerance=2.0,
        thermal_mass_factor=0.9,
        phase_change_temp=0.0
    )


