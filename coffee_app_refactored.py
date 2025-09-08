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
        self.scoring_service = ThreeFactorScoringService()
        
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
        
        # Handle automatic navigation to View Data tab after cup addition
        if st.session_state.get('auto_navigate_to_chart', False):
            st.session_state.auto_navigate_to_chart = False
            # Show navigation message and switch to View Data tab
            st.success("🎉 **Redirecting to View Data page...** Your new cup is highlighted on the chart!")
            st.rerun()
        
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
    
    def _render_add_cup_tab(self):
        """Render the add new cup tab"""
        st.header("Add new cup")
        
        with st.form("add_cup_form"):
            # Get next ID by reloading fresh data to avoid caching issues
            current_df = self.data_service.load_data()
            next_id = self.data_service.get_next_brew_id(current_df)
            
            
            # Basic info
            brew_id = st.number_input("Brew ID", value=next_id, disabled=True, key=f"brew_id_{next_id}")
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
            
            # Three-Factor Scoring System
            st.markdown("### ⭐ Three-Factor Scoring")
            st.markdown("*Rate each aspect on a scale of 0-5 stars (half-stars allowed)*")
            
            scoring_col1, scoring_col2, scoring_col3 = st.columns(3)
            
            with scoring_col1:
                st.markdown("**🌈 Complexity**")
                st.text("How many distinct flavors can you identify? Are there multiple layers to explore?")
                score_complexity = st.slider("Complexity", min_value=0.0, max_value=5.0, value=2.5, step=0.5, key="complexity_score")
            
            with scoring_col2:
                st.markdown("**🍫 Bitterness**") 
                st.text("Is the bitterness balanced and pleasant, or does it overpower other flavors?")
                score_bitterness = st.slider("Bitterness", min_value=0.0, max_value=5.0, value=2.5, step=0.5, key="bitterness_score")
            
            with scoring_col3:
                st.markdown("**🫖 Mouthfeel**")
                st.text("How does the coffee feel in your mouth? Is the body satisfying?")
                score_mouthfeel = st.slider("Mouthfeel", min_value=0.0, max_value=5.0, value=2.5, step=0.5, key="mouthfeel_score")
            
            # Calculate overall score using service (sliders ensure valid range)
            scores = {'complexity': score_complexity, 'bitterness': score_bitterness, 'mouthfeel': score_mouthfeel}
            validation = self.scoring_service.validate_all_scores(scores)
            if validation.is_valid:
                score_overall_rating = self.scoring_service.calculate_overall_score(scores)
            else:
                # This should not happen with sliders, but provide proper error handling
                st.error("Invalid score values detected. Please ensure all scores are between 0 and 5.")
                for category, error in validation.errors.items():
                    st.error(f"{category.title()}: {error}")
                # Use default score when validation fails
                score_overall_rating = 2.5
            
            # Score notes
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
                # Immediate visual feedback that submission was received
                self._show_immediate_submission_feedback(brew_id, bean_form_data.get('bean_name', 'Unknown Bean'))
                
                # Handle the submission
                self._handle_add_cup_submission(
                    brew_id, brew_date, bean_form_data, grind_size, grind_model, 
                    brew_device, water_temp_degC, coffee_dose_grams, water_volume_ml,
                    mug_weight_grams, brew_method, brew_pulse_target_water_ml,
                    brew_bloom_water_ml, brew_bloom_time_s, agitation_method,
                    pour_technique, brew_total_time_s, final_combined_weight_grams,
                    final_tds_percent, score_flavor_profile_category, score_overall_rating,
                    score_notes, estimated_bag_size_grams, score_complexity, 
                    score_bitterness, score_mouthfeel
                )
        
        # Display overall score after form submission
        if submitted and 'score_complexity' in locals() and 'score_bitterness' in locals() and 'score_mouthfeel' in locals():
            st.markdown("---")
            st.markdown("## ✅ Coffee Scored!")
            
            # Display the three factor scores
            score_display_col1, score_display_col2, score_display_col3, score_display_col4 = st.columns(4)
            
            with score_display_col1:
                st.metric("🌈 Complexity", f"{score_complexity:.1f}/5")
            
            with score_display_col2:
                st.metric("🍫 Bitterness", f"{score_bitterness:.1f}/5")
                
            with score_display_col3:
                st.metric("🫖 Mouthfeel", f"{score_mouthfeel:.1f}/5")
                
            with score_display_col4:
                st.metric("📊 Overall Score", f"{score_overall_rating:.2f}/5", 
                         help="Average of the three factors")
            
            # Show notes if provided
            if score_notes and score_notes.strip():
                st.markdown("**Tasting Notes:**")
                st.info(score_notes)
        
        # Note: Automatic navigation to View Data tab is now handled 
        # by the enhanced celebration system with countdown and visual feedback
    
    def _handle_add_cup_submission(self, brew_id, brew_date, bean_form_data, grind_size, 
                                 grind_model, brew_device, water_temp_degC, coffee_dose_grams,
                                 water_volume_ml, mug_weight_grams, brew_method, 
                                 brew_pulse_target_water_ml, brew_bloom_water_ml, brew_bloom_time_s,
                                 agitation_method, pour_technique, brew_total_time_s, 
                                 final_combined_weight_grams, final_tds_percent, 
                                 score_flavor_profile_category, score_overall_rating, 
                                 score_notes, estimated_bag_size_grams, score_complexity, 
                                 score_bitterness, score_mouthfeel):
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
            'score_notes': score_notes,
            'score_complexity': score_complexity,
            'score_bitterness': score_bitterness,
            'score_mouthfeel': score_mouthfeel,
            'scoring_system_version': '3-factor-v1'
        }
        
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