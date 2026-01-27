import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime, date
import numpy as np
import hashlib
import json
from collections import defaultdict

from src.models.unified_score import UnifiedBrewingScore, calculate_unified_score

@dataclass
class CoffeeProcessingConfig:
    """Configuration for coffee data processing
    
    Date Format Standard: All dates are standardized to ISO 8601 format (YYYY-MM-DD)
    - Input: Accepts YYYY-MM-DD or legacy DD/MM/YY formats
    - Output: Always returns YYYY-MM-DD format
    """
    strength_thresholds: Dict[str, float] = None
    extraction_thresholds: Dict[str, float] = None
    zone_bonuses: Dict[str, float] = None
    validation_ranges: Dict[str, Dict[str, float]] = None
    calculation_version: str = "1.1"  # Updated for date standardization
    
    def __post_init__(self):
        if self.strength_thresholds is None:
            self.strength_thresholds = {"weak_max": 1.15, "ideal_max": 1.35}
        if self.extraction_thresholds is None:
            self.extraction_thresholds = {"under_max": 18.0, "ideal_max": 22.0}
        if self.zone_bonuses is None:
            self.zone_bonuses = {"ideal_ideal": 10, "ideal_other": 7, "other_ideal": 7, "other": 4}
        if self.validation_ranges is None:
            self.validation_ranges = {
                "coffee_dose_grams": {"min": 0.1, "max": 50.0},
                "water_volume_ml": {"min": 1, "max": 1000},
                "final_tds_percent": {"min": 0.1, "max": 3.0},
                "final_brew_mass_grams": {"min": 0.1, "max": 1000.0}
            }

