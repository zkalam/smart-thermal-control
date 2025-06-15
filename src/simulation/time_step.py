"""

This module handles time-stepping integration to evolve system temperature over time.

"""

from typing import Optional, Callable
import warnings

from system_state import *
from ..thermal_model.heat_transfer import *
from ..thermal_model.heat_transfer_data import *

"""
Calculate dT/dt using thermal model (derivative function for RK4)

Args:
    current_state: Current system state
    thermal_power: Applied heating/cooling power (W, positive = heating)
    geometry: Container geometry (if None, uses default)

Returns:
    Temperature change rate (°C/s)

"""

def calculate_dT_dt(current_state: SystemState, thermal_power: float = 0.0, 
                                    geometry: Optional[GeometricProperties] = None) -> float:

    # Default geometry if not provided
    if geometry is None:
        geometry = GeometricProperties(
            length=0.15,     # 15cm characteristic length
            area=0.035,      # 350 cm² surface area
            volume=current_state.volume_liters / 1000.0,
            thickness=0.003  # 3mm wall thickness
        )
    
    # Calculate environmental heat transfer using thermal model
    q_conduction = conduction_heat_transfer(
        material=current_state.container_material,
        geometry=geometry,
        temp_hot=max(current_state.blood_temperature, current_state.ambient_temperature),
        temp_cold=min(current_state.blood_temperature, current_state.ambient_temperature)
    )
    
    q_convection = convection_heat_transfer(
        geometry=geometry,
        area=geometry.area,
        temp_surface=current_state.blood_temperature,
        temp_fluid=current_state.ambient_temperature,
        orientation='vertical',
        air_velocity=current_state.air_velocity
    )
    
    q_radiation = radiation_heat_transfer(
        material=current_state.container_material,
        area=geometry.area,
        temp_hot_c=max(current_state.blood_temperature, current_state.ambient_temperature),
        temp_cold_c=min(current_state.blood_temperature, current_state.ambient_temperature)
    )
    
    # Determine heat flow direction
    if current_state.blood_temperature > current_state.ambient_temperature:
        q_environmental = -(q_conduction + q_convection + q_radiation)  # Heat loss
    else:
        q_environmental = q_conduction + q_convection + q_radiation     # Heat gain
    
    # Total heat into system
    q_total = thermal_power + q_environmental  # W
    
    # Temperature change rate: dT/dt = Q / (mass * cp)
    thermal_mass = current_state.get_thermal_mass()  # J/K
    dT_dt = q_total / thermal_mass  # K/s (same as °C/s)
    
    return dT_dt

"""
Create intermediate state for RK4 calculations

Args:
    base_state: Base system state
    temp_offset: Temperature offset from base (°C)
    time_offset: Time offset from base (seconds)

Returns:
    New state with adjusted temperature and time
"""
def create_intermediate_state(base_state: SystemState, temp_offset: float, time_offset: float) -> SystemState:
    return SystemState(
    time=base_state.time + time_offset,
    blood_temp=base_state.blood_temperature + temp_offset,
    ambient_temp=base_state.ambient_temperature,
    air_velocity=base_state.air_velocity,
    blood_product=base_state.blood_product,
    container_material=base_state.container_material,
    volume_liters=base_state.volume_liters,
    container_mass_kg=base_state.container_mass_kg,
    applied_power=base_state.applied_power
)

"""
Single Runge-Kutta 4th order integration step

RK4 Formula:
k1 = f(t, y)
k2 = f(t + dt/2, y + k1*dt/2)
k3 = f(t + dt/2, y + k2*dt/2)
k4 = f(t + dt, y + k3*dt)
y_new = y + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)

Args:
    current_state: Current system state
    dt: Time step (seconds)
    thermal_power: Applied heating/cooling power (W)
    geometry: Container geometry (optional)

Returns:
    New system state after RK4 integration step
"""

