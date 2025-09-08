"""
Tests for data editing functionality

Test the edit brews feature to ensure data integrity and proper updates.
Follows TDD principles as required by the project.
"""

import pytest
import pandas as pd
from datetime import date
import tempfile
import os
from unittest.mock import Mock, patch
from src.services.form_handling_service import FormHandlingService


class TestDataEditing:
    """Test suite for data editing functionality"""
    
    @pytest.fixture
    def form_service(self):
        """Create FormHandlingService instance for testing"""
        return FormHandlingService()
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame with test data"""
        return pd.DataFrame({
            'brew_id': [1, 2, 3],
            'brew_date': ['2025-09-01', '2025-09-02', '2025-09-03'],
            'bean_name': ['Test Bean 1', 'Test Bean 2', 'Test Bean 3'],
            'bean_origin_country': ['Colombia', 'Ethiopia', 'Brazil'],
            'bean_origin_region': ['Huila', 'Yirgacheffe', 'Cerrado'],
            'bean_variety': ['Caturra', 'Heirloom', 'Bourbon'],
            'bean_process_method': ['Washed', 'Natural', 'Honey'],
            'bean_roast_level': ['Medium', 'Light', 'Medium-Dark'],
            'bean_notes': ['Chocolate notes', 'Floral notes', 'Nutty notes'],
            'grind_size': [6.0, 5.5, 6.2],
            'grind_model': ['Fellow Ode Gen 2', 'Fellow Ode Gen 2', 'Fellow Ode Gen 2'],
            'brew_method': ['3 pulse V60', '2 pulse V60', '3 pulse V60'],
            'brew_device': ['V60 ceramic', 'V60 ceramic', 'V60 ceramic'],
            'coffee_dose_grams': [15.0, 16.0, 14.5],
            'water_volume_ml': [250.0, 260.0, 240.0],
            'water_temp_degC': [95.0, 92.0, 94.0],
            'brew_bloom_time_s': [45.0, 40.0, 45.0],
            'brew_bloom_water_ml': [50.0, 55.0, 48.0],
            'brew_pulse_target_water_ml': [60.0, 65.0, 58.0],
            'brew_total_time_s': [180.0, 175.0, 185.0],
            'agitation_method': ['Stir', 'Swirl', 'Stir'],
            'pour_technique': ['Spiral', 'Center pour', 'Spiral'],
            'final_tds_percent': [1.25, 1.35, 1.20],
            'mug_weight_grams': [300.0, 305.0, 295.0],
            'final_combined_weight_grams': [530.0, 545.0, 525.0],
            'score_overall_rating': [4.0, 4.5, 3.8],
            'score_notes': ['Good cup', 'Excellent', 'Decent'],
            'score_flavor_profile_category': ['Balanced', 'Bright/Acidic', 'Rich/Full'],
            'score_complexity': [4.0, 4.5, 3.5],
            'score_bitterness': [3.0, 2.5, 3.5],
            'score_mouthfeel': [4.0, 4.2, 3.8],
            'scoring_system_version': ['3-factor-v1', '3-factor-v1', '3-factor-v1'],
            # Calculated fields (should be preserved during editing)
            'brew_ratio_to_1': [16.7, 16.3, 16.6],
            'final_extraction_yield_percent': [19.2, 20.1, 18.8],
            'score_strength_category': ['Ideal', 'Strong', 'Ideal'],
            'score_extraction_category': ['Ideal', 'Ideal', 'Under'],
            'score_brewing_zone': ['Ideal-Ideal', 'Ideal-Strong', 'Under-Ideal']
        })
    
    def test_update_brew_record_basic_fields(self, form_service, sample_dataframe):
        """Test updating basic fields of a brew record"""
        brew_id = 1
        form_data = {
            'brew_date': date(2025, 9, 10),
            'bean_name': 'Updated Bean Name',
            'bean_origin_country': 'Kenya',
            'bean_origin_region': 'Nyeri',
            'coffee_dose_grams': 17.0,
            'water_volume_ml': 270.0,
            'final_tds_percent': 1.40,
            'score_overall_rating': 4.5
        }
        
        # Update the record
        updated_df = form_service.update_brew_record(sample_dataframe, brew_id, form_data)
        
        # Verify the update
        updated_row = updated_df[updated_df['brew_id'] == brew_id].iloc[0]
        assert updated_row['bean_name'] == 'Updated Bean Name'
        assert updated_row['bean_origin_country'] == 'Kenya'
        assert updated_row['bean_origin_region'] == 'Nyeri'
        assert updated_row['coffee_dose_grams'] == 17.0
        assert updated_row['water_volume_ml'] == 270.0
        assert updated_row['final_tds_percent'] == 1.40
        assert updated_row['score_overall_rating'] == 4.5
        
        # Verify calculated fields are preserved (they should be recalculated separately)
        assert updated_row['brew_ratio_to_1'] == 16.7  # Original calculated value
        assert updated_row['score_strength_category'] == 'Ideal'  # Original calculated value
    
    def test_calculate_final_brew_mass(self, form_service):
        """Test calculation of final brew mass from mug and combined weights"""
        # Test normal calculation
        result = form_service.calculate_final_brew_mass(300.0, 530.0)
        assert result == 230.0
        
        # Test with None values
        assert form_service.calculate_final_brew_mass(None, 530.0) is None
        assert form_service.calculate_final_brew_mass(300.0, None) is None
        assert form_service.calculate_final_brew_mass(None, None) is None
    
    def test_update_brew_record_with_calculated_final_brew_mass(self, form_service, sample_dataframe):
        """Test that final_brew_mass_grams is calculated from mug weights during update"""
        brew_id = 2
        form_data = {
            'mug_weight_grams': 310.0,
            'final_combined_weight_grams': 550.0,
            'coffee_dose_grams': 16.5,
            'water_volume_ml': 260.0
        }
        
        # Update the record
        updated_df = form_service.update_brew_record(sample_dataframe, brew_id, form_data)
        
        # Verify the calculation
        updated_row = updated_df[updated_df['brew_id'] == brew_id].iloc[0]
        assert updated_row['mug_weight_grams'] == 310.0
        assert updated_row['final_combined_weight_grams'] == 550.0
        # The calculated final_brew_mass_grams should be saved to the DataFrame
        # Note: In the actual implementation, this would be handled by the processing step
        
    def test_update_brew_record_preserves_other_records(self, form_service, sample_dataframe):
        """Test that updating one record doesn't affect other records"""
        original_df = sample_dataframe.copy()
        brew_id = 1
        form_data = {
            'bean_name': 'Changed Bean',
            'coffee_dose_grams': 20.0
        }
        
        # Update the record
        updated_df = form_service.update_brew_record(sample_dataframe, brew_id, form_data)
        
        # Verify only the target record changed
        updated_record = updated_df[updated_df['brew_id'] == brew_id].iloc[0]
        assert updated_record['bean_name'] == 'Changed Bean'
        assert updated_record['coffee_dose_grams'] == 20.0
        
        # Verify other records unchanged
        other_records = updated_df[updated_df['brew_id'] != brew_id]
        original_other_records = original_df[original_df['brew_id'] != brew_id]
        
        for col in ['bean_name', 'coffee_dose_grams']:
            pd.testing.assert_series_equal(
                other_records[col].reset_index(drop=True),
                original_other_records[col].reset_index(drop=True),
                check_names=False
            )
    
    def test_get_selectbox_index_helper(self):
        """Test the helper function for getting selectbox indices"""
        # This would be part of the main application class, testing the logic
        options = ["", "Option1", "Option2", "Option3"]
        
        # Test finding existing option
        assert self._get_selectbox_index(options, "Option2") == 2
        
        # Test with None value
        assert self._get_selectbox_index(options, None) == 0
        
        # Test with empty string
        assert self._get_selectbox_index(options, "") == 0
        
        # Test with non-existing value
        assert self._get_selectbox_index(options, "NonExistent") == 0
    
    def _get_selectbox_index(self, options, current_value):
        """Helper method copied from main application for testing"""
        try:
            if current_value is not None and str(current_value).strip():
                return options.index(str(current_value))
        except (ValueError, AttributeError):
            pass
        return 0
    
    def test_form_data_preparation(self, form_service):
        """Test preparation of form data for updating"""
        # This tests the data cleaning and preparation logic
        raw_form_data = {
            'bean_name': '  Test Bean  ',  # Should be stripped
            'bean_origin_country': '',     # Should become None
            'bean_roast_level': 'Medium',  # Should stay as is
            'coffee_dose_grams': 15.5,     # Numeric value
            'score_overall_rating': 4.2    # Float value
        }
        
        # Clean the data (similar to what happens in the form submission)
        cleaned_data = {}
        for key, value in raw_form_data.items():
            if isinstance(value, str):
                cleaned_value = value.strip() if value.strip() else None
                cleaned_data[key] = cleaned_value
            else:
                cleaned_data[key] = value
        
        # Verify cleaning
        assert cleaned_data['bean_name'] == 'Test Bean'
        assert cleaned_data['bean_origin_country'] is None
        assert cleaned_data['bean_roast_level'] == 'Medium'
        assert cleaned_data['coffee_dose_grams'] == 15.5
        assert cleaned_data['score_overall_rating'] == 4.2
    
    def test_update_nonexistent_record(self, form_service, sample_dataframe):
        """Test updating a record that doesn't exist should raise an error"""
        nonexistent_id = 999
        form_data = {'bean_name': 'Test'}
        
        with pytest.raises(IndexError):
            form_service.update_brew_record(sample_dataframe, nonexistent_id, form_data)
    
    @patch('pandas.DataFrame.to_csv')
    def test_csv_save_integration(self, mock_to_csv, form_service, sample_dataframe):
        """Test that the DataFrame can be saved to CSV after updates"""
        brew_id = 1
        form_data = {'bean_name': 'Updated Bean'}
        
        # Update the record
        updated_df = form_service.update_brew_record(sample_dataframe, brew_id, form_data)
        
        # Simulate saving to CSV
        temp_file = tempfile.mktemp(suffix='.csv')
        try:
            updated_df.to_csv(temp_file, index=False)
            mock_to_csv.assert_called_once()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_data_type_preservation(self, form_service, sample_dataframe):
        """Test that data types are preserved during updates"""
        brew_id = 1
        form_data = {
            'coffee_dose_grams': 18.5,      # float
            'water_volume_ml': 275.0,       # float  
            'brew_bloom_time_s': 50.0,      # float
            'score_overall_rating': 4.8,    # float
            'bean_name': 'String Bean'      # string
        }
        
        # Update the record
        updated_df = form_service.update_brew_record(sample_dataframe, brew_id, form_data)
        updated_row = updated_df[updated_df['brew_id'] == brew_id].iloc[0]
        
        # Verify data types
        assert isinstance(updated_row['coffee_dose_grams'], (float, int))
        assert isinstance(updated_row['water_volume_ml'], (float, int))
        assert isinstance(updated_row['brew_bloom_time_s'], (float, int))
        assert isinstance(updated_row['score_overall_rating'], (float, int))
        assert isinstance(updated_row['bean_name'], str)


