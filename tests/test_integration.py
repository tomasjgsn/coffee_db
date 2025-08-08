"""
Integration tests between new extracted business logic and existing functions

These tests ensure that the extracted models and services work correctly
with the existing application functions, following TDD principles.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from pathlib import Path
import tempfile
import os

# Import existing functions from the monolithic application
from visualise_brew_trends import get_bean_statistics, archive_bean, restore_bean

# Import new extracted business logic
from src.services.coffee_data_service import CoffeeDataService
from src.models.bean_statistics import BeanStatistics
from src.repositories.coffee_data_repository import CoffeeDataRepository


class TestIntegrationExistingVsNew:
    """Test that new business logic produces same results as existing functions"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample coffee data for testing"""
        return pd.DataFrame([
            {
                'bean_name': 'La Providencia',
                'bean_origin_country': 'Colombia',
                'bean_origin_region': None,
                'coffee_dose_grams': 15.0,
                'brew_date': date.today() - timedelta(days=5),
                'score_overall_rating': 8.0,
                'archive_status': 'active',
                'estimated_bag_size_grams': 250.0
            },
            {
                'bean_name': 'La Providencia',
                'bean_origin_country': 'Colombia', 
                'bean_origin_region': None,
                'coffee_dose_grams': 17.0,
                'brew_date': date.today() - timedelta(days=2),
                'score_overall_rating': 7.5,
                'archive_status': 'active',
                'estimated_bag_size_grams': 250.0
            },
            {
                'bean_name': 'Gold Maria-Isabel',
                'bean_origin_country': 'Colombia',
                'bean_origin_region': 'Jardin', 
                'coffee_dose_grams': 20.0,
                'brew_date': date.today() - timedelta(days=1),
                'score_overall_rating': 9.0,
                'archive_status': 'active',
                'estimated_bag_size_grams': 250.0
            }
        ])
    
    def test_bean_statistics_compatibility(self, sample_data):
        """Test that new BeanStatistics produces same results as existing get_bean_statistics"""
        # Test existing function
        existing_stats = get_bean_statistics(sample_data)
        
        # Test new business logic  
        new_stats = BeanStatistics.calculate_all_beans(sample_data)
        
        # Should have same number of beans
        assert len(existing_stats) == len(new_stats)
        
        # Compare each bean's statistics
        for existing_bean in existing_stats:
            # Find corresponding bean in new stats
            new_bean = next(
                (b for b in new_stats if b.name == existing_bean['name']), None
            )
            assert new_bean is not None, f"Bean {existing_bean['name']} not found in new stats"
            
            # Compare key metrics (allow small floating point differences)
            assert abs(existing_bean['total_grams_used'] - new_bean.total_grams_used) < 0.01
            assert existing_bean['total_brews'] == new_bean.total_brews
            assert abs(existing_bean['avg_rating'] - new_bean.avg_rating) < 0.1
            assert existing_bean['archive_status'] == new_bean.archive_status
            
            # Region handling (both convert None to empty string)
            existing_region = existing_bean['region'] or ''
            new_region = new_bean.region or ''
            assert existing_region == new_region
    
    def test_archive_function_compatibility(self, sample_data):
        """Test that new service archive function works like existing archive_bean"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save test data to temporary file
            test_file = Path(temp_dir) / "test_data.csv" 
            sample_data.to_csv(test_file, index=False)
            
            # Test existing function
            existing_result = archive_bean('La Providencia', 'Colombia', None, sample_data.copy())
            
            # Test new service
            service = CoffeeDataService(str(test_file))
            new_success = service.archive_bean('La Providencia', 'Colombia', None)
            
            # Both should succeed
            assert new_success is True
            
            # Check that both produce same result
            archived_records_existing = existing_result[
                (existing_result['bean_name'] == 'La Providencia') &
                (existing_result['bean_origin_country'] == 'Colombia') &
                (existing_result['bean_origin_region'].isna())
            ]
            
            updated_data = service.repository.load_data()
            archived_records_new = updated_data[
                (updated_data['bean_name'] == 'La Providencia') &
                (updated_data['bean_origin_country'] == 'Colombia') &
                (updated_data['bean_origin_region'].isna())
            ]
            
            # Both should have archived status
            assert all(archived_records_existing['archive_status'] == 'archived')
            assert all(archived_records_new['archive_status'] == 'archived')
    
    def test_restore_function_compatibility(self, sample_data):
        """Test that new service restore function works like existing restore_bean"""
        # First archive the data
        sample_data.loc[sample_data['bean_name'] == 'La Providencia', 'archive_status'] = 'archived'
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_data.csv"
            sample_data.to_csv(test_file, index=False)
            
            # Test existing function  
            existing_result = restore_bean('La Providencia', 'Colombia', None, sample_data.copy())
            
            # Test new service
            service = CoffeeDataService(str(test_file))
            new_success = service.restore_bean('La Providencia', 'Colombia', None)
            
            # Both should succeed
            assert new_success is True
            
            # Check results
            restored_records_existing = existing_result[
                (existing_result['bean_name'] == 'La Providencia') &
                (existing_result['bean_origin_country'] == 'Colombia') &
                (existing_result['bean_origin_region'].isna())
            ]
            
            updated_data = service.repository.load_data()
            restored_records_new = updated_data[
                (updated_data['bean_name'] == 'La Providencia') &
                (updated_data['bean_origin_country'] == 'Colombia') &
                (updated_data['bean_origin_region'].isna())
            ]
            
            # Both should have active status
            assert all(restored_records_existing['archive_status'] == 'active')
            assert all(restored_records_new['archive_status'] == 'active')


class TestNewBusinessLogicExtensions:
    """Test new functionality that extends beyond existing capabilities"""
    
    def test_service_layer_crud_operations(self):
        """Test that service layer provides full CRUD operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "crud_test.csv"
            
            service = CoffeeDataService(str(test_file))
            
            # Test create (add brew record)
            from src.models.brew_record import BrewRecord
            record = BrewRecord(
                brew_id="crud_test", bean_name="Test Bean", brew_date=date.today(),
                coffee_dose_grams=18.0, water_volume_ml=300,
                final_tds_percent=1.25, final_brew_mass_grams=280.0,
                score_overall_rating=8.5
            )
            
            success = service.add_brew_record(record)
            assert success is True
            
            # Test read
            data = service.repository.load_data()
            assert len(data) == 1
            assert data.iloc[0]['brew_id'] == 'crud_test'
            
            # Test update
            success = service.update_brew_record('crud_test', {'score_overall_rating': 9.0})
            assert success is True
            
            updated_data = service.repository.load_data()
            assert updated_data.iloc[0]['score_overall_rating'] == 9.0
            
            # Test delete
            success = service.delete_brew_record('crud_test')
            assert success is True
            
            final_data = service.repository.load_data()
            assert len(final_data) == 0
    
    def test_data_validation_and_error_handling(self):
        """Test that new business logic provides better validation"""
        from src.models.brew_record import BrewRecord
        
        # Test validation catches invalid data
        with pytest.raises(ValueError, match="coffee_dose_grams must be between"):
            BrewRecord(
                brew_id="invalid", bean_name="Test", brew_date=date.today(),
                coffee_dose_grams=100.0,  # Too high
                water_volume_ml=300, final_tds_percent=1.25, final_brew_mass_grams=280.0
            )
        
        with pytest.raises(ValueError, match="final_tds_percent must be between"):
            BrewRecord(
                brew_id="invalid", bean_name="Test", brew_date=date.today(),
                coffee_dose_grams=18.0, water_volume_ml=300,
                final_tds_percent=5.0,  # Too high
                final_brew_mass_grams=280.0
            )
    
    def test_backup_functionality(self):
        """Test new backup functionality not in original application"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_data.csv"
            
            # Create some test data
            test_data = pd.DataFrame([{
                'brew_id': 'backup_test',
                'bean_name': 'Test Bean',
                'coffee_dose_grams': 18.0
            }])
            
            service = CoffeeDataService(str(test_file))
            service.repository.save_data(test_data)
            
            # Test backup creation
            success = service.backup_data("test")
            assert success is True
            
            # Check backup file exists (look specifically for backup files)
            backup_files = list(Path(temp_dir).glob("*backup_*.csv"))
            assert len(backup_files) == 1
            
            # Verify backup contains same data
            backup_data = pd.read_csv(backup_files[0])
            assert len(backup_data) == 1
            assert backup_data.iloc[0]['brew_id'] == 'backup_test'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])