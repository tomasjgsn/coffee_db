"""
Test-Driven Development tests for coffee data models

This module defines tests FIRST before implementing the domain models.
Following TDD principles - write failing tests, then implement to make them pass.
"""

import pytest
from datetime import date, datetime
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List


class TestCoffeeBean:
    """Test suite for CoffeeBean data model"""
    
    def test_coffee_bean_creation(self):
        """Should create a CoffeeBean with required fields"""
        from src.models.coffee_bean import CoffeeBean
        
        bean = CoffeeBean(
            name="La Providencia",
            origin_country="Colombia",
            origin_region=None
        )
        
        assert bean.name == "La Providencia"
        assert bean.origin_country == "Colombia"
        assert bean.origin_region is None
        assert bean.archive_status == "active"  # Default value
    
    def test_coffee_bean_with_optional_fields(self):
        """Should handle optional fields correctly"""
        from src.models.coffee_bean import CoffeeBean
        
        bean = CoffeeBean(
            name="Gold Maria-Isabel",
            origin_country="Colombia", 
            origin_region="Jardin",
            estimated_bag_size_grams=250.0,
            archive_status="archived"
        )
        
        assert bean.name == "Gold Maria-Isabel"
        assert bean.origin_region == "Jardin"
        assert bean.estimated_bag_size_grams == 250.0
        assert bean.archive_status == "archived"
    
    def test_coffee_bean_equality(self):
        """Should compare beans by name, country, and region"""
        from src.models.coffee_bean import CoffeeBean
        
        bean1 = CoffeeBean("Test Bean", "Ethiopia", "Yirgacheffe")
        bean2 = CoffeeBean("Test Bean", "Ethiopia", "Yirgacheffe")
        bean3 = CoffeeBean("Test Bean", "Ethiopia", "Sidamo")
        
        assert bean1 == bean2
        assert bean1 != bean3
    
    def test_coffee_bean_validation(self):
        """Should validate required fields"""
        from src.models.coffee_bean import CoffeeBean
        
        with pytest.raises(ValueError, match="name is required"):
            CoffeeBean("", "Colombia", None)
        
        with pytest.raises(ValueError, match="origin_country is required"):
            CoffeeBean("Test Bean", "", None)
    
    def test_coffee_bean_from_dict(self):
        """Should create bean from dictionary (for CSV loading)"""
        from src.models.coffee_bean import CoffeeBean
        
        data = {
            'bean_name': 'Test Bean',
            'bean_origin_country': 'Ethiopia',
            'bean_origin_region': 'Yirgacheffe',
            'estimated_bag_size_grams': 250.0,
            'archive_status': 'active'
        }
        
        bean = CoffeeBean.from_dict(data)
        assert bean.name == "Test Bean"
        assert bean.origin_country == "Ethiopia"
        assert bean.origin_region == "Yirgacheffe"
        assert bean.estimated_bag_size_grams == 250.0
    
    def test_coffee_bean_to_dict(self):
        """Should convert bean to dictionary (for CSV saving)"""
        from src.models.coffee_bean import CoffeeBean
        
        bean = CoffeeBean("Test Bean", "Ethiopia", "Yirgacheffe", 250.0, "active")
        data = bean.to_dict()
        
        assert data['bean_name'] == "Test Bean"
        assert data['bean_origin_country'] == "Ethiopia"
        assert data['bean_origin_region'] == "Yirgacheffe"
        assert data['estimated_bag_size_grams'] == 250.0
        assert data['archive_status'] == "active"


