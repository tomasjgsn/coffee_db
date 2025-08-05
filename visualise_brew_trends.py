import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path
from datetime import datetime, date
import subprocess
import sys

CSV_FILE = Path("data/cups_of_coffee.csv")

def load_data():
    """Load data from csv file, cups_of_coffee.csv"""
    df = pd.read_csv(CSV_FILE)
    # Convert date columns
    if 'brew_date' in df.columns:
        df['brew_date'] = pd.to_datetime(df['brew_date']).dt.date
    if 'bean_purchase_date' in df.columns:
        df['bean_purchase_date'] = pd.to_datetime(df['bean_purchase_date'], errors='coerce').dt.date
    if 'bean_harvest_date' in df.columns:
        df['bean_harvest_date'] = pd.to_datetime(df['bean_harvest_date'], errors='coerce').dt.date
    return df

def save_data(df):
    """Save DataFrame back to cups_of_coffee.csv"""
    df.to_csv(CSV_FILE, index=False)
    st.success(f"Data saved to {CSV_FILE}")

def run_post_processing():
    """Run the post-processing script after saving data"""
    try:
        # Run the processing script with stats to get more detailed output
        result = subprocess.run([
            sys.executable, 'process_coffee_data.py', 
            str(CSV_FILE), '--selective', '--stats'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            st.success("✅ Post-processing completed successfully!")
            
            # Always show processing statistics
            if result.stdout:
                with st.expander("📊 Processing Details", expanded=True):
                    st.text(result.stdout)
            
            # Always show terminal logs
            if result.stderr:
                with st.expander("🔍 Terminal Logs", expanded=False):
                    st.text(result.stderr)
            
            return True, result.stdout, result.stderr
        else:
            st.error(f"❌ Post-processing failed: {result.stderr}")
            # Show error output in logs
            if result.stderr:
                with st.expander("🔍 Error Logs", expanded=False):
                    st.text(result.stderr)
            return False, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        st.error("⏱️ Post-processing timed out (>30s)")
        return False, "", ""
    except FileNotFoundError:
        st.warning("⚠️ process_coffee_data.py not found - skipping post-processing")
        return False, "", ""
    except Exception as e:
        st.error(f"❌ Post-processing error: {str(e)}")
        return False, "", ""

def initialize_session_state():
    """Initialize session state variables"""
    if 'df' not in st.session_state:
        st.session_state.df = load_data()
    if 'selected_row' not in st.session_state:
        st.session_state.selected_row = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False

def main():
    # Page Title
    st.title("☕️ Fiends for the Beans")

    # Initialize session state
    initialize_session_state()

    # Create tabs for different operations
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 View Data", "➕ Add Cup", "✏️ Edit Cups", "🗑️ Delete Cups", "⚙️ Processing"])
    
    with tab1:
        st.header("Brew performance")
        st.write("Plot the brewing data based on the brewing control chart: https://sca.coffee/sca-news/25/issue-13/towards-a-new-brewing-chart")
        
        # Filter Panel
        with st.expander("🔍 Filter Data", expanded=False):
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            # Get unique values for each filter (handle missing values separately)
            with filter_col1:
                st.markdown("**🌱 Beans**")
                available_coffees = sorted(st.session_state.df['bean_name'].dropna().unique())
                selected_coffees = st.multiselect(
                    "Select coffees:",
                    options=available_coffees,
                    default=available_coffees,
                    help="Leave all selected to show all coffees"
                )
            
            with filter_col2:
                st.markdown("**⚙️ Grind Size**")
                available_grinds = sorted(st.session_state.df['grind_size'].dropna().unique())
                selected_grinds = st.multiselect(
                    "Select grind sizes:",
                    options=available_grinds,
                    default=available_grinds,
                    help="Leave all selected to show all grind sizes"
                )
            
            with filter_col3:
                st.markdown("**🌡️ Water Temp (°C)**")
                available_temps = sorted(st.session_state.df['water_temp_degC'].dropna().unique())
                selected_temps = st.multiselect(
                    "Select water temperatures:",
                    options=available_temps,
                    default=available_temps,
                    help="Leave all selected to show all temperatures"
                )
            
            # Apply filters (preserve rows with missing values if not filtering on that field)
            filtered_df = st.session_state.df.copy()
            
            if selected_coffees:
                filtered_df = filtered_df[filtered_df['bean_name'].isin(selected_coffees) | filtered_df['bean_name'].isna()]
            if selected_grinds:
                filtered_df = filtered_df[filtered_df['grind_size'].isin(selected_grinds) | filtered_df['grind_size'].isna()]
            if selected_temps:
                filtered_df = filtered_df[filtered_df['water_temp_degC'].isin(selected_temps) | filtered_df['water_temp_degC'].isna()]
            
            # Show filter summary
            st.markdown("---")
            total_rows = len(st.session_state.df)
            filtered_rows = len(filtered_df)
            st.info(f"📊 Showing **{filtered_rows}** of **{total_rows}** brew records")
        
        # Use filtered data for chart
        chart_data = filtered_df if 'filtered_df' in locals() else st.session_state.df
        
        # Define color scheme for brew quality categories
        color_scale = alt.Scale(
            domain=['Under-Weak', 'Under-Ideal', 'Under-Strong', 'Ideal-Weak', 'Ideal-Ideal', 'Ideal-Strong', 'Over-Weak', 'Over-Ideal', 'Over-Strong'],
            range=['#d62728', '#ff7f0e', '#bcbd22', '#17becf', '#2ca02c', '#9467bd', '#e377c2', '#7f7f7f', '#8c564b']
        )
        
        # Define brewing zone boundaries based on SCA standards
        zone_data = pd.DataFrame([
            {'zone': 'Ideal', 'x_min': 18, 'x_max': 22, 'y_min': 1.15, 'y_max': 1.35, 'opacity': 0.1, 'color': '#2ca02c'},
            {'zone': 'Under-Extracted', 'x_min': 10, 'x_max': 18, 'y_min': 0.6, 'y_max': 1.7, 'opacity': 0.05, 'color': '#d62728'},
            {'zone': 'Over-Extracted', 'x_min': 22, 'x_max': 30, 'y_min': 0.6, 'y_max': 1.7, 'opacity': 0.05, 'color': '#ff7f0e'},
            {'zone': 'Weak', 'x_min': 10, 'x_max': 30, 'y_min': 0.6, 'y_max': 1.15, 'opacity': 0.03, 'color': '#17becf'},
            {'zone': 'Strong', 'x_min': 10, 'x_max': 30, 'y_min': 1.35, 'y_max': 1.7, 'opacity': 0.03, 'color': '#9467bd'}
        ])
        
        # Create background zones
        background_zones = alt.Chart(zone_data).mark_rect().encode(
            x=alt.X('x_min:Q', title="Final Extraction Yield [%]", scale=alt.Scale(domain=[10, 30])),
            x2=alt.X2('x_max:Q'),
            y=alt.Y('y_min:Q', title="Total Dissolved Solids, TDS [%]", scale=alt.Scale(domain=[0.6, 1.7])),
            y2=alt.Y2('y_max:Q'),
            color=alt.Color('color:N', scale=None),
            opacity=alt.Opacity('opacity:Q', scale=None),
            tooltip=['zone:N']
        )
        
        # Create data points chart
        points_chart = alt.Chart(chart_data).mark_circle(size=80, stroke='white', strokeWidth=1).encode(
            x=alt.X('final_extraction_yield_percent', 
                    title="Final Extraction Yield [%]",
                    scale=alt.Scale(domain=[10, 30])),
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
        
        # Combine background and points
        chart = (background_zones + points_chart).resolve_scale(
            color='independent'
        ).properties(
            height=400
        )
        st.altair_chart(chart, use_container_width=True)

        # Display raw data logs
        st.header("Brew logs")
        st.write("Cup data logged")
        st.dataframe(chart_data, use_container_width=True)

    with tab2:
        st.header("Add new cup")

        with st.form("add_cup_form"):
            # Get next ID
            next_id = st.session_state.df['brew_id'].max() + 1 if not st.session_state.df.empty else 1
            
            # Initialize session state for selected bean if not exists
            if 'selected_bean_data' not in st.session_state:
                st.session_state.selected_bean_data = None
            
            # Basic info
            brew_id = st.number_input("Brew ID", value=next_id, disabled=True)
            brew_date = st.date_input("Brew Date", value=date.today())
            
            # ========== ROW 1: BEAN SELECTION ==========
            st.markdown("### 🌱 Bean Selection")
            
            # Available Beans Section (stacked vertically for better scrolling)
            # Get unique beans from existing data
            if not st.session_state.df.empty:
                unique_beans = st.session_state.df.drop_duplicates(
                    subset=['bean_name', 'bean_origin_country', 'bean_origin_region']
                )[['bean_name', 'bean_origin_country', 'bean_origin_region', 'bean_variety', 
                   'bean_process_method', 'bean_roast_date', 'bean_roast_level', 'bean_notes']].dropna(subset=['bean_name'])
                
                bean_options = ["Create New Bean"] + [
                    f"{row['bean_name']} - {row['bean_origin_country'] or 'Unknown'}" 
                    for _, row in unique_beans.iterrows()
                ]
            else:
                bean_options = ["Create New Bean"]
                unique_beans = pd.DataFrame()
            
            selected_bean_option = st.radio(
                "Choose bean:",
                bean_options,
                index=0,
                horizontal=True if len(bean_options) <= 4 else False
            )
            
            # Auto-load bean data when selection changes
            if selected_bean_option != "Create New Bean" and not st.session_state.df.empty:
                # Find the selected bean data
                bean_index = bean_options.index(selected_bean_option) - 1
                selected_bean = unique_beans.iloc[bean_index]
                # Only update if different from current selection
                if st.session_state.selected_bean_data != selected_bean.to_dict():
                    st.session_state.selected_bean_data = selected_bean.to_dict()
            elif selected_bean_option == "Create New Bean":
                st.session_state.selected_bean_data = None
            
            # Show current selection
            if selected_bean_option != "Create New Bean":
                st.success(f"✅ Loaded: {selected_bean_option}")
            else:
                st.info("Creating new bean entry")
            
            # Bean Information Section (collapsed by default)
            with st.expander("📋 Bean Information", expanded=False):
                # Use selected bean data if available, otherwise empty defaults
                bean_data = st.session_state.selected_bean_data or {}
                
                # Two columns for better space usage
                bean_info_col1, bean_info_col2 = st.columns([1, 1])
                
                with bean_info_col1:
                    bean_name = st.text_input(
                        "Bean Name", 
                        value=bean_data.get('bean_name', ''),
                        placeholder="e.g., La Providencia"
                    )
                    bean_origin_country = st.text_input(
                        "Origin Country", 
                        value=bean_data.get('bean_origin_country', ''),
                        placeholder="e.g., Colombia"
                    )
                    bean_origin_region = st.text_input(
                        "Origin Region", 
                        value=bean_data.get('bean_origin_region', ''),
                        placeholder="e.g., Huila"
                    )
                    bean_variety = st.text_input(
                        "Bean Variety", 
                        value=bean_data.get('bean_variety', ''),
                        placeholder="e.g., Cenicafe 1"
                    )
                
                with bean_info_col2:
                    process_methods = ["", "Washed", "Natural", "Honey", "Semi-Washed", "Anaerobic", "Other"]
                    bean_process_method = st.selectbox(
                        "Process Method", 
                        process_methods,
                        index=process_methods.index(bean_data.get('bean_process_method', '')) if bean_data.get('bean_process_method') in process_methods else 0
                    )
                    
                    bean_roast_date = st.date_input(
                        "Roast Date", 
                        value=pd.to_datetime(bean_data.get('bean_roast_date')).date() if bean_data.get('bean_roast_date') else None,
                        help="Leave empty if unknown"
                    )
                    
                    roast_levels = ["", "Light", "Light-Medium", "Medium", "Medium-Dark", "Dark"]
                    bean_roast_level = st.selectbox(
                        "Roast Level", 
                        roast_levels,
                        index=roast_levels.index(bean_data.get('bean_roast_level', '')) if bean_data.get('bean_roast_level') in roast_levels else 0
                    )
                
                # Full width for notes
                bean_notes = st.text_area(
                    "Bean Notes", 
                    value=bean_data.get('bean_notes', ''),
                    placeholder="Tasting notes, descriptions..."
                )
                
                # Bean selection status
                if bean_data:
                    st.success("✅ Bean data loaded from selection")
                else:
                    st.info("💡 Select a bean above or enter new bean details")

            # ========== ROW 2: EQUIPMENT & BREWING ==========
            st.markdown("---")
            st.markdown("### ⚙️ Equipment & Brewing")
            equip_col1, equip_col2 = st.columns([1, 1])
            
            with equip_col1:
                st.subheader("Equipment & Grind")
                
                grind_size = st.number_input("Grind Size", min_value=1.0, max_value=11.0, value=None, step=0.1)
                grind_model = st.text_input("Grind Model", value="Fellow Ode Gen 2", placeholder="e.g., Fellow Ode Gen 2")
                
                brew_device = st.selectbox("Brew Device", 
                    ["", "V60 ceramic", "V60", "Chemex", "Aeropress", "French Press", "Espresso", "Hoffman top up", "Other"],
                    index=1)
                
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
                
                agitation_method = st.selectbox("Agitation Method", 
                    ["", "None", "Stir", "Swirl", "Shake", "Gentle stir"])
                
                pour_technique = st.selectbox("Pour Technique", 
                    ["", "Spiral", "Center pour", "Concentric circles", "Pulse pour", "Continuous"])

                # Move final mass here
                brew_total_time_s = st.number_input("Total Brew Time (seconds)", min_value=0, value=None)
                final_combined_weight_grams = st.number_input("Final Combined Weight (g)", min_value=0.0, value=None, step=0.1, help="Total weight: mug + coffee")
                

            # ========== ROW 3: RESULTS & SCORING ==========
            st.markdown("---")
            st.markdown("### 📊 Results & Scoring")
            
            results_col1, results_col2, results_col3 = st.columns([1, 1, 2])
            
            with results_col1:
                final_tds_percent = st.number_input("TDS %", min_value=0.0, max_value=5.0, value=None, step=0.01)
            
            with results_col2:
                score_flavor_profile_category = st.selectbox("Flavor Profile", 
                    ["", "Bright/Acidic", "Balanced", "Rich/Full", "Sweet", "Bitter", "Fruity", "Nutty", "Chocolatey"])
                
            with results_col3:
                score_overall_rating = st.slider("Overall Rating", min_value=1.0, max_value=10.0, value=5.0, step=0.1)
            
            score_notes = st.text_area("Score Notes", placeholder="Detailed tasting notes...", height=100)  

            # Submit button spanning all columns
            st.markdown("---")
            submitted = st.form_submit_button("☕ Add Cup Record", use_container_width=True, type="primary")
            # Info about calculated fields
            st.markdown("**Auto-Calculated Fields** *(Will be computed after saving)*")
            st.info("""
            The following fields will be automatically calculated:          
            • Days since roast\n
            • Brew ratio (water:coffee)\n
            • Extraction yield %\n
            • Coffee grams per liter\n
            • Strength category (Weak/Ideal/Strong)\n
            • Extraction category (Under/Ideal/Over)\n
            • Brewing zone classification\n
            • Composite brew score\n
            • Bean usage statistics\n
            • Processing metadata\n
            """)
            
            if submitted:
                # Calculate final_brew_mass_grams from mug weight and combined weight
                final_brew_mass_grams = None
                if mug_weight_grams is not None and final_combined_weight_grams is not None:
                    final_brew_mass_grams = final_combined_weight_grams - mug_weight_grams
                
                # Collect only input fields (no calculated or metadata fields)
                new_record = {
                    'brew_id': brew_id,
                    'brew_date': brew_date,
                    'bean_name': bean_name if bean_name else None,
                    'bean_origin_country': bean_origin_country if bean_origin_country else None,
                    'bean_origin_region': bean_origin_region if bean_origin_region else None,
                    'bean_variety': bean_variety if bean_variety else None,
                    'bean_process_method': bean_process_method if bean_process_method else None,
                    'bean_roast_date': bean_roast_date,
                    'bean_roast_level': bean_roast_level if bean_roast_level else None,
                    'bean_notes': bean_notes if bean_notes else None,
                    'grind_size': grind_size,
                    'grind_model': grind_model if grind_model else None,
                    'brew_method': brew_method if brew_method else None,
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
                    'final_brew_mass_grams': final_brew_mass_grams,
                    'score_overall_rating': score_overall_rating,
                    'score_notes': score_notes if score_notes else None,
                    'score_flavor_profile_category': score_flavor_profile_category if score_flavor_profile_category else None,
                    # Add new fields for mug tracking
                    'mug_weight_grams': mug_weight_grams,
                    'final_combined_weight_grams': final_combined_weight_grams
                }
                
                # Add to DataFrame
                if st.session_state.df.empty:
                    st.session_state.df = pd.DataFrame([new_record])
                else:
                    new_df = pd.concat([st.session_state.df, pd.DataFrame([new_record])], ignore_index=True)
                    st.session_state.df = new_df
                
                # Save to CSV
                save_data(st.session_state.df)
                
                # Run post-processing script to calculate derived fields
                st.info("🔄 Running post-processing calculations...")
                success, stdout, stderr = run_post_processing()
                if success:
                    # Reload the data to get the calculated fields
                    st.session_state.df = load_data()
                    st.success("✅ New cup added and processed successfully!")
                else:
                    st.warning("⚠️ Cup added but post-processing failed. Some calculated fields may be missing.")
                
                st.rerun()

    with tab3:
        st.header("Edit Cup Record")
        
        if not st.session_state.df.empty:
            # Select cup to edit
            cup_options = [f"{int(row['brew_id'])} - {row['bean_name'] if pd.notna(row['bean_name']) else 'Unknown'} ({row['brew_date']})" for _, row in st.session_state.df.iterrows()]
            selected_cup = st.selectbox("Select cup to edit:", cup_options)
            
            if selected_cup:
                try:
                    selected_id = int(selected_cup.split(' - ')[0])
                    cup_data = st.session_state.df[st.session_state.df['brew_id'] == selected_id].iloc[0]
                except (ValueError, IndexError):
                    st.error("Error parsing cup selection. Please try again.")
                    return
                
                with st.form("edit_cup_form"):
                    st.info(f"Editing cup #{selected_id}")
                    
                    # Basic info
                    brew_date = st.date_input("Brew Date", value=pd.to_datetime(cup_data['brew_date']).date() if pd.notna(cup_data['brew_date']) else None)
                    
                    # Bean Information
                    st.markdown("### 🌱 Bean Information")
                    bean_col1, bean_col2 = st.columns([1, 1])
                    
                    with bean_col1:
                        bean_name = st.text_input("Bean Name", value=cup_data['bean_name'] if pd.notna(cup_data['bean_name']) else "")
                        bean_origin_country = st.text_input("Origin Country", value=cup_data['bean_origin_country'] if pd.notna(cup_data['bean_origin_country']) else "")
                        bean_origin_region = st.text_input("Origin Region", value=cup_data['bean_origin_region'] if pd.notna(cup_data['bean_origin_region']) else "")
                    
                    with bean_col2:
                        bean_variety = st.text_input("Bean Variety", value=cup_data['bean_variety'] if pd.notna(cup_data['bean_variety']) else "")
                        process_methods = ["", "Washed", "Natural", "Honey", "Semi-Washed", "Anaerobic", "Other"]
                        current_process = cup_data['bean_process_method'] if pd.notna(cup_data['bean_process_method']) else ""
                        bean_process_method = st.selectbox("Process Method", process_methods, 
                                                         index=process_methods.index(current_process) if current_process in process_methods else 0)
                        
                        roast_levels = ["", "Light", "Light-Medium", "Medium", "Medium-Dark", "Dark"]
                        current_roast = cup_data['bean_roast_level'] if pd.notna(cup_data['bean_roast_level']) else ""
                        bean_roast_level = st.selectbox("Roast Level", roast_levels,
                                                       index=roast_levels.index(current_roast) if current_roast in roast_levels else 0)
                    
                    bean_notes = st.text_area("Bean Notes", value=cup_data['bean_notes'] if pd.notna(cup_data['bean_notes']) else "")
                    
                    # Equipment & Brewing
                    st.markdown("### ⚙️ Equipment & Brewing")
                    equip_col1, equip_col2 = st.columns([1, 1])
                    
                    with equip_col1:
                        grind_size = st.number_input("Grind Size", min_value=1.0, max_value=11.0, step=0.1,
                                                   value=float(cup_data['grind_size']) if pd.notna(cup_data['grind_size']) else None)
                        grind_model = st.text_input("Grind Model", value=cup_data['grind_model'] if pd.notna(cup_data['grind_model']) else "Fellow Ode Gen 2")
                        
                        brew_devices = ["", "V60 ceramic", "V60", "Chemex", "Aeropress", "French Press", "Espresso", "Hoffman top up", "Other"]
                        current_device = cup_data['brew_device'] if pd.notna(cup_data['brew_device']) else ""
                        brew_device = st.selectbox("Brew Device", brew_devices,
                                                  index=brew_devices.index(current_device) if current_device in brew_devices else 0)
                        
                        water_temp_degC = st.number_input("Water Temperature (°C)", min_value=70.0, max_value=100.0, step=0.1,
                                                        value=float(cup_data['water_temp_degC']) if pd.notna(cup_data['water_temp_degC']) else None)
                    
                    with equip_col2:
                        brew_method = st.text_input("Brew Method", value=cup_data['brew_method'] if pd.notna(cup_data['brew_method']) else "3 pulse V60")
                        coffee_dose_grams = st.number_input("Coffee Dose (g)", min_value=0.0, step=0.1,
                                                          value=float(cup_data['coffee_dose_grams']) if pd.notna(cup_data['coffee_dose_grams']) else None)
                        water_volume_ml = st.number_input("Water Volume (ml)", min_value=0.0, step=0.1,
                                                        value=float(cup_data['water_volume_ml']) if pd.notna(cup_data['water_volume_ml']) else None)
                        brew_total_time_s = st.number_input("Total Brew Time (seconds)", min_value=0,
                                                          value=int(cup_data['brew_total_time_s']) if pd.notna(cup_data['brew_total_time_s']) else None)
                        
                        # Add mug weight fields
                        mug_weight_grams = st.number_input("Mug Weight (g)", min_value=0.0, step=0.1,
                                                         value=float(cup_data['mug_weight_grams']) if pd.notna(cup_data.get('mug_weight_grams')) else None,
                                                         help="Weight of empty mug")
                        final_combined_weight_grams = st.number_input("Final Combined Weight (g)", min_value=0.0, step=0.1,
                                                                    value=float(cup_data['final_combined_weight_grams']) if pd.notna(cup_data.get('final_combined_weight_grams')) else None,
                                                                    help="Total weight: mug + coffee")
                    
                    # Results & Scoring
                    st.markdown("### 📊 Results & Scoring")
                    results_col1, results_col2 = st.columns([1, 1])
                    
                    with results_col1:
                        final_tds_percent = st.number_input("TDS %", min_value=0.0, max_value=5.0, step=0.01,
                                                          value=float(cup_data['final_tds_percent']) if pd.notna(cup_data['final_tds_percent']) else None)
                    
                    with results_col2:
                        score_overall_rating = st.slider("Overall Rating", min_value=1.0, max_value=10.0, step=0.1,
                                                        value=float(cup_data['score_overall_rating']) if pd.notna(cup_data['score_overall_rating']) else 5.0)
                        
                        flavor_profiles = ["", "Bright/Acidic", "Balanced", "Rich/Full", "Sweet", "Bitter", "Fruity", "Nutty", "Chocolatey"]
                        current_flavor = cup_data['score_flavor_profile_category'] if pd.notna(cup_data['score_flavor_profile_category']) else ""
                        score_flavor_profile_category = st.selectbox("Flavor Profile", flavor_profiles,
                                                                    index=flavor_profiles.index(current_flavor) if current_flavor in flavor_profiles else 0)
                    
                    score_notes = st.text_area("Score Notes", value=cup_data['score_notes'] if pd.notna(cup_data['score_notes']) else "")
                    
                    # Submit button
                    st.markdown("---")
                    submitted = st.form_submit_button("💾 Update Cup Record", use_container_width=True, type="primary")
                    
                    if submitted:
                        # Calculate final_brew_mass_grams from mug weight and combined weight
                        calculated_final_brew_mass_grams = None
                        if mug_weight_grams is not None and final_combined_weight_grams is not None:
                            calculated_final_brew_mass_grams = final_combined_weight_grams - mug_weight_grams
                        
                        # Update the record
                        idx = st.session_state.df[st.session_state.df['brew_id'] == selected_id].index[0]
                        
                        # Update only input fields (preserve calculated fields)
                        st.session_state.df.loc[idx, 'brew_date'] = brew_date
                        st.session_state.df.loc[idx, 'bean_name'] = bean_name if bean_name else None
                        st.session_state.df.loc[idx, 'bean_origin_country'] = bean_origin_country if bean_origin_country else None
                        st.session_state.df.loc[idx, 'bean_origin_region'] = bean_origin_region if bean_origin_region else None
                        st.session_state.df.loc[idx, 'bean_variety'] = bean_variety if bean_variety else None
                        st.session_state.df.loc[idx, 'bean_process_method'] = bean_process_method if bean_process_method else None
                        st.session_state.df.loc[idx, 'bean_roast_level'] = bean_roast_level if bean_roast_level else None
                        st.session_state.df.loc[idx, 'bean_notes'] = bean_notes if bean_notes else None
                        st.session_state.df.loc[idx, 'grind_size'] = grind_size
                        st.session_state.df.loc[idx, 'grind_model'] = grind_model if grind_model else None
                        st.session_state.df.loc[idx, 'brew_method'] = brew_method if brew_method else None
                        st.session_state.df.loc[idx, 'brew_device'] = brew_device if brew_device else None
                        st.session_state.df.loc[idx, 'coffee_dose_grams'] = coffee_dose_grams
                        st.session_state.df.loc[idx, 'water_volume_ml'] = water_volume_ml
                        st.session_state.df.loc[idx, 'water_temp_degC'] = water_temp_degC
                        st.session_state.df.loc[idx, 'brew_total_time_s'] = brew_total_time_s
                        st.session_state.df.loc[idx, 'final_tds_percent'] = final_tds_percent
                        st.session_state.df.loc[idx, 'final_brew_mass_grams'] = calculated_final_brew_mass_grams
                        st.session_state.df.loc[idx, 'score_overall_rating'] = score_overall_rating
                        st.session_state.df.loc[idx, 'score_notes'] = score_notes if score_notes else None
                        st.session_state.df.loc[idx, 'score_flavor_profile_category'] = score_flavor_profile_category if score_flavor_profile_category else None
                        # Update new mug weight fields
                        st.session_state.df.loc[idx, 'mug_weight_grams'] = mug_weight_grams
                        st.session_state.df.loc[idx, 'final_combined_weight_grams'] = final_combined_weight_grams
                        
                        # Save to CSV
                        save_data(st.session_state.df)
                        
                        # Run post-processing to recalculate derived fields
                        st.info("🔄 Running post-processing calculations...")
                        success, stdout, stderr = run_post_processing()
                        if success:
                            # Reload the data to get the updated calculated fields
                            st.session_state.df = load_data()
                            st.success("✅ Cup record updated and processed successfully!")
                        else:
                            st.warning("⚠️ Cup updated but post-processing failed. Some calculated fields may be outdated.")
                        
                        st.rerun()
        else:
            st.info("No records available to edit")

    with tab4:
        st.header("Delete Cup Record")
        
        if not st.session_state.df.empty:
            # Cup selection with proper formatting
            cup_options = [f"{int(row['brew_id'])} - {row['bean_name'] if pd.notna(row['bean_name']) else 'Unknown'} ({row['brew_date']})" for _, row in st.session_state.df.iterrows()]
            selected_cup = st.selectbox("Select cup to delete:", cup_options)
            
            if selected_cup:
                try:
                    selected_id = int(selected_cup.split(' - ')[0])
                    cup_data = st.session_state.df[st.session_state.df['brew_id'] == selected_id].iloc[0]
                except (ValueError, IndexError):
                    st.error("Error parsing cup selection. Please try again.")
                    return
                
                # Show detailed cup information in a card format
                st.markdown("---")
                st.subheader("⚠️ Cup to Delete")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Cup ID", f"#{int(cup_data['brew_id'])}")
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
                                # Perform the deletion
                                st.session_state.df = st.session_state.df[st.session_state.df['brew_id'] != selected_id].reset_index(drop=True)
                                
                                # Save to CSV
                                save_data(st.session_state.df)
                                
                                # Reset confirmation state
                                st.session_state.delete_confirmation_step = 0
                                st.session_state.selected_delete_id = None
                                if 'delete_confirmation_input' in st.session_state:
                                    del st.session_state['delete_confirmation_input']
                                
                                st.success(f"✅ Cup #{selected_id} has been permanently deleted.")
                                st.rerun()
                    
                    if not delete_enabled and confirmation_text.strip():
                        st.warning("Please type exactly **DELETE** to confirm (case insensitive)")
        else:
            st.info("No records available to delete")

    with tab5:
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
                success, stdout, stderr = run_post_processing()
            else:
                # Run with --force-full flag for complete reprocessing
                try:
                    result = subprocess.run([
                        sys.executable, 'process_coffee_data.py', 
                        str(CSV_FILE), '--force-full', '--stats'
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        st.success("✅ Full processing completed successfully!")
                        if result.stdout:
                            with st.expander("📊 Processing Details", expanded=True):
                                st.text(result.stdout)
                        
                        # Always show terminal logs
                        if result.stderr:
                            with st.expander("🔍 Terminal Logs", expanded=False):
                                st.text(result.stderr)
                        
                        success = True
                        stdout, stderr = result.stdout, result.stderr
                    else:
                        st.error(f"❌ Processing failed: {result.stderr}")
                        # Show error logs
                        if result.stderr:
                            with st.expander("🔍 Error Logs", expanded=False):
                                st.text(result.stderr)
                        success = False
                        stdout, stderr = result.stdout, result.stderr
                except subprocess.TimeoutExpired:
                    st.error("⏱️ Processing timed out (>60s)")
                    success = False
                    stdout, stderr = "", ""
                except Exception as e:
                    st.error(f"❌ Processing error: {str(e)}")
                    success = False
                    stdout, stderr = "", ""
            
            if success:
                # Reload the data to get any updates
                st.session_state.df = load_data()
                st.success("✅ Data reloaded successfully!")
                # Don't call st.rerun() immediately to prevent logs from disappearing

if __name__ == "__main__":
    main()