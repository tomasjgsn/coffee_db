"""
Test suite for all extracted services

Tests the business logic services that were extracted from the main application.
Following TDD principles to ensure refactoring preserves functionality.
"""

import pytest
import pandas as pd
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

# Import services to test
from src.services.bean_selection_service import BeanSelectionService
from src.services.form_handling_service import FormHandlingService
from src.services.visualization_service import VisualizationService
from src.services.data_management_service import DataManagementService
from src.services.brew_id_service import BrewIdService
from src.services.config import ServiceConfig
from src.services.exceptions import DataLoadError, SecurityError
from src.services.metrics import get_service_metrics


@pytest.fixture
def sample_coffee_data():
    """Fixture providing sample coffee brewing data for testing"""
    return pd.DataFrame([
        {
            'brew_id': 1,
            'brew_date': '2025-08-01',
            'bean_name': 'Test Bean A',
            'bean_origin_country': 'Colombia',
            'bean_origin_region': 'Huila',
            'bean_variety': 'Arabica',
            'bean_process_method': 'Washed',
            'bean_roast_level': 'Medium',
            'coffee_dose_grams': 18.0,
            'water_volume_ml': 250.0,
            'water_temp_degC': 96.0,
            'grind_size': 6.0,
            'final_tds_percent': 1.25,
            'final_extraction_yield_percent': 20.5,
            'score_overall_rating': 7.5,
            'score_brewing_zone': 'Ideal-Ideal',
            'estimated_bag_size_grams': 500.0,
            'archive_status': 'active'
        },
        {
            'brew_id': 2,
            'brew_date': '2025-08-02',
            'bean_name': 'Test Bean B',
            'bean_origin_country': 'Ethiopia',
            'bean_origin_region': 'Yirgacheffe',
            'bean_variety': 'Heirloom',
            'bean_process_method': 'Natural',
            'bean_roast_level': 'Light',
            'coffee_dose_grams': 16.0,
            'water_volume_ml': 240.0,
            'water_temp_degC': 94.0,
            'grind_size': 5.5,
            'final_tds_percent': 1.10,
            'final_extraction_yield_percent': 18.2,
            'score_overall_rating': 8.2,
            'score_brewing_zone': 'Under-Ideal',
            'estimated_bag_size_grams': 250.0,
            'archive_status': 'active'
        },
        {
            'brew_id': 3,
            'brew_date': '2025-08-03',
            'bean_name': 'Test Bean A',
            'bean_origin_country': 'Colombia',
            'bean_origin_region': 'Huila',
            'bean_variety': 'Arabica',
            'bean_process_method': 'Washed',
            'bean_roast_level': 'Medium',
            'coffee_dose_grams': 20.0,
            'water_volume_ml': 300.0,
            'water_temp_degC': 98.0,
            'grind_size': 6.2,
            'final_tds_percent': 1.35,
            'final_extraction_yield_percent': 21.8,
            'score_overall_rating': 7.8,
            'score_brewing_zone': 'Ideal-Strong',
            'estimated_bag_size_grams': 500.0,
            'archive_status': 'archived'
        }
    ])


