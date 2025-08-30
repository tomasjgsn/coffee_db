"""
Tests for Three-Factor Scoring System

Test-driven development for the complexity, bitterness, and mouthfeel scoring validation.
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from services.three_factor_scoring_service import ThreeFactorScoringService


class TestThreeFactorScoringService:
    """Test suite for three-factor scoring service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = ThreeFactorScoringService()
    
    def test_service_initialization(self):
        """Should initialize with correct default values"""
        service = ThreeFactorScoringService()
        assert service.min_score == 0.0
        assert service.max_score == 5.0
        assert service.allow_half_increments is True
    
    def test_validate_complexity_score_valid_values(self):
        """Should validate complexity scores within range"""
        valid_scores = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        
        for score in valid_scores:
            result = self.service.validate_complexity_score(score)
            assert result.is_valid is True
            assert result.error_message is None
    
    def test_validate_complexity_score_invalid_values(self):
        """Should reject invalid complexity scores"""
        invalid_scores = [-1.0, 5.5, 6.0, None, "invalid", 2.3, 2.7]
        
        for score in invalid_scores:
            result = self.service.validate_complexity_score(score)
            assert result.is_valid is False
            assert result.error_message is not None
    
    def test_validate_bitterness_score_valid_values(self):
        """Should validate bitterness scores within range"""
        valid_scores = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        
        for score in valid_scores:
            result = self.service.validate_bitterness_score(score)
            assert result.is_valid is True
            assert result.error_message is None
    
    def test_validate_bitterness_score_invalid_values(self):
        """Should reject invalid bitterness scores"""
        invalid_scores = [-1.0, 5.5, 6.0, None, "invalid", 2.3, 2.7]
        
        for score in invalid_scores:
            result = self.service.validate_bitterness_score(score)
            assert result.is_valid is False
            assert result.error_message is not None
    
    def test_validate_mouthfeel_score_valid_values(self):
        """Should validate mouthfeel scores within range"""
        valid_scores = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        
        for score in valid_scores:
            result = self.service.validate_mouthfeel_score(score)
            assert result.is_valid is True
            assert result.error_message is None
    
    def test_validate_mouthfeel_score_invalid_values(self):
        """Should reject invalid mouthfeel scores"""
        invalid_scores = [-1.0, 5.5, 6.0, None, "invalid", 2.3, 2.7]
        
        for score in invalid_scores:
            result = self.service.validate_mouthfeel_score(score)
            assert result.is_valid is False
            assert result.error_message is not None
    
    def test_validate_all_scores_valid_input(self):
        """Should validate complete three-factor score set"""
        scores = {
            'complexity': 3.5,
            'bitterness': 4.0,
            'mouthfeel': 2.5
        }
        
        result = self.service.validate_all_scores(scores)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_all_scores_mixed_validity(self):
        """Should return specific errors for invalid scores"""
        scores = {
            'complexity': 6.0,  # Invalid - too high
            'bitterness': 4.0,  # Valid
            'mouthfeel': -1.0   # Invalid - too low
        }
        
        result = self.service.validate_all_scores(scores)
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert 'complexity' in result.errors
        assert 'mouthfeel' in result.errors
        assert 'bitterness' not in result.errors
    
    def test_calculate_overall_score_equal_weights(self):
        """Should calculate overall score as average of three factors"""
        scores = {
            'complexity': 4.0,
            'bitterness': 3.0,
            'mouthfeel': 5.0
        }
        
        overall_score = self.service.calculate_overall_score(scores)
        expected = (4.0 + 3.0 + 5.0) / 3
        assert overall_score == pytest.approx(expected, rel=1e-3)
    
    def test_calculate_overall_score_with_zero_values(self):
        """Should handle zero values in calculation"""
        scores = {
            'complexity': 0.0,
            'bitterness': 3.0,
            'mouthfeel': 0.0
        }
        
        overall_score = self.service.calculate_overall_score(scores)
        expected = (0.0 + 3.0 + 0.0) / 3
        assert overall_score == pytest.approx(expected, rel=1e-3)
    
    def test_calculate_overall_score_all_max_values(self):
        """Should handle maximum values correctly"""
        scores = {
            'complexity': 5.0,
            'bitterness': 5.0,
            'mouthfeel': 5.0
        }
        
        overall_score = self.service.calculate_overall_score(scores)
        assert overall_score == 5.0
    
    def test_calculate_overall_score_invalid_input(self):
        """Should raise error for invalid input to calculation"""
        with pytest.raises(ValueError):
            self.service.calculate_overall_score({'complexity': 6.0, 'bitterness': 3.0, 'mouthfeel': 2.0})
        
        with pytest.raises(ValueError):
            self.service.calculate_overall_score({'complexity': 3.0, 'bitterness': 2.0})  # Missing mouthfeel
    
    def test_convert_legacy_score_1_to_10_scale(self):
        """Should convert 1-10 scale scores to 0-5 scale correctly"""
        legacy_scores = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        # Using correct formula: (score - 1) * (5/9)
        expected_scores = [0.0, 0.556, 1.111, 1.667, 2.222, 2.778, 3.333, 3.889, 4.444, 5.0]
        
        for legacy, expected in zip(legacy_scores, expected_scores):
            converted = self.service.convert_legacy_score(legacy)
            assert converted == pytest.approx(expected, rel=1e-3)
    
    def test_convert_legacy_score_edge_cases(self):
        """Should handle edge cases in legacy score conversion"""
        # Test boundary values - correct formula: (score - 1) * (5/9)
        assert self.service.convert_legacy_score(1.0) == 0.0    # (1-1) * (5/9) = 0
        assert self.service.convert_legacy_score(10.0) == 5.0   # (10-1) * (5/9) = 5
        
        # Test decimal values
        assert self.service.convert_legacy_score(7.5) == pytest.approx(3.611, rel=1e-3)   # (7.5-1) * (5/9) ≈ 3.611
        assert self.service.convert_legacy_score(2.3) == pytest.approx(0.722, rel=1e-3)   # (2.3-1) * (5/9) ≈ 0.722
    
    def test_convert_legacy_score_invalid_input(self):
        """Should handle invalid legacy scores"""
        with pytest.raises(ValueError):
            self.service.convert_legacy_score(-1.0)
        
        with pytest.raises(ValueError):
            self.service.convert_legacy_score(11.0)
        
        with pytest.raises(ValueError):
            self.service.convert_legacy_score(None)
    
    def test_format_score_display(self):
        """Should format scores for display correctly"""
        # Test whole numbers
        assert self.service.format_score_display(3.0) == "3"
        assert self.service.format_score_display(5.0) == "5"
        
        # Test half values
        assert self.service.format_score_display(3.5) == "3.5"
        assert self.service.format_score_display(0.5) == "0.5"
        
        # Test zero
        assert self.service.format_score_display(0.0) == "0"
    
    def test_get_score_description(self):
        """Should return appropriate descriptions for score ranges"""
        # Low scores
        assert "low" in self.service.get_score_description("complexity", 1.0).lower()
        
        # High scores  
        assert "high" in self.service.get_score_description("complexity", 5.0).lower()
        
        # Medium scores
        mid_desc = self.service.get_score_description("complexity", 3.0).lower()
        assert "medium" in mid_desc or "moderate" in mid_desc
    
    def test_export_scores_to_dict(self):
        """Should export three-factor scores as dictionary"""
        scores = {
            'complexity': 3.5,
            'bitterness': 4.0,
            'mouthfeel': 2.5
        }
        
        exported = self.service.export_scores_to_dict(scores)
        
        assert exported['score_complexity'] == 3.5
        assert exported['score_bitterness'] == 4.0
        assert exported['score_mouthfeel'] == 2.5
        assert exported['score_overall_rating'] == pytest.approx((3.5 + 4.0 + 2.5) / 3, rel=1e-3)
        assert 'scoring_system_version' in exported
        assert exported['scoring_system_version'] == '3-factor-v1'


