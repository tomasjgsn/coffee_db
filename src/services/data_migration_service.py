"""
Data Migration Service

Handles migration of existing coffee database from 1-10 scoring scale to 1-5 scale
with comprehensive backup and rollback capabilities.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union
from pathlib import Path
import shutil
from datetime import datetime
import logging


@dataclass
class ValidationResult:
    """Result of dataframe structure validation"""
    is_valid: bool
    error_message: Optional[str] = None


@dataclass 
class MigrationResult:
    """Result of data migration operation"""
    success: bool
    backup_path: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class DataMigrationService:
    """Service for migrating coffee database scoring system"""
    
    def __init__(self):
        """Initialize migration service"""
        self.old_scale_min = 1.0
        self.old_scale_max = 10.0
        self.new_scale_min = 0.0
        self.new_scale_max = 5.0
        # Conversion factor for 1-10 to 0-5 scale: (5-0)/(10-1) = 5/9
        self.conversion_factor = (self.new_scale_max - self.new_scale_min) / (self.old_scale_max - self.old_scale_min)
        self.logger = logging.getLogger(__name__)
    
    def convert_single_score(self, score: Union[float, int, None]) -> Union[float, None]:
        """Convert a single score from 1-10 scale to 0-5 scale"""
        if pd.isna(score) or score is None:
            return None if score is None else np.nan
        
        if not isinstance(score, (int, float)):
            raise ValueError(f"Score must be a number, got {type(score)}")
        
        if score < self.old_scale_min or score > self.old_scale_max:
            raise ValueError(f"Score must be between {self.old_scale_min} and {self.old_scale_max}, got {score}")
        
        # Convert: 1-10 scale to true 0-5 scale
        # Formula: (score - old_min) * conversion_factor maps 1→0, 5.5→2.5, 10→5.0
        new_score = (score - self.old_scale_min) * self.conversion_factor
        
        return round(new_score, 3)
    
    def round_to_half_increments(self, score: float) -> float:
        """Round score to nearest half increment (0.5, 1.0, 1.5, etc.)"""
        return round(score * 2) / 2
    
    def validate_dataframe_structure(self, df: pd.DataFrame) -> ValidationResult:
        """Validate that dataframe has required columns for migration"""
        required_columns = ['score_overall_rating']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return ValidationResult(
                False, 
                f"Missing required columns: {missing_columns}"
            )
        
        return ValidationResult(True)
    
    def migrate_dataframe_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Migrate scores in dataframe from 1-10 to 1-5 scale"""
        # Validate structure
        validation = self.validate_dataframe_structure(df)
        if not validation.is_valid:
            raise ValueError(validation.error_message)
        
        # Create a copy to avoid modifying original
        migrated_df = df.copy()
        
        # Backup original scores
        migrated_df['score_overall_rating_original'] = migrated_df['score_overall_rating']
        
        # Convert scores
        def convert_and_round(score):
            if pd.isna(score):
                return np.nan
            try:
                converted = self.convert_single_score(score)
                if converted is None:
                    return np.nan
                return self.round_to_half_increments(converted)
            except ValueError:
                self.logger.warning(f"Could not convert score {score}, keeping as NaN")
                return np.nan
        
        migrated_df['score_overall_rating'] = migrated_df['score_overall_rating'].apply(convert_and_round)
        
        # Add migration metadata
        migrated_df['scoring_system_version'] = '3-factor-v1'
        migrated_df['migration_timestamp'] = datetime.now().isoformat() + 'Z'
        
        return migrated_df
    
    def create_backup(self, file_path: str) -> str:
        """Create backup of original file before migration"""
        file_path_obj = Path(file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_path_obj.stem}_backup_{timestamp}{file_path_obj.suffix}"
        backup_path = file_path_obj.parent / backup_name
        
        shutil.copy2(file_path, backup_path)
        self.logger.info(f"Created backup at {backup_path}")
        
        return str(backup_path)
    
    def rollback_migration(self, file_path: str, backup_path: str) -> None:
        """Rollback migration by restoring from backup"""
        if not Path(backup_path).exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        shutil.copy2(backup_path, file_path)
        self.logger.info(f"Rolled back migration from backup {backup_path}")
    
    def calculate_migration_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistics about the migration"""
        total_rows = len(df)
        scores_column = df['score_overall_rating']
        
        # Count valid scores (not NaN)
        valid_scores = scores_column.dropna()
        scores_migrated = len(valid_scores)
        scores_with_nan = total_rows - scores_migrated
        
        # Calculate averages
        if scores_migrated > 0:
            average_old_score = valid_scores.mean()
            # Convert to new scale for comparison using conversion factor
            average_new_score = (average_old_score - self.old_scale_min) * self.conversion_factor if not pd.isna(average_old_score) else 0
        else:
            average_old_score = 0
            average_new_score = 0
        
        return {
            'total_rows': total_rows,
            'scores_migrated': scores_migrated,
            'scores_with_nan': scores_with_nan,
            'average_old_score': round(average_old_score, 2) if average_old_score else 0,
            'average_new_score': round(average_new_score, 2) if average_new_score else 0,
        }
    
    def migrate_csv_file(self, file_path: str) -> MigrationResult:
        """Migrate an entire CSV file from old to new scoring system"""
        try:
            # Validate file exists
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Load data
            df = pd.read_csv(file_path)
            
            # Validate structure
            validation = self.validate_dataframe_structure(df)
            if not validation.is_valid:
                return MigrationResult(
                    success=False,
                    error_message=validation.error_message
                )
            
            # Calculate pre-migration statistics
            pre_migration_stats = self.calculate_migration_statistics(df)
            
            # Create backup
            backup_path = self.create_backup(file_path)
            
            # Perform migration
            migrated_df = self.migrate_dataframe_scores(df)
            
            # Save migrated data
            migrated_df.to_csv(file_path, index=False)
            
            # Calculate final statistics
            final_stats = self.calculate_migration_statistics(df)  # Use original for old scores
            final_stats.update({
                'backup_created': True,
                'backup_path': backup_path
            })
            
            self.logger.info(f"Successfully migrated {file_path}")
            
            return MigrationResult(
                success=True,
                backup_path=backup_path,
                statistics=final_stats
            )
            
        except Exception as e:
            self.logger.error(f"Migration failed: {str(e)}")
            return MigrationResult(
                success=False,
                error_message=str(e)
            )