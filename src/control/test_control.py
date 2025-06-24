"""
Comprehensive test suite for PID controller implementation

Tests cover PID functionality, blood storage scenarios, and controller performance.
"""

import unittest
from unittest.mock import patch, MagicMock
import time
import math
from .pid_controller import *


class TestPIDGains(unittest.TestCase):
    """Test PID gain parameter handling"""
    
    def test_pid_gains_creation(self):
        """Test PIDGains dataclass creation"""
        gains = PIDGains(kp=2.0, ki=0.5, kd=0.1)
        
        self.assertEqual(gains.kp, 2.0)
        self.assertEqual(gains.ki, 0.5)
        self.assertEqual(gains.kd, 0.1)
    
    def test_pid_gains_defaults(self):
        """Test default PID gain values"""
        gains = PIDGains()
        
        self.assertEqual(gains.kp, 1.0)
        self.assertEqual(gains.ki, 0.1)
        self.assertEqual(gains.kd, 0.05)


class TestControllerMode(unittest.TestCase):
    """Test controller mode enumeration"""
    
    def test_controller_modes(self):
        """Test all controller mode values"""
        self.assertEqual(ControllerMode.MANUAL.value, "manual")
        self.assertEqual(ControllerMode.AUTOMATIC.value, "automatic")
        self.assertEqual(ControllerMode.DISABLED.value, "disabled")


