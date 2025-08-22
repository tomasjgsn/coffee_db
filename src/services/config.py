"""
Configuration management for coffee brewing services
"""

import os
from pathlib import Path
from typing import Dict, Any


class ServiceConfig:
    """Centralized configuration for services"""
    
    # File paths
    DEFAULT_CSV_PATH = "data/cups_of_coffee.csv"
    
    # Data limits
    MAX_FILE_SIZE_MB = 500
    WARN_FILE_SIZE_MB = 100
    
    # Processing timeouts
    POST_PROCESSING_TIMEOUT = 30
    FULL_PROCESSING_TIMEOUT = 60
    
    # UI settings
    RECENT_ADDITIONS_TIMEOUT_MINUTES = 15
    MAX_CHART_POINTS = 1000
    
    # Grind dial settings (Fellow Ode Gen 2)
    GRIND_MIN = 1.0
    GRIND_MAX = 11.0
    GRIND_INCREMENTS = [0.1, 0.2]
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def get_csv_path(cls) -> Path:
        """Get the CSV file path from environment or default"""
        csv_path = os.getenv('COFFEE_CSV_PATH', cls.DEFAULT_CSV_PATH)
        return Path(csv_path)
    
    @classmethod
    def get_processing_timeout(cls, full_processing: bool = False) -> int:
        """Get processing timeout based on type"""
        return cls.FULL_PROCESSING_TIMEOUT if full_processing else cls.POST_PROCESSING_TIMEOUT
    
    @classmethod
    def get_file_size_limits(cls) -> Dict[str, float]:
        """Get file size limits in MB"""
        return {
            'max': cls.MAX_FILE_SIZE_MB,
            'warn': cls.WARN_FILE_SIZE_MB
        }
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return os.getenv('COFFEE_ENV', 'production').lower() == 'development'