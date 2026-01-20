"""
Coffee Brewing Application - Refactored

A Streamlit application for tracking and analyzing coffee brewing data.
Refactored to follow proper separation of concerns with service-oriented architecture.

This file handles UI orchestration only - business logic is extracted to services.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, List

# Import services
from src.services.data_management_service import DataManagementService
from src.services.bean_selection_service import BeanSelectionService
from src.services.form_handling_service import FormHandlingService
from src.services.visualization_service import VisualizationService
from src.services.brew_id_service import BrewIdService
from src.services.three_factor_scoring_service import ThreeFactorScoringService
from src.services.analytics_service import AnalyticsService
from src.services.extraction_analytics_service import ExtractionAnalyticsService

# Import UI components
from src.ui.streamlit_components import StreamlitComponents
from src.ui.wizard_components import WizardComponents, WizardStep, STEP_CONFIG

# Import brew device configuration
from src.config.brew_device_config import (
    BREW_DEVICE_CONFIG,
    get_device_config,
    get_device_fields,
    get_device_category,
    DeviceCategory,
)


class CoffeeBrewingApp:
    """Main application orchestrator for coffee brewing data management"""
    
    def __init__(self):
        # Initialize services
        self.data_service = DataManagementService()
        self.bean_service = BeanSelectionService()
        self.form_service = FormHandlingService()
        self.viz_service = VisualizationService()
        self.brew_id_service = BrewIdService()
        self.scoring_service = ThreeFactorScoringService()
        self.analytics_service = AnalyticsService()
        self.extraction_service = ExtractionAnalyticsService()

        # Initialize UI components
        self.ui = StreamlitComponents()
        self.wizard = WizardComponents()

        # Initialize session state
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables"""
        if 'df' not in st.session_state:
            st.session_state.df = self.data_service.load_data()
        if 'selected_row' not in st.session_state:
            st.session_state.selected_row = None
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False
        if 'recent_additions' not in st.session_state:
            st.session_state.recent_additions = []
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = 0
    
    def _cleanup_expired_recent_additions(self):
        """Remove recent additions older than 15 minutes"""
        if 'recent_additions' not in st.session_state:
            return
        
        cutoff_time = datetime.now() - timedelta(minutes=15)
        st.session_state.recent_additions = [
            addition for addition in st.session_state.recent_additions
            if addition['timestamp'] > cutoff_time
        ]
    
    def _add_recent_addition(self, brew_id: int):
        """Add a brew ID to recent additions list"""
        self._cleanup_expired_recent_additions()
        
        # Remove any existing entry for this brew_id to avoid duplicates
        st.session_state.recent_additions = [
            addition for addition in st.session_state.recent_additions
            if addition['brew_id'] != brew_id
        ]
        
        # Add new entry
        st.session_state.recent_additions.append({
            'brew_id': brew_id,
            'timestamp': datetime.now()
        })
    
    def _get_recent_brew_ids(self) -> list:
        """Get list of recently added brew IDs (within 15 minutes)"""
        self._cleanup_expired_recent_additions()
        return [addition['brew_id'] for addition in st.session_state.recent_additions]
    
    def run(self):
        """Run the main application"""
        # Page Title
        st.title("☕️ Fiends for the Beans")
        
        # Handle automatic navigation to View Data tab after cup addition
        if st.session_state.get('auto_navigate_to_chart', False):
            st.session_state.auto_navigate_to_chart = False
            # Show navigation message and switch to View Data tab
            st.success("🎉 **Redirecting to View Data page...** Your new cup is highlighted on the chart!")
            st.rerun()
        
        # Create tabs for different operations
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 View Data", "📈 Analytics", "➕ Add Cup", "✏️ Data Management", "🗑️ Delete Cups", "⚙️ Processing"
        ])

        # Clean up expired recent additions on each run
        self._cleanup_expired_recent_additions()

        with tab1:
            self._render_view_data_tab()

        with tab2:
            self._render_analytics_tab()

        with tab3:
            self._render_add_cup_tab()

        with tab4:
            self._render_data_management_tab()

        with tab5:
            self._render_delete_cups_tab()

        with tab6:
            self._render_processing_tab()
    
    def _render_view_data_tab(self):
        """Render the data visualization tab"""
        
        # Show special welcome message if user just added a cup
        if st.session_state.get('latest_brew_id') and st.session_state.get('show_view_chart_btn', False):
            self._show_new_cup_welcome()
        
        st.header("Brew performance")
        st.write("Plot the brewing data based on the brewing control chart: https://sca.coffee/sca-news/25/issue-13/towards-a-new-brewing-chart")
        
        # Get recent additions for highlighting
        recent_brew_ids = self._get_recent_brew_ids()
        
        # Show recent additions info if any exist
        if recent_brew_ids:
            if st.session_state.get('show_view_chart_btn', False):
                # Enhanced message for just-added cups
                st.success(f"🎯 **Your new cup (#{st.session_state.get('latest_brew_id')}) is highlighted below!** Plus {len(recent_brew_ids)-1} other recent addition(s)" if len(recent_brew_ids) > 1 else f"🎯 **Your new cup (#{st.session_state.get('latest_brew_id')}) is highlighted below!**")
                # Clear the flag after showing the message
                st.session_state.show_view_chart_btn = False
            else:
                st.info(f"🆕 **{len(recent_brew_ids)} recent addition(s)** highlighted on chart (last 15 minutes)")
        
        # Render brewing control chart with filters and recent highlights
        chart_data = self.ui.render_brewing_control_chart(
            st.session_state.df, 
            show_filters=True, 
            recent_brew_ids=recent_brew_ids
        )
        
        # Display raw data logs
        st.header("Brew logs")
        st.write("Cup data logged")
        st.dataframe(chart_data, use_container_width=True)

    def _render_analytics_tab(self):
        """Render the analytics and insights tab - focused on extraction drivers"""
        st.header("Extraction Analytics")
        st.write("Understand which brewing parameters drive extraction in your brews.")

        df = st.session_state.df

        if df.empty or len(df) < 3:
            st.warning("You need at least 3 brews to see meaningful analytics. Keep brewing!")
            return

        # Get extraction insights
        insights = self.extraction_service.get_extraction_insights(df)
        drivers = insights.drivers

        # Summary metrics row - extraction focused
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Brews Analyzed", drivers.total_brews_analyzed)
        with col2:
            avg_ext = f"{drivers.avg_extraction:.1f}%" if drivers.avg_extraction else "N/A"
            st.metric("Avg Extraction", avg_ext)
        with col3:
            if drivers.extraction_range[0] and drivers.extraction_range[1]:
                range_str = f"{drivers.extraction_range[0]:.1f} - {drivers.extraction_range[1]:.1f}%"
            else:
                range_str = "N/A"
            st.metric("Extraction Range", range_str)
        with col4:
            top_driver = drivers.parameter_impacts[0] if drivers.parameter_impacts else None
            driver_str = top_driver.parameter_display_name if top_driver else "N/A"
            st.metric("Top Driver", driver_str)

        st.markdown("---")

        # Create sub-tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "What Drives Extraction?", "By Method", "Parameter Plots", "Other Insights"
        ])

        with tab1:
            self._render_extraction_drivers_section(df, drivers)

        with tab2:
            self._render_method_analysis_section(df, insights.method_analysis)

        with tab3:
            self._render_parameter_plots_section(df, insights.parameter_plots)

        with tab4:
            self._render_other_insights_section(df)

    def _render_trends_section(self, df: pd.DataFrame):
        """Render the trends analysis section"""
        st.subheader("Improvement Trends")
        st.write("Track how your brewing metrics have changed over time.")

        col1, col2 = st.columns([1, 1])

        with col1:
            metric_options = {
                "Overall Rating": "score_overall_rating",
                "Extraction Yield": "final_extraction_yield_percent",
                "TDS": "final_tds_percent",
            }
            selected_metric = st.selectbox(
                "Metric to analyze",
                options=list(metric_options.keys()),
                key="trend_metric"
            )

        with col2:
            window_days = st.slider(
                "Time window (days)",
                min_value=7,
                max_value=90,
                value=30,
                key="trend_window"
            )

        metric_column = metric_options[selected_metric]
        trend_data = self.analytics_service.calculate_improvement_trend(
            df, metric_column, window_days
        )

        if trend_data.is_meaningful:
            # Show trend summary
            trend_icon = {"improving": "📈", "declining": "📉", "stable": "➡️"}
            trend_color = {"improving": "green", "declining": "red", "stable": "gray"}

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Trend Direction",
                    f"{trend_icon.get(trend_data.trend_direction, '')} {trend_data.trend_direction.title()}"
                )
            with col2:
                change_prefix = "+" if trend_data.percent_change > 0 else ""
                st.metric("Change", f"{change_prefix}{trend_data.percent_change:.1f}%")
            with col3:
                st.metric("Data Points", trend_data.sample_size)

            # Show trend chart
            chart = self.viz_service.create_trend_chart(trend_data)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info(f"Not enough data in the last {window_days} days for trend analysis. "
                   f"Found {trend_data.sample_size} brews (need at least 3).")

    def _render_bean_comparison_section(self, df: pd.DataFrame):
        """Render the bean comparison section"""
        st.subheader("Bean Comparison")
        st.write("Compare performance across different coffee beans.")

        # Get unique beans
        unique_beans = df['bean_name'].dropna().unique().tolist()

        if len(unique_beans) < 2:
            st.info("You need at least 2 different beans to compare.")
            return

        selected_beans = st.multiselect(
            "Select beans to compare",
            options=sorted(unique_beans),
            default=sorted(unique_beans)[:min(3, len(unique_beans))],
            key="comparison_beans"
        )

        if len(selected_beans) < 2:
            st.warning("Please select at least 2 beans to compare.")
            return

        comparison_data = self.analytics_service.calculate_bean_comparison(df, selected_beans)

        # Show confidence indicator
        confidence_colors = {"high": "green", "medium": "orange", "low": "red", "insufficient": "gray"}
        st.caption(f"Confidence level: **{comparison_data.confidence_level}** "
                  f"(minimum {comparison_data.min_sample_size} samples per bean)")

        # Show comparison chart
        chart = self.viz_service.create_comparison_chart(comparison_data)
        st.altair_chart(chart, use_container_width=True)

        # Show detailed metrics table
        with st.expander("Detailed Metrics"):
            metrics_data = []
            for bean_name, metrics in comparison_data.bean_metrics.items():
                metrics_data.append({
                    "Bean": bean_name,
                    "Brews": metrics.sample_size,
                    "Avg Extraction": f"{metrics.avg_extraction:.1f}%" if metrics.avg_extraction else "N/A",
                    "Avg TDS": f"{metrics.avg_tds:.2f}%" if metrics.avg_tds else "N/A",
                    "Avg Rating": f"{metrics.avg_rating:.1f}" if metrics.avg_rating else "N/A",
                    "Best Rating": f"{metrics.best_rating:.1f}" if metrics.best_rating else "N/A",
                })
            st.dataframe(pd.DataFrame(metrics_data), use_container_width=True, hide_index=True)

    def _render_correlations_section(self, df: pd.DataFrame):
        """Render the parameter correlations section"""
        st.subheader("Parameter Correlations")
        st.write("Discover which brewing parameters most influence your results.")

        correlations = self.analytics_service.calculate_parameter_correlations(df)

        if not correlations:
            st.info("Not enough data to calculate correlations. Need at least 3 brews with parameter data.")
            return

        # Filter to meaningful correlations
        meaningful_correlations = [c for c in correlations if c.is_meaningful and c.strength != "none"]

        if meaningful_correlations:
            # Show heatmap
            chart = self.viz_service.create_correlation_heatmap(correlations)
            st.altair_chart(chart, use_container_width=True)

            # Show top correlations
            st.markdown("#### Key Findings")
            strong_correlations = [c for c in meaningful_correlations if c.strength in ["strong", "moderate"]]

            if strong_correlations:
                for corr in sorted(strong_correlations, key=lambda x: abs(x.correlation), reverse=True)[:5]:
                    direction_icon = "📈" if corr.direction == "positive" else "📉"
                    st.write(f"{direction_icon} **{corr.summary}**")
            else:
                st.info("No strong or moderate correlations found. Your brewing parameters may be "
                       "well-optimized, or more data is needed.")
        else:
            st.info("No significant correlations found. This could mean your brewing is already "
                   "well-optimized, or try varying your parameters more to see their effects.")

    def _render_consistency_section(self, df: pd.DataFrame):
        """Render the consistency metrics section"""
        st.subheader("Brewing Consistency")
        st.write("How consistent are you in achieving similar results?")

        # Bean filter
        unique_beans = ["All Beans"] + sorted(df['bean_name'].dropna().unique().tolist())
        selected_bean = st.selectbox(
            "Analyze consistency for",
            options=unique_beans,
            key="consistency_bean"
        )

        bean_name = None if selected_bean == "All Beans" else selected_bean
        consistency = self.analytics_service.calculate_consistency_metrics(df, bean_name)

        if not consistency.is_meaningful:
            st.info(f"Need at least 3 brews to analyze consistency. "
                   f"Currently have {consistency.sample_size} brews.")
            return

        # Show consistency chart
        chart = self.viz_service.create_consistency_chart(consistency)
        st.altair_chart(chart, use_container_width=True)

        # Interpretation
        st.markdown("#### What This Means")
        rating = consistency.consistency_rating

        if rating == "excellent":
            st.success("Your brewing is highly consistent! You're reliably reproducing "
                      "similar results across brews.")
        elif rating == "good":
            st.info("Your brewing is fairly consistent. There's some variation, but "
                   "you're generally in control of your process.")
        elif rating == "fair":
            st.warning("Your brewing shows moderate variation. Consider standardizing "
                      "your process more - weigh precisely, time consistently, etc.")
        else:
            st.error("Your brewing shows high variation. Focus on controlling one variable "
                    "at a time to improve consistency.")

    def _render_extraction_drivers_section(self, df: pd.DataFrame, drivers):
        """Render the main extraction drivers analysis"""
        st.subheader("What Drives Your Extraction?")
        st.write("Parameters ranked by their correlation with extraction yield. "
                "Green bars = higher values increase extraction. Red bars = higher values decrease extraction.")

        if not drivers.parameter_impacts:
            st.info("Not enough data to analyze extraction drivers. Need at least 3 brews with extraction data.")
            return

        # Show the main drivers chart
        chart = self.viz_service.create_extraction_drivers_chart(drivers)
        st.altair_chart(chart, use_container_width=True)

        # Show actionable insights
        st.markdown("#### Actionable Insights")

        top_drivers = drivers.top_drivers
        if top_drivers:
            for impact in top_drivers[:3]:  # Show top 3
                direction_icon = "📈" if impact.impact_direction == "positive" else "📉"
                st.write(f"{direction_icon} **{impact.parameter_display_name}** ({impact.impact_strength} impact)")
                st.caption(impact.actionable_insight)
        else:
            st.info("No strong correlations found. This could mean: "
                   "(1) your parameters are already optimized, "
                   "(2) you need more variation in experiments, or "
                   "(3) other factors (beans, water) may dominate.")

        # Show summary
        st.markdown("---")
        st.caption(drivers.summary)

    def _render_method_analysis_section(self, df: pd.DataFrame, method_analysis):
        """Render extraction comparison by brew method"""
        st.subheader("Extraction by Brew Method")
        st.write("Compare how different brewing methods perform for extraction.")

        if not method_analysis.method_comparisons:
            st.info("Not enough data to compare methods. Need at least 3 brews per method.")
            return

        # Method comparison chart
        chart = self.viz_service.create_method_comparison_chart(method_analysis)
        st.altair_chart(chart, use_container_width=True)

        # Best method highlight
        best = method_analysis.best_method
        if best:
            st.success(f"**Best for extraction:** {best.method_name} "
                      f"(avg {best.avg_extraction:.1f}%, best {best.best_extraction:.1f}%)")

        # Detailed table
        with st.expander("Method Details"):
            method_data = []
            for m in method_analysis.method_comparisons:
                method_data.append({
                    "Method": m.method_name,
                    "Device": m.device_name or "N/A",
                    "Brews": m.brew_count,
                    "Avg Extraction": f"{m.avg_extraction:.1f}%" if m.avg_extraction else "N/A",
                    "Best Extraction": f"{m.best_extraction:.1f}%" if m.best_extraction else "N/A",
                    "Best Grind": f"{m.best_grind:.1f}" if m.best_grind else "N/A",
                    "Best Temp": f"{m.best_temp:.0f}°C" if m.best_temp else "N/A",
                })
            st.dataframe(pd.DataFrame(method_data), use_container_width=True, hide_index=True)

    def _render_parameter_plots_section(self, df: pd.DataFrame, parameter_plots):
        """Render scatter plots of parameter vs extraction"""
        st.subheader("Parameter vs Extraction")
        st.write("Scatter plots showing how each parameter relates to extraction. "
                "Dashed line shows the trend.")

        if not parameter_plots:
            st.info("Not enough data to create parameter plots.")
            return

        # Create 2x2 grid of scatter plots
        params = list(parameter_plots.keys())

        for i in range(0, len(params), 2):
            col1, col2 = st.columns(2)

            with col1:
                if i < len(params):
                    plot_data = parameter_plots[params[i]]
                    chart = self.viz_service.create_parameter_scatter(plot_data)
                    st.altair_chart(chart, use_container_width=True)
                    st.caption(plot_data.trend_description)

            with col2:
                if i + 1 < len(params):
                    plot_data = parameter_plots[params[i + 1]]
                    chart = self.viz_service.create_parameter_scatter(plot_data)
                    st.altair_chart(chart, use_container_width=True)
                    st.caption(plot_data.trend_description)

    def _render_other_insights_section(self, df: pd.DataFrame):
        """Render additional analytics (trends, consistency) as secondary"""
        st.subheader("Additional Insights")

        # Sub-tabs for secondary analytics
        sub1, sub2 = st.tabs(["Trends", "Consistency"])

        with sub1:
            self._render_trends_section(df)

        with sub2:
            self._render_consistency_section(df)

    def _render_add_cup_tab(self):
        """Render the add new cup tab with modern wizard UX"""
        st.header("Add new cup")

        # Initialize wizard session state
        if 'wizard_step' not in st.session_state:
            st.session_state.wizard_step = 0
        if 'wizard_form_data' not in st.session_state:
            st.session_state.wizard_form_data = {}
        if 'add_brew_device' not in st.session_state:
            st.session_state.add_brew_device = "V60 ceramic"

        current_step = st.session_state.wizard_step

        # Render progress stepper
        self.wizard.render_progress_stepper(current_step)

        # Quick actions bar (only on first step)
        if current_step == 0:
            action = self.wizard.render_quick_actions_bar(st.session_state.df)
            if action == "repeat_last":
                defaults = self.wizard.get_last_brew_defaults(st.session_state.df)
                st.session_state.wizard_form_data.update(defaults)
                st.success("Loaded settings from your last brew!")
                st.rerun()
            elif action == "use_best":
                defaults = self.wizard.get_best_brew_defaults(st.session_state.df)
                st.session_state.wizard_form_data.update(defaults)
                st.success("Loaded settings from your best-rated brew!")
                st.rerun()
            elif action == "fresh":
                st.session_state.wizard_form_data = {}
                st.info("Starting fresh with default values")

        st.markdown("---")

        # Render current step content
        step_valid = False

        if current_step == 0:
            step_valid = self._render_wizard_step_bean()
        elif current_step == 1:
            step_valid = self._render_wizard_step_equipment()
        elif current_step == 2:
            step_valid = self._render_wizard_step_brew()
        elif current_step == 3:
            step_valid = self._render_wizard_step_results()

        # Navigation buttons
        is_final = current_step == 3
        go_back, go_next, submit = self.wizard.render_navigation_buttons(
            current_step, total_steps=4, can_proceed=step_valid, is_final=is_final
        )

        if go_back:
            st.session_state.wizard_step = max(0, current_step - 1)
            st.rerun()

        if go_next:
            st.session_state.wizard_step = min(3, current_step + 1)
            st.rerun()

        if submit:
            self._handle_wizard_submission()

    def _render_wizard_step_bean(self) -> bool:
        """Render Step 1: Bean Selection - Returns True if valid"""
        self.wizard.render_step_header(WizardStep.BEAN)

        # Get stored form data
        form_data = st.session_state.wizard_form_data

        # Brew date (at top for context)
        brew_date = st.date_input(
            "Brew Date",
            value=form_data.get('brew_date', date.today()),
            key="wizard_brew_date"
        )
        form_data['brew_date'] = brew_date

        st.markdown("---")

        # Bean Selection Component
        selected_bean_data = self.ui.render_bean_selection_component(
            st.session_state.df,
            context="add",
            key_prefix="wizard_"
        )

        # Bean Information Form
        with st.expander("Bean Details", expanded=selected_bean_data is None):
            bean_form_data = self.ui.render_bean_information_form(
                context="add",
                selected_bean_data=selected_bean_data,
                key_prefix="wizard_"
            )

            # Inventory tracking for new beans
            estimated_bag_size_grams = None
            if selected_bean_data is None:
                st.markdown("#### Inventory Tracking (Optional)")
                estimated_bag_size_grams = st.number_input(
                    "Bag Size (grams)",
                    min_value=0.0,
                    value=form_data.get('estimated_bag_size_grams', 0.0),
                    step=25.0,
                    help="Track usage and get low-stock alerts",
                    key="wizard_bag_size"
                )
            else:
                estimated_bag_size_grams = selected_bean_data.get('estimated_bag_size_grams', 0) or 0

        # Save to form data
        form_data.update(bean_form_data)
        form_data['estimated_bag_size_grams'] = estimated_bag_size_grams
        st.session_state.wizard_form_data = form_data

        # Validation: at minimum need bean name
        is_valid = bool(bean_form_data.get('bean_name', '').strip())

        if not is_valid:
            st.warning("Please enter a bean name to continue")

        return is_valid

    def _render_wizard_step_equipment(self) -> bool:
        """Render Step 2: Equipment Setup - Returns True if valid"""
        self.wizard.render_step_header(WizardStep.EQUIPMENT)

        form_data = st.session_state.wizard_form_data

        # Show what bean was selected (context)
        if form_data.get('bean_name'):
            st.info(f"Bean: **{form_data['bean_name']}** from {form_data.get('bean_origin_country', 'Unknown')}")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Grinder")

            grind_size = self.ui.render_grind_size_dial(
                "Grind Size",
                current_value=form_data.get('grind_size', 6.0),
                key="wizard_grind_size"
            )

            grind_model = st.text_input(
                "Grinder Model",
                value=form_data.get('grind_model', 'Fellow Ode Gen 2'),
                placeholder="e.g., Fellow Ode Gen 2",
                key="wizard_grind_model"
            )

        with col2:
            st.subheader("Brew Device")

            brew_devices = self.form_service.get_brew_devices()
            current_device = form_data.get('brew_device', st.session_state.add_brew_device)
            device_index = brew_devices.index(current_device) if current_device in brew_devices else 1

            brew_device = st.selectbox(
                "Select Device",
                brew_devices,
                index=device_index,
                key="wizard_brew_device",
                help="This determines which brew parameters you'll see next"
            )

            # Show device info
            device_config = get_device_config(brew_device)
            if device_config:
                category = device_config.get('category', 'unknown')
                st.caption(f"Category: {category.replace('_', ' ').title()}")

        # Save to form data
        form_data['grind_size'] = grind_size
        form_data['grind_model'] = grind_model
        form_data['brew_device'] = brew_device
        st.session_state.add_brew_device = brew_device
        st.session_state.wizard_form_data = form_data

        # Always valid (grind has defaults)
        return True

    def _render_wizard_step_brew(self) -> bool:
        """Render Step 3: Brew Parameters - Returns True if valid"""
        self.wizard.render_step_header(WizardStep.BREW)

        form_data = st.session_state.wizard_form_data
        brew_device = form_data.get('brew_device', 'V60 ceramic')

        # Context bar
        st.info(f"Brewing **{form_data.get('bean_name', 'coffee')}** with **{brew_device}** at grind **{form_data.get('grind_size', 6)}**")

        # Core parameters
        st.subheader("Core Parameters")
        core_col1, core_col2, core_col3, core_col4 = st.columns(4)

        with core_col1:
            water_temp = st.number_input(
                "Water Temp (°C)",
                min_value=70.0,
                max_value=100.0,
                value=form_data.get('water_temp_degC') or 96.0,
                step=0.5,
                key="wizard_water_temp"
            )

        with core_col2:
            coffee_dose = st.number_input(
                "Coffee Dose (g)",
                min_value=0.0,
                value=form_data.get('coffee_dose_grams') or 18.0,
                step=0.1,
                key="wizard_coffee_dose"
            )

        with core_col3:
            # Mug weight - placed after dose since workflow is: weigh grinds, then put mug on scale
            mug_weight = st.number_input(
                "Mug Weight (g)",
                min_value=0.0,
                value=form_data.get('mug_weight_grams'),
                step=0.1,
                help="Weight of empty mug",
                key="wizard_mug_weight"
            )

        with core_col4:
            water_volume = st.number_input(
                "Water Volume (ml)",
                min_value=0.0,
                value=form_data.get('water_volume_ml') or 300.0,
                step=1.0,
                key="wizard_water_volume"
            )

        # Show calculated ratio
        if coffee_dose and water_volume and coffee_dose > 0:
            ratio = water_volume / coffee_dose
            st.caption(f"Brew Ratio: **1:{ratio:.1f}**")

        st.markdown("---")

        # Method field
        brew_method = st.text_input(
            "Brew Method",
            value=form_data.get('brew_method', ''),
            placeholder="e.g., Hoffmann V60, Switch hybrid",
            key="wizard_brew_method"
        )

        # Device-specific fields
        st.markdown("---")
        st.subheader(f"{brew_device} Settings")

        device_specific_data = self._render_dynamic_brew_fields(brew_device, key_prefix="wizard")

        # For Hario Switch, timing and weight are handled in device-specific section
        is_hario_switch = brew_device == "Hario Switch"

        if is_hario_switch:
            brew_total_time = device_specific_data.get('brew_total_time_s')
            final_weight = device_specific_data.get('final_combined_weight_grams')
        else:
            # For all other devices, show timing and weight at bottom (measured at end of brew)
            st.markdown("---")
            st.caption("**Post-Brew Measurements** *(recorded after brewing completes)*")

            # Time input in MM'SS" format
            brew_total_time = self.wizard.render_time_input(
                "Total Brew Time",
                form_data.get('brew_total_time_s'),
                key="wizard_brew_time"
            )

            final_weight = st.number_input(
                "Final Combined Weight (g)",
                min_value=0.0,
                value=form_data.get('final_combined_weight_grams'),
                step=0.1,
                help="Mug + coffee after brewing",
                key="wizard_final_weight"
            )

        # Save all to form data
        form_data['water_temp_degC'] = water_temp
        form_data['coffee_dose_grams'] = coffee_dose
        form_data['mug_weight_grams'] = mug_weight
        form_data['water_volume_ml'] = water_volume
        form_data['brew_method'] = brew_method
        form_data['brew_total_time_s'] = brew_total_time
        form_data['final_combined_weight_grams'] = final_weight
        form_data['device_specific_data'] = device_specific_data
        st.session_state.wizard_form_data = form_data

        # Validation: need at least dose and volume
        is_valid = coffee_dose is not None and coffee_dose > 0

        if not is_valid:
            st.warning("Please enter a coffee dose to continue")

        return is_valid

    def _render_wizard_step_results(self) -> bool:
        """Render Step 4: Results & Scoring - Returns True if valid"""
        self.wizard.render_step_header(WizardStep.RESULTS)

        form_data = st.session_state.wizard_form_data

        # Summary of what was brewed
        st.markdown("### Brew Summary")
        summary_cols = st.columns(4)
        with summary_cols[0]:
            st.metric("Bean", form_data.get('bean_name', 'Unknown')[:15])
        with summary_cols[1]:
            st.metric("Device", form_data.get('brew_device', 'Unknown'))
        with summary_cols[2]:
            dose = form_data.get('coffee_dose_grams', 0)
            volume = form_data.get('water_volume_ml', 0)
            ratio = f"1:{volume/dose:.1f}" if dose else "N/A"
            st.metric("Ratio", ratio)
        with summary_cols[3]:
            st.metric("Grind", form_data.get('grind_size', 'N/A'))

        st.markdown("---")

        # Results
        st.subheader("Measurements")
        result_col1, result_col2 = st.columns(2)

        with result_col1:
            final_tds = st.number_input(
                "TDS %",
                min_value=0.0,
                max_value=5.0,
                value=form_data.get('final_tds_percent'),
                step=0.01,
                help="Total Dissolved Solids measurement",
                key="wizard_tds"
            )

        with result_col2:
            flavor_profiles = self.form_service.get_flavor_profiles()
            current_flavor = form_data.get('score_flavor_profile_category', '')
            flavor_index = flavor_profiles.index(current_flavor) if current_flavor in flavor_profiles else 0

            score_flavor = st.selectbox(
                "Flavor Profile",
                flavor_profiles,
                index=flavor_index,
                key="wizard_flavor_profile"
            )

        # Three-Factor Scoring
        st.markdown("---")
        st.subheader("Three-Factor Scoring")
        st.caption("Rate each aspect 0-5 stars (half-stars allowed)")

        score_col1, score_col2, score_col3 = st.columns(3)

        with score_col1:
            st.markdown("**Complexity**")
            st.caption("Flavor layers & nuance")
            score_complexity = st.slider(
                "Complexity",
                min_value=0.0,
                max_value=5.0,
                value=form_data.get('score_complexity', 2.5),
                step=0.5,
                key="wizard_complexity",
                label_visibility="collapsed"
            )

        with score_col2:
            st.markdown("**Bitterness Balance**")
            st.caption("Pleasant vs overpowering")
            score_bitterness = st.slider(
                "Bitterness",
                min_value=0.0,
                max_value=5.0,
                value=form_data.get('score_bitterness', 2.5),
                step=0.5,
                key="wizard_bitterness",
                label_visibility="collapsed"
            )

        with score_col3:
            st.markdown("**Mouthfeel**")
            st.caption("Body & texture")
            score_mouthfeel = st.slider(
                "Mouthfeel",
                min_value=0.0,
                max_value=5.0,
                value=form_data.get('score_mouthfeel', 2.5),
                step=0.5,
                key="wizard_mouthfeel",
                label_visibility="collapsed"
            )

        # Calculate overall score
        scores = {'complexity': score_complexity, 'bitterness': score_bitterness, 'mouthfeel': score_mouthfeel}
        validation = self.scoring_service.validate_all_scores(scores)
        if validation.is_valid:
            score_overall = self.scoring_service.calculate_overall_score(scores)
        else:
            score_overall = 2.5

        # Display overall
        st.markdown(f"### Overall Score: **{score_overall:.1f}/5**")

        # Notes
        score_notes = st.text_area(
            "Tasting Notes",
            value=form_data.get('score_notes', ''),
            placeholder="Describe the flavors, aromas, and your overall impression...",
            height=100,
            key="wizard_notes"
        )

        # Save to form data
        form_data['final_tds_percent'] = final_tds
        form_data['score_flavor_profile_category'] = score_flavor
        form_data['score_complexity'] = score_complexity
        form_data['score_bitterness'] = score_bitterness
        form_data['score_mouthfeel'] = score_mouthfeel
        form_data['score_overall_rating'] = score_overall
        form_data['score_notes'] = score_notes
        st.session_state.wizard_form_data = form_data

        # Always valid (scoring has defaults)
        return True

    def _handle_wizard_submission(self):
        """Handle final submission from wizard"""
        form_data = st.session_state.wizard_form_data

        # Get next brew ID
        current_df = self.data_service.load_data()
        brew_id = self.data_service.get_next_brew_id(current_df)

        # Prepare bean form data structure
        bean_form_data = {
            'bean_name': form_data.get('bean_name'),
            'bean_origin_country': form_data.get('bean_origin_country'),
            'bean_origin_region': form_data.get('bean_origin_region'),
            'bean_variety': form_data.get('bean_variety'),
            'bean_process_method': form_data.get('bean_process_method'),
            'bean_roast_date': form_data.get('bean_roast_date'),
            'bean_roast_level': form_data.get('bean_roast_level'),
            'bean_notes': form_data.get('bean_notes'),
        }

        # Show immediate feedback
        self._show_immediate_submission_feedback(brew_id, form_data.get('bean_name', 'Unknown Bean'))

        # Call the existing submission handler
        self._handle_add_cup_submission(
            brew_id=brew_id,
            brew_date=form_data.get('brew_date', date.today()),
            bean_form_data=bean_form_data,
            grind_size=form_data.get('grind_size', 6.0),
            grind_model=form_data.get('grind_model', 'Fellow Ode Gen 2'),
            brew_device=form_data.get('brew_device', 'V60 ceramic'),
            water_temp_degC=form_data.get('water_temp_degC'),
            coffee_dose_grams=form_data.get('coffee_dose_grams'),
            water_volume_ml=form_data.get('water_volume_ml'),
            mug_weight_grams=form_data.get('mug_weight_grams'),
            brew_method=form_data.get('brew_method'),
            brew_total_time_s=form_data.get('brew_total_time_s'),
            final_combined_weight_grams=form_data.get('final_combined_weight_grams'),
            final_tds_percent=form_data.get('final_tds_percent'),
            score_flavor_profile_category=form_data.get('score_flavor_profile_category'),
            score_overall_rating=form_data.get('score_overall_rating'),
            score_notes=form_data.get('score_notes'),
            estimated_bag_size_grams=form_data.get('estimated_bag_size_grams'),
            score_complexity=form_data.get('score_complexity', 2.5),
            score_bitterness=form_data.get('score_bitterness', 2.5),
            score_mouthfeel=form_data.get('score_mouthfeel', 2.5),
            device_specific_data=form_data.get('device_specific_data', {})
        )

        # Reset wizard after successful submission
        st.session_state.wizard_step = 0
        st.session_state.wizard_form_data = {}
    
    def _handle_add_cup_submission(self, brew_id, brew_date, bean_form_data, grind_size,
                                   grind_model, brew_device, water_temp_degC, coffee_dose_grams,
                                   water_volume_ml, mug_weight_grams, brew_method,
                                   brew_total_time_s, final_combined_weight_grams, final_tds_percent,
                                   score_flavor_profile_category, score_overall_rating,
                                   score_notes, estimated_bag_size_grams, score_complexity,
                                   score_bitterness, score_mouthfeel, device_specific_data=None):
        """Handle form submission for adding a new cup"""

        if device_specific_data is None:
            device_specific_data = {}

        # Prepare form data - core fields
        form_data = {
            'brew_date': brew_date,
            'bean_name': bean_form_data['bean_name'],
            'bean_origin_country': bean_form_data['bean_origin_country'],
            'bean_origin_region': bean_form_data['bean_origin_region'],
            'bean_variety': bean_form_data['bean_variety'],
            'bean_process_method': bean_form_data['bean_process_method'],
            'bean_roast_date': bean_form_data['bean_roast_date'],
            'bean_roast_level': bean_form_data['bean_roast_level'],
            'bean_notes': bean_form_data['bean_notes'],
            'grind_size': grind_size,
            'grind_model': grind_model,
            'brew_device': brew_device,
            'water_temp_degC': water_temp_degC,
            'coffee_dose_grams': coffee_dose_grams,
            'water_volume_ml': water_volume_ml,
            'mug_weight_grams': mug_weight_grams,
            'brew_method': brew_method,
            'brew_total_time_s': brew_total_time_s,
            'final_combined_weight_grams': final_combined_weight_grams,
            'final_tds_percent': final_tds_percent,
            'score_flavor_profile_category': score_flavor_profile_category,
            'score_overall_rating': score_overall_rating,
            'score_notes': score_notes,
            'score_complexity': score_complexity,
            'score_bitterness': score_bitterness,
            'score_mouthfeel': score_mouthfeel,
            'scoring_system_version': '3-factor-v1'
        }

        # Merge device-specific fields into form_data
        form_data.update(device_specific_data)
        
        # Show progress indicators with visual progress bar
        import time
        progress_container = st.empty()
        progress_bar = st.progress(0)
        
        # Step 1: Prepare brew record
        progress_container.info("📝 **Step 1/4:** Preparing brew record...")
        progress_bar.progress(25)
        new_record = self.form_service.prepare_brew_record(form_data, brew_id, estimated_bag_size_grams)
        
        # Step 2: Add to DataFrame
        progress_container.info("💾 **Step 2/4:** Adding record to database...")
        progress_bar.progress(50)
        st.session_state.df = self.data_service.add_record(st.session_state.df, new_record)
        
        # Step 3: Save to CSV
        progress_container.info("💾 **Step 3/4:** Saving data to file...")
        progress_bar.progress(75)
        if not self.data_service.save_data(st.session_state.df):
            progress_container.error("❌ **Failed to save data**")
            progress_bar.empty()
            return
        
        # Step 4: Run post-processing (this takes the most time)
        progress_container.info("🔄 **Step 4/4:** Running calculations (TDS, extraction yield, scores)...")
        progress_bar.progress(90)
        success, stdout, stderr = self.data_service.run_post_processing()
        
        if success:
            # Complete progress and show success
            progress_bar.progress(100)
            progress_container.success("✅ **All steps completed!** Processing brew data...")
            time.sleep(0.3)  # Brief completion display
            
            # Reload the data to get the calculated fields
            st.session_state.df = self.data_service.load_data()
            
            # Add to recent additions for highlighting
            self._add_recent_addition(brew_id)
            
            # Clear progress indicators before celebration
            progress_container.empty()
            progress_bar.empty()
            
            # Enhanced visual celebration with animated elements
            self._show_cup_added_celebration(brew_id, bean_form_data, form_data)
            
            # Set session state for automatic navigation
            st.session_state.show_view_chart_btn = True
            st.session_state.latest_brew_id = brew_id
            st.session_state.auto_navigate_to_chart = True
            
            # Show contextual archive prompt if bag might be running low
            if estimated_bag_size_grams and estimated_bag_size_grams > 0 and coffee_dose_grams:
                self._show_bean_usage_alert(
                    bean_form_data['bean_name'],
                    bean_form_data['bean_origin_country'],
                    bean_form_data['bean_origin_region'],
                    estimated_bag_size_grams
                )
        else:
            # Clear progress and show warning
            progress_container.empty()
            progress_bar.empty()
            st.error("⚠️ **Processing Failed:** Cup was saved but calculations failed. Some fields may be missing.")
        
        # Show processing status if there are details to show
        if stdout or stderr:
            self.ui.render_processing_status(success, stdout, stderr)
        
        st.rerun()
    
    def _show_cup_added_celebration(self, brew_id: int, bean_form_data: dict, form_data: dict):
        """Show animated celebration when a cup is added successfully"""
        
        # Create animated celebration banner
        bean_name = bean_form_data.get('bean_name', 'Unknown Bean')
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #4CAF50, #45a049, #4CAF50);
            background-size: 200% 200%;
            animation: gradient 2s ease infinite;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        ">
        <style>
        @keyframes gradient {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        @keyframes bounce {{
            0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }}
            40% {{ transform: translateY(-10px); }}
            60% {{ transform: translateY(-5px); }}
        }}
        .celebration-emoji {{
            animation: bounce 2s infinite;
            display: inline-block;
            font-size: 2em;
        }}
        </style>
        <div class="celebration-emoji">☕</div>
        <h2 style="margin: 10px 0; font-size: 1.5em;">Cup Added Successfully!</h2>
        <p style="margin: 5px 0; font-size: 1.1em;">Cup #{brew_id} • {bean_name}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show quick brew summary with visual elements
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📊 TDS", 
                f"{form_data.get('final_tds_percent', 0):.2f}%" if form_data.get('final_tds_percent') else "Not measured",
                help="Total Dissolved Solids"
            )
        
        with col2:
            st.metric(
                "⚖️ Ratio", 
                f"1:{form_data.get('water_volume_ml', 0)/form_data.get('coffee_dose_grams', 1):.1f}" if form_data.get('water_volume_ml') and form_data.get('coffee_dose_grams') else "Not calculated",
                help="Water to Coffee Ratio"
            )
            
        with col3:
            st.metric(
                "⭐ Rating", 
                f"{form_data.get('score_overall_rating', 0):.1f}/10" if form_data.get('score_overall_rating') else "Not rated",
                help="Overall flavor rating"
            )
        
        # Auto-navigation countdown
        st.markdown("---")
        
        # Create countdown container
        countdown_container = st.empty()
        
        import time
        countdown_time = 2
        
        for i in range(countdown_time, 0, -1):
            countdown_container.markdown(f"""
            <div style="
                background: #e3f2fd;
                border: 2px solid #2196F3;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                margin: 10px 0;
            ">
            <p style="margin: 0; color: #1976D2; font-weight: bold;">
            🚀 Automatically navigating to View Data page in <span style="color: #FF6B35; font-size: 1.2em;">{i}</span> seconds...
            </p>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 0.9em;">
            Your new cup will be highlighted on the brewing chart!
            </p>
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(1)
        
        # Final message before navigation
        countdown_container.markdown("""
        <div style="
            background: #4CAF50;
            color: white;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            margin: 10px 0;
        ">
        <p style="margin: 0; font-weight: bold;">✨ Navigating now! ✨</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Trigger navigation by setting session state and rerunning
        st.session_state.auto_navigate_to_chart = True

    def _show_immediate_submission_feedback(self, brew_id: int, bean_name: str):
        """Show immediate visual feedback when form is submitted"""
        
        # Large, prominent submission confirmation
        st.markdown(f"""
        <div style="
            background: linear-gradient(45deg, #FF6B35, #F7931E, #FF6B35);
            background-size: 400% 400%;
            animation: submission-glow 1.5s ease infinite;
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            margin: 25px 0;
            border: 3px solid #FF6B35;
            box-shadow: 0 8px 25px rgba(255, 107, 53, 0.3);
        ">
        <style>
        @keyframes submission-glow {{
            0%, 100% {{ background-position: 0% 50%; box-shadow: 0 8px 25px rgba(255, 107, 53, 0.3); }}
            50% {{ background-position: 100% 50%; box-shadow: 0 12px 35px rgba(255, 107, 53, 0.5); }}
        }}
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
            100% {{ transform: scale(1); }}
        }}
        .submission-icon {{
            animation: pulse 1s ease-in-out infinite;
            display: inline-block;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        </style>
        <div class="submission-icon">⚡</div>
        <h2 style="margin: 0 0 10px 0; font-size: 1.8em; font-weight: bold;">SUBMISSION RECEIVED!</h2>
        <p style="margin: 0; font-size: 1.2em; opacity: 0.95;">
        Processing Cup #{brew_id} • {bean_name}
        </p>
        <p style="margin: 10px 0 0 0; font-size: 0.95em; opacity: 0.85;">
        Please wait while we save and calculate your brew data...
        </p>
        </div>
        """, unsafe_allow_html=True)

    def _show_new_cup_welcome(self):
        """Show welcome message on View Data tab for newly added cups"""
        latest_brew_id = st.session_state.get('latest_brew_id')
        if not latest_brew_id:
            return
            
        # Find the newly added cup data
        cup_data = st.session_state.df[st.session_state.df['brew_id'] == latest_brew_id]
        if cup_data.empty:
            return
        
        cup_info = cup_data.iloc[0]
        
        # Create a welcome banner with cup details
        bean_name = cup_info.get('bean_name', 'Unknown Bean')
        rating = cup_info.get('score_overall_rating', 'N/A')
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
        ">
        <h3 style="margin: 0 0 10px 0; font-size: 1.4em;">🎉 Welcome to Your Cup Data!</h3>
        <p style="margin: 0; font-size: 1.1em; opacity: 0.9;">
        Cup #{latest_brew_id} • {bean_name} • Rating: {rating}/10
        </p>
        <p style="margin: 10px 0 0 0; font-size: 0.9em; opacity: 0.8;">
        Look for the highlighted point on the brewing chart below!
        </p>
        </div>
        """, unsafe_allow_html=True)

    def _show_bean_usage_alert(self, bean_name, bean_country, bean_region, estimated_bag_size_grams):
        """Show bean usage alert if bag is running low"""
        # Calculate total usage for this bean using null-safe comparison
        name_match = st.session_state.df['bean_name'] == bean_name
        country_match = st.session_state.df['bean_origin_country'] == bean_country
        
        if pd.isna(bean_region):
            region_match = st.session_state.df['bean_origin_region'].isna()
        else:
            region_match = st.session_state.df['bean_origin_region'] == bean_region
        
        bean_usage = st.session_state.df[name_match & country_match & region_match]['coffee_dose_grams'].fillna(0).sum()
        
        remaining = max(0, estimated_bag_size_grams - bean_usage)
        usage_percentage = (bean_usage / estimated_bag_size_grams) * 100
        
        if usage_percentage >= 90:  # 90% or more used
            st.info(f"💡 **Bean Alert:** Only ~{remaining:.0f}g remaining ({usage_percentage:.0f}% used). Consider archiving if bag is empty?")
        elif usage_percentage >= 75:  # 75% or more used
            st.info(f"📦 **Inventory:** ~{remaining:.0f}g remaining ({usage_percentage:.0f}% used)")
    
    def _render_data_management_tab(self):
        """Render the data management tab"""
        st.header("Data Management")
        
        # Sub-tabs for different management functions
        mgmt_tab1, mgmt_tab2, mgmt_tab3 = st.tabs(["✏️ Edit Brews", "📦 Bean Management", "🔄 Batch Operations"])
        
        with mgmt_tab1:
            self._render_edit_brews()
        
        with mgmt_tab2:
            self._render_bean_management()
        
        with mgmt_tab3:
            self._render_batch_operations()
    
    def _render_edit_brews(self) -> None:
        """Render the edit brews interface"""
        st.subheader("Edit Individual Brew Records")
        
        if not st.session_state.df.empty:
            selected_id = self._render_brew_selection()
            if selected_id:
                cup_data = st.session_state.df[st.session_state.df['brew_id'] == selected_id].iloc[0]
                self._render_calculated_values_display(cup_data)
                self._render_edit_form(selected_id, cup_data)
        else:
            st.info("No records available to edit")
    
    def _render_brew_selection(self) -> Optional[int]:
        """Render brew selection dropdown and return selected brew ID"""
        cup_options = [
            f"{self.brew_id_service.safe_brew_id_to_int(row['brew_id'])} - {row['bean_name'] if pd.notna(row['bean_name']) else 'Unknown'} ({row['brew_date']})" 
            for _, row in st.session_state.df.iterrows()
        ]
        selected_cup = st.selectbox("Select cup to edit:", cup_options)
        
        if selected_cup:
            try:
                return int(selected_cup.split(' - ')[0])
            except (ValueError, IndexError):
                st.error("Error parsing cup selection. Please try again.")
                return None
        return None
    
    def _render_calculated_values_display(self, cup_data: pd.Series) -> None:
        """Display current calculated values for reference"""
        with st.expander("📊 Current Calculated Values (Read-Only)", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Brew Ratio", f"{cup_data.get('brew_ratio_to_1', 'N/A')}:1" if pd.notna(cup_data.get('brew_ratio_to_1')) else "N/A")
                st.metric("Extraction Yield", f"{cup_data.get('final_extraction_yield_percent', 'N/A')}%" if pd.notna(cup_data.get('final_extraction_yield_percent')) else "N/A")
            
            with col2:
                st.metric("Strength Category", cup_data.get('score_strength_category', 'N/A'))
                st.metric("Extraction Category", cup_data.get('score_extraction_category', 'N/A'))
            
            with col3:
                st.metric("Brewing Zone", cup_data.get('score_brewing_zone', 'N/A'))
                st.metric("Days Since Roast", cup_data.get('beans_days_since_roast', 'N/A'))
    
    def _render_edit_form(self, selected_id: int, cup_data: pd.Series) -> None:
        """Render the main edit form for the selected brew"""
        st.markdown("---")
        st.info(f"Editing Brew #{selected_id} - {cup_data.get('bean_name', 'Unknown')} ({cup_data.get('brew_date', 'Unknown')})")
        
        with st.form(f"edit_brew_{selected_id}"):
            form_fields = self._render_form_sections(cup_data)
            
            # Form submission
            col1, col2 = st.columns([1, 4])
            with col1:
                update_brew = st.form_submit_button("Update Brew", type="primary")
            
            if update_brew:
                self._process_form_submission(selected_id, form_fields)
    
    def _render_form_sections(self, cup_data: pd.Series) -> dict:
        """Render all form sections and return collected form data"""
        # Bean Information Section
        st.markdown("### ☕ Bean Information")
        bean_fields = self._render_bean_information_section(cup_data)
        
        # Brewing Parameters Section
        st.markdown("### ⚙️ Brewing Parameters")
        brewing_fields = self._render_brewing_parameters_section(cup_data)
        
        # Scoring Section
        st.markdown("### ⭐ Tasting & Scoring")
        scoring_fields = self._render_scoring_section(cup_data)
        
        # Combine all fields
        return {**bean_fields, **brewing_fields, **scoring_fields}
    
    def _render_bean_information_section(self, cup_data: pd.Series) -> dict:
        """Render bean information form fields"""
        col1, col2 = st.columns(2)
        
        with col1:
            bean_name = st.text_input("Bean Name", value=cup_data.get('bean_name', '') or '')
            bean_origin_country = st.text_input("Origin Country", value=cup_data.get('bean_origin_country', '') or '')
            bean_variety = st.text_input("Variety", value=cup_data.get('bean_variety', '') or '')
            bean_roast_level = st.selectbox(
                "Roast Level", 
                self.form_service.get_roast_levels(),
                index=self._get_selectbox_index(self.form_service.get_roast_levels(), cup_data.get('bean_roast_level'))
            )
        
        with col2:
            bean_origin_region = st.text_input("Origin Region", value=cup_data.get('bean_origin_region', '') or '')
            bean_process_method = st.selectbox(
                "Process Method", 
                self.form_service.get_process_methods(),
                index=self._get_selectbox_index(self.form_service.get_process_methods(), cup_data.get('bean_process_method'))
            )
            bean_roast_date = st.date_input("Roast Date", value=pd.to_datetime(cup_data.get('bean_roast_date')).date() if pd.notna(cup_data.get('bean_roast_date')) else None)
        
        bean_notes = st.text_area("Bean Notes", value=cup_data.get('bean_notes', '') or '', height=100)
        
        return {
            'bean_name': bean_name.strip() if bean_name.strip() else None,
            'bean_origin_country': bean_origin_country.strip() if bean_origin_country.strip() else None,
            'bean_origin_region': bean_origin_region.strip() if bean_origin_region.strip() else None,
            'bean_variety': bean_variety.strip() if bean_variety.strip() else None,
            'bean_process_method': bean_process_method if bean_process_method else None,
            'bean_roast_date': bean_roast_date,
            'bean_roast_level': bean_roast_level if bean_roast_level else None,
            'bean_notes': bean_notes.strip() if bean_notes.strip() else None
        }
    
    def _render_brewing_parameters_section(self, cup_data: pd.Series) -> dict:
        """Render brewing parameters form fields"""
        col1, col2 = st.columns(2)
        
        with col1:
            brew_date = st.date_input("Brew Date", value=pd.to_datetime(cup_data.get('brew_date')).date() if pd.notna(cup_data.get('brew_date')) else None)
            
            # Grind settings
            grind_options = self.form_service.generate_grind_dial_options()
            grind_display_options = self.form_service.format_grind_option_display(grind_options)
            current_grind_index = self.form_service.get_grind_size_index(grind_options, cup_data.get('grind_size'))
            grind_size = st.selectbox("Grind Size", grind_display_options, index=current_grind_index)
            grind_model = st.text_input("Grinder Model", value=cup_data.get('grind_model', '') or '')
            
            brew_method = st.text_input("Brew Method", value=cup_data.get('brew_method', '') or '')
            brew_device = st.selectbox(
                "Brew Device", 
                self.form_service.get_brew_devices(),
                index=self._get_selectbox_index(self.form_service.get_brew_devices(), cup_data.get('brew_device'))
            )
            
            coffee_dose_grams = st.number_input("Coffee Dose (g)", value=float(cup_data.get('coffee_dose_grams', 0)) if pd.notna(cup_data.get('coffee_dose_grams')) else 0.0, min_value=0.0, step=0.1)
            water_volume_ml = st.number_input("Water Volume (ml)", value=float(cup_data.get('water_volume_ml', 0)) if pd.notna(cup_data.get('water_volume_ml')) else 0.0, min_value=0.0, step=1.0)
            water_temp_degC = st.number_input("Water Temperature (°C)", value=float(cup_data.get('water_temp_degC', 0)) if pd.notna(cup_data.get('water_temp_degC')) else 0.0, min_value=0.0, max_value=100.0, step=1.0)
            
        with col2:
            brew_bloom_time_s = st.number_input("Bloom Time (s)", value=float(cup_data.get('brew_bloom_time_s', 0)) if pd.notna(cup_data.get('brew_bloom_time_s')) else 0.0, min_value=0.0, step=1.0)
            brew_bloom_water_ml = st.number_input("Bloom Water (ml)", value=float(cup_data.get('brew_bloom_water_ml', 0)) if pd.notna(cup_data.get('brew_bloom_water_ml')) else 0.0, min_value=0.0, step=1.0)
            brew_pulse_target_water_ml = st.number_input("Pulse Target Water (ml)", value=float(cup_data.get('brew_pulse_target_water_ml', 0)) if pd.notna(cup_data.get('brew_pulse_target_water_ml')) else 0.0, min_value=0.0, step=1.0)
            brew_total_time_s = st.number_input("Total Brew Time (s)", value=float(cup_data.get('brew_total_time_s', 0)) if pd.notna(cup_data.get('brew_total_time_s')) else 0.0, min_value=0.0, step=1.0)
            
            agitation_method = st.selectbox(
                "Agitation Method", 
                self.form_service.get_agitation_methods(),
                index=self._get_selectbox_index(self.form_service.get_agitation_methods(), cup_data.get('agitation_method'))
            )
            pour_technique = st.selectbox(
                "Pour Technique", 
                self.form_service.get_pour_techniques(),
                index=self._get_selectbox_index(self.form_service.get_pour_techniques(), cup_data.get('pour_technique'))
            )
            
            final_tds_percent = st.number_input("Final TDS (%)", value=float(cup_data.get('final_tds_percent', 0)) if pd.notna(cup_data.get('final_tds_percent')) else 0.0, min_value=0.0, max_value=10.0, step=0.01)
            mug_weight_grams = st.number_input("Mug Weight (g)", value=float(cup_data.get('mug_weight_grams', 0)) if pd.notna(cup_data.get('mug_weight_grams')) else 0.0, min_value=0.0, step=0.1)
            final_combined_weight_grams = st.number_input("Final Combined Weight (g)", value=float(cup_data.get('final_combined_weight_grams', 0)) if pd.notna(cup_data.get('final_combined_weight_grams')) else 0.0, min_value=0.0, step=0.1)
        
        return {
            'brew_date': brew_date,
            'grind_size': grind_options[grind_display_options.index(grind_size)] if grind_size in grind_display_options else grind_options[0],
            'grind_model': grind_model.strip() if grind_model.strip() else None,
            'brew_method': brew_method.strip() if brew_method.strip() else None,
            'brew_device': brew_device if brew_device else None,
            'coffee_dose_grams': coffee_dose_grams,
            'water_volume_ml': water_volume_ml,
            'water_temp_degC': water_temp_degC,
            'brew_bloom_time_s': brew_bloom_time_s,
            'brew_bloom_water_ml': brew_bloom_water_ml,
            'brew_pulse_target_water_ml': brew_pulse_target_water_ml,
            'brew_total_time_s': brew_total_time_s,
            'agitation_method': agitation_method if agitation_method else None,
            'pour_technique': pour_technique if pour_technique else None,
            'final_tds_percent': final_tds_percent,
            'mug_weight_grams': mug_weight_grams,
            'final_combined_weight_grams': final_combined_weight_grams
        }
    
    def _render_scoring_section(self, cup_data: pd.Series) -> dict:
        """Render scoring form fields"""
        col1, col2 = st.columns(2)
        
        with col1:
            score_overall_rating = st.number_input("Overall Rating", value=float(cup_data.get('score_overall_rating', 0)) if pd.notna(cup_data.get('score_overall_rating')) else 0.0, min_value=0.0, max_value=5.0, step=0.1)
            score_flavor_profile_category = st.selectbox(
                "Flavor Profile", 
                self.form_service.get_flavor_profiles(),
                index=self._get_selectbox_index(self.form_service.get_flavor_profiles(), cup_data.get('score_flavor_profile_category'))
            )
            score_complexity = st.number_input("Complexity", value=float(cup_data.get('score_complexity', 0)) if pd.notna(cup_data.get('score_complexity')) else 0.0, min_value=0.0, max_value=5.0, step=0.1)
        
        with col2:
            score_notes = st.text_area("Tasting Notes", value=cup_data.get('score_notes', '') or '', height=100)
            score_bitterness = st.number_input("Bitterness", value=float(cup_data.get('score_bitterness', 0)) if pd.notna(cup_data.get('score_bitterness')) else 0.0, min_value=0.0, max_value=5.0, step=0.1)
            score_mouthfeel = st.number_input("Mouthfeel", value=float(cup_data.get('score_mouthfeel', 0)) if pd.notna(cup_data.get('score_mouthfeel')) else 0.0, min_value=0.0, max_value=5.0, step=0.1)
        
        return {
            'score_overall_rating': score_overall_rating,
            'score_notes': score_notes.strip() if score_notes.strip() else None,
            'score_flavor_profile_category': score_flavor_profile_category if score_flavor_profile_category else None,
            'score_complexity': score_complexity,
            'score_bitterness': score_bitterness,
            'score_mouthfeel': score_mouthfeel,
            'scoring_system_version': '3-factor-v1'
        }
    
    def _process_form_submission(self, selected_id: int, form_data: dict) -> None:
        """Process the form submission and update the brew record"""
        try:
            # Update the record using FormHandlingService
            updated_df = self.form_service.update_brew_record(st.session_state.df, selected_id, form_data)
            
            # Save to CSV and reprocess
            self.data_service.save_dataframe_to_csv(updated_df, 'data/cups_of_coffee.csv')
            
            # Reprocess to update calculated fields using data service
            success, message, stats = self.data_service.run_post_processing(selective=True, show_stats=False)
            
            if not success:
                st.error(f"❌ Processing failed: {message}")
                return
            
            # Reload data using consistent method
            st.session_state.df = self.data_service.load_data()
            
            st.success(f"✅ Successfully updated brew #{selected_id}! All calculated fields have been reprocessed.")
            st.rerun()
            
        except ValueError as e:
            st.error(f"❌ Invalid data provided: {str(e)}")
        except KeyError as e:
            st.error(f"❌ Missing required field: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error updating brew: {str(e)}")
    
    def _render_dynamic_brew_fields(self, brew_device: str, key_prefix: str = "",
                                       current_values: dict = None) -> dict:
        """
        Render dynamic brew fields based on selected brew device.

        Args:
            brew_device: The selected brew device name
            key_prefix: Prefix for Streamlit widget keys to ensure uniqueness
            current_values: Current values for edit mode (optional)

        Returns:
            Dictionary of device-specific field values
        """
        if current_values is None:
            current_values = {}

        data = {}
        device_config = get_device_config(brew_device)

        if not device_config:
            # Fallback: show generic pour-over fields for unknown devices
            st.caption("*Select a brew device to see method-specific fields*")
            # Show basic fields
            data['brew_bloom_water_ml'] = st.number_input(
                "Bloom Water Volume (ml)", min_value=0.0, value=current_values.get('brew_bloom_water_ml'),
                step=0.1, key=f"{key_prefix}_bloom_water_ml"
            )
            data['brew_bloom_time_s'] = st.number_input(
                "Bloom Time (seconds)", min_value=0, value=current_values.get('brew_bloom_time_s'),
                key=f"{key_prefix}_bloom_time_s"
            )
            agitation_methods = self.form_service.get_agitation_methods()
            data['agitation_method'] = st.selectbox(
                "Agitation Method", agitation_methods, key=f"{key_prefix}_agitation"
            )
            pour_techniques = self.form_service.get_pour_techniques()
            data['pour_technique'] = st.selectbox(
                "Pour Technique", pour_techniques, key=f"{key_prefix}_pour_technique"
            )
            return data

        category = device_config.get("category")

        # Show device-specific fields based on category
        if category == DeviceCategory.HYBRID.value and "Hario Switch" in brew_device:
            data = self._render_hario_switch_fields(key_prefix, current_values)
        elif category == DeviceCategory.POUR_OVER.value:
            data = self._render_pour_over_fields(brew_device, key_prefix, current_values)
        elif category == DeviceCategory.IMMERSION.value:
            if "Aeropress" in brew_device:
                data = self._render_aeropress_fields(key_prefix, current_values)
            elif "French Press" in brew_device:
                data = self._render_french_press_fields(key_prefix, current_values)
            else:
                data = self._render_generic_immersion_fields(key_prefix, current_values)
        elif category == DeviceCategory.ESPRESSO.value:
            data = self._render_espresso_fields(key_prefix, current_values)
        else:
            # Generic fallback
            data = self._render_pour_over_fields(brew_device, key_prefix, current_values)

        return data

    def _render_hario_switch_fields(self, key_prefix: str, current_values: dict) -> dict:
        """Render Hario Switch specific fields

        Field order based on user feedback:
        - Setup options first (water before grinds, valve start)
        - Bloom parameters
        - Infusion/steep parameters
        - Stir option
        - Valve release time (absolute time since start)
        - Total brew time at bottom (absolute time since start)
        - Drawdown time auto-calculated (total - valve release)

        All times are absolute since start of brew.
        """
        data = {}

        st.caption("**Hario Switch Settings**")
        st.caption("*All times are absolute (since start of brew)*")

        # Setup options
        col1, col2 = st.columns(2)
        with col1:
            data['hario_water_before_grinds'] = st.checkbox(
                "Water before grinds",
                value=current_values.get('hario_water_before_grinds', False),
                help="Add water before coffee grounds?",
                key=f"{key_prefix}_hario_water_first"
            )
        with col2:
            data['hario_valve_start_closed'] = st.checkbox(
                "Valve closed at start",
                value=current_values.get('hario_valve_start_closed', True),
                help="Was the valve closed when brewing started?",
                key=f"{key_prefix}_hario_valve_closed"
            )

        # Bloom parameters
        data['brew_bloom_water_ml'] = st.number_input(
            "Bloom Water (ml)", min_value=0.0,
            value=current_values.get('brew_bloom_water_ml'),
            step=0.1, key=f"{key_prefix}_hario_bloom_water"
        )

        # Bloom time in MM'SS" format
        data['brew_bloom_time_s'] = self.wizard.render_time_input(
            "Bloom Time",
            current_values.get('brew_bloom_time_s'),
            key=f"{key_prefix}_hario_bloom_time"
        )

        # Infusion parameters - time in MM'SS" format
        data['hario_infusion_duration_s'] = self.wizard.render_time_input(
            "Infusion Duration",
            current_values.get('hario_infusion_duration_s'),
            key=f"{key_prefix}_hario_infusion",
            help_text="Total immersion time before opening valve"
        )

        # Stir option
        stir_options = self.form_service.get_hario_stir_options()
        current_stir = current_values.get('hario_stir', '')
        stir_index = stir_options.index(current_stir) if current_stir in stir_options else 0
        data['hario_stir'] = st.selectbox(
            "Stir during infusion", stir_options, index=stir_index,
            help="Did you stir during the immersion phase?",
            key=f"{key_prefix}_hario_stir"
        )

        # Valve release time (absolute since start) - in MM'SS" format
        valve_release_time = self.wizard.render_time_input(
            "Valve Release Time",
            current_values.get('hario_valve_release_time_s'),
            key=f"{key_prefix}_hario_valve_release",
            help_text="Absolute time when valve was opened"
        )
        data['hario_valve_release_time_s'] = valve_release_time

        st.markdown("---")
        st.caption("**Post-Brew Measurements** *(recorded after brewing completes)*")

        # Total brew time (absolute since start) - in MM'SS" format
        total_brew_time = self.wizard.render_time_input(
            "Total Brew Time",
            current_values.get('brew_total_time_s'),
            key=f"{key_prefix}_hario_total_time",
            help_text="Absolute time from start to end of drawdown"
        )
        data['brew_total_time_s'] = total_brew_time

        # Final weight only (mug weight is now in Step 2)
        final_weight = st.number_input(
            "Final Combined Weight (g)",
            min_value=0.0,
            value=current_values.get('final_combined_weight_grams'),
            step=0.1,
            help="Mug + coffee after brewing",
            key=f"{key_prefix}_hario_final_weight"
        )
        data['final_combined_weight_grams'] = final_weight

        # Auto-calculate drawdown time: total brew time - valve release time
        st.caption("*Calculated fields (auto-derived):*")

        if total_brew_time and valve_release_time and total_brew_time > valve_release_time:
            calculated_drawdown = total_brew_time - valve_release_time
            # Format drawdown time in MM'SS" for display
            dd_min = calculated_drawdown // 60
            dd_sec = calculated_drawdown % 60
            st.info(f"**Drawdown Time:** {dd_min}'{dd_sec:02d}\" ({calculated_drawdown}s) *(total - valve release)*")
            data['hario_drawdown_time_s'] = calculated_drawdown
        else:
            # Show as read-only with explanation when can't calculate
            if total_brew_time and valve_release_time:
                st.warning("Drawdown time cannot be calculated (total time must be > valve release time)")
            else:
                st.caption("Drawdown time will be calculated when both total brew time and valve release time are entered")
            data['hario_drawdown_time_s'] = current_values.get('hario_drawdown_time_s')

        return data

    def _render_pour_over_fields(self, brew_device: str, key_prefix: str, current_values: dict) -> dict:
        """Render pour-over specific fields (V60, Chemex, etc.)"""
        data = {}

        st.caption("**Pour-over Settings**")

        data['brew_bloom_water_ml'] = st.number_input(
            "Bloom Water (ml)", min_value=0.0,
            value=current_values.get('brew_bloom_water_ml'),
            step=0.1, key=f"{key_prefix}_pourover_bloom_water"
        )

        # Bloom time in MM'SS" format
        data['brew_bloom_time_s'] = self.wizard.render_time_input(
            "Bloom Time",
            current_values.get('brew_bloom_time_s'),
            key=f"{key_prefix}_pourover_bloom_time"
        )

        # V60-specific swirl options
        if "V60" in brew_device:
            col1, col2 = st.columns(2)
            with col1:
                data['v60_swirl_after_bloom'] = st.checkbox(
                    "Swirl after bloom",
                    value=current_values.get('v60_swirl_after_bloom', False),
                    key=f"{key_prefix}_v60_swirl_bloom"
                )
                data['v60_stir_before_drawdown'] = st.checkbox(
                    "Stir before drawdown",
                    value=current_values.get('v60_stir_before_drawdown', False),
                    key=f"{key_prefix}_v60_stir"
                )
            with col2:
                data['v60_final_swirl'] = st.checkbox(
                    "Final swirl",
                    value=current_values.get('v60_final_swirl', False),
                    key=f"{key_prefix}_v60_final_swirl"
                )

        data['num_pours'] = st.number_input(
            "Number of pours", min_value=1, max_value=10,
            value=current_values.get('num_pours', 2),
            help="How many pour phases (excluding bloom)",
            key=f"{key_prefix}_num_pours"
        )

        agitation_methods = self.form_service.get_agitation_methods()
        current_agitation = current_values.get('agitation_method', '')
        agitation_index = agitation_methods.index(current_agitation) if current_agitation in agitation_methods else 0
        data['agitation_method'] = st.selectbox(
            "Agitation Method", agitation_methods, index=agitation_index,
            key=f"{key_prefix}_pourover_agitation"
        )

        pour_techniques = self.form_service.get_pour_techniques()
        current_pour = current_values.get('pour_technique', '')
        pour_index = pour_techniques.index(current_pour) if current_pour in pour_techniques else 0
        data['pour_technique'] = st.selectbox(
            "Pour Technique", pour_techniques, index=pour_index,
            key=f"{key_prefix}_pourover_technique"
        )

        st.caption("*Dependent variable (outcome):*")
        # Drawdown time in MM'SS" format
        data['drawdown_time_s'] = self.wizard.render_time_input(
            "Drawdown Time",
            current_values.get('drawdown_time_s'),
            key=f"{key_prefix}_pourover_drawdown",
            help_text="Time for final drainage"
        )

        return data

    def _render_aeropress_fields(self, key_prefix: str, current_values: dict) -> dict:
        """Render AeroPress specific fields"""
        data = {}

        st.caption("**AeroPress Settings**")

        orientation_options = self.form_service.get_aeropress_orientation_options()
        current_orientation = current_values.get('aeropress_orientation', '')
        orientation_index = orientation_options.index(current_orientation) if current_orientation in orientation_options else 0
        data['aeropress_orientation'] = st.selectbox(
            "Orientation", orientation_options, index=orientation_index,
            help="Standard (filter down) or Inverted (filter up)",
            key=f"{key_prefix}_aeropress_orientation"
        )

        # Steep time in MM'SS" format
        data['aeropress_steep_time_s'] = self.wizard.render_time_input(
            "Steep Time",
            current_values.get('aeropress_steep_time_s') or 120,
            key=f"{key_prefix}_aeropress_steep",
            help_text="Immersion time before pressing"
        )

        data['aeropress_swirl_before_press'] = st.checkbox(
            "Swirl before press",
            value=current_values.get('aeropress_swirl_before_press', False),
            key=f"{key_prefix}_aeropress_swirl"
        )

        # Wait after swirl in MM'SS" format
        data['aeropress_wait_after_swirl_s'] = self.wizard.render_time_input(
            "Wait after swirl",
            current_values.get('aeropress_wait_after_swirl_s') or 30,
            key=f"{key_prefix}_aeropress_wait",
            help_text="Rest time after swirling"
        )

        # Press duration in MM'SS" format
        data['aeropress_press_duration_s'] = self.wizard.render_time_input(
            "Press Duration",
            current_values.get('aeropress_press_duration_s'),
            key=f"{key_prefix}_aeropress_press",
            help_text="How long the press took"
        )

        return data

    def _render_french_press_fields(self, key_prefix: str, current_values: dict) -> dict:
        """Render French Press specific fields (Hoffmann method)"""
        data = {}

        st.caption("**French Press Settings** *(Hoffmann method)*")

        # Initial steep time in MM'SS" format
        data['frenchpress_initial_steep_s'] = self.wizard.render_time_input(
            "Initial Steep Time",
            current_values.get('frenchpress_initial_steep_s') or 240,
            key=f"{key_prefix}_fp_steep",
            help_text="Time before breaking crust (4 min typical)"
        )

        col1, col2 = st.columns(2)
        with col1:
            data['frenchpress_break_crust'] = st.checkbox(
                "Break crust",
                value=current_values.get('frenchpress_break_crust', True),
                help="Did you break/stir the crust?",
                key=f"{key_prefix}_fp_crust"
            )
        with col2:
            data['frenchpress_skim_foam'] = st.checkbox(
                "Skim foam",
                value=current_values.get('frenchpress_skim_foam', True),
                help="Did you skim the foam?",
                key=f"{key_prefix}_fp_skim"
            )

        # Settling time in MM'SS" format
        data['frenchpress_settling_time_s'] = self.wizard.render_time_input(
            "Settling Time",
            current_values.get('frenchpress_settling_time_s') or 300,
            key=f"{key_prefix}_fp_settle",
            help_text="Wait time after skimming (5-8 min recommended)"
        )

        plunge_options = self.form_service.get_frenchpress_plunge_options()
        current_plunge = current_values.get('frenchpress_plunge_depth', '')
        plunge_index = plunge_options.index(current_plunge) if current_plunge in plunge_options else 0
        data['frenchpress_plunge_depth'] = st.selectbox(
            "Plunge Depth", plunge_options, index=plunge_index,
            help="How far did you plunge?",
            key=f"{key_prefix}_fp_plunge"
        )

        return data

    def _render_espresso_fields(self, key_prefix: str, current_values: dict) -> dict:
        """Render Espresso specific fields"""
        data = {}

        st.caption("**Espresso Settings**")

        data['espresso_yield_g'] = st.number_input(
            "Yield (g)", min_value=0.0,
            value=current_values.get('espresso_yield_g'),
            step=0.1, help="Output weight of espresso",
            key=f"{key_prefix}_espresso_yield"
        )

        # Shot time in MM'SS" format (but typically just seconds for espresso)
        data['espresso_shot_time_s'] = self.wizard.render_time_input(
            "Shot Time",
            current_values.get('espresso_shot_time_s'),
            key=f"{key_prefix}_espresso_shot_time",
            help_text="Total extraction time (25-35s typical)"
        )

        # Pre-infusion time in MM'SS" format
        data['espresso_preinfusion_s'] = self.wizard.render_time_input(
            "Pre-infusion",
            current_values.get('espresso_preinfusion_s'),
            key=f"{key_prefix}_espresso_preinfusion",
            help_text="Duration of pre-infusion phase"
        )

        data['espresso_pressure_bar'] = st.number_input(
            "Pressure (bar)", min_value=0.0, max_value=15.0,
            value=current_values.get('espresso_pressure_bar', 9.0),
            step=0.5, help="Brew pressure if adjustable",
            key=f"{key_prefix}_espresso_pressure"
        )

        return data

    def _render_generic_immersion_fields(self, key_prefix: str, current_values: dict) -> dict:
        """Render generic immersion fields for other devices"""
        data = {}

        st.caption("**Immersion Settings**")

        # Steep time in MM'SS" format
        data['brew_bloom_time_s'] = self.wizard.render_time_input(
            "Steep Time",
            current_values.get('brew_bloom_time_s'),
            key=f"{key_prefix}_immersion_steep"
        )

        agitation_methods = self.form_service.get_agitation_methods()
        current_agitation = current_values.get('agitation_method', '')
        agitation_index = agitation_methods.index(current_agitation) if current_agitation in agitation_methods else 0
        data['agitation_method'] = st.selectbox(
            "Agitation Method", agitation_methods, index=agitation_index,
            key=f"{key_prefix}_immersion_agitation"
        )

        return data

    def _get_selectbox_index(self, options: List[str], current_value: Optional[str]) -> int:
        """
        Get the index of current value in options list for selectbox

        Args:
            options: List of available options
            current_value: Current value to find in options

        Returns:
            Index of current_value in options, or 0 if not found
        """
        try:
            if current_value is not None and str(current_value).strip():
                return options.index(str(current_value))
        except (ValueError, AttributeError):
            pass
        return 0

    def _render_bean_management(self):
        """Render bean management interface"""
        st.subheader("Bean Inventory & Archive Management")
        
        if st.session_state.df.empty:
            st.info("No bean data available")
            return
        
        # Get bean statistics
        bean_stats = self.bean_service.get_bean_statistics(st.session_state.df)
        
        if not bean_stats:
            st.info("No beans found in the database")
            return
        
        # Separate active and archived beans
        active_beans = [bean for bean in bean_stats if bean.archive_status != 'archived']
        archived_beans = [bean for bean in bean_stats if bean.archive_status == 'archived']
        
        # Active Beans Section
        st.markdown(f"### 📊 Active Beans ({len(active_beans)})")
        
        if active_beans:
            # Sort options
            sort_options = {
                "Last Used (Recent First)": lambda x: -x.days_since_last if x.days_since_last != float('inf') else float('inf'),
                "Usage % (High to Low)": lambda x: -x.usage_percentage,
                "Total Brews (High to Low)": lambda x: -x.total_brews,
                "Average Rating (High to Low)": lambda x: -x.avg_rating,
                "Bean Name (A-Z)": lambda x: x.name.lower()
            }
            
            sort_by = st.selectbox("Sort by:", list(sort_options.keys()))
            active_beans_sorted = sorted(active_beans, key=sort_options[sort_by])
            
            # Display active beans
            for bean in active_beans_sorted:
                action = self.ui.render_bean_statistics_card(bean, show_actions=True)
                
                if action == "archive":
                    # Convert empty string to None for null regions
                    region_param = bean.region if bean.region else None
                    st.session_state.df = self.bean_service.archive_bean(bean.name, bean.country, region_param, st.session_state.df)
                    self.data_service.save_data(st.session_state.df)
                    st.success(f"Archived {bean.name}")
                    st.rerun()
        else:
            st.info("No active beans found")
        
        # Archived Beans Section
        st.markdown("---")
        show_archived = st.checkbox(f"📦 Show Archived Beans ({len(archived_beans)})", value=False)
        
        if show_archived and archived_beans:
            st.markdown(f"### 📦 Archived Beans ({len(archived_beans)})")
            
            for bean in archived_beans:
                action = self.ui.render_bean_statistics_card(bean, show_actions=True)
                
                if action == "restore":
                    # Convert empty string to None for null regions
                    region_param = bean.region if bean.region else None
                    st.session_state.df = self.bean_service.restore_bean(bean.name, bean.country, region_param, st.session_state.df)
                    self.data_service.save_data(st.session_state.df)
                    st.success(f"Restored {bean.name}")
                    st.rerun()
    
    def _render_batch_operations(self):
        """Render batch operations interface"""
        st.subheader("Batch Operations")
        
        if st.session_state.df.empty:
            st.info("No data available for batch operations")
            return
        
        # Archive old beans
        st.markdown("### 📦 Archive Old Beans")
        
        days_threshold = st.number_input(
            "Archive beans not used in the last X days:", 
            min_value=1, 
            value=60, 
            step=1,
            help="Beans not used within this period will be archived"
        )
        
        # Find beans that meet the criteria
        old_beans = self.bean_service.find_old_beans(st.session_state.df, days_threshold)
        
        if old_beans:
            st.write(f"**Found {len(old_beans)} beans not used in the last {days_threshold} days:**")
            for bean in old_beans:
                st.write(f"• {bean.name} - {bean.country} (last used {bean.days_since_last} days ago)")
            
            if st.button(f"📦 Archive {len(old_beans)} Old Beans", type="primary"):
                st.session_state.df = self.bean_service.archive_multiple_beans(old_beans, st.session_state.df)
                self.data_service.save_data(st.session_state.df)
                st.success(f"Archived {len(old_beans)} beans")
                st.rerun()
        else:
            st.info(f"No beans found that haven't been used in the last {days_threshold} days")
        
        # Data insights
        st.markdown("---")
        st.markdown("### 📈 Data Insights")
        
        summary = self.data_service.get_data_summary(st.session_state.df)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Records", summary['total_records'])
        
        with col2:
            st.metric("Unique Beans", summary['unique_beans'])
        
        with col3:
            st.metric("Avg Rating", f"{summary['avg_rating']:.1f}/10" if summary['avg_rating'] > 0 else "N/A")
        
        if summary['date_range']:
            st.info(f"📅 **Date Range:** {summary['date_range']}")
        
        st.info(f"📊 **Data Completeness:** {summary['data_completeness']:.1f}%")
    
    def _render_delete_cups_tab(self):
        """Render the delete cups tab"""
        st.header("Delete Cup Record")
        
        if not st.session_state.df.empty:
            # Cup selection
            cup_options = [
                f"{self.brew_id_service.safe_brew_id_to_int(row['brew_id'])} - {row['bean_name'] if pd.notna(row['bean_name']) else 'Unknown'} ({row['brew_date']})" 
                for _, row in st.session_state.df.iterrows()
            ]
            selected_cup = st.selectbox("Select cup to delete:", cup_options)
            
            if selected_cup:
                try:
                    selected_id = int(selected_cup.split(' - ')[0])
                    cup_data = st.session_state.df[st.session_state.df['brew_id'] == selected_id].iloc[0]
                except (ValueError, IndexError):
                    st.error("Error parsing cup selection. Please try again.")
                    return
                
                # Show detailed cup information
                st.markdown("---")
                st.subheader("⚠️ Cup to Delete")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Cup ID", f"#{self.brew_id_service.safe_brew_id_to_int(cup_data['brew_id'])}")
                    st.write(f"**Bean:** {cup_data['bean_name'] if pd.notna(cup_data['bean_name']) else 'Unknown'}")
                    st.write(f"**Date:** {cup_data['brew_date']}")
                
                with col2:
                    st.write(f"**Method:** {cup_data['brew_method'] if pd.notna(cup_data['brew_method']) else 'Unknown'}")
                    st.write(f"**Device:** {cup_data['brew_device'] if pd.notna(cup_data['brew_device']) else 'Unknown'}")
                    st.write(f"**Grind Size:** {cup_data['grind_size'] if pd.notna(cup_data['grind_size']) else 'Unknown'}")
                
                with col3:
                    st.write(f"**TDS:** {cup_data['final_tds_percent']:.2f}%" if pd.notna(cup_data['final_tds_percent']) else "**TDS:** Unknown")
                    st.write(f"**Extraction:** {cup_data['final_extraction_yield_percent']:.1f}%" if pd.notna(cup_data['final_extraction_yield_percent']) else "**Extraction:** Unknown")
                    st.write(f"**Rating:** {cup_data['score_overall_rating']}/10" if pd.notna(cup_data['score_overall_rating']) else "**Rating:** Unknown")
                
                # Show tasting notes if available
                if pd.notna(cup_data['score_notes']) and cup_data['score_notes'].strip():
                    st.write(f"**Notes:** {cup_data['score_notes']}")
                
                st.markdown("---")
                
                # Handle deletion confirmation
                if self.ui.render_delete_confirmation(cup_data, selected_id):
                    # Perform the deletion
                    st.session_state.df = self.data_service.delete_record(st.session_state.df, selected_id)
                    self.data_service.save_data(st.session_state.df)
                    st.success(f"✅ Cup #{selected_id} has been permanently deleted.")
                    st.rerun()
        else:
            st.info("No records available to delete")
    
    def _render_processing_tab(self):
        """Render the processing tab"""
        st.header("Force Data Processing")
        st.write("Manually run the post-processing script to recalculate all derived fields.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("This will run the processing script on all data entries, recalculating fields like extraction yield, strength categories, and brew scores.")
        
        with col2:
            processing_mode = st.selectbox(
                "Processing mode:",
                ["Selective (recommended)", "Full processing"],
                help="Selective only processes changed entries, Full processes all entries"
            )
        
        st.markdown("---")
        
        if st.button("🔄 Run Processing", type="primary", use_container_width=True):
            st.info("🔄 Running data processing...")
            
            # Determine processing mode
            use_selective = processing_mode == "Selective (recommended)"
            
            if use_selective:
                success, stdout, stderr = self.data_service.run_post_processing()
            else:
                success, stdout, stderr = self.data_service.run_full_processing()
            
            # Show processing status
            self.ui.render_processing_status(success, stdout, stderr)
            
            if success:
                # Reload the data to get any updates
                st.session_state.df = self.data_service.load_data()
                st.success("✅ Data reloaded successfully!")


def main():
    """Main application entry point"""
    app = CoffeeBrewingApp()
    app.run()


if __name__ == "__main__":
    main()