/**
 * Enhanced Dashboard.js - Fixes for chart time display and responsiveness
 * 
 * CHANGES MADE:
 * 1. Fixed target temperature simulation to use current slider value
 * 2. Added faster data generation (500ms instead of 1000ms)
 * 3. Enhanced slider event handling for real-time feedback
 * 4. Improved chart data flow
 * 5. Added proper time scale handling for chart
 */

class ThermalControlDashboard {
    constructor() {
        this.isConnected = false;
        this.currentData = {
            temperature: 4.2,
            target: 4.0,
            output: -15,
            safety_level: 'SAFE',
            alarm_count: 0,
            control_mode: 'Automatic',
            pid_terms: { p: -0.8, i: -0.2, d: 0.1 },
            error: 0.2
        };
        
        this.updateInterval = null;
        this.simulationInterval = null; // Add separate simulation interval
        this.chartTimeScale = 60; // seconds
        this.sliderTimeout = null; // For auto-setting after delay
        this.init();
    }

    init() {
        console.log('🚀 Initializing Educational Dashboard...');
        
        // Initialize components
        this.setupEventListeners();
        this.initializeTooltips();
        this.startDataSimulation();
        
        // Start the main update loop
        this.startUpdateLoop();
        
        console.log('✅ Dashboard initialized successfully!');
    }

    setupEventListeners() {
        // Window resize handler
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // Chart controls
        document.getElementById('show-setpoint')?.addEventListener('change', (e) => {
            if (window.temperatureChart) {
                window.temperatureChart.toggleSetpoint(e.target.checked);
            }
        });

        document.getElementById('show-error')?.addEventListener('change', (e) => {
            if (window.temperatureChart) {
                window.temperatureChart.toggleError(e.target.checked);
            }
        });

        document.getElementById('show-output')?.addEventListener('change', (e) => {
            if (window.temperatureChart) {
                window.temperatureChart.toggleOutput(e.target.checked);
            }
        });

        // Safety status click for educational info
        document.getElementById('safety-status')?.addEventListener('click', () => {
            this.showSafetyEducation();
        });

        // System status items click for explanations
        document.querySelectorAll('.status-item').forEach(item => {
            item.addEventListener('click', () => {
                this.explainStatusItem(item);
            });
        });

        // Enhanced target temperature slider with real-time feedback
        this.setupTargetSlider();
    }

    setupTargetSlider() {
        const targetSlider = document.getElementById('target-slider');
        const targetDisplay = document.getElementById('target-temp');
        
        if (!targetSlider || !targetDisplay) return;

        // Real-time update while dragging
        targetSlider.addEventListener('input', (e) => {
            const newTarget = parseFloat(e.target.value);
            
            // Update display immediately with visual feedback
            targetDisplay.textContent = newTarget.toFixed(1);
            targetDisplay.style.color = 'var(--edu-primary, #6366f1)';
            targetDisplay.style.fontWeight = '800';
            targetDisplay.style.textShadow = '0 0 8px rgba(99, 102, 241, 0.5)';
            
            // Update the actual target in simulation immediately
            this.currentData.target = newTarget;
            
            console.log(`🎯 Target temperature slider moved to: ${newTarget}°C`);
            
            // Clear any existing timeout
            if (this.sliderTimeout) {
                clearTimeout(this.sliderTimeout);
            }
        });

        // Handle slider release/change
        targetSlider.addEventListener('change', (e) => {
            const finalTarget = parseFloat(e.target.value);
            
            // Reset styling after a brief delay
            setTimeout(() => {
                targetDisplay.style.color = '';
                targetDisplay.style.fontWeight = '';
                targetDisplay.style.textShadow = '';
            }, 500);
            
            console.log(`🎯 Slider released at: ${finalTarget}°C`);
        });

        // Initialize display with current slider value
        const currentValue = parseFloat(targetSlider.value);
        targetDisplay.textContent = currentValue.toFixed(1);
        this.currentData.target = currentValue; // Make sure data matches slider
    }

