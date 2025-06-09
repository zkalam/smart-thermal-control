"""
Unit tests for heat transfer model
"""

import unittest
import pytest
from unittest.mock import patch
import warnings
from heat_transfer_data import (
    TemperatureUnit, CONSTANTS, MaterialProperties, GeometricProperties, 
    BloodProperties, MaterialLibrary
)
from heat_transfer import HeatTransfer


class TestPhysicalConstants(unittest.TestCase):
    """Test physical constants and temperature units"""
    
    def test_temperature_unit_enum(self):
        """Test temperature unit enumeration"""
        self.assertEqual(TemperatureUnit.CELSIUS.value, "°C")
        self.assertEqual(TemperatureUnit.KELVIN.value, "K")
        self.assertEqual(TemperatureUnit.FAHRENHEIT.value, "°F")
    
    def test_physical_constants_values(self):
        """Test that physical constants have expected values"""
        self.assertAlmostEqual(CONSTANTS.stefan_boltzmann, 5.670374419e-8, places=15)
        self.assertAlmostEqual(CONSTANTS.gravity, 9.80665, places=5)
        self.assertEqual(CONSTANTS.absolute_zero_c, -273.15)
        self.assertEqual(CONSTANTS.water_freezing_c, 0.0)
        self.assertEqual(CONSTANTS.room_temperature_c, 20.0)


class TestMaterialProperties(unittest.TestCase):
    """Test MaterialProperties dataclass"""
    
    def test_valid_material_properties(self):
        """Test creation of valid material properties"""
        mat = MaterialProperties(
            thermal_conductivity=10.0,
            density=1000.0,
            specific_heat=4000.0,
            emissivity=0.5
        )
        self.assertEqual(mat.thermal_conductivity, 10.0)
        self.assertEqual(mat.density, 1000.0)
        self.assertEqual(mat.specific_heat, 4000.0)
        self.assertEqual(mat.emissivity, 0.5)
    
    def test_negative_thermal_conductivity(self):
        """Test that negative thermal conductivity raises ValueError"""
        with self.assertRaises(ValueError) as context:
            MaterialProperties(
                thermal_conductivity=-1.0,
                density=1000.0,
                specific_heat=4000.0,
                emissivity=0.5
            )
        self.assertIn("Thermal conductivity must be non-negative", str(context.exception))
    
    def test_zero_thermal_conductivity(self):
        """Test that zero thermal conductivity is allowed"""
        mat = MaterialProperties(
            thermal_conductivity=0.0,
            density=1000.0,
            specific_heat=4000.0,
            emissivity=0.5
        )
        self.assertEqual(mat.thermal_conductivity, 0.0)
    
    def test_negative_density(self):
        """Test that negative density raises ValueError"""
        with self.assertRaises(ValueError) as context:
            MaterialProperties(
                thermal_conductivity=10.0,
                density=-1000.0,
                specific_heat=4000.0,
                emissivity=0.5
            )
        self.assertIn("Density must be positive", str(context.exception))
    
    def test_zero_density(self):
        """Test that zero density raises ValueError"""
        with self.assertRaises(ValueError):
            MaterialProperties(
                thermal_conductivity=10.0,
                density=0.0,
                specific_heat=4000.0,
                emissivity=0.5
            )
    
    def test_negative_specific_heat(self):
        """Test that negative specific heat raises ValueError"""
        with self.assertRaises(ValueError) as context:
            MaterialProperties(
                thermal_conductivity=10.0,
                density=1000.0,
                specific_heat=-4000.0,
                emissivity=0.5
            )
        self.assertIn("Specific heat must be positive", str(context.exception))
    
    def test_zero_specific_heat(self):
        """Test that zero specific heat raises ValueError"""
        with self.assertRaises(ValueError):
            MaterialProperties(
                thermal_conductivity=10.0,
                density=1000.0,
                specific_heat=0.0,
                emissivity=0.5
            )
    
    def test_emissivity_out_of_range(self):
        """Test that emissivity outside [0,1] raises ValueError"""
        # Test negative emissivity
        with self.assertRaises(ValueError) as context:
            MaterialProperties(
                thermal_conductivity=10.0,
                density=1000.0,
                specific_heat=4000.0,
                emissivity=-0.1
            )
        self.assertIn("Emissivity must be between 0 and 1", str(context.exception))
        
        # Test emissivity > 1
        with self.assertRaises(ValueError) as context:
            MaterialProperties(
                thermal_conductivity=10.0,
                density=1000.0,
                specific_heat=4000.0,
                emissivity=1.1
            )
        self.assertIn("Emissivity must be between 0 and 1", str(context.exception))
    
    def test_boundary_emissivity_values(self):
        """Test that emissivity of 0 and 1 are valid"""
        # Test emissivity = 0
        mat1 = MaterialProperties(
            thermal_conductivity=10.0,
            density=1000.0,
            specific_heat=4000.0,
            emissivity=0.0
        )
        self.assertEqual(mat1.emissivity, 0.0)
        
        # Test emissivity = 1
        mat2 = MaterialProperties(
            thermal_conductivity=10.0,
            density=1000.0,
            specific_heat=4000.0,
            emissivity=1.0
        )
        self.assertEqual(mat2.emissivity, 1.0)


