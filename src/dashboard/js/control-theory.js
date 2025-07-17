/**
 * Control Theory Educational Engine - Dark Theme Version
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
        // Create educational modal with dark theme styling
        const modal = document.createElement('div');
        modal.className = 'concept-modal modal-overlay';
        modal.innerHTML = `
            <div class="concept-modal-content modal-content">
                <div class="concept-header">
                    <h2>${concept.title}</h2>
                    <button class="close-modal" onclick="this.closest('.concept-modal').remove()">×</button>
                </div>
                
                <div class="concept-body">
                    <div class="definition-section">
                        <h3>📋 Definition</h3>
                        <p>${concept.definition}</p>
                        ${concept.formula ? `<div class="formula-dark">Formula: <code>${concept.formula}</code></div>` : ''}
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
        
        document.body.appendChild(modal);
        
        // Add entrance animation
        setTimeout(() => modal.classList.add('modal-visible'), 10);
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

// Add dark theme concept navigation and modal styles
const darkConceptStyles = document.createElement('style');
darkConceptStyles.textContent = `
    /* Dark Theme Concept Navigation */
    .concept-navigation {
        margin-top: var(--space-lg);
        padding: var(--space-lg);
        background: var(--bg-secondary);
        border-radius: var(--border-radius);
        border-left: 4px solid var(--edu-primary);
        border: 1px solid var(--border-color);
    }
    
    .concept-navigation h3 {
        color: var(--text-accent);
        margin-bottom: var(--space-md);
        font-weight: 700;
        letter-spacing: -0.01em;
    }
    
    .concept-buttons {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: var(--space-sm);
        margin-top: var(--space-md);
    }
    
    .concept-buttons button {
        padding: var(--space-sm) var(--space-md);
        background: var(--edu-primary);
        color: white;
        border: none;
        border-radius: var(--border-radius);
        cursor: pointer;
        font-size: 0.85rem;
        font-weight: 600;
        transition: all 0.2s ease;
        letter-spacing: 0.01em;
    }
    
    .concept-buttons button:hover {
        background: var(--edu-secondary);
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    
    /* Dark Theme Modal Styles */
    .modal-overlay {
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .modal-visible {
        opacity: 1;
    }
    
    .modal-content {
        background: var(--bg-panel) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        max-width: 700px !important;
        max-height: 85vh !important;
    }
    
    /* Dark Theme Formula Styling */
    .formula-dark {
        background: var(--bg-dark);
        color: var(--text-primary);
        padding: var(--space-md);
        border-radius: var(--border-radius);
        font-family: 'JetBrains Mono', monospace;
        margin: var(--space-md) 0;
        border-left: 3px solid var(--edu-primary);
        border: 1px solid var(--border-color);
    }
    
    .formula-dark code {
        background: transparent;
        color: var(--text-accent);
        font-weight: 600;
        font-size: 1.1rem;
        letter-spacing: 0.02em;
    }
    
    /* Dark Theme Modal Header */
    .concept-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--space-lg);
        border-bottom: 2px solid var(--border-color);
        padding-bottom: var(--space-md);
    }
    
    .concept-header h2 {
        color: var(--text-accent);
        margin: 0;
        font-weight: 700;
        letter-spacing: -0.01em;
    }
    
    .close-modal {
        background: var(--critical-red);
        color: white;
        border: none;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        cursor: pointer;
        font-size: 18px;
        font-weight: bold;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .close-modal:hover {
        background: var(--emergency-red);
        transform: scale(1.1);
    }
    
    /* Dark Theme Modal Body */
    .concept-body {
        color: var(--text-primary);
    }
    
    .concept-body h3 {
        color: var(--text-accent);
        margin-top: var(--space-lg);
        margin-bottom: var(--space-md);
        font-weight: 700;
        letter-spacing: -0.01em;
    }
    
    .concept-body p {
        color: var(--text-primary);
        line-height: 1.6;
        margin-bottom: var(--space-md);
    }
    
    .concept-body ul {
        color: var(--text-secondary);
        padding-left: var(--space-lg);
    }
    
    .concept-body li {
        margin-bottom: var(--space-sm);
        line-height: 1.5;
    }
    
    /* Dark Theme Modal Sections */
    .definition-section,
    .real-world-section,
    .medical-section,
    .key-points-section,
    .mistakes-section {
        background: var(--bg-secondary);
        padding: var(--space-lg);
        border-radius: var(--border-radius);
        margin-bottom: var(--space-lg);
        border: 1px solid var(--border-color);
    }
    
    .medical-section {
        background: rgba(16, 185, 129, 0.1);
        border-left: 4px solid var(--safe-green);
    }
    
    .mistakes-section {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid var(--warning-yellow);
    }
    
    /* Dark Theme Action Section */
    .action-section {
        margin-top: var(--space-xl);
        text-align: center;
        padding-top: var(--space-lg);
        border-top: 1px solid var(--border-color);
    }
    
    .action-section button {
        background: linear-gradient(135deg, var(--edu-primary), var(--edu-secondary));
        color: white;
        border: none;
        padding: var(--space-md) var(--space-xl);
        border-radius: var(--border-radius);
        cursor: pointer;
        font-weight: 700;
        font-size: 0.9rem;
        transition: all 0.2s ease;
        letter-spacing: 0.01em;
    }
    
    .action-section button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
    }
    
    /* Dark Theme Concept Explanation */
    .concept-explanation {
        background: var(--bg-panel);
        padding: var(--space-lg);
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
    }
    
    .concept-explanation h4 {
        color: var(--text-accent);
        margin-bottom: var(--space-md);
        font-weight: 700;
        letter-spacing: -0.01em;
    }
    
    .concept-explanation p {
        color: var(--text-primary);
        margin-bottom: var(--space-sm);
        line-height: 1.6;
    }
    
    .concept-explanation strong {
        color: var(--text-accent);
        font-weight: 700;
    }
    
    .key-points,
    .solutions {
        margin-top: var(--space-md);
    }
    
    .key-points strong,
    .solutions strong {
        color: var(--text-accent);
        font-weight: 700;
        display: block;
        margin-bottom: var(--space-sm);
    }
    
    .key-points ul,
    .solutions ul {
        color: var(--text-secondary);
        padding-left: var(--space-lg);
        margin: 0;
    }
    
    .key-points li,
    .solutions li {
        margin-bottom: var(--space-xs);
        line-height: 1.5;
    }
    
    /* Responsive Design for Modals */
    @media (max-width: 768px) {
        .modal-content {
            max-width: 95vw !important;
            max-height: 95vh !important;
            margin: var(--space-md) !important;
        }
        
        .concept-buttons {
            grid-template-columns: 1fr !important;
        }
    }
    
    /* Enhanced scrollbar for modal content */
    .modal-content::-webkit-scrollbar {
        width: 8px;
    }
    
    .modal-content::-webkit-scrollbar-track {
        background: var(--bg-dark);
        border-radius: 4px;
    }
    
    .modal-content::-webkit-scrollbar-thumb {
        background: var(--border-light);
        border-radius: 4px;
    }
    
    .modal-content::-webkit-scrollbar-thumb:hover {
        background: var(--text-accent);
    }
    
    /* Animation for concept explanations */
    .concept-explanation {
        animation: slideInUp 0.4s ease-out;
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Enhanced modal entrance animation */
    .concept-modal {
        animation: modalFadeIn 0.3s ease-out;
    }
    
    @keyframes modalFadeIn {
        from {
            opacity: 0;
            backdrop-filter: blur(0px);
        }
        to {
            opacity: 1;
            backdrop-filter: blur(8px);
        }
    }
    
    .modal-content {
        animation: modalSlideIn 0.4s ease-out;
    }
    
    @keyframes modalSlideIn {
        from {
            opacity: 0;
            transform: translateY(-30px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    /* Dark theme focus indicators */
    .concept-buttons button:focus,
    .action-section button:focus,
    .close-modal:focus {
        outline: 2px solid var(--edu-primary);
        outline-offset: 2px;
    }
    
    /* Loading state for concept buttons */
    .concept-buttons button:active {
        transform: translateY(0);
        box-shadow: var(--shadow-sm);
    }
    
    /* Enhanced tooltip for dark theme */
    .concept-tooltip {
        position: absolute;
        background: var(--bg-dark);
        color: var(--text-primary);
        padding: var(--space-sm) var(--space-md);
        border-radius: var(--border-radius);
        font-size: 0.8rem;
        max-width: 200px;
        z-index: 1001;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s ease;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-color);
    }
    
    .concept-tooltip.visible {
        opacity: 1;
    }
    
    /* Status indicators in concept explanations */
    .concept-status {
        display: inline-flex;
        align-items: center;
        gap: var(--space-xs);
        padding: var(--space-xs) var(--space-sm);
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .concept-status.beginner {
        background: rgba(34, 197, 94, 0.15);
        color: var(--safe-green);
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .concept-status.intermediate {
        background: rgba(245, 158, 11, 0.15);
        color: var(--warning-yellow);
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .concept-status.advanced {
        background: rgba(239, 68, 68, 0.15);
        color: var(--critical-red);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
`;

document.head.appendChild(darkConceptStyles);

// Initialize Control Theory Educator when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.controlTheory = new ControlTheoryEducator();
    console.log('📚 Control Theory Educator initialized with dark theme!');
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ControlTheoryEducator;
}