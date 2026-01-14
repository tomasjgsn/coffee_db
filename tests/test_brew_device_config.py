"""
Test suite for brew device configuration.

Tests the device-specific brewing parameter configurations following TDD principles.
"""

import pytest
from src.config.brew_device_config import (
    BREW_DEVICE_CONFIG,
    get_device_config,
    get_device_fields,
    get_all_device_specific_columns,
    get_device_category,
    DeviceCategory,
)


class TestBrewDeviceConfig:
    """Test the brew device configuration structure"""

    def test_all_expected_devices_present(self):
        """Test that all expected brew devices are configured"""
        expected_devices = [
            "V60",
            "V60 ceramic",
            "Hario Switch",
            "Chemex",
            "Aeropress",
            "French Press",
            "Espresso",
        ]

        for device in expected_devices:
            assert device in BREW_DEVICE_CONFIG, f"Missing device: {device}"

    def test_device_has_required_keys(self):
        """Test that each device configuration has required keys"""
        required_keys = ["category", "fields"]

        for device_name, config in BREW_DEVICE_CONFIG.items():
            for key in required_keys:
                assert key in config, f"Device '{device_name}' missing required key: {key}"

    def test_device_category_is_valid(self):
        """Test that each device has a valid category"""
        valid_categories = [cat.value for cat in DeviceCategory]

        for device_name, config in BREW_DEVICE_CONFIG.items():
            assert config["category"] in valid_categories, \
                f"Device '{device_name}' has invalid category: {config['category']}"

    def test_field_has_required_attributes(self):
        """Test that each field has required attributes"""
        required_field_keys = ["type", "label"]

        for device_name, config in BREW_DEVICE_CONFIG.items():
            for field_name, field_config in config["fields"].items():
                for key in required_field_keys:
                    assert key in field_config, \
                        f"Device '{device_name}' field '{field_name}' missing required key: {key}"


class TestHarioSwitchConfig:
    """Test Hario Switch specific configuration"""

    def test_hario_switch_exists(self):
        """Test that Hario Switch is in the config"""
        assert "Hario Switch" in BREW_DEVICE_CONFIG

    def test_hario_switch_is_hybrid_category(self):
        """Test that Hario Switch is categorized as hybrid"""
        config = BREW_DEVICE_CONFIG["Hario Switch"]
        assert config["category"] == DeviceCategory.HYBRID.value

    def test_hario_switch_has_required_fields(self):
        """Test Hario Switch has all user-requested fields"""
        required_fields = [
            "hario_water_before_grinds",
            "hario_infusion_duration_s",
            "hario_stir",
            "hario_drawdown_time_s",
        ]

        config = BREW_DEVICE_CONFIG["Hario Switch"]
        for field in required_fields:
            assert field in config["fields"], f"Hario Switch missing field: {field}"

    def test_water_before_grinds_is_boolean(self):
        """Test water_before_grinds field is boolean type"""
        config = BREW_DEVICE_CONFIG["Hario Switch"]
        field = config["fields"]["hario_water_before_grinds"]
        assert field["type"] == "boolean"

    def test_infusion_duration_is_number(self):
        """Test infusion_duration field is number type"""
        config = BREW_DEVICE_CONFIG["Hario Switch"]
        field = config["fields"]["hario_infusion_duration_s"]
        assert field["type"] == "number"

    def test_stir_is_dropdown(self):
        """Test stir field is dropdown type"""
        config = BREW_DEVICE_CONFIG["Hario Switch"]
        field = config["fields"]["hario_stir"]
        assert field["type"] == "dropdown"

    def test_drawdown_time_is_dependent(self):
        """Test drawdown_time is marked as dependent variable"""
        config = BREW_DEVICE_CONFIG["Hario Switch"]
        field = config["fields"]["hario_drawdown_time_s"]
        assert field.get("dependent", False) is True


class TestV60Config:
    """Test V60 specific configuration"""

    def test_v60_exists(self):
        """Test that V60 is in the config"""
        assert "V60" in BREW_DEVICE_CONFIG

    def test_v60_is_pour_over_category(self):
        """Test that V60 is categorized as pour_over"""
        config = BREW_DEVICE_CONFIG["V60"]
        assert config["category"] == DeviceCategory.POUR_OVER.value

    def test_v60_has_bloom_fields(self):
        """Test V60 has bloom-related fields"""
        config = BREW_DEVICE_CONFIG["V60"]
        # These map to existing columns
        assert "brew_bloom_water_ml" in config["fields"]
        assert "brew_bloom_time_s" in config["fields"]

    def test_v60_has_swirl_fields(self):
        """Test V60 has swirl tracking fields"""
        config = BREW_DEVICE_CONFIG["V60"]
        assert "v60_swirl_after_bloom" in config["fields"]
        assert "v60_final_swirl" in config["fields"]