class TestGeometricProperties(unittest.TestCase):
    """Test GeometricProperties dataclass"""
    
    def test_valid_geometric_properties(self):
        """Test creation of valid geometric properties"""
        geom = GeometricProperties(
            length=1.0,
            area=2.0,
            volume=3.0,
            thickness=0.1,
            air_velocity=0.5
        )
        self.assertEqual(geom.length, 1.0)
        self.assertEqual(geom.area, 2.0)
        self.assertEqual(geom.volume, 3.0)
        self.assertEqual(geom.thickness, 0.1)
        self.assertEqual(geom.air_velocity, 0.5)
    
    def test_optional_parameters(self):
        """Test that optional parameters default to None"""
        geom = GeometricProperties(
            length=1.0,
            area=2.0,
            volume=3.0
        )
        self.assertIsNone(geom.thickness)
        self.assertIsNone(geom.air_velocity)
    
    def test_negative_dimensions(self):
        """Test that negative dimensions raise ValueError"""
        # Negative length
        with self.assertRaises(ValueError) as context:
            GeometricProperties(length=-1.0, area=2.0, volume=3.0)
        self.assertIn("All geometric dimensions must be positive", str(context.exception))
        
        # Negative area
        with self.assertRaises(ValueError):
            GeometricProperties(length=1.0, area=-2.0, volume=3.0)
        
        # Negative volume
        with self.assertRaises(ValueError):
            GeometricProperties(length=1.0, area=2.0, volume=-3.0)
    
    def test_zero_dimensions(self):
        """Test that zero dimensions raise ValueError"""
        with self.assertRaises(ValueError):
            GeometricProperties(length=0.0, area=2.0, volume=3.0)
    
    def test_negative_thickness(self):
        """Test that negative thickness raises ValueError"""
        with self.assertRaises(ValueError) as context:
            GeometricProperties(
                length=1.0, area=2.0, volume=3.0, thickness=-0.1
            )
        self.assertIn("Thickness must be positive if specified", str(context.exception))
    
    def test_negative_air_velocity(self):
        """Test that negative air velocity raises ValueError"""
        with self.assertRaises(ValueError) as context:
            GeometricProperties(
                length=1.0, area=2.0, volume=3.0, air_velocity=-0.5
            )
        self.assertIn("Air velocity must be greater than or equal to zero", str(context.exception))
    
    def test_zero_air_velocity(self):
        """Test that zero air velocity is allowed"""
        geom = GeometricProperties(
            length=1.0, area=2.0, volume=3.0, air_velocity=0.0
        )
        self.assertEqual(geom.air_velocity, 0.0)


