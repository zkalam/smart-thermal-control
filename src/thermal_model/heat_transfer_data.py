"""

This module is a library and defines physical properties needed for a model

"""
from typing import Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum

class TemperatureUnit(Enum):
    CELSIUS = "°C"
    KELVIN = "K"
    FAHRENHEIT = "°F"

# Immutable physical constants
class PhysicalConstantsType(NamedTuple):

    stefan_boltzmann: float    # W/(m²·K⁴) - Stefan-Boltzmann constant
    gravity: float            # m/s² - Standard gravity for natural convection
    
    # Temperature reference points
    absolute_zero_c: float    # °C - Absolute zero in Celsius
    water_freezing_c: float   # °C - Water freezing point
    room_temperature_c: float # °C - Standard room temperature


CONSTANTS = PhysicalConstantsType(
    stefan_boltzmann=5.670374419e-8,  
    gravity=9.80665,
    absolute_zero_c=-273.15,
    water_freezing_c=0.0,
    room_temperature_c=20.0
)

@dataclass
class MaterialProperties:
    # Physical properties of materials for heat transfer calculations
    thermal_conductivity: float  # W/mK - ability to conduct heat
    density: float              # kg/m³ - mass density
    specific_heat: float        # J/kgK - energy to raise temp by 1K
    emissivity: float     # 0-1, surface emissivity for radiation
    
    def __post_init__(self):
        # Validate material properties
        if self.thermal_conductivity < 0:
            raise ValueError("Thermal conductivity must be non-negative")
        if self.density <= 0:
            raise ValueError("Density must be positive")
        if self.specific_heat <= 0:
            raise ValueError("Specific heat must be positive")
        if not 0 <= self.emissivity <= 1:
            raise ValueError("Emissivity must be between 0 and 1")


@dataclass
class GeometricProperties:
    # Geometric properties for heat transfer calculations
    length: float              # m - characteristic length
    area: float                # m² - heat transfer area
    volume: float              # m³ - volume for thermal mass
    thickness: Optional[float] = None  # m - wall thickness for conduction
    air_velocity: Optional[float] = None # m/s air velocity for convection

    def __post_init__(self):
        # Validate geometric properties
        if self.length <= 0 or self.area <= 0 or self.volume <= 0:
            raise ValueError("All geometric dimensions must be positive")
        if self.thickness is not None and self.thickness <= 0:
            raise ValueError("Thickness must be positive if specified")
        if self.air_velocity is not None and self.air_velocity < 0:
            raise ValueError("Air velocity must be greater than or equal to zero")


@dataclass
class BloodProperties:
    # Thermal properties specific to blood products
    blood_type: str
    target_temp_c: float        # °C - target storage temperature
    temp_tolerance_c: float     # °C - allowable temperature deviation
    critical_temp_high_c: float # °C - maximum safe temperature
    critical_temp_low_c: float  # °C - minimum safe temperature
    density: float              # kg/m³
    specific_heat: float        # J/kgK
    thermal_conductivity: float # W/mK
    thermal_mass_factor: float  # Multiplier for effective thermal mass
    
    # Phase change properties
    phase_change_temp_c: Optional[float] = None  # °C - freezing point
    latent_heat: Optional[float] = None          # J/kg - latent heat of fusion
    
    def __post_init__(self):
        # Validate blood storage temperatures
        if self.critical_temp_low_c >= self.critical_temp_high_c:
            raise ValueError("Critical low temperature must be less than critical high temperature")
        
        # Validate target temperature is within safe range
        if not (self.critical_temp_low_c <= self.target_temp_c <= self.critical_temp_high_c):
            raise ValueError(f"Target temperature {self.target_temp_c}°C outside safe range "
                           f"[{self.critical_temp_low_c}, {self.critical_temp_high_c}]°C")


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

    # Blood properties
    WHOLE_BLOOD = BloodProperties(
        blood_type="Whole Blood",
        target_temp_c=4.0,
        temp_tolerance_c=0.5,       
        critical_temp_high_c=6.0,   # FDA maximum
        critical_temp_low_c=1.0,    # FDA minimum
        density=1060.0,             # kg/m³
        specific_heat=3600.0,       # J/kgK
        thermal_conductivity=0.5,   # W/mK (similar to water)
        thermal_mass_factor=1.2,
        phase_change_temp_c=-0.6,
        latent_heat=334000.0        # J/kg (approximate)
    )
    
    RED_BLOOD_CELLS = BloodProperties(
        blood_type="Red Blood Cells",
        target_temp_c=4.0,
        temp_tolerance_c=0.5,
        critical_temp_high_c=6.0,
        critical_temp_low_c=1.0,
        density=1060.0,
        specific_heat=3600.0,
        thermal_conductivity=0.5,
        thermal_mass_factor=1.15,
        phase_change_temp_c=-0.6,
        latent_heat=334000.0
    )
    
    PLASMA = BloodProperties(
        blood_type="Fresh Frozen Plasma",
        target_temp_c=-18.0,
        temp_tolerance_c=0.0,       # No tolerance above -18°C
        critical_temp_high_c=-18.0, # FDA requirement: must be ≤-18°C
        critical_temp_low_c=-80.0,  # Practical lower limit
        density=1025.0,
        specific_heat=3400.0,
        thermal_conductivity=0.45,
        thermal_mass_factor=0.95,
        phase_change_temp_c=0.0,
        latent_heat=334000.0
    )
    
    PLATELETS = BloodProperties(
        blood_type="Platelets",
        target_temp_c=22.0,         # 20-24°C with agitation
        temp_tolerance_c=2.0,
        critical_temp_high_c=24.0,
        critical_temp_low_c=20.0,
        density=1040.0,
        specific_heat=3500.0,
        thermal_conductivity=0.48,
        thermal_mass_factor=1.0,
        phase_change_temp_c=None,   # No freezing concerns
        latent_heat=None
    )