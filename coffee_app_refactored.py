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

# Import services
from src.services.data_management_service import DataManagementService
from src.services.bean_selection_service import BeanSelectionService
from src.services.form_handling_service import FormHandlingService
from src.services.visualization_service import VisualizationService
from src.services.brew_id_service import BrewIdService

# Import UI components
from src.ui.streamlit_components import StreamlitComponents


class CoffeeBrewingApp:
    """Main application orchestrator for coffee brewing data management"""
    
    def __init__(self):
        # Initialize services
        self.data_service = DataManagementService()
        self.bean_service = BeanSelectionService()
        self.form_service = FormHandlingService()
        self.viz_service = VisualizationService()
        self.brew_id_service = BrewIdService()
        
        # Initialize UI components
        self.ui = StreamlitComponents()
        
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
        
        # Create tabs for different operations
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 View Data", "➕ Add Cup", "✏️ Data Management", "🗑️ Delete Cups", "⚙️ Processing"
        ])
        
        # Clean up expired recent additions on each run
        self._cleanup_expired_recent_additions()
        
        with tab1:
            self._render_view_data_tab()
        
        with tab2:
            self._render_add_cup_tab()
        
        with tab3:
            self._render_data_management_tab()
        
        with tab4:
            self._render_delete_cups_tab()
        
        with tab5:
            self._render_processing_tab()
    
    def _render_view_data_tab(self):
        """Render the data visualization tab"""
        st.header("Brew performance")
        st.write("Plot the brewing data based on the brewing control chart: https://sca.coffee/sca-news/25/issue-13/towards-a-new-brewing-chart")
        
        # Get recent additions for highlighting
        recent_brew_ids = self._get_recent_brew_ids()
        
        # Show recent additions info if any exist
        if recent_brew_ids:
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
    
    def _render_add_cup_tab(self):
        """Render the add new cup tab"""
        st.header("Add new cup")
        
        with st.form("add_cup_form"):
            # Get next ID
            next_id = self.data_service.get_next_brew_id(st.session_state.df)
            
            # Basic info
            brew_id = st.number_input("Brew ID", value=next_id, disabled=True)
            brew_date = st.date_input("Brew Date", value=date.today())
            
            # Bean Selection Component
            selected_bean_data = self.ui.render_bean_selection_component(
                st.session_state.df, 
                context="add", 
                key_prefix="add_"
            )
            
            # Bean Information Section
            with st.expander("📋 Bean Information", expanded=False):
                bean_form_data = self.ui.render_bean_information_form(
                    context="add",
                    selected_bean_data=selected_bean_data,
                    key_prefix="add_"
                )
                
                # Add inventory tracking for new beans
                estimated_bag_size_grams = None
                if selected_bean_data is None:  # Create New Bean mode
                    st.markdown("#### 📦 Inventory Tracking (Optional)")
                    estimated_bag_size_grams = st.number_input(
                        "Estimated Bag Size (grams)", 
                        min_value=0.0, 
                        value=0.0, 
                        step=25.0,
                        help="Enter the total weight of the coffee bag to track usage and get low-stock alerts",
                        key="add_estimated_bag_size_grams"
                    )
                else:
                    # Use existing bag size for selected bean
                    estimated_bag_size_grams = selected_bean_data.get('estimated_bag_size_grams', 0) or 0
            
            # Equipment & Brewing Section
            st.markdown("---")
            st.markdown("### ⚙️ Equipment & Brewing")
            equip_col1, equip_col2 = st.columns([1, 1])
            
            with equip_col1:
                st.subheader("Equipment & Grind")
                grind_size = self.ui.render_grind_size_dial("Grind Size", current_value=6.0, key="add_grind_size")
                grind_model = st.text_input("Grind Model", value="Fellow Ode Gen 2", placeholder="e.g., Fellow Ode Gen 2")
                
                brew_devices = self.form_service.get_brew_devices()
                brew_device = st.selectbox("Brew Device", brew_devices, index=1)
                
                water_temp_degC = st.number_input("Water Temperature (°C)", min_value=70.0, max_value=100.0, value=None, step=0.1)
                coffee_dose_grams = st.number_input("Coffee Dose (g)", min_value=0.0, value=None, step=0.1)
                water_volume_ml = st.number_input("Water Volume (ml)", min_value=0.0, value=None, step=0.1)
                mug_weight_grams = st.number_input("Mug Weight (g)", min_value=0.0, value=None, step=0.1, help="Weight of empty mug")
            
            with equip_col2:
                st.subheader("Brew Process")
                brew_method = st.text_input("Brew Method", value="3 pulse V60", placeholder="e.g., 3 pulse V60")
                brew_pulse_target_water_ml = st.number_input("Pulse Target Water Volume (ml)", min_value=0.0, value=None, step=0.1)
                brew_bloom_water_ml = st.number_input("Bloom Water Volume (ml)", min_value=0.0, value=None, step=0.1)
                brew_bloom_time_s = st.number_input("Bloom Time (seconds)", min_value=0, value=None)
                
                agitation_methods = self.form_service.get_agitation_methods()
                agitation_method = st.selectbox("Agitation Method", agitation_methods)
                
                pour_techniques = self.form_service.get_pour_techniques()
                pour_technique = st.selectbox("Pour Technique", pour_techniques)
                
                brew_total_time_s = st.number_input("Total Brew Time (seconds)", min_value=0, value=None)
                final_combined_weight_grams = st.number_input("Final Combined Weight (g)", min_value=0.0, value=None, step=0.1, help="Total weight: mug + coffee")
            
            # Results & Scoring Section
            st.markdown("---")
            st.markdown("### 📊 Results & Scoring")
            
            results_col1, results_col2, results_col3 = st.columns([1, 1, 2])
            
            with results_col1:
                final_tds_percent = st.number_input("TDS %", min_value=0.0, max_value=5.0, value=None, step=0.01)
            
            with results_col2:
                flavor_profiles = self.form_service.get_flavor_profiles()
                score_flavor_profile_category = st.selectbox("Flavor Profile", flavor_profiles)
            
            with results_col3:
                score_overall_rating = st.slider("Overall Rating", min_value=1.0, max_value=10.0, value=5.0, step=0.1)
            
            score_notes = st.text_area("Score Notes", placeholder="Detailed tasting notes...", height=100)
            
            # Submit button
            st.markdown("---")
            submitted = st.form_submit_button("☕ Add Cup Record", use_container_width=True, type="primary")
            
            # Info about calculated fields
            st.markdown("**Auto-Calculated Fields** *(Will be computed after saving)*")
            st.info("""
            The following fields will be automatically calculated:          
            • Days since roast • Brew ratio (water:coffee) • Extraction yield %
            • Coffee grams per liter • Strength category (Weak/Ideal/Strong)
            • Extraction category (Under/Ideal/Over) • Brewing zone classification
            • Composite brew score • Bean usage statistics • Processing metadata
            """)
            
            if submitted:
                self._handle_add_cup_submission(
                    brew_id, brew_date, bean_form_data, grind_size, grind_model, 
                    brew_device, water_temp_degC, coffee_dose_grams, water_volume_ml,
                    mug_weight_grams, brew_method, brew_pulse_target_water_ml,
                    brew_bloom_water_ml, brew_bloom_time_s, agitation_method,
                    pour_technique, brew_total_time_s, final_combined_weight_grams,
                    final_tds_percent, score_flavor_profile_category, score_overall_rating,
                    score_notes, estimated_bag_size_grams
                )
    
    def _handle_add_cup_submission(self, brew_id, brew_date, bean_form_data, grind_size, 
                                 grind_model, brew_device, water_temp_degC, coffee_dose_grams,
                                 water_volume_ml, mug_weight_grams, brew_method, 
                                 brew_pulse_target_water_ml, brew_bloom_water_ml, brew_bloom_time_s,
                                 agitation_method, pour_technique, brew_total_time_s, 
                                 final_combined_weight_grams, final_tds_percent, 
                                 score_flavor_profile_category, score_overall_rating, 
                                 score_notes, estimated_bag_size_grams):
        """Handle form submission for adding a new cup"""
        
        # Prepare form data
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
            'brew_pulse_target_water_ml': brew_pulse_target_water_ml,
            'brew_bloom_water_ml': brew_bloom_water_ml,
            'brew_bloom_time_s': brew_bloom_time_s,
            'agitation_method': agitation_method,
            'pour_technique': pour_technique,
            'brew_total_time_s': brew_total_time_s,
            'final_combined_weight_grams': final_combined_weight_grams,
            'final_tds_percent': final_tds_percent,
            'score_flavor_profile_category': score_flavor_profile_category,
            'score_overall_rating': score_overall_rating,
            'score_notes': score_notes
        }
        
        # Prepare brew record
        new_record = self.form_service.prepare_brew_record(form_data, brew_id, estimated_bag_size_grams)
        
        # Add to DataFrame
        st.session_state.df = self.data_service.add_record(st.session_state.df, new_record)
        
        # Save to CSV
        if not self.data_service.save_data(st.session_state.df):
            st.error("Failed to save data")
            return
        
        # Run post-processing
        st.info("🔄 Running post-processing calculations...")
        success, stdout, stderr = self.data_service.run_post_processing()
        
        if success:
            # Reload the data to get the calculated fields
            st.session_state.df = self.data_service.load_data()
            
            # Add to recent additions for highlighting
            self._add_recent_addition(brew_id)
            
            # Enhanced success message with view chart option
            st.success(f"✅ **Cup #{brew_id} added successfully!** View it highlighted on the chart.")
            
            # Add button to navigate to view data tab
            if st.button("📊 View on Chart", type="primary", key="view_chart_btn"):
                st.session_state.active_tab = 0  # View Data tab
                st.rerun()
            
            # Show contextual archive prompt if bag might be running low
            if estimated_bag_size_grams and estimated_bag_size_grams > 0 and coffee_dose_grams:
                self._show_bean_usage_alert(
                    bean_form_data['bean_name'],
                    bean_form_data['bean_origin_country'],
                    bean_form_data['bean_origin_region'],
                    estimated_bag_size_grams
                )
        else:
            st.warning("⚠️ Cup added but post-processing failed. Some calculated fields may be missing.")
        
        # Show processing status
        self.ui.render_processing_status(success, stdout, stderr)
        st.rerun()
    
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
    
    def _render_edit_brews(self):
        """Render the edit brews interface"""
        st.subheader("Edit Individual Brew Records")
        
        if not st.session_state.df.empty:
            # Select cup to edit
            cup_options = [
                f"{self.brew_id_service.safe_brew_id_to_int(row['brew_id'])} - {row['bean_name'] if pd.notna(row['bean_name']) else 'Unknown'} ({row['brew_date']})" 
                for _, row in st.session_state.df.iterrows()
            ]
            selected_cup = st.selectbox("Select cup to edit:", cup_options)
            
            if selected_cup:
                try:
                    selected_id = int(selected_cup.split(' - ')[0])
                    cup_data = st.session_state.df[st.session_state.df['brew_id'] == selected_id].iloc[0]
                except (ValueError, IndexError):
                    st.error("Error parsing cup selection. Please try again.")
                    return
                
                # Render edit form (simplified version)
                st.info(f"Editing cup #{selected_id}")
                st.write("Edit form implementation would go here...")
                st.write(f"Current cup data: {cup_data['bean_name']} - {cup_data['brew_date']}")
                # Note: Full edit form implementation would be similar to add form
        else:
            st.info("No records available to edit")
    
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