class TestBloodProperties(unittest.TestCase):
    """Test BloodProperties dataclass"""
    
    def test_valid_blood_properties(self):
        """Test creation of valid blood properties"""
        blood = BloodProperties(
            blood_type="Test Blood",
            target_temp_c=4.0,
            temp_tolerance_c=0.5,
            critical_temp_high_c=6.0,
            critical_temp_low_c=1.0,
            density=1060.0,
            specific_heat=3600.0,
            thermal_conductivity=0.5,
            thermal_mass_factor=1.2,
            phase_change_temp_c=-0.6,
            latent_heat=334000.0
        )
        self.assertEqual(blood.blood_type, "Test Blood")
        self.assertEqual(blood.target_temp_c, 4.0)
        self.assertEqual(blood.temp_tolerance_c, 0.5)
    
    def test_invalid_temperature_range(self):
        """Test that invalid critical temperature range raises ValueError"""
        with self.assertRaises(ValueError) as context:
            BloodProperties(
                blood_type="Test Blood",
                target_temp_c=4.0,
                temp_tolerance_c=0.5,
                critical_temp_high_c=1.0,  # Lower than critical_temp_low_c
                critical_temp_low_c=6.0,
                density=1060.0,
                specific_heat=3600.0,
                thermal_conductivity=0.5,
                thermal_mass_factor=1.2
            )
        self.assertIn("Critical low temperature must be less than critical high temperature", str(context.exception))
    
    def test_target_temp_outside_safe_range(self):
        """Test that target temperature outside safe range raises ValueError"""
        with self.assertRaises(ValueError) as context:
            BloodProperties(
                blood_type="Test Blood",
                target_temp_c=10.0,  # Above critical_temp_high_c
                temp_tolerance_c=0.5,
                critical_temp_high_c=6.0,
                critical_temp_low_c=1.0,
                density=1060.0,
                specific_heat=3600.0,
                thermal_conductivity=0.5,
                thermal_mass_factor=1.2
            )
        self.assertIn("Target temperature 10.0°C outside safe range", str(context.exception))
    
    def test_optional_phase_change_properties(self):
        """Test that phase change properties can be None"""
        blood = BloodProperties(
            blood_type="Test Blood",
            target_temp_c=22.0,
            temp_tolerance_c=2.0,
            critical_temp_high_c=24.0,
            critical_temp_low_c=20.0,
            density=1040.0,
            specific_heat=3500.0,
            thermal_conductivity=0.48,
            thermal_mass_factor=1.0
        )
        self.assertIsNone(blood.phase_change_temp_c)
        self.assertIsNone(blood.latent_heat)


class TestMaterialLibrary(unittest.TestCase):
    """Test predefined materials in MaterialLibrary"""
    
    def test_aluminum_properties(self):
        """Test aluminum material properties"""
        al = MaterialLibrary.ALUMINUM
        self.assertEqual(al.thermal_conductivity, 205.0)
        self.assertEqual(al.density, 2700.0)
        self.assertEqual(al.specific_heat, 900.0)
        self.assertEqual(al.emissivity, 0.1)
    
    def test_blood_products(self):
        """Test blood product properties"""
        whole_blood = MaterialLibrary.WHOLE_BLOOD
        self.assertEqual(whole_blood.blood_type, "Whole Blood")
        self.assertEqual(whole_blood.target_temp_c, 4.0)
        
        plasma = MaterialLibrary.PLASMA
        self.assertEqual(plasma.blood_type, "Fresh Frozen Plasma")
        self.assertEqual(plasma.target_temp_c, -18.0)
        
        platelets = MaterialLibrary.PLATELETS
        self.assertEqual(platelets.blood_type, "Platelets")
        self.assertEqual(platelets.target_temp_c, 22.0)
    
    def test_all_materials_valid(self):
        """Test that all predefined materials are valid"""
        # Test all material properties
        materials = [
            MaterialLibrary.ALUMINUM,
            MaterialLibrary.STAINLESS_STEEL_316,
            MaterialLibrary.ABS_PLASTIC,
            MaterialLibrary.POLYSTYRENE,
            MaterialLibrary.MEDICAL_GRADE_PVC,
            MaterialLibrary.PETG,
            MaterialLibrary.POLYURETHANE_FOAM,
            MaterialLibrary.VACUUM_INSULATION,
            MaterialLibrary.PARAFFIN_WAX,
            MaterialLibrary.SILICON
        ]
        
        for material in materials:
            self.assertIsInstance(material, MaterialProperties)
            self.assertGreater(material.density, 0)
            self.assertGreater(material.specific_heat, 0)
            self.assertGreaterEqual(material.thermal_conductivity, 0)
            self.assertGreaterEqual(material.emissivity, 0)
            self.assertLessEqual(material.emissivity, 1)