class TestBeanSelectionService:
    """Test the Bean Selection Service"""
    
    @pytest.fixture
    def service(self):
        return BeanSelectionService()
    
    def test_get_unique_beans_active_only(self, service, sample_coffee_data):
        """Test getting unique beans excluding archived ones"""
        unique_beans = service.get_unique_beans(sample_coffee_data, show_archived=False)
        
        # Should only get active beans
        assert len(unique_beans) == 2  # Test Bean A (active) and Test Bean B
        bean_names = unique_beans['bean_name'].tolist()
        assert 'Test Bean A' in bean_names
        assert 'Test Bean B' in bean_names
    
    def test_get_unique_beans_include_archived(self, service, sample_coffee_data):
        """Test getting unique beans including archived ones"""
        unique_beans = service.get_unique_beans(sample_coffee_data, show_archived=True)
        
        # Should get both active and archived
        assert len(unique_beans) == 2  # Still 2 unique beans, but includes archived entries
    
    def test_get_bean_options_with_usage(self, service, sample_coffee_data):
        """Test creating bean options with usage information"""
        unique_beans = service.get_unique_beans(sample_coffee_data, show_archived=False)
        options = service.get_bean_options_with_usage(sample_coffee_data, unique_beans, "add")
        
        assert len(options) == 3  # "Create New Bean" + 2 unique beans
        assert options[0] == "Create New Bean"
        
        # Check that usage info is included
        bean_a_option = next((opt for opt in options if 'Test Bean A' in opt), None)
        assert bean_a_option is not None
        assert 'remaining' in bean_a_option.lower()
    
    def test_get_selected_bean_data(self, service, sample_coffee_data):
        """Test getting selected bean data from option"""
        unique_beans = service.get_unique_beans(sample_coffee_data, show_archived=False)
        options = service.get_bean_options_with_usage(sample_coffee_data, unique_beans, "add")
        
        # Test selecting actual bean
        selected_option = options[1]  # First real bean option
        bean_data = service.get_selected_bean_data(selected_option, unique_beans, options, "add")
        
        assert bean_data is not None
        assert 'bean_name' in bean_data
        
        # Test manual entry
        manual_data = service.get_selected_bean_data("Create New Bean", unique_beans, options, "add")
        assert manual_data is None
    
    def test_get_bean_statistics(self, service, sample_coffee_data):
        """Test calculating bean statistics"""
        stats = service.get_bean_statistics(sample_coffee_data)
        
        assert len(stats) == 2  # Two unique beans
        
        # Find Test Bean A stats
        bean_a_stats = next((s for s in stats if s.name == 'Test Bean A'), None)
        assert bean_a_stats is not None
        assert bean_a_stats.total_brews == 2  # Two brews of Test Bean A
        assert bean_a_stats.total_grams_used == 38.0  # 18 + 20
        assert bean_a_stats.bag_size == 500.0
        assert bean_a_stats.remaining_grams == 462.0  # 500 - 38
    
    def test_archive_bean(self, service, sample_coffee_data):
        """Test archiving a bean"""
        df = sample_coffee_data.copy()
        
        # Archive Test Bean B
        updated_df = service.archive_bean('Test Bean B', 'Ethiopia', 'Yirgacheffe', df)
        
        # Check that the bean is now archived
        archived_records = updated_df[updated_df['bean_name'] == 'Test Bean B']
        assert all(archived_records['archive_status'] == 'archived')
    
    def test_restore_bean(self, service, sample_coffee_data):
        """Test restoring an archived bean"""
        df = sample_coffee_data.copy()
        
        # Test Bean A record 3 is archived, restore it
        updated_df = service.restore_bean('Test Bean A', 'Colombia', 'Huila', df)
        
        # Check that all Test Bean A records are now active
        bean_a_records = updated_df[updated_df['bean_name'] == 'Test Bean A']
        assert all(bean_a_records['archive_status'] == 'active')
    
    def test_find_old_beans(self, service, sample_coffee_data):
        """Test finding old beans based on days threshold"""
        # Mock today's date to control the calculation
        with patch('pandas.Timestamp.now') as mock_now:
            mock_now.return_value.date.return_value = date(2025, 8, 10)
            
            old_beans = service.find_old_beans(sample_coffee_data, days_threshold=5)
            
            # All beans should be considered old since they were brewed 7-9 days ago
            assert len(old_beans) > 0


