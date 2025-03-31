import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Medical Bot",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Function to call the API
def get_medical_response(question):
    """Call the FastAPI backend to get a response for the medical question"""
    try:
        response = requests.post(
            "https://trt-demo-ai-bots.demotrt.com/api/medical-bot/consult",
            json={"question": question}
        )
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the JSON response properly
        try:
            # First try to parse as JSON
            result = response.json()
            return result.get("answer", "Error: Unable to parse response")
        except json.JSONDecodeError:
            # If not JSON, return the raw text with quotes stripped
            return response.text.strip('"')
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

# App title and description
st.title("🏥 Medical Bot Assistant")
st.markdown("""
This application provides AI-powered responses to medical questions.
Please note that this is not a substitute for professional medical advice.
""")

# User input
user_question = st.text_area("Enter your medical question:", height=100)

# Submit button
if st.button("Get Answer"):
    if user_question:
        with st.spinner("Getting response..."):
            # Call the API
            response = get_medical_response(user_question)
            
            if response:
                # Display the response
                st.markdown("### Response:")
                
                # Create an expandable container for the response
                with st.container():
                    st.write(response)  # Using st.write instead of st.markdown for better rendering
                
                # Add a disclaimer
                st.markdown("---")
                st.caption("Disclaimer: This information is provided for educational purposes only and is not intended as medical advice. Always consult with a qualified healthcare provider for medical concerns.")
    else:
        st.warning("Please enter a question.")

# Sidebar with information
with st.sidebar:
    st.header("About Medical Bot")
    st.info("""
    Medical Bot uses advanced AI to provide informative responses to medical questions.
    
    The bot has access to a comprehensive knowledge base spanning various medical domains.
    """)
    
    st.header("Instructions")
    st.markdown("""
    1. Type your medical question in the text area
    2. Click the "Get Answer" button
    3. Review the AI-generated response
    """)
    
    st.header("Limitations")
    st.warning("""
    - This bot cannot diagnose conditions
    - It does not have access to your personal medical history
    - Always consult with healthcare professionals for medical advice
    """)
