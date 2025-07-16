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
    nitrogen = st.number_input("Nitrogen (mg/kg)", min_value=0.0, max_value=500.0, value=90.0, step=0.1)
    phosphorus = st.number_input("Phosphorus (mg/kg)", min_value=0.0, max_value=300.0, value=40.0, step=0.1)
    potassium = st.number_input("Potassium (mg/kg)", min_value=0.0, max_value=600.0, value=150.0, step=0.1)
    organic_matter = st.number_input("Organic Matter (%)", min_value=0.0, max_value=20.0, value=2.5, step=0.1)
    moisture = st.number_input("Moisture (%)", min_value=0.0, max_value=100.0, value=30.0, step=0.1)
    temperature = st.number_input("Temperature (°C)", min_value=-20.0, max_value=60.0, value=25.0, step=0.1)
    crop_name = st.text_input("Crop Name", value="wheat")
    submitted = st.form_submit_button("Analyze Soil")

if submitted:
    with st.spinner("Analyzing soil suitability..."):
        api_key = os.environ.get("OPENAI_API_KEY")
        analyzer = SoilSuitabilityAnalyzer(openai_api_key=api_key)
        soil_data = {
            "ph": ph,
            "nitrogen": nitrogen,
            "phosphorus": phosphorus,
            "potassium": potassium,
            "organic_matter": organic_matter,
            "moisture": moisture,
            "temperature": temperature
        }
        result = analyzer.analyze(soil_data, crop_name)
        st.markdown(result["summary"])
