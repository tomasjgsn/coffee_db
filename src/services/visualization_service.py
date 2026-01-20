"""
Visualization Service

Handles chart creation and data visualization logic for coffee brewing analysis.
Extracted from main application to improve separation of concerns.

Extended with analytics visualization methods for:
- Trend charts (improvement over time)
- Bean comparison charts
- Correlation heatmaps
- Consistency visualizations
"""

import pandas as pd
import altair as alt
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from src.models.analytics_models import (
        TrendData,
        ComparisonData,
        CorrelationResult,
        ConsistencyMetrics,
    )


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
    # Analytics Visualization Methods
    # =========================================================================

    def get_trend_color(self, direction: str) -> str:
        """
        Get color based on trend direction.

        Args:
            direction: "improving", "declining", or "stable"

        Returns:
            Hex color code
        """
        colors = {
            "improving": "#2ca02c",  # Green
            "declining": "#d62728",  # Red
            "stable": "#7f7f7f",     # Gray
        }
        return colors.get(direction, "#7f7f7f")

    def get_correlation_color_scale(self) -> alt.Scale:
        """
        Get color scale for correlation heatmap.

        Returns:
            Altair scale for correlations (-1 to 1)
        """
        return alt.Scale(
            domain=[-1, 0, 1],
            range=["#d62728", "#ffffff", "#2ca02c"],  # Red -> White -> Green
            type="linear",
        )

    def prepare_trend_chart_data(self, trend_data: "TrendData") -> pd.DataFrame:
        """
        Prepare trend data as DataFrame for charting.

        Args:
            trend_data: TrendData object with values and dates

        Returns:
            DataFrame ready for Altair charting
        """
        if not trend_data.values or not trend_data.dates:
            return pd.DataFrame(columns=["date", "value", "moving_avg"])

        return pd.DataFrame({
            "date": trend_data.dates,
            "value": trend_data.values,
            "moving_avg": trend_data.moving_average,
        })

    def prepare_comparison_chart_data(self, comparison_data: "ComparisonData") -> pd.DataFrame:
        """
        Prepare comparison data as DataFrame for charting.

        Args:
            comparison_data: ComparisonData object with bean metrics

        Returns:
            DataFrame ready for Altair charting
        """
        if not comparison_data.bean_metrics:
            return pd.DataFrame(columns=["bean_name", "metric", "value"])

        rows = []
        for bean_name, metrics in comparison_data.bean_metrics.items():
            rows.append({
                "bean_name": bean_name,
                "sample_size": metrics.sample_size,
                "avg_extraction": metrics.avg_extraction,
                "avg_tds": metrics.avg_tds,
                "avg_rating": metrics.avg_rating,
                "avg_brew_score": metrics.avg_brew_score,
                "extraction_std": metrics.extraction_std,
                "tds_std": metrics.tds_std,
                "rating_std": metrics.rating_std,
                "best_rating": metrics.best_rating,
                "worst_rating": metrics.worst_rating,
            })

        return pd.DataFrame(rows)

    def prepare_correlation_chart_data(self, correlations: List["CorrelationResult"]) -> pd.DataFrame:
        """
        Prepare correlation data as DataFrame for charting.

        Args:
            correlations: List of CorrelationResult objects

        Returns:
            DataFrame ready for Altair heatmap
        """
        if not correlations:
            return pd.DataFrame(columns=["parameter", "metric", "correlation", "strength"])

        return pd.DataFrame([
            {
                "parameter": c.parameter,
                "metric": c.metric,
                "correlation": c.correlation,
                "strength": c.strength,
                "direction": c.direction,
                "sample_size": c.sample_size,
            }
            for c in correlations
        ])

    def create_trend_chart(self, trend_data: "TrendData") -> alt.Chart:
        """
        Create a trend chart showing metric values over time with moving average.

        Args:
            trend_data: TrendData object with trend analysis

        Returns:
            Altair layered chart with points and trend line
        """
        df = self.prepare_trend_chart_data(trend_data)

        if df.empty:
            # Return empty chart with message
            return alt.Chart(pd.DataFrame({"text": ["No data available"]})).mark_text(
                fontSize=14, color="gray"
            ).encode(
                text="text:N"
            ).properties(
                width=400,
                height=200,
                title="Trend Analysis - No Data"
            )

        trend_color = self.get_trend_color(trend_data.trend_direction)

        # Create base chart
        base = alt.Chart(df).encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %d")),
        )

        # Data points
        points = base.mark_circle(size=60, color=trend_color, opacity=0.7).encode(
            y=alt.Y("value:Q", title=self._format_metric_name(trend_data.metric)),
            tooltip=[
                alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
                alt.Tooltip("value:Q", title="Value", format=".2f"),
            ],
        )

        # Moving average line
        line = base.mark_line(color=trend_color, strokeWidth=2, opacity=0.8).encode(
            y=alt.Y("moving_avg:Q"),
        )

        # Combine layers
        chart = (line + points).properties(
            width=500,
            height=250,
            title=f"{self._format_metric_name(trend_data.metric)} Trend ({trend_data.window_days} days)"
        )

        return chart

    def create_comparison_chart(self, comparison_data: "ComparisonData") -> alt.Chart:
        """
        Create a grouped bar chart comparing beans across metrics.

        Args:
            comparison_data: ComparisonData object with bean metrics

        Returns:
            Altair grouped bar chart
        """
        df = self.prepare_comparison_chart_data(comparison_data)

        if df.empty:
            return alt.Chart(pd.DataFrame({"text": ["No data available"]})).mark_text(
                fontSize=14, color="gray"
            ).encode(
                text="text:N"
            ).properties(
                width=400,
                height=200,
                title="Bean Comparison - No Data"
            )

        # Melt the dataframe for grouped bar chart
        metrics_to_show = ["avg_extraction", "avg_rating"]
        df_melted = df.melt(
            id_vars=["bean_name", "sample_size"],
            value_vars=metrics_to_show,
            var_name="metric",
            value_name="value",
        )

        # Clean up metric names for display
        df_melted["metric"] = df_melted["metric"].replace({
            "avg_extraction": "Avg Extraction %",
            "avg_rating": "Avg Rating",
        })

        chart = alt.Chart(df_melted).mark_bar().encode(
            x=alt.X("bean_name:N", title="Bean", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color("metric:N", title="Metric",
                           scale=alt.Scale(scheme="category10")),
            xOffset="metric:N",
            tooltip=[
                alt.Tooltip("bean_name:N", title="Bean"),
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("value:Q", title="Value", format=".2f"),
                alt.Tooltip("sample_size:Q", title="Sample Size"),
            ],
        ).properties(
            width=400,
            height=300,
            title="Bean Comparison"
        )

        return chart

    def create_correlation_heatmap(self, correlations: List["CorrelationResult"]) -> alt.Chart:
        """
        Create a heatmap showing correlations between parameters and metrics.

        Args:
            correlations: List of CorrelationResult objects

        Returns:
            Altair heatmap chart
        """
        df = self.prepare_correlation_chart_data(correlations)

        if df.empty:
            return alt.Chart(pd.DataFrame({"text": ["No correlations to display"]})).mark_text(
                fontSize=14, color="gray"
            ).encode(
                text="text:N"
            ).properties(
                width=400,
                height=200,
                title="Parameter Correlations - No Data"
            )

        # Clean up labels
        df["parameter_label"] = df["parameter"].apply(self._format_metric_name)
        df["metric_label"] = df["metric"].apply(self._format_metric_name)

        # Create heatmap
        heatmap = alt.Chart(df).mark_rect().encode(
            x=alt.X("metric_label:N", title="Outcome Metric", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("parameter_label:N", title="Brewing Parameter"),
            color=alt.Color(
                "correlation:Q",
                title="Correlation",
                scale=self.get_correlation_color_scale(),
                legend=alt.Legend(orient="right"),
            ),
            tooltip=[
                alt.Tooltip("parameter_label:N", title="Parameter"),
                alt.Tooltip("metric_label:N", title="Metric"),
                alt.Tooltip("correlation:Q", title="Correlation", format=".2f"),
                alt.Tooltip("strength:N", title="Strength"),
                alt.Tooltip("sample_size:Q", title="Sample Size"),
            ],
        )

        # Add correlation values as text
        # Use a calculated field for text color based on absolute correlation
        df["text_color"] = df["correlation"].apply(
            lambda c: "white" if abs(c) > 0.5 else "black"
        )
        text = alt.Chart(df).mark_text(fontSize=12).encode(
            x=alt.X("metric_label:N"),
            y=alt.Y("parameter_label:N"),
            text=alt.Text("correlation:Q", format=".2f"),
            color=alt.Color("text_color:N", scale=None, legend=None),
        )

        chart = (heatmap + text).properties(
            width=300,
            height=250,
            title="Parameter-Outcome Correlations"
        )

        return chart

    def create_consistency_chart(self, consistency: "ConsistencyMetrics") -> alt.Chart:
        """
        Create a gauge-like chart showing consistency score.

        Args:
            consistency: ConsistencyMetrics object

        Returns:
            Altair chart visualizing consistency
        """
        # Create data for the gauge visualization
        score = consistency.consistency_score

        # Determine color based on score
        if score >= 80:
            color = "#2ca02c"  # Green - Excellent
            rating = "Excellent"
        elif score >= 60:
            color = "#17becf"  # Blue - Good
            rating = "Good"
        elif score >= 40:
            color = "#ff7f0e"  # Orange - Fair
            rating = "Fair"
        else:
            color = "#d62728"  # Red - Needs Improvement
            rating = "Needs Improvement"

        # Create bar chart for consistency score
        df = pd.DataFrame([{
            "category": "Consistency Score",
            "score": score,
            "max_score": 100,
            "rating": rating,
        }])

        # Background bar (full range)
        background = alt.Chart(df).mark_bar(color="#e0e0e0").encode(
            x=alt.X("max_score:Q", title="Score", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("category:N", title=""),
        )

        # Score bar
        foreground = alt.Chart(df).mark_bar(color=color).encode(
            x=alt.X("score:Q"),
            y=alt.Y("category:N"),
            tooltip=[
                alt.Tooltip("score:Q", title="Score", format=".1f"),
                alt.Tooltip("rating:N", title="Rating"),
            ],
        )

        # Score text
        text = alt.Chart(df).mark_text(
            align="left",
            baseline="middle",
            dx=5,
            fontSize=14,
            fontWeight="bold",
        ).encode(
            x=alt.X("score:Q"),
            y=alt.Y("category:N"),
            text=alt.Text("score:Q", format=".0f"),
            color=alt.value("white" if score > 50 else "black"),
        )

        # Combine
        scope = f"for {consistency.bean_name}" if consistency.bean_name else "Overall"
        chart = (background + foreground + text).properties(
            width=400,
            height=80,
            title=f"Brewing Consistency {scope}"
        )

        # Add metrics breakdown if available
        if consistency.extraction_cv is not None or consistency.tds_cv is not None:
            metrics_data = []
            if consistency.extraction_cv is not None:
                metrics_data.append({
                    "metric": "Extraction CV",
                    "value": consistency.extraction_cv,
                    "type": "cv",
                })
            if consistency.tds_cv is not None:
                metrics_data.append({
                    "metric": "TDS CV",
                    "value": consistency.tds_cv,
                    "type": "cv",
                })
            if consistency.rating_cv is not None:
                metrics_data.append({
                    "metric": "Rating CV",
                    "value": consistency.rating_cv,
                    "type": "cv",
                })

            if metrics_data:
                metrics_df = pd.DataFrame(metrics_data)
                # Add color column based on CV thresholds
                metrics_df["bar_color"] = metrics_df["value"].apply(
                    lambda v: "#2ca02c" if v <= 5 else ("#ff7f0e" if v <= 10 else "#d62728")
                )
                metrics_chart = alt.Chart(metrics_df).mark_bar().encode(
                    x=alt.X("value:Q", title="Coefficient of Variation (%)"),
                    y=alt.Y("metric:N", title=""),
                    color=alt.Color("bar_color:N", scale=None, legend=None),
                    tooltip=[
                        alt.Tooltip("metric:N", title="Metric"),
                        alt.Tooltip("value:Q", title="CV %", format=".1f"),
                    ],
                ).properties(
                    width=400,
                    height=100,
                    title="Consistency Breakdown (Lower is Better)"
                )

                chart = alt.vconcat(chart, metrics_chart)

        return chart

    def _format_metric_name(self, column_name: str) -> str:
        """
        Format column name for display.

        Args:
            column_name: Raw column name (e.g., "final_extraction_yield_percent")

        Returns:
            Human-readable name (e.g., "Extraction Yield %")
        """
        name_map = {
            "final_extraction_yield_percent": "Extraction %",
            "final_tds_percent": "TDS %",
            "score_overall_rating": "Overall Rating",
            "score_brew": "Brew Score",
            "grind_size": "Grind Size",
            "water_temp_degC": "Water Temp (°C)",
            "brew_ratio_to_1": "Brew Ratio",
            "brew_bloom_time_s": "Bloom Time (s)",
            "brew_total_time_s": "Total Time (s)",
            "brew_bloom_water_ml": "Bloom Water (ml)",
            "brew_pulse_target_water_ml": "Pulse Target (ml)",
            "coffee_dose_grams": "Dose (g)",
            "water_volume_ml": "Water Volume (ml)",
            "avg_extraction": "Avg Extraction %",
            "avg_tds": "Avg TDS %",
            "avg_rating": "Avg Rating",
        }
        return name_map.get(column_name, column_name.replace("_", " ").title())