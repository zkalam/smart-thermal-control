/**
 * Data Connector - Bridge between Educational Dashboard and Python Control System
 * Handles all communication with the Flask backend server
 */

class DataConnector {
    constructor() {
        this.baseURL = 'http://127.0.0.1:5000';
        this.socket = null;
        this.isConnected = false;
        this.systemInitialized = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // 2 seconds
        
        // Callbacks for real-time data
        this.statusCallbacks = [];
        this.errorCallbacks = [];
        this.connectionCallbacks = [];
        
        this.init();
    }

    init() {
        console.log('🔌 Initializing Data Connector...');
        
        // Initialize WebSocket connection
        this.connectWebSocket();
        
        // Set up periodic connection health check
        setInterval(() => {
            this.checkConnectionHealth();
        }, 10000); // Check every 10 seconds
        
        console.log('✅ Data Connector initialized');
    }

    // WebSocket Management
    connectWebSocket() {
        try {
            console.log('📡 Connecting to WebSocket...');
            
            // Initialize Socket.IO connection
            this.socket = io(this.baseURL, {
                transports: ['websocket', 'polling'], // Fallback to polling if WebSocket fails
                timeout: 5000,
                reconnection: true,
                reconnectionDelay: this.reconnectDelay,
                reconnectionAttempts: this.maxReconnectAttempts
            });
            
            this.setupSocketEvents();
            
        } catch (error) {
            console.error('❌ WebSocket connection failed:', error);
            this.handleConnectionError(error);
        }
    }

    setupSocketEvents() {
        this.socket.on('connect', () => {
            console.log('✅ WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.notifyConnectionCallbacks('connected');
        });

        this.socket.on('disconnect', () => {
            console.log('⚠️ WebSocket disconnected');
            this.isConnected = false;
            this.notifyConnectionCallbacks('disconnected');
        });

        this.socket.on('status_update', (data) => {
            this.handleStatusUpdate(data);
        });

        this.socket.on('connection_status', (data) => {
            console.log('📊 Connection status:', data);
            this.systemInitialized = data.system_running || false;
        });

        this.socket.on('error', (error) => {
            console.error('❌ WebSocket error:', error);
            this.notifyErrorCallbacks(error);
        });

        this.socket.on('connect_error', (error) => {
            console.error('❌ WebSocket connection error:', error);
            this.handleConnectionError(error);
        });
    }

    // API Communication Methods
    async makeAPICall(endpoint, method = 'GET', data = null) {
        try {
            const config = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };

            if (data) {
                config.body = JSON.stringify(data);
            }

            const response = await fetch(`${this.baseURL}${endpoint}`, config);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();

        } catch (error) {
            console.error(`❌ API call failed [${method} ${endpoint}]:`, error);
            this.notifyErrorCallbacks(error);
            throw error;
        }
    }

    // System Control Methods
    async initializeSystem(bloodProductType = 'WHOLE_BLOOD') {
        console.log(`🏥 Initializing system with ${bloodProductType}...`);
        
        try {
            const result = await this.makeAPICall('/api/initialize', 'POST', {
                blood_product: bloodProductType
            });

            if (result.success) {
                this.systemInitialized = true;
                console.log('✅ System initialized successfully');
                return result;
            } else {
                throw new Error(result.message || 'Failed to initialize system');
            }

        } catch (error) {
            console.error('❌ System initialization failed:', error);
            throw error;
        }
    }

    async getSystemStatus() {
        try {
            return await this.makeAPICall('/api/status');
        } catch (error) {
            // Don't spam error logs for status requests
            if (!error.message.includes('System not initialized')) {
                console.error('❌ Failed to get system status:', error);
            }
            throw error;
        }
    }

    async shutdownSystem() {
        console.log('⏹️ Shutting down system...');
        
        try {
            const result = await this.makeAPICall('/api/shutdown', 'POST');
            
            if (result.success) {
                this.systemInitialized = false;
                console.log('✅ System shutdown successfully');
            }
            
            return result;

        } catch (error) {
            console.error('❌ System shutdown failed:', error);
            throw error;
        }
    }

    // PID Control Methods
    async setPIDGains(kp, ki, kd) {
        console.log(`🎛️ Setting PID gains: Kp=${kp}, Ki=${ki}, Kd=${kd}`);
        
        try {
            const result = await this.makeAPICall('/api/set_gains', 'POST', {
                kp: parseFloat(kp),
                ki: parseFloat(ki), 
                kd: parseFloat(kd)
            });

            if (result.success) {
                console.log('✅ PID gains updated successfully');
                return result;
            } else {
                throw new Error(result.error || 'Failed to set PID gains');
            }

        } catch (error) {
            console.error('❌ Failed to set PID gains:', error);
            
            // Show user-friendly error for safety violations
            if (error.message.includes('Invalid gains')) {
                this.showSafetyWarning('PID gains outside safe range!', error.message);
            }
            
            throw error;
        }
    }

