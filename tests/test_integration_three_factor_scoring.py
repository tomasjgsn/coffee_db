"""
Integration Tests for Three-Factor Scoring System

End-to-end tests to verify the complete workflow from UI to data storage.
"""

import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from services.three_factor_scoring_service import ThreeFactorScoringService
from services.data_migration_service import DataMigrationService
from services.form_handling_service import FormHandlingService
from services.data_management_service import DataManagementService


class TestThreeFactorScoringIntegration:
    """Integration tests for the three-factor scoring system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.scoring_service = ThreeFactorScoringService()
        self.migration_service = DataMigrationService()
        self.form_service = FormHandlingService()
        
        # Create sample data with both old and new scoring systems
        self.sample_data = pd.DataFrame({
            'brew_id': [1, 2, 3, 4],
            'bean_name': ['Bean A', 'Bean B', 'Bean A', 'Bean C'],
            'brew_date': ['2025-07-01', '2025-07-02', '2025-07-03', '2025-07-04'],
            'score_overall_rating': [7.5, 4.2, 9.1, 6.0],  # Old 1-10 scale
            'score_notes': ['Good', 'Weak', 'Excellent', 'Average'],
            'coffee_dose_grams': [15.0, 16.0, 14.5, 15.5],
            'water_volume_ml': [250.0, 260.0, 240.0, 255.0]
        })
    
    def test_end_to_end_new_entry_workflow(self):
        """Test complete workflow for adding new entry with three-factor scoring"""
        # 1. Create form data with three-factor scores
        form_data = {
            'brew_date': '2025-08-30',
            'bean_name': 'Test Bean',
            'bean_origin_country': 'Colombia',
            'bean_origin_region': 'Huila',
            'bean_variety': 'Arabica',
            'bean_process_method': 'Washed',
            'bean_roast_date': '2025-08-20',
            'bean_roast_level': 'Medium',
            'bean_notes': 'Fruity, bright',
            'coffee_dose_grams': 15.0,
            'water_volume_ml': 250.0,
            'water_temp_degC': 95.0,
            'brew_total_time_s': 180.0,
            'final_tds_percent': 1.2,
            'score_complexity': 4.0,
            'score_bitterness': 3.5,
            'score_mouthfeel': 4.5,
            'score_notes': 'Complex flavors with balanced bitterness',
            'score_flavor_profile_category': 'Fruity',
            'scoring_system_version': '3-factor-v1'
        }
        
        # 2. Calculate overall score using scoring service
        scores = {
            'complexity': form_data['score_complexity'],
            'bitterness': form_data['score_bitterness'],
            'mouthfeel': form_data['score_mouthfeel']
        }
        
        overall_score = self.scoring_service.calculate_overall_score(scores)
        form_data['score_overall_rating'] = overall_score
        
        # 3. Validate scores
        validation = self.scoring_service.validate_all_scores(scores)
        assert validation.is_valid, f"Validation failed: {validation.errors}"
        
        # 4. Prepare brew record using form service
        brew_record = self.form_service.prepare_brew_record(form_data, 99, 250.0)
        
        # 5. Verify the record contains all three-factor scoring fields
        assert 'score_complexity' in brew_record
        assert 'score_bitterness' in brew_record
        assert 'score_mouthfeel' in brew_record
        assert 'scoring_system_version' in brew_record
        
        assert brew_record['score_complexity'] == 4.0
        assert brew_record['score_bitterness'] == 3.5
        assert brew_record['score_mouthfeel'] == 4.5
        assert brew_record['scoring_system_version'] == '3-factor-v1'
        
        # 6. Verify overall score calculation
        expected_overall = (4.0 + 3.5 + 4.5) / 3
        assert abs(brew_record['score_overall_rating'] - expected_overall) < 0.001
        
        # 7. Verify export functionality
        exported = self.scoring_service.export_scores_to_dict(scores)
        assert exported['score_complexity'] == 4.0
        assert exported['score_bitterness'] == 3.5
        assert exported['score_mouthfeel'] == 4.5
        assert exported['scoring_system_version'] == '3-factor-v1'
    
    def test_data_migration_and_backwards_compatibility(self):
        """Test that old data migrates correctly and new data works alongside"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            # Write old format data
            self.sample_data.to_csv(temp_file.name, index=False)
            
            try:
                # Migrate data
                migration_result = self.migration_service.migrate_csv_file(temp_file.name)
                assert migration_result.success, f"Migration failed: {migration_result.error_message}"
                
                # Load migrated data
                migrated_df = pd.read_csv(temp_file.name)
                
                # Verify migration
                assert 'score_overall_rating_original' in migrated_df.columns
                assert 'scoring_system_version' in migrated_df.columns
                assert 'migration_timestamp' in migrated_df.columns
                
                # Verify score conversions (1-10 to 0-5 scale)
                original_scores = [7.5, 4.2, 9.1, 6.0]
                expected_new_scores = [4.0, 2.0, 4.5, 3.0]  # Rounded to half increments
                
                for i, (original, expected) in enumerate(zip(original_scores, expected_new_scores)):
                    assert migrated_df.iloc[i]['score_overall_rating_original'] == original
                    assert abs(migrated_df.iloc[i]['score_overall_rating'] - expected) < 0.1
                
                # Add new entry with three-factor scoring
                new_data = {
                    'brew_id': 5,
                    'bean_name': 'New Bean',
                    'brew_date': '2025-08-30',
                    'score_overall_rating': 3.8,  # New 0-5 scale
                    'score_complexity': 4.0,
                    'score_bitterness': 3.5,
                    'score_mouthfeel': 4.0,
                    'scoring_system_version': '3-factor-v1',
                    'coffee_dose_grams': 15.0,
                    'water_volume_ml': 250.0
                }
                
                # Append new data
                new_df = pd.concat([migrated_df, pd.DataFrame([new_data])], ignore_index=True)
                new_df.to_csv(temp_file.name, index=False)
                
                # Verify mixed data loads correctly
                final_df = pd.read_csv(temp_file.name)
                assert len(final_df) == 5
                
                # Check last entry has three-factor scores
                last_entry = final_df.iloc[-1]
                assert last_entry['score_complexity'] == 4.0
                assert last_entry['score_bitterness'] == 3.5
                assert last_entry['score_mouthfeel'] == 4.0
                assert last_entry['scoring_system_version'] == '3-factor-v1'
                
                # Check migrated entries have migration metadata
                for i in range(4):  # First 4 were migrated
                    entry = final_df.iloc[i]
                    assert entry['scoring_system_version'] == '3-factor-v1'
                    assert pd.notna(entry['migration_timestamp'])
                
            finally:
                os.unlink(temp_file.name)
                if migration_result.backup_path and os.path.exists(migration_result.backup_path):
                    os.unlink(migration_result.backup_path)
    
    def test_score_validation_workflow(self):
        """Test complete validation workflow"""
        # Valid scores
        valid_scores = {
            'complexity': 3.5,
            'bitterness': 4.0,
            'mouthfeel': 2.5
        }
        
        validation = self.scoring_service.validate_all_scores(valid_scores)
        assert validation.is_valid
        assert len(validation.errors) == 0
        
        overall = self.scoring_service.calculate_overall_score(valid_scores)
        assert overall == pytest.approx(3.333, rel=1e-3)
        
        # Invalid scores
        invalid_scores = {
            'complexity': 6.0,  # Too high
            'bitterness': -1.0,  # Too low
            'mouthfeel': 2.3    # Invalid increment
        }
        
        validation = self.scoring_service.validate_all_scores(invalid_scores)
        assert not validation.is_valid
        assert len(validation.errors) == 3
        assert 'complexity' in validation.errors
        assert 'bitterness' in validation.errors
        assert 'mouthfeel' in validation.errors
        
        # Should raise error when trying to calculate with invalid scores
        with pytest.raises(ValueError):
            self.scoring_service.calculate_overall_score(invalid_scores)
    
    def test_legacy_conversion_accuracy(self):
        """Test legacy score conversion accuracy"""
        # Test key conversion points
        conversion_tests = [
            (1.0, 0.5),    # Min old -> min new
            (2.0, 1.0),    # Low score
            (5.0, 2.5),    # Mid score
            (8.0, 4.0),    # High score
            (10.0, 5.0),   # Max old -> max new
            (7.5, 3.75),   # Decimal case
        ]
        
        for old_score, expected_new in conversion_tests:
            converted = self.scoring_service.convert_legacy_score(old_score)
            assert converted == pytest.approx(expected_new, rel=1e-3)
            
            # Test rounding to half increments
            rounded = self.migration_service.round_to_half_increments(converted)
            expected_rounded = round(expected_new * 2) / 2
            assert rounded == expected_rounded
    
    def test_csv_handling_with_three_factor_scores(self):
        """Test CSV file handling with three-factor scores"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            # Create data with three-factor scores
            three_factor_data = pd.DataFrame({
                'brew_id': [1, 2, 3],
                'bean_name': ['Bean A', 'Bean B', 'Bean C'],
                'brew_date': ['2025-08-01', '2025-08-02', '2025-08-03'],
                'score_overall_rating': [3.5, 4.0, 2.5],
                'score_complexity': [3.0, 4.5, 2.0],
                'score_bitterness': [4.0, 3.5, 3.0],
                'score_mouthfeel': [3.5, 4.0, 2.5],
                'scoring_system_version': ['3-factor-v1', '3-factor-v1', '3-factor-v1'],
                'coffee_dose_grams': [15.0, 16.0, 14.5],
                'water_volume_ml': [250.0, 260.0, 240.0]
            })
            
            three_factor_data.to_csv(temp_file.name, index=False)
            
            try:
                # Load and verify data can be read correctly
                loaded_df = pd.read_csv(temp_file.name)
                
                assert len(loaded_df) == 3
                assert 'score_complexity' in loaded_df.columns
                assert 'score_bitterness' in loaded_df.columns
                assert 'score_mouthfeel' in loaded_df.columns
                assert 'scoring_system_version' in loaded_df.columns
                
                # Verify calculations are consistent
                for i in range(3):
                    row = loaded_df.iloc[i]
                    expected_overall = (row['score_complexity'] + row['score_bitterness'] + row['score_mouthfeel']) / 3
                    assert abs(row['score_overall_rating'] - expected_overall) < 0.1
                
            finally:
                os.unlink(temp_file.name)
    
    def test_score_display_formatting(self):
        """Test score display formatting for UI"""
        # Test whole numbers
        assert self.scoring_service.format_score_display(3.0) == "3"
        assert self.scoring_service.format_score_display(5.0) == "5"
        
        # Test decimals
        assert self.scoring_service.format_score_display(3.5) == "3.5"
        assert self.scoring_service.format_score_display(2.5) == "2.5"
        
        # Test descriptions
        complexity_desc = self.scoring_service.get_score_description("complexity", 4.5)
        assert "high" in complexity_desc.lower()
        
        bitterness_desc = self.scoring_service.get_score_description("bitterness", 2.0)
        assert "medium-low" in bitterness_desc.lower() or "low" in bitterness_desc.lower()
        
        mouthfeel_desc = self.scoring_service.get_score_description("mouthfeel", 3.0)
        assert "medium" in mouthfeel_desc.lower()
    
    def test_error_handling_and_edge_cases(self):
        """Test error handling and edge cases"""
        # Test with None values
        result = self.migration_service.convert_single_score(None)
        assert result is None
        
        # Test with NaN values
        import numpy as np
        result = self.migration_service.convert_single_score(np.nan)
        assert pd.isna(result)
        
        # Test validation with missing scores
        incomplete_scores = {'complexity': 3.0, 'bitterness': 4.0}  # Missing mouthfeel
        validation = self.scoring_service.validate_all_scores(incomplete_scores)
        assert not validation.is_valid
        assert 'mouthfeel' in validation.errors
        
        # Test legacy conversion edge cases
        with pytest.raises(ValueError):
            self.scoring_service.convert_legacy_score(-1.0)
        
        with pytest.raises(ValueError):
            self.scoring_service.convert_legacy_score(11.0)
        
        with pytest.raises(ValueError):
            self.scoring_service.convert_legacy_score(None)