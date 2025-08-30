"""
Form Handling Service

Handles form data processing, validation, and formatting for coffee brewing forms.
Extracted from main application to improve separation of concerns.
"""

import pandas as pd
from typing import Dict, List, Optional, Any, Union
from datetime import date
import logging


class FormHandlingService:
    """Service for handling form data processing and validation"""
    
    def __init__(self):
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(f"{__name__}.FormHandlingService")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def generate_grind_dial_options(self) -> List[float]:
        """
        Generate grind size options matching Fellow Ode Gen 2 dial (1-11 with .1, .2 intermediates)
        
        Returns:
            List of grind size options
        """
        options = []
        for i in range(1, 12):  # 1 to 11
            options.append(float(i))       # e.g., 5.0
            if i < 11:  # Don't add intermediates after 11
                options.append(i + 0.1)    # e.g., 5.1
                options.append(i + 0.2)    # e.g., 5.2
        return options
    
    def format_grind_option_display(self, options: List[float]) -> List[str]:
        """
        Format grind options for display (show integers without decimal, decimals with one place)
        
        Args:
            options: List of grind size options
            
        Returns:
            List of formatted display strings
        """
        formatted_options = []
        for opt in options:
            if opt == int(opt):
                formatted_options.append(f"{int(opt)}")
            else:
                formatted_options.append(f"{opt:.1f}")
        return formatted_options
    
    def get_grind_size_index(self, options: List[float], current_value: Optional[float]) -> int:
        """
        Get the index of current grind size value in options list
        
        Args:
            options: List of grind size options
            current_value: Current grind size value
            
        Returns:
            Index in options list, 0 if not found
        """
        if current_value is not None:
            try:
                return options.index(float(current_value))
            except (ValueError, TypeError):
                pass
        return 0
    
    def prepare_bean_form_data(self, selected_bean_data: Optional[Dict[str, Any]], 
                             current_bean_data: Optional[Dict[str, Any]], 
                             context: str = "add") -> Dict[str, Any]:
        """
        Prepare bean data for form population based on context and data sources
        
        Args:
            selected_bean_data: Data from bean selection dropdown
            current_bean_data: Current bean data (for edit mode)
            context: "add" or "edit" context
            
        Returns:
            Dictionary of bean data for form population
        """
        # Determine data source priority:
        # 1. Selected bean data (from dropdown)
        # 2. Current bean data (for edit mode)
        # 3. Empty defaults (for new entries)
        if selected_bean_data:
            return selected_bean_data
        elif current_bean_data:
            return current_bean_data
        else:
            return {}
    
    def extract_bean_form_values(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and clean bean form values
        
        Args:
            form_data: Raw form data from UI
            
        Returns:
            Cleaned bean data dictionary
        """
        return {
            'bean_name': form_data.get('bean_name', '').strip() or None,
            'bean_origin_country': form_data.get('bean_origin_country', '').strip() or None,
            'bean_origin_region': form_data.get('bean_origin_region', '').strip() or None,
            'bean_variety': form_data.get('bean_variety', '').strip() or None,
            'bean_process_method': form_data.get('bean_process_method', '') or None,
            'bean_roast_date': form_data.get('bean_roast_date'),
            'bean_roast_level': form_data.get('bean_roast_level', '') or None,
            'bean_notes': form_data.get('bean_notes', '').strip() or None
        }
    
    def calculate_final_brew_mass(self, mug_weight_grams: Optional[float], 
                                final_combined_weight_grams: Optional[float]) -> Optional[float]:
        """
        Calculate final brew mass from mug weight and combined weight
        
        Args:
            mug_weight_grams: Weight of empty mug
            final_combined_weight_grams: Total weight (mug + coffee)
            
        Returns:
            Final brew mass or None if cannot calculate
        """
        if mug_weight_grams is not None and final_combined_weight_grams is not None:
            return final_combined_weight_grams - mug_weight_grams
        return None
    
    def prepare_brew_record(self, form_data: Dict[str, Any], brew_id: int, 
                          estimated_bag_size_grams: Optional[float] = None) -> Dict[str, Any]:
        """
        Prepare a complete brew record from form data
        
        Args:
            form_data: Form data from UI
            brew_id: Brew ID for the record
            estimated_bag_size_grams: Optional bag size for new beans
            
        Returns:
            Complete brew record dictionary
        """
        # Calculate final_brew_mass_grams from mug weight and combined weight
        final_brew_mass_grams = self.calculate_final_brew_mass(
            form_data.get('mug_weight_grams'),
            form_data.get('final_combined_weight_grams')
        )
        
        # Collect only input fields (no calculated or metadata fields)
        new_record = {
            'brew_id': brew_id,
            'brew_date': form_data.get('brew_date'),
            'bean_name': form_data.get('bean_name') or None,
            'bean_origin_country': form_data.get('bean_origin_country') or None,
            'bean_origin_region': form_data.get('bean_origin_region') or None,
            'bean_variety': form_data.get('bean_variety') or None,
            'bean_process_method': form_data.get('bean_process_method') or None,
            'bean_roast_date': form_data.get('bean_roast_date'),
            'bean_roast_level': form_data.get('bean_roast_level') or None,
            'bean_notes': form_data.get('bean_notes') or None,
            'grind_size': form_data.get('grind_size'),
            'grind_model': form_data.get('grind_model') or None,
            'brew_method': form_data.get('brew_method') or None,
            'brew_device': form_data.get('brew_device') or None,
            'coffee_dose_grams': form_data.get('coffee_dose_grams'),
            'water_volume_ml': form_data.get('water_volume_ml'),
            'water_temp_degC': form_data.get('water_temp_degC'),
            'brew_bloom_time_s': form_data.get('brew_bloom_time_s'),
            'brew_bloom_water_ml': form_data.get('brew_bloom_water_ml'),
            'brew_pulse_target_water_ml': form_data.get('brew_pulse_target_water_ml'),
            'brew_total_time_s': form_data.get('brew_total_time_s'),
            'agitation_method': form_data.get('agitation_method') or None,
            'pour_technique': form_data.get('pour_technique') or None,
            'final_tds_percent': form_data.get('final_tds_percent'),
            'final_brew_mass_grams': final_brew_mass_grams,
            'score_overall_rating': form_data.get('score_overall_rating'),
            'score_notes': form_data.get('score_notes') or None,
            'score_flavor_profile_category': form_data.get('score_flavor_profile_category') or None,
            'score_complexity': form_data.get('score_complexity'),
            'score_bitterness': form_data.get('score_bitterness'),
            'score_mouthfeel': form_data.get('score_mouthfeel'),
            'scoring_system_version': form_data.get('scoring_system_version', '3-factor-v1'),
            # Add mug tracking fields
            'mug_weight_grams': form_data.get('mug_weight_grams'),
            'final_combined_weight_grams': form_data.get('final_combined_weight_grams'),
            # Add inventory and archive fields
            'estimated_bag_size_grams': estimated_bag_size_grams if estimated_bag_size_grams and estimated_bag_size_grams > 0 else None,
            'archive_status': 'active'  # All new beans start as active
        }
        
        return new_record
    
    def update_brew_record(self, df: pd.DataFrame, brew_id: int, 
                          form_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Update an existing brew record in the DataFrame
        
        Args:
            df: DataFrame containing brew records
            brew_id: ID of record to update
            form_data: Updated form data
            
        Returns:
            Updated DataFrame
        """
        idx = df[df['brew_id'] == brew_id].index[0]
        
        # Calculate final_brew_mass_grams from mug weight and combined weight
        calculated_final_brew_mass_grams = self.calculate_final_brew_mass(
            form_data.get('mug_weight_grams'),
            form_data.get('final_combined_weight_grams')
        )
        
        # Update only input fields (preserve calculated fields)
        df.loc[idx, 'brew_date'] = form_data.get('brew_date')
        df.loc[idx, 'bean_name'] = form_data.get('bean_name') or None
        df.loc[idx, 'bean_origin_country'] = form_data.get('bean_origin_country') or None
        df.loc[idx, 'bean_origin_region'] = form_data.get('bean_origin_region') or None
        df.loc[idx, 'bean_variety'] = form_data.get('bean_variety') or None
        df.loc[idx, 'bean_process_method'] = form_data.get('bean_process_method') or None
        df.loc[idx, 'bean_roast_level'] = form_data.get('bean_roast_level') or None
        df.loc[idx, 'bean_notes'] = form_data.get('bean_notes') or None
        df.loc[idx, 'grind_size'] = form_data.get('grind_size')
        df.loc[idx, 'grind_model'] = form_data.get('grind_model') or None
        df.loc[idx, 'brew_method'] = form_data.get('brew_method') or None
        df.loc[idx, 'brew_device'] = form_data.get('brew_device') or None
        df.loc[idx, 'coffee_dose_grams'] = form_data.get('coffee_dose_grams')
        df.loc[idx, 'water_volume_ml'] = form_data.get('water_volume_ml')
        df.loc[idx, 'water_temp_degC'] = form_data.get('water_temp_degC')
        df.loc[idx, 'brew_total_time_s'] = form_data.get('brew_total_time_s')
        df.loc[idx, 'final_tds_percent'] = form_data.get('final_tds_percent')
        df.loc[idx, 'final_brew_mass_grams'] = calculated_final_brew_mass_grams
        df.loc[idx, 'score_overall_rating'] = form_data.get('score_overall_rating')
        df.loc[idx, 'score_notes'] = form_data.get('score_notes') or None
        df.loc[idx, 'score_flavor_profile_category'] = form_data.get('score_flavor_profile_category') or None
        df.loc[idx, 'score_complexity'] = form_data.get('score_complexity')
        df.loc[idx, 'score_bitterness'] = form_data.get('score_bitterness')
        df.loc[idx, 'score_mouthfeel'] = form_data.get('score_mouthfeel')
        df.loc[idx, 'scoring_system_version'] = form_data.get('scoring_system_version', '3-factor-v1')
        # Update mug weight fields
        df.loc[idx, 'mug_weight_grams'] = form_data.get('mug_weight_grams')
        df.loc[idx, 'final_combined_weight_grams'] = form_data.get('final_combined_weight_grams')
        
        return df
    
    def get_process_methods(self) -> List[str]:
        """Get list of available process methods"""
        return ["", "Washed", "Natural", "Honey", "Semi-Washed", "Anaerobic", "Other"]
    
    def get_roast_levels(self) -> List[str]:
        """Get list of available roast levels"""
        return ["", "Light", "Light-Medium", "Medium", "Medium-Dark", "Dark"]
    
    def get_brew_devices(self) -> List[str]:
        """Get list of available brew devices"""
        return ["", "V60 ceramic", "V60", "Chemex", "Aeropress", "French Press", "Espresso", "Hoffman top up", "Other"]
    
    def get_agitation_methods(self) -> List[str]:
        """Get list of available agitation methods"""
        return ["", "None", "Stir", "Swirl", "Shake", "Gentle stir"]
    
    def get_pour_techniques(self) -> List[str]:
        """Get list of available pour techniques"""
        return ["", "Spiral", "Center pour", "Concentric circles", "Pulse pour", "Continuous"]
    
    def get_flavor_profiles(self) -> List[str]:
        """Get list of available flavor profiles"""
        return ["", "Bright/Acidic", "Balanced", "Rich/Full", "Sweet", "Bitter", "Fruity", "Nutty", "Chocolatey"]
    
    def validate_form_data(self, form_data: Dict[str, Any]) -> List[str]:
        """
        Validate form data and return list of validation errors
        
        Args:
            form_data: Form data to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Required fields validation
        if not form_data.get('bean_name', '').strip():
            errors.append("Bean name is required")
        
        if not form_data.get('grind_size'):
            errors.append("Grind size is required")
        
        # Numeric field validation
        numeric_fields = [
            ('coffee_dose_grams', 'Coffee dose'),
            ('water_volume_ml', 'Water volume'),
            ('score_overall_rating', 'Overall rating')
        ]
        
        for field, label in numeric_fields:
            value = form_data.get(field)
            if value is not None and value < 0:
                errors.append(f"{label} cannot be negative")
        
        # TDS validation
        tds = form_data.get('final_tds_percent')
        if tds is not None and (tds < 0 or tds > 5):
            errors.append("TDS % should be between 0 and 5")
        
        # Rating validation
        rating = form_data.get('score_overall_rating')
        if rating is not None and (rating < 0 or rating > 5):
            errors.append("Rating should be between 0 and 5")
        
        return errors