class TestPIDController(unittest.TestCase):
    """Test core PID controller functionality"""
    
    def setUp(self):
        """Set up test controller"""
        self.gains = PIDGains(kp=1.0, ki=0.1, kd=0.05)
        self.setpoint = 4.0
        self.output_limits = (-100.0, 50.0)
        
        self.controller = PIDController(
            gains=self.gains,
            setpoint=self.setpoint,
            output_limits=self.output_limits
        )
    
    def test_controller_initialization(self):
        """Test controller initialization"""
        self.assertEqual(self.controller.gains.kp, 1.0)
        self.assertEqual(self.controller.setpoint, 4.0)
        self.assertEqual(self.controller.output_min, -100.0)
        self.assertEqual(self.controller.output_max, 50.0)
        self.assertEqual(self.controller.mode, ControllerMode.AUTOMATIC)
        
        # Initial state should be reset
        self.assertEqual(self.controller.last_error, 0.0)
        self.assertEqual(self.controller.integral, 0.0)
        self.assertIsNone(self.controller.last_time)
        self.assertEqual(self.controller.last_output, 0.0)
    
    def test_setpoint_adjustment(self):
        """Test setpoint changes"""
        self.controller.set_setpoint(6.0)
        self.assertEqual(self.controller.setpoint, 6.0)
        
        # Test plasma temperature setpoint
        self.controller.set_setpoint(-18.0)
        self.assertEqual(self.controller.setpoint, -18.0)
    
    def test_gain_adjustment(self):
        """Test PID gain adjustments"""
        new_gains = PIDGains(kp=2.0, ki=0.2, kd=0.1)
        self.controller.set_gains(new_gains)
        
        self.assertEqual(self.controller.gains.kp, 2.0)
        self.assertEqual(self.controller.gains.ki, 0.2)
        self.assertEqual(self.controller.gains.kd, 0.1)
    
    def test_mode_changes(self):
        """Test controller mode switching"""
        # Test manual mode
        self.controller.set_mode(ControllerMode.MANUAL)
        self.assertEqual(self.controller.mode, ControllerMode.MANUAL)
        
        # Test disabled mode (should reset controller)
        self.controller.integral = 5.0  # Set some state
        self.controller.set_mode(ControllerMode.DISABLED)
        self.assertEqual(self.controller.mode, ControllerMode.DISABLED)
        self.assertEqual(self.controller.integral, 0.0)  # Should be reset
    
    def test_proportional_control(self):
        """Test proportional term calculation"""
        # Mock time to control dt
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0.0, 1.0]  # 1 second time step
            
            # Large error should produce proportional response
            current_temp = 20.0  # 16°C above setpoint
            output = self.controller.update(current_temp, dt=1.0)
            
            # With kp=1.0, error=16°C, proportional term should dominate
            expected_proportional = self.gains.kp * (self.setpoint - current_temp)
            # Output should be close to proportional term (integral and derivative small)
            self.assertLess(output, 0)  # Should be cooling (negative)
            self.assertGreater(abs(output), 10)  # Should be significant response
    
    def test_integral_control(self):
        """Test integral term accumulation"""
        dt = 1.0
        steady_error_temp = 5.0  # 1°C above setpoint
        
        # Run several iterations with steady error
        outputs = []
        for i in range(5):
            output = self.controller.update(steady_error_temp, dt=dt)
            outputs.append(output)
        
        # Integral term should accumulate, making output more negative over time
        self.assertLess(outputs[-1], outputs[0])  # Later output should be more negative
        
        # Integral should have accumulated
        self.assertLess(self.controller.integral, -1.0)  # Negative integral
    
    def test_derivative_control(self):
        """Test derivative term response to changing error"""
        dt = 1.0
        
        # First update with large error
        output1 = self.controller.update(10.0, dt=dt)  # 6°C error
        
        # Second update with smaller error (fast improvement)
        output2 = self.controller.update(5.0, dt=dt)   # 1°C error
        
        # Derivative term should reduce output due to improving error
        # (Error decreased rapidly, so derivative should oppose further cooling)
        self.assertGreater(output2, output1)  # Less cooling due to derivative
    
    def test_output_limits(self):
        """Test output limiting"""
        # Test maximum cooling limit - need a bigger error to hit limits
        very_hot_temp = 200.0  # Much higher above setpoint to ensure saturation
        output = self.controller.update(very_hot_temp, dt=1.0)
        self.assertEqual(output, self.controller.output_min)  # Should hit min limit (-100W)
        
        # Reset controller and test heating limit
        self.controller.reset()
        very_cold_temp = -200.0  # Much lower below setpoint to ensure saturation
        output = self.controller.update(very_cold_temp, dt=1.0)
        self.assertEqual(output, self.controller.output_max)  # Should hit max limit (50W)
    
    def test_integral_windup_protection(self):
        """Test integral windup protection"""
        dt = 1.0
        very_hot_temp = 50.0  # Large persistent error
        
        # Run many iterations to try to cause windup
        for i in range(20):
            output = self.controller.update(very_hot_temp, dt=dt)
        
        # Output should still be at limit, not beyond
        self.assertEqual(output, self.output_limits[0])
        
        # Integral should be limited to prevent windup
        max_reasonable_integral = abs(self.output_limits[0] / self.gains.ki)
        self.assertLessEqual(abs(self.controller.integral), max_reasonable_integral * 1.1)
    
    def test_disabled_mode_output(self):
        """Test that disabled mode produces no output"""
        self.controller.set_mode(ControllerMode.DISABLED)
        
        output = self.controller.update(20.0, dt=1.0)  # Large error
        self.assertEqual(output, 0.0)  # Should produce no output
    
    def test_manual_mode_output(self):
        """Test that manual mode produces no automatic output"""
        self.controller.set_mode(ControllerMode.MANUAL)
        
        output = self.controller.update(20.0, dt=1.0)  # Large error
        self.assertEqual(output, 0.0)  # Should produce no automatic output
    
    def test_reset_functionality(self):
        """Test controller reset"""
        # Build up some controller state
        self.controller.update(10.0, dt=1.0)
        self.controller.update(8.0, dt=1.0)
        
        # Verify state exists
        self.assertNotEqual(self.controller.integral, 0.0)
        self.assertNotEqual(self.controller.last_error, 0.0)
        self.assertTrue(len(self.controller.error_history) > 0)
        
        # Reset and verify clean state
        self.controller.reset()
        
        self.assertEqual(self.controller.integral, 0.0)
        self.assertEqual(self.controller.last_error, 0.0)
        self.assertIsNone(self.controller.last_time)
        self.assertEqual(self.controller.last_output, 0.0)
        self.assertEqual(len(self.controller.error_history), 0)
        self.assertEqual(len(self.controller.output_history), 0)
    
    def test_zero_time_step_handling(self):
        """Test handling of zero or negative time steps"""
        # First normal update
        output1 = self.controller.update(10.0, dt=1.0)
        
        # Zero time step should return last output
        output2 = self.controller.update(8.0, dt=0.0)
        self.assertEqual(output2, output1)
        
        # Negative time step should return last output
        output3 = self.controller.update(6.0, dt=-1.0)
        self.assertEqual(output3, output1)