    initializeTooltips() {
        const tooltip = document.getElementById('tooltip');
        const helpIcons = document.querySelectorAll('[data-tooltip]');

        helpIcons.forEach(icon => {
            icon.addEventListener('mouseenter', (e) => {
                const text = e.target.getAttribute('data-tooltip');
                tooltip.textContent = text;
                tooltip.classList.add('visible');
                
                const rect = e.target.getBoundingClientRect();
                tooltip.style.left = rect.left + 'px';
                tooltip.style.top = (rect.bottom + 10) + 'px';
            });

            icon.addEventListener('mouseleave', () => {
                tooltip.classList.remove('visible');
            });
        });
    }

    startDataSimulation() {
        // Use real data connector instead of simulation
        console.log('🔗 Connecting to real control system...');
        
        // Set up data connector callbacks
        if (window.dataConnector) {
            window.dataConnector.onStatusUpdate((data) => {
                this.handleRealSystemData(data);
            });
            
            window.dataConnector.onConnectionChange((status) => {
                this.handleConnectionChange(status);
            });
            
            window.dataConnector.onError((error) => {
                console.error('🔌 Data connector error:', error);
            });
        } else {
            console.warn('⚠️ Data connector not available, falling back to enhanced simulation');
            this.startEnhancedSimulation();
        }
    }

    handleRealSystemData(data) {
        try {
            // Update current data from real system
            this.currentData.temperature = data.current_temperature_c || 4.0;
            this.currentData.target = data.target_temperature_c || 4.0;
            this.currentData.output = data.pid_controller?.last_output_w || 0;
            this.currentData.safety_level = data.safety?.safety_level || 'SAFE';
            this.currentData.alarm_count = data.safety?.active_alarms?.length || 0;
            this.currentData.control_mode = data.control_mode || 'automatic';
            
            // Update PID terms if available
            if (data.pid_controller) {
                this.currentData.pid_terms.p = data.pid_controller.p_term || 0;
                this.currentData.pid_terms.i = data.pid_controller.i_term || 0;
                this.currentData.pid_terms.d = data.pid_controller.d_term || 0;
            }
            
            // Calculate error
            this.currentData.error = this.currentData.target - this.currentData.temperature;
            
            // Update educational context if available
            if (data.educational_context) {
                this.updateEducationalMetrics(data.educational_context);
            }
            
        } catch (error) {
            console.error('❌ Error processing real system data:', error);
        }
    }

    handleConnectionChange(status) {
        const connectionIndicator = document.getElementById('connection-status');
        if (connectionIndicator) {
            connectionIndicator.textContent = status === 'connected' ? 'Connected' : 'Disconnected';
            connectionIndicator.className = `connection-status ${status}`;
        }
        
        if (status === 'disconnected') {
            console.warn('⚠️ Lost connection to control system, falling back to simulation');
            this.startEnhancedSimulation();
        }
    }

    updateEducationalMetrics(context) {
        // Update educational content based on real system analysis
        if (context.learning_opportunities && context.learning_opportunities.length > 0) {
            this.currentLearningOpportunities = context.learning_opportunities;
        }
        
        if (context.control_quality) {
            this.currentControlQuality = context.control_quality;
        }
    }

    startSimulation() {
        // Legacy method - redirect to enhanced simulation
        this.startEnhancedSimulation();
    }

    startEnhancedSimulation() {
        // Enhanced simulation with faster updates for better responsiveness
        console.log('🔄 Starting enhanced data simulation...');
        
        // Clear any existing simulation
        if (this.simulationInterval) {
            clearInterval(this.simulationInterval);
        }
        
        // Generate data every 500ms instead of 1000ms for faster response
        this.simulationInterval = setInterval(() => {
            this.simulateRealisticData();
        }, 500);
    }

