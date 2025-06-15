"""

Tests for SystemState, Integrator, ThermalSystem and simulation scenarios.

"""

import unittest
from unittest.mock import patch
import warnings
from system_state import *
from time_step import *
from thermal_system import *
from ..thermal_model.heat_transfer_data import *
from ..thermal_model.heat_transfer import validate_blood_temperature


class TestSystemState(unittest.TestCase):
    """Test SystemState class functionality"""
    
    def setUp(self):
        """Set up test components"""
        self.blood_product = MaterialLibrary.WHOLE_BLOOD
        self.container_material = MaterialLibrary.MEDICAL_GRADE_PVC
        self.volume_liters = 0.5
        self.container_mass_kg = 0.08
    
    def test_system_state_creation(self):
        """Test creating SystemState with valid parameters"""
        state = SystemState(
            time=0.0,
            blood_temp=20.0,
            ambient_temp=4.0,
            air_velocity=1.0,
            blood_product=self.blood_product,
            container_material=self.container_material,
            volume_liters=self.volume_liters,
            container_mass_kg=self.container_mass_kg,
            applied_power=0.0
        )
        
        # Validate basic properties
        self.assertEqual(state.time, 0.0)
        self.assertEqual(state.blood_temperature, 20.0)
        self.assertEqual(state.ambient_temperature, 4.0)
        self.assertEqual(state.air_velocity, 1.0)
        self.assertEqual(state.applied_power, 0.0)
    
    def test_thermal_mass_calculation(self):
        """Test thermal mass calculation integration"""
        state = SystemState(
            time=0.0, blood_temp=4.0, ambient_temp=4.0, air_velocity=1.0,
            blood_product=self.blood_product, container_material=self.container_material,
            volume_liters=self.volume_liters, container_mass_kg=self.container_mass_kg
        )
        
        thermal_mass = state.get_thermal_mass()
        self.assertIsInstance(thermal_mass, float)
        self.assertGreater(thermal_mass, 1000)  # Reasonable for 0.5L blood
        self.assertLess(thermal_mass, 5000)     # Not excessive
    
    def test_safety_validation(self):
        """Test safety status integration"""
        # Safe temperature
        safe_state = SystemState(
            time=0.0, blood_temp=4.0, ambient_temp=4.0, air_velocity=1.0,
            blood_product=self.blood_product, container_material=self.container_material,
            volume_liters=self.volume_liters, container_mass_kg=self.container_mass_kg
        )
        
        self.assertTrue(safe_state.is_safe())
        safety_status = safe_state.get_safety_status()
        self.assertTrue(safety_status['is_safe'])
        self.assertEqual(safety_status['status'], 'safe')
        
        # Unsafe temperature
        unsafe_state = SystemState(
            time=0.0, blood_temp=25.0, ambient_temp=4.0, air_velocity=1.0,
            blood_product=self.blood_product, container_material=self.container_material,
            volume_liters=self.volume_liters, container_mass_kg=self.container_mass_kg
        )
        
        self.assertFalse(unsafe_state.is_safe())
        unsafe_safety = unsafe_state.get_safety_status()
        self.assertFalse(unsafe_safety['is_safe'])
        self.assertEqual(unsafe_safety['status'], 'critical')
    
    def test_state_copy(self):
        """Test state copying functionality"""
        original = SystemState(
            time=100.0, blood_temp=15.0, ambient_temp=4.0, air_velocity=1.0,
            blood_product=self.blood_product, container_material=self.container_material,
            volume_liters=self.volume_liters, container_mass_kg=self.container_mass_kg
        )
        
        copied = original.copy()
        
        # Should be equal but separate objects
        self.assertEqual(copied.time, original.time)
        self.assertEqual(copied.blood_temperature, original.blood_temperature)
        self.assertIsNot(copied, original)  # Different objects
        
        # Modifying copy shouldn't affect original
        copied.blood_temperature = 10.0
        self.assertEqual(original.blood_temperature, 15.0)
    
    def test_string_representation(self):
        """Test __str__ method"""
        state = SystemState(
            time=120.0, blood_temp=4.5, ambient_temp=4.0, air_velocity=1.0,
            blood_product=self.blood_product, container_material=self.container_material,
            volume_liters=self.volume_liters, container_mass_kg=self.container_mass_kg
        )
        
        str_repr = str(state)
        self.assertIn("t=120.0s", str_repr)
        self.assertIn("T_blood=4.5°C", str_repr)
        self.assertIn("SAFE", str_repr)
    