class TestBrewRecord:
    """Test suite for BrewRecord data model"""
    
    def test_brew_record_creation(self):
        """Should create a BrewRecord with required fields"""
        from src.models.brew_record import BrewRecord
        
        record = BrewRecord(
            brew_id="brew_001",
            bean_name="Test Bean",
            brew_date=date(2025, 1, 15),
            coffee_dose_grams=18.0,
            water_volume_ml=300,
            final_tds_percent=1.25,
            final_brew_mass_grams=280.0
        )
        
        assert record.brew_id == "brew_001"
        assert record.bean_name == "Test Bean"
        assert record.coffee_dose_grams == 18.0
        assert record.water_volume_ml == 300
        assert record.final_tds_percent == 1.25
        assert record.final_brew_mass_grams == 280.0
    
    def test_brew_record_validation(self):
        """Should validate input data ranges"""
        from src.models.brew_record import BrewRecord
        
        # Test coffee dose validation
        with pytest.raises(ValueError, match="coffee_dose_grams must be between"):
            BrewRecord(
                brew_id="test", bean_name="Test", brew_date=date.today(),
                coffee_dose_grams=0, water_volume_ml=300, 
                final_tds_percent=1.25, final_brew_mass_grams=280.0
            )
        
        # Test TDS validation  
        with pytest.raises(ValueError, match="final_tds_percent must be between"):
            BrewRecord(
                brew_id="test", bean_name="Test", brew_date=date.today(),
                coffee_dose_grams=18.0, water_volume_ml=300, 
                final_tds_percent=5.0, final_brew_mass_grams=280.0
            )
    
    def test_brew_record_calculated_fields(self):
        """Should calculate derived metrics automatically"""
        from src.models.brew_record import BrewRecord
        
        record = BrewRecord(
            brew_id="test", bean_name="Test", brew_date=date.today(),
            coffee_dose_grams=18.0, water_volume_ml=300, 
            final_tds_percent=1.25, final_brew_mass_grams=280.0
        )
        
        # Should calculate brew ratio
        assert abs(record.brew_ratio_to_1 - 16.7) < 0.1  # 300/18 ≈ 16.7
        
        # Should calculate extraction yield
        expected_extraction = (280.0 * 1.25) / 18.0  # ≈ 19.4%
        assert abs(record.final_extraction_yield_percent - expected_extraction) < 0.1
    
    def test_brew_record_from_dict(self):
        """Should create record from dictionary (for CSV loading)"""
        from src.models.brew_record import BrewRecord
        
        data = {
            'brew_id': 'brew_001',
            'bean_name': 'Test Bean',
            'brew_date': '2025-01-15',
            'coffee_dose_grams': 18.0,
            'water_volume_ml': 300,
            'final_tds_percent': 1.25,
            'final_brew_mass_grams': 280.0,
            'score_overall_rating': 8.5
        }
        
        record = BrewRecord.from_dict(data)
        assert record.brew_id == "brew_001"
        assert record.brew_date == date(2025, 1, 15)
        assert record.score_overall_rating == 8.5


class TestBrewingCalculations:
    """Test suite for brewing calculation utilities"""
    
    def test_brewing_zone_classification(self):
        """Should classify brewing zones correctly"""
        from src.models.brewing_calculations import classify_brewing_zone
        
        # Test Ideal-Ideal zone
        assert classify_brewing_zone(1.25, 20.0) == "Ideal-Ideal"
        
        # Test Under-Weak zone  
        assert classify_brewing_zone(1.0, 17.0) == "Under-Weak"
        
        # Test Over-Strong zone
        assert classify_brewing_zone(1.5, 23.0) == "Over-Strong"
    
    def test_strength_category(self):
        """Should categorize strength by TDS"""
        from src.models.brewing_calculations import categorize_strength
        
        assert categorize_strength(1.0) == "Weak"
        assert categorize_strength(1.25) == "Ideal"
        assert categorize_strength(1.5) == "Strong"
    
    def test_extraction_category(self):
        """Should categorize extraction by yield percentage"""
        from src.models.brewing_calculations import categorize_extraction
        
        assert categorize_extraction(17.0) == "Under"
        assert categorize_extraction(20.0) == "Ideal" 
        assert categorize_extraction(23.0) == "Over"
    
    def test_brew_score_calculation(self):
        """Should calculate composite brew score"""
        from src.models.brewing_calculations import calculate_brew_score
        
        # Test with Ideal-Ideal zone
        score = calculate_brew_score(8.0, "Ideal-Ideal")
        expected = (8.0 * 0.6) + (10 * 0.4)  # 4.8 + 4.0 = 8.8
        assert abs(score - expected) < 0.1
        
        # Test with missing rating
        score = calculate_brew_score(None, "Ideal-Ideal")
        assert score is None


