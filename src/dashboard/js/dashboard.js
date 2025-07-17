/**
 * Smart Thermal Control System - Educational Dashboard
 * Main dashboard coordination and initialization
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
        this.chartTimeScale = 60; // seconds
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
        // Simulate realistic thermal control system data
        // This would normally connect to your Python control system
        
        console.log('🔄 Starting data simulation...');
        
        setInterval(() => {
            this.simulateRealisticData();
        }, 1000); // Update every second for smooth visualization
    }

    simulateRealisticData() {
        // Simulate realistic PID control behavior
        const time = Date.now() / 1000;
        
        // Add some realistic noise and trends
        const noise = (Math.random() - 0.5) * 0.1;
        const targetTemp = 4.0;
        
        // Simulate PID response
        this.currentData.error = targetTemp - this.currentData.temperature;
        
        // Simple PID simulation (this would come from your actual control system)
        const kp = parseFloat(document.getElementById('kp-slider')?.value || 1.0);
        const ki = parseFloat(document.getElementById('ki-slider')?.value || 0.1);
        const kd = parseFloat(document.getElementById('kd-slider')?.value || 0.05);
        
        this.currentData.pid_terms.p = kp * this.currentData.error;
        this.currentData.pid_terms.i += ki * this.currentData.error * 0.1; // dt = 0.1
        this.currentData.pid_terms.d = kd * (this.currentData.error - (this.currentData.previousError || 0)) / 0.1;
        
        this.currentData.previousError = this.currentData.error;
        
        // Calculate total output
        this.currentData.output = this.currentData.pid_terms.p + 
                                 this.currentData.pid_terms.i + 
                                 this.currentData.pid_terms.d;
        
        // Simulate temperature response (simplified thermal dynamics)
        const thermalTimeConstant = 30; // seconds
        const temperatureChange = this.currentData.output * 0.001 / thermalTimeConstant;
        this.currentData.temperature += temperatureChange + noise;
        
        // Simulate safety monitoring
        this.updateSafetyStatus();
        
        // Clamp values for realism
        this.currentData.temperature = Math.max(0, Math.min(50, this.currentData.temperature));
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
        this.updateElement('target-temp', this.currentData.target.toFixed(1));
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

    // Public methods for external control
    setTargetTemperature(temp) {
        this.currentData.target = temp;
        this.updateElement('target-temp', temp.toFixed(1));
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
        console.log('🔄 System reset to initial conditions');
    }
}

// Global functions for UI interactions
function adjustTimeScale(seconds) {
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

function triggerDisturbance() {
    if (window.dashboard) {
        window.dashboard.triggerDisturbance();
    }
}

function resetSystem() {
    if (window.dashboard) {
        window.dashboard.resetSystem();
    }
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