    simulateRealisticData() {
        // Enhanced simulation with proper target tracking from slider
        const dt = 0.5; // 500ms = 0.5 seconds
        
        // Get target from current slider value (this was the key fix!)
        const slider = document.getElementById('target-slider');
        if (slider) {
            this.currentData.target = parseFloat(slider.value);
        }
        
        // Add some realistic noise and trends
        const noise = (Math.random() - 0.5) * 0.02; // Reduced noise for smoother display
        
        // Simulate PID response
        this.currentData.error = this.currentData.target - this.currentData.temperature;
        
        // Get current PID gains from sliders
        const kp = parseFloat(document.getElementById('kp-slider')?.value || 1.0);
        const ki = parseFloat(document.getElementById('ki-slider')?.value || 0.1);
        const kd = parseFloat(document.getElementById('kd-slider')?.value || 0.05);
        
        // PID calculation with proper time step
        this.currentData.pid_terms.p = kp * this.currentData.error;
        
        // Integral term with windup protection
        this.currentData.pid_terms.i += ki * this.currentData.error * dt;
        this.currentData.pid_terms.i = Math.max(-50, Math.min(50, this.currentData.pid_terms.i));
        
        // Derivative term
        const errorRate = (this.currentData.error - (this.currentData.previousError || 0)) / dt;
        this.currentData.pid_terms.d = kd * errorRate;
        this.currentData.previousError = this.currentData.error;
        
        // Calculate total output
        this.currentData.output = this.currentData.pid_terms.p + 
                                 this.currentData.pid_terms.i + 
                                 this.currentData.pid_terms.d;
        
        // Limit output
        this.currentData.output = Math.max(-100, Math.min(100, this.currentData.output));
        
        // Enhanced thermal system simulation
        const thermalTimeConstant = 15; // Faster response for demonstration
        const heatCapacity = 800;
        const ambientTemp = 20; // Room temperature
        const heatLoss = 0.03; // Heat loss coefficient
        
        // Temperature response with realistic thermal dynamics
        const powerEffect = this.currentData.output * 0.0008 / heatCapacity * dt;
        const ambientLoss = (this.currentData.temperature - ambientTemp) * heatLoss * dt;
        
        this.currentData.temperature += powerEffect - ambientLoss + noise;
        
        // Simulate safety monitoring
        this.updateSafetyStatus();
        
        // Clamp values for realism
        this.currentData.temperature = Math.max(-2, Math.min(15, this.currentData.temperature));
        this.currentData.output = Math.max(-100, Math.min(100, this.currentData.output));
    }

    updateSafetyStatus() {
        const temp = this.currentData.temperature;
        
        if (temp < 1.0 || temp > 6.0) {
            this.currentData.safety_level = 'CRITICAL';
            this.currentData.alarm_count = Math.max(1, this.currentData.alarm_count);
        } else if (temp < 2.0 || temp > 5.0) {
            this.currentData.safety_level = 'WARNING';
        } else {
            this.currentData.safety_level = 'SAFE';
            this.currentData.alarm_count = Math.max(0, this.currentData.alarm_count - 0.1);
        }
        
        this.currentData.alarm_count = Math.round(this.currentData.alarm_count);
    }

    startUpdateLoop() {
        this.updateInterval = setInterval(() => {
            this.updateDisplay();
        }, 100); // Update display 10 times per second for smooth UI
    }

