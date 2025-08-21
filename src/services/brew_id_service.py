"""
Brew ID Service

Handles brew ID generation and validation to fix the TypeError issue
in the main application where string IDs were causing arithmetic errors.
"""

import pandas as pd
import numpy as np
from typing import Union, Any
import logging


class BrewIdService:
    """Service for handling brew ID generation and validation"""
    
    def __init__(self):
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(f"{__name__}.BrewIdService")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_next_id(self, df: pd.DataFrame) -> int:
        """
        Get the next brew ID from a DataFrame, handling mixed string/numeric IDs
        
        Args:
            df: DataFrame containing brew_id column
            
        Returns:
            Next available integer ID
        """
        try:
            # Handle empty DataFrame
            if df.empty or 'brew_id' not in df.columns:
                return 1
            
            # Get all brew_id values and convert to numeric where possible
            brew_ids = df['brew_id'].dropna()  # Remove NaN values
            
            if len(brew_ids) == 0:
                return 1
            
            numeric_ids = []
            
            for brew_id in brew_ids:
                try:
                    # Try to convert to integer
                    if isinstance(brew_id, str):
                        # Handle string IDs (including floats as strings like '1.0')
                        stripped = brew_id.strip()
                        if stripped.replace('.', '').isdigit() or stripped.isdigit():
                            # Convert string to float then int to handle '1.0' -> 1
                            numeric_ids.append(int(float(stripped)))
                        # Skip non-numeric strings
                    elif isinstance(brew_id, (int, float)) and not pd.isna(brew_id):
                        # Handle numeric IDs
                        numeric_ids.append(int(brew_id))
                except (ValueError, TypeError):
                    # Skip invalid values
                    continue
            
            if len(numeric_ids) == 0:
                # No numeric IDs found, start from 1
                return 1
            
            # Return max + 1
            max_id = max(numeric_ids)
            return max_id + 1
            
        except Exception as e:
            self.logger.error(f"Error generating next brew ID: {e}")
            return 1
    
    def validate_brew_id(self, brew_id: Any) -> bool:
        """
        Validate that a brew ID is acceptable
        
        Args:
            brew_id: The ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if brew_id is None:
                return False
            
            if isinstance(brew_id, str):
                # Empty strings are invalid
                if not brew_id.strip():
                    return False
                
                # Must be a positive integer as string
                if brew_id.strip().isdigit():
                    return int(brew_id.strip()) > 0
                else:
                    return False
            
            elif isinstance(brew_id, (int, float)):
                # Must be positive integer
                if pd.isna(brew_id):
                    return False
                
                # Convert to int and check if it's positive
                int_id = int(brew_id)
                return int_id > 0 and int_id == brew_id  # No decimal part
            
            return False
            
        except (ValueError, TypeError):
            return False
    
    def normalize_brew_id(self, brew_id: Any) -> Union[int, None]:
        """
        Normalize a brew ID to an integer
        
        Args:
            brew_id: The ID to normalize
            
        Returns:
            Integer ID or None if invalid
        """
        try:
            if not self.validate_brew_id(brew_id):
                return None
            
            if isinstance(brew_id, str):
                return int(brew_id.strip())
            elif isinstance(brew_id, (int, float)):
                return int(brew_id)
            
            return None
            
        except (ValueError, TypeError):
            return None
    
    def safe_brew_id_to_int(self, brew_id: Any, default: int = 0) -> int:
        """
        Safely convert brew_id to integer, with fallback
        
        Args:
            brew_id: The ID to convert
            default: Default value if conversion fails
            
        Returns:
            Integer ID or default value
        """
        try:
            if isinstance(brew_id, str):
                stripped = brew_id.strip()
                if stripped.replace('.', '').isdigit() or stripped.isdigit():
                    # Handle strings like '1.0' or '1'
                    return int(float(stripped))
                else:
                    return default
            elif isinstance(brew_id, (int, float)) and not pd.isna(brew_id):
                return int(brew_id)
            else:
                return default
                
        except (ValueError, TypeError):
            return default