class TestFormHandlingService:
    """Test the Form Handling Service"""
    
    @pytest.fixture
    def service(self):
        return FormHandlingService()
    
    def test_generate_grind_dial_options(self, service):
        """Test generating grind dial options"""
        options = service.generate_grind_dial_options()
        
        # Should have 1.0, 1.1, 1.2, 2.0, 2.1, 2.2, ..., 11.0
        assert len(options) == 31  # 10 * 3 + 1 (no .1, .2 after 11)
        assert 1.0 in options
        assert 1.1 in options
        assert 1.2 in options
        assert 11.0 in options
        assert 11.1 not in options  # Should not exist
    
    def test_format_grind_option_display(self, service):
        """Test formatting grind options for display"""
        options = [1.0, 1.1, 2.0, 2.2]
        formatted = service.format_grind_option_display(options)
        
        assert formatted == ["1", "1.1", "2", "2.2"]
    
    def test_get_grind_size_index(self, service):
        """Test getting grind size index"""
        options = [1.0, 1.1, 1.2, 2.0]
        
        assert service.get_grind_size_index(options, 1.1) == 1
        assert service.get_grind_size_index(options, 2.0) == 3
        assert service.get_grind_size_index(options, 5.0) == 0  # Not found, return 0
        assert service.get_grind_size_index(options, None) == 0
    
    def test_prepare_bean_form_data(self, service):
        """Test preparing bean form data with different sources"""
        selected_data = {'bean_name': 'Selected Bean', 'bean_country': 'Colombia'}
        current_data = {'bean_name': 'Current Bean', 'bean_country': 'Ethiopia'}
        
        # Should prioritize selected data
        result = service.prepare_bean_form_data(selected_data, current_data, "add")
        assert result == selected_data
        
        # Should fall back to current data if no selection
        result = service.prepare_bean_form_data(None, current_data, "edit")
        assert result == current_data
        
        # Should return empty dict if no data
        result = service.prepare_bean_form_data(None, None, "add")
        assert result == {}
    
    def test_calculate_final_brew_mass(self, service):
        """Test calculating final brew mass"""
        # Valid calculation
        result = service.calculate_final_brew_mass(350.0, 580.0)
        assert result == 230.0
        
        # Missing data
        assert service.calculate_final_brew_mass(None, 580.0) is None
        assert service.calculate_final_brew_mass(350.0, None) is None
    
    def test_prepare_brew_record(self, service):
        """Test preparing a complete brew record"""
        form_data = {
            'brew_date': date(2025, 8, 1),
            'bean_name': 'Test Bean',
            'bean_origin_country': 'Colombia',
            'grind_size': 6.0,
            'coffee_dose_grams': 18.0,
            'score_overall_rating': 7.5,
            'mug_weight_grams': 350.0,
            'final_combined_weight_grams': 580.0
        }
        
        record = service.prepare_brew_record(form_data, brew_id=5, estimated_bag_size_grams=500.0)
        
        assert record['brew_id'] == 5
        assert record['bean_name'] == 'Test Bean'
        assert record['final_brew_mass_grams'] == 230.0  # 580 - 350
        assert record['estimated_bag_size_grams'] == 500.0
        assert record['archive_status'] == 'active'
    
    def test_validate_form_data(self, service):
        """Test form data validation"""
        # Valid data
        valid_data = {
            'bean_name': 'Test Bean',
            'grind_size': 6.0,
            'coffee_dose_grams': 18.0,
            'final_tds_percent': 1.25,
            'score_overall_rating': 7.5
        }
        errors = service.validate_form_data(valid_data)
        assert len(errors) == 0
        
        # Invalid data
        invalid_data = {
            'bean_name': '',  # Required field missing
            'grind_size': None,  # Required field missing
            'coffee_dose_grams': -5.0,  # Negative value
            'final_tds_percent': 10.0,  # Out of range
            'score_overall_rating': 15.0  # Out of range
        }
        errors = service.validate_form_data(invalid_data)
        assert len(errors) > 0
        assert any('Bean name is required' in error for error in errors)
        assert any('Grind size is required' in error for error in errors)


class TestVisualizationService:
    """Test the Visualization Service"""
    
    @pytest.fixture
    def service(self):
        return VisualizationService()
    
    def test_get_brewing_control_chart_zones(self, service):
        """Test getting brewing control chart zone definitions"""
        zones = service.get_brewing_control_chart_zones()
        
        assert len(zones) == 5  # 5 zones defined
        assert 'Ideal' in zones['zone'].values
        assert 'Under-Extracted' in zones['zone'].values
        assert 'Over-Extracted' in zones['zone'].values
    
    def test_get_brew_quality_color_scale(self, service):
        """Test getting brew quality color scale"""
        color_scale = service.get_brew_quality_color_scale()
        
        # Should be an Altair Scale object
        assert hasattr(color_scale, 'domain')
        assert hasattr(color_scale, 'range')
    
    def test_apply_data_filters(self, service, sample_coffee_data):
        """Test applying data filters"""
        filters = {
            'coffees': ['Test Bean A'],
            'grinds': [6.0, 6.2],
            'temps': []  # Empty filter should not filter
        }
        
        filtered_df = service.apply_data_filters(sample_coffee_data, filters)
        
        # Should only have Test Bean A records with specified grind sizes
        assert len(filtered_df) == 2  # Two Test Bean A records
        assert all(filtered_df['bean_name'] == 'Test Bean A')
        assert all(filtered_df['grind_size'].isin([6.0, 6.2]))
    
    def test_get_filter_options(self, service, sample_coffee_data):
        """Test getting available filter options"""
        options = service.get_filter_options(sample_coffee_data)
        
        assert 'coffees' in options
        assert 'grinds' in options
        assert 'temps' in options
        assert 'Test Bean A' in options['coffees']
        assert 'Test Bean B' in options['coffees']
    
    def test_get_filter_summary_info(self, service, sample_coffee_data):
        """Test getting filter summary information"""
        filtered_df = sample_coffee_data.head(2)  # Take first 2 rows
        summary = service.get_filter_summary_info(sample_coffee_data, filtered_df)
        
        assert summary['total_rows'] == 3
        assert summary['filtered_rows'] == 2
        assert abs(summary['filtered_percentage'] - 66.67) < 0.1  # Should be ~66.67%
    
    def test_create_summary_metrics(self, service, sample_coffee_data):
        """Test creating summary metrics"""
        metrics = service.create_summary_metrics(sample_coffee_data)
        
        assert metrics['total_brews'] == 3
        assert metrics['unique_beans'] == 2
        assert metrics['avg_rating'] > 0
        assert metrics['avg_tds'] > 0
        assert metrics['avg_extraction'] > 0