class TestHeatTransferTemperatureConversion(unittest.TestCase):
    """Test temperature conversion methods"""
    
    def test_celsius_to_kelvin(self):
        """Test Celsius to Kelvin conversion"""
        # Test standard conversions
        self.assertAlmostEqual(HeatTransfer.celsius_to_kelvin(0), 273.15, places=10)
        self.assertAlmostEqual(HeatTransfer.celsius_to_kelvin(100), 373.15, places=10)
        self.assertAlmostEqual(HeatTransfer.celsius_to_kelvin(-273.15), 0, places=10)
        self.assertAlmostEqual(HeatTransfer.celsius_to_kelvin(20), 293.15, places=10)
    
    def test_celsius_to_kelvin_below_absolute_zero(self):
        """Test that temperature below absolute zero raises ValueError"""
        with self.assertRaises(ValueError) as context:
            HeatTransfer.celsius_to_kelvin(-300)
        self.assertIn("below absolute zero", str(context.exception))
    
    def test_kelvin_to_celsius(self):
        """Test Kelvin to Celsius conversion"""
        # Test standard conversions
        self.assertAlmostEqual(HeatTransfer.kelvin_to_celsius(273.15), 0, places=10)
        self.assertAlmostEqual(HeatTransfer.kelvin_to_celsius(373.15), 100, places=10)
        self.assertAlmostEqual(HeatTransfer.kelvin_to_celsius(0), -273.15, places=10)
        self.assertAlmostEqual(HeatTransfer.kelvin_to_celsius(293.15), 20, places=10)
    
    def test_kelvin_to_celsius_negative_kelvin(self):
        """Test that negative Kelvin temperature raises ValueError"""
        with self.assertRaises(ValueError) as context:
            HeatTransfer.kelvin_to_celsius(-10)
        self.assertIn("below absolute zero", str(context.exception))


class TestHeatTransferConduction(unittest.TestCase):
    """Test conduction heat transfer calculations"""
    
    def setUp(self):
        """Set up test materials and geometry"""
        self.material = MaterialProperties(
            thermal_conductivity=10.0,
            density=1000.0,
            specific_heat=4000.0,
            emissivity=0.5
        )
        self.geometry = GeometricProperties(
            length=1.0,
            area=1.0,
            volume=1.0,
            thickness=0.1
        )
    
    def test_conduction_resistance(self):
        """Test conduction resistance calculation"""
        R = HeatTransfer.conduction_resistance(self.material, self.geometry)
        expected_R = 0.1 / (10.0 * 1.0)  # thickness / (k * area)
        self.assertAlmostEqual(R, expected_R, places=10)
    
    def test_conduction_resistance_no_thickness(self):
        """Test that missing thickness raises ValueError"""
        geom_no_thickness = GeometricProperties(
            length=1.0, area=1.0, volume=1.0
        )
        with self.assertRaises(ValueError) as context:
            HeatTransfer.conduction_resistance(self.material, geom_no_thickness)
        self.assertIn("Thickness required", str(context.exception))
    
    def test_conduction_resistance_zero_thickness(self):
        """Test that zero thickness raises ValueError"""
        geom_zero_thickness = GeometricProperties(
            length=1.0, area=1.0, volume=1.0, thickness=0.0
        )
        with self.assertRaises(ValueError) as context:
            HeatTransfer.conduction_resistance(self.material, geom_zero_thickness)
        self.assertIn("Thickness must be positive", str(context.exception))
    
    def test_conduction_heat_transfer(self):
        """Test conduction heat transfer calculation"""
        q = HeatTransfer.conduction_heat_transfer(
            self.material, self.geometry, temp_hot=100, temp_cold=50
        )
        expected_q = (10.0 * 1.0 * (100 - 50)) / 0.1  # k * A * ΔT / L
        self.assertAlmostEqual(q, expected_q, places=8)
    
    def test_conduction_heat_transfer_no_thickness(self):
        """Test conduction with missing thickness uses length"""
        geom_no_thickness = GeometricProperties(
            length=0.2, area=1.0, volume=1.0
        )
        q = HeatTransfer.conduction_heat_transfer(
            self.material, geom_no_thickness, temp_hot=100, temp_cold=50
        )
        expected_q = (10.0 * 1.0 * (100 - 50)) / 0.2  # Uses length as thickness
        self.assertAlmostEqual(q, expected_q, places=8)
    
    def test_conduction_negative_temperature_difference(self):
        """Test conduction with negative temperature difference"""
        q = HeatTransfer.conduction_heat_transfer(
            self.material, self.geometry, temp_hot=50, temp_cold=100
        )
        expected_q = (10.0 * 1.0 * (50 - 100)) / 0.1  # Negative heat flow
        self.assertAlmostEqual(q, expected_q, places=8)
        self.assertLess(q, 0)  # Should be negative


