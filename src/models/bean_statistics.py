"""
Bean statistics calculation model

Handles statistical calculations for individual coffee beans across multiple brew records.
Extracted from the monolithic application following TDD principles.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, List
import pandas as pd


@dataclass
class BeanStatistics:
    """Statistical summary for a coffee bean"""
    
    name: str
    country: str
    region: Optional[str]
    total_brews: int
    total_grams_used: float
    bag_size: float
    remaining_grams: float
    usage_percentage: float
    avg_rating: float
    last_used: Optional[date]
    days_since_last: Optional[int]
    archive_status: str
    records: List[dict]
    
    @classmethod
    def calculate_for_bean(cls, bean_name: str, df: pd.DataFrame) -> 'BeanStatistics':
        """Calculate statistics for a specific bean from DataFrame"""
        
        # Filter records for this bean
        bean_df = df[df['bean_name'] == bean_name].copy()
        
        if len(bean_df) == 0:
            raise ValueError(f"No records found for bean: {bean_name}")
        
        # Get basic bean info from first record
        first_record = bean_df.iloc[0]
        name = first_record['bean_name']
        country = first_record.get('bean_origin_country', 'Unknown')
        region = first_record.get('bean_origin_region')
        if pd.isna(region):
            region = None
        
        # Calculate statistics
        total_brews = len(bean_df)
        
        # Total grams used (handle NaN values)
        grams_series = bean_df['coffee_dose_grams'].fillna(0)
        total_grams_used = float(grams_series.sum())
        
        # Bag size and remaining calculations
        bag_size = float(first_record.get('estimated_bag_size_grams', 0))
        if pd.isna(bag_size):
            bag_size = 0.0
        
        remaining_grams = max(0, bag_size - total_grams_used)
        usage_percentage = (total_grams_used / bag_size * 100) if bag_size > 0 else 0.0
        
        # Average rating (handle NaN values)
        ratings = bean_df['score_overall_rating'].dropna()
        avg_rating = float(ratings.mean()) if len(ratings) > 0 else 0.0
        
        # Last used date and days since
        last_used = None
        days_since_last = None
        if 'brew_date' in bean_df.columns:
            # Convert to datetime if needed
            dates = pd.to_datetime(bean_df['brew_date'], errors='coerce').dt.date
            valid_dates = dates.dropna()
            if len(valid_dates) > 0:
                last_used = valid_dates.max()
                if last_used:
                    days_since_last = (date.today() - last_used).days
        
        # Archive status
        archive_status = first_record.get('archive_status', 'active')
        if pd.isna(archive_status):
            archive_status = 'active'
        
        # Convert records to list of dicts
        records = bean_df.to_dict('records')
        
        return cls(
            name=name,
            country=country,
            region=region,
            total_brews=total_brews,
            total_grams_used=total_grams_used,
            bag_size=bag_size,
            remaining_grams=remaining_grams,
            usage_percentage=round(usage_percentage, 1),
            avg_rating=round(avg_rating, 2) if avg_rating > 0 else 0.0,
            last_used=last_used,
            days_since_last=days_since_last,
            archive_status=archive_status,
            records=records
        )
    
    @classmethod
    def calculate_all_beans(cls, df: pd.DataFrame) -> List['BeanStatistics']:
        """Calculate statistics for all unique beans in DataFrame"""
        if df.empty:
            return []
        
        # Get unique beans
        unique_beans = df['bean_name'].dropna().unique()
        
        statistics = []
        for bean_name in unique_beans:
            try:
                stats = cls.calculate_for_bean(bean_name, df)
                statistics.append(stats)
            except Exception as e:
                # Log error but continue processing other beans
                print(f"Error calculating statistics for {bean_name}: {e}")
                continue
        
        return statistics