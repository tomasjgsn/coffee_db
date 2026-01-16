"""
Brew Device Configuration

Defines brewing parameters for each device type, informed by James Hoffmann's recipes.
This configuration drives the dynamic form rendering in the UI.
"""

from enum import Enum
from typing import Dict, List, Optional, Any


class DeviceCategory(Enum):
    """Categories of brewing devices"""
    POUR_OVER = "pour_over"
    IMMERSION = "immersion"
    HYBRID = "hybrid"
    ESPRESSO = "espresso"


# Field type definitions for rendering
FIELD_TYPES = {
    "number": "numeric input",
    "boolean": "checkbox",
    "dropdown": "selectbox",
    "text": "text input",
}


BREW_DEVICE_CONFIG: Dict[str, Dict[str, Any]] = {
    # ==========================================================================
    # POUR-OVER DEVICES
    # ==========================================================================
    "V60": {
        "category": DeviceCategory.POUR_OVER.value,
        "description": "Hario V60 pour-over dripper",
        "fields": {
            # Existing fields (mapped to current CSV columns)
            "brew_bloom_water_ml": {
                "type": "number",
                "label": "Bloom Water (ml)",
                "help": "Water for bloom phase (typically 2-3x coffee dose)",
                "default": None,
                "min": 0,
            },
            "brew_bloom_time_s": {
                "type": "number",
                "label": "Bloom Time (s)",
                "help": "Duration of bloom phase",
                "default": 45,
                "min": 0,
            },
            # New V60-specific fields
            "v60_swirl_after_bloom": {
                "type": "boolean",
                "label": "Swirl after bloom",
                "help": "Did you swirl the V60 after blooming?",
                "default": False,
            },
            "num_pours": {
                "type": "number",
                "label": "Number of pours",
                "help": "How many pour phases (excluding bloom)",
                "default": 2,
                "min": 1,
                "max": 10,
            },
            "agitation_method": {
                "type": "dropdown",
                "label": "Agitation Method",
                "help": "Agitation during brewing",
                "options_method": "get_agitation_methods",
            },
            "v60_stir_before_drawdown": {
                "type": "boolean",
                "label": "Stir before drawdown",
                "help": "Did you stir before final drawdown?",
                "default": False,
            },
            "v60_final_swirl": {
                "type": "boolean",
                "label": "Final swirl",
                "help": "Did you swirl before drawdown?",
                "default": False,
            },
            "brew_total_time_s": {
                "type": "number",
                "label": "Total Brew Time (s)",
                "help": "Total time from first pour to end of drawdown",
                "default": None,
                "min": 0,
            },
            "drawdown_time_s": {
                "type": "number",
                "label": "Drawdown Time (s)",
                "help": "Time for final drainage after last pour",
                "default": None,
                "min": 0,
                "dependent": True,
            },
        },
    },

    "V60 ceramic": {
        "category": DeviceCategory.POUR_OVER.value,
        "description": "Hario V60 ceramic pour-over dripper",
        "inherits": "V60",  # Inherits all fields from V60
        # No fields needed - will be resolved via inheritance
    },

    "Chemex": {
        "category": DeviceCategory.POUR_OVER.value,
        "description": "Chemex pour-over brewer with thick filters",
        "fields": {
            "brew_bloom_water_ml": {
                "type": "number",
                "label": "Bloom Water (ml)",
                "help": "Water for bloom phase (60-90g typical)",
                "default": None,
                "min": 0,
            },
            "brew_bloom_time_s": {
                "type": "number",
                "label": "Bloom Time (s)",
                "help": "Duration of bloom phase",
                "default": 45,
                "min": 0,
            },
            "num_pours": {
                "type": "number",
                "label": "Number of pours",
                "help": "How many pour phases (typically 3-4)",
                "default": 3,
                "min": 1,
                "max": 10,
            },
            "agitation_method": {
                "type": "dropdown",
                "label": "Agitation Method",
                "help": "Agitation during brewing",
                "options_method": "get_agitation_methods",
            },
            "brew_total_time_s": {
                "type": "number",
                "label": "Total Brew Time (s)",
                "help": "Total time (typically ~4:10)",
                "default": None,
                "min": 0,
            },
            "drawdown_time_s": {
                "type": "number",
                "label": "Drawdown Time (s)",
                "help": "Time for final drainage",
                "default": None,
                "min": 0,
                "dependent": True,
            },
        },
    },

    # ==========================================================================
    # HYBRID DEVICES
    # ==========================================================================
    "Hario Switch": {
        "category": DeviceCategory.HYBRID.value,
        "description": "Hario Switch immersion/percolation hybrid dripper",
        "fields": {
            "hario_water_before_grinds": {
                "type": "boolean",
                "label": "Water before grinds",
                "help": "Was water added before coffee grounds?",
                "default": False,
            },
            "hario_valve_start_closed": {
                "type": "boolean",
                "label": "Valve closed at start",
                "help": "Was the valve closed when brewing started?",
                "default": True,
            },
            "brew_bloom_water_ml": {
                "type": "number",
                "label": "Bloom Water (ml)",
                "help": "Water for initial bloom/saturation",
                "default": None,
                "min": 0,
            },
            "brew_bloom_time_s": {
                "type": "number",
                "label": "Bloom Time (s)",
                "help": "Duration of initial bloom",
                "default": None,
                "min": 0,
            },
            "hario_infusion_duration_s": {
                "type": "number",
                "label": "Infusion Duration (s)",
                "help": "Total immersion/steep time before opening valve",
                "default": None,
                "min": 0,
            },
            "hario_stir": {
                "type": "dropdown",
                "label": "Stir during infusion",
                "help": "Did you stir during the immersion phase?",
                "options_method": "get_hario_stir_options",
            },
            "hario_settling_time_s": {
                "type": "number",
                "label": "Settling Time (s)",
                "help": "Calculated: valve release time minus infusion duration",
                "default": None,
                "min": 0,
                "dependent": True,
                "calculated": True,
            },
            "hario_valve_release_time_s": {
                "type": "number",
                "label": "Valve Release Time (s)",
                "help": "Time on timer when valve was opened",
                "default": None,
                "min": 0,
            },
            "brew_total_time_s": {
                "type": "number",
                "label": "Total Brew Time (s)",
                "help": "Total time from start to end of drawdown",
                "default": None,
                "min": 0,
            },
            "hario_drawdown_time_s": {
                "type": "number",
                "label": "Drawdown Time (s)",
                "help": "Time for drainage after opening valve",
                "default": None,
                "min": 0,
                "dependent": True,
            },
        },
    },

    # ==========================================================================
    # IMMERSION DEVICES
    # ==========================================================================
    "Aeropress": {
        "category": DeviceCategory.IMMERSION.value,
        "description": "AeroPress immersion brewer with pressure plunge",
        "fields": {
            "aeropress_orientation": {
                "type": "dropdown",
                "label": "Orientation",
                "help": "Standard (filter down) or Inverted (filter up)",
                "options_method": "get_aeropress_orientation_options",
            },
            "aeropress_steep_time_s": {
                "type": "number",
                "label": "Steep Time (s)",
                "help": "Immersion time before pressing (typically 120s)",
                "default": 120,
                "min": 0,
            },
            "aeropress_swirl_before_press": {
                "type": "boolean",
                "label": "Swirl before press",
                "help": "Did you swirl before pressing?",
                "default": False,
            },
            "aeropress_wait_after_swirl_s": {
                "type": "number",
                "label": "Wait after swirl (s)",
                "help": "Rest time after swirling (typically 30s)",
                "default": 30,
                "min": 0,
            },
            "aeropress_press_duration_s": {
                "type": "number",
                "label": "Press Duration (s)",
                "help": "How long the press took (typically 30s)",
                "default": None,
                "min": 0,
            },
            "brew_total_time_s": {
                "type": "number",
                "label": "Total Brew Time (s)",
                "help": "Total time from water contact to end of press",
                "default": None,
                "min": 0,
            },
        },
    },

    "French Press": {
        "category": DeviceCategory.IMMERSION.value,
        "description": "French Press full immersion brewer (Hoffmann method)",
        "fields": {
            "frenchpress_initial_steep_s": {
                "type": "number",
                "label": "Initial Steep Time (s)",
                "help": "Time before breaking crust (typically 240s/4min)",
                "default": 240,
                "min": 0,
            },
            "frenchpress_break_crust": {
                "type": "boolean",
                "label": "Break crust",
                "help": "Did you break/stir the crust?",
                "default": True,
            },
            "frenchpress_skim_foam": {
                "type": "boolean",
                "label": "Skim foam",
                "help": "Did you skim the foam after breaking crust?",
                "default": True,
            },
            "frenchpress_settling_time_s": {
                "type": "number",
                "label": "Settling Time (s)",
                "help": "Wait time after skimming (5-8 min recommended)",
                "default": 300,
                "min": 0,
            },
            "frenchpress_plunge_depth": {
                "type": "dropdown",
                "label": "Plunge Depth",
                "help": "How far did you plunge?",
                "options_method": "get_frenchpress_plunge_options",
            },
            "brew_total_time_s": {
                "type": "number",
                "label": "Total Brew Time (s)",
                "help": "Total time from pour to pour",
                "default": None,
                "min": 0,
            },
        },
    },

    # ==========================================================================
    # ESPRESSO
    # ==========================================================================
    "Espresso": {
        "category": DeviceCategory.ESPRESSO.value,
        "description": "Espresso extraction",
        "fields": {
            "espresso_yield_g": {
                "type": "number",
                "label": "Yield (g)",
                "help": "Output weight of espresso",
                "default": None,
                "min": 0,
            },
            "espresso_shot_time_s": {
                "type": "number",
                "label": "Shot Time (s)",
                "help": "Total extraction time (typically 25-35s)",
                "default": None,
                "min": 0,
            },
            "espresso_preinfusion_s": {
                "type": "number",
                "label": "Pre-infusion (s)",
                "help": "Duration of pre-infusion phase",
                "default": None,
                "min": 0,
            },
            "espresso_pressure_bar": {
                "type": "number",
                "label": "Pressure (bar)",
                "help": "Brew pressure if adjustable",
                "default": 9.0,
                "min": 0,
                "max": 15,
            },
        },
    },

    # ==========================================================================
    # OTHER / FALLBACK
    # ==========================================================================
    "Other": {
        "category": DeviceCategory.POUR_OVER.value,  # Default to pour-over behavior
        "description": "Other brewing device",
        "fields": {
            "brew_bloom_time_s": {
                "type": "number",
                "label": "Bloom Time (s)",
                "help": "Duration of bloom phase",
                "default": None,
                "min": 0,
            },
            "brew_bloom_water_ml": {
                "type": "number",
                "label": "Bloom Water (ml)",
                "help": "Water for bloom phase",
                "default": None,
                "min": 0,
            },
            "agitation_method": {
                "type": "dropdown",
                "label": "Agitation Method",
                "help": "Agitation during brewing",
                "options_method": "get_agitation_methods",
            },
            "brew_total_time_s": {
                "type": "number",
                "label": "Total Brew Time (s)",
                "help": "Total brewing time",
                "default": None,
                "min": 0,
            },
        },
    },

    # Legacy device - keep for backward compatibility
    "Hoffman top up": {
        "category": DeviceCategory.POUR_OVER.value,
        "description": "Hoffmann top-up V60 method",
        "inherits": "V60",  # Inherits all fields from V60
        # No fields needed - will be resolved via inheritance
    },
}


