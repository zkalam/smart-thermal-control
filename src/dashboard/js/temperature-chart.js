/**
 * Real-Time Temperature Chart
 * Educational visualization component for temperature control
 */

class TemperatureChart {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        // Chart configuration
        this.config = {
            maxDataPoints: 300,
            timeWindow: 60, // seconds
            updateInterval: 100, // ms
            
            // Display options
            showSetpoint: true,
            showError: true,
            showOutput: true,
            
            // Visual styling
            backgroundColor: '#ffffff',
            gridColor: '#e5e7eb',
            textColor: '#374151',
            
            // Line colors
            temperatureColor: '#ef4444',
            setpointColor: '#10b981',
            errorColor: '#f59e0b',
            outputColor: '#3b82f6'
        };
        
        // Data storage
        this.data = {
            temperature: [],
            setpoint: [],
            error: [],
            output: [],
            timestamps: []
        };
        
        // Chart dimensions
        this.margins = { top: 40, right: 80, bottom: 40, left: 60 };
        this.chartArea = {
            x: this.margins.left,
            y: this.margins.top,
            width: this.canvas.width - this.margins.left - this.margins.right,
            height: this.canvas.height - this.margins.top - this.margins.bottom
        };
        
        this.init();
    }

    init() {
        console.log('📊 Initializing Temperature Chart...');
        
        // Set up canvas
        this.setupCanvas();
        
        // Start drawing loop
        this.startDrawLoop();
        
        console.log('✅ Temperature Chart ready!');
    }

    setupCanvas() {
        // Handle high DPI displays
        const devicePixelRatio = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();
        
        this.canvas.width = rect.width * devicePixelRatio;
        this.canvas.height = rect.height * devicePixelRatio;
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
        
        this.ctx.scale(devicePixelRatio, devicePixelRatio);
        
        // Update chart area for new dimensions
        this.chartArea = {
            x: this.margins.left,
            y: this.margins.top,
            width: rect.width - this.margins.left - this.margins.right,
            height: rect.height - this.margins.top - this.margins.bottom
        };
    }

    addDataPoint(dataPoint) {
        const now = Date.now();
        
        // Add new data
        this.data.timestamps.push(now);
        this.data.temperature.push(dataPoint.temperature);
        this.data.setpoint.push(dataPoint.target);
        this.data.error.push(dataPoint.error);
        this.data.output.push(dataPoint.output);
        
        // Remove old data to maintain window size
        const cutoffTime = now - (this.config.timeWindow * 1000);
        this.removeOldData(cutoffTime);
    }

    removeOldData(cutoffTime) {
        while (this.data.timestamps.length > 0 && this.data.timestamps[0] < cutoffTime) {
            this.data.timestamps.shift();
            this.data.temperature.shift();
            this.data.setpoint.shift();
            this.data.error.shift();
            this.data.output.shift();
        }
        
        // Also enforce max data points limit
        while (this.data.timestamps.length > this.config.maxDataPoints) {
            this.data.timestamps.shift();
            this.data.temperature.shift();
            this.data.setpoint.shift();
            this.data.error.shift();
            this.data.output.shift();
        }
    }

    startDrawLoop() {
        const draw = () => {
            this.draw();
            requestAnimationFrame(draw);
        };
        draw();
    }

    draw() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Fill background
        this.ctx.fillStyle = this.config.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        if (this.data.timestamps.length < 2) {
            this.drawEmptyState();
            return;
        }
        
        // Draw chart elements
        this.drawGrid();
        this.drawAxes();
        
        // Draw data lines
        if (this.config.showSetpoint) this.drawLine('setpoint', this.config.setpointColor, 2);
        if (this.config.showOutput) this.drawOutputBars();
        this.drawLine('temperature', this.config.temperatureColor, 3);
        if (this.config.showError) this.drawLine('error', this.config.errorColor, 2, true);
        
        // Draw legend and labels
        this.drawLegend();
        this.drawLabels();
        this.drawEducationalAnnotations();
    }

    drawGrid() {
        this.ctx.strokeStyle = this.config.gridColor;
        this.ctx.lineWidth = 1;
        this.ctx.setLineDash([2, 2]);
        
        // Vertical grid lines (time)
        const timeSpan = this.config.timeWindow * 1000;
        const gridInterval = timeSpan / 6; // 6 vertical lines
        
        for (let i = 0; i <= 6; i++) {
            const x = this.chartArea.x + (i * this.chartArea.width / 6);
            this.ctx.beginPath();
            this.ctx.moveTo(x, this.chartArea.y);
            this.ctx.lineTo(x, this.chartArea.y + this.chartArea.height);
            this.ctx.stroke();
        }
        
        // Horizontal grid lines (temperature)
        for (let i = 0; i <= 5; i++) {
            const y = this.chartArea.y + (i * this.chartArea.height / 5);
            this.ctx.beginPath();
            this.ctx.moveTo(this.chartArea.x, y);
            this.ctx.lineTo(this.chartArea.x + this.chartArea.width, y);
            this.ctx.stroke();
        }
        
        this.ctx.setLineDash([]);
    }

    drawAxes() {
        this.ctx.strokeStyle = this.config.textColor;
        this.ctx.lineWidth = 2;
        
        // Y-axis
        this.ctx.beginPath();
        this.ctx.moveTo(this.chartArea.x, this.chartArea.y);
        this.ctx.lineTo(this.chartArea.x, this.chartArea.y + this.chartArea.height);
        this.ctx.stroke();
        
        // X-axis
        this.ctx.beginPath();
        this.ctx.moveTo(this.chartArea.x, this.chartArea.y + this.chartArea.height);
        this.ctx.lineTo(this.chartArea.x + this.chartArea.width, this.chartArea.y + this.chartArea.height);
        this.ctx.stroke();
        
        // Y-axis labels (temperature)
        this.ctx.fillStyle = this.config.textColor;
        this.ctx.font = '12px sans-serif';
        this.ctx.textAlign = 'right';
        this.ctx.textBaseline = 'middle';
        
        const tempRange = this.getTemperatureRange();
        for (let i = 0; i <= 5; i++) {
            const temp = tempRange.min + (i * (tempRange.max - tempRange.min) / 5);
            const y = this.chartArea.y + this.chartArea.height - (i * this.chartArea.height / 5);
            this.ctx.fillText(temp.toFixed(1) + '°C', this.chartArea.x - 10, y);
        }
        
        // X-axis labels (time)
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'top';
        
        for (let i = 0; i <= 6; i++) {
            const secondsAgo = (6 - i) * this.config.timeWindow / 6;
            const x = this.chartArea.x + (i * this.chartArea.width / 6);
            this.ctx.fillText(`-${secondsAgo.toFixed(0)}s`, x, this.chartArea.y + this.chartArea.height + 5);
        }
    }

    drawLine(dataKey, color, lineWidth, isError = false) {
        if (this.data[dataKey].length < 2) return;
        
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = lineWidth;
        this.ctx.setLineDash([]);
        
        const range = isError ? this.getErrorRange() : this.getTemperatureRange();
        const now = Date.now();
        const timeSpan = this.config.timeWindow * 1000;
        
        this.ctx.beginPath();
        
        for (let i = 0; i < this.data[dataKey].length; i++) {
            const value = this.data[dataKey][i];
            const timestamp = this.data.timestamps[i];
            
            const x = this.chartArea.x + ((now - timestamp) / timeSpan) * this.chartArea.width;
            const x_pos = this.chartArea.x + this.chartArea.width - x + this.chartArea.x;
            
            let y;
            if (isError) {
                // Center error around middle of chart
                const errorCenter = this.chartArea.y + this.chartArea.height / 2;
                y = errorCenter - (value / (range.max - range.min)) * this.chartArea.height / 4;
            } else {
                y = this.chartArea.y + this.chartArea.height - 
                    ((value - range.min) / (range.max - range.min)) * this.chartArea.height;
            }
            
            if (i === 0) {
                this.ctx.moveTo(x_pos, y);
            } else {
                this.ctx.lineTo(x_pos, y);
            }
        }
        
        this.ctx.stroke();
    }

    drawOutputBars() {
        if (this.data.output.length === 0) return;
        
        this.ctx.fillStyle = this.config.outputColor + '40'; // Semi-transparent
        
        const now = Date.now();
        const timeSpan = this.config.timeWindow * 1000;
        const outputRange = this.getOutputRange();
        const zeroY = this.chartArea.y + this.chartArea.height / 2;
        
        for (let i = 0; i < this.data.output.length; i++) {
            const value = this.data.output[i];
            const timestamp = this.data.timestamps[i];
            
            const x = this.chartArea.x + ((now - timestamp) / timeSpan) * this.chartArea.width;
            const x_pos = this.chartArea.x + this.chartArea.width - x + this.chartArea.x;
            
            const barHeight = Math.abs(value) / Math.max(Math.abs(outputRange.max), Math.abs(outputRange.min)) * this.chartArea.height / 4;
            const barY = value >= 0 ? zeroY - barHeight : zeroY;
            
            this.ctx.fillRect(x_pos - 1, barY, 2, Math.abs(barHeight));
        }
    }

    drawLegend() {
        const legendX = this.chartArea.x + this.chartArea.width + 10;
        let legendY = this.chartArea.y + 20;
        
        this.ctx.font = '12px sans-serif';
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'middle';
        
        const legendItems = [
            { label: 'Temperature', color: this.config.temperatureColor, show: true },
            { label: 'Setpoint', color: this.config.setpointColor, show: this.config.showSetpoint },
            { label: 'Error', color: this.config.errorColor, show: this.config.showError },
            { label: 'Output', color: this.config.outputColor, show: this.config.showOutput }
        ];
        
        legendItems.forEach(item => {
            if (!item.show) return;
            
            // Draw color indicator
            this.ctx.fillStyle = item.color;
            this.ctx.fillRect(legendX, legendY - 4, 12, 8);
            
            // Draw label
            this.ctx.fillStyle = this.config.textColor;
            this.ctx.fillText(item.label, legendX + 18, legendY);
            
            legendY += 20;
        });
    }

    drawLabels() {
        // Chart title
        this.ctx.font = 'bold 16px sans-serif';
        this.ctx.fillStyle = this.config.textColor;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'top';
        this.ctx.fillText('Real-Time System Response', 
                         this.chartArea.x + this.chartArea.width / 2, 10);
        
        // Y-axis label
        this.ctx.save();
        this.ctx.translate(15, this.chartArea.y + this.chartArea.height / 2);
        this.ctx.rotate(-Math.PI / 2);
        this.ctx.font = '14px sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('Temperature (°C)', 0, 0);
        this.ctx.restore();
        
        // X-axis label
        this.ctx.font = '14px sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'bottom';
        this.ctx.fillText('Time (seconds ago)', 
                         this.chartArea.x + this.chartArea.width / 2, 
                         this.canvas.height - 5);
    }

    drawEducationalAnnotations() {
        if (this.data.temperature.length === 0) return;
        
        // Current values box
        const currentTemp = this.data.temperature[this.data.temperature.length - 1];
        const currentTarget = this.data.setpoint[this.data.setpoint.length - 1];
        const currentError = this.data.error[this.data.error.length - 1];
        
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
        this.ctx.strokeStyle = this.config.textColor;
        this.ctx.lineWidth = 1;
        
        const boxX = this.chartArea.x + 10;
        const boxY = this.chartArea.y + 10;
        const boxWidth = 200;
        const boxHeight = 80;
        
        this.ctx.fillRect(boxX, boxY, boxWidth, boxHeight);
        this.ctx.strokeRect(boxX, boxY, boxWidth, boxHeight);
        
        // Current values text
        this.ctx.fillStyle = this.config.textColor;
        this.ctx.font = '12px sans-serif';
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'top';
        
        this.ctx.fillText(`Current: ${currentTemp.toFixed(2)}°C`, boxX + 10, boxY + 10);
        this.ctx.fillText(`Target: ${currentTarget.toFixed(2)}°C`, boxX + 10, boxY + 25);
        this.ctx.fillText(`Error: ${currentError.toFixed(2)}°C`, boxX + 10, boxY + 40);
        
        // Performance indicator
        const performance = Math.abs(currentError) < 0.1 ? 'Excellent' : 
                           Math.abs(currentError) < 0.5 ? 'Good' : 'Needs Adjustment';
        const perfColor = Math.abs(currentError) < 0.1 ? '#10b981' : 
                         Math.abs(currentError) < 0.5 ? '#f59e0b' : '#ef4444';
        
        this.ctx.fillStyle = perfColor;
        this.ctx.fillText(`Performance: ${performance}`, boxX + 10, boxY + 55);
    }

    drawEmptyState() {
        this.ctx.fillStyle = this.config.textColor;
        this.ctx.font = '16px sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText('Waiting for data...', 
                         this.canvas.width / 2, this.canvas.height / 2);
    }

    getTemperatureRange() {
        if (this.data.temperature.length === 0) return { min: 0, max: 10 };
        
        const allTemps = [...this.data.temperature, ...this.data.setpoint];
        const min = Math.min(...allTemps);
        const max = Math.max(...allTemps);
        const padding = (max - min) * 0.1 || 1;
        
        return { 
            min: min - padding, 
            max: max + padding 
        };
    }

    getErrorRange() {
        if (this.data.error.length === 0) return { min: -1, max: 1 };
        
        const maxError = Math.max(...this.data.error.map(Math.abs));
        return { min: -maxError, max: maxError };
    }

    getOutputRange() {
        if (this.data.output.length === 0) return { min: -100, max: 100 };
        
        const min = Math.min(...this.data.output);
        const max = Math.max(...this.data.output);
        
        return { min, max };
    }

    // Public API methods
    toggleSetpoint(show) {
        this.config.showSetpoint = show;
        console.log(`📊 Setpoint display: ${show ? 'ON' : 'OFF'}`);
    }

    toggleError(show) {
        this.config.showError = show;
        console.log(`📊 Error display: ${show ? 'ON' : 'OFF'}`);
    }

    toggleOutput(show) {
        this.config.showOutput = show;
        console.log(`📊 Output display: ${show ? 'ON' : 'OFF'}`);
    }

    setTimeWindow(seconds) {
        this.config.timeWindow = seconds;
        console.log(`📊 Time window: ${seconds} seconds`);
    }

    clear() {
        this.data = {
            temperature: [],
            setpoint: [],
            error: [],
            output: [],
            timestamps: []
        };
        console.log('📊 Chart data cleared');
    }

    resize() {
        this.setupCanvas();
        console.log('📊 Chart resized');
    }

    // Educational methods
    highlightFeature(feature) {
        // Temporarily highlight specific chart features for educational purposes
        switch(feature) {
            case 'overshoot':
                this.drawOvershootAnnotation();
                break;
            case 'steady-state':
                this.drawSteadyStateAnnotation();
                break;
            case 'oscillation':
                this.drawOscillationAnnotation();
                break;
        }
    }

    drawOvershootAnnotation() {
        // Find and highlight overshoot in temperature data
        if (this.data.temperature.length < 10) return;
        
        const recentData = this.data.temperature.slice(-30);
        const maxTemp = Math.max(...recentData);
        const targetTemp = this.data.setpoint[this.data.setpoint.length - 1];
        
        if (maxTemp > targetTemp + 0.2) {
            // Draw overshoot annotation
            this.ctx.fillStyle = 'rgba(239, 68, 68, 0.3)';
            this.ctx.strokeStyle = '#ef4444';
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash([5, 5]);
            
            // Draw annotation box
            const boxX = this.chartArea.x + this.chartArea.width * 0.7;
            const boxY = this.chartArea.y + 20;
            
            this.ctx.fillRect(boxX, boxY, 150, 60);
            this.ctx.strokeRect(boxX, boxY, 150, 60);
            
            this.ctx.fillStyle = '#dc2626';
            this.ctx.font = 'bold 12px sans-serif';
            this.ctx.textAlign = 'left';
            this.ctx.fillText('⚠️ OVERSHOOT DETECTED', boxX + 10, boxY + 20);
            this.ctx.font = '10px sans-serif';
            this.ctx.fillText(`Peak: ${maxTemp.toFixed(2)}°C`, boxX + 10, boxY + 35);
            this.ctx.fillText(`Target: ${targetTemp.toFixed(2)}°C`, boxX + 10, boxY + 50);
            
            this.ctx.setLineDash([]);
        }
    }

    drawSteadyStateAnnotation() {
        // Analyze for steady-state error
        if (this.data.temperature.length < 20) return;
        
        const recentTemps = this.data.temperature.slice(-20);
        const recentTargets = this.data.setpoint.slice(-20);
        
        const avgTemp = recentTemps.reduce((a, b) => a + b) / recentTemps.length;
        const avgTarget = recentTargets.reduce((a, b) => a + b) / recentTargets.length;
        const steadyStateError = Math.abs(avgTemp - avgTarget);
        
        if (steadyStateError > 0.1) {
            this.ctx.fillStyle = 'rgba(245, 158, 11, 0.3)';
            this.ctx.strokeStyle = '#f59e0b';
            this.ctx.lineWidth = 2;
            
            const boxX = this.chartArea.x + this.chartArea.width * 0.6;
            const boxY = this.chartArea.y + this.chartArea.height - 80;
            
            this.ctx.fillRect(boxX, boxY, 180, 60);
            this.ctx.strokeRect(boxX, boxY, 180, 60);
            
            this.ctx.fillStyle = '#d97706';
            this.ctx.font = 'bold 12px sans-serif';
            this.ctx.textAlign = 'left';
            this.ctx.fillText('📍 STEADY-STATE ERROR', boxX + 10, boxY + 20);
            this.ctx.font = '10px sans-serif';
            this.ctx.fillText(`Error: ${steadyStateError.toFixed(3)}°C`, boxX + 10, boxY + 35);
            this.ctx.fillText('Consider increasing Ki', boxX + 10, boxY + 50);
        }
    }

    drawOscillationAnnotation() {
        // Detect oscillatory behavior
        if (this.data.temperature.length < 30) return;
        
        const recentData = this.data.temperature.slice(-30);
        const peaks = this.findPeaks(recentData);
        
        if (peaks.length > 3) {
            this.ctx.fillStyle = 'rgba(139, 92, 246, 0.3)';
            this.ctx.strokeStyle = '#8b5cf6';
            this.ctx.lineWidth = 2;
            
            const boxX = this.chartArea.x + 20;
            const boxY = this.chartArea.y + this.chartArea.height - 80;
            
            this.ctx.fillRect(boxX, boxY, 160, 60);
            this.ctx.strokeRect(boxX, boxY, 160, 60);
            
            this.ctx.fillStyle = '#7c3aed';
            this.ctx.font = 'bold 12px sans-serif';
            this.ctx.textAlign = 'left';
            this.ctx.fillText('🌊 OSCILLATION', boxX + 10, boxY + 20);
            this.ctx.font = '10px sans-serif';
            this.ctx.fillText(`${peaks.length} peaks detected`, boxX + 10, boxY + 35);
            this.ctx.fillText('Try reducing Kp or Ki', boxX + 10, boxY + 50);
        }
    }

    findPeaks(data) {
        const peaks = [];
        for (let i = 1; i < data.length - 1; i++) {
            if (data[i] > data[i-1] && data[i] > data[i+1]) {
                peaks.push(i);
            }
        }
        return peaks;
    }

    // Educational demonstration methods
    demonstrateStepResponse() {
        console.log('📈 Demonstrating step response...');
        // This would trigger a setpoint change in the control system
        // and highlight the resulting response characteristics
        
        setTimeout(() => {
            this.highlightFeature('overshoot');
        }, 2000);
        
        setTimeout(() => {
            this.highlightFeature('steady-state');
        }, 5000);
    }

    demonstrateDisturbanceResponse() {
        console.log('🌪️ Demonstrating disturbance response...');
        // This would trigger a disturbance and show how the controller responds
        
        if (window.dashboard) {
            window.dashboard.triggerDisturbance(1.0);
        }
        
        setTimeout(() => {
            this.highlightFeature('oscillation');
        }, 3000);
    }

    // Export chart data for analysis
    exportData() {
        const chartData = {
            timestamps: [...this.data.timestamps],
            temperature: [...this.data.temperature],
            setpoint: [...this.data.setpoint],
            error: [...this.data.error],
            output: [...this.data.output],
            config: { ...this.config }
        };
        
        const dataStr = JSON.stringify(chartData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `temperature_data_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        console.log('📊 Chart data exported');
    }
}

// Global chart functions
function adjustTimeScale(seconds) {
    if (window.temperatureChart) {
        window.temperatureChart.setTimeWindow(seconds);
    }
    
    // Update active button
    document.querySelectorAll('.time-controls button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    console.log(`📊 Chart time scale: ${seconds}s`);
}

function clearChart() {
    if (window.temperatureChart) {
        window.temperatureChart.clear();
    }
}

function exportChartData() {
    if (window.temperatureChart) {
        window.temperatureChart.exportData();
    }
}

function demonstrateStepResponse() {
    if (window.temperatureChart) {
        window.temperatureChart.demonstrateStepResponse();
    }
}

function demonstrateDisturbanceResponse() {
    if (window.temperatureChart) {
        window.temperatureChart.demonstrateDisturbanceResponse();
    }
}

// Initialize temperature chart when page loads
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('temperature-chart');
    if (canvas) {
        window.temperatureChart = new TemperatureChart('temperature-chart');
        console.log('📊 Temperature Chart initialized!');
    }
});

// Handle window resize
window.addEventListener('resize', () => {
    if (window.temperatureChart) {
        setTimeout(() => {
            window.temperatureChart.resize();
        }, 100);
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TemperatureChart;
}