    async setTargetTemperature(temperature) {
        console.log(`🎯 Setting target temperature: ${temperature}°C`);
        
        try {
            const result = await this.makeAPICall('/api/set_target', 'POST', {
                temperature: parseFloat(temperature)
            });

            if (result.success) {
                console.log('✅ Target temperature updated successfully');
                return result;
            } else {
                throw new Error(result.error || 'Failed to set target temperature');
            }

        } catch (error) {
            console.error('❌ Failed to set target temperature:', error);
            
            // Show user-friendly error for safety violations
            if (error.message.includes('outside safe range')) {
                this.showSafetyWarning('Temperature outside safe range!', error.message);
            }
            
            throw error;
        }
    }

    async setControlMode(mode) {
        console.log(`⚙️ Setting control mode: ${mode}`);
        
        try {
            const result = await this.makeAPICall('/api/control_mode', 'POST', {
                mode: mode.toLowerCase()
            });

            if (result.success) {
                console.log('✅ Control mode updated successfully');
                return result;
            } else {
                throw new Error(result.error || 'Failed to set control mode');
            }

        } catch (error) {
            console.error('❌ Failed to set control mode:', error);
            throw error;
        }
    }

    // Educational Methods
    async triggerDisturbance(magnitude = 2.0) {
        console.log(`🌪️ Triggering disturbance: ${magnitude}°C`);
        
        try {
            const result = await this.makeAPICall('/api/trigger_disturbance', 'POST', {
                magnitude: parseFloat(magnitude)
            });

            if (result.success) {
                console.log('✅ Disturbance triggered successfully');
                this.showEducationalTip(`Disturbance applied: ${magnitude}°C. Watch how the controller responds!`);
                return result;
            } else {
                throw new Error(result.error || 'Failed to trigger disturbance');
            }

        } catch (error) {
            console.error('❌ Failed to trigger disturbance:', error);
            throw error;
        }
    }

    async runExperiment(experimentType) {
        console.log(`🧪 Running experiment: ${experimentType}`);
        
        try {
            const result = await this.makeAPICall(`/api/experiments/${experimentType}`, 'POST');

            if (result.success) {
                console.log(`✅ Experiment ${experimentType} started successfully`);
                this.showExperimentResult(result.result);
                return result;
            } else {
                throw new Error(result.error || `Failed to run experiment: ${experimentType}`);
            }

        } catch (error) {
            console.error(`❌ Failed to run experiment ${experimentType}:`, error);
            throw error;
        }
    }

    async getHistoricalData(limit = 100, startTime = null) {
        try {
            let url = `/api/history?limit=${limit}`;
            if (startTime) {
                url += `&start_time=${startTime}`;
            }

            return await this.makeAPICall(url);

        } catch (error) {
            console.error('❌ Failed to get historical data:', error);
            throw error;
        }
    }

    // Callback Management
    onStatusUpdate(callback) {
        this.statusCallbacks.push(callback);
    }

    onError(callback) {
        this.errorCallbacks.push(callback);
    }

    onConnectionChange(callback) {
        this.connectionCallbacks.push(callback);
    }

    removeCallback(callbackArray, callback) {
        const index = callbackArray.indexOf(callback);
        if (index > -1) {
            callbackArray.splice(index, 1);
        }
    }

