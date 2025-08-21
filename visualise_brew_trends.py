import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path
from datetime import datetime, date
import subprocess
import sys
from src.services.brew_id_service import BrewIdService

CSV_FILE = Path("data/cups_of_coffee.csv")

# Global brew ID service instance
_brew_id_service = BrewIdService()

def safe_int_brew_id(brew_id, default=0):
    """Safely convert brew_id to int to avoid TypeError"""
    return _brew_id_service.safe_brew_id_to_int(brew_id, default)

def load_data():
    """Load data from csv file, cups_of_coffee.csv"""
    import csv
    df = pd.read_csv(CSV_FILE, quoting=csv.QUOTE_MINIMAL)
    
    # Clean and fix brew_id column
    if 'brew_id' in df.columns:
        # Convert to numeric, invalid values become NaN
        df['brew_id'] = pd.to_numeric(df['brew_id'], errors='coerce')
        
        # Find records with invalid brew_id (now NaN)
        invalid_mask = df['brew_id'].isna()
        if invalid_mask.any():
            # Get the next valid ID to assign to invalid records
            max_valid_id = df.loc[~invalid_mask, 'brew_id'].max()
            next_id = int(max_valid_id + 1) if pd.notna(max_valid_id) else 1
            
            # Assign sequential IDs to invalid records
            num_invalid = invalid_mask.sum()
            df.loc[invalid_mask, 'brew_id'] = list(range(next_id, next_id + num_invalid))
            
            print(f"Fixed {num_invalid} invalid brew_id values, assigned IDs {next_id}-{next_id + num_invalid - 1}")
        
        # Convert to integer type
        df['brew_id'] = df['brew_id'].astype('Int64')
    
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
    # Validate brew_id before saving
    if 'brew_id' in df.columns:
        invalid_ids = df['brew_id'].isna() | (df['brew_id'] < 1)
        if invalid_ids.any():
            st.error(f"Cannot save: {invalid_ids.sum()} records have invalid brew_id values")
            return False
    
    # Prepare a copy for saving to handle date fields properly
    df_to_save = df.copy()
    
    # Convert date columns back to strings for CSV saving to avoid NaN/float issues
    date_columns = ['bean_purchase_date', 'bean_harvest_date']
    for col in date_columns:
        if col in df_to_save.columns:
            # Convert NaT (pandas null dates) to empty strings
            df_to_save[col] = df_to_save[col].astype(str).replace('NaT', '')
    
    import csv
    df_to_save.to_csv(CSV_FILE, index=False, quoting=csv.QUOTE_MINIMAL)
    st.success(f"Data saved to {CSV_FILE}")
    return True

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

def generate_grind_dial_options():
    """Generate grind size options matching Fellow Ode Gen 2 dial (1-11 with .1, .2 intermediates)"""
    options = []
    for i in range(1, 12):  # 1 to 11
        options.append(float(i))       # e.g., 5.0
        if i < 11:  # Don't add intermediates after 11
            options.append(i + 0.1)    # e.g., 5.1
            options.append(i + 0.2)    # e.g., 5.2
    return options

def grind_size_dial(label, current_value=None, key=None):
    """Create a grind size dial that mimics Fellow Ode Gen 2 interface"""
    options = generate_grind_dial_options()
    
    # Format options for display (show integers without decimal, decimals with one place)
    formatted_options = []
    for opt in options:
        if opt == int(opt):
            formatted_options.append(f"{int(opt)}")
        else:
            formatted_options.append(f"{opt:.1f}")
    
    # Find current index
    current_index = 0
    if current_value is not None:
        try:
            current_index = options.index(float(current_value))
        except (ValueError, TypeError):
            current_index = 0
    
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

