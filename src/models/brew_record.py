"""
Brew Record domain model

Represents a single coffee brewing session with all measurements and calculated fields.
Extracted from the monolithic application following TDD principles.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Dict, Any
import pandas as pd


@dataclass 
class BrewRecord:
    """Domain model for a coffee brew record"""
    
    brew_id: str
    bean_name: str
    brew_date: date
    coffee_dose_grams: float
    water_volume_ml: int
    final_tds_percent: float
    final_brew_mass_grams: float
    
    # Optional fields
    score_overall_rating: Optional[float] = None
    bean_purchase_date: Optional[date] = None
    grind_size: Optional[float] = None
    water_temperature_c: Optional[float] = None
    notes: Optional[str] = None
    
    # Calculated fields (computed automatically)
    brew_ratio_to_1: float = field(init=False)
    final_extraction_yield_percent: float = field(init=False)
    coffee_grams_per_liter: float = field(init=False)
    
    def __post_init__(self):
        """Validate inputs and calculate derived fields"""
        self._validate_inputs()
        self._calculate_derived_fields()
    
    def _validate_inputs(self):
        """Validate input data ranges"""
        if not (0.1 <= self.coffee_dose_grams <= 50.0):
            raise ValueError("coffee_dose_grams must be between 0.1 and 50.0")
        
        if not (1 <= self.water_volume_ml <= 1000):
            raise ValueError("water_volume_ml must be between 1 and 1000")
        
        if not (0.1 <= self.final_tds_percent <= 3.0):
            raise ValueError("final_tds_percent must be between 0.1 and 3.0")
        
        if not (0.1 <= self.final_brew_mass_grams <= 1000.0):
            raise ValueError("final_brew_mass_grams must be between 0.1 and 1000.0")
        
        if self.score_overall_rating is not None:
            if not (0 <= self.score_overall_rating <= 10):
                raise ValueError("score_overall_rating must be between 0 and 10")
    
    def _calculate_derived_fields(self):
        """Calculate derived brewing metrics"""
        # Brew ratio (water:coffee)
        self.brew_ratio_to_1 = round(self.water_volume_ml / self.coffee_dose_grams, 1)
        
        # Extraction yield percentage
        self.final_extraction_yield_percent = round(
            (self.final_brew_mass_grams * self.final_tds_percent) / self.coffee_dose_grams, 2
        )
        
        # Coffee grams per liter of water
        self.coffee_grams_per_liter = round(
            (self.coffee_dose_grams / self.water_volume_ml) * 1000, 1
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrewRecord':
        """Create BrewRecord from dictionary (e.g., CSV row)"""
        def clean_value(value):
            if pd.isna(value) or value is None:
                return None
            return value
        
        def parse_date(date_value):
            if date_value is None or pd.isna(date_value):
                return None
            if isinstance(date_value, str):
                return datetime.strptime(date_value, '%Y-%m-%d').date()
            elif isinstance(date_value, datetime):
                return date_value.date()
            elif isinstance(date_value, date):
                return date_value
            return None
        
        return cls(
            brew_id=data['brew_id'],
            bean_name=data['bean_name'],
            brew_date=parse_date(data['brew_date']),
            coffee_dose_grams=float(data['coffee_dose_grams']),
            water_volume_ml=int(data['water_volume_ml']),
            final_tds_percent=float(data['final_tds_percent']),
            final_brew_mass_grams=float(data['final_brew_mass_grams']),
            score_overall_rating=clean_value(data.get('score_overall_rating')),
            bean_purchase_date=parse_date(data.get('bean_purchase_date')),
            grind_size=clean_value(data.get('grind_size')),
            water_temperature_c=clean_value(data.get('water_temperature_c')),
            notes=clean_value(data.get('notes'))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert BrewRecord to dictionary (for CSV saving)"""
        return {
            'brew_id': self.brew_id,
            'bean_name': self.bean_name,
            'brew_date': self.brew_date.strftime('%Y-%m-%d') if self.brew_date else None,
            'coffee_dose_grams': self.coffee_dose_grams,
            'water_volume_ml': self.water_volume_ml,
            'final_tds_percent': self.final_tds_percent,
            'final_brew_mass_grams': self.final_brew_mass_grams,
            'score_overall_rating': self.score_overall_rating,
            'bean_purchase_date': self.bean_purchase_date.strftime('%Y-%m-%d') if self.bean_purchase_date else None,
            'grind_size': self.grind_size,
            'water_temperature_c': self.water_temperature_c,
            'notes': self.notes,
            'brew_ratio_to_1': self.brew_ratio_to_1,
            'final_extraction_yield_percent': self.final_extraction_yield_percent,
            'coffee_grams_per_liter': self.coffee_grams_per_liter
        }