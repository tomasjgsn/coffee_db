"""
Data Management Service

Handles data loading, saving, validation, and post-processing operations.
Extracted from main application to improve separation of concerns.
"""

import pandas as pd
import csv
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from .brew_id_service import BrewIdService


class DataManagementService:
    """Service for handling data operations, file I/O, and processing"""
    
    def __init__(self, csv_file_path: Union[str, Path] = "data/cups_of_coffee.csv"):
        self.csv_file = Path(csv_file_path)
        self.brew_id_service = BrewIdService()
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(f"{__name__}.DataManagementService")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def load_data(self) -> pd.DataFrame:
        """
        Load data from csv file with proper type handling
        
        Returns:
            DataFrame with loaded and cleaned data
        """
        try:
            # Load with proper CSV quoting
            df = pd.read_csv(self.csv_file, quoting=csv.QUOTE_MINIMAL)
            
            # Clean and fix brew_id column
            if 'brew_id' in df.columns:
                # Convert to numeric, invalid values become NaN
                df['brew_id'] = pd.to_numeric(df['brew_id'], errors='coerce')
                
                # Find records with invalid brew_id (now NaN)
                invalid_mask = df['brew_id'].isna()
                if invalid_mask.any():
                    # Get the next valid ID to assign to invalid records
                    max_valid_id = df.loc[~invalid_mask, 'brew_id'].max()
                    next_id = int(max_valid_id + 1) if pd.notna(max_valid_id) else 1
                    
                    # Assign sequential IDs to invalid records
                    num_invalid = invalid_mask.sum()
                    df.loc[invalid_mask, 'brew_id'] = list(range(next_id, next_id + num_invalid))
                    
                    self.logger.info(f"Fixed {num_invalid} invalid brew_id values, assigned IDs {next_id}-{next_id + num_invalid - 1}")
                
                # Convert to integer type
                df['brew_id'] = df['brew_id'].astype('Int64')
            
            # Convert date columns
            if 'brew_date' in df.columns:
                df['brew_date'] = pd.to_datetime(df['brew_date']).dt.date
            if 'bean_purchase_date' in df.columns:
                df['bean_purchase_date'] = pd.to_datetime(df['bean_purchase_date'], errors='coerce').dt.date
            if 'bean_harvest_date' in df.columns:
                df['bean_harvest_date'] = pd.to_datetime(df['bean_harvest_date'], errors='coerce').dt.date
            
            self.logger.info(f"Loaded {len(df)} records from {self.csv_file}")
            return df
            
        except FileNotFoundError:
            self.logger.warning(f"CSV file not found: {self.csv_file}. Creating empty DataFrame.")
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def save_data(self, df: pd.DataFrame) -> bool:
        """
        Save DataFrame back to CSV file
        
        Args:
            df: DataFrame to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate brew_id before saving
            if 'brew_id' in df.columns:
                invalid_ids = df['brew_id'].isna() | (df['brew_id'] < 1)
                if invalid_ids.any():
                    self.logger.error(f"Cannot save: {invalid_ids.sum()} records have invalid brew_id values")
                    return False
            
            # Prepare a copy for saving to handle date fields properly
            df_to_save = df.copy()
            
            # Convert date columns back to strings for CSV saving to avoid NaN/float issues
            date_columns = ['bean_purchase_date', 'bean_harvest_date']
            for col in date_columns:
                if col in df_to_save.columns:
                    # Convert NaT (pandas null dates) to empty strings
                    df_to_save[col] = df_to_save[col].astype(str).replace('NaT', '')
            
            # Ensure directory exists
            self.csv_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with proper CSV quoting
            df_to_save.to_csv(self.csv_file, index=False, quoting=csv.QUOTE_MINIMAL)
            self.logger.info(f"Data saved to {self.csv_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
            return False
    
    def add_record(self, df: pd.DataFrame, new_record: Dict[str, Any]) -> pd.DataFrame:
        """
        Add a new record to the DataFrame
        
        Args:
            df: Existing DataFrame
            new_record: New record to add
            
        Returns:
            Updated DataFrame
        """
        try:
            if df.empty:
                new_df = pd.DataFrame([new_record])
            else:
                new_df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            
            self.logger.info(f"Added new record with brew_id: {new_record.get('brew_id', 'unknown')}")
            return new_df
            
        except Exception as e:
            self.logger.error(f"Error adding record: {e}")
            return df
    
    def delete_record(self, df: pd.DataFrame, brew_id: int) -> pd.DataFrame:
        """
        Delete a record from the DataFrame
        
        Args:
            df: DataFrame to modify
            brew_id: ID of record to delete
            
        Returns:
            Updated DataFrame
        """
        try:
            initial_count = len(df)
            updated_df = df[df['brew_id'] != brew_id].reset_index(drop=True)
            deleted_count = initial_count - len(updated_df)
            
            if deleted_count > 0:
                self.logger.info(f"Deleted {deleted_count} record(s) with brew_id: {brew_id}")
            else:
                self.logger.warning(f"No records found with brew_id: {brew_id}")
            
            return updated_df
            
        except Exception as e:
            self.logger.error(f"Error deleting record: {e}")
            return df
    
    def run_post_processing(self, selective: bool = True, show_stats: bool = True) -> Tuple[bool, str, str]:
        """
        Run the post-processing script after saving data
        
        Args:
            selective: Whether to use selective processing
            show_stats: Whether to show processing statistics
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            # Build command arguments
            cmd = [sys.executable, 'process_coffee_data.py', str(self.csv_file)]
            
            if selective:
                cmd.append('--selective')
            
            if show_stats:
                cmd.append('--stats')
            
            # Run the processing script
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info("Post-processing completed successfully")
                return True, result.stdout, result.stderr
            else:
                self.logger.error(f"Post-processing failed: {result.stderr}")
                return False, result.stdout, result.stderr
                
        except subprocess.TimeoutExpired:
            self.logger.error("Post-processing timed out (>30s)")
            return False, "", ""
        except FileNotFoundError:
            self.logger.warning("process_coffee_data.py not found - skipping post-processing")
            return False, "", ""
        except Exception as e:
            self.logger.error(f"Post-processing error: {str(e)}")
            return False, "", ""
    
    def run_full_processing(self, show_stats: bool = True) -> Tuple[bool, str, str]:
        """
        Run full post-processing (not selective)
        
        Args:
            show_stats: Whether to show processing statistics
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            # Run with --force-full flag for complete reprocessing
            cmd = [sys.executable, 'process_coffee_data.py', str(self.csv_file), '--force-full']
            
            if show_stats:
                cmd.append('--stats')
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info("Full processing completed successfully")
                return True, result.stdout, result.stderr
            else:
                self.logger.error(f"Full processing failed: {result.stderr}")
                return False, result.stdout, result.stderr
                
        except subprocess.TimeoutExpired:
            self.logger.error("Full processing timed out (>60s)")
            return False, "", ""
        except Exception as e:
            self.logger.error(f"Full processing error: {str(e)}")
            return False, "", ""
    
    def get_next_brew_id(self, df: pd.DataFrame) -> int:
        """
        Get the next available brew ID
        
        Args:
            df: DataFrame containing existing brew records
            
        Returns:
            Next available brew ID
        """
        return self.brew_id_service.get_next_id(df)
    
    def validate_dataframe(self, df: pd.DataFrame) -> List[str]:
        """
        Validate DataFrame structure and data integrity
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        # Check for required columns
        required_columns = ['brew_id', 'brew_date', 'bean_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")
        
        if not df.empty and 'brew_id' in df.columns:
            # Check for duplicate brew IDs
            duplicate_ids = df[df['brew_id'].duplicated()]['brew_id'].tolist()
            if duplicate_ids:
                issues.append(f"Duplicate brew IDs found: {duplicate_ids}")
            
            # Check for invalid brew IDs
            invalid_ids = df[(df['brew_id'].isna()) | (df['brew_id'] < 1)]
            if not invalid_ids.empty:
                issues.append(f"Invalid brew IDs found: {len(invalid_ids)} records")
        
        # Check for missing essential data
        if not df.empty:
            missing_bean_names = df[df['bean_name'].isna() | (df['bean_name'] == '')]
            if not missing_bean_names.empty:
                issues.append(f"Missing bean names: {len(missing_bean_names)} records")
        
        return issues
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get summary information about the dataset
        
        Args:
            df: DataFrame to summarize
            
        Returns:
            Dictionary with summary statistics
        """
        if df.empty:
            return {
                'total_records': 0,
                'unique_beans': 0,
                'date_range': None,
                'avg_rating': 0,
                'data_completeness': 0
            }
        
        # Calculate completeness percentage
        total_cells = df.size
        non_null_cells = df.notna().sum().sum()
        completeness = (non_null_cells / total_cells * 100) if total_cells > 0 else 0
        
        # Date range
        date_range = None
        if 'brew_date' in df.columns:
            min_date = df['brew_date'].min()
            max_date = df['brew_date'].max()
            if pd.notna(min_date) and pd.notna(max_date):
                date_range = f"{min_date} to {max_date}"
        
        return {
            'total_records': len(df),
            'unique_beans': df['bean_name'].nunique() if 'bean_name' in df.columns else 0,
            'date_range': date_range,
            'avg_rating': df['score_overall_rating'].mean() if 'score_overall_rating' in df.columns else 0,
            'data_completeness': completeness
        }
    
    def backup_data(self, backup_suffix: str = "_backup") -> bool:
        """
        Create a backup of the current data file
        
        Args:
            backup_suffix: Suffix to add to backup filename
            
        Returns:
            True if backup was successful
        """
        try:
            if not self.csv_file.exists():
                self.logger.warning("No data file to backup")
                return False
            
            backup_path = self.csv_file.with_name(f"{self.csv_file.stem}{backup_suffix}{self.csv_file.suffix}")
            
            # Copy the file
            import shutil
            shutil.copy2(self.csv_file, backup_path)
            
            self.logger.info(f"Backup created: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False
    
    def restore_from_backup(self, backup_suffix: str = "_backup") -> bool:
        """
        Restore data from backup file
        
        Args:
            backup_suffix: Suffix of backup filename to restore from
            
        Returns:
            True if restore was successful
        """
        try:
            backup_path = self.csv_file.with_name(f"{self.csv_file.stem}{backup_suffix}{self.csv_file.suffix}")
            
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Copy backup to main file
            import shutil
            shutil.copy2(backup_path, self.csv_file)
            
            self.logger.info(f"Data restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring from backup: {e}")
            return False