"""
Visualization Service

Handles chart creation and data visualization logic for coffee brewing analysis.
Extracted from main application to improve separation of concerns.
"""

import pandas as pd
import numpy as np
import altair as alt
from typing import Dict, List, Optional, Any, Tuple
import logging

from src.models.unified_score import UnifiedBrewingScore


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

    # =========================================================================
    # Unified Brewing Score Visualizations
    # =========================================================================

    def get_isometric_line_data(
        self,
        brew_ratios: List[float] = None,
        extraction_range: Tuple[float, float] = (10, 24)
    ) -> pd.DataFrame:
        """
        Generate data for isometric brew ratio lines.

        Isometric lines represent constant brew ratios on the brewing control chart.
        The relationship is: TDS = (Brew_Ratio / 1000) × Extraction

        Args:
            brew_ratios: List of brew ratios in g/L to plot (default: common ratios)
            extraction_range: Range of extraction values for the lines

        Returns:
            DataFrame with columns: brew_ratio, extraction, tds
        """
        if brew_ratios is None:
            brew_ratios = [50, 55, 60, 65, 70, 75, 80]

        lines_data = []
        e_min, e_max = extraction_range

        for ratio in brew_ratios:
            # Generate points along the extraction range
            extractions = np.linspace(e_min, e_max, 50)
            for e in extractions:
                tds = (ratio / 1000) * e
                # Only include points within reasonable TDS range
                if 0.5 <= tds <= 1.8:
                    lines_data.append({
                        'brew_ratio': ratio,
                        'extraction': e,
                        'tds': tds,
                        'label': f'{ratio} g/L'
                    })

        return pd.DataFrame(lines_data)

    def get_optimal_points_data(self, brew_ratios: List[float] = None) -> pd.DataFrame:
        """
        Get optimal (extraction, TDS) points for each brew ratio.

        Args:
            brew_ratios: List of brew ratios in g/L

        Returns:
            DataFrame with optimal points for each brew ratio
        """
        if brew_ratios is None:
            brew_ratios = [50, 55, 60, 65, 70, 75, 80]

        scorer = UnifiedBrewingScore()
        optimal_data = []

        for ratio in brew_ratios:
            e_opt, t_opt = scorer.get_optimal_point(ratio)
            optimal_data.append({
                'brew_ratio': ratio,
                'extraction': e_opt,
                'tds': t_opt,
                'label': f'{ratio} g/L optimal'
            })

        return pd.DataFrame(optimal_data)

    def create_isometric_lines_chart(
        self,
        brew_ratios: List[float] = None,
        show_labels: bool = True
    ) -> alt.Chart:
        """
        Create isometric brew ratio lines for the brewing control chart.

        Args:
            brew_ratios: List of brew ratios to display
            show_labels: Whether to show ratio labels on the lines

        Returns:
            Altair chart with isometric lines
        """
        lines_data = self.get_isometric_line_data(brew_ratios)

        # Create the lines
        lines = alt.Chart(lines_data).mark_line(
            strokeDash=[4, 4],
            opacity=0.5
        ).encode(
            x=alt.X('extraction:Q', scale=alt.Scale(domain=[10, 24])),
            y=alt.Y('tds:Q', scale=alt.Scale(domain=[0.6, 1.7])),
            color=alt.Color('label:N',
                           title='Brew Ratio',
                           scale=alt.Scale(scheme='viridis'),
                           legend=alt.Legend(orient='bottom', columns=4) if show_labels else None),
            detail='brew_ratio:N'
        )

        if show_labels:
            # Add labels at the end of each line
            label_data = lines_data.groupby('brew_ratio').apply(
                lambda x: x.loc[x['tds'].idxmax()]
            ).reset_index(drop=True)

            labels = alt.Chart(label_data).mark_text(
                align='left',
                dx=5,
                fontSize=10,
                fontWeight='bold'
            ).encode(
                x=alt.X('extraction:Q'),
                y=alt.Y('tds:Q'),
                text='label:N',
                color=alt.value('#666666')
            )

            return lines + labels

        return lines

    def create_optimal_points_chart(self, brew_ratios: List[float] = None) -> alt.Chart:
        """
        Create markers for optimal points on isometric lines.

        Args:
            brew_ratios: List of brew ratios to show optimal points for

        Returns:
            Altair chart with optimal point markers
        """
        optimal_data = self.get_optimal_points_data(brew_ratios)

        points = alt.Chart(optimal_data).mark_point(
            shape='diamond',
            size=100,
            filled=True,
            stroke='white',
            strokeWidth=2
        ).encode(
            x=alt.X('extraction:Q', scale=alt.Scale(domain=[10, 24])),
            y=alt.Y('tds:Q', scale=alt.Scale(domain=[0.6, 1.7])),
            color=alt.Color('brew_ratio:Q',
                           title='Brew Ratio (g/L)',
                           scale=alt.Scale(scheme='viridis')),
            tooltip=[
                alt.Tooltip('brew_ratio:Q', title='Brew Ratio (g/L)'),
                alt.Tooltip('extraction:Q', title='Optimal Extraction %', format='.1f'),
                alt.Tooltip('tds:Q', title='Optimal TDS %', format='.2f')
            ]
        )

        return points

    def create_enhanced_brewing_control_chart(
        self,
        chart_data: pd.DataFrame,
        show_isometric_lines: bool = True,
        show_optimal_points: bool = True,
        color_by_score: bool = False,
        recent_brew_ids: list = None
    ) -> alt.Chart:
        """
        Create enhanced brewing control chart with isometric lines and score coloring.

        Args:
            chart_data: DataFrame containing brew data
            show_isometric_lines: Whether to display isometric lines
            show_optimal_points: Whether to display optimal point markers
            color_by_score: If True, color points by unified_brewing_score
            recent_brew_ids: List of brew IDs to highlight

        Returns:
            Combined Altair chart
        """
        # Get zone data
        zone_data = self.get_brewing_control_chart_zones()

        # Create background zones
        background_zones = self.create_background_zones_chart(zone_data)

        layers = [background_zones]

        # Add isometric lines if requested
        if show_isometric_lines:
            isometric_lines = self.create_isometric_lines_chart(show_labels=True)
            layers.append(isometric_lines)

        # Add optimal points if requested
        if show_optimal_points:
            optimal_points = self.create_optimal_points_chart()
            layers.append(optimal_points)

        # Create data points chart
        if color_by_score and 'unified_brewing_score' in chart_data.columns:
            points = self._create_score_colored_points(chart_data)
        else:
            color_scale = self.get_brew_quality_color_scale()
            points = self.create_data_points_chart(chart_data, color_scale)

        layers.append(points)

        # Highlight recent brews if provided
        if recent_brew_ids and not chart_data.empty:
            valid_recent_ids = [bid for bid in recent_brew_ids if bid in chart_data['brew_id'].values]
            if valid_recent_ids:
                recent_data = chart_data[chart_data['brew_id'].isin(valid_recent_ids)]
                if not recent_data.empty:
                    color_scale = self.get_brew_quality_color_scale()
                    recent_points = self.create_recent_points_chart(recent_data, color_scale)
                    layers.append(recent_points)

        # Combine all layers
        chart = alt.layer(*layers).resolve_scale(
            color='independent'
        ).properties(
            height=450,
            title='Brewing Control Chart with Isometric Lines'
        )

        return chart

    def _create_score_colored_points(self, chart_data: pd.DataFrame) -> alt.Chart:
        """
        Create data points colored by unified brewing score.

        Args:
            chart_data: DataFrame with unified_brewing_score column

        Returns:
            Altair chart with score-colored points
        """
        return alt.Chart(chart_data).mark_circle(
            size=100,
            stroke='white',
            strokeWidth=1
        ).encode(
            x=alt.X('final_extraction_yield_percent:Q',
                    title="Final Extraction Yield [%]",
                    scale=alt.Scale(domain=[10, 24])),
            y=alt.Y('final_tds_percent:Q',
                    title="Total Dissolved Solids, TDS [%]",
                    scale=alt.Scale(domain=[0.6, 1.7])),
            color=alt.Color('unified_brewing_score:Q',
                           title='Unified Score',
                           scale=alt.Scale(scheme='viridis', domain=[0, 100]),
                           legend=alt.Legend(orient='right')),
            size=alt.Size('score_overall_rating:Q',
                         title='User Rating',
                         scale=alt.Scale(domain=[1, 10], range=[50, 150]),
                         legend=alt.Legend(orient='right')),
            tooltip=[
                alt.Tooltip('bean_name:N', title='Bean'),
                alt.Tooltip('brew_date:T', title='Date'),
                alt.Tooltip('final_extraction_yield_percent:Q', title='Extraction %', format='.1f'),
                alt.Tooltip('final_tds_percent:Q', title='TDS %', format='.2f'),
                alt.Tooltip('unified_brewing_score:Q', title='Unified Score', format='.1f'),
                alt.Tooltip('score_brewing_zone:N', title='Zone'),
                alt.Tooltip('score_overall_rating:Q', title='User Rating', format='.1f'),
                alt.Tooltip('coffee_grams_per_liter:Q', title='Brew Ratio (g/L)', format='.1f')
            ]
        )

    def create_score_contour_chart(
        self,
        brew_ratio: float = 65.0,
        extraction_range: Tuple[float, float] = (12, 24),
        tds_range: Tuple[float, float] = (0.8, 1.6),
        resolution: int = 50
    ) -> alt.Chart:
        """
        Create a contour/heatmap showing unified score across extraction-TDS space.

        Args:
            brew_ratio: Fixed brew ratio for the contour
            extraction_range: Range of extraction values
            tds_range: Range of TDS values
            resolution: Number of points in each dimension

        Returns:
            Altair heatmap chart
        """
        scorer = UnifiedBrewingScore()

        # Generate grid
        extractions = np.linspace(extraction_range[0], extraction_range[1], resolution)
        tds_values = np.linspace(tds_range[0], tds_range[1], resolution)

        grid_data = []
        for e in extractions:
            for t in tds_values:
                score = scorer.calculate(e, t, brew_ratio)
                grid_data.append({
                    'extraction': e,
                    'tds': t,
                    'score': score
                })

        grid_df = pd.DataFrame(grid_data)

        # Get optimal point for annotation
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio)

        # Create heatmap
        heatmap = alt.Chart(grid_df).mark_rect().encode(
            x=alt.X('extraction:Q',
                    title='Extraction Yield [%]',
                    bin=alt.Bin(maxbins=resolution)),
            y=alt.Y('tds:Q',
                    title='TDS [%]',
                    bin=alt.Bin(maxbins=resolution)),
            color=alt.Color('score:Q',
                           title='Unified Score',
                           scale=alt.Scale(scheme='viridis', domain=[0, 100]))
        )

        # Add optimal point marker
        optimal_point = alt.Chart(pd.DataFrame([{
            'extraction': e_opt,
            'tds': t_opt,
            'label': f'Optimal ({e_opt:.1f}%, {t_opt:.2f}%)'
        }])).mark_point(
            shape='cross',
            size=200,
            stroke='red',
            strokeWidth=3
        ).encode(
            x='extraction:Q',
            y='tds:Q',
            tooltip=['label:N']
        )

        return (heatmap + optimal_point).properties(
            height=400,
            title=f'Unified Score Contour (Brew Ratio: {brew_ratio} g/L)'
        )

    def create_parameter_sensitivity_chart(
        self,
        chart_data: pd.DataFrame,
        parameter: str,
        parameter_label: str = None
    ) -> alt.Chart:
        """
        Create scatter plot showing relationship between a parameter and unified score.

        Args:
            chart_data: DataFrame with brewing data
            parameter: Column name of the parameter to analyze
            parameter_label: Display label for the parameter

        Returns:
            Altair chart with scatter and trend line
        """
        if parameter not in chart_data.columns:
            self.logger.warning(f"Parameter {parameter} not found in data")
            return alt.Chart().mark_text().encode(text=alt.value(f"Parameter {parameter} not found"))

        if 'unified_brewing_score' not in chart_data.columns:
            self.logger.warning("unified_brewing_score not found in data")
            return alt.Chart().mark_text().encode(text=alt.value("Unified score not calculated"))

        # Filter valid data
        plot_data = chart_data[[parameter, 'unified_brewing_score', 'bean_name', 'brew_date']].dropna()

        if plot_data.empty:
            return alt.Chart().mark_text().encode(text=alt.value("No valid data"))

        label = parameter_label or parameter

        # Scatter points
        scatter = alt.Chart(plot_data).mark_circle(
            size=80,
            opacity=0.6
        ).encode(
            x=alt.X(f'{parameter}:Q', title=label),
            y=alt.Y('unified_brewing_score:Q',
                    title='Unified Brewing Score',
                    scale=alt.Scale(domain=[0, 100])),
            color=alt.value('#1f77b4'),
            tooltip=[
                alt.Tooltip('bean_name:N', title='Bean'),
                alt.Tooltip('brew_date:T', title='Date'),
                alt.Tooltip(f'{parameter}:Q', title=label),
                alt.Tooltip('unified_brewing_score:Q', title='Score', format='.1f')
            ]
        )

        # Trend line (LOESS regression)
        trend = scatter.transform_loess(
            parameter, 'unified_brewing_score', bandwidth=0.4
        ).mark_line(
            color='#ff7f0e',
            strokeWidth=3
        ).encode(
            x=f'{parameter}:Q',
            y='unified_brewing_score:Q'
        )

        return (scatter + trend).properties(
            height=300,
            title=f'{label} vs Unified Brewing Score'
        )

    def create_multi_parameter_sensitivity_grid(
        self,
        chart_data: pd.DataFrame,
        parameters: Dict[str, str] = None
    ) -> alt.Chart:
        """
        Create a grid of parameter sensitivity charts.

        Args:
            chart_data: DataFrame with brewing data
            parameters: Dict of {column_name: display_label}

        Returns:
            Altair concatenated chart grid
        """
        if parameters is None:
            parameters = {
                'grind_size': 'Grind Size',
                'water_temp_degC': 'Water Temperature (°C)',
                'coffee_grams_per_liter': 'Brew Ratio (g/L)',
                'brew_ratio_to_1': 'Water:Coffee Ratio'
            }

        charts = []
        for param, label in parameters.items():
            if param in chart_data.columns:
                chart = self.create_parameter_sensitivity_chart(chart_data, param, label)
                charts.append(chart)

        if not charts:
            return alt.Chart().mark_text().encode(text=alt.value("No parameters available"))

        # Arrange in 2-column grid
        rows = []
        for i in range(0, len(charts), 2):
            if i + 1 < len(charts):
                rows.append(alt.hconcat(charts[i], charts[i + 1]))
            else:
                rows.append(charts[i])

        return alt.vconcat(*rows)

    def create_correlation_heatmap(
        self,
        chart_data: pd.DataFrame,
        columns: List[str] = None
    ) -> alt.Chart:
        """
        Create correlation heatmap between brewing parameters and scores.

        Args:
            chart_data: DataFrame with brewing data
            columns: List of columns to include in correlation

        Returns:
            Altair heatmap chart
        """
        if columns is None:
            columns = [
                'grind_size', 'water_temp_degC', 'coffee_grams_per_liter',
                'brew_ratio_to_1', 'final_extraction_yield_percent',
                'final_tds_percent', 'unified_brewing_score', 'score_overall_rating'
            ]

        # Filter to available columns
        available_cols = [c for c in columns if c in chart_data.columns]

        if len(available_cols) < 2:
            return alt.Chart().mark_text().encode(text=alt.value("Insufficient data for correlation"))

        # Calculate correlation matrix
        corr_matrix = chart_data[available_cols].corr()

        # Convert to long format for Altair
        corr_data = []
        for i, col1 in enumerate(available_cols):
            for j, col2 in enumerate(available_cols):
                corr_data.append({
                    'var1': col1,
                    'var2': col2,
                    'correlation': corr_matrix.loc[col1, col2]
                })

        corr_df = pd.DataFrame(corr_data)

        # Create heatmap
        heatmap = alt.Chart(corr_df).mark_rect().encode(
            x=alt.X('var1:N', title=None, sort=available_cols),
            y=alt.Y('var2:N', title=None, sort=available_cols),
            color=alt.Color('correlation:Q',
                           title='Correlation',
                           scale=alt.Scale(scheme='redblue', domain=[-1, 1])),
            tooltip=[
                alt.Tooltip('var1:N', title='Variable 1'),
                alt.Tooltip('var2:N', title='Variable 2'),
                alt.Tooltip('correlation:Q', title='Correlation', format='.2f')
            ]
        )

        # Add text labels
        text = alt.Chart(corr_df).mark_text(fontSize=10).encode(
            x=alt.X('var1:N', sort=available_cols),
            y=alt.Y('var2:N', sort=available_cols),
            text=alt.Text('correlation:Q', format='.2f'),
            color=alt.condition(
                alt.datum.correlation > 0.5,
                alt.value('white'),
                alt.condition(
                    alt.datum.correlation < -0.5,
                    alt.value('white'),
                    alt.value('black')
                )
            )
        )

        return (heatmap + text).properties(
            height=400,
            width=500,
            title='Parameter Correlation Matrix'
        )

    def create_cross_parameter_heatmap(
        self,
        chart_data: pd.DataFrame,
        x_param: str,
        y_param: str,
        x_label: str = None,
        y_label: str = None,
        aggregation: str = 'mean'
    ) -> alt.Chart:
        """
        Create heatmap showing average unified score across two parameters.

        Args:
            chart_data: DataFrame with brewing data
            x_param: Column for x-axis
            y_param: Column for y-axis
            x_label: Display label for x-axis
            y_label: Display label for y-axis
            aggregation: Aggregation method ('mean', 'median', 'max')

        Returns:
            Altair heatmap chart
        """
        if x_param not in chart_data.columns or y_param not in chart_data.columns:
            return alt.Chart().mark_text().encode(text=alt.value("Parameters not found"))

        if 'unified_brewing_score' not in chart_data.columns:
            return alt.Chart().mark_text().encode(text=alt.value("Unified score not calculated"))

        x_label = x_label or x_param
        y_label = y_label or y_param

        # Create binned heatmap
        heatmap = alt.Chart(chart_data).mark_rect().encode(
            x=alt.X(f'{x_param}:Q',
                    title=x_label,
                    bin=alt.Bin(maxbins=10)),
            y=alt.Y(f'{y_param}:Q',
                    title=y_label,
                    bin=alt.Bin(maxbins=10)),
            color=alt.Color(f'{aggregation}(unified_brewing_score):Q',
                           title=f'{aggregation.title()} Score',
                           scale=alt.Scale(scheme='viridis', domain=[0, 100])),
            tooltip=[
                alt.Tooltip(f'{x_param}:Q', title=x_label, bin=True),
                alt.Tooltip(f'{y_param}:Q', title=y_label, bin=True),
                alt.Tooltip(f'{aggregation}(unified_brewing_score):Q',
                           title=f'{aggregation.title()} Score', format='.1f'),
                alt.Tooltip('count():Q', title='Count')
            ]
        )

        return heatmap.properties(
            height=350,
            title=f'{x_label} × {y_label}: {aggregation.title()} Unified Score'
        )

    def create_score_distribution_chart(self, chart_data: pd.DataFrame) -> alt.Chart:
        """
        Create histogram showing distribution of unified brewing scores.

        Args:
            chart_data: DataFrame with brewing data

        Returns:
            Altair histogram chart
        """
        if 'unified_brewing_score' not in chart_data.columns:
            return alt.Chart().mark_text().encode(text=alt.value("Unified score not calculated"))

        histogram = alt.Chart(chart_data).mark_bar(
            opacity=0.7,
            color='#1f77b4'
        ).encode(
            x=alt.X('unified_brewing_score:Q',
                    title='Unified Brewing Score',
                    bin=alt.Bin(step=5)),
            y=alt.Y('count():Q', title='Number of Brews'),
            tooltip=[
                alt.Tooltip('unified_brewing_score:Q', title='Score Range', bin=True),
                alt.Tooltip('count():Q', title='Count')
            ]
        )

        # Add mean line
        mean_score = chart_data['unified_brewing_score'].mean()
        mean_line = alt.Chart(pd.DataFrame([{'mean': mean_score}])).mark_rule(
            color='red',
            strokeWidth=2,
            strokeDash=[4, 4]
        ).encode(
            x='mean:Q'
        )

        mean_label = alt.Chart(pd.DataFrame([{
            'mean': mean_score,
            'label': f'Mean: {mean_score:.1f}'
        }])).mark_text(
            align='left',
            dx=5,
            dy=-10,
            color='red',
            fontWeight='bold'
        ).encode(
            x='mean:Q',
            text='label:N'
        )

        return (histogram + mean_line + mean_label).properties(
            height=250,
            title='Unified Brewing Score Distribution'
        )

    def create_score_by_bean_chart(self, chart_data: pd.DataFrame) -> alt.Chart:
        """
        Create box plot showing score distribution by bean type.

        Args:
            chart_data: DataFrame with brewing data

        Returns:
            Altair box plot chart
        """
        if 'unified_brewing_score' not in chart_data.columns:
            return alt.Chart().mark_text().encode(text=alt.value("Unified score not calculated"))

        # Filter beans with at least 2 brews
        bean_counts = chart_data['bean_name'].value_counts()
        valid_beans = bean_counts[bean_counts >= 2].index.tolist()

        if not valid_beans:
            return alt.Chart().mark_text().encode(text=alt.value("Need at least 2 brews per bean"))

        filtered_data = chart_data[chart_data['bean_name'].isin(valid_beans)]

        boxplot = alt.Chart(filtered_data).mark_boxplot(
            extent='min-max'
        ).encode(
            x=alt.X('bean_name:N',
                    title='Bean',
                    sort=alt.EncodingSortField(field='unified_brewing_score', op='median', order='descending')),
            y=alt.Y('unified_brewing_score:Q',
                    title='Unified Brewing Score',
                    scale=alt.Scale(domain=[0, 100])),
            color=alt.Color('bean_name:N', legend=None)
        )

        return boxplot.properties(
            height=300,
            title='Score Distribution by Bean'
        )

    def create_score_trend_chart(self, chart_data: pd.DataFrame) -> alt.Chart:
        """
        Create line chart showing unified score trend over time.

        Args:
            chart_data: DataFrame with brewing data

        Returns:
            Altair line chart
        """
        if 'unified_brewing_score' not in chart_data.columns:
            return alt.Chart().mark_text().encode(text=alt.value("Unified score not calculated"))

        # Sort by date
        sorted_data = chart_data.sort_values('brew_date')

        # Create scatter points
        points = alt.Chart(sorted_data).mark_circle(
            size=60,
            opacity=0.6
        ).encode(
            x=alt.X('brew_date:T', title='Brew Date'),
            y=alt.Y('unified_brewing_score:Q',
                    title='Unified Brewing Score',
                    scale=alt.Scale(domain=[0, 100])),
            color=alt.Color('bean_name:N', title='Bean'),
            tooltip=[
                alt.Tooltip('bean_name:N', title='Bean'),
                alt.Tooltip('brew_date:T', title='Date'),
                alt.Tooltip('unified_brewing_score:Q', title='Score', format='.1f'),
                alt.Tooltip('score_brewing_zone:N', title='Zone')
            ]
        )

        # Rolling average trend line
        trend = alt.Chart(sorted_data).mark_line(
            color='#ff7f0e',
            strokeWidth=2
        ).transform_window(
            rolling_mean='mean(unified_brewing_score)',
            frame=[-3, 3]
        ).encode(
            x='brew_date:T',
            y='rolling_mean:Q'
        )

        return (points + trend).properties(
            height=300,
            title='Unified Score Trend Over Time (with 7-brew rolling average)'
        )