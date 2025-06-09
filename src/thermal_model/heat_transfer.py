"""

This module implements heat transfer mechanisms in the context of blood storage:
- Conduction (Fourier's Law)
- Convection (Newton's Law of Cooling)
- Radiation (Stefan-Boltzmann Law)

"""
from heat_transfer_data import *
import warnings


""" Heat transfer calculations """

# Convert Celsius to Kelvin with validation
def celsius_to_kelvin(temp_c: float) -> float:
    
    if temp_c < CONSTANTS.absolute_zero_c:
        raise ValueError(f"Temperature {temp_c}°C is below absolute zero")
    return temp_c + 273.15

# Convert Kelvin to Celsius with validation
def kelvin_to_celsius(temp_k: float) -> float:
    
    if temp_k < 0:
        raise ValueError(f"Temperature {temp_k}K is below absolute zero")
    return temp_k - 273.15

"""
Calculate thermal resistance for conduction through a material

For planar geometry: R = thickness / (k × area)
For cylindrical: R = ln(r_outer/r_inner) / (2π × k × length)

Args:
    material: Material thermal properties
    geometry: Geometric properties
    
Returns:
    Thermal resistance in K/W
"""
def conduction_resistance(material: MaterialProperties, geometry: GeometricProperties) -> float:

    if geometry.thickness is None:
        raise ValueError("Thickness required for conduction resistance calculation")
    
    if geometry.thickness <= 0:
        raise ValueError("Thickness must be positive")
    
    R_cond = geometry.thickness / (material.thermal_conductivity * geometry.area)
    return R_cond

"""
Get typical convection coefficients for different scenarios

    Args:
        T_surface: Surface temperature (°C)
        T_fluid: Fluid temperature (°C)
        length: Characteristic length (m)
        velocity: Air velocity (m/s)
        orientation: 'vertical', 'horizontal_hot_up', or 'horizontal_hot_down'
    
Returns:
    Convective heat transfer coefficient (W/m²K)
"""
def get_convection_coefficient(length: float, temp_surface: float, temp_fluid: float, velocity: float, orientation: str) -> float:
    
    # Static air conditions
    if velocity < 0.1:
        # Temperature difference
        delta_T = abs(temp_surface - temp_fluid)
        
        if delta_T < 0.1:
            return 1.0  # Minimal convection for very small temperature differences

        # Film temperature for property evaluation
        T_film = celsius_to_kelvin((temp_surface + temp_fluid) / 2)

        # Air properties at film temperature (approximate)
        # These are simplified correlations for air at atmospheric pressure
        beta = 1 / T_film  # Thermal expansion coefficient for ideal gas
        nu = 1.5e-5 * (T_film / 300)**1.5  # Kinematic viscosity (m²/s)
        alpha = 2.2e-5 * (T_film / 300)**1.5  # Thermal diffusivity (m²/s)
        k_air = 0.026 * (T_film / 300)**0.8  # Thermal conductivity (W/mK)

        # Rayleigh number
        Ra = CONSTANTS.gravity * beta * delta_T * length**3 / (nu * alpha)

        # Nusselt number correlations based on orientation
        if orientation == 'vertical':
            if Ra < 1e9:
                Nu = 0.68 + 0.67 * Ra**(1/4) / (1 + (0.492/0.7)**(9/16))**(4/9)
            else:
                Nu = (0.825 + 0.387 * Ra**(1/6) / (1 + (0.492/0.7)**(9/16))**(8/27))**2
        elif orientation == 'horizontal_hot_up':
            Nu = 0.54 * Ra**(1/4) if Ra < 1e7 else 0.15 * Ra**(1/3)
        elif orientation == 'horizontal_hot_down':
            Nu = 0.27 * Ra**(1/4)
        else:
            warnings.warn(f"Unknown orientation '{orientation}', using vertical correlation")
            Nu = 0.68 + 0.67 * Ra**(1/4) / (1 + (0.492/0.7)**(9/16))**(4/9)

        # Convection coefficient
        h = Nu * k_air / length
    
        return max(h, 1.0)  # Minimum convection coefficient

    # Air is moving (fan blowing or container is being transported)
    else:
        # Film temperature for property evaluation
        T_film = celsius_to_kelvin((temp_surface + temp_fluid) / 2)

        # Air properties (simplified)
        nu = 1.5e-5 * (T_film / 300)**1.5  # Kinematic viscosity
        k_air = 0.026 * (T_film / 300)**0.8  # Thermal conductivity
        Pr = 0.7  # Prandtl number for air (approximately constant)

        # Reynolds number
        Re = velocity * length / nu

        # Nusselt number correlation (flat plate, external flow)
        if Re < 5e5:  # Laminar flow
            Nu = 0.664 * Re**0.5 * Pr**(1/3)
        else:  # Turbulent flow
            Nu = 0.037 * Re**0.8 * Pr**(1/3)
        
        # Convection coefficient
        h = Nu * k_air / length
        
        return h