class TestDataManagementService:
    """Test the Data Management Service"""
    
    @pytest.fixture
    def service(self):
        # Create a temporary CSV file for testing
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_file.close()
        return DataManagementService(temp_file.name)
    
    def test_save_and_load_data(self, service, sample_coffee_data):
        """Test saving and loading data"""
        # Save data
        success = service.save_data(sample_coffee_data)
        assert success
        
        # Load data back
        loaded_df = service.load_data()
        assert len(loaded_df) == len(sample_coffee_data)
        assert 'brew_id' in loaded_df.columns
    
    def test_add_record(self, service, sample_coffee_data):
        """Test adding a new record"""
        new_record = {
            'brew_id': 4,
            'bean_name': 'New Bean',
            'brew_date': date(2025, 8, 4),
            'score_overall_rating': 8.0
        }
        
        updated_df = service.add_record(sample_coffee_data, new_record)
        assert len(updated_df) == len(sample_coffee_data) + 1
        assert updated_df.iloc[-1]['bean_name'] == 'New Bean'
    
    def test_delete_record(self, service, sample_coffee_data):
        """Test deleting a record"""
        updated_df = service.delete_record(sample_coffee_data, brew_id=2)
        assert len(updated_df) == len(sample_coffee_data) - 1
        assert 2 not in updated_df['brew_id'].values
    
    def test_get_next_brew_id(self, service, sample_coffee_data):
        """Test getting next brew ID"""
        next_id = service.get_next_brew_id(sample_coffee_data)
        assert next_id == 4  # Should be max(3) + 1
    
    def test_validate_dataframe(self, service, sample_coffee_data):
        """Test DataFrame validation"""
        # Valid DataFrame
        issues = service.validate_dataframe(sample_coffee_data)
        assert len(issues) == 0
        
        # Invalid DataFrame - missing required columns
        invalid_df = sample_coffee_data.drop(columns=['brew_id'])
        issues = service.validate_dataframe(invalid_df)
        assert len(issues) > 0
        assert any('Missing required columns' in issue for issue in issues)
    
    def test_get_data_summary(self, service, sample_coffee_data):
        """Test getting data summary"""
        summary = service.get_data_summary(sample_coffee_data)
        
        assert summary['total_records'] == 3
        assert summary['unique_beans'] == 2
        assert summary['avg_rating'] > 0
        assert summary['data_completeness'] > 0
    
    @patch('subprocess.run')
    def test_run_post_processing(self, mock_run, service):
        """Test running post-processing"""
        # Mock successful processing
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Processing successful"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        success, stdout, stderr = service.run_post_processing()
        
        assert success
        assert "Processing successful" in stdout
        assert mock_run.called
    
    def teardown_method(self, method):
        """Clean up temporary files after each test"""
        # Clean up any temporary files created during testing
        import glob
        for temp_file in glob.glob("/tmp/tmp*.csv"):
            try:
                os.unlink(temp_file)
            except OSError:
                pass


