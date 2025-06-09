"""

This module is a library and implements heat transfer mechanisms:
- Conduction (Fourier's Law)
- Convection (Newton's Law of Cooling)
- Radiation (Stefan-Boltzmann Law)

"""

import numpy as np
from heat_transfer_data import *
import warnings

"""
Get typical convection coefficients for different storage scenarios

Args:
    storage_type: Type of storage environment
    
Returns:
    Convective heat transfer coefficient (W/m²K)
"""
def get_convection_coefficient(storage_type: str) -> float:
    coefficients = {
        'still_air': CONSTANTS.still_air,           
        'forced_air': CONSTANTS.forced_air,         
        'refrigerated': CONSTANTS.refrigerated,       
        'transport': CONSTANTS.transport,          
        'emergency': CONSTANTS.emergency,           
    }
    
    return coefficients.get(storage_type.lower(), 5.0)

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

# Heat transfer calculations
class HeatTransfer:

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
    @staticmethod
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
        h_conv: Convective heat transfer coefficient (W/m²K)
        area: Heat transfer area (m²)
        temp_surface: Surface temperature (°C)
        temp_fluid: Fluid temperature (°C)
        
    Returns:
        Heat transfer rate (W)
    """
    @staticmethod
    def convection_heat_transfer(storage_type: str, area: float, temp_surface: float, temp_fluid: float) -> float:

        h_conv = get_convection_coefficient(storage_type)
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
    @staticmethod
    def radiation_heat_transfer(material: MaterialProperties, area: float, temp_hot_c: float, temp_cold_c: float) -> float:

        # Convert to Kelvin for Stefan-Boltzmann law
        temp_hot_k = celsius_to_kelvin(temp_hot_c)
        temp_cold_k = celsius_to_kelvin(temp_cold_c)
        
        q_rad = (material.emissivity * CONSTANTS.stefan_boltzmann * area * (temp_hot_k**4 - temp_cold_k**4))
        
        return q_rad
