#!/usr/bin/env python3
"""
Smart Thermal Control System - Educational Dashboard Server
Flask web server that bridges the educational dashboard to the control system
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Add the project root to Python path for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import with absolute paths
try:
    from ..control.control_interface import create_blood_storage_control_system, ControlMode
    from ..thermal_model.heat_transfer_data import MaterialLibrary
    from ..control.pid_controller import PIDGains
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

class DashboardServer:
    """Educational Dashboard Server integrating with thermal control system"""
    
    def __init__(self):
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'educational_dashboard_2024'
        
        # Enable CORS for development
        CORS(self.app, origins=["http://localhost:*", "http://127.0.0.1:*"])
        
        # Initialize SocketIO for real-time updates
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Control system instance
        self.control_system = None
        self.system_running = False
        
        # Data storage for dashboard
        self.status_history = []
        self.max_history_length = 1000
        
        # Thread control
        self.update_thread = None
        self.should_stop = False
        
        # Educational features
        self.learning_sessions = {}
        self.experiment_results = []
        
        self.setup_routes()
        self.setup_socketio_events()
        
    def initialize_control_system(self, blood_product_type='WHOLE_BLOOD'):
        """Initialize the thermal control system"""
        try:
            print(f"Initializing control system for {blood_product_type}...")
            
            # Select blood product
            blood_products = {
                'WHOLE_BLOOD': MaterialLibrary.WHOLE_BLOOD,
                'PLASMA': MaterialLibrary.PLASMA,
                'PLATELETS': MaterialLibrary.PLATELETS
            }
            
            blood_product = blood_products.get(blood_product_type, MaterialLibrary.WHOLE_BLOOD)
            
            # Create control system
            self.control_system = create_blood_storage_control_system(
                blood_product=blood_product,
                container_material=MaterialLibrary.STAINLESS_STEEL_316,
                volume_liters=2.0,
                container_mass_kg=1.5
            )
            
            # Start the system
            result = self.control_system.start_system(initial_temperature=20.0)
            self.system_running = True
            
            print(f"Control system initialized: {result}")
            return True
            
        except Exception as e:
            print(f"Failed to initialize control system: {e}")
            return False
    
    def setup_routes(self):
        """Setup Flask REST API routes"""
        
        @self.app.route('/')
        def serve_dashboard():
            """Serve the main dashboard HTML"""
            return send_from_directory('.', 'index.html')
        
        @self.app.route('/<path:path>')
        def serve_static(path):
            """Serve static files (CSS, JS, etc.)"""
            return send_from_directory('.', path)
        
        @self.app.route('/api/status', methods=['GET'])
        def get_system_status():
            """Get current system status"""
            try:
                if not self.control_system or not self.system_running:
                    return jsonify({
                        'error': 'System not initialized',
                        'system_running': False
                    }), 400
                
                # Get status from control system
                status = self.control_system.get_status()
                
                # Add timestamp and educational context
                enhanced_status = self.enhance_status_for_education(status)
                
                # Store in history
                self.add_to_history(enhanced_status)
                
                return jsonify(enhanced_status)
                
            except Exception as e:
                print(f"Error getting status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/initialize', methods=['POST'])
        def initialize_system():
            """Initialize the control system"""
            try:
                data = request.get_json() or {}
                blood_product = data.get('blood_product', 'WHOLE_BLOOD')
                
                success = self.initialize_control_system(blood_product)
                
                if success:
                    # Start the real-time update thread
                    self.start_update_thread()
                    
                    return jsonify({
                        'success': True,
                        'message': 'System initialized successfully',
                        'blood_product': blood_product
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Failed to initialize system'
                    }), 500
                    
            except Exception as e:
                print(f"Initialization error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/set_gains', methods=['POST'])
        def set_pid_gains():
            """Set PID controller gains"""
            try:
                if not self.control_system or not self.system_running:
                    return jsonify({'error': 'System not running'}), 400
                
                data = request.get_json()
                kp = float(data.get('kp', 1.0))
                ki = float(data.get('ki', 0.1))
                kd = float(data.get('kd', 0.05))
                
                # Validate gains for safety
                if not self.validate_gains(kp, ki, kd):
                    return jsonify({
                        'error': 'Invalid gains - would compromise safety',
                        'limits': {
                            'kp': '0.1 - 10.0',
                            'ki': '0.0 - 2.0', 
                            'kd': '0.0 - 1.0'
                        }
                    }), 400
                
                # Set gains in control system
                gains = PIDGains(kp=kp, ki=ki, kd=kd)
                self.control_system.pid_controller.set_gains(gains)
                
                # Log educational activity
                self.log_educational_activity('pid_tuning', {
                    'kp': kp, 'ki': ki, 'kd': kd,
                    'timestamp': datetime.now().isoformat()
                })
                
                return jsonify({
                    'success': True,
                    'gains': {'kp': kp, 'ki': ki, 'kd': kd}
                })
                
            except Exception as e:
                print(f"Error setting gains: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/set_target', methods=['POST'])
        def set_target_temperature():
            """Set target temperature"""
            try:
                if not self.control_system or not self.system_running:
                    return jsonify({'error': 'System not running'}), 400
                
                data = request.get_json()
                target = float(data.get('temperature'))
                
                # Validate temperature for safety
                blood_product = self.control_system.blood_product
                if not (blood_product.critical_temp_low_c <= target <= blood_product.critical_temp_high_c):
                    return jsonify({
                        'error': f'Temperature outside safe range: {blood_product.critical_temp_low_c} to {blood_product.critical_temp_high_c}°C'
                    }), 400
                
                # Set target temperature
                success = self.control_system.set_target_temperature(target)
                
                if success:
                    self.log_educational_activity('setpoint_change', {
                        'target': target,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return jsonify({
                        'success': True,
                        'target_temperature': target
                    })
                else:
                    return jsonify({'error': 'Failed to set temperature'}), 500
                    
            except Exception as e:
                print(f"Error setting target: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/control_mode', methods=['POST'])
        def set_control_mode():
            """Set control mode (automatic, manual, etc.)"""
            try:
                if not self.control_system or not self.system_running:
                    return jsonify({'error': 'System not running'}), 400
                
                data = request.get_json()
                mode_str = data.get('mode', 'automatic').upper()
                
                # Convert string to ControlMode enum
                mode_map = {
                    'AUTOMATIC': ControlMode.AUTOMATIC,
                    'MANUAL': ControlMode.MANUAL,
                    'EMERGENCY': ControlMode.EMERGENCY,
                    'MAINTENANCE': ControlMode.MAINTENANCE
                }
                
                mode = mode_map.get(mode_str)
                if not mode:
                    return jsonify({'error': f'Invalid mode: {mode_str}'}), 400
                
                success = self.control_system.set_control_mode(mode)
                
                return jsonify({
                    'success': success,
                    'mode': mode_str.lower()
                })
                
            except Exception as e:
                print(f"Error setting control mode: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trigger_disturbance', methods=['POST'])
        def trigger_disturbance():
            """Trigger a disturbance for educational purposes"""
            try:
                if not self.control_system or not self.system_running:
                    return jsonify({'error': 'System not running'}), 400
                
                data = request.get_json() or {}
                magnitude = float(data.get('magnitude', 2.0))
                
                # Apply disturbance by temporarily changing temperature
                current_temp = self.control_system.get_current_temperature()
                new_temp = current_temp + magnitude
                
                # Set the disturbance (this would normally be external)
                self.control_system.thermal_system.current_state.blood_temperature = new_temp
                
                self.log_educational_activity('disturbance', {
                    'magnitude': magnitude,
                    'timestamp': datetime.now().isoformat()
                })
                
                return jsonify({
                    'success': True,
                    'disturbance_magnitude': magnitude,
                    'message': f'Applied {magnitude}°C disturbance'
                })
                
            except Exception as e:
                print(f"Error triggering disturbance: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/experiments/<experiment_type>', methods=['POST'])
        def run_experiment(experiment_type):
            """Run educational experiments"""
            try:
                if not self.control_system or not self.system_running:
                    return jsonify({'error': 'System not running'}), 400
                
                experiment_result = self.execute_experiment(experiment_type)
                
                return jsonify({
                    'success': True,
                    'experiment': experiment_type,
                    'result': experiment_result
                })
                
            except Exception as e:
                print(f"Error running experiment: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/history', methods=['GET'])
        def get_status_history():
            """Get historical status data"""
            try:
                # Get query parameters
                limit = int(request.args.get('limit', 100))
                start_time = request.args.get('start_time')
                
                history = self.status_history[-limit:]
                
                if start_time:
                    start_timestamp = datetime.fromisoformat(start_time).timestamp()
                    history = [s for s in history if s.get('timestamp', 0) >= start_timestamp]
                
                return jsonify({
                    'history': history,
                    'total_points': len(self.status_history)
                })
                
            except Exception as e:
                print(f"Error getting history: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/shutdown', methods=['POST'])
        def shutdown_system():
            """Shutdown the control system"""
            try:
                if self.control_system and self.system_running:
                    result = self.control_system.stop_system()
                    self.system_running = False
                    self.stop_update_thread()
                    
                    return jsonify({
                        'success': True,
                        'message': 'System shutdown successfully',
                        'result': result
                    })
                else:
                    return jsonify({'success': True, 'message': 'System already stopped'})
                    
            except Exception as e:
                print(f"Error shutting down: {e}")
                return jsonify({'error': str(e)}), 500
    
    def setup_socketio_events(self):
        """Setup SocketIO events for real-time communication"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print('Dashboard client connected')
            emit('connection_status', {'status': 'connected', 'system_running': self.system_running})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Dashboard client disconnected')
        
        @self.socketio.on('request_status')
        def handle_status_request():
            """Handle real-time status requests"""
            if self.control_system and self.system_running:
                try:
                    status = self.control_system.get_status()
                    enhanced_status = self.enhance_status_for_education(status)
                    emit('status_update', enhanced_status)
                except Exception as e:
                    emit('error', {'message': str(e)})
    
    def enhance_status_for_education(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance status data with educational context"""
        try:
            enhanced = status.copy()
            enhanced['timestamp'] = time.time()
            enhanced['timestamp_iso'] = datetime.now().isoformat()
            
            # Add educational context
            current_temp = status.get('current_temperature_c', 4.0)
            target_temp = status.get('target_temperature_c', 4.0)
            error = target_temp - current_temp
            
            # Calculate PID terms if available
            pid_status = status.get('pid_controller', {})
            
            enhanced['educational_context'] = {
                'error': error,
                'abs_error': abs(error),
                'error_percentage': (abs(error) / target_temp) * 100 if target_temp != 0 else 0,
                'control_quality': self.assess_control_quality(error, pid_status),
                'learning_opportunities': self.identify_learning_opportunities(status)
            }
            
            return enhanced
            
        except Exception as e:
            print(f"Error enhancing status: {e}")
            return status
    
    def assess_control_quality(self, error: float, pid_status: Dict) -> str:
        """Assess current control performance for educational feedback"""
        abs_error = abs(error)
        
        if abs_error < 0.1:
            return 'excellent'
        elif abs_error < 0.5:
            return 'good'
        elif abs_error < 1.0:
            return 'moderate'
        else:
            return 'poor'
    
    def identify_learning_opportunities(self, status: Dict) -> list:
        """Identify educational concepts relevant to current system state"""
        opportunities = []
        
        # Get current values
        current_temp = status.get('current_temperature_c', 4.0)
        target_temp = status.get('target_temperature_c', 4.0)
        safety_level = status.get('safety', {}).get('safety_level', 'SAFE')
        
        error = abs(target_temp - current_temp)
        
        # Identify relevant concepts
        if error > 1.0:
            opportunities.append('proportional_control')
        if error > 0.1:
            opportunities.append('steady_state_error')
        if safety_level != 'SAFE':
            opportunities.append('safety_systems')
        
        return opportunities
    
    def validate_gains(self, kp: float, ki: float, kd: float) -> bool:
        """Validate PID gains for safety"""
        return (0.1 <= kp <= 10.0 and 
                0.0 <= ki <= 2.0 and 
                0.0 <= kd <= 1.0)
    
    def execute_experiment(self, experiment_type: str) -> Dict[str, Any]:
        """Execute educational experiments"""
        experiments = {
            'overshoot': self.experiment_overshoot,
            'steady_state': self.experiment_steady_state,
            'oscillation': self.experiment_oscillation,
            'disturbance_response': self.experiment_disturbance_response
        }
        
        experiment_func = experiments.get(experiment_type)
        if experiment_func:
            return experiment_func()
        else:
            return {'error': f'Unknown experiment: {experiment_type}'}
    
    def experiment_overshoot(self) -> Dict[str, Any]:
        """Demonstrate overshoot with high Kp"""
        # Set aggressive gains
        gains = PIDGains(kp=4.0, ki=0.1, kd=0.0)
        self.control_system.pid_controller.set_gains(gains)
        
        # Trigger setpoint change
        original_target = self.control_system.get_current_temperature()
        new_target = original_target + 2.0
        self.control_system.set_target_temperature(new_target)
        
        return {
            'description': 'High Kp gain demonstration',
            'gains': {'kp': 4.0, 'ki': 0.1, 'kd': 0.0},
            'expected_result': 'Watch for overshoot and oscillation',
            'learning_objective': 'Understanding the effect of proportional gain'
        }
    
    def experiment_steady_state(self) -> Dict[str, Any]:
        """Demonstrate steady-state error with Ki=0"""
        # Set P-only control
        gains = PIDGains(kp=1.0, ki=0.0, kd=0.05)
        self.control_system.pid_controller.set_gains(gains)
        
        return {
            'description': 'P-only control demonstration',
            'gains': {'kp': 1.0, 'ki': 0.0, 'kd': 0.05},
            'expected_result': 'System may not reach exact setpoint',
            'learning_objective': 'Understanding the need for integral control'
        }
    
    def experiment_oscillation(self) -> Dict[str, Any]:
        """Demonstrate oscillation with excessive gains"""
        # Set unstable gains
        gains = PIDGains(kp=5.0, ki=0.8, kd=0.0)
        self.control_system.pid_controller.set_gains(gains)
        
        return {
            'description': 'Excessive gain demonstration',
            'gains': {'kp': 5.0, 'ki': 0.8, 'kd': 0.0},
            'expected_result': 'System will oscillate around setpoint',
            'learning_objective': 'Understanding system stability and the need for proper tuning'
        }
    
    def experiment_disturbance_response(self) -> Dict[str, Any]:
        """Demonstrate disturbance rejection"""
        # Apply disturbance
        current_temp = self.control_system.get_current_temperature()
        self.control_system.thermal_system.current_state.blood_temperature = current_temp + 2.0
        
        return {
            'description': 'Disturbance rejection demonstration',
            'disturbance': '+2.0°C temperature step',
            'expected_result': 'Controller will work to reject the disturbance',
            'learning_objective': 'Understanding how controllers respond to external disturbances'
        }
    
    def log_educational_activity(self, activity_type: str, data: Dict[str, Any]):
        """Log educational activities for analytics"""
        log_entry = {
            'type': activity_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        # In a real system, this would go to a database
        print(f"Educational Activity: {log_entry}")
    
    def add_to_history(self, status: Dict[str, Any]):
        """Add status to history with size limiting"""
        self.status_history.append(status)
        
        if len(self.status_history) > self.max_history_length:
            self.status_history.pop(0)
    
    def start_update_thread(self):
        """Start the real-time update thread"""
        if self.update_thread and self.update_thread.is_alive():
            return
        
        self.should_stop = False
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        print("Started real-time update thread")
    
    def stop_update_thread(self):
        """Stop the real-time update thread"""
        self.should_stop = True
        if self.update_thread:
            self.update_thread.join(timeout=2.0)
        print("Stopped real-time update thread")
    

    def update_loop(self):
        """Main update loop for real-time data with enhanced thermal integration"""
        print("Starting enhanced update loop with thermal integration...")
        
        while not self.should_stop and self.system_running:
            try:
                if self.control_system:
                    # CRITICAL FIX: Force the control system to actually calculate and apply thermal power
                    
                    # Get current temperature BEFORE update
                    temp_before = self.control_system.get_current_temperature()
                    
                    # Force PID calculation with manual thermal power application
                    current_temp = self.control_system.get_current_temperature()
                    target_temp = self.control_system.config.target_temperature
                    
                    # Manual PID calculation to ensure it works
                    error = target_temp - current_temp
                    
                    # Get PID gains
                    kp = self.control_system.pid_controller.gains.kp
                    ki = self.control_system.pid_controller.gains.ki  
                    kd = self.control_system.pid_controller.gains.kd
                    
                    # Calculate PID output manually to ensure it works
                    dt = 1.0  # 1 second time step
                    
                    # Proportional term
                    p_term = kp * error
                    
                    # Integral term (simplified)
                    if not hasattr(self, '_integral_accumulator'):
                        self._integral_accumulator = 0.0
                    self._integral_accumulator += error * dt
                    # Prevent windup
                    self._integral_accumulator = max(-50.0, min(50.0, self._integral_accumulator))
                    i_term = ki * self._integral_accumulator
                    
                    # Derivative term
                    if not hasattr(self, '_last_error'):
                        self._last_error = error
                    d_term = kd * (error - self._last_error) / dt
                    self._last_error = error
                    
                    # Total PID output
                    pid_output = p_term + i_term + d_term
                    
                    # Limit output to reasonable range
                    pid_output = max(-100.0, min(100.0, pid_output))
                    
                    print(f"Manual PID Debug: Temp={current_temp:.2f}°C, Target={target_temp:.2f}°C, Error={error:.2f}°C, Output={pid_output:.1f}W")
                    
                    # FORCE thermal power application directly to the thermal system
                    if hasattr(self.control_system, 'thermal_system'):
                        # Apply power directly to thermal system
                        actual_power = self.control_system.thermal_system.apply_thermal_power(pid_output)
                        print(f"Applied thermal power: {actual_power:.1f}W")
                        
                        # Force thermal system step
                        new_state = self.control_system.thermal_system.step(dt)
                        print(f"Thermal step result: {new_state}")
                        
                        # Get temperature after thermal step
                        temp_after = self.control_system.get_current_temperature()
                        temp_change = temp_after - temp_before
                        print(f"Temperature change: {temp_change:.4f}°C (from {temp_before:.2f} to {temp_after:.2f})")
                    
                    # Also run the normal control system update
                    self.control_system.update(dt=dt)
                    
                    # Get enhanced status
                    status = self.control_system.get_status()
                    enhanced_status = self.enhance_status_for_education(status)
                    
                    # Force update the PID terms in status for display
                    enhanced_status['pid_controller']['p_term'] = p_term
                    enhanced_status['pid_controller']['i_term'] = i_term  
                    enhanced_status['pid_controller']['d_term'] = d_term
                    enhanced_status['pid_controller']['last_output_w'] = pid_output
                    
                    # Add thermal debugging info
                    enhanced_status['thermal_debug'] = {
                        'temperature_before': temp_before,
                        'temperature_after': self.control_system.get_current_temperature(),
                        'temperature_change': self.control_system.get_current_temperature() - temp_before,
                        'applied_power': pid_output,
                        'manual_calculation': True
                    }
                    
                    # Add to history
                    self.add_to_history(enhanced_status)
                    
                    # Emit to all connected clients
                    self.socketio.emit('status_update', enhanced_status)
                    
                    # Debug output every 5 seconds
                    if not hasattr(self, '_debug_counter'):
                        self._debug_counter = 0
                    self._debug_counter += 1
                    
                    if self._debug_counter % 5 == 0:
                        print(f"System Status - Temp: {current_temp:.2f}°C, Target: {target_temp:.2f}°C, Output: {pid_output:.1f}W")
                    
                time.sleep(1.0)  # Update every second
                
            except Exception as e:
                print(f"Error in enhanced update loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5.0)  # Wait longer if there's an error


    # Also add this method to check thermal system state
    def debug_thermal_system(self):
        """Debug the thermal system to see what's happening"""
        if self.control_system and hasattr(self.control_system, 'thermal_system'):
            ts = self.control_system.thermal_system
            
            print("=== THERMAL SYSTEM DEBUG ===")
            print(f"Current temperature: {ts.get_current_temperature():.2f}°C")
            
            if hasattr(ts, 'current_state'):
                print(f"Blood temperature: {ts.current_state.blood_temperature:.2f}°C")
                print(f"Container temperature: {ts.current_state.container_temperature:.2f}°C")
                print(f"Ambient temperature: {ts.current_state.ambient_temperature:.2f}°C")
            
            if hasattr(ts, 'actuator_limits'):
                print(f"Max heating power: {ts.actuator_limits.max_heating_power}W")
                print(f"Max cooling power: {ts.actuator_limits.max_cooling_power}W")
            
            # Try to apply a test thermal power
            print("Testing thermal power application...")
            test_temp_before = ts.get_current_temperature()
            test_power = 50.0  # 50W heating
            actual_power = ts.apply_thermal_power(test_power)
            ts.step(1.0)  # 1 second step
            test_temp_after = ts.get_current_temperature()
            
            print(f"Test: {test_power}W → {actual_power}W applied")
            print(f"Temperature change: {test_temp_before:.2f}°C → {test_temp_after:.2f}°C ({test_temp_after - test_temp_before:.4f}°C)")
            print("=== END DEBUG ===")
            
            return {
                'before': test_temp_before,
                'after': test_temp_after,
                'change': test_temp_after - test_temp_before,
                'power_applied': actual_power
            }
        else:
            print("No thermal system found!")
            return None


    # Add this route to your DashboardServer for debugging
    def setup_debug_routes(self):
        """Add debug routes to diagnose thermal issues"""
        
        @self.app.route('/api/debug/thermal', methods=['GET'])
        def debug_thermal():
            """Debug thermal system state"""
            try:
                result = self.debug_thermal_system()
                return jsonify({
                    'success': True,
                    'debug_result': result,
                    'thermal_system_exists': hasattr(self.control_system, 'thermal_system') if self.control_system else False,
                    'system_running': self.system_running
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/debug/force_temp_change', methods=['POST'])
        def force_temp_change():
            """Force a temperature change for testing"""
            try:
                data = request.get_json() or {}
                power = float(data.get('power', 50.0))
                duration = float(data.get('duration', 5.0))
                
                if not self.control_system:
                    return jsonify({'error': 'System not running'}), 400
                
                print(f"Forcing temperature change with {power}W for {duration}s...")
                
                temp_before = self.control_system.get_current_temperature()
                
                # Apply power for specified duration
                for i in range(int(duration)):
                    actual_power = self.control_system.thermal_system.apply_thermal_power(power)
                    self.control_system.thermal_system.step(1.0)
                    time.sleep(0.1)  # Small delay
                
                temp_after = self.control_system.get_current_temperature()
                
                return jsonify({
                    'success': True,
                    'power_applied': power,
                    'duration': duration,
                    'temperature_before': temp_before,
                    'temperature_after': temp_after,
                    'temperature_change': temp_after - temp_before
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the dashboard server"""
        print(f"Starting Educational Dashboard Server...")
        print(f"Dashboard will be available at: http://{host}:{port}")
        print(f"Educational features enabled")
        print(f"Debug mode: {debug}")
        
        try:
            self.socketio.run(
                self.app, 
                host=host, 
                port=port, 
                debug=debug,
                allow_unsafe_werkzeug=True  # For development only
            )
        except KeyboardInterrupt:
            print("\nShutting down server...")
            self.stop_update_thread()
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            if self.control_system and self.system_running:
                self.control_system.stop_system()

def main():
    """Main entry point"""
    server = DashboardServer()
    
    # Run the server
    server.run(
        host='127.0.0.1',  # Localhost only for development
        port=5000,
        debug=True  # Enable debug mode for development
    )

if __name__ == '__main__':
    main()