class CoffeeDataProcessor:
    """Coffee brewing data processor that transforms raw data into comprehensive metrics"""
    
    REQUIRED_FIELDS = [
        'coffee_dose_grams', 'water_volume_ml', 'final_tds_percent', 
        'final_brew_mass_grams', 'brew_date', 'bean_name'
    ]
    
    OPTIONAL_FIELDS = [
        'score_overall_rating', 'bean_purchase_date'
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = CoffeeProcessingConfig(**(config or {}))
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data according to requirements"""
        try:
            # Check required fields
            missing_fields = [field for field in self.REQUIRED_FIELDS if field not in data or data[field] is None]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Validate data types and ranges
            self._validate_numeric_field(data, 'coffee_dose_grams', float)
            self._validate_numeric_field(data, 'water_volume_ml', (int, float))
            self._validate_numeric_field(data, 'final_tds_percent', float)
            self._validate_numeric_field(data, 'final_brew_mass_grams', float)
            
            # Validate optional fields if present
            if 'score_overall_rating' in data and pd.notna(data['score_overall_rating']):
                self._validate_numeric_field(data, 'score_overall_rating', (int, float))
            
            # Validate ranges
            for field, ranges in self.config.validation_ranges.items():
                if field in data and data[field] is not None:
                    value = float(data[field])
                    if not (ranges['min'] <= value <= ranges['max']):
                        raise ValueError(f"{field} value {value} outside valid range {ranges['min']}-{ranges['max']}")
            
            # Validate dates
            self._validate_date_field(data, 'brew_date')
            if 'bean_purchase_date' in data and data['bean_purchase_date'] is not None and str(data['bean_purchase_date']).strip() != '':
                self._validate_date_field(data, 'bean_purchase_date')
            
            # Logical validations (allow some tolerance for brew mass > water volume)
            if data['final_brew_mass_grams'] > data['water_volume_ml'] * 1.1:  # 10% tolerance
                self.logger.warning(f"final_brew_mass_grams ({data['final_brew_mass_grams']}) significantly exceeds water_volume_ml ({data['water_volume_ml']})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            raise
    
    def _validate_numeric_field(self, data: Dict[str, Any], field: str, expected_type: Union[type, tuple]) -> None:
        """Validate a numeric field"""
        if field in data and data[field] is not None:
            try:
                value = float(data[field]) if not isinstance(data[field], (int, float)) else data[field]
                if not isinstance(value, expected_type if isinstance(expected_type, tuple) else (expected_type,)):
                    if not isinstance(value, (int, float)):
                        raise ValueError(f"{field} must be numeric")
                if value <= 0:
                    raise ValueError(f"{field} must be greater than 0")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid {field}: {e}")
    
    def _validate_date_field(self, data: Dict[str, Any], field: str) -> None:
        """Validate a date field and ensure it can be parsed to standard format"""
        if field in data and data[field] is not None:
            try:
                # Use our standardized date parser
                parsed_date = self._parse_date(data[field])
                # This validates that the date can be parsed successfully
            except Exception as e:
                raise ValueError(f"Invalid {field}: {e}. Expected format: YYYY-MM-DD or legacy DD/MM/YY")
    
    def _calculate_beans_days_since_roast(self, brew_data: Dict[str, Any]) -> Optional[int]:
        """Calculate days since bean roast date"""
        try:
            if 'bean_purchase_date' not in brew_data or brew_data['bean_purchase_date'] is None:
                return None
            
            brew_date = self._parse_date(brew_data['brew_date'])
            purchase_date = self._parse_date(brew_data['bean_purchase_date'])
            
            days_diff = (brew_date - purchase_date).days
            
            if days_diff < 0:
                self.logger.warning(f"Negative days since roast: {days_diff}. Brew date before purchase date.")
                return None
            
            return days_diff
            
        except Exception as e:
            self.logger.error(f"Error calculating beans_days_since_roast: {e}")
            return None
    
    def _calculate_brew_ratio(self, brew_data: Dict[str, Any]) -> float:
        """Calculate brew ratio (water:coffee)"""
        try:
            ratio = brew_data['water_volume_ml'] / brew_data['coffee_dose_grams']
            return round(ratio, 1)
        except ZeroDivisionError:
            self.logger.error("Cannot calculate brew ratio: coffee_dose_grams is zero")
            raise
        except Exception as e:
            self.logger.error(f"Error calculating brew ratio: {e}")
            raise
    
    def _calculate_extraction_yield(self, brew_data: Dict[str, Any]) -> float:
        """Calculate final extraction yield percentage"""
        try:
            yield_percent = (brew_data['final_brew_mass_grams'] * brew_data['final_tds_percent']) / brew_data['coffee_dose_grams']
            return round(yield_percent, 2)
        except ZeroDivisionError:
            self.logger.error("Cannot calculate extraction yield: coffee_dose_grams is zero")
            raise
        except Exception as e:
            self.logger.error(f"Error calculating extraction yield: {e}")
            raise
    
    def _calculate_coffee_grams_per_liter(self, brew_data: Dict[str, Any]) -> float:
        """Calculate coffee dose in grams per liter of water"""
        try:
            grams_per_liter = (brew_data['coffee_dose_grams'] / brew_data['water_volume_ml']) * 1000
            return round(grams_per_liter, 1)
        except ZeroDivisionError:
            self.logger.error("Cannot calculate grams per liter: water_volume_ml is zero")
            raise
        except Exception as e:
            self.logger.error(f"Error calculating grams per liter: {e}")
            raise
    
    def _classify_strength(self, tds_percent: float) -> str:
        """Classify strength based on TDS percentage"""
        if tds_percent < self.config.strength_thresholds['weak_max']:
            return "Weak"
        elif tds_percent <= self.config.strength_thresholds['ideal_max']:
            return "Ideal"
        else:
            return "Strong"
    
    def _classify_extraction(self, extraction_yield: float) -> str:
        """Classify extraction based on yield percentage"""
        if extraction_yield < self.config.extraction_thresholds['under_max']:
            return "Under"
        elif extraction_yield <= self.config.extraction_thresholds['ideal_max']:
            return "Ideal"
        else:
            return "Over"
    
    def _generate_brewing_zone(self, extraction_category: str, strength_category: str) -> str:
        """Generate brewing zone classification"""
        return f"{extraction_category}-{strength_category}"
    
    def _calculate_brew_score(self, overall_rating: Optional[float], brewing_zone: str) -> Optional[float]:
        """Calculate composite brew score"""
        try:
            # Return None if overall_rating is missing
            if overall_rating is None or pd.isna(overall_rating):
                return None
                
            # Determine zone bonus
            if brewing_zone == "Ideal-Ideal":
                zone_bonus = self.config.zone_bonuses['ideal_ideal']
            elif "Ideal" in brewing_zone:
                zone_bonus = self.config.zone_bonuses['ideal_other']
            else:
                zone_bonus = self.config.zone_bonuses['other']
            
            # Calculate weighted score
            brew_score = (overall_rating * 0.6) + (zone_bonus * 0.4)
            return round(brew_score, 1)

        except Exception as e:
            self.logger.error(f"Error calculating brew score: {e}")
            raise

    def _calculate_unified_brewing_score(
        self,
        extraction_yield: Optional[float],
        tds_percent: Optional[float],
        coffee_grams_per_liter: Optional[float]
    ) -> Optional[float]:
        """Calculate brew-ratio-aware unified brewing score (0-100).

        The unified score measures how close a brew's (extraction, TDS) pair
        is to the optimal point for its specific brew ratio on the isometric line.

        Args:
            extraction_yield: Final extraction yield percentage
            tds_percent: TDS percentage
            coffee_grams_per_liter: Brew ratio in g/L

        Returns:
            Score 0-100 or None if inputs are missing/invalid
        """
        try:
            # Use the convenience function which handles None values gracefully
            score = calculate_unified_score(
                extraction=extraction_yield,
                tds=tds_percent,
                brew_ratio=coffee_grams_per_liter
            )

            if score is not None:
                return round(score, 1)
            return None

        except Exception as e:
            self.logger.warning(f"Error calculating unified brewing score: {e}")
            return None

    def _parse_date(self, date_value: Union[str, date, datetime]) -> Optional[date]:
        """Parse date and convert to standard format (YYYY-MM-DD)
        
        Accepts:
        - ISO format: YYYY-MM-DD (preferred/standard)
        - Legacy format: D/M/YY or DD/MM/YY (converted to standard)
        - Empty string: Returns None (for optional date fields)
        """
        if isinstance(date_value, datetime):
            return date_value.date()
        elif isinstance(date_value, date):
            return date_value
        elif isinstance(date_value, str):
            date_value = date_value.strip()
            
            # Handle empty string as None (optional date fields)
            if not date_value:
                return None
            
            # First try ISO format (YYYY-MM-DD) - this is our standard
            try:
                return datetime.strptime(date_value, '%Y-%m-%d').date()
            except ValueError:
                pass
            
            # Handle legacy DD/MM/YY format from existing data
            if '/' in date_value:
                try:
                    # Parse DD/MM/YY or D/M/YY format
                    parsed_date = datetime.strptime(date_value, '%d/%m/%y')
                    # Convert 2-digit year to 4-digit (25 = 2025, etc.)
                    if parsed_date.year < 100:
                        if parsed_date.year <= 30:
                            parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                        else:
                            parsed_date = parsed_date.replace(year=parsed_date.year + 1900)
                    return parsed_date.date()
                except ValueError:
                    pass
            
            # Try ISO format with time
            try:
                return datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S').date()
            except ValueError:
                pass
            
            raise ValueError(f"Date must be in YYYY-MM-DD format. Received: {date_value}")
        else:
            raise ValueError(f"Invalid date type: {type(date_value)}")
    
    def _format_date_to_standard(self, date_obj: Optional[date]) -> Optional[str]:
        """Convert date object to standard ISO format string (YYYY-MM-DD)"""
        if date_obj is None:
            return None
        return date_obj.strftime('%Y-%m-%d')
    
    def process_single_brew(self, brew_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single brew record and add calculated fields"""
        try:
            # Validate input
            self.validate_input(brew_data)
            
            # Create copy to avoid modifying original
            result = brew_data.copy()
            
            # Normalize dates to standard format (YYYY-MM-DD)
            if 'brew_date' in result and result['brew_date'] is not None:
                parsed_brew_date = self._parse_date(result['brew_date'])
                result['brew_date'] = self._format_date_to_standard(parsed_brew_date)
            
            if 'bean_purchase_date' in result and result['bean_purchase_date'] is not None and str(result['bean_purchase_date']).strip() != '':
                parsed_purchase_date = self._parse_date(result['bean_purchase_date'])
                if parsed_purchase_date is not None:
                    result['bean_purchase_date'] = self._format_date_to_standard(parsed_purchase_date)
                else:
                    result['bean_purchase_date'] = ''
            
            # Time-based calculations
            result['beans_days_since_roast'] = self._calculate_beans_days_since_roast(brew_data)
            
            # Brewing calculations
            result['brew_ratio_to_1'] = self._calculate_brew_ratio(brew_data)
            result['final_extraction_yield_percent'] = self._calculate_extraction_yield(brew_data)
            result['coffee_grams_per_liter'] = self._calculate_coffee_grams_per_liter(brew_data)
            
            # Classifications
            result['score_strength_category'] = self._classify_strength(brew_data['final_tds_percent'])
            result['score_extraction_category'] = self._classify_extraction(result['final_extraction_yield_percent'])
            result['score_brewing_zone'] = self._generate_brewing_zone(
                result['score_extraction_category'], 
                result['score_strength_category']
            )
            
            # Composite score (handle missing overall rating)
            overall_rating = brew_data.get('score_overall_rating')
            if pd.isna(overall_rating):
                overall_rating = None
            result['score_brew'] = self._calculate_brew_score(overall_rating, result['score_brewing_zone'])

            # Unified brewing score (brew-ratio-aware distance from optimal)
            result['unified_brewing_score'] = self._calculate_unified_brewing_score(
                extraction_yield=result['final_extraction_yield_percent'],
                tds_percent=brew_data['final_tds_percent'],
                coffee_grams_per_liter=result['coffee_grams_per_liter']
            )

            return result
            
        except Exception as e:
            self.logger.error(f"Error processing single brew: {e}")
            raise
    
    def _calculate_bean_statistics(self, df: pd.DataFrame, current_index: int) -> Dict[str, Any]:
        """Calculate statistical analysis per bean for a specific row"""
        try:
            current_row = df.iloc[current_index]
            bean_name = current_row['bean_name']
            
            # Filter all rows with same bean name
            bean_mask = df['bean_name'] == bean_name
            bean_df = df[bean_mask].copy()
            
            # Bean usage count (including current brew)
            bean_usage_count = len(bean_df)
            
            # Average rating for this bean (including current brew)
            valid_ratings = bean_df['score_overall_rating'].dropna()
            avg_rating = round(valid_ratings.mean(), 1) if len(valid_ratings) > 0 else None
            
            # Calculate improvement vs last brew
            improvement_vs_last = None
            if bean_usage_count > 1 and pd.notna(current_row['score_overall_rating']):
                # Sort by brew_date to find previous brew
                bean_df_sorted = bean_df.sort_values('brew_date')
                current_row_in_sorted = bean_df_sorted[bean_df_sorted.index == current_index]
                
                if len(current_row_in_sorted) > 0:
                    current_position = bean_df_sorted.index.get_loc(current_index)
                    if current_position > 0:
                        previous_rating = bean_df_sorted.iloc[current_position - 1]['score_overall_rating']
                        current_rating = current_row['score_overall_rating']
                        if pd.notna(previous_rating) and pd.notna(current_rating):
                            improvement_vs_last = round(current_rating - previous_rating, 1)
            
            return {
                'bean_usage_count': bean_usage_count,
                'score_avg_rating_this_bean': avg_rating,
                'score_improvement_vs_last': improvement_vs_last
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating bean statistics: {e}")
            return {
                'bean_usage_count': None,
                'score_avg_rating_this_bean': None,
                'score_improvement_vs_last': None
            }
    
    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process entire dataframe and add calculated fields"""
        try:
            if df.empty:
                self.logger.warning("Empty dataframe provided")
                return df
            
            # Create copy to avoid modifying original
            result_df = df.copy()
            
            # Normalize date columns to standard format (YYYY-MM-DD)
            for date_col in ['brew_date', 'bean_purchase_date']:
                if date_col in result_df.columns:
                    # Parse and normalize each date
                    for idx in result_df.index:
                        if pd.notna(result_df.loc[idx, date_col]):
                            try:
                                parsed_date = self._parse_date(result_df.loc[idx, date_col])
                                result_df.loc[idx, date_col] = self._format_date_to_standard(parsed_date)
                            except Exception as e:
                                self.logger.warning(f"Could not parse {date_col} at row {idx}: {e}")
                                result_df.loc[idx, date_col] = None
                    
                    # Convert to datetime for calculations
                    result_df[date_col] = pd.to_datetime(result_df[date_col], errors='coerce')
            
            # Initialize new columns
            new_columns = [
                'beans_days_since_roast', 'brew_ratio_to_1', 'final_extraction_yield_percent',
                'coffee_grams_per_liter', 'score_strength_category', 'score_extraction_category',
                'score_brewing_zone', 'score_brew', 'unified_brewing_score', 'bean_usage_count',
                'score_avg_rating_this_bean', 'score_improvement_vs_last'
            ]
            
            for col in new_columns:
                result_df[col] = None
            
            # Process each row (skip if already processed)
            successful_rows = 0
            skipped_rows = 0
            processed_rows = 0
            
            for idx in result_df.index:
                try:
                    row_data = result_df.loc[idx].to_dict()
                    
                    # Check if row needs processing
                    if not self._needs_processing(row_data):
                        skipped_rows += 1
                        successful_rows += 1
                        continue
                    
                    # Process single brew calculations
                    processed_row = self.process_single_brew(row_data)
                    
                    # Update row with calculated values
                    for col in ['beans_days_since_roast', 'brew_ratio_to_1', 'final_extraction_yield_percent',
                               'coffee_grams_per_liter', 'score_strength_category', 'score_extraction_category',
                               'score_brewing_zone', 'score_brew', 'unified_brewing_score']:
                        result_df.loc[idx, col] = processed_row[col]
                    
                    # Update dates to standardized format
                    if 'brew_date' in processed_row:
                        result_df.loc[idx, 'brew_date'] = processed_row['brew_date']
                    if 'bean_purchase_date' in processed_row:
                        result_df.loc[idx, 'bean_purchase_date'] = processed_row['bean_purchase_date']
                    
                    processed_rows += 1
                    successful_rows += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing row {idx}: {e}")
                    # Continue processing other rows
                    continue
            
            # Calculate bean statistics for all rows (requires full dataset)
            for idx in result_df.index:
                try:
                    bean_stats = self._calculate_bean_statistics(result_df, idx)
                    for col, value in bean_stats.items():
                        result_df.loc[idx, col] = value
                except Exception as e:
                    self.logger.error(f"Error calculating bean statistics for row {idx}: {e}")
                    continue
            
            self.logger.info(f"Successfully processed {successful_rows}/{len(df)} rows")
            return result_df
            
        except Exception as e:
            self.logger.error(f"Error processing dataframe: {e}")
            raise
    
    def _needs_processing(self, row_data: Dict[str, Any]) -> bool:
        """Check if a row needs processing or re-processing"""
        # List of calculated fields that should be present after processing
        calculated_fields = [
            'beans_days_since_roast', 'brew_ratio_to_1', 'final_extraction_yield_percent',
            'coffee_grams_per_liter', 'score_strength_category', 'score_extraction_category',
            'score_brewing_zone', 'score_brew', 'unified_brewing_score', 'bean_usage_count',
            'score_avg_rating_this_bean', 'score_improvement_vs_last'
        ]
        
        # Check if any calculated fields are missing or null
        for field in calculated_fields:
            if field not in row_data or pd.isna(row_data[field]):
                return True
        
        # Check if dates need standardization (not in YYYY-MM-DD format)
        for date_field in ['brew_date', 'bean_purchase_date']:
            if date_field in row_data and pd.notna(row_data[date_field]):
                date_str = str(row_data[date_field])
                # If it contains '/' it's in legacy format and needs processing
                if '/' in date_str:
                    return True
                # If it's not in YYYY-MM-DD format, it needs processing
                try:
                    datetime.strptime(date_str.split()[0], '%Y-%m-%d')  # Handle datetime strings
                except ValueError:
                    return True
        
        # Check if data seems to be from an older calculation version
        # This is a simple heuristic - in a real system you might store version info per row
        try:
            # Recalculate one field to see if it matches
            expected_ratio = round(row_data.get('water_volume_ml', 0) / row_data.get('coffee_dose_grams', 1), 1)
            current_ratio = row_data.get('brew_ratio_to_1')
            if abs(expected_ratio - current_ratio) > 0.1:  # Allow small floating point differences
                return True
        except (ZeroDivisionError, TypeError):
            return True
        
        return False
    
    def get_calculation_metadata(self) -> Dict[str, Any]:
        """Return metadata about calculation configuration"""
        return {
            'calculation_version': self.config.calculation_version,
            'strength_thresholds': self.config.strength_thresholds,
            'extraction_thresholds': self.config.extraction_thresholds,
            'zone_bonuses': self.config.zone_bonuses,
            'validation_ranges': self.config.validation_ranges,
            'required_fields': self.REQUIRED_FIELDS
        }


class SelectiveDataProcessor:
    """Enhanced processor with hash-based change detection for selective processing"""
    
    # Default raw data fields for hash calculation
    DEFAULT_RAW_FIELDS = [
        'coffee_dose_grams', 'water_volume_ml', 'final_tds_percent', 
        'final_brew_mass_grams', 'bean_name', 'brew_date', 'bean_purchase_date',
        'score_overall_rating'
    ]
    
    # Metadata columns for tracking processing state
    METADATA_COLUMNS = [
        'raw_data_hash', 'calculation_version', 'last_processed_timestamp'
    ]
    
    # Calculated fields for validation
    CALCULATED_FIELDS = [
        'beans_days_since_roast', 'brew_ratio_to_1', 'final_extraction_yield_percent',
        'coffee_grams_per_liter', 'score_strength_category', 'score_extraction_category',
        'score_brewing_zone', 'score_brew', 'unified_brewing_score', 'bean_usage_count',
        'score_avg_rating_this_bean', 'score_improvement_vs_last'
    ]
    
    def __init__(self, config: Dict[str, Any] = None, target_version: str = "1.2.0"):
        """Initialize SelectiveDataProcessor with optional configuration"""
        self.config = config or {}
        self.target_version = target_version
        self.raw_fields = self.config.get('raw_fields', self.DEFAULT_RAW_FIELDS)
        self.validation_tolerances = self.config.get('validation_tolerances', {
            'brew_ratio_to_1': 0.1,
            'final_extraction_yield_percent': 0.1
        })
        self.hash_algorithm = self.config.get('hash_algorithm', 'md5')
        
        # Initialize base processor for actual calculations
        self.base_processor = CoffeeDataProcessor(config)
        self.logger = self._setup_logging()
        
        # Statistics tracking
        self._reset_statistics()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(f"{__name__}.SelectiveProcessor")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _reset_statistics(self):
        """Reset processing statistics"""
        self.stats = {
            'entries_processed': 0,
            'total_entries': 0,
            'trigger_breakdown': defaultdict(int),
            'processing_time_seconds': 0.0,
            'version_applied': self.target_version,
            'efficiency_ratio': 0.0,
            'hash_mismatches': [],
            'validation_failures': [],
            'processing_decisions': [],
            'processed_brew_ids': []
        }
    
    def calculate_raw_data_hash(self, row: pd.Series) -> str:
        """Calculate MD5 hash of concatenated raw input fields"""
        try:
            # Extract raw field values in defined order
            hash_components = []
            for field in self.raw_fields:
                value = row.get(field, '')
                
                # Handle different data types consistently
                if pd.isna(value) or value is None:
                    hash_components.append('')
                elif isinstance(value, (int, float)):
                    # Round floating-point values to 6 decimal places for consistency
                    if isinstance(value, float):
                        hash_components.append(f"{value:.6f}")
                    else:
                        hash_components.append(str(value))
                elif isinstance(value, (datetime, date)):
                    # Convert dates to ISO format string
                    hash_components.append(value.strftime('%Y-%m-%d') if hasattr(value, 'strftime') else str(value))
                else:
                    # Convert everything else to string
                    hash_components.append(str(value))
            
            # Concatenate and hash
            concatenated = '|'.join(hash_components)
            if self.hash_algorithm.lower() == 'md5':
                return hashlib.md5(concatenated.encode('utf-8')).hexdigest()
            else:
                raise ValueError(f"Unsupported hash algorithm: {self.hash_algorithm}")
                
        except Exception as e:
            self.logger.error(f"Error calculating hash for row: {e}")
            return ""
    
    def _add_metadata_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add metadata columns if they don't exist"""
        df_copy = df.copy()
        
        for col in self.METADATA_COLUMNS:
            if col not in df_copy.columns:
                df_copy[col] = None
                
        return df_copy
    
    def _validate_calculated_field_consistency(self, row: pd.Series) -> List[str]:
        """Validate calculated fields against raw data for consistency"""
        inconsistencies = []
        
        try:
            # Validate brew_ratio_to_1
            if (pd.notna(row.get('brew_ratio_to_1')) and 
                pd.notna(row.get('water_volume_ml')) and 
                pd.notna(row.get('coffee_dose_grams'))):
                
                expected_ratio = row['water_volume_ml'] / row['coffee_dose_grams']
                actual_ratio = row['brew_ratio_to_1']
                tolerance = self.validation_tolerances.get('brew_ratio_to_1', 0.1)
                
                if abs(expected_ratio - actual_ratio) > tolerance:
                    inconsistencies.append(f"brew_ratio_to_1 mismatch: expected {expected_ratio:.2f}, got {actual_ratio}")
            
            # Validate final_extraction_yield_percent
            if (pd.notna(row.get('final_extraction_yield_percent')) and 
                pd.notna(row.get('final_brew_mass_grams')) and
                pd.notna(row.get('final_tds_percent')) and
                pd.notna(row.get('coffee_dose_grams'))):
                
                expected_yield = (row['final_brew_mass_grams'] * row['final_tds_percent']) / row['coffee_dose_grams']
                actual_yield = row['final_extraction_yield_percent']
                tolerance = self.validation_tolerances.get('final_extraction_yield_percent', 0.1)
                
                if abs(expected_yield - actual_yield) > tolerance:
                    inconsistencies.append(f"final_extraction_yield_percent mismatch: expected {expected_yield:.2f}, got {actual_yield}")
                    
        except Exception as e:
            inconsistencies.append(f"Validation error: {e}")
            
        return inconsistencies
    
    def identify_entries_needing_processing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identify entries that need processing based on multiple criteria"""
        start_time = datetime.now()
        
        # Add metadata columns if missing
        df_with_metadata = self._add_metadata_columns(df)
        
        # Calculate current hash for all entries
        df_with_metadata['current_hash'] = df_with_metadata.apply(self.calculate_raw_data_hash, axis=1)
        
        # Initialize processing flags
        df_with_metadata['needs_processing'] = False
        df_with_metadata['processing_reasons'] = ''
        
        processing_decisions = []
        
        for idx in df_with_metadata.index:
            row = df_with_metadata.loc[idx]
            reasons = []
            
            # Check 1: Missing calculated fields
            missing_fields = []
            for field in self.CALCULATED_FIELDS:
                if pd.isna(row.get(field)):
                    missing_fields.append(field)
            
            if missing_fields:
                reasons.append(f"missing_fields: {', '.join(missing_fields[:3])}{'...' if len(missing_fields) > 3 else ''}")
                self.stats['trigger_breakdown']['missing_calculated_fields'] += 1
            
            # Check 2: Hash mismatch
            current_hash = row.get('current_hash', '')
            stored_hash = row.get('raw_data_hash', '')
            
            if current_hash != stored_hash and current_hash != '':
                reasons.append("hash_mismatch")
                self.stats['trigger_breakdown']['hash_mismatch'] += 1
                self.stats['hash_mismatches'].append({
                    'index': idx,
                    'old_hash': stored_hash,
                    'new_hash': current_hash
                })
            
            # Check 3: Missing hash
            if pd.isna(stored_hash) or stored_hash == '':
                reasons.append("missing_hash")
                self.stats['trigger_breakdown']['missing_hash'] += 1
            
            # Check 4: Version mismatch
            stored_version = row.get('calculation_version', '')
            if stored_version != self.target_version:
                reasons.append(f"version_mismatch: {stored_version} -> {self.target_version}")
                self.stats['trigger_breakdown']['version_mismatch'] += 1
            
            # Check 5: Missing version
            if pd.isna(stored_version) or stored_version == '':
                reasons.append("missing_version")
                self.stats['trigger_breakdown']['missing_version'] += 1
            
            # Check 6: Validation inconsistencies
            if not missing_fields:  # Only validate if calculated fields exist
                inconsistencies = self._validate_calculated_field_consistency(row)
                if inconsistencies:
                    reasons.append("validation_inconsistency")
                    self.stats['trigger_breakdown']['validation_inconsistency'] += 1
                    self.stats['validation_failures'].extend([
                        {'index': idx, 'issue': issue} for issue in inconsistencies
                    ])
            
            # Set processing flag and reasons
            if reasons:
                df_with_metadata.loc[idx, 'needs_processing'] = True
                df_with_metadata.loc[idx, 'processing_reasons'] = '; '.join(reasons)
                
                processing_decisions.append({
                    'index': idx,
                    'reasons': reasons,
                    'current_hash': current_hash,
                    'stored_hash': stored_hash
                })
        
        # Update statistics
        self.stats['processing_decisions'] = processing_decisions
        processing_time = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"Entry identification completed in {processing_time:.3f}s")
        
        return df_with_metadata
    
    def process_selective_update(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Process only entries that need updating"""
        start_time = datetime.now()
        self._reset_statistics()
        self.stats['total_entries'] = len(df)
        
        # Identify entries needing processing
        self.logger.info("Identifying entries needing processing...")
        df_analyzed = self.identify_entries_needing_processing(df)
        
        # Filter entries that need processing
        entries_to_process = df_analyzed[df_analyzed['needs_processing'] == True]
        self.stats['entries_processed'] = len(entries_to_process)
        
        if len(entries_to_process) == 0:
            self.logger.info("No entries require processing")
            # Clean up temporary columns
            result_df = df_analyzed.drop(columns=['current_hash', 'needs_processing', 'processing_reasons'], errors='ignore')
            self.stats['processing_time_seconds'] = (datetime.now() - start_time).total_seconds()
            self.stats['efficiency_ratio'] = 1.0  # Perfect efficiency - no work needed
            return result_df, self.get_processing_statistics()
        
        self.logger.info(f"Processing {len(entries_to_process)} out of {len(df)} entries")
        
        # Process entries in order of brew_date for statistical calculations
        if 'brew_date' in entries_to_process.columns:
            entries_to_process = entries_to_process.sort_values('brew_date')
        
        # Create result dataframe
        result_df = df_analyzed.copy()
        
        # Process each entry that needs updating
        successful_updates = 0
        for idx in entries_to_process.index:
            try:
                row_data = result_df.loc[idx].to_dict()
                
                # Use base processor for actual calculations
                processed_row = self.base_processor.process_single_brew(row_data)
                
                # Update calculated fields
                for field in self.CALCULATED_FIELDS:
                    if field in processed_row:
                        result_df.loc[idx, field] = processed_row[field]
                
                # Update dates to standardized format
                for date_field in ['brew_date', 'bean_purchase_date']:
                    if date_field in processed_row and processed_row[date_field] is not None:
                        result_df.loc[idx, date_field] = processed_row[date_field]
                
                # Track processed brew ID
                if 'brew_id' in row_data and row_data['brew_id'] is not None:
                    self.stats['processed_brew_ids'].append(row_data['brew_id'])
                    self.logger.debug(f"Added brew_id {row_data['brew_id']} to processed list")
                
                successful_updates += 1
                
            except Exception as e:
                self.logger.error(f"Failed to process entry at index {idx}: {e}")
                continue
        
        # Recalculate bean statistics for all entries (since they depend on the full dataset)
        self.logger.info("Recalculating bean statistics...")
        for idx in result_df.index:
            try:
                bean_stats = self.base_processor._calculate_bean_statistics(result_df, idx)
                for col, value in bean_stats.items():
                    result_df.loc[idx, col] = value
            except Exception as e:
                self.logger.error(f"Error calculating bean statistics for row {idx}: {e}")
                continue
        
        # Update metadata for successfully processed entries
        result_df = self.update_processing_metadata(result_df)
        
        # Clean up temporary columns
        result_df = result_df.drop(columns=['current_hash', 'needs_processing', 'processing_reasons'], errors='ignore')
        
        # Update final statistics
        self.stats['processing_time_seconds'] = (datetime.now() - start_time).total_seconds()
        if self.stats['total_entries'] > 0:
            self.stats['efficiency_ratio'] = 1.0 - (self.stats['entries_processed'] / self.stats['total_entries'])
        
        self.logger.info(f"Successfully processed {successful_updates} entries in {self.stats['processing_time_seconds']:.3f}s")
        self.logger.info(f"Efficiency: {self.stats['efficiency_ratio']:.1%} computational savings")
        
        return result_df, self.get_processing_statistics()
    
    def update_processing_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Update metadata fields for processed entries"""
        result_df = df.copy()
        current_timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Update metadata for entries that were processed
        processed_mask = result_df.get('needs_processing', False) == True
        
        for idx in result_df[processed_mask].index:
            # Update hash with current calculated value
            result_df.loc[idx, 'raw_data_hash'] = self.calculate_raw_data_hash(result_df.loc[idx])
            result_df.loc[idx, 'calculation_version'] = self.target_version
            result_df.loc[idx, 'last_processed_timestamp'] = current_timestamp
        
        return result_df
    
    def validate_calculated_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate calculated fields across the dataframe"""
        validation_results = []
        
        for idx in df.index:
            row = df.loc[idx]
            inconsistencies = self._validate_calculated_field_consistency(row)
            
            if inconsistencies:
                validation_results.append({
                    'index': idx,
                    'inconsistencies': inconsistencies
                })
        
        if validation_results:
            self.logger.warning(f"Found validation issues in {len(validation_results)} entries")
            for result in validation_results[:5]:  # Log first 5 issues
                self.logger.warning(f"Row {result['index']}: {result['inconsistencies']}")
        
        return df
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Return comprehensive processing statistics"""
        return {
            'entries_processed': self.stats['entries_processed'],
            'total_entries': self.stats['total_entries'],
            'trigger_breakdown': dict(self.stats['trigger_breakdown']),
            'processing_time_seconds': self.stats['processing_time_seconds'],
            'version_applied': self.stats['version_applied'],
            'efficiency_ratio': self.stats['efficiency_ratio'],
            'hash_mismatches_count': len(self.stats['hash_mismatches']),
            'validation_failures_count': len(self.stats['validation_failures']),
            'processing_decisions_count': len(self.stats['processing_decisions']),
            'processed_brew_ids': self.stats['processed_brew_ids']
        }
    
    def get_hash_debugging_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return detailed hash debugging information"""
        debug_info = {
            'hash_mismatches': self.stats['hash_mismatches'][:10],  # First 10 mismatches
            'validation_failures': self.stats['validation_failures'][:10],  # First 10 failures
            'raw_fields_used': self.raw_fields,
            'hash_algorithm': self.hash_algorithm,
            'sample_hash_calculation': {}
        }
        
        # Add sample hash calculation for first row
        if len(df) > 0:
            first_row = df.iloc[0]
            debug_info['sample_hash_calculation'] = {
                'raw_values': {field: first_row.get(field, 'N/A') for field in self.raw_fields},
                'calculated_hash': self.calculate_raw_data_hash(first_row)
            }
        
        return debug_info

def main():
    """Process coffee data from CSV file"""
    try:
        # Create processor
        processor = CoffeeDataProcessor()
        
        # Load and process the actual data
        print("Loading coffee data...")
        df = pd.read_csv("data/cups_of_coffee.csv")
        print(f"Loaded {len(df)} rows")
        
        # Process the dataframe
        print("Processing coffee data...")
        processed_df = processor.process_dataframe(df)
        
        # Save processed data back to the same file
        import csv
        processed_df.to_csv("data/cups_of_coffee.csv", index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"✓ Processed {len(processed_df)} rows and saved to data/cups_of_coffee.csv")
        
        # Show sample of calculated fields
        calc_fields = ['beans_days_since_roast', 'brew_ratio_to_1', 'final_extraction_yield_percent',
                      'score_strength_category', 'score_extraction_category', 'score_brewing_zone']
        print("\nCalculated fields (first row):")
        for field in calc_fields:
            if field in processed_df.columns:
                value = processed_df[field].iloc[0]
                print(f"  {field}: {value}")
        
    except FileNotFoundError:
        print("Error: data/cups_of_coffee.csv not found")
    except Exception as e:
        print(f"Processing failed: {e}")

if __name__ == "__main__":
    main()