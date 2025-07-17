import streamlit as st
import os
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from app.src.agents.soil_logic import SoilSuitabilityAnalyzer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Soil Crop Suitability Analyzer", layout="centered")
st.title("🌱 Soil Crop Suitability Analyzer")

# Sidebar for API key
if not os.environ.get("OPENAI_API_KEY"):
    st.sidebar.warning("Please set your OPENAI_API_KEY in your environment or .env file.")

# Soil parameter inputs
st.header("Enter Soil Parameters")
with st.form("soil_form"):
    ph = st.number_input("pH", min_value=0.0, max_value=14.0, value=6.5, step=0.1)
    organic_matter = st.number_input("Organic Matter (%)", min_value=0.0, max_value=20.0, value=2.5, step=0.1)
    nitrogen = st.number_input("Nitrogen (mg/kg)", min_value=0.0, max_value=500.0, value=90.0, step=0.1)
    phosphorus = st.number_input("Phosphorus (mg/kg)", min_value=0.0, max_value=300.0, value=40.0, step=0.1)
    potassium = st.number_input("Potassium (mg/kg)", min_value=0.0, max_value=600.0, value=150.0, step=0.1)
    sand = st.number_input("Sand (%)", min_value=0.0, max_value=100.0, value=40.0, step=0.1)
    silt = st.number_input("Silt (%)", min_value=0.0, max_value=100.0, value=40.0, step=0.1)
    clay = st.number_input("Clay (%)", min_value=0.0, max_value=100.0, value=20.0, step=0.1)
    electrical_conductivity = st.number_input("Electrical Conductivity (dS/m)", min_value=0.0, max_value=10.0, value=0.5, step=0.01)
    moisture = st.number_input("Moisture (%)", min_value=0.0, max_value=100.0, value=30.0, step=0.1)
    temperature = st.number_input("Temperature (°C)", min_value=-20.0, max_value=60.0, value=25.0, step=0.1)
    crop_name = st.text_input("Crop Name", value="wheat")

    st.markdown("---")
    st.subheader("Add Custom Parameters")
    if 'custom_param_count' not in st.session_state:
        st.session_state['custom_param_count'] = 0
    if 'custom_param_names' not in st.session_state:
        st.session_state['custom_param_names'] = {}
    if 'custom_param_values' not in st.session_state:
        st.session_state['custom_param_values'] = {}
    submitted = st.form_submit_button("Analyze Soil")

# Add custom parameter button outside the form
if st.button("+ Add Parameter", key="add_param_button"):
    if 'custom_param_count' not in st.session_state:
        st.session_state['custom_param_count'] = 0
    st.session_state['custom_param_count'] += 1

# After the form: show all custom params as editable rows with delete buttons
if 'custom_param_count' in st.session_state and st.session_state['custom_param_count'] > 0:
    st.markdown("#### Custom Parameters")
    to_delete = []
    for i in range(st.session_state['custom_param_count']):
        col1, col2, col3 = st.columns([2,1,0.3])
        st.session_state['custom_param_names'][i] = col1.text_input(f"Parameter Name {i+1}", key=f"custom_param_name_{i}", value=st.session_state['custom_param_names'].get(i, ""))
        st.session_state['custom_param_values'][i] = col2.number_input(f"Value", key=f"custom_param_value_{i}", value=st.session_state['custom_param_values'].get(i, 0.0))
        if col3.button("❌", key=f"delete_param_{i}"):
            to_delete.append(i)
    # Actually delete after iterating
    for i in to_delete:
        del st.session_state['custom_param_names'][i]
        del st.session_state['custom_param_values'][i]
        st.session_state['custom_param_count'] -= 1
        st.rerun()

# Gather custom parameters from session_state
custom_params = []
if 'custom_param_count' in st.session_state and st.session_state['custom_param_count'] > 0:
    for i in range(st.session_state['custom_param_count']):
        name = st.session_state['custom_param_names'].get(i, "")
        value = st.session_state['custom_param_values'].get(i, 0.0)
        if name:
            custom_params.append((name, value))

if submitted:
    with st.spinner("Analyzing soil suitability..."):
        api_key = os.environ.get("OPENAI_API_KEY")
        analyzer = SoilSuitabilityAnalyzer(openai_api_key=api_key)
        soil_data = {
            "ph": ph,
            "organic_matter": organic_matter,
            "nitrogen": nitrogen,
            "phosphorus": phosphorus,
            "potassium": potassium,
            "sand": sand,
            "silt": silt,
            "clay": clay,
            "electrical_conductivity": electrical_conductivity,
            "moisture": moisture,
            "temperature": temperature
        }
        # Add custom parameters
        for name, value in custom_params:
            soil_data[name] = value
        result = analyzer.analyze(soil_data, crop_name)
        st.markdown(result["summary"])
