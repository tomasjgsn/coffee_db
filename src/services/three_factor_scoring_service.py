"""
Three-Factor Scoring Service

Handles validation, calculation, and conversion for the new three-factor scoring system
based on complexity, bitterness, and mouthfeel ratings (1-5 scale).
"""

from dataclasses import dataclass
from typing import Dict, Optional, Union
import pandas as pd


@dataclass
class ValidationResult:
    """Result of score validation"""
    is_valid: bool
    error_message: Optional[str] = None


@dataclass
class BulkValidationResult:
    """Result of validating multiple scores"""
    is_valid: bool
    errors: Dict[str, str]


class ThreeFactorScoringService:
    """Service for handling three-factor coffee scoring system"""
    
    def __init__(self):
        """Initialize scoring service with default parameters"""
        self.min_score = 0.0
        self.max_score = 5.0
        self.allow_half_increments = True
        self.score_categories = ['complexity', 'bitterness', 'mouthfeel']
    
    def validate_complexity_score(self, score: Union[float, int, None]) -> ValidationResult:
        """Validate complexity score"""
        return self._validate_individual_score(score, 'complexity')
    
    def validate_bitterness_score(self, score: Union[float, int, None]) -> ValidationResult:
        """Validate bitterness score"""
        return self._validate_individual_score(score, 'bitterness')
    
    def validate_mouthfeel_score(self, score: Union[float, int, None]) -> ValidationResult:
        """Validate mouthfeel score"""
        return self._validate_individual_score(score, 'mouthfeel')
    
    def _validate_individual_score(self, score: Union[float, int, None], category: str) -> ValidationResult:
        """Validate an individual score"""
        if score is None:
            return ValidationResult(False, f"{category.title()} score is required")
        
        if not isinstance(score, (int, float)):
            return ValidationResult(False, f"{category.title()} score must be a number")
        
        if score < self.min_score or score > self.max_score:
            return ValidationResult(False, f"{category.title()} score must be between {self.min_score} and {self.max_score}")
        
        if self.allow_half_increments:
            # Check if score is in 0.5 increments
            if (score * 2) != int(score * 2):
                return ValidationResult(False, f"{category.title()} score must be in half-point increments (0.5, 1.0, 1.5, etc.)")
        else:
            # Only allow whole numbers
            if score != int(score):
                return ValidationResult(False, f"{category.title()} score must be a whole number")
        
        return ValidationResult(True)
    
    def validate_all_scores(self, scores: Dict[str, Union[float, int, None]]) -> BulkValidationResult:
        """Validate all three factor scores"""
        errors = {}
        
        # Validate each score category
        if 'complexity' in scores:
            result = self.validate_complexity_score(scores['complexity'])
            if not result.is_valid:
                errors['complexity'] = result.error_message
        else:
            errors['complexity'] = 'Complexity score is required'
        
        if 'bitterness' in scores:
            result = self.validate_bitterness_score(scores['bitterness'])
            if not result.is_valid:
                errors['bitterness'] = result.error_message
        else:
            errors['bitterness'] = 'Bitterness score is required'
        
        if 'mouthfeel' in scores:
            result = self.validate_mouthfeel_score(scores['mouthfeel'])
            if not result.is_valid:
                errors['mouthfeel'] = result.error_message
        else:
            errors['mouthfeel'] = 'Mouthfeel score is required'
        
        is_valid = len(errors) == 0
        return BulkValidationResult(is_valid, errors)
    
    def calculate_overall_score(self, scores: Dict[str, Union[float, int]]) -> float:
        """Calculate overall score as average of three factors"""
        # Validate input first
        validation_result = self.validate_all_scores(scores)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid scores provided: {validation_result.errors}")
        
        # Check all required scores are present
        required_keys = {'complexity', 'bitterness', 'mouthfeel'}
        if not required_keys.issubset(scores.keys()):
            missing = required_keys - set(scores.keys())
            raise ValueError(f"Missing required scores: {missing}")
        
        # Calculate average
        total = scores['complexity'] + scores['bitterness'] + scores['mouthfeel']
        overall_score = total / 3.0
        
        return round(overall_score, 3)  # Round to 3 decimal places for precision
    
    def convert_legacy_score(self, legacy_score: Union[float, int, None]) -> float:
        """Convert 1-10 scale score to 0-5 scale"""
        if legacy_score is None:
            raise ValueError("Legacy score cannot be None")
        
        if not isinstance(legacy_score, (int, float)):
            raise ValueError("Legacy score must be a number")
        
        if legacy_score < 0.0 or legacy_score > 10.0:
            raise ValueError("Legacy score must be between 0.0 and 10.0")
        
        # Convert from 1-10 scale to 0-5 scale
        # Formula: new_score = old_score * 0.5
        new_score = legacy_score * 0.5
        
        return round(new_score, 3)
    
    def format_score_display(self, score: Union[float, int]) -> str:
        """Format score for display (remove unnecessary decimals)"""
        if score == int(score):
            return str(int(score))
        else:
            return str(score)
    
    def get_score_description(self, category: str, score: Union[float, int]) -> str:
        """Get descriptive text for score ranges"""
        if score <= 1.5:
            return f"Low {category}"
        elif score <= 2.5:
            return f"Medium-low {category}"
        elif score <= 3.5:
            return f"Medium {category}"
        elif score <= 4.5:
            return f"Medium-high {category}"
        else:
            return f"High {category}"
    
    def export_scores_to_dict(self, scores: Dict[str, Union[float, int]]) -> Dict[str, Union[float, str]]:
        """Export three-factor scores as dictionary for database storage"""
        # Calculate overall score
        overall_score = self.calculate_overall_score(scores)
        
        return {
            'score_complexity': scores['complexity'],
            'score_bitterness': scores['bitterness'],
            'score_mouthfeel': scores['mouthfeel'],
            'score_overall_rating': overall_score,
            'scoring_system_version': '3-factor-v1'
        }