class TestTimeIntegration(unittest.TestCase):

    """Test RK4 integration and time stepping"""

    def setUp(self):
        """Set up integration test components"""
        self.blood_product = MaterialLibrary.WHOLE_BLOOD
        self.container_material = MaterialLibrary.MEDICAL_GRADE_PVC
        self.integrator = Integrator()
        
        self.initial_state = SystemState(
            time=0.0, blood_temp=20.0, ambient_temp=4.0, air_velocity=1.0,
            blood_product=self.blood_product, container_material=self.container_material,
            volume_liters=0.5, container_mass_kg=0.08
        )
    
    def test_single_integration_step(self):
        """Test single RK4 integration step"""
        dt = 10.0  # 10 seconds
        thermal_power = -25.0  # 25W cooling
        
        new_state = self.integrator.step(self.initial_state, dt, thermal_power)
        
        # Validate state progression
        self.assertEqual(new_state.time, self.initial_state.time + dt)
        self.assertLess(new_state.blood_temperature, self.initial_state.blood_temperature)  # Should cool
        self.assertEqual(new_state.ambient_temperature, self.initial_state.ambient_temperature)  # Unchanged
        self.assertEqual(new_state.applied_power, thermal_power)
    
    def test_cooling_simulation(self):
        """Test complete cooling simulation"""
        duration = 300.0  # 5 minutes
        dt = 10.0
        thermal_power = -50.0  # Strong cooling
        
        states = self.integrator.simulate(self.initial_state, duration, dt, thermal_power)
        
        # Validate simulation results
        self.assertGreater(len(states), 1)
        self.assertEqual(states[0].time, 0.0)
        self.assertAlmostEqual(states[-1].time, duration, delta=dt)
        
        # Temperature should decrease over time
        initial_temp = states[0].blood_temperature
        final_temp = states[-1].blood_temperature
        self.assertLess(final_temp, initial_temp)
        
        # Should approach ambient temperature
        ambient_temp = states[0].ambient_temperature
        self.assertLess(abs(final_temp - ambient_temp), abs(initial_temp - ambient_temp))
    
    def test_heating_simulation(self):
        """Test heating simulation"""
        # Start with cold blood
        cold_state = SystemState(
            time=0.0, blood_temp=1.0, ambient_temp=20.0, air_velocity=1.0,
            blood_product=self.blood_product, container_material=self.container_material,
            volume_liters=0.5, container_mass_kg=0.08
        )
        
        duration = 300.0
        dt = 10.0
        thermal_power = 30.0  # Heating
        
        states = self.integrator.simulate(cold_state, duration, dt, thermal_power)
        
        # Temperature should increase
        initial_temp = states[0].blood_temperature
        final_temp = states[-1].blood_temperature
        self.assertGreater(final_temp, initial_temp)
    
    def test_variable_power_simulation(self):
        """Test simulation with time-varying power"""
        def power_function(time: float) -> float:
            if time < 150.0:  # First 2.5 minutes: cooling
                return -40.0
            else:  # Rest: heating
                return 20.0
        
        duration = 300.0
        dt = 10.0
        
        states = self.integrator.simulate_with_variable_power(
            self.initial_state, duration, dt, power_function
        )
        
        # Should have cooling then heating phases
        self.assertGreater(len(states), 20)
        
        # Find transition point
        transition_states = [s for s in states if 140.0 <= s.time <= 160.0]
        self.assertGreater(len(transition_states), 0)
    
    def test_no_power_simulation(self):
        """Test natural cooling with no applied power"""
        duration = 600.0  # 10 minutes
        dt = 30.0
        thermal_power = 0.0  # No applied power
        
        states = self.integrator.simulate(self.initial_state, duration, dt, thermal_power)
        
        # Should still cool towards ambient (natural heat transfer)
        initial_temp = states[0].blood_temperature
        final_temp = states[-1].blood_temperature
        self.assertLess(final_temp, initial_temp)
        
        # All states should have zero applied power
        for state in states:
            self.assertEqual(state.applied_power, 0.0)

    
