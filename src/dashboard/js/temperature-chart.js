/**
 * Enhanced Temperature Chart - Better Time Management and Responsiveness
 * Fixes: 1) Limited time display, 2) Slow response issues
 */

class TemperatureChart {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error(`Canvas ${canvasId} not found`);
            return;
        }
        
        this.ctx = this.canvas.getContext('2d');
        this.data = [];
        this.maxDataPoints = 1000; // Increased from default
        this.timeWindow = 60; // Default 1 minute window (in seconds)
        this.isRunning = true;
        
        // Chart display options
        this.showSetpoint = true;
        this.showError = true;
        this.showOutput = true;
        
        // Colors for dark theme
        this.colors = {
            temperature: '#ef4444',    // Red
            setpoint: '#10b981',       // Green  
            error: '#f59e0b',         // Orange
            output: '#3b82f6',        // Blue
            grid: '#334155',          // Dark gray
            text: '#94a3b8',          // Light gray
            background: '#1e293b'     // Dark background
        };
        
        this.init();
    }
    
    init() {
        console.log('📊 Initializing Enhanced Temperature Chart...');
        
        // Set up canvas
        this.setupCanvas();
        
        // Start the animation loop
        this.startAnimationLoop();
        
        // Set up event listeners
        this.setupEventListeners();
        
        console.log('✅ Temperature Chart initialized!');
    }
    
    setupCanvas() {
        // Set canvas size for better resolution
        const rect = this.canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        
        this.ctx.scale(dpr, dpr);
        
        // Set canvas display size
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
    }
    
    setupEventListeners() {
        // Handle window resize
        window.addEventListener('resize', () => {
            this.setupCanvas();
        });
        
        // Chart control buttons
        document.getElementById('show-setpoint')?.addEventListener('change', (e) => {
            this.showSetpoint = e.target.checked;
        });
        
        document.getElementById('show-error')?.addEventListener('change', (e) => {
            this.showError = e.target.checked;
        });
        
        document.getElementById('show-output')?.addEventListener('change', (e) => {
            this.showOutput = e.target.checked;
        });
    }
    
    addDataPoint(dataPoint) {
        // Enhanced data point with timestamp
        const point = {
            time: dataPoint.time || Date.now(),
            temperature: dataPoint.temperature || 0,
            target: dataPoint.target || 0,
            error: dataPoint.error || 0,
            output: dataPoint.output || 0
        };
        
        this.data.push(point);
        
        // Remove old data points beyond our time window and max points
        const cutoffTime = Date.now() - (this.timeWindow * 1000);
        this.data = this.data.filter(p => p.time > cutoffTime);
        
        // Also limit by max points for performance
        if (this.data.length > this.maxDataPoints) {
            this.data = this.data.slice(-this.maxDataPoints);
        }
        
        // Force a redraw
        this.needsRedraw = true;
    }
    
    startAnimationLoop() {
        const animate = () => {
            if (this.isRunning) {
                this.draw();
                requestAnimationFrame(animate);
            }
        };
        animate();
    }
    
    draw() {
        if (!this.ctx) return;
        
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;
        
        // Clear canvas
        this.ctx.fillStyle = this.colors.background;
        this.ctx.fillRect(0, 0, width, height);
        
        if (this.data.length < 2) {
            this.drawNoDataMessage(width, height);
            return;
        }
        
        // Calculate chart area (leave space for labels)
        const padding = { top: 40, right: 80, bottom: 60, left: 80 };
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;
        
        // Calculate time and value ranges
        const timeRange = this.calculateTimeRange();
        const valueRange = this.calculateValueRange();
        
        // Draw grid
        this.drawGrid(padding, chartWidth, chartHeight, timeRange, valueRange);
        
        // Draw data lines
        if (this.showSetpoint) {
            this.drawLine('target', padding, chartWidth, chartHeight, timeRange, valueRange, this.colors.setpoint, 2);
        }
        
        this.drawLine('temperature', padding, chartWidth, chartHeight, timeRange, valueRange, this.colors.temperature, 3);
        
        if (this.showError) {
            this.drawLine('error', padding, chartWidth, chartHeight, timeRange, valueRange, this.colors.error, 2);
        }
        
        if (this.showOutput) {
            this.drawOutputLine(padding, chartWidth, chartHeight, timeRange, valueRange);
        }
        
        // Draw legend
        this.drawLegend(width, height);
        
        // Draw current values box
        this.drawCurrentValues(padding);
    }
    
    calculateTimeRange() {
        if (this.data.length === 0) return { min: 0, max: 1000 };
        
        const now = Date.now();
        const timeWindow = this.timeWindow * 1000; // Convert to milliseconds
        
        return {
            min: now - timeWindow,
            max: now
        };
    }
    
    calculateValueRange() {
        if (this.data.length === 0) {
            return { min: 0, max: 10 };
        }
        
        let minTemp = Infinity;
        let maxTemp = -Infinity;
        let minOutput = Infinity;
        let maxOutput = -Infinity;
        
        // Filter data to current time window
        const cutoffTime = Date.now() - (this.timeWindow * 1000);
        const visibleData = this.data.filter(p => p.time > cutoffTime);
        
        visibleData.forEach(point => {
            minTemp = Math.min(minTemp, point.temperature, point.target);
            maxTemp = Math.max(maxTemp, point.temperature, point.target);
            
            if (this.showError) {
                minTemp = Math.min(minTemp, point.error);
                maxTemp = Math.max(maxTemp, point.error);
            }
            
            if (this.showOutput) {
                minOutput = Math.min(minOutput, point.output);
                maxOutput = Math.max(maxOutput, point.output);
            }
        });
        
        // Add some padding to the range
        const tempPadding = (maxTemp - minTemp) * 0.1 || 1;
        
        return {
            minTemp: minTemp - tempPadding,
            maxTemp: maxTemp + tempPadding,
            minOutput: minOutput,
            maxOutput: maxOutput
        };
    }
    
    drawGrid(padding, chartWidth, chartHeight, timeRange, valueRange) {
        this.ctx.strokeStyle = this.colors.grid;
        this.ctx.lineWidth = 1;
        this.ctx.font = '12px Inter, sans-serif';
        this.ctx.fillStyle = this.colors.text;
        
        // Vertical grid lines (time)
        const timeStep = (timeRange.max - timeRange.min) / 6;
        for (let i = 0; i <= 6; i++) {
            const time = timeRange.min + (i * timeStep);
            const x = padding.left + (i * chartWidth / 6);
            
            // Draw line
            this.ctx.beginPath();
            this.ctx.moveTo(x, padding.top);
            this.ctx.lineTo(x, padding.top + chartHeight);
            this.ctx.stroke();
            
            // Draw label
            const secondsAgo = Math.round((Date.now() - time) / 1000);
            const label = secondsAgo === 0 ? '0s' : `-${secondsAgo}s`;
            this.ctx.fillText(label, x - 15, padding.top + chartHeight + 20);
        }
        
        // Horizontal grid lines (temperature)
        const tempStep = (valueRange.maxTemp - valueRange.minTemp) / 5;
        for (let i = 0; i <= 5; i++) {
            const temp = valueRange.minTemp + (i * tempStep);
            const y = padding.top + chartHeight - (i * chartHeight / 5);
            
            // Draw line
            this.ctx.beginPath();
            this.ctx.moveTo(padding.left, y);
            this.ctx.lineTo(padding.left + chartWidth, y);
            this.ctx.stroke();
            
            // Draw label
            this.ctx.fillText(temp.toFixed(1) + '°C', 5, y + 5);
        }
    }
    
    drawLine(dataKey, padding, chartWidth, chartHeight, timeRange, valueRange, color, lineWidth = 2) {
        const cutoffTime = Date.now() - (this.timeWindow * 1000);
        const visibleData = this.data.filter(p => p.time > cutoffTime);
        
        if (visibleData.length < 2) return;
        
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = lineWidth;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        
        this.ctx.beginPath();
        
        visibleData.forEach((point, index) => {
            const x = padding.left + ((point.time - timeRange.min) / (timeRange.max - timeRange.min)) * chartWidth;
            const y = padding.top + chartHeight - ((point[dataKey] - valueRange.minTemp) / (valueRange.maxTemp - valueRange.minTemp)) * chartHeight;
            
            if (index === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        });
        
        this.ctx.stroke();
    }
    
    drawOutputLine(padding, chartWidth, chartHeight, timeRange, valueRange) {
        const cutoffTime = Date.now() - (this.timeWindow * 1000);
        const visibleData = this.data.filter(p => p.time > cutoffTime);
        
        if (visibleData.length < 2) return;
        
        // Scale output to fit in the chart (secondary axis)
        const outputScale = chartHeight * 0.3; // Use bottom 30% of chart
        
        this.ctx.strokeStyle = this.colors.output;
        this.ctx.lineWidth = 2;
        this.ctx.globalAlpha = 0.7; // Make it semi-transparent
        
        this.ctx.beginPath();
        
        visibleData.forEach((point, index) => {
            const x = padding.left + ((point.time - timeRange.min) / (timeRange.max - timeRange.min)) * chartWidth;
            
            // Scale output value to chart coordinates
            const outputRange = valueRange.maxOutput - valueRange.minOutput || 100;
            const normalizedOutput = (point.output - valueRange.minOutput) / outputRange;
            const y = padding.top + chartHeight - (normalizedOutput * outputScale);
            
            if (index === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        });
        
        this.ctx.stroke();
        this.ctx.globalAlpha = 1.0; // Reset alpha
    }
    
    drawLegend(width, height) {
        const legendX = width - 120;
        const legendY = 20;
        
        this.ctx.font = '12px Inter, sans-serif';
        
        const items = [
            { name: 'Temperature', color: this.colors.temperature, show: true },
            { name: 'Setpoint', color: this.colors.setpoint, show: this.showSetpoint },
            { name: 'Error', color: this.colors.error, show: this.showError },
            { name: 'Output', color: this.colors.output, show: this.showOutput }
        ];
        
        items.forEach((item, index) => {
            if (!item.show) return;
            
            const y = legendY + (index * 20);
            
            // Draw color indicator
            this.ctx.fillStyle = item.color;
            this.ctx.fillRect(legendX, y - 5, 15, 3);
            
            // Draw text
            this.ctx.fillStyle = this.colors.text;
            this.ctx.fillText(item.name, legendX + 20, y);
        });
    }
    
    drawCurrentValues(padding) {
        if (this.data.length === 0) return;
        
        const latest = this.data[this.data.length - 1];
        const boxX = padding.left + 10;
        const boxY = padding.top + 10;
        const boxWidth = 200;
        const boxHeight = 80;
        
        // Draw background
        this.ctx.fillStyle = 'rgba(30, 41, 59, 0.9)';
        this.ctx.fillRect(boxX, boxY, boxWidth, boxHeight);
        
        // Draw border
        this.ctx.strokeStyle = this.colors.grid;
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(boxX, boxY, boxWidth, boxHeight);
        
        // Draw text
        this.ctx.font = 'bold 12px Inter, sans-serif';
        this.ctx.fillStyle = this.colors.text;
        
        const textX = boxX + 10;
        let textY = boxY + 20;
        
        this.ctx.fillText(`Current: ${latest.temperature.toFixed(2)}°C`, textX, textY);
        textY += 15;
        this.ctx.fillText(`Target: ${latest.target.toFixed(2)}°C`, textX, textY);
        textY += 15;
        this.ctx.fillText(`Error: ${latest.error.toFixed(2)}°C`, textX, textY);
        
        // Performance indicator
        const errorMagnitude = Math.abs(latest.error);
        let performance = 'Excellent';
        let perfColor = this.colors.setpoint;
        
        if (errorMagnitude > 0.5) {
            performance = 'Needs Adjustment';
            perfColor = this.colors.error;
        } else if (errorMagnitude > 0.2) {
            performance = 'Good';
            perfColor = this.colors.temperature;
        }
        
        textY += 15;
        this.ctx.fillStyle = perfColor;
        this.ctx.fillText(`Performance: ${performance}`, textX, textY);
    }
    
    drawNoDataMessage(width, height) {
        this.ctx.font = '16px Inter, sans-serif';
        this.ctx.fillStyle = this.colors.text;
        this.ctx.textAlign = 'center';
        this.ctx.fillText('Waiting for data...', width / 2, height / 2);
        this.ctx.textAlign = 'left';
    }
    
    // Public methods for external control
    setTimeWindow(seconds) {
        this.timeWindow = Math.max(10, Math.min(600, seconds)); // Limit between 10s and 10min
        console.log(`📊 Chart time window set to ${this.timeWindow} seconds`);
        
        // Update active button styling
        document.querySelectorAll('.time-controls button').forEach(btn => {
            btn.classList.remove('active');
            if (btn.textContent.includes(seconds + 's') || 
                (seconds === 60 && btn.textContent.includes('1m')) ||
                (seconds === 300 && btn.textContent.includes('5m'))) {
                btn.classList.add('active');
            }
        });
    }
    
    toggleSetpoint(show) {
        this.showSetpoint = show;
    }
    
    toggleError(show) {
        this.showError = show;
    }
    
    toggleOutput(show) {
        this.showOutput = show;
    }
    
    clear() {
        this.data = [];
        console.log('🗑️ Chart data cleared');
    }
    
    resize() {
        this.setupCanvas();
    }
    
    stop() {
        this.isRunning = false;
    }
    
    start() {
        this.isRunning = true;
        this.startAnimationLoop();
    }
}

// Enhanced global functions for chart controls
function adjustTimeScale(seconds) {
    if (window.temperatureChart) {
        window.temperatureChart.setTimeWindow(seconds);
    }
    
    if (window.dashboard) {
        window.dashboard.chartTimeScale = seconds;
    }
    
    console.log(`📊 Chart time scale changed to ${seconds} seconds`);
}

function clearChart() {
    if (window.temperatureChart) {
        window.temperatureChart.clear();
    }
    console.log('🗑️ Chart data cleared');
}

// Initialize chart when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for other components to load
    setTimeout(() => {
        window.temperatureChart = new TemperatureChart('temperature-chart');
        console.log('📊 Temperature Chart initialized!');
        
        // Test with some sample data if no real data is coming
        setTimeout(() => {
            if (window.temperatureChart && window.temperatureChart.data.length === 0) {
                console.log('🧪 No real data detected, starting with sample data');
                // This will be replaced by real data from dashboard
            }
        }, 2000);
    }, 500);
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TemperatureChart;
}