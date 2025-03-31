import streamlit as st
import requests
import json
import time
from PIL import Image
import io
import base64
from typing import Dict, Any, Optional

# API configuration
API_URL = "https://trt-demo-ai-bots.demotrt.com"
TIMEOUT = 10  # seconds

def check_api_connection() -> bool:
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_URL}/api/interior-design/health", timeout=TIMEOUT)
        return response.status_code == 200
    except:
        return False

def generate_design_image(room_type: str, style: str, requirements: str) -> Dict[str, Any]:
    """Generate an interior design image."""
    try:
        response = requests.post(
            f"{API_URL}/api/interior-design/generate-image",
            json={
                "room_type": room_type,
                "style": style,
                "requirements": requirements
            },
            timeout=60  # Longer timeout for image generation
        )
        return response.json()
    except Exception as e:
        st.error(f"Error generating design image: {str(e)}")
        return {"status": "error", "error": str(e)}

def modify_design_image(image_url: str, modifications: str) -> Dict[str, Any]:
    """Modify an interior design image."""
    try:
        response = requests.post(
            f"{API_URL}/api/interior-design/modify-image",
            json={
                "image_url": image_url,
                "modifications": modifications
            },
            timeout=60  # Longer timeout for image modification
        )
        return response.json()
    except Exception as e:
        st.error(f"Error modifying design image: {str(e)}")
        return {"status": "error", "error": str(e)}

def estimate_cost(image_url: str, room_type: str, style: str, requirements: str) -> Dict[str, Any]:
    """Estimate the cost of implementing a design."""
    try:
        response = requests.post(
            f"{API_URL}/api/interior-design/estimate-cost",
            json={
                "image_url": image_url,
                "room_type": room_type,
                "style": style,
                "requirements": requirements
            },
            timeout=60  # Longer timeout for cost estimation
        )
        return response.json()
    except Exception as e:
        st.error(f"Error estimating cost: {str(e)}")
        return {"status": "error", "error": str(e)}

def main():
    st.set_page_config(
        page_title="Interior Design Assistant",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better UI
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2563EB;
        margin-bottom: 1rem;
    }
    .info-text {
        font-size: 1rem;
        color: #4B5563;
    }
    .highlight {
        background-color: #DBEAFE;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stButton > button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar for API connection status
    with st.sidebar:
        st.title("Interior Design Assistant")
        st.markdown("---")
        
        # API connection status
        st.subheader("API Connection")
        api_status = check_api_connection()
        
        if api_status:
            st.success("✅ Connected to API")
        else:
            st.error("❌ Not connected to API")
            st.info("Please start the API server using the command:\n```\npython -m app.main\n```")
            
            if st.button("Check API Connection"):
                if check_api_connection():
                    st.success("✅ Connected to API")
                    st.rerun()
                else:
                    st.error("❌ Still not connected to API")
        
        st.markdown("---")
        st.markdown("### About")
        st.info(
            "This app helps you design rooms with AI. "
            "Generate interior design images, modify them, "
            "and get cost estimates for implementation."
        )
    
    # Main content
    st.markdown('<h1 class="main-header">Interior Design Assistant</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="info-text">Generate beautiful interior designs with AI, modify them to your liking, and get cost estimates for implementation.</p>',
        unsafe_allow_html=True
    )
    
    # Initialize session state
    if "design_image_url" not in st.session_state:
        st.session_state.design_image_url = None
    if "room_type" not in st.session_state:
        st.session_state.room_type = ""
    if "style" not in st.session_state:
        st.session_state.style = ""
    if "requirements" not in st.session_state:
        st.session_state.requirements = ""
    if "cost_estimate" not in st.session_state:
        st.session_state.cost_estimate = None
    
    # Main workflow
    if st.session_state.design_image_url is None:
        # Step 1: Generate Design Image
        st.markdown('<h2 class="sub-header">Step 1: Generate Interior Design Image</h2>', unsafe_allow_html=True)
        
        with st.form("design_form"):
            room_type = st.selectbox(
                "Room Type",
                options=["Living Room", "Bedroom", "Kitchen", "Bathroom", "Home Office", "Dining Room", "Outdoor Space"]
            )
            
            style = st.selectbox(
                "Design Style",
                options=["Modern", "Contemporary", "Minimalist", "Traditional", "Industrial", "Scandinavian", "Bohemian", "Mid-Century Modern", "Rustic", "Coastal"]
            )
            
            requirements = st.text_area(
                "Specific Requirements",
                placeholder="Describe your requirements, e.g., 'I need a space for a home theater setup, with comfortable seating for 5 people, and storage for books.'"
            )
            
            generate_button = st.form_submit_button("Generate Design Image")
        
        if generate_button and api_status:
            with st.spinner("Generating interior design image..."):
                result = generate_design_image(room_type, style, requirements)
                
                if result["status"] == "success":
                    st.session_state.design_image_url = result["image_url"]
                    st.session_state.room_type = room_type
                    st.session_state.style = style
                    st.session_state.requirements = requirements
                    st.rerun()
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
        elif generate_button and not api_status:
            st.error("Cannot generate design: API not connected")
    
    else:
        # Display the current design image
        st.markdown('<h2 class="sub-header">Your Interior Design</h2>', unsafe_allow_html=True)
        st.image(st.session_state.design_image_url, caption="Interior Design", use_container_width=True)
        
        # Step 2: Modify Design Image
        st.markdown('<h2 class="sub-header">Step 2: Modify Design (Optional)</h2>', unsafe_allow_html=True)
        
        with st.expander("Make modifications to your design", expanded=True):
            modifications = st.text_area(
                "Describe the modifications you want to make",
                placeholder="E.g., 'Change the wall color to blue, add more plants, replace the sofa with a sectional'"
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Apply Modifications") and api_status:
                    with st.spinner("Applying modifications..."):
                        result = modify_design_image(st.session_state.design_image_url, modifications)
                        
                        if result["status"] == "success":
                            st.session_state.design_image_url = result["image_url"]
                            st.rerun()
                        else:
                            st.error(f"Error: {result.get('error', 'Unknown error')}")
            with col2:
                if st.button("Start Over"):
                    st.session_state.design_image_url = None
                    st.session_state.cost_estimate = None
                    st.rerun()
        
        # Step 3: Cost Estimation
        st.markdown('<h2 class="sub-header">Step 3: Get Cost Estimate</h2>', unsafe_allow_html=True)
        
        if st.session_state.cost_estimate is None:
            if st.button("Generate Cost Estimate") and api_status:
                with st.spinner("Estimating cost..."):
                    result = estimate_cost(
                        st.session_state.design_image_url,
                        st.session_state.room_type,
                        st.session_state.style,
                        st.session_state.requirements
                    )
                    
                    if result["status"] == "success":
                        st.session_state.cost_estimate = result["cost_estimate"]
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error')}")
        else:
            # Display cost estimate
            st.markdown('<div class="highlight">', unsafe_allow_html=True)
            st.markdown("### Cost Breakdown")
            st.markdown(st.session_state.cost_estimate)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Save and share options
            st.markdown("### Save or Share Your Design")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Design"):
                    st.success("Design saved successfully! (Demo only)")
            with col2:
                if st.button("Share Design"):
                    st.success("Design shared successfully! (Demo only)")

if __name__ == "__main__":
    main()
