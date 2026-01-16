"""
Configuration module for coffee database application.
"""

from .brew_device_config import (
    BREW_DEVICE_CONFIG,
    get_device_config,
    get_device_fields,
    get_all_device_specific_columns,
    get_device_category,
    DeviceCategory,
)

__all__ = [
    'BREW_DEVICE_CONFIG',
    'get_device_config',
    'get_device_fields',
    'get_all_device_specific_columns',
    'get_device_category',
    'DeviceCategory',
]