class TestValidationResult:
    """Test the validation result data structure"""
    
    def test_validation_result_success(self):
        """Should create successful validation result"""
        from services.three_factor_scoring_service import ValidationResult
        
        result = ValidationResult(is_valid=True, error_message=None)
        assert result.is_valid is True
        assert result.error_message is None
    
    def test_validation_result_failure(self):
        """Should create failed validation result with message"""
        from services.three_factor_scoring_service import ValidationResult
        
        error_msg = "Score must be between 0 and 5"
        result = ValidationResult(is_valid=False, error_message=error_msg)
        assert result.is_valid is False
        assert result.error_message == error_msg


class TestBulkValidationResult:
    """Test the bulk validation result data structure"""
    
    def test_bulk_validation_result_success(self):
        """Should create successful bulk validation result"""
        from services.three_factor_scoring_service import BulkValidationResult
        
        result = BulkValidationResult(is_valid=True, errors={})
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_bulk_validation_result_with_errors(self):
        """Should create bulk validation result with specific errors"""
        from services.three_factor_scoring_service import BulkValidationResult
        
        errors = {
            'complexity': 'Score too high',
            'mouthfeel': 'Score too low'
        }
        result = BulkValidationResult(is_valid=False, errors=errors)
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert result.errors['complexity'] == 'Score too high'
        assert result.errors['mouthfeel'] == 'Score too low'