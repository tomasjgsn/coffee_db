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
        # Run the processing script
        result = subprocess.run([
            sys.executable, 'process_coffee_data.py', 
            str(CSV_FILE), '--selective'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            st.success("✅ Post-processing completed successfully!")
            if result.stdout:
                # Show processing statistics in an expander
                with st.expander("📊 Processing Details"):
                    st.text(result.stdout)
            return True
        else:
            st.error(f"❌ Post-processing failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        st.error("⏱️ Post-processing timed out (>30s)")
        return False
    except FileNotFoundError:
        st.warning("⚠️ process_coffee_data.py not found - skipping post-processing")
        return False
    except Exception as e:
        st.error(f"❌ Post-processing error: {str(e)}")
        return False

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

    # Sidebar for operations
    st.sidebar.header("Operations")
    operation = st.sidebar.radio(
        "Choose operation:",
        ["View brew data", "Add new cup", "Edit cups", "Delete cups"]
    )

    # Display current data
    st.header("Brew performance")
    st.write("Plot the brewing data based on the brewing control chart: https://sca.coffee/sca-news/25/issue-13/towards-a-new-brewing-chart")
    
    x = 'final_tds_percent'
    y = 'final_extraction_yield_percent'
    parameteric_line = ''
    bean_name = 'bean_name'

    chart = alt.Chart(st.session_state.df).mark_circle(size=60).encode(
        x=alt.X('final_extraction_yield_percent', title="Final Extraction Yield [%]",scale=alt.Scale(domain=[10, 30])),
        y=alt.Y('final_tds_percent', title="Total Dissolved Solids, TDS [%]", scale=alt.Scale(domain=[0.5, 1.5])),
        tooltip=[x, y, 'coffee_grams_per_liter', 'bean_name', 'grind_size', 'water_temp_degC', 'brew_date']
    )
    st.altair_chart(chart, use_container_width=True)

    # Display raw data logs
    st.header("Brew logs")
    st.write("Cup data logged")
    st.dataframe(st.session_state.df, use_container_width=True)

    if operation == "View brew data":
        st.info("Select an operation from the sidebar to modify the data.")

    elif operation == "Add new cup":
        st.header("Add new cup")

        with st.form("add_cup_form"):
            # Get next ID
            next_id = st.session_state.df['brew_id'].max() + 1 if not st.session_state.df.empty else 1

            # Create 3-column layout:
            col1, col2, col3 = st.columns(3)

            # ========== COLUMN 1: BEAN & SOURCE INFORMATION ==========
            with col1:
                st.subheader("🌱 Bean & Source Information")
                
                brew_id = st.number_input("Brew ID", value=next_id, disabled=True)
                brew_date = st.date_input("Brew Date", value=date.today())
                bean_name = st.text_input("Bean Name", placeholder="e.g., La Providencia")
                bean_origin_country = st.text_input("Origin Country", placeholder="e.g., Colombia")
                bean_origin_region = st.text_input("Origin Region", placeholder="e.g., Huila")
                bean_variety = st.text_input("Bean Variety", placeholder="e.g., Cenicafe 1")
                
                bean_process_method = st.selectbox("Process Method", 
                    ["", "Washed", "Natural", "Honey", "Semi-Washed", "Anaerobic", "Other"])
                
                bean_harvest_date = st.date_input("Harvest Date", value=None, help="Leave empty if unknown")
                bean_purchase_date = st.date_input("Purchase Date", value=None)
                
                bean_roast_level = st.selectbox("Roast Level", 
                    ["", "Light", "Light-Medium", "Medium", "Medium-Dark", "Dark"])
                
                bean_notes = st.text_area("Bean Notes", placeholder="Tasting notes, descriptions...")

            # ========== COLUMN 2: BREWING PROCESS & EQUIPMENT ==========
            with col2:
                st.subheader("⚙️ Brewing Process & Equipment")
                
                grind_size = st.number_input("Grind Size", min_value=1, max_value=40, value=None)
                grind_model = st.text_input("Grind Model", placeholder="e.g., Fellow Ode Gen 2")
                
                brew_method = st.selectbox("Brew Method", 
                    ["", "V60", "Chemex", "Aeropress", "French Press", "Espresso", "Hoffman top up", "Other"])
                
                brew_device = st.text_input("Brew Device", placeholder="e.g., V60 ceramic")
                kettle_type = st.text_input("Kettle Type", placeholder="e.g., Gooseneck electric")
                scale_model = st.text_input("Scale Model", placeholder="e.g., Hario V60")
                water_source = st.text_input("Water Source", placeholder="e.g., Filtered tap")
                
                coffee_dose_grams = st.number_input("Coffee Dose (g)", min_value=0.0, value=None, step=0.1)
                water_volume_ml = st.number_input("Water Volume (ml)", min_value=0, value=None)
                water_temp_degC = st.number_input("Water Temperature (°C)", min_value=70, max_value=100, value=None)
                
                brew_bloom_time_s = st.number_input("Bloom Time (seconds)", min_value=0, value=None)
                brew_total_time_s = st.number_input("Total Brew Time (seconds)", min_value=0, value=None)
                
                agitation_method = st.selectbox("Agitation Method", 
                    ["", "None", "Stir", "Swirl", "Shake", "Gentle stir"])
                
                pour_technique = st.selectbox("Pour Technique", 
                    ["", "Spiral", "Center pour", "Concentric circles", "Pulse pour", "Continuous"])

            # ========== COLUMN 3: RESULTS & SCORING ==========
            with col3:
                st.subheader("📊 Results & Scoring")
                
                final_tds_percent = st.number_input("TDS %", min_value=0.0, max_value=5.0, value=None, step=0.01)
                final_brew_mass_grams = st.number_input("Final Brew Mass (g)", min_value=0, value=None)
                
                score_overall_rating = st.slider("Overall Rating", min_value=1.0, max_value=10.0, value=5.0, step=0.1)
                score_notes = st.text_area("Score Notes", placeholder="Detailed tasting notes...")
                
                score_flavor_profile_category = st.selectbox("Flavor Profile", 
                    ["", "Bright/Acidic", "Balanced", "Rich/Full", "Sweet", "Bitter", "Fruity", "Nutty", "Chocolatey"])

            # Submit button spanning all columns
            st.markdown("---")
            submitted = st.form_submit_button("☕ Add Cup Record", use_container_width=True)
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
                # Collect only input fields (no calculated or metadata fields)
                new_record = {
                    'brew_id': brew_id,
                    'brew_date': brew_date,
                    'bean_name': bean_name if bean_name else None,
                    'bean_origin_country': bean_origin_country if bean_origin_country else None,
                    'bean_origin_region': bean_origin_region if bean_origin_region else None,
                    'bean_variety': bean_variety if bean_variety else None,
                    'bean_process_method': bean_process_method if bean_process_method else None,
                    'bean_harvest_date': bean_harvest_date,
                    'bean_purchase_date': bean_purchase_date,
                    'bean_roast_level': bean_roast_level if bean_roast_level else None,
                    'bean_notes': bean_notes if bean_notes else None,
                    'grind_size': grind_size,
                    'grind_model': grind_model if grind_model else None,
                    'brew_method': brew_method if brew_method else None,
                    'brew_device': brew_device if brew_device else None,
                    'kettle_type': kettle_type if kettle_type else None,
                    'scale_model': scale_model if scale_model else None,
                    'water_source': water_source if water_source else None,
                    'coffee_dose_grams': coffee_dose_grams,
                    'water_volume_ml': water_volume_ml,
                    'water_temp_degC': water_temp_degC,
                    'brew_bloom_time_s': brew_bloom_time_s,
                    'brew_total_time_s': brew_total_time_s,
                    'agitation_method': agitation_method if agitation_method else None,
                    'pour_technique': pour_technique if pour_technique else None,
                    'final_tds_percent': final_tds_percent,
                    'final_brew_mass_grams': final_brew_mass_grams,
                    'score_overall_rating': score_overall_rating,
                    'score_notes': score_notes if score_notes else None,
                    'score_flavor_profile_category': score_flavor_profile_category if score_flavor_profile_category else None
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
                if run_post_processing():
                    # Reload the data to get the calculated fields
                    st.session_state.df = load_data()
                    st.success("✅ New cup added and processed successfully!")
                else:
                    st.warning("⚠️ Cup added but post-processing failed. Some calculated fields may be missing.")
                
                st.rerun()

    elif operation == "Edit cups":
        st.header("Edit Cup Record")
        
        if not st.session_state.df.empty:
            # Select cup to edit
            cup_options = [f"{row['brew_id']} - {row['bean_name']} ({row['brew_date']})" for _, row in st.session_state.df.iterrows()]
            selected_cup = st.selectbox("Select cup to edit:", cup_options)
            
            if selected_cup:
                selected_id = int(selected_cup.split(' - ')[0])
                cup_data = st.session_state.df[st.session_state.df['brew_id'] == selected_id].iloc[0]
                
                st.info("Edit functionality can be implemented here using similar form structure")
        else:
            st.info("No records available to edit")

    elif operation == "Delete cups":
        st.header("Delete Cup Record")
        
        if not st.session_state.df.empty:
            cup_options = [f"{row['brew_id']} - {row['bean_name']} ({row['brew_date']})" for _, row in st.session_state.df.iterrows()]
            selected_cup = st.selectbox("Select cup to delete:", cup_options)
            
            if selected_cup:
                selected_id = int(selected_cup.split(' - ')[0])
                cup_data = st.session_state.df[st.session_state.df['brew_id'] == selected_id].iloc[0]
                
                # Show cup details
                st.write("**Cup to delete:**")
                st.write(f"- **Bean:** {cup_data['bean_name']}")
                st.write(f"- **Date:** {cup_data['brew_date']}")
                st.write(f"- **Method:** {cup_data['brew_method']}")
                
                with st.form("delete_cup_form"):
                    st.warning("Are you sure you want to delete this cup record? This action cannot be undone.")
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        confirmed = st.form_submit_button("🗑️ Delete", type="primary")
                    with col2:
                        st.form_submit_button("Cancel", disabled=True)
                    
                    if confirmed:
                        # Remove from DataFrame
                        st.session_state.df = st.session_state.df[st.session_state.df['brew_id'] != selected_id].reset_index(drop=True)
                        
                        # Save to CSV
                        save_data(st.session_state.df)
                        st.rerun()
        else:
            st.info("No records available to delete")

if __name__ == "__main__":
    main()