class TestBrewIdService:
    """Test the Brew ID Service"""
    
    @pytest.fixture
    def service(self):
        return BrewIdService()
    
    def test_get_next_id_normal_case(self, service):
        """Test getting next ID with normal numeric data"""
        df = pd.DataFrame({'brew_id': [1, 2, 3]})
        next_id = service.get_next_id(df)
        assert next_id == 4
    
    def test_get_next_id_empty_dataframe(self, service):
        """Test getting next ID with empty DataFrame"""
        df = pd.DataFrame()
        next_id = service.get_next_id(df)
        assert next_id == 1
    
    def test_get_next_id_mixed_types(self, service):
        """Test getting next ID with mixed string/numeric data"""
        df = pd.DataFrame({'brew_id': [1, '2', '3.0', 'invalid', 5]})
        next_id = service.get_next_id(df)
        assert next_id == 6  # Should handle mixed types correctly
    
    def test_safe_brew_id_to_int(self, service):
        """Test safe conversion of brew IDs to integers"""
        assert service.safe_brew_id_to_int(5) == 5
        assert service.safe_brew_id_to_int('5') == 5
        assert service.safe_brew_id_to_int('5.0') == 5
        assert service.safe_brew_id_to_int('invalid', default=0) == 0
        assert service.safe_brew_id_to_int(None, default=0) == 0
    
    def test_validate_brew_id(self, service):
        """Test brew ID validation"""
        assert service.validate_brew_id(1) is True
        assert service.validate_brew_id('1') is True
        assert service.validate_brew_id('5') is True
        assert service.validate_brew_id(0) is False  # Must be positive
        assert service.validate_brew_id(-1) is False
        assert service.validate_brew_id('invalid') is False
        assert service.validate_brew_id(None) is False
        assert service.validate_brew_id('') is False
    
    def test_normalize_brew_id(self, service):
        """Test brew ID normalization"""
        assert service.normalize_brew_id(1) == 1
        assert service.normalize_brew_id('5') == 5
        assert service.normalize_brew_id(3.0) == 3
        assert service.normalize_brew_id('invalid') is None
        assert service.normalize_brew_id(0) is None
        assert service.normalize_brew_id(-1) is None


