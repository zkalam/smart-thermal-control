/**
 * Interactive PID Tuning Laboratory
 * Educational component for learning PID control concepts
 */

class PIDTuningLab {
    constructor() {
        this.currentPreset = 'medical';
        this.experiments = [
            {
                id: 1,
                title: "High Proportional Gain",
                description: "Increase Kp to 3.0 and observe what happens to the system response. Do you see overshoot?",
                targetValues: { kp: 3.0, ki: 0.1, kd: 0.05 },
                expectedResult: "You should see faster response but potential overshoot and oscillation."
            },
            {
                id: 2,
                title: "Zero Integral Gain", 
                description: "Set Ki to 0.0 and watch for steady-state error. Can the system reach the exact target?",
                targetValues: { kp: 1.0, ki: 0.0, kd: 0.05 },
                expectedResult: "The system may not reach the exact setpoint - that's steady-state error!"
            },
            {
                id: 3,
                title: "High Derivative Gain",
                description: "Increase Kd to 0.3 and trigger a disturbance. Notice how it dampens oscillations?",
                targetValues: { kp: 1.0, ki: 0.1, kd: 0.3 },
                expectedResult: "The system should be more stable and less prone to overshoot."
            },
            {
                id: 4,
                title: "Aggressive Tuning",
                description: "Try high gains: Kp=4.0, Ki=0.5, Kd=0.1. What happens to stability?",
                targetValues: { kp: 4.0, ki: 0.5, kd: 0.1 },
                expectedResult: "The system may become unstable with excessive oscillation!"
            },
            {
                id: 5,
                title: "Conservative Tuning",
                description: "Use very low gains: Kp=0.3, Ki=0.02, Kd=0.01. How does response time change?",
                targetValues: { kp: 0.3, ki: 0.02, kd: 0.01 },
                expectedResult: "Very stable but slow response - good for delicate processes."
            }
        ];
        
        this.currentExperiment = 0;
        this.init();
    }

    init() {
        console.log('🎛️ Initializing PID Tuning Laboratory...');
        
        this.setupSliders();
        this.setupPresetButtons();
        this.setupExperiments();
        this.loadPreset('medical'); // Start with medical-grade tuning
        
        console.log('✅ PID Lab initialized!');
    }

