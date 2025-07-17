/**
 * Control Theory Educational Engine
 * Provides dynamic educational content and explanations for control systems concepts
 */

class ControlTheoryEducator {
    constructor() {
        this.currentLearningMode = 'beginner';
        this.conceptDatabase = this.initializeConceptDatabase();
        this.learningHistory = [];
        this.currentConcepts = [];
        
        this.init();
    }

    init() {
        console.log('📚 Initializing Control Theory Educator...');
        
        this.setupEducationalContent();
        this.startAdaptiveLearning();
        
        console.log('✅ Control Theory Educator ready!');
    }

    initializeConceptDatabase() {
        return {
            // Basic PID Concepts
            proportional: {
                level: 'beginner',
                title: 'Proportional Control (P)',
                definition: 'The proportional term produces an output value that is proportional to the current error value.',
                formula: 'P_out = Kp × error',
                realWorld: 'Like pressing harder on the gas pedal when you\'re further behind a car.',
                medicalContext: 'Higher Kp means more aggressive temperature correction, but can cause overshoot.',
                keyPoints: [
                    'Larger error = larger control action',
                    'Can never eliminate steady-state error alone',
                    'Higher Kp = faster response but potential instability'
                ],
                commonMistakes: [
                    'Setting Kp too high causing oscillation',
                    'Expecting P-only control to reach exact setpoint'
                ]
            },

            integral: {
                level: 'intermediate',
                title: 'Integral Control (I)',
                definition: 'The integral term is proportional to both the magnitude and duration of the error.',
                formula: 'I_out = Ki × ∫error dt',
                realWorld: 'Like a persistent driver who keeps accelerating until reaching the exact speed limit.',
                medicalContext: 'Ki eliminates steady-state error, ensuring blood reaches exact target temperature.',
                keyPoints: [
                    'Eliminates steady-state error',
                    'Accounts for past errors over time',
                    'Can cause windup if not properly limited'
                ],
                commonMistakes: [
                    'Setting Ki too high causing oscillation',
                    'Not implementing anti-windup protection'
                ]
            },

            derivative: {
                level: 'intermediate',
                title: 'Derivative Control (D)',
                definition: 'The derivative term predicts future error based on its current rate of change.',
                formula: 'D_out = Kd × (d_error/dt)',
                realWorld: 'Like anticipating traffic slowdown and easing off the gas before getting too close.',
                medicalContext: 'Kd provides damping, preventing temperature overshoot that could damage blood.',
                keyPoints: [
                    'Provides damping and stability',
                    'Reduces overshoot and oscillation',
                    'Can amplify noise in measurements'
                ],
                commonMistakes: [
                    'Setting Kd too high making system sluggish',
                    'Not filtering noise before derivative calculation'
                ]
            },

            // Advanced Concepts
            steadyStateError: {
                level: 'intermediate',
                title: 'Steady-State Error',
                definition: 'The difference between the desired output and actual output after the system has reached equilibrium.',
                formula: 'SSE = setpoint - final_value',
                realWorld: 'Like cruise control settling at 68 mph when set to 70 mph.',
                medicalContext: 'Even small steady-state errors can compromise blood storage quality over time.',
                keyPoints: [
                    'P-only control always has steady-state error for step inputs',
                    'I term is required to eliminate steady-state error',
                    'Type of input affects steady-state error'
                ],
                solutions: [
                    'Add integral control (Ki > 0)',
                    'Increase system gain (but watch stability)',
                    'Use feedforward control for known disturbances'
                ]
            },

            overshoot: {
                level: 'beginner',
                title: 'Overshoot',
                definition: 'When the system response exceeds the target value before settling.',
                formula: 'Overshoot % = ((peak - setpoint) / setpoint) × 100',
                realWorld: 'Like accelerating past your exit because you pressed the gas too hard.',
                medicalContext: 'Temperature overshoot above 6°C can damage red blood cells - dangerous!',
                keyPoints: [
                    'Caused by aggressive control (high Kp)',
                    'Can be reduced with derivative control (Kd)',
                    'Trade-off between speed and overshoot'
                ],
                solutions: [
                    'Reduce proportional gain (Kp)',
                    'Add derivative control (Kd)',
                    'Use setpoint ramping'
                ]
            },

            oscillation: {
                level: 'intermediate',
                title: 'Oscillation',
                definition: 'When the system output continuously varies around the setpoint.',
                realWorld: 'Like swerving back and forth trying to stay in your lane.',
                medicalContext: 'Temperature oscillation stresses blood components and wastes energy.',
                keyPoints: [
                    'Often caused by too much gain (Kp or Ki)',
                    'Can indicate system instability',
                    'Derivative control helps dampen oscillations'
                ],
                solutions: [
                    'Reduce Kp and/or Ki',
                    'Add derivative control (Kd)',
                    'Check for external disturbances'
                ]
            },

            // Safety and Medical Concepts
            fdaCompliance: {
                level: 'advanced',
                title: 'FDA Blood Storage Requirements',
                definition: 'Regulatory requirements for safe blood product storage temperatures.',
                medicalContext: 'FDA mandates whole blood storage at 1-6°C to prevent bacterial growth and cell damage.',
                keyPoints: [
                    'Whole blood: 1-6°C (FDA requirement)',
                    'Plasma: ≤-18°C (Fresh Frozen Plasma)',
                    'Platelets: 20-24°C with agitation',
                    'Temperature monitoring required every 4 hours'
                ],
                safetyImplications: [
                    'Above 6°C: Bacterial growth risk',
                    'Below 1°C: Cell membrane damage',
                    'Temperature excursions must be documented',
                    'Out-of-range products may need disposal'
                ]
            },

            thermalDynamics: {
                level: 'advanced',
                title: 'Thermal System Dynamics',
                definition: 'How thermal systems respond to energy inputs and environmental changes.',
                formula: 'C × dT/dt = Q_in - Q_out',
                medicalContext: 'Understanding thermal dynamics helps optimize blood storage system design.',
                keyPoints: [
                    'Thermal mass affects response speed',
                    'Insulation reduces energy requirements',
                    'Heat transfer occurs through conduction, convection, radiation'
                ],
                practicalImplications: [
                    'Larger containers respond more slowly',
                    'Better insulation improves efficiency',
                    'Ambient temperature affects cooling load'
                ]
            }
        };
    }