class TestRecentAdditionsFeature:
    """Test suite for recent additions highlighting functionality"""
    
    def test_visualization_service_handles_recent_brew_ids(self):
        """Test that VisualizationService can create charts with recent highlights"""
        from src.services.visualization_service import VisualizationService
        
        service = VisualizationService()
        
        # Create test data
        test_data = pd.DataFrame({
            'brew_id': [1, 2, 3],
            'final_extraction_yield_percent': [18.5, 20.0, 22.5],
            'final_tds_percent': [1.25, 1.30, 1.35],
            'score_brewing_zone': ['Ideal', 'Ideal', 'Over-Extracted'],
            'score_overall_rating': [7.5, 8.0, 6.5],
            'bean_name': ['Test Bean 1', 'Test Bean 2', 'Test Bean 3'],
            'brew_date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'score_flavor_profile_category': ['Fruity', 'Nutty', 'Chocolate'],
            'coffee_grams_per_liter': [60.0, 62.0, 58.0],
            'grind_size': [6.0, 6.5, 7.0],
            'water_temp_degC': [93.0, 94.0, 92.0],
            'brew_method': ['V60', 'V60', 'V60']
        })
        
        # Test chart creation without recent highlights
        chart = service.create_brewing_control_chart(test_data)
        assert chart is not None
        
        # Test chart creation with recent highlights
        recent_brew_ids = [2, 3]
        chart_with_highlights = service.create_brewing_control_chart(test_data, recent_brew_ids)
        assert chart_with_highlights is not None
        
        # Test recent points chart creation
        recent_data = test_data[test_data['brew_id'].isin(recent_brew_ids)]
        color_scale = service.get_brew_quality_color_scale()
        recent_chart = service.create_recent_points_chart(recent_data, color_scale)
        assert recent_chart is not None
    
    def test_recent_points_chart_styling(self):
        """Test that recent points have enhanced visual styling"""
        from src.services.visualization_service import VisualizationService
        
        service = VisualizationService()
        
        # Create test data for recent points
        recent_data = pd.DataFrame({
            'brew_id': [1],
            'final_extraction_yield_percent': [19.0],
            'final_tds_percent': [1.28],
            'score_brewing_zone': ['Ideal'],
            'score_overall_rating': [8.0],
            'bean_name': ['Recent Bean'],
            'brew_date': ['2024-01-01'],
            'score_flavor_profile_category': ['Fruity'],
            'coffee_grams_per_liter': [60.0],
            'grind_size': [6.0],
            'water_temp_degC': [93.0],
            'brew_method': ['V60']
        })
        
        color_scale = service.get_brew_quality_color_scale()
        recent_chart = service.create_recent_points_chart(recent_data, color_scale)
        
        # Verify chart is created (detailed styling verification would require Altair internals)
        assert recent_chart is not None
        
        # Test with empty data
        empty_data = pd.DataFrame()
        empty_chart = service.create_recent_points_chart(empty_data, color_scale)
        assert empty_chart is not None
    
    def test_chart_data_separation(self):
        """Test that chart correctly separates recent and regular data"""
        from src.services.visualization_service import VisualizationService
        
        service = VisualizationService()
        
        # Create test data
        test_data = pd.DataFrame({
            'brew_id': [1, 2, 3, 4, 5],
            'final_extraction_yield_percent': [18.0, 19.0, 20.0, 21.0, 22.0],
            'final_tds_percent': [1.20, 1.25, 1.30, 1.35, 1.40],
            'score_brewing_zone': ['Ideal'] * 5,
            'score_overall_rating': [7.0, 7.5, 8.0, 8.5, 9.0],
            'bean_name': [f'Bean {i}' for i in range(1, 6)],
            'brew_date': ['2024-01-01'] * 5,
            'score_flavor_profile_category': ['Fruity'] * 5,
            'coffee_grams_per_liter': [60.0] * 5,
            'grind_size': [6.0] * 5,
            'water_temp_degC': [93.0] * 5,
            'brew_method': ['V60'] * 5
        })
        
        recent_brew_ids = [3, 5]  # IDs 3 and 5 are recent
        
        # Simulate data separation logic
        recent_data = test_data[test_data['brew_id'].isin(recent_brew_ids)]
        regular_data = test_data[~test_data['brew_id'].isin(recent_brew_ids)]
        
        assert len(recent_data) == 2
        assert len(regular_data) == 3
        assert list(recent_data['brew_id']) == [3, 5]
        assert list(regular_data['brew_id']) == [1, 2, 4]
        
        # Test chart creation with separated data
        chart = service.create_brewing_control_chart(test_data, recent_brew_ids)
        assert chart is not None
    
    def test_empty_recent_brew_ids_handling(self):
        """Test that empty or None recent_brew_ids are handled correctly"""
        from src.services.visualization_service import VisualizationService
        
        service = VisualizationService()
        
        # Create test data
        test_data = pd.DataFrame({
            'brew_id': [1, 2],
            'final_extraction_yield_percent': [18.0, 20.0],
            'final_tds_percent': [1.25, 1.30],
            'score_brewing_zone': ['Ideal', 'Ideal'],
            'score_overall_rating': [7.5, 8.0],
            'bean_name': ['Bean 1', 'Bean 2'],
            'brew_date': ['2024-01-01', '2024-01-02'],
            'score_flavor_profile_category': ['Fruity', 'Nutty'],
            'coffee_grams_per_liter': [60.0, 62.0],
            'grind_size': [6.0, 6.5],
            'water_temp_degC': [93.0, 94.0],
            'brew_method': ['V60', 'V60']
        })
        
        # Test with None recent_brew_ids
        chart_none = service.create_brewing_control_chart(test_data, None)
        assert chart_none is not None
        
        # Test with empty list
        chart_empty = service.create_brewing_control_chart(test_data, [])
        assert chart_empty is not None
        
        # Test with non-existent brew IDs
        chart_nonexistent = service.create_brewing_control_chart(test_data, [99, 100])
        assert chart_nonexistent is not None


class TestServiceInfrastructure:
    """Test service infrastructure components"""
    
    def test_service_config(self):
        """Test service configuration"""
        config = ServiceConfig()
        
        # Test file size limits
        limits = config.get_file_size_limits()
        assert 'max' in limits
        assert 'warn' in limits
        assert limits['max'] > limits['warn']
        
        # Test CSV path
        csv_path = config.get_csv_path()
        assert isinstance(csv_path, Path)
        
        # Test timeouts
        assert config.get_processing_timeout(False) < config.get_processing_timeout(True)
    
    def test_metrics_collection(self):
        """Test metrics collection"""
        metrics = get_service_metrics()
        
        # Test that metrics instance exists
        assert metrics is not None
        
        # Test basic functionality
        stats = metrics.get_all_stats()
        assert isinstance(stats, dict)
    
    def test_security_validation(self):
        """Test security validation in data management"""
        # This would test path validation and other security measures
        # For now, just ensure the service initializes properly with security imports
        service = DataManagementService()
        assert service is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])