def render_bean_selection_component(context="add", current_bean_data=None, key_prefix=""):
    """
    Unified bean selection component for both add and edit workflows.
    
    Args:
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
    if not st.session_state.df.empty:
        # Filter out archived beans unless "show archived" is enabled
        show_archived = st.checkbox(
            "Show archived beans", 
            value=False, 
            help="Include archived beans in selection", 
            key=f"{key_prefix}show_archived"
        )
        
        df_filtered = st.session_state.df.copy()
        if not show_archived:
            # Only show active beans (default behavior if archive_status is missing)
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
        
        # Create bean options with usage information
        bean_options = ["Create New Bean" if context == "add" else "Manual Entry"]
        for _, row in unique_beans.iterrows():
            # Calculate usage for this bean
            bean_usage = st.session_state.df[
                (st.session_state.df['bean_name'] == row['bean_name']) & 
                (st.session_state.df['bean_origin_country'] == row['bean_origin_country']) &
                (st.session_state.df['bean_origin_region'] == row['bean_origin_region'])
            ]['coffee_dose_grams'].fillna(0).sum()
            
            bag_size = row.get('estimated_bag_size_grams', 0) or 0
            usage_info = ""
            if bag_size > 0:
                remaining = max(0, bag_size - bean_usage)
                usage_info = f" (~{remaining:.0f}g remaining)"
            
            archive_indicator = " 📦" if row.get('archive_status') == 'archived' else ""
            bean_display = f"{row['bean_name']}{usage_info}{archive_indicator}"
            bean_options.append(bean_display)
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
    if selected_bean_option != manual_entry_label and not st.session_state.df.empty:
        # Find the selected bean data
        bean_index = bean_options.index(selected_bean_option) - 1
        selected_bean = unique_beans.iloc[bean_index]
        # Only update if different from current selection
        if st.session_state[session_key] != selected_bean.to_dict():
            st.session_state[session_key] = selected_bean.to_dict()
    elif selected_bean_option == manual_entry_label:
        st.session_state[session_key] = None
    
    # Show current selection with preview of what will be populated
    if selected_bean_option != manual_entry_label:
        st.success(f"✅ Loaded: {selected_bean_option}")
        
        # Show preview of bean data that will populate the fields
        if st.session_state[session_key]:
            bean_data = st.session_state[session_key]
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
    else:
        mode_text = "Creating new bean entry" if context == "add" else "Manual entry mode - fields populated with current data"
        st.info(mode_text)
    
    return st.session_state[session_key]

def render_bean_information_form(context="add", selected_bean_data=None, current_bean_data=None, key_prefix=""):
    """
    Unified bean information form component.
    
    Args:
        context: "add" or "edit" - determines default behavior
        selected_bean_data: dict from bean selection (if any)
        current_bean_data: dict of current bean data (for edit mode fallback)
        key_prefix: unique prefix for form field keys
    
    Returns:
        dict: Form field values
    """
    # Determine data source priority:
    # 1. Selected bean data (from dropdown)
    # 2. Current bean data (for edit mode)
    # 3. Empty defaults (for new entries)
    if selected_bean_data:
        bean_data_source = selected_bean_data
    elif current_bean_data:
        bean_data_source = current_bean_data
    else:
        bean_data_source = {}
    
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
        process_methods = ["", "Washed", "Natural", "Honey", "Semi-Washed", "Anaerobic", "Other"]
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
        
        roast_levels = ["", "Light", "Light-Medium", "Medium", "Medium-Dark", "Dark"]
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 View Data", "➕ Add Cup", "✏️ Data Management", "🗑️ Delete Cups", "⚙️ Processing"])
    
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
            # Get next ID using the service to handle string/numeric mix
            next_id = _brew_id_service.get_next_id(st.session_state.df)
            
            # Basic info
            brew_id = st.number_input("Brew ID", value=next_id, disabled=True)
            brew_date = st.date_input("Brew Date", value=date.today())
            
            # ========== BEAN SELECTION (UNIFIED COMPONENT) ==========
            selected_bean_data = render_bean_selection_component(
                context="add", 
                key_prefix="add_"
            )
            
            # Bean Information Section (collapsed by default)
            with st.expander("📋 Bean Information", expanded=False):
                bean_form_data = render_bean_information_form(
                    context="add",
                    selected_bean_data=selected_bean_data,
                    key_prefix="add_"
                )
                
                # Add inventory tracking for new beans
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
                
                # Extract bean data from form
                bean_name = bean_form_data['bean_name']
                bean_variety = bean_form_data['bean_variety']
                bean_process_method = bean_form_data['bean_process_method']
                bean_roast_date = bean_form_data['bean_roast_date']
                bean_roast_level = bean_form_data['bean_roast_level']
                bean_notes = bean_form_data['bean_notes']

            # ========== ROW 2: EQUIPMENT & BREWING ==========
            st.markdown("---")
            st.markdown("### ⚙️ Equipment & Brewing")
            equip_col1, equip_col2 = st.columns([1, 1])
            
            with equip_col1:
                st.subheader("Equipment & Grind")
                
                grind_size = grind_size_dial("Grind Size", current_value=6.0, key="add_grind_size")
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
                
                # For country and region, use values from form data
                bean_origin_country = bean_form_data.get('bean_origin_country') or None
                bean_origin_region = bean_form_data.get('bean_origin_region') or None
                
                # Collect only input fields (no calculated or metadata fields)
                new_record = {
                    'brew_id': brew_id,
                    'brew_date': brew_date,
                    'bean_name': bean_name if bean_name else None,
                    'bean_origin_country': bean_origin_country,
                    'bean_origin_region': bean_origin_region,
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
                    'final_combined_weight_grams': final_combined_weight_grams,
                    # Add new inventory and archive fields
                    'estimated_bag_size_grams': estimated_bag_size_grams if estimated_bag_size_grams > 0 else None,
                    'archive_status': 'active'  # All new beans start as active
                }
                
                # Add to DataFrame
                if st.session_state.df.empty:
                    st.session_state.df = pd.DataFrame([new_record])
                else:
                    new_df = pd.concat([st.session_state.df, pd.DataFrame([new_record])], ignore_index=True)
                    st.session_state.df = new_df
                
                # Save to CSV
                if not save_data(st.session_state.df):
                    st.stop()
                
                # Run post-processing script to calculate derived fields
                st.info("🔄 Running post-processing calculations...")
                success, stdout, stderr = run_post_processing()
                if success:
                    # Reload the data to get the calculated fields
                    st.session_state.df = load_data()
                    st.success("✅ New cup added and processed successfully!")
                    
                    # Show contextual archive prompt if bag might be running low
                    if estimated_bag_size_grams > 0 and coffee_dose_grams:
                        # Calculate total usage for this bean using null-safe comparison
                        name_match = st.session_state.df['bean_name'] == bean_name
                        country_match = st.session_state.df['bean_origin_country'] == bean_origin_country
                        if pd.isna(bean_origin_region):
                            region_match = st.session_state.df['bean_origin_region'].isna()
                        else:
                            region_match = st.session_state.df['bean_origin_region'] == bean_origin_region
                        
                        bean_usage = st.session_state.df[name_match & country_match & region_match
                        ]['coffee_dose_grams'].fillna(0).sum()
                        
                        remaining = max(0, estimated_bag_size_grams - bean_usage)
                        usage_percentage = (bean_usage / estimated_bag_size_grams) * 100
                        
                        if usage_percentage >= 90:  # 90% or more used
                            st.info(f"💡 **Bean Alert:** Only ~{remaining:.0f}g remaining ({usage_percentage:.0f}% used). Consider archiving if bag is empty?")
                        elif usage_percentage >= 75:  # 75% or more used
                            st.info(f"📦 **Inventory:** ~{remaining:.0f}g remaining ({usage_percentage:.0f}% used)")
                else:
                    st.warning("⚠️ Cup added but post-processing failed. Some calculated fields may be missing.")
                
                st.rerun()

    with tab3:
        st.header("Data Management")
        
        # Sub-tabs for different management functions
        mgmt_tab1, mgmt_tab2, mgmt_tab3 = st.tabs(["✏️ Edit Brews", "📦 Bean Management", "🔄 Batch Operations"])
        
        with mgmt_tab1:
            st.subheader("Edit Individual Brew Records")
            
            if not st.session_state.df.empty:
                # Select cup to edit
                cup_options = [f"{safe_int_brew_id(row['brew_id'])} - {row['bean_name'] if pd.notna(row['bean_name']) else 'Unknown'} ({row['brew_date']})" for _, row in st.session_state.df.iterrows()]
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
                        
                        # ========== BEAN SELECTION (UNIFIED COMPONENT) ==========
                        # Prepare current bean data from cup_data for fallback
                        current_bean_data = {
                            'bean_name': cup_data['bean_name'] if pd.notna(cup_data['bean_name']) else "",
                            'bean_origin_country': cup_data['bean_origin_country'] if pd.notna(cup_data['bean_origin_country']) else "",
                            'bean_origin_region': cup_data['bean_origin_region'] if pd.notna(cup_data['bean_origin_region']) else "",
                            'bean_variety': cup_data['bean_variety'] if pd.notna(cup_data['bean_variety']) else "",
                            'bean_process_method': cup_data['bean_process_method'] if pd.notna(cup_data['bean_process_method']) else "",
                            'bean_roast_level': cup_data['bean_roast_level'] if pd.notna(cup_data['bean_roast_level']) else "",
                            'bean_notes': cup_data['bean_notes'] if pd.notna(cup_data['bean_notes']) else ""
                        }
                        
                        selected_bean_data = render_bean_selection_component(
                            context="edit",
                            key_prefix="edit_"
                        )
                        
                        # Bean Information Section
                        st.markdown("### 🌱 Bean Information")
                        bean_form_data = render_bean_information_form(
                            context="edit",
                            selected_bean_data=selected_bean_data,
                            current_bean_data=current_bean_data,
                            key_prefix="edit_"
                        )
                        
                        # Extract bean data from form
                        bean_name = bean_form_data['bean_name']
                        bean_origin_country = bean_form_data['bean_origin_country']
                        bean_origin_region = bean_form_data['bean_origin_region']
                        bean_variety = bean_form_data['bean_variety']
                        bean_process_method = bean_form_data['bean_process_method']
                        bean_roast_level = bean_form_data['bean_roast_level']
                        bean_notes = bean_form_data['bean_notes']
                        
                        # Equipment & Brewing
                        st.markdown("### ⚙️ Equipment & Brewing")
                        equip_col1, equip_col2 = st.columns([1, 1])
                        
                        with equip_col1:
                            grind_size = grind_size_dial("Grind Size", 
                                                       current_value=cup_data['grind_size'] if pd.notna(cup_data['grind_size']) else None,
                                                       key="edit_grind_size")
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
                            success, _, _ = run_post_processing()
                            if success:
                                # Reload the data to get the updated calculated fields
                                st.session_state.df = load_data()
                                st.success("✅ Cup record updated and processed successfully!")
                            else:
                                st.warning("⚠️ Cup updated but post-processing failed. Some calculated fields may be outdated.")
                            
                            st.rerun()
            else:
                st.info("No records available to edit")
                
        with mgmt_tab2:
            render_bean_management()
            
        with mgmt_tab3:
            render_batch_operations()

    with tab4:
        st.header("Delete Cup Record")
        
        if not st.session_state.df.empty:
            # Cup selection with proper formatting
            cup_options = [f"{safe_int_brew_id(row['brew_id'])} - {row['bean_name'] if pd.notna(row['bean_name']) else 'Unknown'} ({row['brew_date']})" for _, row in st.session_state.df.iterrows()]
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
                    st.metric("Cup ID", f"#{safe_int_brew_id(cup_data['brew_id'])}")
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

def get_bean_statistics(df):
    """Calculate statistics for each unique bean"""
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
        
        bean_stats.append({
            'name': bean_combo['bean_name'],
            'country': bean_combo['bean_origin_country'] or 'Unknown',
            'region': bean_combo['bean_origin_region'] if pd.notna(bean_combo['bean_origin_region']) else '',
            'total_brews': total_brews,
            'total_grams_used': total_grams_used,
            'bag_size': bag_size,
            'remaining_grams': remaining_grams,
            'usage_percentage': usage_percentage,
            'avg_rating': avg_rating,
            'last_used': last_used,
            'days_since_last': days_since_last,
            'archive_status': archive_status,
            'records': bean_records
        })
    
    return bean_stats

def archive_bean(bean_name, bean_country, bean_region, df):
    """Archive a bean by updating all its records"""
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

def restore_bean(bean_name, bean_country, bean_region, df):
    """Restore an archived bean by updating all its records"""
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

def render_bean_management():
    """Render the Bean Management interface with Option A layout"""
    st.subheader("Bean Inventory & Archive Management")
    
    if st.session_state.df.empty:
        st.info("No bean data available")
        return
    
    # Get bean statistics
    bean_stats = get_bean_statistics(st.session_state.df)
    
    if not bean_stats:
        st.info("No beans found in the database")
        return
    
    # Separate active and archived beans
    active_beans = [bean for bean in bean_stats if bean['archive_status'] != 'archived']
    archived_beans = [bean for bean in bean_stats if bean['archive_status'] == 'archived']
    
    # Active Beans Section
    st.markdown(f"### 📊 Active Beans ({len(active_beans)})")
    
    if active_beans:
        # Sort options
        sort_options = {
            "Last Used (Recent First)": lambda x: -x['days_since_last'] if x['days_since_last'] != float('inf') else float('inf'),
            "Usage % (High to Low)": lambda x: -x['usage_percentage'],
            "Total Brews (High to Low)": lambda x: -x['total_brews'],
            "Average Rating (High to Low)": lambda x: -x['avg_rating'],
            "Bean Name (A-Z)": lambda x: x['name'].lower()
        }
        
        sort_by = st.selectbox("Sort by:", list(sort_options.keys()))
        active_beans_sorted = sorted(active_beans, key=sort_options[sort_by])
        
        # Display active beans
        for bean in active_beans_sorted:
            with st.expander(f"🌱 {bean['name']} - {bean['country']} {bean['region']}", expanded=False):
                col_info, col_actions = st.columns([3, 1])
                
                with col_info:
                    # Basic stats
                    info_col1, info_col2, info_col3 = st.columns(3)
                    
                    with info_col1:
                        st.metric("Total Brews", bean['total_brews'])
                        if bean['days_since_last'] != float('inf'):
                            st.write(f"**Last used:** {bean['days_since_last']} days ago")
                        else:
                            st.write("**Last used:** Never")
                    
                    with info_col2:
                        st.metric("Used", f"{bean['total_grams_used']:.0f}g")
                        if bean['bag_size'] > 0:
                            st.write(f"**Bag size:** {bean['bag_size']:.0f}g")
                    
                    with info_col3:
                        if bean['avg_rating'] > 0:
                            st.metric("Avg Rating", f"{bean['avg_rating']:.1f}/10")
                        if bean['bag_size'] > 0:
                            st.write(f"**Remaining:** ~{bean['remaining_grams']:.0f}g ({bean['usage_percentage']:.0f}% used)")
                            
                            # Progress bar for usage
                            progress_value = min(bean['usage_percentage'] / 100, 1.0)
                            st.progress(progress_value)
                
                with col_actions:
                    st.write("**Actions**")
                    
                    # Archive button
                    if st.button(f"📦 Archive", key=f"archive_{bean['name']}_{bean['country']}_{bean['region']}", 
                                help="Mark this bean as archived (removes from active selection)"):
                        # Convert empty string to None for null regions
                        region_param = bean['region'] if bean['region'] else None
                        st.session_state.df = archive_bean(bean['name'], bean['country'], region_param, st.session_state.df)
                        save_data(st.session_state.df)
                        st.success(f"Archived {bean['name']}")
                        st.rerun()
                    
                    # Smart suggestions
                    if bean['days_since_last'] > 30:
                        st.warning("💡 Not used recently")
                    elif bean['usage_percentage'] >= 90:
                        st.info("⚠️ Almost empty")
    else:
        st.info("No active beans found")
    
    # Archived Beans Section
    st.markdown("---")
    show_archived = st.checkbox(f"📦 Show Archived Beans ({len(archived_beans)})", value=False)
    
    if show_archived and archived_beans:
        st.markdown(f"### 📦 Archived Beans ({len(archived_beans)})")
        
        for bean in archived_beans:
            with st.expander(f"📦 {bean['name']} - {bean['country']} {bean['region']} (Archived)", expanded=False):
                col_info, col_actions = st.columns([3, 1])
                
                with col_info:
                    st.write(f"**Total brews:** {bean['total_brews']}")
                    st.write(f"**Total used:** {bean['total_grams_used']:.0f}g")
                    if bean['avg_rating'] > 0:
                        st.write(f"**Average rating:** {bean['avg_rating']:.1f}/10")
                
                with col_actions:
                    st.write("**Actions**")
                    if st.button(f"🔄 Restore", key=f"restore_{bean['name']}_{bean['country']}_{bean['region']}",
                                help="Restore this bean to active status"):
                        # Convert empty string to None for null regions
                        region_param = bean['region'] if bean['region'] else None
                        st.session_state.df = restore_bean(bean['name'], bean['country'], region_param, st.session_state.df)
                        save_data(st.session_state.df)
                        st.success(f"Restored {bean['name']}")
                        st.rerun()

def render_batch_operations():
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
    bean_stats = get_bean_statistics(st.session_state.df)
    old_beans = [
        bean for bean in bean_stats 
        if bean['archive_status'] != 'archived' and bean['days_since_last'] > days_threshold
    ]
    
    if old_beans:
        st.write(f"**Found {len(old_beans)} beans not used in the last {days_threshold} days:**")
        for bean in old_beans:
            st.write(f"• {bean['name']} - {bean['country']} (last used {bean['days_since_last']} days ago)")
        
        if st.button(f"📦 Archive {len(old_beans)} Old Beans", type="primary"):
            for bean in old_beans:
                # Convert empty string to None for null regions
                region_param = bean['region'] if bean['region'] else None
                st.session_state.df = archive_bean(bean['name'], bean['country'], region_param, st.session_state.df)
            
            save_data(st.session_state.df)
            st.success(f"Archived {len(old_beans)} beans")
            st.rerun()
    else:
        st.info(f"No beans found that haven't been used in the last {days_threshold} days")
    
    # Data insights
    st.markdown("---")
    st.markdown("### 📈 Data Insights")
    
    active_beans = [bean for bean in bean_stats if bean['archive_status'] != 'archived']
    
    if active_beans:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_beans = len(active_beans)
            st.metric("Active Beans", total_beans)
        
        with col2:
            avg_rating = sum(bean['avg_rating'] for bean in active_beans) / len(active_beans)
            st.metric("Average Rating", f"{avg_rating:.1f}/10")
        
        with col3:
            low_stock_beans = len([bean for bean in active_beans if bean['usage_percentage'] >= 75])
            st.metric("Low Stock Beans", low_stock_beans)
        
        # Recent activity
        recent_beans = [bean for bean in active_beans if bean['days_since_last'] <= 7]
        if recent_beans:
            st.write(f"**Recently used beans ({len(recent_beans)}):**")
            for bean in sorted(recent_beans, key=lambda x: x['days_since_last']):
                days_text = "today" if bean['days_since_last'] == 0 else f"{bean['days_since_last']} days ago"
                st.write(f"• {bean['name']} - used {days_text}")

if __name__ == "__main__":
    main()