    setupEducationalContent() {
        // Set up dynamic content updating
        this.updateEducationalContent();
        
        // Set up concept exploration
        this.setupConceptNavigation();
        
        // Initialize learning recommendations
        this.initializeLearningPath();
    }

    startAdaptiveLearning() {
        // Monitor user interactions and adapt content
        setInterval(() => {
            this.analyzeUserBehavior();
            this.updateLearningRecommendations();
        }, 5000);
    }

    updateEducationalContent() {
        // Get current system state for context-aware education
        const currentState = this.getCurrentSystemState();
        const relevantConcepts = this.identifyRelevantConcepts(currentState);
        
        this.displayRelevantConcepts(relevantConcepts);
    }

    getCurrentSystemState() {
        // Get current system data for educational context
        if (window.dashboard && window.dashboard.currentData) {
            return {
                error: Math.abs(window.dashboard.currentData.error || 0),
                temperature: window.dashboard.currentData.temperature || 4.0,
                target: window.dashboard.currentData.target || 4.0,
                output: window.dashboard.currentData.output || 0,
                pidTerms: window.dashboard.currentData.pid_terms || { p: 0, i: 0, d: 0 },
                safetyLevel: window.dashboard.currentData.safety_level || 'SAFE'
            };
        }
        return { error: 0, temperature: 4.0, target: 4.0, output: 0, pidTerms: { p: 0, i: 0, d: 0 }, safetyLevel: 'SAFE' };
    }

