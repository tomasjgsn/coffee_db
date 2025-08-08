"""
Brewing calculations and classifications

Contains business logic for coffee brewing science calculations.
Extracted from the monolithic application following TDD principles.
"""

from typing import Optional


# Default thresholds based on coffee science research
DEFAULT_STRENGTH_THRESHOLDS = {
    "weak_max": 1.15,
    "ideal_max": 1.35
}

DEFAULT_EXTRACTION_THRESHOLDS = {
    "under_max": 18.0,
    "ideal_max": 22.0
}

DEFAULT_ZONE_BONUSES = {
    "Ideal-Ideal": 10,
    "Ideal-Weak": 7,
    "Ideal-Strong": 7,
    "Under-Ideal": 7,
    "Over-Ideal": 7,
    "Under-Weak": 4,
    "Under-Strong": 4,
    "Over-Weak": 4,
    "Over-Strong": 4
}


def categorize_strength(tds_percent: float) -> str:
    """Categorize strength based on TDS percentage"""
    if tds_percent < DEFAULT_STRENGTH_THRESHOLDS["weak_max"]:
        return "Weak"
    elif tds_percent <= DEFAULT_STRENGTH_THRESHOLDS["ideal_max"]:
        return "Ideal"
    else:
        return "Strong"


def categorize_extraction(extraction_yield: float) -> str:
    """Categorize extraction based on yield percentage"""
    if extraction_yield < DEFAULT_EXTRACTION_THRESHOLDS["under_max"]:
        return "Under"
    elif extraction_yield <= DEFAULT_EXTRACTION_THRESHOLDS["ideal_max"]:
        return "Ideal"
    else:
        return "Over"


def classify_brewing_zone(tds_percent: float, extraction_yield: float) -> str:
    """Generate brewing zone classification"""
    strength_category = categorize_strength(tds_percent)
    extraction_category = categorize_extraction(extraction_yield)
    return f"{extraction_category}-{strength_category}"


def calculate_brew_score(overall_rating: Optional[float], brewing_zone: str) -> Optional[float]:
    """Calculate composite brew score based on rating and brewing zone"""
    if overall_rating is None:
        return None
    
    # Get zone bonus
    zone_bonus = DEFAULT_ZONE_BONUSES.get(brewing_zone, 4)  # Default to 4 if zone not found
    
    # Calculate weighted score: 60% rating + 40% zone bonus
    brew_score = (overall_rating * 0.6) + (zone_bonus * 0.4)
    return round(brew_score, 1)


def calculate_days_since_roast(brew_date, bean_purchase_date) -> Optional[int]:
    """Calculate days since bean roast date (using purchase date as proxy)"""
    if brew_date is None or bean_purchase_date is None:
        return None
    
    days_diff = (brew_date - bean_purchase_date).days
    
    if days_diff < 0:
        return None  # Negative days doesn't make sense
    
    return days_diff