def rk4_step(current_state: SystemState, dt: float, thermal_power: float = 0.0,
             geometry: Optional[GeometricProperties] = None) -> SystemState:

 # Update applied power for intermediate calculations
    state_with_power = SystemState(
        time=current_state.time,
        blood_temp=current_state.blood_temperature,
        ambient_temp=current_state.ambient_temperature,
        air_velocity=current_state.air_velocity,
        blood_product=current_state.blood_product,
        container_material=current_state.container_material,
        volume_liters=current_state.volume_liters,
        container_mass_kg=current_state.container_mass_kg,
        applied_power=thermal_power
    )
    
    # k1: derivative at current state
    k1 = calculate_dT_dt(state_with_power, thermal_power, geometry)
    
    # k2: derivative at midpoint using k1
    intermediate_state2 = create_intermediate_state(state_with_power, k1 * dt/2, dt/2)
    k2 = calculate_dT_dt(intermediate_state2, thermal_power, geometry)
    
    # k3: derivative at midpoint using k2  
    intermediate_state3 = create_intermediate_state(state_with_power, k2 * dt/2, dt/2)
    k3 = calculate_dT_dt(intermediate_state3, thermal_power, geometry)
    
    # k4: derivative at endpoint using k3
    intermediate_state4 = create_intermediate_state(state_with_power, k3 * dt, dt)
    k4 = calculate_dT_dt(intermediate_state4, thermal_power, geometry)
    
    # RK4 weighted average
    dT = (dt/6) * (k1 + 2*k2 + 2*k3 + k4)
    new_temperature = current_state.blood_temperature + dT
    
    # Create new state
    new_state = SystemState(
        time=current_state.time + dt,
        blood_temp=new_temperature,
        ambient_temp=current_state.ambient_temperature,
        air_velocity=current_state.air_velocity,
        blood_product=current_state.blood_product,
        container_material=current_state.container_material,
        volume_liters=current_state.volume_liters,
        container_mass_kg=current_state.container_mass_kg,
        applied_power=thermal_power
    )
    
    return new_state

"""
Runge-Kutta 4th order integrator for thermal simulation

"""
class Integrator:

    """
    Initialize RK4 integrator
    
    Args:
        default_geometry: Default container geometry to use
    """
    def __init__(self, default_geometry: Optional[GeometricProperties] = None):

        self.default_geometry = default_geometry
        self.step_count = 0

        """
    Perform one RK4 integration step
    
    Args:
        current_state: Current system state
        dt: Time step (seconds)  
        thermal_power: Applied thermal power (W)
    
    Returns:
        New system state after RK4 integration step
    """   
    def step(self, current_state: SystemState, dt: float, thermal_power: float = 0.0) -> SystemState:

        self.step_count += 1
        return rk4_step(current_state, dt, thermal_power, self.default_geometry)


    """
    Run complete simulation using RK4
    
    Args:
        initial_state: Starting system state
        duration: Total simulation time (seconds)
        dt: Time step (seconds)
        thermal_power: Constant thermal power (W)
    
    Returns:
        List of system states over time
    """
    def simulate(self, initial_state: SystemState, duration: float, dt: float = 1.0,
                 thermal_power: float = 0.0) -> list[SystemState]:
       
        states = [initial_state]
        current_state = initial_state
        
        time_elapsed = 0.0
        while time_elapsed < duration:
            # Adjust final time step if needed
            actual_dt = min(dt, duration - time_elapsed)
            
            # RK4 integration step
            new_state = self.step(current_state, actual_dt, thermal_power)
            states.append(new_state)
            
            # Update for next iteration
            current_state = new_state
            time_elapsed += actual_dt
        
        return states

    """
    Run simulation with time-varying thermal power
    
    Args:
        initial_state: Starting system state
        duration: Total simulation time (seconds)
        dt: Time step (seconds)
        power_function: Function that takes time and returns thermal power
    
    Returns:
        List of system states over time
    """  
    def simulate_with_variable_power(self, initial_state: SystemState, duration: float, dt: float,
                                   power_function: Callable[[float], float]) -> list[SystemState]:

        states = [initial_state]
        current_state = initial_state
        
        time_elapsed = 0.0
        while time_elapsed < duration:
            actual_dt = min(dt, duration - time_elapsed)
            
            # Get thermal power at current time
            current_power = power_function(current_state.time)
            
            # RK4 step with current power
            new_state = self.step(current_state, actual_dt, current_power)
            states.append(new_state)
            
            current_state = new_state
            time_elapsed += actual_dt
        
        return states
    
    def get_step_count(self) -> int:
        # Get number of integration steps performed
        return self.step_count
    
    def reset(self):
        # Reset step counter
        self.step_count = 0