    identifyRelevantConcepts(state) {
        const concepts = [];
        
        // Error-based concept selection
        if (Math.abs(state.error) > 1.0) {
            concepts.push('proportional', 'overshoot');
        } else if (Math.abs(state.error) > 0.1) {
            concepts.push('steadyStateError', 'integral');
        }
        
        // Oscillation detection
        if (this.detectOscillation(state)) {
            concepts.push('oscillation', 'derivative');
        }
        
        // Safety-related concepts
        if (state.safetyLevel !== 'SAFE') {
            concepts.push('fdaCompliance');
        }
        
        // PID tuning context
        if (window.pidLab) {
            const gains = window.pidLab.getCurrentGains();
            if (gains.kp > 2.0) concepts.push('overshoot');
            if (gains.ki === 0) concepts.push('steadyStateError');
            if (gains.kd > 0.1) concepts.push('derivative');
        }
        
        return concepts.length > 0 ? concepts : ['proportional']; // Default to basic concept
    }

    detectOscillation(state) {
        // Simple oscillation detection logic
        this.recentErrors = this.recentErrors || [];
        this.recentErrors.push(state.error);
        
        if (this.recentErrors.length > 10) {
            this.recentErrors.shift();
        }
        
        if (this.recentErrors.length < 6) return false;
        
        // Check for sign changes indicating oscillation
        let signChanges = 0;
        for (let i = 1; i < this.recentErrors.length; i++) {
            if ((this.recentErrors[i] > 0) !== (this.recentErrors[i-1] > 0)) {
                signChanges++;
            }
        }
        
        return signChanges > 3; // More than 3 sign changes indicates oscillation
    }