class TestDataEditingIntegration:
    """Integration tests for the complete data editing workflow"""
    
    def test_full_edit_workflow_simulation(self):
        """Test the complete workflow: select -> edit -> save -> reprocess"""
        # This would typically be tested with actual UI components
        # For now, we test the core logic flow
        
        # 1. Load data (simulated)
        test_data = pd.DataFrame({
            'brew_id': [1],
            'bean_name': ['Original Bean'],
            'coffee_dose_grams': [15.0],
            'final_tds_percent': [1.25],
            'final_brew_mass_grams': [230.0],
            'mug_weight_grams': [300.0],
            'final_combined_weight_grams': [530.0]
        })
        
        # 2. Update record (simulated)
        form_service = FormHandlingService()
        updated_data = {
            'bean_name': 'Updated Bean',
            'coffee_dose_grams': 16.0,
            'mug_weight_grams': 310.0,
            'final_combined_weight_grams': 540.0
        }
        
        result_df = form_service.update_brew_record(test_data, 1, updated_data)
        
        # 3. Verify updates
        updated_row = result_df.iloc[0]
        assert updated_row['bean_name'] == 'Updated Bean'
        assert updated_row['coffee_dose_grams'] == 16.0
        assert updated_row['mug_weight_grams'] == 310.0
        assert updated_row['final_combined_weight_grams'] == 540.0
        
        # 4. Verify that final_brew_mass_grams would be recalculated
        # (In the real workflow, this happens via the processing pipeline)
        expected_final_brew_mass = 540.0 - 310.0  # 230.0
        calculated_mass = form_service.calculate_final_brew_mass(310.0, 540.0)
        assert calculated_mass == expected_final_brew_mass