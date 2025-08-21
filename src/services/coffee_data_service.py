"""
Coffee Data Service

Business logic layer for coffee brewing operations.
Coordinates between repositories and domain models.
Extracted from the monolithic application following TDD principles.
"""

from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import date
import logging

from src.repositories.coffee_data_repository import CoffeeDataRepository
from src.models.coffee_bean import CoffeeBean
from src.models.brew_record import BrewRecord
from src.models.bean_statistics import BeanStatistics
from src.models.brewing_calculations import classify_brewing_zone, calculate_brew_score


class CoffeeDataService:
    """Service layer for coffee data operations"""
    
    def __init__(self, csv_file_path: str):
        """Initialize service with data repository"""
        self.repository = CoffeeDataRepository(csv_file_path)
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(f"{__name__}.CoffeeDataService")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_bean_list(self, include_archived: bool = False) -> List[CoffeeBean]:
        """Get list of coffee beans"""
        try:
            beans_data = self.repository.get_unique_beans()
            
            beans = []
            for bean_data in beans_data:
                if not include_archived and bean_data.get('archive_status') == 'archived':
                    continue
                
                bean = CoffeeBean(
                    name=bean_data['name'],
                    origin_country=bean_data['country'],
                    origin_region=bean_data['region'],
                    archive_status=bean_data.get('archive_status', 'active')
                )
                beans.append(bean)
            
            return beans
            
        except Exception as e:
            self.logger.error(f"Error getting bean list: {e}")
            return []
    
    def get_bean_statistics(self, bean_name: str, country: str, region: Optional[str] = None) -> Optional[BeanStatistics]:
        """Get statistics for a specific bean"""
        try:
            df = self.repository.get_records_for_bean(bean_name, country, region)
            if df.empty:
                return None
            
            return BeanStatistics.calculate_for_bean(bean_name, df)
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics for {bean_name}: {e}")
            return None
    
    def get_all_bean_statistics(self, include_archived: bool = False) -> List[BeanStatistics]:
        """Get statistics for all beans"""
        try:
            df = self.repository.load_data()
            if df.empty:
                return []
            
            # Filter archived beans if requested
            if not include_archived:
                df = df[df.get('archive_status', 'active') != 'archived']
            
            return BeanStatistics.calculate_all_beans(df)
            
        except Exception as e:
            self.logger.error(f"Error calculating all bean statistics: {e}")
            return []
    
    def archive_bean(self, bean_name: str, country: str, region: Optional[str] = None) -> bool:
        """Archive a coffee bean and all its records"""
        try:
            success = self.repository.update_bean_archive_status(
                bean_name, country, region, 'archived'
            )
            
            if success:
                self.logger.info(f"Archived bean: {bean_name} ({country}, {region})")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error archiving bean {bean_name}: {e}")
            return False
    
    def restore_bean(self, bean_name: str, country: str, region: Optional[str] = None) -> bool:
        """Restore an archived coffee bean"""
        try:
            success = self.repository.update_bean_archive_status(
                bean_name, country, region, 'active'
            )
            
            if success:
                self.logger.info(f"Restored bean: {bean_name} ({country}, {region})")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error restoring bean {bean_name}: {e}")
            return False
    
    def add_brew_record(self, record: BrewRecord) -> bool:
        """Add a new brew record"""
        try:
            # Load existing data
            df = self.repository.load_data()
            
            # Convert record to dictionary
            record_dict = record.to_dict()
            
            # Add calculated brewing zone and score
            zone = classify_brewing_zone(record.final_tds_percent, record.final_extraction_yield_percent)
            record_dict['score_brewing_zone'] = zone
            record_dict['score_brew'] = calculate_brew_score(record.score_overall_rating, zone)
            
            # Create new row DataFrame
            new_row = pd.DataFrame([record_dict])
            
            # Append to existing data
            if df.empty:
                updated_df = new_row
            else:
                updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # Save updated data
            self.repository.save_data(updated_df)
            
            self.logger.info(f"Added brew record: {record.brew_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding brew record {record.brew_id}: {e}")
            return False
    
    def update_brew_record(self, brew_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing brew record"""
        try:
            df = self.repository.load_data()
            if df.empty:
                return False
            
            # Find record to update
            mask = df['brew_id'] == brew_id
            if not mask.any():
                self.logger.warning(f"Brew record not found: {brew_id}")
                return False
            
            # Apply updates
            for field, value in updates.items():
                if field in df.columns:
                    df.loc[mask, field] = value
            
            # Save updated data
            self.repository.save_data(df)
            
            self.logger.info(f"Updated brew record: {brew_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating brew record {brew_id}: {e}")
            return False
    
    def delete_brew_record(self, brew_id: str) -> bool:
        """Delete a brew record"""
        try:
            df = self.repository.load_data()
            if df.empty:
                return False
            
            # Find record to delete
            mask = df['brew_id'] == brew_id
            if not mask.any():
                self.logger.warning(f"Brew record not found: {brew_id}")
                return False
            
            # Remove record
            updated_df = df[~mask]
            
            # Save updated data
            self.repository.save_data(updated_df)
            
            self.logger.info(f"Deleted brew record: {brew_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting brew record {brew_id}: {e}")
            return False
    
    def backup_data(self, backup_suffix: Optional[str] = None) -> bool:
        """Create backup of current data"""
        try:
            backup_path = self.repository.backup_data(backup_suffix)
            self.logger.info(f"Created data backup: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False