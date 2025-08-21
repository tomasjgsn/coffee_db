"""
Test brew ID handling to fix the TypeError issue

Following TDD principles - write test first to reproduce the bug, then fix it.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date


class TestBrewIdHandling:
    """Test suite for brew ID generation and handling"""
    
    def test_brew_id_max_with_string_ids(self):
        """Should handle string brew IDs without throwing TypeError"""
        # This test reproduces the bug
        df = pd.DataFrame([
            {'brew_id': '1', 'bean_name': 'Test Bean'},
            {'brew_id': '2', 'bean_name': 'Test Bean'},
            {'brew_id': '10', 'bean_name': 'Test Bean'}  # String '10' > '2' lexicographically
        ])
        
        # This should not throw a TypeError
        # We need a function that handles both string and numeric IDs
        from src.services.brew_id_service import BrewIdService
        
        service = BrewIdService()
        next_id = service.get_next_id(df)
        
        # Should return the next integer ID
        assert next_id == 11  # Max numeric value is 10, so next is 11
    
    def test_brew_id_max_with_numeric_ids(self):
        """Should handle numeric brew IDs correctly"""
        df = pd.DataFrame([
            {'brew_id': 1, 'bean_name': 'Test Bean'},
            {'brew_id': 2, 'bean_name': 'Test Bean'},
            {'brew_id': 10, 'bean_name': 'Test Bean'}
        ])
        
        from src.services.brew_id_service import BrewIdService
        
        service = BrewIdService()
        next_id = service.get_next_id(df)
        
        assert next_id == 11
    
    def test_brew_id_max_with_mixed_ids(self):
        """Should handle mixed string and numeric brew IDs"""
        df = pd.DataFrame([
            {'brew_id': 1, 'bean_name': 'Test Bean'},
            {'brew_id': '2', 'bean_name': 'Test Bean'},
            {'brew_id': 'abc', 'bean_name': 'Test Bean'},  # Non-numeric string
            {'brew_id': '15', 'bean_name': 'Test Bean'}
        ])
        
        from src.services.brew_id_service import BrewIdService
        
        service = BrewIdService()
        next_id = service.get_next_id(df)
        
        # Should find the max numeric value (15) and return 16
        assert next_id == 16
    
    def test_brew_id_empty_dataframe(self):
        """Should handle empty DataFrame"""
        df = pd.DataFrame()
        
        from src.services.brew_id_service import BrewIdService
        
        service = BrewIdService()
        next_id = service.get_next_id(df)
        
        assert next_id == 1
    
    def test_brew_id_no_numeric_ids(self):
        """Should handle case where no numeric IDs exist"""
        df = pd.DataFrame([
            {'brew_id': 'abc', 'bean_name': 'Test Bean'},
            {'brew_id': 'def', 'bean_name': 'Test Bean'},
            {'brew_id': 'xyz', 'bean_name': 'Test Bean'}
        ])
        
        from src.services.brew_id_service import BrewIdService
        
        service = BrewIdService()
        next_id = service.get_next_id(df)
        
        # Should start from 1 if no numeric IDs found
        assert next_id == 1
    
    def test_brew_id_nan_values(self):
        """Should handle NaN values in brew_id column"""
        df = pd.DataFrame([
            {'brew_id': 1, 'bean_name': 'Test Bean'},
            {'brew_id': np.nan, 'bean_name': 'Test Bean'},
            {'brew_id': '5', 'bean_name': 'Test Bean'}
        ])
        
        from src.services.brew_id_service import BrewIdService
        
        service = BrewIdService()
        next_id = service.get_next_id(df)
        
        assert next_id == 6  # Max of 1 and 5 is 5, so next is 6
    
    def test_validate_brew_id_format(self):
        """Should validate brew ID format"""
        from src.services.brew_id_service import BrewIdService
        
        service = BrewIdService()
        
        # Valid IDs
        assert service.validate_brew_id("123") is True
        assert service.validate_brew_id(123) is True
        assert service.validate_brew_id("1") is True
        
        # Invalid IDs
        assert service.validate_brew_id("") is False
        assert service.validate_brew_id(None) is False
        assert service.validate_brew_id("abc") is False
        assert service.validate_brew_id(-1) is False
    
    def test_safe_brew_id_to_int(self):
        """Should safely convert brew IDs to integers with fallback"""
        from src.services.brew_id_service import BrewIdService
        
        service = BrewIdService()
        
        # Valid conversions
        assert service.safe_brew_id_to_int("123") == 123
        assert service.safe_brew_id_to_int(456) == 456
        assert service.safe_brew_id_to_int(789.0) == 789
        
        # Invalid conversions should return default
        assert service.safe_brew_id_to_int("abc") == 0  # default is 0
        assert service.safe_brew_id_to_int(None) == 0
        assert service.safe_brew_id_to_int("") == 0
        assert service.safe_brew_id_to_int(np.nan) == 0
        
        # Custom default
        assert service.safe_brew_id_to_int("invalid", default=999) == 999
    
    def test_brew_id_with_decimal_strings(self):
        """Should handle decimal strings like '1.0' which pandas sometimes creates"""
        from src.services.brew_id_service import BrewIdService
        
        service = BrewIdService()
        
        # Test decimal string conversion
        assert service.safe_brew_id_to_int("1.0") == 1
        assert service.safe_brew_id_to_int("5.0") == 5
        assert service.safe_brew_id_to_int("10.0") == 10
        
        # Test with actual DataFrame scenario
        df = pd.DataFrame([
            {'brew_id': '1.0', 'bean_name': 'Test Bean'},
            {'brew_id': '2.0', 'bean_name': 'Test Bean'},
            {'brew_id': '5.0', 'bean_name': 'Test Bean'}
        ])
        
        next_id = service.get_next_id(df)
        assert next_id == 6  # Max of 1, 2, 5 is 5, so next is 6