    displayRelevantConcepts(conceptKeys) {
        const learningContent = document.getElementById('learning-content');
        if (!learningContent) return;
        
        // Select primary concept to display
        const primaryConcept = conceptKeys[0];
        const concept = this.conceptDatabase[primaryConcept];
        
        if (!concept) return;
        
        let content = `
            <div class="concept-explanation">
                <h4>💡 ${concept.title}</h4>
                <p><strong>What's happening:</strong> ${concept.definition}</p>
        `;
        
        if (concept.medicalContext) {
            content += `<p><strong>Medical relevance:</strong> ${concept.medicalContext}</p>`;
        }
        
        if (concept.keyPoints) {
            content += `
                <div class="key-points">
                    <strong>Key Points:</strong>
                    <ul>
                        ${concept.keyPoints.map(point => `<li>${point}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        if (concept.solutions) {
            content += `
                <div class="solutions">
                    <strong>Solutions:</strong>
                    <ul>
                        ${concept.solutions.map(solution => `<li>${solution}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        content += `</div>`;
        
        learningContent.innerHTML = content;
        learningContent.classList.add('slide-in');
        
        // Track learning progress
        this.recordConceptViewed(primaryConcept);
    }

    setupConceptNavigation() {
        // Add concept navigation buttons if they don't exist
        const theoryPanel = document.querySelector('.control-theory-panel');
        if (!theoryPanel) return;
        
        const navHTML = `
            <div class="concept-navigation">
                <h3>🎓 Explore Control Concepts:</h3>
                <div class="concept-buttons">
                    <button onclick="window.controlTheory.explainConcept('proportional')">Proportional (P)</button>
                    <button onclick="window.controlTheory.explainConcept('integral')">Integral (I)</button>
                    <button onclick="window.controlTheory.explainConcept('derivative')">Derivative (D)</button>
                    <button onclick="window.controlTheory.explainConcept('steadyStateError')">Steady-State Error</button>
                    <button onclick="window.controlTheory.explainConcept('overshoot')">Overshoot</button>
                    <button onclick="window.controlTheory.explainConcept('oscillation')">Oscillation</button>
                </div>
            </div>
        `;
        
        // Insert navigation after current learning content
        const currentLearning = theoryPanel.querySelector('.current-learning');
        if (currentLearning && !theoryPanel.querySelector('.concept-navigation')) {
            currentLearning.insertAdjacentHTML('afterend', navHTML);
        }
    }

    explainConcept(conceptKey) {
        const concept = this.conceptDatabase[conceptKey];
        if (!concept) return;
        
        console.log(`📖 Explaining concept: ${concept.title}`);
        
        // Create detailed explanation modal/popup
        this.showConceptModal(concept);
        
        // Record for learning analytics
        this.recordConceptExplored(conceptKey);
    }

    showConceptModal(concept) {
        // Create educational modal
        const modal = document.createElement('div');
        modal.className = 'concept-modal';
        modal.innerHTML = `
            <div class="concept-modal-content">
                <div class="concept-header">
                    <h2>${concept.title}</h2>
                    <button class="close-modal" onclick="this.closest('.concept-modal').remove()">×</button>
                </div>
                
                <div class="concept-body">
                    <div class="definition-section">
                        <h3>📋 Definition</h3>
                        <p>${concept.definition}</p>
                        ${concept.formula ? `<div class="formula">Formula: <code>${concept.formula}</code></div>` : ''}
                    </div>
                    
                    ${concept.realWorld ? `
                        <div class="real-world-section">
                            <h3>🌍 Real-World Analogy</h3>
                            <p>${concept.realWorld}</p>
                        </div>
                    ` : ''}
                    
                    ${concept.medicalContext ? `
                        <div class="medical-section">
                            <h3>🏥 Medical Context</h3>
                            <p>${concept.medicalContext}</p>
                        </div>
                    ` : ''}
                    
                    ${concept.keyPoints ? `
                        <div class="key-points-section">
                            <h3>🔑 Key Points</h3>
                            <ul>
                                ${concept.keyPoints.map(point => `<li>${point}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${concept.commonMistakes ? `
                        <div class="mistakes-section">
                            <h3>⚠️ Common Mistakes</h3>
                            <ul>
                                ${concept.commonMistakes.map(mistake => `<li>${mistake}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    <div class="action-section">
                        <button onclick="window.controlTheory.demonstrateConcept('${Object.keys(this.conceptDatabase).find(key => this.conceptDatabase[key] === concept)}')">
                            🧪 See It In Action
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Style the modal
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        `;
        
        modal.querySelector('.concept-modal-content').style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 30px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        `;
        
        document.body.appendChild(modal);
    }

    demonstrateConcept(conceptKey) {
        console.log(`🎭 Demonstrating concept: ${conceptKey}`);
        
        switch(conceptKey) {
            case 'proportional':
                this.demonstrateProportionalControl();
                break;
            case 'integral':
                this.demonstrateIntegralControl();
                break;
            case 'derivative':
                this.demonstrateDerivativeControl();
                break;
            case 'overshoot':
                this.demonstrateOvershoot();
                break;
            case 'oscillation':
                this.demonstrateOscillation();
                break;
            default:
                this.showLearningTip(`Demonstration for ${conceptKey} coming soon!`);
        }
        
        // Close modal
        document.querySelector('.concept-modal')?.remove();
    }

    demonstrateProportionalControl() {
        if (window.pidLab) {
            window.pidLab.setGains(2.0, 0.0, 0.0); // P-only control
            this.showLearningTip('Watch: P-only control responds quickly but may have steady-state error!');
        }
    }

    demonstrateIntegralControl() {
        if (window.pidLab) {
            window.pidLab.setGains(1.0, 0.3, 0.0); // Add strong I term
            this.showLearningTip('Watch: Integral control eliminates steady-state error but may cause overshoot!');
        }
    }

    demonstrateDerivativeControl() {
        if (window.pidLab) {
            window.pidLab.setGains(2.0, 0.2, 0.2); // Add D term for damping
            this.showLearningTip('Watch: Derivative control provides damping and reduces overshoot!');
        }
    }

    demonstrateOvershoot() {
        if (window.pidLab) {
            window.pidLab.setGains(4.0, 0.1, 0.0); // High Kp
            setTimeout(() => {
                if (window.dashboard) {
                    window.dashboard.setTargetTemperature(6.0);
                }
            }, 1000);
            this.showLearningTip('Watch: High Kp causes overshoot! Temperature will exceed the target.');
        }
    }

    demonstrateOscillation() {
        if (window.pidLab) {
            window.pidLab.setGains(5.0, 0.8, 0.0); // Unstable gains
            this.showLearningTip('Watch: Too much gain causes oscillation! The system becomes unstable.');
        }
    }

    showLearningTip(message) {
        // Reuse the tip system from PID lab
        if (window.pidLab) {
            window.pidLab.showLearningTip(message);
        } else {
            console.log(`💡 Learning Tip: ${message}`);
        }
    }

    // Learning Analytics
    recordConceptViewed(conceptKey) {
        this.learningHistory.push({
            type: 'concept_viewed',
            concept: conceptKey,
            timestamp: Date.now()
        });
    }

    recordConceptExplored(conceptKey) {
        this.learningHistory.push({
            type: 'concept_explored',
            concept: conceptKey,
            timestamp: Date.now()
        });
    }

    analyzeUserBehavior() {
        // Analyze learning patterns and adapt content
        const recentHistory = this.learningHistory.slice(-10);
        
        // Check if user is exploring advanced concepts
        const advancedConcepts = recentHistory.filter(entry => 
            this.conceptDatabase[entry.concept]?.level === 'advanced'
        );
        
        if (advancedConcepts.length > 3 && this.currentLearningMode === 'beginner') {
            this.currentLearningMode = 'advanced';
            console.log('🎓 Advancing to advanced learning mode');
        }
    }

    initializeLearningPath() {
        // Set up recommended learning progression
        this.learningPath = [
            ['proportional', 'Basic proportional control'],
            ['integral', 'Eliminating steady-state error'],
            ['derivative', 'Adding stability with derivative'],
            ['overshoot', 'Understanding overshoot'],
            ['oscillation', 'Preventing oscillation'],
            ['fdaCompliance', 'Medical device requirements']
        ];
    }

    updateLearningRecommendations() {
        // Update educational content based on user progress
        this.updateEducationalContent();
    }

    // Public API
    getCurrentConcepts() {
        return this.currentConcepts;
    }

    setLearningMode(mode) {
        this.currentLearningMode = mode;
        console.log(`📚 Learning mode set to: ${mode}`);
    }
}

// Add concept navigation button styles
const conceptStyles = document.createElement('style');
conceptStyles.textContent = `
    .concept-navigation {
        margin-top: 20px;
        padding: 20px;
        background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
        border-radius: 8px;
        border-left: 4px solid var(--edu-primary);
    }
    
    .concept-buttons {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 10px;
        margin-top: 15px;
    }
    
    .concept-buttons button {
        padding: 8px 12px;
        background: var(--edu-primary);
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.2s ease;
    }
    
    .concept-buttons button:hover {
        background: var(--edu-secondary);
        transform: translateY(-1px);
    }
    
    .formula {
        background: #f8fafc;
        padding: 10px;
        border-radius: 6px;
        font-family: monospace;
        margin: 10px 0;
        border-left: 3px solid var(--edu-primary);
    }
    
    .concept-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 15px;
    }
    
    .close-modal {
        background: #ef4444;
        color: white;
        border: none;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        cursor: pointer;
        font-size: 18px;
        font-weight: bold;
    }
    
    .concept-body h3 {
        color: var(--edu-primary);
        margin-top: 20px;
        margin-bottom: 10px;
    }
    
    .action-section {
        margin-top: 25px;
        text-align: center;
        padding-top: 20px;
        border-top: 1px solid #e5e7eb;
    }
    
    .action-section button {
        background: linear-gradient(135deg, var(--edu-primary), var(--edu-secondary));
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.2s ease;
    }
    
    .action-section button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
`;
document.head.appendChild(conceptStyles);

// Initialize Control Theory Educator when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.controlTheory = new ControlTheoryEducator();
    console.log('📚 Control Theory Educator initialized!');
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ControlTheoryEducator;
}