class TestControllerStatus(unittest.TestCase):
    """Test controller status and monitoring"""
    
    def setUp(self):
        """Set up test controller"""
        self.controller = PIDController(
            gains=PIDGains(kp=1.0, ki=0.1, kd=0.05),
            setpoint=4.0,
            output_limits=(-100.0, 50.0)
        )
    
    def test_status_reporting(self):
        """Test controller status dictionary"""
        # Run a few updates to build history
        self.controller.update(10.0, dt=1.0)
        self.controller.update(8.0, dt=1.0)
        
        status = self.controller.get_status()
        
        # Verify status structure
        self.assertIn('mode', status)
        self.assertIn('setpoint_c', status)
        self.assertIn('last_error_c', status)
        self.assertIn('integral_term', status)
        self.assertIn('last_output_w', status)
        self.assertIn('gains', status)
        self.assertIn('output_limits_w', status)
        self.assertIn('avg_recent_error_c', status)
        self.assertIn('performance', status)
        
        # Verify status values
        self.assertEqual(status['mode'], 'automatic')
        self.assertEqual(status['setpoint_c'], 4.0)
        self.assertEqual(status['output_limits_w'], (-100.0, 50.0))
        
        # Verify gain reporting
        gains = status['gains']
        self.assertEqual(gains['kp'], 1.0)
        self.assertEqual(gains['ki'], 0.1)
        self.assertEqual(gains['kd'], 0.05)
    
    def test_performance_metrics(self):
        """Test performance metric calculations"""
        # Run updates with known errors
        test_temps = [10.0, 8.0, 6.0, 5.0, 4.5]  # Approaching setpoint
        
        for temp in test_temps:
            self.controller.update(temp, dt=1.0)
        
        status = self.controller.get_status()
        performance = status['performance']
        
        # Verify performance metrics exist
        self.assertIn('sse', performance)
        self.assertIn('ise', performance)
        self.assertIn('max_error', performance)
        
        # Verify reasonable values
        self.assertGreater(performance['sse'], 0)  # Should have some error
        self.assertGreater(performance['max_error'], 0)  # Should have max error
        self.assertLess(performance['max_error'], 10)  # But not excessive
    
    def test_error_history_limiting(self):
        """Test that error history is limited to prevent memory issues"""
        # Run many updates to test history limiting
        for i in range(1200):  # More than the 1000 limit
            self.controller.update(5.0, dt=1.0)
        
        # History should be limited
        self.assertEqual(len(self.controller.error_history), 1000)
        self.assertEqual(len(self.controller.output_history), 1000)


class TestPredefinedControllers(unittest.TestCase):
    """Test predefined controller configurations"""
    
    def test_blood_storage_controller(self):
        """Test blood storage controller creation"""
        controller = create_blood_storage_controller(target_temp=4.0)
        
        self.assertEqual(controller.setpoint, 4.0)
        self.assertEqual(controller.gains.kp, 1.0)
        self.assertEqual(controller.gains.ki, 0.1)
        self.assertEqual(controller.gains.kd, 0.05)
        self.assertEqual(controller.output_min, -100.0)
        self.assertEqual(controller.output_max, 50.0)
    
    def test_plasma_controller(self):
        """Test plasma storage controller creation"""
        controller = create_plasma_controller(target_temp=-18.0)
        
        self.assertEqual(controller.setpoint, -18.0)
        self.assertEqual(controller.gains.kp, 2.0)  # More aggressive
        self.assertEqual(controller.gains.ki, 0.2)
        self.assertEqual(controller.gains.kd, 0.1)
        self.assertEqual(controller.output_min, -200.0)
        self.assertEqual(controller.output_max, 100.0)
    
    def test_platelet_controller(self):
        """Test platelet storage controller creation"""
        controller = create_platelet_controller(target_temp=22.0)
        
        self.assertEqual(controller.setpoint, 22.0)
        self.assertEqual(controller.gains.kp, 1.5)  # Moderate response
        self.assertEqual(controller.gains.ki, 0.15)
        self.assertEqual(controller.gains.kd, 0.075)
        self.assertEqual(controller.output_min, -75.0)
        self.assertEqual(controller.output_max, 75.0)