    updateDisplay() {
        // Update system status values
        this.updateElement('current-temp', this.currentData.temperature.toFixed(1));
        
        // Only update target display if user isn't actively adjusting slider
        const targetDisplay = document.getElementById('target-temp');
        const slider = document.getElementById('target-slider');
        if (targetDisplay && slider && !targetDisplay.style.color) {
            // Only update if not currently being adjusted by user
            this.updateElement('target-temp', this.currentData.target.toFixed(1));
        }
        
        this.updateElement('control-output', this.currentData.output.toFixed(0));
        this.updateElement('safety-level', this.currentData.safety_level);
        this.updateElement('alarm-count', this.currentData.alarm_count);
        this.updateElement('control-mode', this.currentData.control_mode);

        // Update safety status indicator
        const safetyIndicator = document.getElementById('safety-status');
        if (safetyIndicator) {
            safetyIndicator.textContent = this.currentData.safety_level;
            safetyIndicator.className = `status-indicator ${this.currentData.safety_level.toLowerCase()}`;
        }

        // Update PID terms display
        this.updateElement('p-term-value', this.currentData.pid_terms.p.toFixed(2));
        this.updateElement('i-term-value', this.currentData.pid_terms.i.toFixed(2));
        this.updateElement('d-term-value', this.currentData.pid_terms.d.toFixed(2));

        // Update PID term visual bars
        this.updatePIDTermBars();

        // Update educational content based on current state
        this.updateEducationalContent();

        // Update chart if it exists
        if (window.temperatureChart) {
            window.temperatureChart.addDataPoint({
                time: Date.now(),
                temperature: this.currentData.temperature,
                target: this.currentData.target,
                error: this.currentData.error,
                output: this.currentData.output
            });
        }
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updatePIDTermBars() {
        // Update visual representation of PID terms
        const maxValue = 10; // Scale for visualization
        
        const updateBar = (className, value) => {
            const bar = document.querySelector(`.${className}`);
            if (bar) {
                const percentage = Math.min(100, Math.abs(value) / maxValue * 100);
                bar.style.width = percentage + '%';
            }
        };

        updateBar('p-fill', this.currentData.pid_terms.p);
        updateBar('i-fill', this.currentData.pid_terms.i);
        updateBar('d-fill', this.currentData.pid_terms.d);
    }

    updateEducationalContent() {
        const learningContent = document.getElementById('learning-content');
        if (!learningContent) return;

        let content = '';
        const temp = this.currentData.temperature;
        const target = this.currentData.target;
        const error = Math.abs(temp - target);

        if (error < 0.1) {
            content = `<p>🎯 <strong>Excellent Control!</strong> The system is maintaining temperature within ±0.1°C. 
                      The I term is handling any small steady-state error, while the P term provides the main control effort.</p>`;
        } else if (error < 0.5) {
            content = `<p>✅ <strong>Good Control:</strong> Small error of ${error.toFixed(2)}°C. 
                      The P term (${this.currentData.pid_terms.p.toFixed(2)}) is working to reduce this error. 
                      Watch how the control output adjusts!</p>`;
        } else if (error < 1.0) {
            content = `<p>⚠️ <strong>Moderate Error:</strong> The system is ${error.toFixed(2)}°C away from target. 
                      The P term is ${this.currentData.pid_terms.p > 0 ? 'heating' : 'cooling'} to correct this. 
                      Consider increasing Kp for faster response.</p>`;
        } else {
            content = `<p>🚨 <strong>Large Error:</strong> Significant deviation of ${error.toFixed(2)}°C! 
                      This might indicate a disturbance or need for better tuning. 
                      The safety system is monitoring closely.</p>`;
        }

        learningContent.innerHTML = content;
    }

    showSafetyEducation() {
        // Educational popup about safety systems (simplified for now)
        const message = `
🛡️ Safety System Education:

The safety monitor continuously checks:
• Temperature limits (1-6°C for whole blood)
• Rate of change (prevents thermal shock)
• Time outside safe ranges
• System component health

Current Status: ${this.currentData.safety_level}
This ensures patient safety and blood product integrity!
        `;
        
        alert(message); // In a real implementation, this would be a nice modal
    }

    explainStatusItem(item) {
        const label = item.querySelector('label').textContent;
        let explanation = '';

        switch(label) {
            case 'Current Temperature':
                explanation = `This is the actual temperature measured by the sensor. 
                              It should stay within 1-6°C for whole blood storage.`;
                break;
            case 'Target Temperature':
                explanation = `The desired temperature (setpoint). The PID controller 
                              works to maintain the current temperature at this value.`;
                break;
            case 'Control Output':
                explanation = `The power output from the PID controller. 
                              Negative values = cooling, Positive values = heating.`;
                break;
            case 'Safety Level':
                explanation = `Current safety status based on FDA regulations:
                              SAFE = 1-6°C, WARNING = outside preferred range, 
                              CRITICAL = approaching dangerous levels.`;
                break;
            case 'Active Alarms':
                explanation = `Number of active safety alarms. These alert operators 
                              to conditions that need attention.`;
                break;
            case 'Control Mode':
                explanation = `Current operating mode:
                              Automatic = PID controller active
                              Manual = operator control
                              Emergency = safety override active`;
                break;
        }

        if (explanation) {
            // Simple tooltip for now - in real implementation would be a nice popup
            alert(explanation);
        }
    }

    handleResize() {
        // Handle responsive layout changes
        if (window.temperatureChart) {
            window.temperatureChart.resize();
        }
    }

    // Enhanced public methods for external control
    setTargetTemperature(temp) {
        // Update internal data
        this.currentData.target = temp;
        
        // Update slider to match
        const slider = document.getElementById('target-slider');
        if (slider) {
            slider.value = temp;
        }
        
        // Show visual feedback
        this.showTargetSetFeedback(temp);
        
        // Send to real system if available
        if (window.dataConnector && window.dataConnector.isSystemReady()) {
            window.dataConnector.setTargetTemperature(temp)
                .then(result => {
                    console.log('Target temperature updated in real system');
                })
                .catch(error => {
                    console.error('Failed to update target temperature:', error);
                });
        }
    }

    showTargetSetFeedback(temperature) {
        // Visual feedback when target is successfully set
        const targetDisplay = document.getElementById('target-temp');
        if (targetDisplay) {
            targetDisplay.style.color = 'var(--safe-green, #10b981)';
            targetDisplay.style.fontWeight = '800';
            targetDisplay.textContent = temperature.toFixed(1);
            
            setTimeout(() => {
                targetDisplay.style.color = '';
                targetDisplay.style.fontWeight = '';
            }, 1000);
        }
        
        console.log(`✅ Target temperature set to: ${temperature.toFixed(1)}°C`);
    }

    triggerDisturbance(magnitude = 2.0) {
        // Simulate a disturbance (like opening a door)
        this.currentData.temperature += magnitude;
        console.log(`🌪️ Disturbance triggered: +${magnitude}°C`);
    }

    resetSystem() {
        this.currentData.temperature = 4.2;
        this.currentData.target = 4.0;
        this.currentData.output = 0;
        this.currentData.pid_terms = { p: 0, i: 0, d: 0 };
        
        // Reset slider
        const slider = document.getElementById('target-slider');
        if (slider) slider.value = 4.0;
        
        console.log('🔄 System reset to initial conditions');
    }
}

// Enhanced global functions for UI interactions
function adjustTimeScale(seconds) {
    // Update chart time window directly
    if (window.temperatureChart) {
        window.temperatureChart.setTimeWindow(seconds);
    }
    
    if (window.dashboard) {
        window.dashboard.chartTimeScale = seconds;
    }
    
    // Update active button
    document.querySelectorAll('.time-controls button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    console.log(`📊 Chart time scale changed to ${seconds} seconds`);
}

function clearChart() {
    if (window.temperatureChart) {
        window.temperatureChart.clear();
    }
    console.log('🗑️ Chart data cleared');
}

function triggerDisturbanceFromUI(magnitude = 2.0) {
    if (window.dashboard) {
        window.dashboard.triggerDisturbance(magnitude);
    }
}

function resetSystem() {
    if (window.dashboard) {
        window.dashboard.resetSystem();
    }
}

function setTargetFromSlider() {
    const slider = document.getElementById('target-slider');
    const targetTemp = parseFloat(slider.value);
    
    if (window.dashboard) {
        window.dashboard.setTargetTemperature(targetTemp);
    }
}

function updateTargetSliderValue() {
    // This is now handled by setupTargetSlider() but keeping for compatibility
    const slider = document.getElementById('target-slider');
    const display = document.getElementById('target-temp');
    
    if (slider && display) {
        display.textContent = parseFloat(slider.value).toFixed(1);
    }
}

// Enhanced initialization
function initializeSystemFromUI() {
    const initButton = document.querySelector('.init-button');
    if (initButton) {
        initButton.textContent = 'Initializing...';
        initButton.disabled = true;
    }
    
    setTimeout(() => {
        if (window.dashboard) {
            // Start enhanced simulation
            window.dashboard.startEnhancedSimulation();
            
            // Update connection status
            const connectionStatus = document.getElementById('connection-status');
            if (connectionStatus) {
                connectionStatus.textContent = 'Simulating';
                connectionStatus.className = 'connection-status partial';
            }
        }
        
        if (initButton) {
            initButton.textContent = 'System Active';
            initButton.disabled = false;
        }
        
        console.log('✅ System initialized with enhanced simulation');
    }, 1000);
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new ThermalControlDashboard();
    console.log('🎓 Educational Dashboard Ready!');
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThermalControlDashboard;
}