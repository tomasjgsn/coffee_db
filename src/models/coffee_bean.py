"""
Coffee Bean domain model

Represents a coffee bean with its origin information and properties.
Extracted from the monolithic application following TDD principles.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import pandas as pd


@dataclass
class CoffeeBean:
    """Domain model for a coffee bean"""
    
    name: str
    origin_country: str
    origin_region: Optional[str] = None
    estimated_bag_size_grams: Optional[float] = None
    archive_status: str = "active"
    
    def __post_init__(self):
        """Validate required fields after initialization"""
        if not self.name or self.name.strip() == "":
            raise ValueError("name is required and cannot be empty")
        
        if not self.origin_country or self.origin_country.strip() == "":
            raise ValueError("origin_country is required and cannot be empty")
        
        # Clean up empty string to None for region
        if self.origin_region == "":
            self.origin_region = None
    
    def __eq__(self, other) -> bool:
        """Compare beans by name, country, and region"""
        if not isinstance(other, CoffeeBean):
            return False
        
        return (
            self.name == other.name and
            self.origin_country == other.origin_country and
            self.origin_region == other.origin_region
        )
    
    def __hash__(self) -> int:
        """Hash bean for use in sets and dictionaries"""
        return hash((self.name, self.origin_country, self.origin_region))
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoffeeBean':
        """Create CoffeeBean from dictionary (e.g., CSV row)"""
        # Handle both pandas NaN and None values
        def clean_value(value):
            if pd.isna(value) or value is None:
                return None
            return value
        
        return cls(
            name=data['bean_name'],
            origin_country=data['bean_origin_country'],
            origin_region=clean_value(data.get('bean_origin_region')),
            estimated_bag_size_grams=clean_value(data.get('estimated_bag_size_grams')),
            archive_status=data.get('archive_status', 'active')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert CoffeeBean to dictionary (for CSV saving)"""
        return {
            'bean_name': self.name,
            'bean_origin_country': self.origin_country, 
            'bean_origin_region': self.origin_region,
            'estimated_bag_size_grams': self.estimated_bag_size_grams,
            'archive_status': self.archive_status
        }