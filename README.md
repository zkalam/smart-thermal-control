# Smart Thermal Control

A Python-based temperature control system specifically for blood storage applications, ensuring optimal storage conditions for life-saving blood products through intelligent monitoring and control algorithms.

## Project Overview

This system provides automated, precise temperature control for critical blood storage scenarios including:

- Blood Banks & Hospitals: Whole blood and red blood cell storage (1-6°C)
- Plasma Centers: Fresh frozen plasma storage (-18°C or below)
- Mobile Blood Units: Temperature-controlled transport containers
- Emergency Medical Services: Portable blood storage for field operations
- Research Facilities: Temperature-sensitive blood component storage

Think of it as a medical-grade smart thermostat with the precision and reliability required for life-critical blood storage applications.

## Project Structure

smart-thermal-control/
├── src/
│   ├── thermal_model/          # Heat transfer physics and calculations
│   │   ├── __init__.py
│   │   ├──[physics model files]
│   ├── control/                # Temperature control algorithms
│   │   ├── __init__.py
│   │   └── [control files]
│   ├── simulation/             # Dynamic system simulation
│   │   ├── __init__.py
│   │   └── [simulation files]
│   └── dashboard/              # User interface and monitoring
│       ├── __init__.py
│       └── [dashboard files]
├── __init__.py            
├── requirements.txt            # Python dependencies
├── pytest.ini                  # configuration file for pytest
├── .gitignore                 # Git ignore rules
└── README.md                  # This file

## Module Descriptions

### `src/thermal_model/`
Contains the core heat transfer physics calculations:
- **heat_transfer.py**: Heat transfer mechanisms (conduction, convection, radiation)
- **heat_transfer_data.py**: Material properties and blood product specifications
- **test_heat_transfer.py**: Unit testing

### `src/controller/`
Temperature control algorithms and safety systems:
- Control logic (PID)
- Safety monitoring and limits
- Control system interfaces

### `src/simulation/`
Dynamic system simulation and modeling:
- Time-based temperature evolution
- System state management
- Integration with physics model

### `src/dashboard/`
User interface and system monitoring:
- Real-time temperature displays
- Control parameter adjustment
- Data logging and visualization