class TestAeropressConfig:
    """Test AeroPress specific configuration"""

    def test_aeropress_exists(self):
        """Test that Aeropress is in the config"""
        assert "Aeropress" in BREW_DEVICE_CONFIG

    def test_aeropress_is_immersion_category(self):
        """Test that AeroPress is categorized as immersion"""
        config = BREW_DEVICE_CONFIG["Aeropress"]
        assert config["category"] == DeviceCategory.IMMERSION.value

    def test_aeropress_has_orientation_field(self):
        """Test AeroPress has orientation field"""
        config = BREW_DEVICE_CONFIG["Aeropress"]
        assert "aeropress_orientation" in config["fields"]
        field = config["fields"]["aeropress_orientation"]
        assert field["type"] == "dropdown"

    def test_aeropress_has_steep_time(self):
        """Test AeroPress has steep time field"""
        config = BREW_DEVICE_CONFIG["Aeropress"]
        assert "aeropress_steep_time_s" in config["fields"]

    def test_aeropress_has_press_duration(self):
        """Test AeroPress has press duration field"""
        config = BREW_DEVICE_CONFIG["Aeropress"]
        assert "aeropress_press_duration_s" in config["fields"]


class TestFrenchPressConfig:
    """Test French Press specific configuration"""

    def test_french_press_exists(self):
        """Test that French Press is in the config"""
        assert "French Press" in BREW_DEVICE_CONFIG

    def test_french_press_is_immersion_category(self):
        """Test that French Press is categorized as immersion"""
        config = BREW_DEVICE_CONFIG["French Press"]
        assert config["category"] == DeviceCategory.IMMERSION.value

    def test_french_press_has_hoffmann_method_fields(self):
        """Test French Press has Hoffmann method fields"""
        required_fields = [
            "frenchpress_initial_steep_s",
            "frenchpress_break_crust",
            "frenchpress_skim_foam",
            "frenchpress_settling_time_s",
            "frenchpress_plunge_depth",
        ]

        config = BREW_DEVICE_CONFIG["French Press"]
        for field in required_fields:
            assert field in config["fields"], f"French Press missing field: {field}"


class TestEspressoConfig:
    """Test Espresso specific configuration"""

    def test_espresso_exists(self):
        """Test that Espresso is in the config"""
        assert "Espresso" in BREW_DEVICE_CONFIG

    def test_espresso_is_espresso_category(self):
        """Test that Espresso is categorized correctly"""
        config = BREW_DEVICE_CONFIG["Espresso"]
        assert config["category"] == DeviceCategory.ESPRESSO.value

    def test_espresso_has_yield_field(self):
        """Test Espresso has yield field"""
        config = BREW_DEVICE_CONFIG["Espresso"]
        assert "espresso_yield_g" in config["fields"]

    def test_espresso_has_shot_time(self):
        """Test Espresso has shot time field"""
        config = BREW_DEVICE_CONFIG["Espresso"]
        assert "espresso_shot_time_s" in config["fields"]


class TestHelperFunctions:
    """Test helper functions for accessing device configuration"""

    def test_get_device_config_returns_config(self):
        """Test get_device_config returns correct config"""
        config = get_device_config("Hario Switch")
        assert config is not None
        assert "category" in config
        assert "fields" in config

    def test_get_device_config_returns_none_for_unknown(self):
        """Test get_device_config returns None for unknown device"""
        config = get_device_config("Unknown Device")
        assert config is None

    def test_get_device_config_empty_string(self):
        """Test get_device_config handles empty string"""
        config = get_device_config("")
        assert config is None

    def test_get_device_fields_returns_fields(self):
        """Test get_device_fields returns field dictionary"""
        fields = get_device_fields("Hario Switch")
        assert fields is not None
        assert "hario_water_before_grinds" in fields

    def test_get_device_fields_returns_empty_for_unknown(self):
        """Test get_device_fields returns empty dict for unknown device"""
        fields = get_device_fields("Unknown Device")
        assert fields == {}

    def test_get_all_device_specific_columns(self):
        """Test getting all device-specific column names"""
        columns = get_all_device_specific_columns()

        # Should include Hario Switch columns
        assert "hario_water_before_grinds" in columns
        assert "hario_infusion_duration_s" in columns
        assert "hario_stir" in columns
        assert "hario_drawdown_time_s" in columns

        # Should include AeroPress columns
        assert "aeropress_orientation" in columns
        assert "aeropress_steep_time_s" in columns

        # Should include French Press columns
        assert "frenchpress_initial_steep_s" in columns

        # Should include Espresso columns
        assert "espresso_yield_g" in columns

    def test_get_device_category(self):
        """Test get_device_category returns correct category"""
        assert get_device_category("V60") == DeviceCategory.POUR_OVER.value
        assert get_device_category("Hario Switch") == DeviceCategory.HYBRID.value
        assert get_device_category("Aeropress") == DeviceCategory.IMMERSION.value
        assert get_device_category("Espresso") == DeviceCategory.ESPRESSO.value

    def test_get_device_category_unknown(self):
        """Test get_device_category returns None for unknown device"""
        assert get_device_category("Unknown") is None


class TestDeviceCategory:
    """Test DeviceCategory enum"""

    def test_device_category_values(self):
        """Test that DeviceCategory has expected values"""
        assert DeviceCategory.POUR_OVER.value == "pour_over"
        assert DeviceCategory.IMMERSION.value == "immersion"
        assert DeviceCategory.HYBRID.value == "hybrid"
        assert DeviceCategory.ESPRESSO.value == "espresso"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