class TestBeanStatistics:
    """Test suite for bean statistics calculations"""
    
    def test_bean_usage_statistics(self):
        """Should calculate usage statistics for a bean"""
        from src.models.bean_statistics import BeanStatistics
        
        # Create sample data
        records = pd.DataFrame([
            {
                'bean_name': 'Test Bean',
                'coffee_dose_grams': 18.0,
                'brew_date': date(2025, 1, 10),
                'score_overall_rating': 8.0
            },
            {
                'bean_name': 'Test Bean', 
                'coffee_dose_grams': 16.0,
                'brew_date': date(2025, 1, 12),
                'score_overall_rating': 7.5
            }
        ])
        
        stats = BeanStatistics.calculate_for_bean('Test Bean', records)
        
        assert stats.total_brews == 2
        assert stats.total_grams_used == 34.0
        assert stats.avg_rating == 7.75
        assert stats.last_used == date(2025, 1, 12)
        assert stats.days_since_last == (date.today() - date(2025, 1, 12)).days
    
    def test_bean_statistics_with_bag_size(self):
        """Should calculate remaining grams and usage percentage"""
        from src.models.bean_statistics import BeanStatistics
        
        records = pd.DataFrame([{
            'bean_name': 'Test Bean',
            'coffee_dose_grams': 50.0,
            'estimated_bag_size_grams': 250.0,
            'brew_date': date.today(),
            'score_overall_rating': 8.0
        }])
        
        stats = BeanStatistics.calculate_for_bean('Test Bean', records)
        
        assert stats.bag_size == 250.0
        assert stats.remaining_grams == 200.0
        assert stats.usage_percentage == 20.0


class TestDataRepository:
    """Test suite for data access layer"""
    
    def test_load_coffee_data(self):
        """Should load coffee data from CSV"""
        from src.repositories.coffee_data_repository import CoffeeDataRepository
        
        # This test will pass once we implement the repository
        repo = CoffeeDataRepository("data/cups_of_coffee.csv")
        data = repo.load_data()
        
        assert isinstance(data, pd.DataFrame)
    
    def test_save_coffee_data(self):
        """Should save coffee data to CSV"""
        from src.repositories.coffee_data_repository import CoffeeDataRepository
        
        repo = CoffeeDataRepository("data/test_output.csv")
        test_data = pd.DataFrame([{
            'bean_name': 'Test Bean',
            'coffee_dose_grams': 18.0,
            'brew_date': date.today()
        }])
        
        repo.save_data(test_data)
        
        # Verify saved data
        loaded_data = repo.load_data()
        assert len(loaded_data) == 1
        assert loaded_data.iloc[0]['bean_name'] == 'Test Bean'


class TestCoffeeDataService:
    """Test suite for coffee data business logic service"""
    
    def test_get_bean_list(self):
        """Should return list of unique beans"""
        from src.services.coffee_data_service import CoffeeDataService
        
        service = CoffeeDataService("data/cups_of_coffee.csv")
        beans = service.get_bean_list()
        
        assert isinstance(beans, list)
        assert len(beans) > 0
    
    def test_archive_bean(self):
        """Should archive a bean and all its records"""  
        from src.services.coffee_data_service import CoffeeDataService
        from src.models.brew_record import BrewRecord
        
        service = CoffeeDataService("data/test_archive.csv")
        
        # First add a test record
        record = BrewRecord(
            brew_id="test_archive", bean_name="Test Bean", brew_date=date.today(),
            coffee_dose_grams=18.0, water_volume_ml=300, 
            final_tds_percent=1.25, final_brew_mass_grams=280.0
        )
        
        # Create test data with bean info
        test_data = pd.DataFrame([{
            'brew_id': 'test_archive',
            'bean_name': 'Test Bean',
            'bean_origin_country': 'Ethiopia',
            'bean_origin_region': 'Yirgacheffe',
            'brew_date': date.today(),
            'coffee_dose_grams': 18.0,
            'water_volume_ml': 300,
            'final_tds_percent': 1.25,
            'final_brew_mass_grams': 280.0,
            'archive_status': 'active'
        }])
        
        service.repository.save_data(test_data)
        
        # Now test archiving
        result = service.archive_bean("Test Bean", "Ethiopia", "Yirgacheffe")
        assert result is True
    
    def test_add_brew_record(self):
        """Should add new brew record with validation"""
        from src.services.coffee_data_service import CoffeeDataService
        from src.models.brew_record import BrewRecord
        
        service = CoffeeDataService("data/cups_of_coffee.csv")
        
        record = BrewRecord(
            brew_id="new_brew", bean_name="Test Bean", brew_date=date.today(),
            coffee_dose_grams=18.0, water_volume_ml=300, 
            final_tds_percent=1.25, final_brew_mass_grams=280.0
        )
        
        success = service.add_brew_record(record)
        assert success is True