def _resolve_device_config(device_name: str) -> Optional[Dict[str, Any]]:
    """
    Resolve device configuration with inheritance support.

    If a device has an 'inherits' property, merge parent fields with any
    device-specific overrides.

    Args:
        device_name: Name of the brew device

    Returns:
        Resolved device configuration with inherited fields merged
    """
    if not device_name:
        return None

    config = BREW_DEVICE_CONFIG.get(device_name)
    if config is None:
        return None

    # Check if this device inherits from another
    parent_name = config.get("inherits")
    if parent_name:
        parent_config = BREW_DEVICE_CONFIG.get(parent_name)
        if parent_config:
            # Merge parent fields with device-specific overrides
            parent_fields = parent_config.get("fields", {})
            device_fields = config.get("fields", {})
            merged_fields = {**parent_fields, **device_fields}

            # Return merged config
            return {
                **config,
                "fields": merged_fields
            }

    return config


def get_device_config(device_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the configuration for a specific brew device with inheritance resolved.

    Args:
        device_name: Name of the brew device

    Returns:
        Device configuration dictionary with inherited fields merged, or None if not found
    """
    return _resolve_device_config(device_name)


def get_device_fields(device_name: str) -> Dict[str, Dict[str, Any]]:
    """
    Get the field definitions for a specific brew device.

    Args:
        device_name: Name of the brew device

    Returns:
        Dictionary of field configurations, empty dict if device not found
    """
    config = get_device_config(device_name)
    if config is None:
        return {}
    return config.get("fields", {})


def get_device_category(device_name: str) -> Optional[str]:
    """
    Get the category for a specific brew device.

    Args:
        device_name: Name of the brew device

    Returns:
        Category string or None if device not found
    """
    config = get_device_config(device_name)
    if config is None:
        return None
    return config.get("category")


def get_all_device_specific_columns() -> List[str]:
    """
    Get all device-specific column names that need to be added to the CSV.

    Returns:
        List of unique column names across all devices
    """
    columns = set()

    # Columns that already exist in the CSV (don't include these)
    existing_columns = {
        "brew_bloom_water_ml",
        "brew_bloom_time_s",
        "brew_total_time_s",
        "agitation_method",
        "pour_technique",
        "brew_pulse_target_water_ml",
    }

    for device_name, config in BREW_DEVICE_CONFIG.items():
        for field_name in config.get("fields", {}).keys():
            if field_name not in existing_columns:
                columns.add(field_name)

    return sorted(list(columns))


def get_devices_by_category(category: DeviceCategory) -> List[str]:
    """
    Get all devices belonging to a specific category.

    Args:
        category: DeviceCategory enum value

    Returns:
        List of device names in that category
    """
    devices = []
    for device_name, config in BREW_DEVICE_CONFIG.items():
        if config.get("category") == category.value:
            devices.append(device_name)
    return devices
