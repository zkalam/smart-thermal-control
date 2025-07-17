#!/usr/bin/env python3
"""
Smart Thermal Control System - Dashboard Launcher
Quick script to start the educational dashboard with Python integration
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

def find_project_root():
    """Find the project root directory"""
    current = Path(__file__).parent
    
    # Look for key project files
    while current != current.parent:
        if (current / "src").exists() and (current / "src" / "control").exists():
            return current
        current = current.parent
    
    # Fallback to current directory
    return Path.cwd()

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = ['flask', 'flask-cors', 'flask-socketio']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        print("Install with: pip install flask flask-cors flask-socketio")
        return False
    return True

def start_python_server():
    """Start the Python Flask server"""
    try:
        # Add project root to Python path
        project_root = find_project_root()
        sys.path.insert(0, str(project_root))
        
        print("Starting Python thermal control server...")
        print(f"Project root: {project_root}")
        
        # Import and start the dashboard server
        from src.dashboard.dashboard_server import DashboardServer
        
        server = DashboardServer()
        print("Server initialized successfully!")
        print("Dashboard available at: http://127.0.0.1:5000")
        print("Press Ctrl+C to stop the server")
        
        # Start server
        server.run(host='127.0.0.1', port=5000, debug=False)
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running from the correct directory")
        print("Project structure should have: src/control/, src/thermal_model/, etc.")
        return False
    except Exception as e:
        print(f"Server startup error: {e}")
        return False
    
    return True

def open_browser():
    """Open browser to dashboard after short delay"""
    time.sleep(3)  # Wait for server to start
    try:
        webbrowser.open('http://127.0.0.1:5000')
        print("Browser opened to dashboard")
    except Exception as e:
        print(f"Could not open browser: {e}")

def main():
    """Main startup sequence"""
    print("=" * 60)
    print("Smart Thermal Control System - Educational Dashboard")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Start browser opening in background
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start the Python server (blocking)
    success = start_python_server()
    
    return 0 if success else 1

if __name__ == '__main__':
    exit_code = main()