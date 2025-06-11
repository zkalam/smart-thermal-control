"""
Unit tests for heat transfer model
"""

from heat_transfer import *
from heat_transfer_data import *
import unittest
from unittest.mock import patch
import warnings


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
        )
        self.assertEqual(geom.length, 1.0)
        self.assertEqual(geom.area, 2.0)
        self.assertEqual(geom.volume, 3.0)
        self.assertEqual(geom.thickness, 0.1)
    
    def test_optional_parameters(self):
        """Test that optional parameters default to None"""
        geom = GeometricProperties(
            length=1.0,
            area=2.0,
            volume=3.0
        )
        self.assertIsNone(geom.thickness)
    
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
        self.assertAlmostEqual(celsius_to_kelvin(0), 273.15, places=10)
        self.assertAlmostEqual(celsius_to_kelvin(100), 373.15, places=10)
        self.assertAlmostEqual(celsius_to_kelvin(-273.15), 0, places=10)
        self.assertAlmostEqual(celsius_to_kelvin(20), 293.15, places=10)
    
    def test_celsius_to_kelvin_below_absolute_zero(self):
        """Test that temperature below absolute zero raises ValueError"""
        with self.assertRaises(ValueError) as context:
            celsius_to_kelvin(-300)
        self.assertIn("below absolute zero", str(context.exception))
    
    def test_kelvin_to_celsius(self):
        """Test Kelvin to Celsius conversion"""
        # Test standard conversions
        self.assertAlmostEqual(kelvin_to_celsius(273.15), 0, places=10)
        self.assertAlmostEqual(kelvin_to_celsius(373.15), 100, places=10)
        self.assertAlmostEqual(kelvin_to_celsius(0), -273.15, places=10)
        self.assertAlmostEqual(kelvin_to_celsius(293.15), 20, places=10)
    
    def test_kelvin_to_celsius_negative_kelvin(self):
        """Test that negative Kelvin temperature raises ValueError"""
        with self.assertRaises(ValueError) as context:
            kelvin_to_celsius(-10)
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
        R = conduction_resistance(self.material, self.geometry)
        expected_R = 0.1 / (10.0 * 1.0)  # thickness / (k * area)
        self.assertAlmostEqual(R, expected_R, places=10)
    
    def test_conduction_resistance_no_thickness(self):
        """Test that missing thickness raises ValueError"""
        geom_no_thickness = GeometricProperties(
            length=1.0, area=1.0, volume=1.0
        )
        with self.assertRaises(ValueError) as context:
            conduction_resistance(self.material, geom_no_thickness)
        self.assertIn("Thickness required", str(context.exception))
    
    def test_conduction_resistance_zero_thickness(self):
        """Test that zero thickness raises ValueError"""
        with self.assertRaises(ValueError) as context:
            geom_zero_thickness = GeometricProperties(
            length=1.0, area=1.0, volume=1.0, thickness=0.0
            )
            conduction_resistance(self.material, geom_zero_thickness)
        self.assertIn("Thickness must be positive if specified", str(context.exception))
    
    def test_conduction_heat_transfer(self):
        """Test conduction heat transfer calculation"""
        q = conduction_heat_transfer(
            self.material, self.geometry, temp_hot=100, temp_cold=50
        )
        expected_q = (10.0 * 1.0 * (100 - 50)) / 0.1  # k * A * ΔT / L
        self.assertAlmostEqual(q, expected_q, places=8)
    
    def test_conduction_heat_transfer_no_thickness(self):
        """Test conduction with missing thickness uses length"""
        geom_no_thickness = GeometricProperties(
            length=0.2, area=1.0, volume=1.0
        )
        q = conduction_heat_transfer(
            self.material, geom_no_thickness, temp_hot=100, temp_cold=50
        )
        expected_q = (10.0 * 1.0 * (100 - 50)) / 0.2  # Uses length as thickness
        self.assertAlmostEqual(q, expected_q, places=8)
    
    def test_conduction_negative_temperature_difference(self):
        """Test conduction with negative temperature difference"""
        q = conduction_heat_transfer(
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
            volume=1.0,n
        )
    
    def test_convection_coefficient_natural_vertical(self):
        """Test natural convection coefficient for vertical surface"""
        h = get_convection_coefficient(
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
        h = get_convection_coefficient(
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
        h = get_convection_coefficient(
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
            h = get_convection_coefficient(
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
        q = convection_heat_transfer(
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
        q = convection_heat_transfer(
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
        q = radiation_heat_transfer(
            material=self.material,
            area=1.0,
            temp_hot_c=100,
            temp_cold_c=20
        )
        self.assertGreater(q, 0)  # Should be positive
        self.assertIsInstance(q, float)
    
    def test_radiation_same_temperature(self):
        """Test radiation with same temperatures"""
        q = radiation_heat_transfer(
            material=self.material,
            area=1.0,
            temp_hot_c=50,
            temp_cold_c=50
        )
        self.assertAlmostEqual(q, 0, places=10)
    
    def test_radiation_cold_to_hot(self):
        """Test radiation from cold to hot surface"""
        q = radiation_heat_transfer(
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
        q = radiation_heat_transfer(
            material=material_no_emit,
            area=1.0,
            temp_hot_c=100,
            temp_cold_c=20
        )
        self.assertAlmostEqual(q, 0, places=10)

class TestThermalCapacitance(unittest.TestCase):
    """Test thermal capacitance calculations"""
    def setUp(self):
        """Set up test material"""
        self.material = MaterialProperties(
            thermal_conductivity=10.0,
            density=1000.0,
            specific_heat=4000.0,
            emissivity=0.8
        )

    def test_capacitance_typical_mass(self):
        """Test capacitance with typical mass"""
        mass = 2.0  # kg
        expected = mass * self.material.specific_heat
        result = calculate_thermal_capacitance(self.material, mass)
        self.assertAlmostEqual(result, expected)

    def test_capacitance_zero_mass(self):
        """Capacitance should be 0 when mass is 0"""
        result = calculate_thermal_capacitance(self.material, 0)
        self.assertEqual(result, 0.0)

    def test_capacitance_negative_mass(self):
        """Capacitance with negative mass should return negative result"""
        mass = -1.0
        expected = mass * self.material.specific_heat
        result = calculate_thermal_capacitance(self.material, mass)
        self.assertEqual(result, expected)
    
class TestThermalDiffusivity(unittest.TestCase):
    """Test thermal diffusivity calculations"""
    
    def setUp(self):
        """Set up test material"""
        self.material = MaterialProperties(
            thermal_conductivity=10.0,
            density=1000.0,
            specific_heat=4000.0,
            emissivity=0.8
        )
    
    def test_thermal_diffusivity_calculation(self):
        """Test thermal diffusivity calculation: α = k/(ρcp)"""
        alpha = thermal_diffusivity(self.material)
        expected = 10.0 / (1000.0 * 4000.0)  # k / (ρ * cp)
        self.assertAlmostEqual(alpha, expected, places=12)
    
    def test_thermal_diffusivity_units(self):
        """Test that thermal diffusivity has correct units (m²/s)"""
        alpha = thermal_diffusivity(self.material)
        self.assertIsInstance(alpha, float)
        self.assertGreater(alpha, 0)  # Should be positive for valid materials
    
    def test_thermal_diffusivity_realistic_values(self):
        """Test thermal diffusivity for realistic materials"""
        # Test aluminum (high diffusivity)
        alpha_al = thermal_diffusivity(MaterialLibrary.ALUMINUM)
        self.assertGreater(alpha_al, 1e-5)  # Metals have high thermal diffusivity
        
        # Test plastic (low diffusivity)
        alpha_plastic = thermal_diffusivity(MaterialLibrary.ABS_PLASTIC)
        self.assertLess(alpha_plastic, 1e-6)  # Plastics have low thermal diffusivity
        
        # Aluminum should have much higher diffusivity than plastic
        self.assertGreater(alpha_al, alpha_plastic * 100)


class TestBloodTemperatureValidation(unittest.TestCase):
    """Test blood temperature validation function"""
    
    def setUp(self):
        """Set up test blood product"""
        self.blood = MaterialLibrary.WHOLE_BLOOD
    
    def test_temperature_within_tolerance(self):
        """Test temperature within tolerance range"""
        result = validate_blood_temperature(self.blood, 4.0)  # Target temperature
        
        self.assertTrue(result['is_safe'])
        self.assertTrue(result['is_within_tolerance'])
        self.assertEqual(result['deviation_from_target'], 0.0)
        self.assertEqual(result['status'], 'safe')
    
    def test_temperature_safe_but_outside_tolerance(self):
        """Test temperature safe but outside tolerance"""
        result = validate_blood_temperature(self.blood, 5.5)  # Safe but not ideal
        
        self.assertTrue(result['is_safe'])
        self.assertFalse(result['is_within_tolerance'])
        self.assertEqual(result['deviation_from_target'], 1.5)
        self.assertEqual(result['status'], 'safe')
    
    def test_temperature_too_high(self):
        """Test temperature above critical high"""
        result = validate_blood_temperature(self.blood, 7.0)  # Above 6°C critical
        
        self.assertFalse(result['is_safe'])
        self.assertFalse(result['is_within_tolerance'])
        self.assertEqual(result['deviation_from_target'], 3.0)
        self.assertEqual(result['status'], 'critical')
    
    def test_temperature_too_low(self):
        """Test temperature below critical low"""
        result = validate_blood_temperature(self.blood, 0.5)  # Below 1°C critical
        
        self.assertFalse(result['is_safe'])
        self.assertFalse(result['is_within_tolerance'])
        self.assertEqual(result['deviation_from_target'], -3.5)
        self.assertEqual(result['status'], 'critical')
    
    def test_temperature_at_critical_boundaries(self):
        """Test temperatures at critical boundaries"""
        # At critical high (should be safe)
        result_high = validate_blood_temperature(self.blood, 6.0)
        self.assertTrue(result_high['is_safe'])
        
        # At critical low (should be safe)
        result_low = validate_blood_temperature(self.blood, 1.0)
        self.assertTrue(result_low['is_safe'])
    
    def test_plasma_temperature_validation(self):
        """Test temperature validation for frozen plasma"""
        plasma = MaterialLibrary.PLASMA
        
        # At target temperature (-18°C)
        result_target = validate_blood_temperature(plasma, -18.0)
        self.assertTrue(result_target['is_safe'])
        self.assertTrue(result_target['is_within_tolerance'])
        
        # Above critical temperature
        result_warm = validate_blood_temperature(plasma, -15.0)
        self.assertFalse(result_warm['is_safe'])
        self.assertEqual(result_warm['status'], 'critical')


class TestBloodThermalMass(unittest.TestCase):
    """Test blood thermal mass calculations"""
    
    def setUp(self):
        """Set up test blood and container properties"""
        self.blood = MaterialLibrary.WHOLE_BLOOD
        self.container = MaterialLibrary.ABS_PLASTIC
    
    def test_calculate_blood_thermal_mass_dict_return(self):
        """Test blood thermal mass calculation returns detailed dictionary"""
        result = calculate_blood_thermal_mass(
            blood_product=self.blood,
            volume_liters=0.5,
            container_material=self.container,
            container_mass_kg=0.1
        )
        
        # Should return dictionary with detailed breakdown
        self.assertIsInstance(result, dict)
        self.assertIn('total_thermal_mass', result)
        self.assertIn('blood_thermal_mass', result)
        self.assertIn('container_thermal_mass', result)
        self.assertIn('blood_mass_kg', result)
        
        # Verify blood mass calculation
        volume_m3 = 0.5 / 1000.0
        expected_blood_mass = self.blood.density * volume_m3
        self.assertAlmostEqual(result['blood_mass_kg'], expected_blood_mass, places=8)
        
        # Verify thermal mass components
        expected_blood_thermal_mass = (
            result['blood_mass_kg'] * self.blood.specific_heat * self.blood.thermal_mass_factor
        )
        expected_container_thermal_mass = 0.1 * self.container.specific_heat
        
        self.assertAlmostEqual(result['blood_thermal_mass'], expected_blood_thermal_mass, places=6)
        self.assertAlmostEqual(result['container_thermal_mass'], expected_container_thermal_mass, places=6)
        
        # Total should equal sum of components
        expected_total = result['blood_thermal_mass'] + result['container_thermal_mass']
        self.assertAlmostEqual(result['total_thermal_mass'], expected_total, places=8)
    
    def test_blood_thermal_mass_different_products(self):
        """Test thermal mass calculation for different blood products"""
        volume = 0.5  # liters
        container_mass = 0.1  # kg
        
        # Test whole blood
        whole_blood_result = calculate_blood_thermal_mass(
            self.blood, volume, self.container, container_mass
        )
        
        # Test plasma
        plasma_result = calculate_blood_thermal_mass(
            MaterialLibrary.PLASMA, volume, self.container, container_mass
        )
        
        # Test platelets
        platelet_result = calculate_blood_thermal_mass(
            MaterialLibrary.PLATELETS, volume, self.container, container_mass
        )
        
        # All should return valid dictionaries
        for result in [whole_blood_result, plasma_result, platelet_result]:
            self.assertIsInstance(result, dict)
            self.assertGreater(result['total_thermal_mass'], 0)
            self.assertGreater(result['blood_thermal_mass'], 0)
            self.assertGreater(result['container_thermal_mass'], 0)
        
        # Different blood products should have different thermal masses
        # due to different densities and thermal mass factors
        self.assertNotEqual(
            whole_blood_result['blood_thermal_mass'],
            plasma_result['blood_thermal_mass']
        )
    
    def test_calculate_thermal_mass_invalid_inputs(self):
        """Test thermal mass with invalid inputs"""
        # Test negative volume
        with self.assertRaises(ValueError) as context:
            calculate_blood_thermal_mass(
                self.blood, -0.5, self.container, 0.1
            )
        self.assertIn("Volume must be positive", str(context.exception))
        
        # Test zero volume
        with self.assertRaises(ValueError):
            calculate_blood_thermal_mass(
                self.blood, 0.0, self.container, 0.1
            )
        
        # Test negative container mass
        with self.assertRaises(ValueError) as context:
            calculate_blood_thermal_mass(
                self.blood, 0.5, self.container, -0.1
            )
        self.assertIn("container mass non-negative", str(context.exception))
    
    def test_calculate_thermal_mass_zero_container_mass(self):
        """Test thermal mass with zero container mass"""
        result = calculate_blood_thermal_mass(
            self.blood, 0.5, self.container, 0.0
        )
        
        # Container thermal mass should be zero
        self.assertEqual(result['container_thermal_mass'], 0.0)
        
        # Total should equal only blood thermal mass
        self.assertEqual(result['total_thermal_mass'], result['blood_thermal_mass'])
        
        # Blood thermal mass should still be calculated correctly
        volume_m3 = 0.5 / 1000.0
        expected_blood_mass = self.blood.density * volume_m3
        expected_blood_thermal_mass = (
            expected_blood_mass * self.blood.specific_heat * self.blood.thermal_mass_factor
        )
        self.assertAlmostEqual(result['blood_thermal_mass'], expected_blood_thermal_mass, places=6)
    
    def test_thermal_mass_scaling_with_volume(self):
        """Test that thermal mass scales proportionally with volume"""
        container_mass = 0.1
        
        # Test different volumes
        volume_1L = calculate_blood_thermal_mass(self.blood, 1.0, self.container, container_mass)
        volume_2L = calculate_blood_thermal_mass(self.blood, 2.0, self.container, container_mass)
        
        # Blood thermal mass should scale with volume
        ratio = volume_2L['blood_thermal_mass'] / volume_1L['blood_thermal_mass']
        self.assertAlmostEqual(ratio, 2.0, places=8)
        
        # Blood mass should also scale
        mass_ratio = volume_2L['blood_mass_kg'] / volume_1L['blood_mass_kg']
        self.assertAlmostEqual(mass_ratio, 2.0, places=8)
        
        # Container thermal mass should remain the same
        self.assertEqual(volume_1L['container_thermal_mass'], volume_2L['container_thermal_mass'])


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for realistic blood storage scenarios"""
        
    def test_blood_bag_cooling_detailed_analysis(self):
        """Test comprehensive blood bag cooling with all heat transfer mechanisms"""
        # System setup - blood bag in cooling environment
        blood = MaterialLibrary.WHOLE_BLOOD
        container = MaterialLibrary.MEDICAL_GRADE_PVC
        
        # Realistic blood bag geometry
        bag_geometry = GeometricProperties(
            length=0.15,     # 15cm characteristic length
            area=0.035,      # 350 cm² surface area
            volume=0.0005,   # 500 mL volume
            thickness=0.003, # 3mm effective thermal path
        )
        
        # Temperature scenario: room temperature bag entering refrigerator
        initial_bag_temp = 22.0  # Room temperature
        refrigerator_temp = 4.0  # Target storage temperature
        air_velocity= 0.2 # Gentle air circulation
        
        # Calculate thermal properties
        thermal_data = calculate_blood_thermal_mass(
            blood_product=blood,
            volume_liters=0.5,
            container_material=container,
            container_mass_kg=0.08  # Typical blood bag weight
        )
        
        # Calculate all heat transfer mechanisms
        q_conduction = conduction_heat_transfer(
            material=container,
            geometry=bag_geometry,
            temp_hot=initial_bag_temp,
            temp_cold=refrigerator_temp
        )
        
        q_convection = convection_heat_transfer(
            geometry=bag_geometry,
            area=bag_geometry.area,
            temp_surface=initial_bag_temp,
            temp_fluid=refrigerator_temp,
            velocity = air_velocity,
            orientation='vertical'
        )
        
        q_radiation = radiation_heat_transfer(
            material=container,
            area=bag_geometry.area,
            temp_hot_c=initial_bag_temp,
            temp_cold_c=refrigerator_temp
        )
        
        # Validate thermal mass calculation
        if isinstance(thermal_data, dict):
            thermal_mass = thermal_data['total_thermal_mass']
        else:
            thermal_mass = thermal_data
            
        self.assertGreater(thermal_mass, 1500)  # Reasonable for 500mL blood
        self.assertLess(thermal_mass, 3000)     # But not excessive
        
        # Validate heat transfer calculations
        self.assertGreater(q_conduction, 0)  # Heat flows from warm bag to cold environment
        self.assertGreater(q_convection, 0)  # Heat convects from warm surface to cold air
        self.assertGreater(q_radiation, 0)   # Heat radiates from warm bag to cold walls
        
        # Calculate total heat loss rate and cooling characteristics
        total_heat_loss = q_conduction + q_convection + q_radiation
        self.assertGreater(total_heat_loss, 0.5)  # Should have reasonable heat loss rate (>0.5W)
        self.assertLess(total_heat_loss, 50.0)    # Adjusted upper limit for realistic scenarios
        
        # Estimate thermal time constant
        temperature_difference = initial_bag_temp - refrigerator_temp
        effective_thermal_resistance = temperature_difference / total_heat_loss
        time_constant = thermal_mass * effective_thermal_resistance
        
        # Time constant should be realistic for blood bag cooling
        self.assertGreater(time_constant, 300)   # >5 minutes (slow cooling preserves blood)
        self.assertLess(time_constant, 7200)     # <2 hours (practical cooling time)
        
        # Validate temperature safety
        initial_validation = validate_blood_temperature(blood, initial_bag_temp)
        final_validation = validate_blood_temperature(blood, refrigerator_temp)
        
        self.assertFalse(initial_validation['is_safe'])  # Initial temp too high
        self.assertTrue(final_validation['is_safe'])     # Final temp is safe
        self.assertTrue(final_validation['is_within_tolerance'])  # And within tolerance

    def test_platelet_room_temperature_storage(self):
        """Test platelet storage at room temperature with agitation"""
        platelets = MaterialLibrary.PLATELETS
        container = MaterialLibrary.ABS_PLASTIC
        
        # Platelet container with agitation
        platelet_geometry = GeometricProperties(
            length=0.10,     # 10cm characteristic length
            area=0.020,      # 200 cm² surface area
            volume=0.0002,   # 200 mL platelet unit
            thickness=0.002, # 2mm thin walls for gas exchange
        )
        
        # Temperature scenario: maintaining room temperature storage
        storage_temp = 22.0    # Target platelet storage temperature
        room_temp = 25.0       # Slightly warm room
        air_velocity= 0.5 # Air movement from agitation
        
        # Calculate thermal properties
        thermal_data = calculate_blood_thermal_mass(
            blood_product=platelets,
            volume_liters=0.2,
            container_material=container,
            container_mass_kg=0.04
        )
        
        # Calculate heat transfer (slight warming scenario)
        q_conduction = conduction_heat_transfer(
            material=container,
            geometry=platelet_geometry,
            temp_hot=room_temp,
            temp_cold=storage_temp
        )
        
        q_convection = convection_heat_transfer(
            geometry=platelet_geometry,
            area=platelet_geometry.area,
            temp_surface=storage_temp,
            temp_fluid=room_temp,
            velocity=air_velocity,
            orientation='horizontal_hot_up'  # Platelet bags often stored horizontally
        )
        
        # Validate platelet-specific requirements
        self.assertIsInstance(thermal_data, dict)
        
        # Platelets have different thermal properties than other blood products
        whole_blood_thermal = calculate_blood_thermal_mass(MaterialLibrary.WHOLE_BLOOD, 0.2, container, 0.04)
        if isinstance(thermal_data, dict) and isinstance(whole_blood_thermal, dict):
            self.assertNotEqual(thermal_data['blood_thermal_mass'], whole_blood_thermal['blood_thermal_mass'])
        
        # Heat transfer should be relatively small (small temperature difference)
        total_heat_gain = q_conduction + abs(q_convection)  # abs because convection might be negative
        self.assertLess(total_heat_gain, 10.0)  # Adjusted upper limit for small temperature differences
        
        # Validate temperature safety for platelets
        storage_validation = validate_blood_temperature(platelets, storage_temp)
        self.assertTrue(storage_validation['is_safe'])
        self.assertTrue(storage_validation['is_within_tolerance'])
        
        # Test temperature boundaries
        too_cold_validation = validate_blood_temperature(platelets, 19.0)
        too_hot_validation = validate_blood_temperature(platelets, 25.0)
        
        self.assertFalse(too_cold_validation['is_safe'])
        self.assertFalse(too_hot_validation['is_safe'])

    def test_thermal_diffusivity_integration_scenarios(self):
        """Test thermal diffusivity in realistic heat transfer scenarios"""
        materials = [
            ('Whole Blood', MaterialLibrary.WHOLE_BLOOD),
            ('Plasma', MaterialLibrary.PLASMA),
            ('Medical PVC', MaterialLibrary.MEDICAL_GRADE_PVC),
            ('Aluminum', MaterialLibrary.ALUMINUM),
            ('Insulation', MaterialLibrary.POLYURETHANE_FOAM)
        ]
        
        diffusivities = {}
        
        # Calculate thermal diffusivity for all materials
        for name, material in materials:
            alpha = thermal_diffusivity(material)
            diffusivities[name] = alpha
            
            # Validate reasonable ranges
            self.assertGreater(alpha, 1e-9)   # Greater than 0.001 mm²/s
            self.assertLess(alpha, 1e-3)      # Less than 1000 mm²/s
        
        # Validate relative diffusivities make physical sense
        # Aluminum (metal) should have highest thermal diffusivity
        self.assertGreater(diffusivities['Aluminum'], diffusivities['Medical PVC'])
        self.assertGreater(diffusivities['Aluminum'], diffusivities['Whole Blood'])
        
        # Note: Insulation can have higher thermal diffusivity than expected due to low density
        # So we'll just check that it's in a reasonable range
        self.assertGreater(diffusivities['Insulation'], 1e-8)  # Not too low
        self.assertLess(diffusivities['Insulation'], 1e-5)     # Not too high
        
        # Blood products should have similar diffusivities to each other
        blood_plasma_ratio = diffusivities['Whole Blood'] / diffusivities['Plasma']
        self.assertGreater(blood_plasma_ratio, 0.1)  # Within order of magnitude
        self.assertLess(blood_plasma_ratio, 10.0)
        
        # Calculate characteristic time scales for different materials
        characteristic_length = 0.01  # 1 cm
        
        for name, alpha in diffusivities.items():
            characteristic_time = characteristic_length**2 / alpha
            
            # Validate reasonable time scales
            if name == 'Aluminum':
                self.assertLess(characteristic_time, 600)     # Fast response for metal (10 min max)
            else:  # All other materials
                self.assertGreater(characteristic_time, 10)   # At least 10 seconds
                self.assertLess(characteristic_time, 36000)   # Less than 10 hours

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)