"""
Calculate conductive heat transfer rate using Fourier's Law
Q = k * A * (T_hot - T_cold) / L

Args:
    material: Material thermal properties
    geometry: Geometric properties
    temp_hot: Hot side temperature (°C)
    temp_cold: Cold side temperature (°C)
    
Returns:
    Heat transfer rate (W)
"""
def conduction_heat_transfer(material: MaterialProperties, geometry: GeometricProperties, temp_hot: float, temp_cold: float) -> float:

    if geometry.thickness is None:
        geometry.thickness = geometry.length
        
    if geometry.thickness <= 0:
        raise ValueError("Thickness must be positive for conduction calculations")
        
    delta_t = temp_hot - temp_cold
    q_cond = (material.thermal_conductivity * geometry.area * delta_t) / geometry.thickness
    
    return q_cond


"""
Calculate convective heat transfer using Newton's Law of Cooling
Q = h * A * (T_surface - T_fluid)

Args:
    geometry: Geometric properties
    area: Heat transfer area (m²)
    temp_surface: Surface temperature (°C)
    temp_fluid: Fluid temperature (°C)
    orientation: 'vertical', 'horizontal_hot_up', or 'horizontal_hot_down'
    
Returns:
    Heat transfer rate (W)
"""
def convection_heat_transfer(geometry: GeometricProperties, area: float, temp_surface: float, temp_fluid: float, orientation: str) -> float:

    h_conv = get_convection_coefficient(geometry.length, temp_surface, temp_fluid, geometry.air_velocity, orientation)
    delta_t = temp_surface - temp_fluid
    q_conv =  h_conv * area * delta_t
    
    return q_conv


"""
Calculate radiative heat transfer with explicit temperature units
Q = ε * σ * A * (T_hot⁴ - T_cold⁴)

Args:
    material: Material properties (for emissivity)
    area: Heat transfer area (m²)
    temp_hot_c: Hot temperature (°C) - explicitly Celsius
    temp_cold_c: Cold temperature (°C) - explicitly Celsius
    
Returns:
    Heat transfer rate (W)
"""
def radiation_heat_transfer(material: MaterialProperties, area: float, temp_hot_c: float, temp_cold_c: float) -> float:

    # Convert to Kelvin for Stefan-Boltzmann law
    temp_hot_k = celsius_to_kelvin(temp_hot_c)
    temp_cold_k = celsius_to_kelvin(temp_cold_c)
    
    q_rad = (material.emissivity * CONSTANTS.stefan_boltzmann * area * (temp_hot_k**4 - temp_cold_k**4))
    
    return q_rad

"""
Calculate effective thermal mass including blood and container

"""
def calculate_blood_thermal_mass(blood_product: BloodProperties, volume_liters: float, container_material: MaterialProperties, container_mass_kg: float) -> float:

    if volume_liters <= 0 or container_mass_kg < 0:
        raise ValueError("Volume must be positive, container mass non-negative")
    
    # Convert volume to m³
    volume_m3 = volume_liters / 1000.0
    
    # Calculate blood thermal mass using actual blood properties
    blood_mass_kg = blood_product.density * volume_m3
    blood_thermal_mass = (blood_mass_kg * blood_product.specific_heat * blood_product.thermal_mass_factor)
    
    # Container thermal mass
    container_thermal_mass = container_mass_kg * container_material.specific_heat
    
    return blood_thermal_mass + container_thermal_mass


