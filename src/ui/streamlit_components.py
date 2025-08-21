"""
Streamlit UI Components

Reusable UI components for the coffee brewing application.
Extracted from main application to improve separation of concerns.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import date
from ..services.bean_selection_service import BeanSelectionService
from ..services.form_handling_service import FormHandlingService
from ..services.visualization_service import VisualizationService
from ..models.bean_statistics import BeanStatistics


class StreamlitComponents:
    """Reusable Streamlit UI components for coffee brewing application"""
    
    def __init__(self):
        self.bean_service = BeanSelectionService()
        self.form_service = FormHandlingService()
        self.viz_service = VisualizationService()
    
    def render_grind_size_dial(self, label: str, current_value: Optional[float] = None, 
                             key: Optional[str] = None) -> float:
        """
        Create a grind size dial that mimics Fellow Ode Gen 2 interface
        
        Args:
            label: Label for the selectbox
            current_value: Current grind size value
            key: Unique key for the component
            
        Returns:
            Selected grind size value
        """
        options = self.form_service.generate_grind_dial_options()
        formatted_options = self.form_service.format_grind_option_display(options)
        current_index = self.form_service.get_grind_size_index(options, current_value)
        
        # Create the selectbox that looks like a dial
        selected_index = st.selectbox(
            label,
            range(len(options)),
            index=current_index,
            format_func=lambda x: formatted_options[x],
            key=key,
            help="Grind settings matching Fellow Ode Gen 2: 1, 1.1, 1.2, 2, 2.1, 2.2, etc."
        )
        
        return options[selected_index]
    
    def render_bean_selection_component(self, df: pd.DataFrame, context: str = "add", 
                                      current_bean_data: Optional[Dict[str, Any]] = None, 
                                      key_prefix: str = "") -> Optional[Dict[str, Any]]:
        """
        Unified bean selection component for both add and edit workflows
        
        Args:
            df: DataFrame containing existing data
            context: "add" or "edit" - determines default behavior
            current_bean_data: dict of current bean data (for edit mode)
            key_prefix: unique prefix for session state keys
            
        Returns:
            dict: Selected bean data or None if manual entry
        """
        # Session state key for selected bean data
        session_key = f'{key_prefix}selected_bean_data'
        if session_key not in st.session_state:
            st.session_state[session_key] = None
        
        st.markdown("### 🌱 Bean Selection")
        
        # Get unique beans from existing data (only active beans by default)
        if not df.empty:
            # Filter out archived beans unless "show archived" is enabled
            show_archived = st.checkbox(
                "Show archived beans", 
                value=False, 
                help="Include archived beans in selection", 
                key=f"{key_prefix}show_archived"
            )
            
            unique_beans = self.bean_service.get_unique_beans(df, show_archived)
            bean_options = self.bean_service.get_bean_options_with_usage(df, unique_beans, context)
        else:
            bean_options = ["Create New Bean" if context == "add" else "Manual Entry"]
            unique_beans = pd.DataFrame()
        
        selected_bean_option = st.radio(
            "Choose bean:",
            bean_options,
            index=0,
            horizontal=True if len(bean_options) <= 4 else False,
            key=f"{key_prefix}bean_selection"
        )
        
        # Auto-load bean data when selection changes
        manual_entry_label = "Create New Bean" if context == "add" else "Manual Entry"
        selected_bean_data = self.bean_service.get_selected_bean_data(
            selected_bean_option, unique_beans, bean_options, context
        )
        
        # Update session state
        if selected_bean_data != st.session_state[session_key]:
            st.session_state[session_key] = selected_bean_data
        
        # Show current selection with preview
        if selected_bean_option != manual_entry_label:
            st.success(f"✅ Loaded: {selected_bean_option}")
            
            # Show preview of bean data that will populate the fields
            if st.session_state[session_key]:
                self._render_bean_data_preview(st.session_state[session_key])
        else:
            mode_text = "Creating new bean entry" if context == "add" else "Manual entry mode - fields populated with current data"
            st.info(mode_text)
        
        return st.session_state[session_key]
    
    def _render_bean_data_preview(self, bean_data: Dict[str, Any]) -> None:
        """Render preview of bean data"""
        with st.expander("🔍 Preview of Bean Data", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if bean_data.get('bean_name'):
                    st.write(f"**Name:** {bean_data['bean_name']}")
                if bean_data.get('bean_origin_country'):
                    st.write(f"**Country:** {bean_data['bean_origin_country']}")
                if bean_data.get('bean_origin_region'):
                    st.write(f"**Region:** {bean_data['bean_origin_region']}")
                if bean_data.get('bean_variety'):
                    st.write(f"**Variety:** {bean_data['bean_variety']}")
            with col2:
                if bean_data.get('bean_process_method'):
                    st.write(f"**Process:** {bean_data['bean_process_method']}")
                if bean_data.get('bean_roast_level'):
                    st.write(f"**Roast:** {bean_data['bean_roast_level']}")
                if bean_data.get('bean_roast_date'):
                    st.write(f"**Roast Date:** {bean_data['bean_roast_date']}")
            if bean_data.get('bean_notes'):
                st.write(f"**Notes:** {bean_data['bean_notes']}")
    
    def render_bean_information_form(self, context: str = "add", 
                                   selected_bean_data: Optional[Dict[str, Any]] = None, 
                                   current_bean_data: Optional[Dict[str, Any]] = None, 
                                   key_prefix: str = "") -> Dict[str, Any]:
        """
        Unified bean information form component
        
        Args:
            context: "add" or "edit" - determines default behavior
            selected_bean_data: dict from bean selection (if any)
            current_bean_data: dict of current bean data (for edit mode fallback)
            key_prefix: unique prefix for form field keys
            
        Returns:
            dict: Form field values
        """
        # Prepare data source for form population
        bean_data_source = self.form_service.prepare_bean_form_data(
            selected_bean_data, current_bean_data, context
        )
        
        # Two columns for better space usage
        bean_info_col1, bean_info_col2 = st.columns([1, 1])
        
        with bean_info_col1:
            bean_name = st.text_input(
                "Bean Name", 
                value=bean_data_source.get('bean_name', ''),
                placeholder="e.g., La Providencia",
                key=f"{key_prefix}bean_name"
            )
            bean_origin_country = st.text_input(
                "Origin Country",
                value=bean_data_source.get('bean_origin_country', ''),
                placeholder="e.g., Colombia",
                key=f"{key_prefix}bean_origin_country"
            )
            bean_origin_region = st.text_input(
                "Origin Region",
                value=bean_data_source.get('bean_origin_region', ''),
                placeholder="e.g., Huila",
                key=f"{key_prefix}bean_origin_region"
            )
            bean_variety = st.text_input(
                "Bean Variety", 
                value=bean_data_source.get('bean_variety', ''),
                placeholder="e.g., Cenicafe 1",
                key=f"{key_prefix}bean_variety"
            )
        
        with bean_info_col2:
            process_methods = self.form_service.get_process_methods()
            bean_process_method = st.selectbox(
                "Process Method", 
                process_methods,
                index=process_methods.index(bean_data_source.get('bean_process_method', '')) if bean_data_source.get('bean_process_method') in process_methods else 0,
                key=f"{key_prefix}bean_process_method"
            )
            
            # Handle roast date properly
            roast_date_value = None
            if bean_data_source.get('bean_roast_date'):
                try:
                    roast_date_value = pd.to_datetime(bean_data_source['bean_roast_date']).date()
                except:
                    roast_date_value = None
            
            bean_roast_date = st.date_input(
                "Roast Date", 
                value=roast_date_value,
                help="Leave empty if unknown",
                key=f"{key_prefix}bean_roast_date"
            )
            
            roast_levels = self.form_service.get_roast_levels()
            bean_roast_level = st.selectbox(
                "Roast Level", 
                roast_levels,
                index=roast_levels.index(bean_data_source.get('bean_roast_level', '')) if bean_data_source.get('bean_roast_level') in roast_levels else 0,
                key=f"{key_prefix}bean_roast_level"
            )
        
        # Full width for notes
        bean_notes = st.text_area(
            "Bean Notes", 
            value=bean_data_source.get('bean_notes', ''),
            placeholder="Tasting notes, descriptions...",
            key=f"{key_prefix}bean_notes"
        )
        
        return {
            'bean_name': bean_name,
            'bean_origin_country': bean_origin_country,
            'bean_origin_region': bean_origin_region,
            'bean_variety': bean_variety,
            'bean_process_method': bean_process_method,
            'bean_roast_date': bean_roast_date,
            'bean_roast_level': bean_roast_level,
            'bean_notes': bean_notes
        }
    
    def render_brewing_control_chart(self, df: pd.DataFrame, show_filters: bool = True) -> pd.DataFrame:
        """
        Render the brewing control chart with optional filters
        
        Args:
            df: DataFrame containing brew data
            show_filters: Whether to show filter panel
            
        Returns:
            Filtered DataFrame used for the chart
        """
        chart_data = df.copy()
        
        if show_filters and not df.empty:
            # Filter Panel
            with st.expander("🔍 Filter Data", expanded=False):
                filter_options = self.viz_service.get_filter_options(df)
                
                filter_col1, filter_col2, filter_col3 = st.columns(3)
                
                with filter_col1:
                    st.markdown("**🌱 Beans**")
                    selected_coffees = st.multiselect(
                        "Select coffees:",
                        options=filter_options['coffees'],
                        default=filter_options['coffees'],
                        help="Leave all selected to show all coffees"
                    )
                
                with filter_col2:
                    st.markdown("**⚙️ Grind Size**")
                    selected_grinds = st.multiselect(
                        "Select grind sizes:",
                        options=filter_options['grinds'],
                        default=filter_options['grinds'],
                        help="Leave all selected to show all grind sizes"
                    )
                
                with filter_col3:
                    st.markdown("**🌡️ Water Temp (°C)**")
                    selected_temps = st.multiselect(
                        "Select water temperatures:",
                        options=filter_options['temps'],
                        default=filter_options['temps'],
                        help="Leave all selected to show all temperatures"
                    )
                
                # Apply filters
                filters = {
                    'coffees': selected_coffees,
                    'grinds': selected_grinds,
                    'temps': selected_temps
                }
                chart_data = self.viz_service.apply_data_filters(df, filters)
                
                # Show filter summary
                filter_summary = self.viz_service.get_filter_summary_info(df, chart_data)
                st.markdown("---")
                st.info(f"📊 Showing **{filter_summary['filtered_rows']}** of **{filter_summary['total_rows']}** brew records")
        
        # Create and display chart
        if not chart_data.empty:
            chart = self.viz_service.create_brewing_control_chart(chart_data)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No data available for chart")
        
        return chart_data
    
    def render_bean_statistics_card(self, bean_stat: BeanStatistics, 
                                  show_actions: bool = True) -> Optional[str]:
        """
        Render a bean statistics card
        
        Args:
            bean_stat: BeanStatistics object to display
            show_actions: Whether to show action buttons
            
        Returns:
            Action taken ("archive", "restore", None)
        """
        action_taken = None
        
        with st.expander(f"🌱 {bean_stat.name} - {bean_stat.country} {bean_stat.region}", expanded=False):
            col_info, col_actions = st.columns([3, 1])
            
            with col_info:
                # Basic stats
                info_col1, info_col2, info_col3 = st.columns(3)
                
                with info_col1:
                    st.metric("Total Brews", bean_stat.total_brews)
                    if bean_stat.days_since_last != float('inf'):
                        st.write(f"**Last used:** {bean_stat.days_since_last} days ago")
                    else:
                        st.write("**Last used:** Never")
                
                with info_col2:
                    st.metric("Used", f"{bean_stat.total_grams_used:.0f}g")
                    if bean_stat.bag_size > 0:
                        st.write(f"**Bag size:** {bean_stat.bag_size:.0f}g")
                
                with info_col3:
                    if bean_stat.avg_rating > 0:
                        st.metric("Avg Rating", f"{bean_stat.avg_rating:.1f}/10")
                    if bean_stat.bag_size > 0:
                        st.write(f"**Remaining:** ~{bean_stat.remaining_grams:.0f}g ({bean_stat.usage_percentage:.0f}% used)")
                        
                        # Progress bar for usage
                        progress_value = min(bean_stat.usage_percentage / 100, 1.0)
                        st.progress(progress_value)
            
            if show_actions:
                with col_actions:
                    st.write("**Actions**")
                    
                    if bean_stat.archive_status != 'archived':
                        # Archive button
                        if st.button(f"📦 Archive", key=f"archive_{bean_stat.name}_{bean_stat.country}_{bean_stat.region}", 
                                    help="Mark this bean as archived (removes from active selection)"):
                            action_taken = "archive"
                        
                        # Smart suggestions
                        if bean_stat.days_since_last > 30:
                            st.warning("💡 Not used recently")
                        elif bean_stat.usage_percentage >= 90:
                            st.info("⚠️ Almost empty")
                    else:
                        # Restore button for archived beans
                        if st.button(f"🔄 Restore", key=f"restore_{bean_stat.name}_{bean_stat.country}_{bean_stat.region}",
                                    help="Restore this bean to active status"):
                            action_taken = "restore"
        
        return action_taken
    
    def render_delete_confirmation(self, cup_data: pd.Series, selected_id: int) -> bool:
        """
        Render multi-step delete confirmation interface
        
        Args:
            cup_data: Series containing cup data to delete
            selected_id: ID of the selected cup
            
        Returns:
            True if deletion should proceed
        """
        # Initialize confirmation state
        if 'delete_confirmation_step' not in st.session_state:
            st.session_state.delete_confirmation_step = 0
        if 'selected_delete_id' not in st.session_state:
            st.session_state.selected_delete_id = None
        
        # Reset confirmation if different cup selected
        if st.session_state.selected_delete_id != selected_id:
            st.session_state.delete_confirmation_step = 0
            st.session_state.selected_delete_id = selected_id
        
        # Multi-step confirmation process
        if st.session_state.delete_confirmation_step == 0:
            # Step 1: Initial delete button
            st.error("⚠️ **WARNING:** This action cannot be undone!")
            
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                if st.button("🗑️ Delete This Cup", type="secondary", use_container_width=True):
                    st.session_state.delete_confirmation_step = 1
                    st.rerun()
            
            return False
        
        elif st.session_state.delete_confirmation_step == 1:
            # Step 2: Type confirmation
            st.error("🚨 **FINAL CONFIRMATION REQUIRED**")
            st.write("To confirm deletion, please type **DELETE** in the box below:")
            
            confirmation_text = st.text_input(
                "Type DELETE to confirm:",
                placeholder="Type DELETE here...",
                key="delete_confirmation_input"
            )
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.delete_confirmation_step = 0
                    st.session_state.selected_delete_id = None
                    if 'delete_confirmation_input' in st.session_state:
                        del st.session_state['delete_confirmation_input']
                    st.rerun()
            
            with col3:
                delete_enabled = confirmation_text.strip().upper() == "DELETE"
                if st.button(
                    "🗑️ CONFIRM DELETE", 
                    type="primary" if delete_enabled else "secondary",
                    disabled=not delete_enabled,
                    use_container_width=True
                ):
                    if delete_enabled:
                        # Reset confirmation state
                        st.session_state.delete_confirmation_step = 0
                        st.session_state.selected_delete_id = None
                        if 'delete_confirmation_input' in st.session_state:
                            del st.session_state['delete_confirmation_input']
                        return True
            
            if not delete_enabled and confirmation_text.strip():
                st.warning("Please type exactly **DELETE** to confirm (case insensitive)")
            
            return False
        
        return False
    
    def render_processing_status(self, success: bool, stdout: str, stderr: str) -> None:
        """
        Render processing status with appropriate styling
        
        Args:
            success: Whether processing was successful
            stdout: Standard output from processing
            stderr: Standard error from processing
        """
        if success:
            st.success("✅ Post-processing completed successfully!")
            
            # Always show processing statistics
            if stdout:
                with st.expander("📊 Processing Details", expanded=True):
                    st.text(stdout)
            
            # Always show terminal logs
            if stderr:
                with st.expander("🔍 Terminal Logs", expanded=False):
                    st.text(stderr)
        else:
            st.error("❌ Post-processing failed")
            # Show error output in logs
            if stderr:
                with st.expander("🔍 Error Logs", expanded=False):
                    st.text(stderr)