    setupSliders() {
        // Kp slider
        const kpSlider = document.getElementById('kp-slider');
        const kpValue = document.getElementById('kp-value');
        const kpExplanation = document.getElementById('kp-explanation');

        if (kpSlider && kpValue) {
            kpSlider.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                kpValue.textContent = value.toFixed(1);
                this.updatePIDGain('kp', value);
                this.updateExplanation('kp', value, kpExplanation);
            });
        }

        // Ki slider
        const kiSlider = document.getElementById('ki-slider');
        const kiValue = document.getElementById('ki-value');
        const kiExplanation = document.getElementById('ki-explanation');

        if (kiSlider && kiValue) {
            kiSlider.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                kiValue.textContent = value.toFixed(2);
                this.updatePIDGain('ki', value);
                this.updateExplanation('ki', value, kiExplanation);
            });
        }

        // Kd slider
        const kdSlider = document.getElementById('kd-slider');
        const kdValue = document.getElementById('kd-value');
        const kdExplanation = document.getElementById('kd-explanation');

        if (kdSlider && kdValue) {
            kdSlider.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                kdValue.textContent = value.toFixed(3);
                this.updatePIDGain('kd', value);
                this.updateExplanation('kd', value, kdExplanation);
            });
        }
    }

    setupPresetButtons() {
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const preset = e.target.getAttribute('data-preset');
                this.loadPreset(preset);
                
                // Visual feedback
                document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
    }

    setupExperiments() {
        this.displayCurrentExperiment();
        
        // Setup experiment buttons
        const tryButton = document.querySelector('.try-button');
        if (tryButton) {
            tryButton.addEventListener('click', () => {
                this.executeCurrentExperiment();
            });
        }
    }

    updatePIDGain(parameter, value) {
        // This would normally send the new gains to your Python control system
        console.log(`🔧 Updated ${parameter.toUpperCase()}: ${value}`);
        
        // For now, just trigger educational feedback
        this.provideLearningFeedback(parameter, value);
        
        // Reset integral term when Ki changes to avoid windup during tuning
        if (parameter === 'ki' && window.dashboard) {
            window.dashboard.currentData.pid_terms.i = 0;
        }
    }

    updateExplanation(parameter, value, explanationElement) {
        if (!explanationElement) return;

        let explanation = '';
        
        switch(parameter) {
            case 'kp':
                if (value < 0.5) {
                    explanation = "Low Kp = slow, stable response. Good for systems that can't handle aggressive control.";
                } else if (value < 2.0) {
                    explanation = "Moderate Kp = balanced response. Good starting point for most systems.";
                } else if (value < 4.0) {
                    explanation = "High Kp = fast response, but watch for overshoot and oscillation.";
                } else {
                    explanation = "Very high Kp = likely to cause instability! System may oscillate wildly.";
                }
                break;
                
            case 'ki':
                if (value < 0.01) {
                    explanation = "Very low Ki = may not eliminate steady-state error completely.";
                } else if (value < 0.1) {
                    explanation = "Low Ki = slow elimination of steady-state error, but stable.";
                } else if (value < 0.5) {
                    explanation = "Moderate Ki = good balance of error correction and stability.";
                } else {
                    explanation = "High Ki = fast error correction but may cause oscillation and overshoot.";
                }
                break;
                
            case 'kd':
                if (value < 0.01) {
                    explanation = "Very low Kd = minimal damping. System may overshoot.";
                } else if (value < 0.1) {
                    explanation = "Low Kd = some damping. Helps reduce overshoot moderately.";
                } else if (value < 0.3) {
                    explanation = "Moderate Kd = good damping. Reduces overshoot and oscillation.";
                } else {
                    explanation = "High Kd = strong damping. May make system sluggish and sensitive to noise.";
                }
                break;
        }
        
        explanationElement.textContent = explanation;
        explanationElement.classList.add('slide-in');
        
        // Remove animation class after completion
        setTimeout(() => {
            explanationElement.classList.remove('slide-in');
        }, 300);
    }

    loadPreset(presetName) {
        console.log(`📋 Loading preset: ${presetName}`);
        
        let gains = {};
        let description = '';
        
        switch(presetName) {
            case 'conservative':
                gains = { kp: 0.5, ki: 0.05, kd: 0.02 };
                description = 'Conservative tuning prioritizes stability over speed. Good for delicate processes.';
                break;
                
            case 'aggressive':
                gains = { kp: 2.5, ki: 0.3, kd: 0.1 };
                description = 'Aggressive tuning for fast response. Use when system can handle more aggressive control.';
                break;
                
            case 'medical':
            default:
                gains = { kp: 1.0, ki: 0.1, kd: 0.05 };
                description = 'Medical-grade tuning balances response time with stability for patient safety.';
                break;
        }
        
        // Update sliders
        this.setSliderValue('kp-slider', 'kp-value', gains.kp, 1);
        this.setSliderValue('ki-slider', 'ki-value', gains.ki, 2);
        this.setSliderValue('kd-slider', 'kd-value', gains.kd, 3);
        
        // Update explanations
        const explanations = {
            'kp': document.getElementById('kp-explanation'),
            'ki': document.getElementById('ki-explanation'),
            'kd': document.getElementById('kd-explanation')
        };
        
        Object.keys(gains).forEach(param => {
            this.updateExplanation(param, gains[param], explanations[param]);
            this.updatePIDGain(param, gains[param]);
        });
        
        this.currentPreset = presetName;
        this.showPresetEducation(presetName, description);
    }

    setSliderValue(sliderId, valueId, value, decimals) {
        const slider = document.getElementById(sliderId);
        const valueDisplay = document.getElementById(valueId);
        
        if (slider && valueDisplay) {
            slider.value = value;
            valueDisplay.textContent = value.toFixed(decimals);
        }
    }

    showPresetEducation(presetName, description) {
        // Create temporary educational message
        const educationalNote = document.querySelector('.educational-note p');
        if (educationalNote) {
            const originalText = educationalNote.innerHTML;
            educationalNote.innerHTML = `<strong>Preset Loaded: ${presetName.charAt(0).toUpperCase() + presetName.slice(1)}</strong><br>${description}`;
            
            // Restore original text after 5 seconds
            setTimeout(() => {
                educationalNote.innerHTML = originalText;
            }, 5000);
        }
    }

    displayCurrentExperiment() {
        const experimentCard = document.getElementById('current-experiment');
        if (!experimentCard) return;

        const experiment = this.experiments[this.currentExperiment];
        
        experimentCard.innerHTML = `
            <p><strong>Experiment ${experiment.id}: ${experiment.title}</strong></p>
            <p>${experiment.description}</p>
            <button class="try-button" onclick="window.pidLab.executeCurrentExperiment()">Try It!</button>
            <button class="next-button" onclick="window.pidLab.nextExperiment()">Next Experiment →</button>
        `;
    }

    executeCurrentExperiment() {
        const experiment = this.experiments[this.currentExperiment];
        console.log(`🧪 Executing experiment: ${experiment.title}`);
        
        // Set the target PID values
        this.setSliderValue('kp-slider', 'kp-value', experiment.targetValues.kp, 1);
        this.setSliderValue('ki-slider', 'ki-value', experiment.targetValues.ki, 2);
        this.setSliderValue('kd-slider', 'kd-value', experiment.targetValues.kd, 3);
        
        // Update the system
        Object.keys(experiment.targetValues).forEach(param => {
            this.updatePIDGain(param, experiment.targetValues[param]);
        });
        
        // Show expected result after a delay
        setTimeout(() => {
            this.showExperimentResult(experiment);
        }, 3000);
        
        // Add some excitement to the experience
        this.highlightChanges();
    }

    showExperimentResult(experiment) {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'experiment-result';
        resultDiv.innerHTML = `
            <div class="result-content">
                <h4>🔬 Experiment Result:</h4>
                <p>${experiment.expectedResult}</p>
                <p><em>Observe the temperature chart and PID terms to see the effects!</em></p>
                <button onclick="this.parentElement.parentElement.remove()">Got it!</button>
            </div>
        `;
        
        resultDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            z-index: 1000;
            max-width: 400px;
            text-align: center;
        `;
        
        resultDiv.querySelector('.result-content button').style.cssText = `
            background: rgba(255,255,255,0.2);
            border: 2px solid white;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 15px;
            font-weight: 600;
        `;
        
        document.body.appendChild(resultDiv);
    }

    nextExperiment() {
        this.currentExperiment = (this.currentExperiment + 1) % this.experiments.length;
        this.displayCurrentExperiment();
        console.log(`➡️ Advanced to experiment ${this.currentExperiment + 1}`);
    }

    highlightChanges() {
        // Add visual feedback when values change
        document.querySelectorAll('.pid-parameter').forEach(param => {
            param.style.transform = 'scale(1.02)';
            param.style.boxShadow = '0 4px 12px rgba(99, 102, 241, 0.3)';
            param.style.transition = 'all 0.3s ease';
        });
        
        setTimeout(() => {
            document.querySelectorAll('.pid-parameter').forEach(param => {
                param.style.transform = 'scale(1)';
                param.style.boxShadow = 'none';
            });
        }, 1000);
    }

    provideLearningFeedback(parameter, value) {
        // Provide real-time educational feedback based on parameter changes
        const feedbackMessages = [];
        
        // Get current values
        const kp = parseFloat(document.getElementById('kp-slider')?.value || 1.0);
        const ki = parseFloat(document.getElementById('ki-slider')?.value || 0.1);
        const kd = parseFloat(document.getElementById('kd-slider')?.value || 0.05);
        
        // Analyze the tuning combination
        if (kp > 3.0 && ki > 0.3) {
            feedbackMessages.push("⚠️ High Kp + High Ki combination may cause severe oscillation!");
        }
        
        if (kp < 0.3 && ki < 0.05) {
            feedbackMessages.push("🐌 Very conservative tuning - expect slow response.");
        }
        
        if (kd > 0.2) {
            feedbackMessages.push("🛡️ High derivative gain will strongly dampen oscillations.");
        }
        
        if (ki === 0) {
            feedbackMessages.push("📍 Zero integral gain - watch for steady-state error!");
        }
        
        // Show feedback if any
        if (feedbackMessages.length > 0) {
            this.showLearningTip(feedbackMessages[0]);
        }
    }

    showLearningTip(message) {
        // Remove existing tip
        const existingTip = document.querySelector('.learning-tip');
        if (existingTip) {
            existingTip.remove();
        }
        
        // Create new tip
        const tip = document.createElement('div');
        tip.className = 'learning-tip';
        tip.textContent = message;
        tip.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 999;
            max-width: 300px;
            font-size: 14px;
            font-weight: 500;
            animation: slideInRight 0.3s ease;
        `;
        
        document.body.appendChild(tip);
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            tip.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => tip.remove(), 300);
        }, 4000);
    }

    // Educational methods for specific scenarios
    demonstrateOvershoot() {
        console.log('🎯 Demonstrating overshoot...');
        this.loadPreset('aggressive');
        
        // Trigger a setpoint change to show overshoot
        setTimeout(() => {
            if (window.dashboard) {
                const originalTarget = window.dashboard.currentData.target;
                window.dashboard.setTargetTemperature(originalTarget + 2);
                
                setTimeout(() => {
                    window.dashboard.setTargetTemperature(originalTarget);
                }, 10000);
            }
        }, 1000);
        
        this.showLearningTip('Watch the temperature chart - you should see overshoot with aggressive tuning!');
    }

    demonstrateSteadyStateError() {
        console.log('📍 Demonstrating steady-state error...');
        
        // Set Ki to zero
        this.setSliderValue('ki-slider', 'ki-value', 0.0, 2);
        this.updatePIDGain('ki', 0.0);
        
        this.showLearningTip('With Ki=0, the system may not reach the exact setpoint. This is steady-state error!');
    }

    demonstrateStability() {
        console.log('🛡️ Demonstrating system stability...');
        this.loadPreset('medical');
        
        // Trigger a disturbance
        setTimeout(() => {
            if (window.dashboard) {
                window.dashboard.triggerDisturbance(1.5);
            }
        }, 1000);
        
        this.showLearningTip('Medical-grade tuning provides good stability. Watch how it handles disturbances!');
    }

    // Public API methods
    getCurrentGains() {
        return {
            kp: parseFloat(document.getElementById('kp-slider')?.value || 1.0),
            ki: parseFloat(document.getElementById('ki-slider')?.value || 0.1),
            kd: parseFloat(document.getElementById('kd-slider')?.value || 0.05)
        };
    }

    setGains(kp, ki, kd) {
        this.setSliderValue('kp-slider', 'kp-value', kp, 1);
        this.setSliderValue('ki-slider', 'ki-value', ki, 2);
        this.setSliderValue('kd-slider', 'kd-value', kd, 3);
        
        this.updatePIDGain('kp', kp);
        this.updatePIDGain('ki', ki);
        this.updatePIDGain('kd', kd);
    }
}

// Global functions for UI interactions
function tryExperiment(experimentId) {
    if (window.pidLab) {
        window.pidLab.currentExperiment = experimentId - 1;
        window.pidLab.executeCurrentExperiment();
    }
}

function demonstrateOvershoot() {
    if (window.pidLab) {
        window.pidLab.demonstrateOvershoot();
    }
}

function demonstrateSteadyStateError() {
    if (window.pidLab) {
        window.pidLab.demonstrateSteadyStateError();
    }
}

function demonstrateStability() {
    if (window.pidLab) {
        window.pidLab.demonstrateStability();
    }
}

// Add CSS animations for tips
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .experiment-result .result-content button:hover {
        background: rgba(255,255,255,0.3) !important;
        transform: scale(1.05);
    }
    
    .next-button {
        background: rgba(255,255,255,0.2) !important;
        border: 2px solid white !important;
        color: white !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        cursor: pointer !important;
        margin-left: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    .next-button:hover {
        background: rgba(255,255,255,0.3) !important;
        transform: scale(1.05) !important;
    }
`;
document.head.appendChild(style);

// Initialize PID Lab when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.pidLab = new PIDTuningLab();
    console.log('🎛️ PID Tuning Laboratory Ready!');
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PIDTuningLab;
}