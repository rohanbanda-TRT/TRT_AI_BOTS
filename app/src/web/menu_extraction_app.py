import streamlit as st
import requests
import json
import os
import uuid
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a file handler
file_handler = logging.FileHandler('menu_extraction_app.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# API URL
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")

def check_api_connection():
    """Check if the API server is running and accessible."""
    try:
        response = requests.get(f"{API_URL}/menu-extraction/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def upload_images(files):
    """Upload images to the API and get their URLs."""
    try:
        # Prepare files for upload
        files_to_upload = [("files", (file.name, file.getvalue(), file.type)) for file in files]
        
        # Log the request
        logger.info(f"Uploading {len(files)} images to {API_URL}/menu-extraction/upload-images")
        
        # Upload images
        response = requests.post(
            f"{API_URL}/menu-extraction/upload-images",
            files=files_to_upload,
            timeout=30
        )
        
        # Log the response
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Upload successful. Response: {json.dumps(result)}")
            return result
        else:
            logger.error(f"Upload failed. Status code: {response.status_code}. Response: {response.text}")
            return {"status": "error", "error": response.text}
    except Exception as e:
        logger.error(f"Error uploading images: {str(e)}")
        return {"status": "error", "error": str(e)}

def process_query(query, image_urls=None, session_id=None):
    """Process a query with the API."""
    try:
        # Prepare request data
        data = {
            "query": query,
            "image_urls": image_urls,
            "session_id": session_id
        }
        
        # Log the request
        logger.info(f"Processing query with API. Payload: {json.dumps(data)}")
        
        # Process query
        response = requests.post(
            f"{API_URL}/menu-extraction/process-query",
            json=data,
            # timeout=120  # Increase timeout to 120 seconds
        )
        
        # Log the response
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Query processing successful. Response=--------------------------------: {result}")
            return result
        else:
            logger.error(f"Query processing failed. Status code: {response.status_code}. Response: {response.text}")
            return {"status": "error", "error": response.text}
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return {"status": "error", "error": "API request timed out"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error processing query: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return {"status": "error", "error": str(e)}

def display_images(image_files):
    """Display uploaded images in a grid layout."""
    if not image_files:
        return
    
    # Calculate number of columns based on number of images
    num_images = len(image_files)
    cols = min(3, num_images)  # Maximum 3 columns
    
    # Create columns
    columns = st.columns(cols)
    
    # Display images in columns
    for i, image_file in enumerate(image_files):
        col_idx = i % cols
        with columns[col_idx]:
            try:
                image = Image.open(image_file)
                st.image(image, caption=f"Menu Image {i+1}", use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying image: {str(e)}")

def main():
    st.set_page_config(page_title="Menu Extraction Assistant", layout="wide")
    
    # App title
    st.title("Menu Extraction Assistant")
    
    # Check API connection
    api_available = check_api_connection()
    
    # Sidebar
    with st.sidebar:
        st.header("About")
        st.write("This app helps you extract and analyze restaurant menu information from images.")
        
        # API connection status
        st.subheader("API Connection")
        connection_status = "Connected" if api_available else "Disconnected"
        st.write(f"Status: {connection_status}")
        
        if st.button("Check API Connection"):
            if check_api_connection():
                st.success("API is available!")
            else:
                st.error("API is not available. Please start the API server.")
                st.code("python -m app.main", language="bash")
    
    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Main content area
    if not api_available:
        st.warning("API server is not available. Please start the API server to use all features.")
    
    # Create tabs
    chat_tab, data_tab, text_tab = st.tabs(["Chat", "Menu Data", "Raw Text"])
    
    with chat_tab:
        # Display chat history
        for message in st.session_state.chat_history:
            if message["is_user"]:
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Upload Menu Images", 
            type=["jpg", "jpeg", "png"], 
            accept_multiple_files=True
        )
        
        # Display uploaded images if any
        if uploaded_files:
            display_images(uploaded_files)
        
        # Query input
        query = st.text_input("Ask a question about the menu:")
        
        # Process button
        if st.button("Send"):
            if query:
                # Add user message to chat history
                st.session_state.chat_history.append({
                    "content": query,
                    "is_user": True
                })
                
                # Process the query
                if uploaded_files:
                    # First upload the images
                    with st.spinner("Uploading images..."):
                        upload_result = upload_images(uploaded_files)
                    
                    if upload_result["status"] == "success":
                        # Get image URLs
                        image_urls = upload_result["image_urls"]
                        session_id = upload_result["session_id"]
                        
                        # Log the image URLs
                        logger.info(f"Received image URLs: {json.dumps(image_urls)}")
                        st.session_state.last_image_urls = image_urls
                        
                        # Process query with image URLs
                        with st.spinner("Processing query..."):
                            result = process_query(query, image_urls, session_id)
                    else:
                        error_msg = f"Error uploading images: {upload_result.get('error', 'Unknown error')}"
                        logger.error(error_msg)
                        st.error(error_msg)
                        result = {"status": "error", "error": upload_result.get("error", "Unknown error")}
                else:
                    # Process query without images
                    with st.spinner("Processing query..."):
                        result = process_query(query, session_id=st.session_state.session_id)
                
                # Process the result
                if result["status"] == "success":
                    # Add response to chat history
                    st.session_state.chat_history.append({
                        "content": result["response"],
                        "is_user": False
                    })
                    
                    # Store menu data and raw text if available
                    if "menu_data" in result:
                        st.session_state.menu_data = result["menu_data"]
                    
                    if "raw_extracted_text" in result:
                        st.session_state.raw_text = result["raw_extracted_text"]
                    
                    # Rerun to update the chat history
                    st.rerun()
                else:
                    error_msg = f"Error: {result.get('error', 'Unknown error')}"
                    logger.error(error_msg)
                    st.error(error_msg)
    
    # Menu Data tab
    with data_tab:
        if "menu_data" in st.session_state and st.session_state.menu_data:
            # Display structured menu data
            st.json(st.session_state.menu_data)
        else:
            st.info("Upload a menu image and ask a question to see structured menu data here.")
    
    # Raw Text tab
    with text_tab:
        if "raw_text" in st.session_state and st.session_state.raw_text:
            for i, text in enumerate(st.session_state.raw_text):
                st.subheader(f"Menu Image {i+1} - Extracted Text")
                st.text_area(f"Raw text from image {i+1}", text, height=300, key=f"raw_text_{i}")
        else:
            st.info("Upload a menu image and ask a question to see extracted raw text here.")

if __name__ == "__main__":
    main()