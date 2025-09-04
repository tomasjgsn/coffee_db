"""
Visualization Service

Handles chart creation and data visualization logic for coffee brewing analysis.
Extracted from main application to improve separation of concerns.
"""

import pandas as pd
import altair as alt
from typing import Dict, List, Optional, Any, Tuple
import logging


class VisualizationService:
    """Service for handling data visualization and chart creation"""
    
    def __init__(self):
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(f"{__name__}.VisualizationService")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_brewing_control_chart_zones(self) -> pd.DataFrame:
        """
        Define brewing zone boundaries based on SCA standards
        
        Returns:
            DataFrame containing zone definitions
        """
        return pd.DataFrame([
            {'zone': 'Ideal', 'x_min': 18, 'x_max': 22, 'y_min': 1.15, 'y_max': 1.35, 'opacity': 0.1, 'color': '#2ca02c'},
            {'zone': 'Under-Extracted', 'x_min': 10, 'x_max': 18, 'y_min': 0.6, 'y_max': 1.7, 'opacity': 0.05, 'color': '#d62728'},
            {'zone': 'Over-Extracted', 'x_min': 22, 'x_max': 24, 'y_min': 0.6, 'y_max': 1.7, 'opacity': 0.05, 'color': '#ff7f0e'},
            {'zone': 'Weak', 'x_min': 10, 'x_max': 24, 'y_min': 0.6, 'y_max': 1.15, 'opacity': 0.03, 'color': '#17becf'},
            {'zone': 'Strong', 'x_min': 10, 'x_max': 24, 'y_min': 1.35, 'y_max': 1.7, 'opacity': 0.03, 'color': '#9467bd'}
        ])
    
    def get_brew_quality_color_scale(self) -> alt.Scale:
        """
        Define color scheme for brew quality categories
        
        Returns:
            Altair color scale for brew quality zones
        """
        return alt.Scale(
            domain=['Under-Weak', 'Under-Ideal', 'Under-Strong', 'Ideal-Weak', 'Ideal-Ideal', 'Ideal-Strong', 'Over-Weak', 'Over-Ideal', 'Over-Strong'],
            range=['#d62728', '#ff7f0e', '#bcbd22', '#17becf', '#2ca02c', '#9467bd', '#e377c2', '#7f7f7f', '#8c564b']
        )
    
    def create_background_zones_chart(self, zone_data: pd.DataFrame) -> alt.Chart:
        """
        Create background zones chart for brewing control chart
        
        Args:
            zone_data: DataFrame containing zone definitions
            
        Returns:
            Altair chart for background zones
        """
        return alt.Chart(zone_data).mark_rect().encode(
            x=alt.X('x_min:Q', title="Final Extraction Yield [%]", scale=alt.Scale(domain=[10, 24])),
            x2=alt.X2('x_max:Q'),
            y=alt.Y('y_min:Q', title="Total Dissolved Solids, TDS [%]", scale=alt.Scale(domain=[0.6, 1.7])),
            y2=alt.Y2('y_max:Q'),
            color=alt.Color('color:N', scale=None),
            opacity=alt.Opacity('opacity:Q', scale=None),
            tooltip=['zone:N']
        )
    
    def create_data_points_chart(self, chart_data: pd.DataFrame, color_scale: alt.Scale) -> alt.Chart:
        """
        Create data points chart for brewing control chart
        
        Args:
            chart_data: DataFrame containing brew data
            color_scale: Color scale for brew quality zones
            
        Returns:
            Altair chart for data points
        """
        return alt.Chart(chart_data).mark_circle(size=80, stroke='white', strokeWidth=1).encode(
            x=alt.X('final_extraction_yield_percent', 
                    title="Final Extraction Yield [%]",
                    scale=alt.Scale(domain=[10, 24])),
            y=alt.Y('final_tds_percent', 
                    title="Total Dissolved Solids, TDS [%]", 
                    scale=alt.Scale(domain=[0.6, 1.7])),
            color=alt.Color('score_brewing_zone:N',
                           title='Brew Quality Zone',
                           scale=color_scale,
                           legend=alt.Legend(orient='right', titleFontSize=12, labelFontSize=10)),
            size=alt.Size('score_overall_rating:Q',
                         title='Overall Rating',
                         scale=alt.Scale(domain=[1, 10], range=[40, 120]),
                         legend=alt.Legend(orient='right', titleFontSize=12, labelFontSize=10)),
            tooltip=['bean_name:N', 'brew_date:T', 'final_extraction_yield_percent:Q', 'final_tds_percent:Q', 
                    'score_brewing_zone:N', 'score_overall_rating:Q', 'score_flavor_profile_category:N',
                    'coffee_grams_per_liter:Q', 'grind_size:O', 'water_temp_degC:Q', 'brew_method:N']
        )
    
    def create_recent_points_chart(self, recent_data: pd.DataFrame, color_scale: alt.Scale) -> alt.Chart:
        """
        Create highlighted chart for recently added data points
        
        Args:
            recent_data: DataFrame containing recent brew data
            color_scale: Color scale for brew quality zones
            
        Returns:
            Altair chart for recent data points with enhanced styling
        """
        # Create main recent points with enhanced styling
        recent_points = alt.Chart(recent_data).mark_circle(
            size=120,  # Larger than regular points
            stroke='#ff6b35',  # Bright orange border
            strokeWidth=3,  # Thick border
            opacity=0.9
        ).encode(
            x=alt.X('final_extraction_yield_percent', 
                    scale=alt.Scale(domain=[10, 24])),
            y=alt.Y('final_tds_percent', 
                    scale=alt.Scale(domain=[0.6, 1.7])),
            color=alt.Color('score_brewing_zone:N',
                           scale=color_scale,
                           legend=None),  # Don't duplicate legend
            size=alt.Size('score_overall_rating:Q',
                         scale=alt.Scale(domain=[1, 10], range=[80, 160]),  # Larger range
                         legend=None),  # Don't duplicate legend
            tooltip=['bean_name:N', 'brew_date:T', 'final_extraction_yield_percent:Q', 'final_tds_percent:Q', 
                    'score_brewing_zone:N', 'score_overall_rating:Q', 'score_flavor_profile_category:N',
                    'coffee_grams_per_liter:Q', 'grind_size:O', 'water_temp_degC:Q', 'brew_method:N']
        )
        
        # Add pulsing effect with a slightly larger circle
        pulse_ring = alt.Chart(recent_data).mark_circle(
            size=180,  # Even larger
            stroke='#ff6b35',
            strokeWidth=2,
            fill=None,  # Transparent fill
            opacity=0.4
        ).encode(
            x=alt.X('final_extraction_yield_percent', 
                    scale=alt.Scale(domain=[10, 24])),
            y=alt.Y('final_tds_percent', 
                    scale=alt.Scale(domain=[0.6, 1.7]))
        )
        
        return pulse_ring + recent_points
    
    def create_brewing_control_chart(self, chart_data: pd.DataFrame, recent_brew_ids: list = None) -> alt.Chart:
        """
        Create complete brewing control chart with optional recent highlighting
        
        Args:
            chart_data: DataFrame containing brew data
            recent_brew_ids: List of brew IDs to highlight as recently added
            
        Returns:
            Combined Altair chart with background zones and data points
        """
        # Get zone data and color scale
        zone_data = self.get_brewing_control_chart_zones()
        color_scale = self.get_brew_quality_color_scale()
        
        # Create background zones
        background_zones = self.create_background_zones_chart(zone_data)
        
        # Separate recent and regular data points
        recent_brew_ids = recent_brew_ids or []
        if recent_brew_ids and not chart_data.empty:
            # Filter recent_brew_ids to only include IDs that exist in chart_data
            valid_recent_ids = [brew_id for brew_id in recent_brew_ids if brew_id in chart_data['brew_id'].values]
            
            # Split data into recent and regular using only valid IDs
            recent_data = chart_data[chart_data['brew_id'].isin(valid_recent_ids)] if valid_recent_ids else pd.DataFrame()
            regular_data = chart_data[~chart_data['brew_id'].isin(valid_recent_ids)]
            
            # Create separate charts - only include non-empty charts
            chart_layers = [background_zones]
            
            if not regular_data.empty:
                regular_points = self.create_data_points_chart(regular_data, color_scale)
                chart_layers.append(regular_points)
            
            if not recent_data.empty:
                recent_points = self.create_recent_points_chart(recent_data, color_scale)
                chart_layers.append(recent_points)
            
            # Combine all layers
            if len(chart_layers) == 1:
                # Only background zones
                chart = background_zones.properties(height=400)
            else:
                # Background + data points
                chart = alt.layer(*chart_layers).resolve_scale(
                    color='independent'
                ).properties(
                    height=400
                )
        else:
            # Regular chart without highlighting
            points_chart = self.create_data_points_chart(chart_data, color_scale)
            chart = (background_zones + points_chart).resolve_scale(
                color='independent'
            ).properties(
                height=400
            )
        
        return chart
    
    def apply_data_filters(self, df: pd.DataFrame, filters: Dict[str, List[Any]]) -> pd.DataFrame:
        """
        Apply filters to the DataFrame
        
        Args:
            df: DataFrame to filter
            filters: Dictionary of filter criteria
                    {
                        'coffees': List of coffee names,
                        'grinds': List of grind sizes,
                        'temps': List of temperatures
                    }
            
        Returns:
            Filtered DataFrame
        """
        filtered_df = df.copy()
        
        # Apply coffee filter
        if filters.get('coffees'):
            filtered_df = filtered_df[filtered_df['bean_name'].isin(filters['coffees']) | filtered_df['bean_name'].isna()]
        
        # Apply grind size filter
        if filters.get('grinds'):
            filtered_df = filtered_df[filtered_df['grind_size'].isin(filters['grinds']) | filtered_df['grind_size'].isna()]
        
        # Apply temperature filter
        if filters.get('temps'):
            filtered_df = filtered_df[filtered_df['water_temp_degC'].isin(filters['temps']) | filtered_df['water_temp_degC'].isna()]
        
        return filtered_df
    
    def get_filter_options(self, df: pd.DataFrame) -> Dict[str, List[Any]]:
        """
        Get available filter options from the DataFrame
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary of available filter options
        """
        return {
            'coffees': sorted(df['bean_name'].dropna().unique()),
            'grinds': sorted(df['grind_size'].dropna().unique()),
            'temps': sorted(df['water_temp_degC'].dropna().unique())
        }
    
    def get_filter_summary_info(self, original_df: pd.DataFrame, filtered_df: pd.DataFrame) -> Dict[str, int]:
        """
        Get summary information about applied filters
        
        Args:
            original_df: Original unfiltered DataFrame
            filtered_df: Filtered DataFrame
            
        Returns:
            Dictionary with filter summary statistics
        """
        return {
            'total_rows': len(original_df),
            'filtered_rows': len(filtered_df),
            'filtered_percentage': (len(filtered_df) / len(original_df) * 100) if len(original_df) > 0 else 0
        }
    
    def prepare_chart_data(self, df: pd.DataFrame, filters: Optional[Dict[str, List[Any]]] = None) -> pd.DataFrame:
        """
        Prepare data for chart visualization with optional filtering
        
        Args:
            df: Raw DataFrame
            filters: Optional filters to apply
            
        Returns:
            Prepared chart data
        """
        chart_data = df.copy()
        
        # Apply filters if provided
        if filters:
            chart_data = self.apply_data_filters(chart_data, filters)
        
        # Ensure required columns exist for visualization
        required_columns = [
            'final_extraction_yield_percent', 
            'final_tds_percent', 
            'score_brewing_zone',
            'score_overall_rating'
        ]
        
        missing_columns = [col for col in required_columns if col not in chart_data.columns]
        if missing_columns:
            self.logger.warning(f"Missing required columns for visualization: {missing_columns}")
        
        return chart_data
    
    def create_summary_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Create summary metrics for the brew data
        
        Args:
            df: DataFrame containing brew data
            
        Returns:
            Dictionary of summary metrics
        """
        if df.empty:
            return {
                'total_brews': 0,
                'avg_rating': 0,
                'avg_tds': 0,
                'avg_extraction': 0,
                'unique_beans': 0
            }
        
        return {
            'total_brews': len(df),
            'avg_rating': df['score_overall_rating'].fillna(0).mean(),
            'avg_tds': df['final_tds_percent'].fillna(0).mean(),
            'avg_extraction': df['final_extraction_yield_percent'].fillna(0).mean(),
            'unique_beans': df['bean_name'].nunique()
        }
    
    def format_chart_tooltip_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format data for better chart tooltips
        
        Args:
            df: DataFrame to format
            
        Returns:
            DataFrame with formatted tooltip columns
        """
        formatted_df = df.copy()
        
        # Format numeric columns for tooltips
        if 'final_extraction_yield_percent' in formatted_df.columns:
            formatted_df['extraction_formatted'] = formatted_df['final_extraction_yield_percent'].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
            )
        
        if 'final_tds_percent' in formatted_df.columns:
            formatted_df['tds_formatted'] = formatted_df['final_tds_percent'].apply(
                lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
            )
        
        if 'score_overall_rating' in formatted_df.columns:
            formatted_df['rating_formatted'] = formatted_df['score_overall_rating'].apply(
                lambda x: f"{x:.1f}/10" if pd.notna(x) else "N/A"
            )
        
        return formatted_df