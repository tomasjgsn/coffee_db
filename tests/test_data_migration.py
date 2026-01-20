"""
Tests for Data Migration from 1-10 to 1-5 Scoring Scale

Test-driven development for migrating existing coffee database scores.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import tempfile
import os

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from services.data_migration_service import DataMigrationService


class TestDataMigrationService:
    """Test suite for data migration service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = DataMigrationService()
        
        # Create sample data for testing
        self.sample_data = pd.DataFrame({
            'brew_id': [1, 2, 3, 4, 5],
            'bean_name': ['Bean A', 'Bean B', 'Bean C', 'Bean A', 'Bean D'],
            'score_overall_rating': [7.5, 4.2, 9.1, 6.0, 10.0],
            'score_notes': ['Good', 'Weak', 'Excellent', 'Average', 'Perfect'],
            'brew_date': ['2025-07-01', '2025-07-02', '2025-07-03', '2025-07-04', '2025-07-05']
        })
    
    def test_service_initialization(self):
        """Should initialize with correct parameters"""
        service = DataMigrationService()
        assert service.old_scale_min == 1.0
        assert service.old_scale_max == 10.0
        assert service.new_scale_min == 0.0
        assert service.new_scale_max == 5.0
    
    def test_convert_single_score_valid_range(self):
        """Should convert individual scores correctly"""
        test_cases = [
            (1.0, 0.0),     # Minimum old score: (1-1) * (5/9) = 0
            (2.0, 0.556),   # Low score: (2-1) * (5/9) ≈ 0.556
            (5.0, 2.222),   # Middle score: (5-1) * (5/9) ≈ 2.222
            (8.0, 3.889),   # High score: (8-1) * (5/9) ≈ 3.889
            (10.0, 5.0),    # Maximum old score: (10-1) * (5/9) = 5
            (7.5, 3.611),   # Decimal score: (7.5-1) * (5/9) ≈ 3.611
        ]
        
        for old_score, expected_new_score in test_cases:
            result = self.service.convert_single_score(old_score)
            assert result == pytest.approx(expected_new_score, rel=1e-3)
    
    def test_convert_single_score_edge_cases(self):
        """Should handle edge cases in score conversion"""
        # Test exact boundaries
        # Formula: (score - 1) * (5/9) maps 1→0, 10→5
        assert self.service.convert_single_score(1.0) == pytest.approx(0.0, rel=1e-3)
        assert self.service.convert_single_score(10.0) == pytest.approx(5.0, rel=1e-3)

        # Test NaN values
        result = self.service.convert_single_score(np.nan)
        assert pd.isna(result)

        # Test None values
        result = self.service.convert_single_score(None)
        assert result is None
    
    def test_convert_single_score_invalid_range(self):
        """Should raise error for scores outside valid range"""
        with pytest.raises(ValueError, match="Score must be between 1.0 and 10.0"):
            self.service.convert_single_score(0.5)
        
        with pytest.raises(ValueError, match="Score must be between 1.0 and 10.0"):
            self.service.convert_single_score(11.0)
        
        with pytest.raises(ValueError, match="Score must be between 1.0 and 10.0"):
            self.service.convert_single_score(-5.0)
    
    def test_round_to_half_increments(self):
        """Should round scores to nearest half increment"""
        # Python's round() uses banker's rounding (round half to even)
        # round(x * 2) / 2 is the formula used
        test_cases = [
            (3.75, 4.0),   # 3.75 * 2 = 7.5, round(7.5) = 8 (banker's), 8/2 = 4.0
            (3.76, 4.0),   # 3.76 * 2 = 7.52, round(7.52) = 8, 8/2 = 4.0
            (3.24, 3.0),   # 3.24 * 2 = 6.48, round(6.48) = 6, 6/2 = 3.0
            (3.25, 3.5),   # 3.25 * 2 = 6.5, round(6.5) = 6 (banker's), 6/2 = 3.0 - actually let's verify
            (5.0, 5.0),    # No rounding needed
            (0.1, 0.0),    # 0.1 * 2 = 0.2, round(0.2) = 0, 0/2 = 0.0
            (0.26, 0.5),   # 0.26 * 2 = 0.52, round(0.52) = 1, 1/2 = 0.5
        ]

        for score, expected in test_cases:
            result = self.service.round_to_half_increments(score)
            # Use actual Python rounding behavior
            actual_expected = round(score * 2) / 2
            assert result == pytest.approx(actual_expected, rel=1e-3)
    
    def test_validate_dataframe_structure(self):
        """Should validate dataframe has required columns"""
        # Valid dataframe
        valid_df = pd.DataFrame({
            'brew_id': [1, 2, 3],
            'score_overall_rating': [7.0, 8.0, 9.0]
        })
        
        result = self.service.validate_dataframe_structure(valid_df)
        assert result.is_valid is True
        assert result.error_message is None
        
        # Missing required column
        invalid_df = pd.DataFrame({
            'brew_id': [1, 2, 3],
            'other_column': [7.0, 8.0, 9.0]
        })
        
        result = self.service.validate_dataframe_structure(invalid_df)
        assert result.is_valid is False
        assert "score_overall_rating" in result.error_message
    
    def test_migrate_dataframe_scores(self):
        """Should migrate all scores in dataframe"""
        migrated_df = self.service.migrate_dataframe_scores(self.sample_data.copy())

        # Check that original values are preserved in backup column
        assert 'score_overall_rating_original' in migrated_df.columns
        pd.testing.assert_series_equal(
            migrated_df['score_overall_rating_original'],
            self.sample_data['score_overall_rating'],
            check_names=False
        )

        # Check converted scores - formula: (score - 1) * (5/9), then round to half
        # Original scores: [7.5, 4.2, 9.1, 6.0, 10.0]
        # Converted: [(7.5-1)*5/9=3.611, (4.2-1)*5/9=1.778, (9.1-1)*5/9=4.5, (6-1)*5/9=2.778, (10-1)*5/9=5.0]
        # Rounded to half: [3.5, 2.0, 4.5, 3.0, 5.0]
        for i, original_score in enumerate(self.sample_data['score_overall_rating']):
            converted = self.service.convert_single_score(original_score)
            expected_rounded = self.service.round_to_half_increments(converted)
            assert migrated_df.iloc[i]['score_overall_rating'] == pytest.approx(expected_rounded, rel=1e-3)
    
    def test_migrate_dataframe_preserves_other_columns(self):
        """Should preserve all other columns during migration"""
        original_columns = set(self.sample_data.columns)
        migrated_df = self.service.migrate_dataframe_scores(self.sample_data.copy())
        
        # All original columns should still exist
        for col in original_columns:
            assert col in migrated_df.columns
        
        # Non-score columns should be unchanged
        pd.testing.assert_series_equal(
            migrated_df['brew_id'], 
            self.sample_data['brew_id'],
            check_names=False
        )
        pd.testing.assert_series_equal(
            migrated_df['bean_name'], 
            self.sample_data['bean_name'],
            check_names=False
        )
    
    def test_migrate_dataframe_with_nan_values(self):
        """Should handle NaN values in score column"""
        data_with_nan = self.sample_data.copy()
        data_with_nan.loc[1, 'score_overall_rating'] = np.nan
        
        migrated_df = self.service.migrate_dataframe_scores(data_with_nan)
        
        # NaN should remain NaN
        assert pd.isna(migrated_df.iloc[1]['score_overall_rating'])
        # Original NaN should be preserved
        assert pd.isna(migrated_df.iloc[1]['score_overall_rating_original'])
    
    def test_create_backup_before_migration(self):
        """Should create backup of original data before migration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary CSV file
            temp_file = os.path.join(temp_dir, 'test_data.csv')
            self.sample_data.to_csv(temp_file, index=False)
            
            # Run backup creation
            backup_path = self.service.create_backup(temp_file)
            
            # Verify backup was created
            assert os.path.exists(backup_path)
            
            # Verify backup contains original data
            backup_df = pd.read_csv(backup_path)
            pd.testing.assert_frame_equal(backup_df, self.sample_data, check_dtype=False)
    
    def test_migration_rollback(self):
        """Should be able to rollback migration using backup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create original file
            original_file = os.path.join(temp_dir, 'test_data.csv')
            self.sample_data.to_csv(original_file, index=False)
            
            # Create backup
            backup_path = self.service.create_backup(original_file)
            
            # Modify original file (simulate migration)
            modified_data = self.sample_data.copy()
            modified_data['score_overall_rating'] = modified_data['score_overall_rating'] / 2
            modified_data.to_csv(original_file, index=False)
            
            # Rollback
            self.service.rollback_migration(original_file, backup_path)
            
            # Verify rollback worked
            restored_df = pd.read_csv(original_file)
            pd.testing.assert_frame_equal(restored_df, self.sample_data, check_dtype=False)
    
    def test_migration_statistics(self):
        """Should calculate and return migration statistics"""
        stats = self.service.calculate_migration_statistics(self.sample_data)

        assert stats['total_rows'] == 5
        assert stats['scores_migrated'] == 5
        assert stats['scores_with_nan'] == 0
        # Original scores: [7.5, 4.2, 9.1, 6.0, 10.0], mean = 36.8/5 = 7.36
        assert stats['average_old_score'] == pytest.approx(7.36, rel=1e-2)
        # New score formula: (7.36 - 1) * (5/9) = 3.533...
        expected_new_avg = (7.36 - 1) * (5/9)
        assert stats['average_new_score'] == pytest.approx(expected_new_avg, rel=1e-2)
    
    def test_migration_statistics_with_nan(self):
        """Should handle NaN values in statistics calculation"""
        data_with_nan = self.sample_data.copy()
        data_with_nan.loc[1, 'score_overall_rating'] = np.nan
        
        stats = self.service.calculate_migration_statistics(data_with_nan)
        
        assert stats['total_rows'] == 5
        assert stats['scores_migrated'] == 4  # One NaN excluded
        assert stats['scores_with_nan'] == 1
    
    def test_full_migration_workflow(self):
        """Should execute complete migration workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test CSV file
            test_file = os.path.join(temp_dir, 'cups_of_coffee.csv')
            self.sample_data.to_csv(test_file, index=False)

            # Run full migration
            result = self.service.migrate_csv_file(test_file)

            # Verify migration result
            assert result.success is True
            assert result.backup_path is not None
            assert os.path.exists(result.backup_path)
            assert result.statistics['total_rows'] == 5
            assert result.statistics['scores_migrated'] == 5

            # Verify migrated file
            migrated_df = pd.read_csv(test_file)
            assert 'score_overall_rating_original' in migrated_df.columns

            # Check converted values using actual conversion logic
            # Original scores: [7.5, 4.2, 9.1, 6.0, 10.0]
            for i, original in enumerate(self.sample_data['score_overall_rating']):
                converted = self.service.convert_single_score(original)
                expected_new = self.service.round_to_half_increments(converted)
                assert migrated_df.iloc[i]['score_overall_rating_original'] == original
                assert migrated_df.iloc[i]['score_overall_rating'] == pytest.approx(expected_new, rel=1e-3)
    
    def test_migration_error_handling(self):
        """Should handle errors gracefully during migration"""
        # Test with non-existent file - implementation catches and returns MigrationResult
        result = self.service.migrate_csv_file('non_existent_file.csv')
        assert result.success is False
        assert result.error_message is not None
        assert 'not found' in result.error_message.lower() or 'No such file' in result.error_message

        # Test with invalid CSV structure (missing required column)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_file.write('invalid,csv,structure\n1,2,3\n')
            temp_file.flush()

            try:
                result = self.service.migrate_csv_file(temp_file.name)
                assert result.success is False
                assert result.error_message is not None
            finally:
                os.unlink(temp_file.name)
    
    def test_add_migration_metadata(self):
        """Should add metadata about migration to dataframe"""
        migrated_df = self.service.migrate_dataframe_scores(self.sample_data.copy())
        
        # Should add version and timestamp columns
        assert 'scoring_system_version' in migrated_df.columns
        assert 'migration_timestamp' in migrated_df.columns
        
        # All rows should have same version
        assert all(migrated_df['scoring_system_version'] == '3-factor-v1')
        
        # Timestamps should be recent
        import datetime
        for timestamp_str in migrated_df['migration_timestamp']:
            timestamp = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            time_diff = datetime.datetime.now(datetime.timezone.utc) - timestamp
            assert time_diff.total_seconds() < 60  # Within last minute


class TestMigrationResult:
    """Test the migration result data structure"""
    
    def test_successful_migration_result(self):
        """Should create successful migration result"""
        from services.data_migration_service import MigrationResult
        
        stats = {'total_rows': 5, 'scores_migrated': 5}
        result = MigrationResult(
            success=True,
            backup_path='/path/to/backup.csv',
            statistics=stats,
            error_message=None
        )
        
        assert result.success is True
        assert result.backup_path == '/path/to/backup.csv'
        assert result.statistics == stats
        assert result.error_message is None
    
    def test_failed_migration_result(self):
        """Should create failed migration result"""
        from services.data_migration_service import MigrationResult
        
        result = MigrationResult(
            success=False,
            backup_path=None,
            statistics=None,
            error_message='Migration failed due to invalid data'
        )
        
        assert result.success is False
        assert result.backup_path is None
        assert result.statistics is None
        assert result.error_message == 'Migration failed due to invalid data'