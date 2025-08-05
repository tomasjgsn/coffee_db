import pytest
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from visualise_brew_trends import get_bean_statistics, archive_bean, restore_bean


class TestGetBeanStatistics:
    """Test suite for get_bean_statistics function"""
    
    def test_empty_dataframe(self):
        """Should return empty list for empty DataFrame"""
        df = pd.DataFrame()
        stats = get_bean_statistics(df)
        assert stats == []
    
    def test_beans_with_null_regions(self):
        """Should properly identify beans with NaN/None region values"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'La Providencia', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 15.0,
                'brew_date': date.today(),
                'score_overall_rating': 8.0
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 1
        la_prov_bean = stats[0]
        assert la_prov_bean['name'] == 'La Providencia'
        assert la_prov_bean['region'] == ''  # Should be empty string, not 'nan'
        assert la_prov_bean['country'] == 'Colombia'
    
    def test_beans_with_regions(self):
        """Should handle beans with valid region values"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Gold Maria-Isabel', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': 'Jardin', 
                'coffee_dose_grams': 20.0,
                'brew_date': date.today(),
                'score_overall_rating': 7.5
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 1
        bean = stats[0]
        assert bean['name'] == 'Gold Maria-Isabel'
        assert bean['region'] == 'Jardin'
        assert bean['country'] == 'Colombia'
    
    def test_mixed_region_scenarios(self):
        """Should handle mix of null and valid regions"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'La Providencia', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 15.0,
                'brew_date': date.today(),
                'score_overall_rating': 8.0
            },
            {
                'bean_name': 'Gold Maria-Isabel', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': 'Jardin', 
                'coffee_dose_grams': 20.0,
                'brew_date': date.today(),
                'score_overall_rating': 7.5
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 2
        
        # Find each bean
        la_prov = next(s for s in stats if s['name'] == 'La Providencia')
        maria_isabel = next(s for s in stats if s['name'] == 'Gold Maria-Isabel')
        
        assert la_prov['region'] == ''
        assert maria_isabel['region'] == 'Jardin'
    
    def test_usage_calculations(self):
        """Should correctly sum coffee_dose_grams for each bean"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 18.0,
                'brew_date': date.today(),
                'score_overall_rating': 7.0
            },
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 16.0,
                'brew_date': date.today(),
                'score_overall_rating': 8.0
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 1
        bean = stats[0]
        assert bean['total_grams_used'] == 34.0
        assert bean['total_brews'] == 2
    
    def test_archive_status_detection(self):
        """Should correctly identify active vs archived beans"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Active Bean', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 15.0,
                'brew_date': date.today(),
                'score_overall_rating': 8.0,
                'archive_status': 'active'
            },
            {
                'bean_name': 'Old Bean', 
                'bean_origin_country': 'Brazil', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 12.0,
                'brew_date': date.today(),
                'score_overall_rating': 6.0,
                'archive_status': 'archived'
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 2
        
        active_bean = next(s for s in stats if s['name'] == 'Active Bean')
        archived_bean = next(s for s in stats if s['name'] == 'Old Bean')
        
        assert active_bean['archive_status'] == 'active'
        assert archived_bean['archive_status'] == 'archived'
    
    def test_bag_size_calculations(self):
        """Should calculate remaining grams and usage percentage"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 50.0,
                'brew_date': date.today(),
                'score_overall_rating': 7.0,
                'estimated_bag_size_grams': 250.0
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 1
        bean = stats[0]
        assert bean['bag_size'] == 250.0
        assert bean['remaining_grams'] == 200.0
        assert bean['usage_percentage'] == 20.0
    
    def test_last_used_calculation(self):
        """Should find most recent brew_date per bean"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 18.0,
                'brew_date': yesterday,
                'score_overall_rating': 7.0
            },
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 16.0,
                'brew_date': today,
                'score_overall_rating': 8.0
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 1
        bean = stats[0]
        assert bean['last_used'] == today
    
    def test_days_since_last_calculation(self):
        """Should calculate days since last use correctly"""
        yesterday = date.today() - timedelta(days=1)
        
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 18.0,
                'brew_date': yesterday,
                'score_overall_rating': 7.0
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 1
        bean = stats[0]
        assert bean['days_since_last'] == 1
    
    def test_average_rating_calculation(self):
        """Should calculate mean score_overall_rating per bean"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 18.0,
                'brew_date': date.today(),
                'score_overall_rating': 6.0
            },
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 16.0,
                'brew_date': date.today(),
                'score_overall_rating': 8.0
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 1
        bean = stats[0]
        assert bean['avg_rating'] == 7.0
    
    def test_required_fields_present(self):
        """Should include all required fields in stats"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 18.0,
                'brew_date': date.today(),
                'score_overall_rating': 7.0
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 1
        bean = stats[0]
        
        required_fields = [
            'name', 'country', 'region', 'total_brews', 'total_grams_used',
            'bag_size', 'remaining_grams', 'usage_percentage', 'avg_rating',
            'last_used', 'days_since_last', 'archive_status', 'records'
        ]
        
        for field in required_fields:
            assert field in bean, f"Missing required field: {field}"


class TestArchiveBean:
    """Test suite for archive_bean function"""
    
    def test_archive_bean_with_region(self):
        """Archive bean that has a region value"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Gold Maria-Isabel', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': 'Jardin', 
                'coffee_dose_grams': 20.0,
                'archive_status': 'active'
            }
        ])
        
        result_df = archive_bean('Gold Maria-Isabel', 'Colombia', 'Jardin', test_data)
        
        # Check that the bean is archived
        assert result_df.iloc[0]['archive_status'] == 'archived'
    
    def test_archive_bean_with_null_region(self):
        """Archive bean with NaN/None region"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'La Providencia', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 15.0,
                'archive_status': 'active'
            }
        ])
        
        result_df = archive_bean('La Providencia', 'Colombia', None, test_data)
        
        # Check that the bean is archived
        assert result_df.iloc[0]['archive_status'] == 'archived'
    
    def test_archive_multiple_records(self):
        """Should update all records for the same bean"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'La Providencia', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 15.0,
                'archive_status': 'active'
            },
            {
                'bean_name': 'La Providencia', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 18.0,
                'archive_status': 'active'
            },
            {
                'bean_name': 'Other Bean', 
                'bean_origin_country': 'Brazil', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 12.0,
                'archive_status': 'active'
            }
        ])
        
        result_df = archive_bean('La Providencia', 'Colombia', None, test_data)
        
        # All La Providencia records should be archived
        la_prov_records = result_df[result_df['bean_name'] == 'La Providencia']
        assert all(la_prov_records['archive_status'] == 'archived')
        
        # Other beans should remain unchanged
        other_records = result_df[result_df['bean_name'] != 'La Providencia']
        assert all(other_records['archive_status'] == 'active')
    
    def test_archive_nonexistent_bean(self):
        """Should handle gracefully when bean doesn't exist"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Existing Bean', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 15.0,
                'archive_status': 'active'
            }
        ])
        
        result_df = archive_bean('Nonexistent Bean', 'Colombia', None, test_data)
        
        # No changes should be made
        assert all(result_df['archive_status'] == 'active')
        assert len(result_df) == 1
    
    def test_archive_status_update(self):
        """Should set archive_status to 'archived' for all matching records"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 18.0,
                'archive_status': 'active'
            }
        ])
        
        result_df = archive_bean('Test Bean', 'Ethiopia', 'Yirgacheffe', test_data)
        
        assert result_df.iloc[0]['archive_status'] == 'archived'
    
    def test_archive_creates_missing_column(self):
        """Should create archive_status column if missing"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 18.0
                # No archive_status column
            }
        ])
        
        result_df = archive_bean('Test Bean', 'Ethiopia', 'Yirgacheffe', test_data)
        
        # Column should be created and bean archived
        assert 'archive_status' in result_df.columns
        assert result_df.iloc[0]['archive_status'] == 'archived'
    
    def test_archive_handles_nan_column(self):
        """Should handle existing column with NaN values"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 18.0,
                'archive_status': np.nan
            }
        ])
        
        result_df = archive_bean('Test Bean', 'Ethiopia', 'Yirgacheffe', test_data)
        
        assert result_df.iloc[0]['archive_status'] == 'archived'
    
    def test_archive_with_empty_string_region(self):
        """Should handle empty string region (UI passes empty string for null regions)"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': None,  # Stored as None in DB
                'coffee_dose_grams': 18.0,
                'archive_status': 'active'
            }
        ])
        
        # UI passes empty string for null regions, function should handle it
        result_df = archive_bean('Test Bean', 'Ethiopia', '', test_data)  # Empty string
        
        assert result_df.iloc[0]['archive_status'] == 'archived'


class TestRestoreBean:
    """Test suite for restore_bean function"""
    
    def test_restore_archived_bean(self):
        """Should change archive_status from 'archived' to 'active'"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Old Bean', 
                'bean_origin_country': 'Brazil', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 12.0,
                'archive_status': 'archived'
            }
        ])
        
        result_df = restore_bean('Old Bean', 'Brazil', None, test_data)
        
        assert result_df.iloc[0]['archive_status'] == 'active'
    
    def test_restore_bean_with_null_region(self):
        """Should handle null region values properly"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'La Providencia', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 15.0,
                'archive_status': 'archived'
            }
        ])
        
        result_df = restore_bean('La Providencia', 'Colombia', None, test_data)
        
        assert result_df.iloc[0]['archive_status'] == 'active'
    
    def test_restore_all_records(self):
        """Should update all records for the bean"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Archived Bean', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': 'Jardin', 
                'coffee_dose_grams': 15.0,
                'archive_status': 'archived'
            },
            {
                'bean_name': 'Archived Bean', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': 'Jardin', 
                'coffee_dose_grams': 18.0,
                'archive_status': 'archived'
            },
            {
                'bean_name': 'Other Bean', 
                'bean_origin_country': 'Brazil', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 12.0,
                'archive_status': 'archived'
            }
        ])
        
        result_df = restore_bean('Archived Bean', 'Colombia', 'Jardin', test_data)
        
        # All Archived Bean records should be restored
        archived_bean_records = result_df[result_df['bean_name'] == 'Archived Bean']
        assert all(archived_bean_records['archive_status'] == 'active')
        
        # Other beans should remain unchanged
        other_records = result_df[result_df['bean_name'] != 'Archived Bean']
        assert all(other_records['archive_status'] == 'archived')
    
    def test_restore_nonexistent_bean(self):
        """Should handle gracefully when bean doesn't exist"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Existing Bean', 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 15.0,
                'archive_status': 'archived'
            }
        ])
        
        result_df = restore_bean('Nonexistent Bean', 'Colombia', None, test_data)
        
        # No changes should be made
        assert all(result_df['archive_status'] == 'archived')
        assert len(result_df) == 1


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_bean_name(self):
        """Should handle beans with empty/null names"""
        test_data = pd.DataFrame([
            {
                'bean_name': None, 
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': None, 
                'coffee_dose_grams': 15.0,
                'brew_date': date.today(),
                'score_overall_rating': 8.0
            }
        ])
        
        stats = get_bean_statistics(test_data)
        # Should exclude beans with null names
        assert len(stats) == 0
    
    def test_missing_columns_graceful_handling(self):
        """Should handle DataFrames missing new columns gracefully"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 18.0,
                'brew_date': date.today(),
                'score_overall_rating': 7.0
                # Missing estimated_bag_size_grams and archive_status
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 1
        bean = stats[0]
        assert bean['bag_size'] == 0
        assert bean['archive_status'] == 'active'  # Should default to 'active'
    
    def test_nan_archive_status_handling(self):
        """Should handle NaN values in archive_status column"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 18.0,
                'brew_date': date.today(),
                'score_overall_rating': 7.0,
                'archive_status': np.nan  # Explicitly NaN
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 1
        bean = stats[0]
        assert bean['archive_status'] == 'active'  # Should default to 'active' when NaN
    
    def test_nan_values_in_coffee_dose(self):
        """Should handle NaN values in coffee_dose_grams"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': np.nan,
                'brew_date': date.today(),
                'score_overall_rating': 7.0
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 1
        bean = stats[0]
        assert bean['total_grams_used'] == 0.0
    
    def test_nan_values_in_ratings(self):
        """Should handle NaN values in score_overall_rating"""
        test_data = pd.DataFrame([
            {
                'bean_name': 'Test Bean', 
                'bean_origin_country': 'Ethiopia', 
                'bean_origin_region': 'Yirgacheffe', 
                'coffee_dose_grams': 18.0,
                'brew_date': date.today(),
                'score_overall_rating': np.nan
            }
        ])
        
        stats = get_bean_statistics(test_data)
        assert len(stats) == 1
        bean = stats[0]
        assert bean['avg_rating'] == 0.0


if __name__ == "__main__":
    pytest.main([__file__])