class TestThermalSystem(unittest.TestCase):
    """Test high-level ThermalSystem interface"""
    
    def setUp(self):
        """Set up thermal system test components"""
        self.blood_product = MaterialLibrary.WHOLE_BLOOD
        self.container_material = MaterialLibrary.MEDICAL_GRADE_PVC
        
        self.thermal_system = ThermalSystem(
            blood_product=self.blood_product,
            container_material=self.container_material,
            volume_liters=0.5,
            container_mass_kg=0.08
        )
    
    def test_thermal_system_initialization(self):
        """Test ThermalSystem initialization"""
        # Validate initial state
        self.assertEqual(self.thermal_system.get_current_temperature(), 20.0)
        self.assertEqual(self.thermal_system.current_thermal_power, 0.0)
        self.assertEqual(self.thermal_system.commanded_power, 0.0)
        self.assertEqual(self.thermal_system.actuator_mode, ActuatorMode.OFF)
        
        # Validate system state
        state = self.thermal_system.get_system_state()
        self.assertIsInstance(state, SystemState)
        self.assertEqual(state.blood_temperature, 20.0)
    
    def test_actuator_limits_default(self):
        """Test default actuator limits"""
        limits = self.thermal_system.actuator_limits
        self.assertIsInstance(limits, ActuatorLimits)
        self.assertEqual(limits.max_heating_power, 50.0)
        self.assertEqual(limits.max_cooling_power, 100.0)
        self.assertEqual(limits.min_power_increment, 1.0)
    
    def test_custom_actuator_limits(self):
        """Test custom actuator limits"""
        custom_limits = ActuatorLimits(
            max_heating_power=25.0,
            max_cooling_power=75.0,
            min_power_increment=0.5
        )
        
        system = ThermalSystem(
            self.blood_product, self.container_material, 0.5, 0.08,
            actuator_limits=custom_limits
        )
        
        self.assertEqual(system.actuator_limits.max_heating_power, 25.0)
        self.assertEqual(system.actuator_limits.max_cooling_power, 75.0)
    
    def test_apply_thermal_power_within_limits(self):
        """Test applying power within actuator limits"""
        # Test heating within limits
        actual_power = self.thermal_system.apply_thermal_power(30.0)
        self.assertEqual(actual_power, 30.0)
        self.assertEqual(self.thermal_system.current_thermal_power, 30.0)
        self.assertEqual(self.thermal_system.actuator_mode, ActuatorMode.HEATING)
        
        # Test cooling within limits
        actual_power = self.thermal_system.apply_thermal_power(-50.0)
        self.assertEqual(actual_power, -50.0)
        self.assertEqual(self.thermal_system.current_thermal_power, -50.0)
        self.assertEqual(self.thermal_system.actuator_mode, ActuatorMode.COOLING)
    
    def test_apply_thermal_power_exceeding_limits(self):
        """Test applying power that exceeds actuator limits"""
        # Test heating beyond limit
        actual_power = self.thermal_system.apply_thermal_power(75.0)  # Above 50W limit
        self.assertEqual(actual_power, 50.0)  # Should be limited
        self.assertEqual(self.thermal_system.commanded_power, 75.0)  # Requested power stored
        
        # Test cooling beyond limit
        actual_power = self.thermal_system.apply_thermal_power(-150.0)  # Above 100W limit
        self.assertEqual(actual_power, -100.0)  # Should be limited
    
    def test_apply_thermal_power_deadband(self):
        """Test power application in deadband region"""
        # Test power below minimum threshold
        actual_power = self.thermal_system.apply_thermal_power(0.5)  # Below 1W minimum
        self.assertEqual(actual_power, 0.0)
        self.assertEqual(self.thermal_system.actuator_mode, ActuatorMode.DEADBAND)
        
        # Test zero power
        actual_power = self.thermal_system.apply_thermal_power(0.0)
        self.assertEqual(actual_power, 0.0)
        self.assertEqual(self.thermal_system.actuator_mode, ActuatorMode.OFF)
    
    def test_actuator_status(self):
        """Test actuator status reporting"""
        # Test heating status
        self.thermal_system.apply_thermal_power(25.0)
        status = self.thermal_system.get_actuator_status()
        
        self.assertEqual(status['mode'], 'heating')
        self.assertEqual(status['commanded_power_w'], 25.0)
        self.assertEqual(status['actual_power_w'], 25.0)
        self.assertEqual(status['power_utilization_pct'], 50.0)  # 25W / 50W max = 50%
        self.assertFalse(status['is_saturated'])
        self.assertFalse(status['in_deadband'])
        
        # Test saturation
        self.thermal_system.apply_thermal_power(100.0)  # Above heating limit
        status = self.thermal_system.get_actuator_status()
        self.assertTrue(status['is_saturated'])
    
    def test_simulation_step(self):
        """Test single simulation step"""
        initial_temp = self.thermal_system.get_current_temperature()
        self.thermal_system.apply_thermal_power(-30.0)
        
        new_state = self.thermal_system.step(dt=10.0)
        
        # Temperature should have changed
        new_temp = self.thermal_system.get_current_temperature()
        self.assertNotEqual(new_temp, initial_temp)
        self.assertLess(new_temp, initial_temp)  # Should cool
        
        # State should be updated
        self.assertEqual(new_state.time, 10.0)
        self.assertEqual(new_state.applied_power, -30.0)
    
    def test_system_reset(self):
        """Test system reset functionality"""
        # Run simulation and apply power
        self.thermal_system.apply_thermal_power(-25.0)
        self.thermal_system.step(dt=60.0)
        
        initial_temp = self.thermal_system.get_current_temperature()
        self.assertNotEqual(initial_temp, 20.0)  # Should have changed
        
        # Reset system
        self.thermal_system.reset(initial_temperature=22.0, ambient_temperature=5.0)
        
        # Should be back to specified initial conditions
        self.assertEqual(self.thermal_system.get_current_temperature(), 22.0)
        self.assertEqual(self.thermal_system.get_system_state().ambient_temperature, 5.0)
        self.assertEqual(self.thermal_system.current_thermal_power, 0.0)
        self.assertEqual(self.thermal_system.actuator_mode, ActuatorMode.OFF)


    
