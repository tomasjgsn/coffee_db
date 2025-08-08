"""
Coffee Data Repository

Data access layer for coffee brewing data.
Handles CSV file operations and data persistence.
Extracted from the monolithic application following TDD principles.
"""

from pathlib import Path
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging


class CoffeeDataRepository:
    """Repository for coffee brewing data persistence"""
    
    def __init__(self, csv_file_path: str):
        """Initialize repository with CSV file path"""
        self.csv_file_path = Path(csv_file_path)
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(f"{__name__}.CoffeeDataRepository")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def load_data(self) -> pd.DataFrame:
        """Load coffee data from CSV file"""
        try:
            if not self.csv_file_path.exists():
                self.logger.warning(f"CSV file {self.csv_file_path} not found, returning empty DataFrame")
                return pd.DataFrame()
            
            df = pd.read_csv(self.csv_file_path)
            
            # Convert date columns
            date_columns = ['brew_date', 'bean_purchase_date', 'bean_harvest_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
            
            self.logger.info(f"Loaded {len(df)} records from {self.csv_file_path}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading data from {self.csv_file_path}: {e}")
            raise
    
    def save_data(self, df: pd.DataFrame) -> bool:
        """Save DataFrame to CSV file"""
        try:
            # Create directory if it doesn't exist
            self.csv_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert date columns to strings for CSV storage
            df_to_save = df.copy()
            date_columns = ['brew_date', 'bean_purchase_date', 'bean_harvest_date']
            for col in date_columns:
                if col in df_to_save.columns:
                    df_to_save[col] = df_to_save[col].apply(
                        lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) and hasattr(x, 'strftime') else x
                    )
            
            df_to_save.to_csv(self.csv_file_path, index=False)
            self.logger.info(f"Saved {len(df)} records to {self.csv_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data to {self.csv_file_path}: {e}")
            raise
    
    def backup_data(self, backup_suffix: Optional[str] = None) -> Path:
        """Create backup of current data file"""
        if not self.csv_file_path.exists():
            raise FileNotFoundError(f"Cannot backup non-existent file: {self.csv_file_path}")
        
        if backup_suffix is None:
            backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_path = self.csv_file_path.with_name(
            f"{self.csv_file_path.stem}_backup_{backup_suffix}.csv"
        )
        
        try:
            # Copy current file to backup
            import shutil
            shutil.copy2(self.csv_file_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            raise
    
    def get_unique_beans(self) -> List[Dict[str, Any]]:
        """Get list of unique coffee beans"""
        try:
            df = self.load_data()
            if df.empty:
                return []
            
            # Group by bean characteristics
            unique_beans = df.groupby([
                'bean_name', 'bean_origin_country', 'bean_origin_region'
            ]).first().reset_index()
            
            beans = []
            for _, row in unique_beans.iterrows():
                beans.append({
                    'name': row['bean_name'],
                    'country': row['bean_origin_country'], 
                    'region': row['bean_origin_region'] if pd.notna(row['bean_origin_region']) else None,
                    'archive_status': row.get('archive_status', 'active')
                })
            
            return beans
            
        except Exception as e:
            self.logger.error(f"Error getting unique beans: {e}")
            return []
    
    def get_records_for_bean(self, bean_name: str, country: str, region: Optional[str] = None) -> pd.DataFrame:
        """Get all records for a specific bean"""
        try:
            df = self.load_data()
            if df.empty:
                return pd.DataFrame()
            
            # Filter by bean characteristics
            mask = (df['bean_name'] == bean_name) & (df['bean_origin_country'] == country)
            
            if region is not None:
                mask = mask & (df['bean_origin_region'] == region)
            else:
                mask = mask & (df['bean_origin_region'].isna() | (df['bean_origin_region'] == ''))
            
            return df[mask].copy()
            
        except Exception as e:
            self.logger.error(f"Error getting records for bean {bean_name}: {e}")
            return pd.DataFrame()
    
    def update_bean_archive_status(self, bean_name: str, country: str, region: Optional[str], 
                                 new_status: str) -> bool:
        """Update archive status for all records of a specific bean"""
        try:
            df = self.load_data()
            if df.empty:
                return False
            
            # Find matching records
            mask = (df['bean_name'] == bean_name) & (df['bean_origin_country'] == country)
            
            if region is not None and region != '':
                mask = mask & (df['bean_origin_region'] == region)
            else:
                mask = mask & (df['bean_origin_region'].isna() | (df['bean_origin_region'] == ''))
            
            if not mask.any():
                self.logger.warning(f"No records found for bean: {bean_name}, {country}, {region}")
                return False
            
            # Create archive_status column if it doesn't exist
            if 'archive_status' not in df.columns:
                df['archive_status'] = 'active'
            
            # Update status for matching records
            df.loc[mask, 'archive_status'] = new_status
            
            # Save updated data
            self.save_data(df)
            
            updated_count = mask.sum()
            self.logger.info(f"Updated archive status to '{new_status}' for {updated_count} records of {bean_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating archive status for {bean_name}: {e}")
            return False