class TestHeatTransferConvection(unittest.TestCase):
    """Test convection heat transfer calculations"""
    
    def setUp(self):
        """Set up test geometry"""
        self.geometry = GeometricProperties(
            length=1.0,
            area=1.0,
            volume=1.0,
            air_velocity=0.0  # Natural convection
        )
    
    def test_convection_coefficient_natural_vertical(self):
        """Test natural convection coefficient for vertical surface"""
        h = HeatTransfer.get_convection_coefficient(
            length=1.0,
            temp_surface=50,
            temp_fluid=20,
            velocity=0.0,
            orientation='vertical'
        )
        self.assertGreater(h, 1.0)  # Should be greater than minimum
        self.assertIsInstance(h, float)
    
    def test_convection_coefficient_forced(self):
        """Test forced convection coefficient"""
        h = HeatTransfer.get_convection_coefficient(
            length=1.0,
            temp_surface=50,
            temp_fluid=20,
            velocity=2.0,
            orientation='vertical'
        )
        self.assertGreater(h, 1.0)
        self.assertIsInstance(h, float)
    
    def test_convection_coefficient_small_temperature_difference(self):
        """Test convection with very small temperature difference"""
        h = HeatTransfer.get_convection_coefficient(
            length=1.0,
            temp_surface=20.05,
            temp_fluid=20.0,
            velocity=0.0,
            orientation='vertical'
        )
        self.assertEqual(h, 1.0)  # Should return minimum value
    
    def test_convection_unknown_orientation(self):
        """Test convection with unknown orientation generates warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            h = HeatTransfer.get_convection_coefficient(
                length=1.0,
                temp_surface=50,
                temp_fluid=20,
                velocity=0.0,
                orientation='unknown'
            )
            self.assertEqual(len(w), 1)
            self.assertIn("Unknown orientation", str(w[0].message))
            self.assertGreater(h, 0)
    
    def test_convection_heat_transfer(self):
        """Test convection heat transfer calculation"""
        q = HeatTransfer.convection_heat_transfer(
            geometry=self.geometry,
            area=2.0,
            temp_surface=50,
            temp_fluid=20,
            orientation='vertical'
        )
        self.assertGreater(q, 0)  # Should be positive for hot surface
        self.assertIsInstance(q, float)
    
    def test_convection_heat_transfer_cold_surface(self):
        """Test convection with cold surface"""
        q = HeatTransfer.convection_heat_transfer(
            geometry=self.geometry,
            area=2.0,
            temp_surface=10,
            temp_fluid=20,
            orientation='vertical'
        )
        self.assertLess(q, 0)  # Should be negative for cold surface


class TestHeatTransferRadiation(unittest.TestCase):
    """Test radiation heat transfer calculations"""
    
    def setUp(self):
        """Set up test material"""
        self.material = MaterialProperties(
            thermal_conductivity=10.0,
            density=1000.0,
            specific_heat=4000.0,
            emissivity=0.8
        )
    
    def test_radiation_heat_transfer(self):
        """Test radiation heat transfer calculation"""
        q = HeatTransfer.radiation_heat_transfer(
            material=self.material,
            area=1.0,
            temp_hot_c=100,
            temp_cold_c=20
        )
        self.assertGreater(q, 0)  # Should be positive
        self.assertIsInstance(q, float)
    
    def test_radiation_same_temperature(self):
        """Test radiation with same temperatures"""
        q = HeatTransfer.radiation_heat_transfer(
            material=self.material,
            area=1.0,
            temp_hot_c=50,
            temp_cold_c=50
        )
        self.assertAlmostEqual(q, 0, places=10)
    
    def test_radiation_cold_to_hot(self):
        """Test radiation from cold to hot surface"""
        q = HeatTransfer.radiation_heat_transfer(
            material=self.material,
            area=1.0,
            temp_hot_c=20,
            temp_cold_c=100
        )
        self.assertLess(q, 0)  # Should be negative
    
    def test_radiation_zero_emissivity(self):
        """Test radiation with zero emissivity"""
        material_no_emit = MaterialProperties(
            thermal_conductivity=10.0,
            density=1000.0,
            specific_heat=4000.0,
            emissivity=0.0
        )
        q = HeatTransfer.radiation_heat_transfer(
            material=material_no_emit,
            area=1.0,
            temp_hot_c=100,
            temp_cold_c=20
        )
        self.assertAlmostEqual(q, 0, places=10)


class TestBloodThermalMass(unittest.TestCase):
    """Test blood thermal mass calculations"""
    
    def setUp(self):
        """Set up test blood and container properties"""
        self.blood = MaterialLibrary.WHOLE_BLOOD
        self.container = MaterialLibrary.ABS_PLASTIC
    
    def test_calculate_blood_thermal_mass(self):
        """Test blood thermal mass calculation"""
        thermal_mass = HeatTransfer.calculate_blood_thermal_mass(
            blood_product=self.blood,
            volume_liters=0.5,
            container_material=self.container,
            container_mass_kg=0.1
        )
        
        # Calculate expected values
        volume_m3 = 0.5 / 1000.0
        blood_mass_kg = self.blood.density * volume_m3
        expected_blood_thermal_mass = (
            blood_mass_kg * self.blood.specific_heat * self.blood.thermal_mass_factor
        )
        expected_container_thermal_mass = 0.1 * self.container.specific_heat
        expected_total = expected_blood_thermal_mass + expected_container_thermal_mass
        
        self.assertAlmostEqual(thermal_mass, expected_total, places=8)
    
    def test_calculate_thermal_mass_invalid_volume(self):
        """Test thermal mass with invalid volume"""
        with self.assertRaises(ValueError) as context:
            HeatTransfer.calculate_blood_thermal_mass(
                blood_product=self.blood,
                volume_liters=-0.5,
                container_material=self.container,
                container_mass_kg=0.1
            )
        self.assertIn("Volume must be positive", str(context.exception))
    
    def test_calculate_thermal_mass_negative_container_mass(self):
        """Test thermal mass with negative container mass"""
        with self.assertRaises(ValueError) as context:
            HeatTransfer.calculate_blood_thermal_mass(
                blood_product=self.blood,
                volume_liters=0.5,
                container_material=self.container,
                container_mass_kg=-0.1
            )
        self.assertIn("container mass non-negative", str(context.exception))
    
    def test_calculate_thermal_mass_zero_container_mass(self):
        """Test thermal mass with zero container mass"""
        thermal_mass = HeatTransfer.calculate_blood_thermal_mass(
            blood_product=self.blood,
            volume_liters=0.5,
            container_material=self.container,
            container_mass_kg=0.0
        )
        
        # Should only include blood thermal mass
        volume_m3 = 0.5 / 1000.0
        blood_mass_kg = self.blood.density * volume_m3
        expected = blood_mass_kg * self.blood.specific_heat * self.blood.thermal_mass_factor
        
        self.assertAlmostEqual(thermal_mass, expected, places=8)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for realistic scenarios"""
    
    def test_blood_bag_cooling_scenario(self):
        """Test realistic blood bag cooling scenario"""
        # Blood bag properties
        blood = MaterialLibrary.WHOLE_BLOOD
        container = MaterialLibrary.MEDICAL_GRADE_PVC
        insulation = MaterialLibrary.POLYURETHANE_FOAM
        
        # Geometry
        bag_geometry = GeometricProperties(
            length=0.2,  # 20cm characteristic length
            area=0.04,   # 0.04 m² surface area
            volume=0.0005,  # 0.5L volume
            thickness=0.002,  # 2mm wall thickness
            air_velocity=0.1  # Slight air movement
        )
        
        # Calculate thermal mass
        thermal_mass = HeatTransfer.calculate_blood_thermal_mass(
            blood_product=blood,
            volume_liters=0.5,
            container_material=container,
            container_mass_kg=0.05
        )
        
        # Calculate heat transfer rates
        q_conduction = HeatTransfer.conduction_heat_transfer(
            material=container,
            geometry=bag_geometry,
            temp_hot=25,  # Room temperature
            temp_cold=4   # Target blood temperature
        )
        
        q_convection = HeatTransfer.convection_heat_transfer(
            geometry=bag_geometry,
            area=bag_geometry.area,
            temp_surface=4,
            temp_fluid=25,
            orientation='vertical'
        )
        
        q_radiation = HeatTransfer.radiation_heat_transfer(
            material=container,
            area=bag_geometry.area,
            temp_hot_c=25,
            temp_cold_c=4
        )
        
        # All calculations should complete without error
        self.assertIsInstance(thermal_mass, float)
        self.assertIsInstance(q_conduction, float)
        self.assertIsInstance(q_convection, float)
        self.assertIsInstance(q_radiation, float)
        
        # Heat should flow into the cold blood bag
        self.assertGreater(q_conduction, 0)
        self.assertLess(q_convection, 0)  # Negative because surface is colder
        self.assertGreater(q_radiation, 0)  # Positive because environment radiates heat TO the cold bag

    def test_warm_blood_bag_into_cooler_scenario(self):
        """Test realistic scenario: warm blood bag placed into cooler"""
        # Blood bag at room temperature being cooled down
        blood = MaterialLibrary.WHOLE_BLOOD
        container = MaterialLibrary.MEDICAL_GRADE_PVC
        
        # Geometry - same blood bag
        bag_geometry = GeometricProperties(
            length=0.2,  # 20cm characteristic length
            area=0.04,   # 0.04 m² surface area
            volume=0.0005,  # 0.5L volume
            thickness=0.002,  # 2mm wall thickness
            air_velocity=0.5  # Cooler fan circulation
        )
        
        # Initial conditions: bag at room temp, cooler environment at 4°C
        bag_temp = 20.0  # Room temperature blood bag
        cooler_temp = 4.0  # Cooler environment
        
        # Calculate thermal mass - important for cooling time estimation
        thermal_mass = HeatTransfer.calculate_blood_thermal_mass(
            blood_product=blood,
            volume_liters=0.5,
            container_material=container,
            container_mass_kg=0.05
        )
        
        # Calculate heat transfer rates (heat leaving the warm bag)
        q_conduction = HeatTransfer.conduction_heat_transfer(
            material=container,
            geometry=bag_geometry,
            temp_hot=bag_temp,  # Warm bag
            temp_cold=cooler_temp  # Cold cooler
        )
        
        q_convection = HeatTransfer.convection_heat_transfer(
            geometry=bag_geometry,
            area=bag_geometry.area,
            temp_surface=bag_temp,  # Warm bag surface
            temp_fluid=cooler_temp,  # Cold air in cooler
            orientation='vertical'
        )
        
        q_radiation = HeatTransfer.radiation_heat_transfer(
            material=container,
            area=bag_geometry.area,
            temp_hot_c=bag_temp,  # Warm bag
            temp_cold_c=cooler_temp  # Cold cooler walls
        )
        
        # All calculations should complete without error
        self.assertIsInstance(thermal_mass, float)
        self.assertIsInstance(q_conduction, float)
        self.assertIsInstance(q_convection, float)
        self.assertIsInstance(q_radiation, float)
        
        # Verify thermal mass is reasonable for a blood bag
        self.assertGreater(thermal_mass, 1000)  # Should be > 1000 J/K
        self.assertLess(thermal_mass, 10000)    # Should be < 10000 J/K
        
        # Heat should flow OUT of the warm blood bag (cooling it down)
        self.assertGreater(q_conduction, 0)  # Positive: heat flows from warm bag to cold cooler
        self.assertGreater(q_convection, 0)  # Positive: heat flows from warm surface to cold air
        self.assertGreater(q_radiation, 0)   # Positive: heat radiates from warm bag to cold walls
        
        # Total heat loss rate (all positive values indicate heat leaving the bag)
        total_heat_loss = q_conduction + q_convection + q_radiation
        self.assertGreater(total_heat_loss, 0)
        
        # Convection should be significant due to forced air circulation
        self.assertGreater(q_convection, q_conduction * 0.5)  # Convection at least 50% of conduction
        
        # Estimate cooling time constant (rough approximation)
        # τ = thermal_mass / (total_heat_transfer_coefficient * area)
        # For this test, just verify we can calculate it
        if total_heat_loss > 0:
            temperature_difference = bag_temp - cooler_temp
            overall_heat_transfer_coeff = total_heat_loss / (bag_geometry.area * temperature_difference)
            time_constant = thermal_mass / (overall_heat_transfer_coeff * bag_geometry.area)
            
            # Time constant should be reasonable (between 1 minute and 2 hours)
            self.assertGreater(time_constant, 60)    # > 1 minute
            self.assertLess(time_constant, 7200)     # < 2 hours
            
        # Verify the bag is initially too warm for safe storage
        self.assertGreater(bag_temp, blood.critical_temp_high_c)
        
        # Verify target temperature is within safe range
        self.assertLessEqual(cooler_temp, blood.critical_temp_high_c)
        self.assertGreaterEqual(cooler_temp, blood.critical_temp_low_c)



if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)