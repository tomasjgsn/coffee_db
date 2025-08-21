"""
Bean Selection Service

Handles bean selection logic, bean statistics, and bean management operations.
Extracted from main application to improve separation of concerns.
"""

import pandas as pd
from typing import Dict, List, Optional, Any, Union
import logging
from datetime import date
from ..models.coffee_bean import CoffeeBean
from ..models.bean_statistics import BeanStatistics


class BeanSelectionService:
    """Service for handling bean selection and bean-related operations"""
    
    def __init__(self):
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(f"{__name__}.BeanSelectionService")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_unique_beans(self, df: pd.DataFrame, show_archived: bool = False) -> pd.DataFrame:
        """
        Get unique beans from dataframe with usage information
        
        Args:
            df: DataFrame containing coffee data
            show_archived: Whether to include archived beans
            
        Returns:
            DataFrame of unique beans with usage statistics
        """
        if df.empty:
            return pd.DataFrame()
        
        # Filter archived beans if needed
        df_filtered = df.copy()
        if not show_archived:
            if 'archive_status' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['archive_status'] != 'archived']
        
        # Build column list dynamically based on what exists
        base_cols = ['bean_name', 'bean_origin_country', 'bean_origin_region', 'bean_variety', 
                   'bean_process_method', 'bean_roast_date', 'bean_roast_level', 'bean_notes']
        optional_cols = ['estimated_bag_size_grams', 'archive_status']
        
        # Only include columns that actually exist
        cols_to_select = [col for col in base_cols if col in df_filtered.columns]
        for col in optional_cols:
            if col in df_filtered.columns:
                cols_to_select.append(col)
        
        unique_beans = df_filtered.drop_duplicates(
            subset=['bean_name', 'bean_origin_country', 'bean_origin_region']
        )[cols_to_select].dropna(subset=['bean_name'])
        
        return unique_beans
    
    def get_bean_options_with_usage(self, df: pd.DataFrame, unique_beans: pd.DataFrame, 
                                  context: str = "add") -> List[str]:
        """
        Create bean options list with usage information
        
        Args:
            df: Full DataFrame for usage calculations
            unique_beans: DataFrame of unique beans
            context: "add" or "edit" context
            
        Returns:
            List of formatted bean option strings
        """
        bean_options = ["Create New Bean" if context == "add" else "Manual Entry"]
        
        for _, row in unique_beans.iterrows():
            # Calculate usage for this bean
            bean_usage = df[
                (df['bean_name'] == row['bean_name']) & 
                (df['bean_origin_country'] == row['bean_origin_country']) &
                (df['bean_origin_region'] == row['bean_origin_region'])
            ]['coffee_dose_grams'].fillna(0).sum()
            
            bag_size = row.get('estimated_bag_size_grams', 0) or 0
            usage_info = ""
            if bag_size > 0:
                remaining = max(0, bag_size - bean_usage)
                usage_info = f" (~{remaining:.0f}g remaining)"
            
            archive_indicator = " 📦" if row.get('archive_status') == 'archived' else ""
            bean_display = f"{row['bean_name']}{usage_info}{archive_indicator}"
            bean_options.append(bean_display)
        
        return bean_options
    
    def get_selected_bean_data(self, selected_option: str, unique_beans: pd.DataFrame, 
                             bean_options: List[str], context: str = "add") -> Optional[Dict[str, Any]]:
        """
        Get bean data for the selected option
        
        Args:
            selected_option: Selected bean option string
            unique_beans: DataFrame of unique beans
            bean_options: List of all bean options
            context: "add" or "edit" context
            
        Returns:
            Dictionary of bean data or None for manual entry
        """
        manual_entry_label = "Create New Bean" if context == "add" else "Manual Entry"
        
        if selected_option == manual_entry_label or unique_beans.empty:
            return None
        
        try:
            # Find the selected bean data
            bean_index = bean_options.index(selected_option) - 1
            if 0 <= bean_index < len(unique_beans):
                selected_bean = unique_beans.iloc[bean_index]
                return selected_bean.to_dict()
        except (ValueError, IndexError):
            self.logger.warning(f"Could not find bean data for selection: {selected_option}")
        
        return None
    
    def get_bean_statistics(self, df: pd.DataFrame) -> List[BeanStatistics]:
        """
        Calculate statistics for each unique bean
        
        Args:
            df: DataFrame containing coffee data
            
        Returns:
            List of BeanStatistics objects
        """
        if df.empty:
            return []
        
        # Get unique beans based on name, country, and region
        unique_bean_combinations = df.drop_duplicates(
            subset=['bean_name', 'bean_origin_country', 'bean_origin_region']
        )[['bean_name', 'bean_origin_country', 'bean_origin_region']].dropna(subset=['bean_name'])
        
        bean_stats = []
        for _, bean_combo in unique_bean_combinations.iterrows():
            # Get all records for this bean combination (handle NaN values properly)
            name_match = df['bean_name'] == bean_combo['bean_name']
            country_match = df['bean_origin_country'] == bean_combo['bean_origin_country']
            
            # Handle NaN region comparison properly
            if pd.isna(bean_combo['bean_origin_region']):
                region_match = df['bean_origin_region'].isna()
            else:
                region_match = df['bean_origin_region'] == bean_combo['bean_origin_region']
            
            bean_records = df[name_match & country_match & region_match].copy()
            
            if bean_records.empty:
                continue
                
            # Calculate statistics
            total_brews = len(bean_records)
            total_grams_used = bean_records['coffee_dose_grams'].fillna(0).sum()
            avg_rating = bean_records['score_overall_rating'].fillna(0).mean()
            last_used = bean_records['brew_date'].max()
            
            # Get bag size and archive status from most recent entry
            latest_record = bean_records.iloc[-1]
            bag_size = latest_record.get('estimated_bag_size_grams', 0) or 0
            archive_status = latest_record.get('archive_status', 'active')
            # Handle NaN values in archive_status
            if pd.isna(archive_status):
                archive_status = 'active'
            
            remaining_grams = max(0, bag_size - total_grams_used) if bag_size > 0 else 0
            usage_percentage = (total_grams_used / bag_size * 100) if bag_size > 0 else 0
            
            # Calculate days since last used
            if pd.notna(last_used):
                days_since_last = (pd.Timestamp.now().date() - pd.to_datetime(last_used).date()).days
            else:
                days_since_last = float('inf')
            
            bean_stat = BeanStatistics(
                name=bean_combo['bean_name'],
                country=bean_combo['bean_origin_country'] or 'Unknown',
                region=bean_combo['bean_origin_region'] if pd.notna(bean_combo['bean_origin_region']) else '',
                total_brews=total_brews,
                total_grams_used=total_grams_used,
                bag_size=bag_size,
                remaining_grams=remaining_grams,
                usage_percentage=usage_percentage,
                avg_rating=avg_rating,
                last_used=last_used,
                days_since_last=days_since_last,
                archive_status=archive_status,
                records=bean_records
            )
            bean_stats.append(bean_stat)
        
        return bean_stats
    
    def archive_bean(self, bean_name: str, bean_country: str, bean_region: Optional[str], 
                    df: pd.DataFrame) -> pd.DataFrame:
        """
        Archive a bean by updating all its records
        
        Args:
            bean_name: Name of the bean
            bean_country: Country of origin
            bean_region: Region of origin (can be None)
            df: DataFrame to update
            
        Returns:
            Updated DataFrame
        """
        # Ensure archive_status column exists and is of string type
        if 'archive_status' not in df.columns:
            df['archive_status'] = 'active'
        elif df['archive_status'].dtype != 'object':
            df['archive_status'] = df['archive_status'].astype('object')
            df['archive_status'] = df['archive_status'].fillna('active')
        
        # Update all records for this bean (handle NaN values properly)
        name_match = df['bean_name'] == bean_name
        country_match = df['bean_origin_country'] == bean_country
        
        # Handle NaN and empty string region comparison properly
        if pd.isna(bean_region) or bean_region == '':
            region_match = df['bean_origin_region'].isna()
        else:
            region_match = df['bean_origin_region'] == bean_region
        
        mask = name_match & country_match & region_match
        df.loc[mask, 'archive_status'] = 'archived'
        return df
    
    def restore_bean(self, bean_name: str, bean_country: str, bean_region: Optional[str], 
                    df: pd.DataFrame) -> pd.DataFrame:
        """
        Restore an archived bean by updating all its records
        
        Args:
            bean_name: Name of the bean
            bean_country: Country of origin
            bean_region: Region of origin (can be None)
            df: DataFrame to update
            
        Returns:
            Updated DataFrame
        """
        # Ensure archive_status column exists and is of string type
        if 'archive_status' not in df.columns:
            df['archive_status'] = 'active'
        elif df['archive_status'].dtype != 'object':
            df['archive_status'] = df['archive_status'].astype('object')
            df['archive_status'] = df['archive_status'].fillna('active')
        
        # Update all records for this bean (handle NaN values properly)
        name_match = df['bean_name'] == bean_name
        country_match = df['bean_origin_country'] == bean_country
        
        # Handle NaN and empty string region comparison properly
        if pd.isna(bean_region) or bean_region == '':
            region_match = df['bean_origin_region'].isna()
        else:
            region_match = df['bean_origin_region'] == bean_region
        
        mask = name_match & country_match & region_match
        df.loc[mask, 'archive_status'] = 'active'
        return df
    
    def find_old_beans(self, df: pd.DataFrame, days_threshold: int) -> List[BeanStatistics]:
        """
        Find beans that haven't been used in the specified number of days
        
        Args:
            df: DataFrame containing coffee data
            days_threshold: Number of days threshold
            
        Returns:
            List of BeanStatistics for old beans
        """
        bean_stats = self.get_bean_statistics(df)
        old_beans = [
            bean for bean in bean_stats 
            if bean.archive_status != 'archived' and bean.days_since_last > days_threshold
        ]
        return old_beans
    
    def archive_multiple_beans(self, beans: List[BeanStatistics], df: pd.DataFrame) -> pd.DataFrame:
        """
        Archive multiple beans
        
        Args:
            beans: List of BeanStatistics to archive
            df: DataFrame to update
            
        Returns:
            Updated DataFrame
        """
        for bean in beans:
            # Convert empty string to None for null regions
            region_param = bean.region if bean.region else None
            df = self.archive_bean(bean.name, bean.country, region_param, df)
        
        return df