class TestSimulationScenarios(unittest.TestCase):
    """Test complete simulation scenarios"""
    
    def test_blood_cooling_scenario(self):
        """Test realistic blood cooling from room temperature"""
        system = ThermalSystem(
            MaterialLibrary.WHOLE_BLOOD,
            MaterialLibrary.MEDICAL_GRADE_PVC,
            0.5, 0.08
        )
        
        # Simulate 30 minutes of active cooling
        duration = 1800.0  # 30 minutes
        dt = 30.0
        cooling_power = -40.0  # 40W cooling
        
        initial_temp = system.get_current_temperature()
        self.assertEqual(initial_temp, 20.0)
        self.assertFalse(system.get_system_state().is_safe())  # Too warm initially
        
        # Run cooling simulation
        system.apply_thermal_power(cooling_power)
        
        states = []
        time_elapsed = 0.0
        while time_elapsed < duration:
            state = system.step(dt)
            states.append(state)
            time_elapsed += dt
        
        final_temp = system.get_current_temperature()
        final_state = system.get_system_state()
        
        # Validate cooling performance
        self.assertLess(final_temp, initial_temp)  # Should have cooled
        self.assertGreater(final_temp, 4.0)        # But not below ambient yet
        
        # Should be approaching safe range
        temp_reduction = initial_temp - final_temp
        self.assertGreater(temp_reduction, 5.0)  # At least 5°C reduction
    
    def test_plasma_thawing_scenario(self):
        """Test plasma thawing from frozen state"""
        system = ThermalSystem(
            MaterialLibrary.PLASMA,
            MaterialLibrary.PETG,
            0.3, 0.05  # Smaller plasma unit
        )
        
        # Start with frozen plasma
        system.reset(initial_temperature=-20.0, ambient_temperature=20.0)
        
        # Apply moderate heating
        heating_power = 15.0
        system.apply_thermal_power(heating_power)
        
        # Simulate 20 minutes of thawing
        duration = 1200.0
        dt = 60.0  # 1 minute steps
        
        states = []
        time_elapsed = 0.0
        while time_elapsed < duration:
            state = system.step(dt)
            states.append(state)
            time_elapsed += dt
        
        initial_temp = states[0].blood_temperature
        final_temp = states[-1].blood_temperature
        
        # Should warm up significantly
        self.assertGreater(final_temp, initial_temp)
        self.assertGreater(final_temp, -10.0)  # Should be well above starting temp
    
    def test_controller_interface_scenario(self):
        """Test system interface for controller integration"""
        system = ThermalSystem(
            MaterialLibrary.WHOLE_BLOOD,
            MaterialLibrary.MEDICAL_GRADE_PVC,
            0.5, 0.08
        )
        
        # Simulate simple controller logic
        target_temp = 4.0
        dt = 10.0
        
        for i in range(20):  # 200 seconds
            current_temp = system.get_current_temperature()
            error = target_temp - current_temp
            
            # Simple proportional control
            kp = 5.0  # Proportional gain
            power_command = kp * error
            
            actual_power = system.apply_thermal_power(power_command)
            state = system.step(dt)
            
            # Monitor system
            status = system.get_actuator_status()
            
            # Validate controller interface
            self.assertIsInstance(current_temp, float)
            self.assertIsInstance(actual_power, float)
            self.assertIsInstance(status, dict)
            self.assertIn('mode', status)
        
        # Should be moving toward target
        final_temp = system.get_current_temperature()
        self.assertLess(abs(final_temp - target_temp), abs(20.0 - target_temp))
    
    def test_safety_monitoring_scenario(self):
        """Test safety monitoring during extreme conditions"""
        system = ThermalSystem(
            MaterialLibrary.WHOLE_BLOOD,
            MaterialLibrary.MEDICAL_GRADE_PVC,
            0.5, 0.08
        )
        
        # Apply excessive heating
        system.apply_thermal_power(50.0)  # Maximum heating
        
        safety_violations = []
        
        for i in range(30):  # 5 minutes
            state = system.step(dt=10.0)
            
            if not state.is_safe():
                safety_violations.append({
                    'time': state.time,
                    'temperature': state.blood_temperature,
                    'status': state.get_safety_status()
                })
        
        # Should eventually exceed safe temperature
        self.assertGreater(len(safety_violations), 0)
        
        # Validate safety violation data
        for violation in safety_violations:
            self.assertGreater(violation['temperature'], 6.0)  # Above safe limit
            self.assertEqual(violation['status']['status'], 'critical')


if __name__ == '__main__':
    unittest.main(verbosity=2)