    // Event Handlers
    handleStatusUpdate(data) {
        // Add client-side timestamp
        data.client_timestamp = Date.now();
        
        // Notify all status callbacks
        this.statusCallbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('❌ Status callback error:', error);
            }
        });
    }

    handleConnectionError(error) {
        this.isConnected = false;
        this.reconnectAttempts++;
        
        if (this.reconnectAttempts <= this.maxReconnectAttempts) {
            console.log(`🔄 Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay * this.reconnectAttempts); // Exponential backoff
        } else {
            console.error('❌ Max reconnection attempts reached');
            this.showConnectionError('Lost connection to server. Please refresh the page.');
        }
    }

    notifyStatusCallbacks(data) {
        this.statusCallbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('❌ Status callback error:', error);
            }
        });
    }

    notifyErrorCallbacks(error) {
        this.errorCallbacks.forEach(callback => {
            try {
                callback(error);
            } catch (error) {
                console.error('❌ Error callback error:', error);
            }
        });
    }

    notifyConnectionCallbacks(status) {
        this.connectionCallbacks.forEach(callback => {
            try {
                callback(status);
            } catch (error) {
                console.error('❌ Connection callback error:', error);
            }
        });
    }

    // Connection Health
    checkConnectionHealth() {
        if (!this.isConnected && this.socket) {
            console.log('🔍 Checking connection health...');
            
            // Try to reconnect if not connected
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.connectWebSocket();
            }
        }
        
        // Update connection status indicator
        this.updateConnectionIndicator();
    }

    updateConnectionIndicator() {
        const indicator = document.getElementById('connection-status');
        if (indicator) {
            if (this.isConnected && this.systemInitialized) {
                indicator.textContent = 'Connected';
                indicator.className = 'connection-status connected';
            } else if (this.isConnected) {
                indicator.textContent = 'Connected (System Not Started)';
                indicator.className = 'connection-status partial';
            } else {
                indicator.textContent = 'Disconnected';
                indicator.className = 'connection-status disconnected';
            }
        }
    }

    // User Interface Helpers
    showSafetyWarning(title, message) {
        // Create safety warning popup
        const warning = document.createElement('div');
        warning.className = 'safety-warning';
        warning.innerHTML = `
            <div class="warning-content">
                <h3>⚠️ ${title}</h3>
                <p>${message}</p>
                <button onclick="this.parentElement.parentElement.remove()">Understood</button>
            </div>
        `;
        
        warning.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(239, 68, 68, 0.9);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 2000;
            color: white;
        `;
        
        warning.querySelector('.warning-content').style.cssText = `
            background: white;
            color: #dc2626;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            max-width: 400px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        `;
        
        warning.querySelector('button').style.cssText = `
            background: #dc2626;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 15px;
            font-weight: 600;
        `;
        
        document.body.appendChild(warning);
    }

    showEducationalTip(message) {
        // Reuse the educational tip system from PID lab
        if (window.pidLab && window.pidLab.showLearningTip) {
            window.pidLab.showLearningTip(message);
        } else {
            console.log(`💡 Educational Tip: ${message}`);
        }
    }

    showExperimentResult(result) {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'experiment-result-popup';
        resultDiv.innerHTML = `
            <div class="result-content">
                <h3>🧪 Experiment Started</h3>
                <h4>${result.description}</h4>
                <p><strong>Expected Result:</strong> ${result.expected_result}</p>
                <p><strong>Learning Objective:</strong> ${result.learning_objective}</p>
                <button onclick="this.parentElement.parentElement.remove()">Continue Watching</button>
            </div>
        `;
        
        resultDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            z-index: 1500;
            max-width: 450px;
            text-align: center;
        `;
        
        resultDiv.querySelector('button').style.cssText = `
            background: rgba(255,255,255,0.2);
            border: 2px solid white;
            color: white;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 15px;
            font-weight: 600;
        `;
        
        document.body.appendChild(resultDiv);
    }

    showConnectionError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'connection-error';
        errorDiv.innerHTML = `
            <div class="error-content">
                <h3>📡 Connection Error</h3>
                <p>${message}</p>
                <button onclick="window.location.reload()">Refresh Page</button>
            </div>
        `;
        
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 1000;
            max-width: 300px;
        `;
        
        errorDiv.querySelector('button').style.cssText = `
            background: rgba(255,255,255,0.2);
            border: 1px solid white;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 10000);
    }

    // Utility Methods
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            systemInitialized: this.systemInitialized,
            reconnectAttempts: this.reconnectAttempts
        };
    }

    // Public API for easy integration
    isSystemReady() {
        return this.isConnected && this.systemInitialized;
    }

    async ensureSystemReady() {
        if (!this.isConnected) {
            throw new Error('Not connected to server');
        }
        
        if (!this.systemInitialized) {
            console.log('🔄 System not initialized, initializing now...');
            await this.initializeSystem();
        }
    }
}

// Global functions for UI integration
async function initializeSystemFromUI(bloodProductType = 'WHOLE_BLOOD') {
    try {
        if (window.dataConnector) {
            const result = await window.dataConnector.initializeSystem(bloodProductType);
            console.log('✅ System initialized from UI');
            return result;
        }
    } catch (error) {
        console.error('❌ Failed to initialize system from UI:', error);
        alert(`Failed to initialize system: ${error.message}`);
    }
}

async function triggerDisturbanceFromUI(magnitude = 2.0) {
    try {
        if (window.dataConnector && window.dataConnector.isSystemReady()) {
            await window.dataConnector.triggerDisturbance(magnitude);
        } else {
            alert('System not ready. Please initialize the system first.');
        }
    } catch (error) {
        console.error('❌ Failed to trigger disturbance from UI:', error);
    }
}

async function runExperimentFromUI(experimentType) {
    try {
        if (window.dataConnector && window.dataConnector.isSystemReady()) {
            await window.dataConnector.runExperiment(experimentType);
        } else {
            alert('System not ready. Please initialize the system first.');
        }
    } catch (error) {
        console.error(`❌ Failed to run experiment ${experimentType} from UI:`, error);
    }
}

// Include Socket.IO client library check
function ensureSocketIOLoaded() {
    if (typeof io === 'undefined') {
        console.error('❌ Socket.IO client library not loaded!');
        
        // Dynamically load Socket.IO if not present
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js';
        script.onload = () => {
            console.log('✅ Socket.IO loaded dynamically');
            if (window.dataConnector) {
                window.dataConnector.connectWebSocket();
            }
        };
        document.head.appendChild(script);
        
        return false;
    }
    return true;
}

// Initialize data connector when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (ensureSocketIOLoaded()) {
        window.dataConnector = new DataConnector();
        console.log('🔌 Data Connector ready!');
    } else {
        // Will initialize after Socket.IO loads
        setTimeout(() => {
            window.dataConnector = new DataConnector();
            console.log('🔌 Data Connector ready (after Socket.IO load)!');
        }, 1000);
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataConnector;
}