class TestTuningMethods(unittest.TestCase):
    """Test controller tuning helper methods"""
    
    def setUp(self):
        """Set up test controller"""
        self.controller = PIDController(
            gains=PIDGains(kp=1.0, ki=0.1, kd=0.05),
            setpoint=4.0
        )
    
    def test_aggressive_tuning(self):
        """Test aggressive tuning setting"""
        self.controller.tune_aggressive()
        
        self.assertEqual(self.controller.gains.kp, 3.0)
        self.assertEqual(self.controller.gains.ki, 0.5)
        self.assertEqual(self.controller.gains.kd, 0.2)
    
    def test_conservative_tuning(self):
        """Test conservative tuning setting"""
        self.controller.tune_conservative()
        
        self.assertEqual(self.controller.gains.kp, 0.5)
        self.assertEqual(self.controller.gains.ki, 0.05)
        self.assertEqual(self.controller.gains.kd, 0.01)
    
    def test_blood_storage_tuning(self):
        """Test blood storage specific tuning"""
        self.controller.tune_blood_storage()
        
        self.assertEqual(self.controller.gains.kp, 1.0)
        self.assertEqual(self.controller.gains.ki, 0.1)
        self.assertEqual(self.controller.gains.kd, 0.05)


class TestControllerScenarios(unittest.TestCase):
    """Test realistic control scenarios"""
    
    def test_setpoint_tracking(self):
        """Test controller tracking setpoint"""
        controller = create_blood_storage_controller(target_temp=4.0)
        
        # Simulate temperature starting above setpoint and being controlled
        current_temp = 20.0
        dt = 1.0
        
        temperatures = [current_temp]
        outputs = []
        
        # Simulate simple first-order response to controller output
        for i in range(60):  # 60 seconds for more time to respond
            output = controller.update(current_temp, dt=dt)
            outputs.append(output)
            
            # Simple thermal response model with ambient losses
            # dT/dt = (-output - ambient_losses) / thermal_mass
            thermal_mass = 2000.0  # J/K
            ambient_temp = 4.0  # Refrigerator ambient
            ambient_loss_coeff = 10.0  # Heat loss to ambient (W/K)
            ambient_losses = ambient_loss_coeff * (current_temp - ambient_temp)
            
            total_heat = -output - ambient_losses
            temp_change = total_heat * dt / thermal_mass
            current_temp += temp_change
            temperatures.append(current_temp)
        
        # Controller should drive temperature toward setpoint
        final_temp = temperatures[-1]
        initial_temp = temperatures[0]
        
        self.assertLess(final_temp, initial_temp)  # Should cool
        self.assertLess(abs(final_temp - 4.0), abs(initial_temp - 4.0))  # Closer to setpoint
    
    def test_disturbance_rejection(self):
        """Test controller response to disturbances"""
        controller = create_blood_storage_controller(target_temp=4.0)
        
        # Start at setpoint
        current_temp = 4.0
        dt = 1.0
        
        # Apply disturbance (door opening, warm air)
        disturbance_heat = 20.0  # W of heating disturbance
        thermal_mass = 2000.0  # J/K
        
        outputs = []
        temperatures = [current_temp]
        
        for i in range(20):
            output = controller.update(current_temp, dt=dt)
            outputs.append(output)
            
            # Apply both controller output and disturbance
            total_heat = -output + disturbance_heat
            temp_change = total_heat * dt / thermal_mass
            current_temp += temp_change
            temperatures.append(current_temp)
        
        # Controller should compensate for disturbance
        # Output should become increasingly negative to counter heating
        self.assertLess(outputs[-1], outputs[0])  # More cooling over time
        
        # Temperature should not rise excessively
        max_temp = max(temperatures)
        self.assertLess(max_temp, 8.0)  # Should keep under reasonable limit
    
    def test_plasma_freezing_scenario(self):
        """Test plasma controller for freezing scenario"""
        controller = create_plasma_controller(target_temp=-18.0)
        
        # Start at room temperature
        current_temp = 20.0
        dt = 5.0  # 5 second steps for faster freezing
        thermal_mass = 800.0  # Smaller thermal mass for faster response
        
        temperatures = [current_temp]
        
        for i in range(120):  # 10 minutes (more time for freezing)
            output = controller.update(current_temp, dt=dt)
            
            # More realistic cooling with ambient losses
            ambient_temp = -18.0  # Freezer ambient temperature
            ambient_loss_coeff = 5.0  # Heat transfer to ambient (W/K)
            ambient_losses = ambient_loss_coeff * (current_temp - ambient_temp)
            
            # Total heat removal (controller output + ambient losses)
            total_heat = -output - ambient_losses
            temp_change = total_heat * dt / thermal_mass
            current_temp += temp_change
            temperatures.append(current_temp)
            
            # Stop if target reached
            if current_temp <= -18.0:
                break
        
        final_temp = temperatures[-1]
        
        # Should reach freezing temperatures
        self.assertLess(final_temp, 0.0)  # Below freezing
        self.assertLess(final_temp, temperatures[0])  # Significant cooling


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def test_extreme_temperatures(self):
        """Test controller with extreme temperature inputs"""
        controller = PIDController(
            gains=PIDGains(kp=1.0, ki=0.1, kd=0.05),
            setpoint=4.0,
            output_limits=(-100.0, 50.0)
        )
        
        # Test very hot temperature
        output_hot = controller.update(100.0, dt=1.0)
        self.assertEqual(output_hot, -100.0)  # Should hit cooling limit
        
        # Reset and test very cold temperature
        controller.reset()
        output_cold = controller.update(-50.0, dt=1.0)
        self.assertEqual(output_cold, 50.0)  # Should hit heating limit
    
    def test_zero_gains(self):
        """Test controller with zero gains"""
        controller = PIDController(
            gains=PIDGains(kp=0.0, ki=0.0, kd=0.0),
            setpoint=4.0
        )
        
        output = controller.update(20.0, dt=1.0)  # Large error
        self.assertEqual(output, 0.0)  # No gains = no output
    
    def test_very_small_time_steps(self):
        """Test controller with very small time steps"""
        controller = PIDController(
            gains=PIDGains(kp=1.0, ki=0.1, kd=0.05),
            setpoint=4.0
        )
        
        # Very small time step
        output = controller.update(10.0, dt=0.001)
        self.assertIsInstance(output, float)
        self.assertGreater(abs(output), 0)  # Should still produce output
    
    def test_setpoint_at_temperature_limits(self):
        """Test setpoints at extreme temperatures"""
        # Very low setpoint (liquid nitrogen range)
        controller_cold = PIDController(
            gains=PIDGains(kp=1.0, ki=0.1, kd=0.05),
            setpoint=-196.0  # Liquid nitrogen
        )
        
        output = controller_cold.update(20.0, dt=1.0)
        self.assertLess(output, 0)  # Should call for cooling
        
        # Very high setpoint
        controller_hot = PIDController(
            gains=PIDGains(kp=1.0, ki=0.1, kd=0.05),
            setpoint=100.0  # Boiling water
        )
        
        output = controller_hot.update(20.0, dt=1.0)
        self.assertGreater(output, 0)  # Should call for heating


if __name__ == '__main__':
    # Run all tests with detailed output
    unittest.main(verbosity=2)