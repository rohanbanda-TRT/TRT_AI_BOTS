"""
Streamlit application for the Menu Extraction Agent.
"""
import os
import sys
import requests
import json
import uuid
import streamlit as st
from dotenv import load_dotenv

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

from app.src.core.config import get_settings

# Load environment variables
load_dotenv()

# API endpoint
API_URL = "http://127.0.0.1:8000"

# Set page config
st.set_page_config(
    page_title="Menu Extraction",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def initialize_session_state():
    """Initialize session state variables"""
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "menu_data" not in st.session_state:
        st.session_state.menu_data = None
    if "extracted_text" not in st.session_state:
        st.session_state.extracted_text = None
    if "uploaded_images" not in st.session_state:
        st.session_state.uploaded_images = []

# Function to check API connection
def check_api_connection():
    """Check if the API is available"""
    try:
        response = requests.get(f"{API_URL}/api/menu-extraction/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# Function to send a chat message
def send_chat_message(message):
    """Send a chat message to the API"""
    try:
        response = requests.post(
            f"{API_URL}/api/menu-extraction/chat",
            json={
                "message": message,
                "conversation_id": st.session_state.conversation_id
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {str(e)}")
        return {"answer": "Sorry, I couldn't connect to the API. Please try again later."}

# Function to analyze menu images
def analyze_menu_images(image_files, message=None):
    """Send menu images to the API for analysis"""
    try:
        # Prepare files for upload
        files = []
        for i, img in enumerate(image_files):
            files.append(("menu_images", (img.name, img.getvalue(), img.type)))
        
        data = {"conversation_id": st.session_state.conversation_id}
        
        # Add message if provided
        if message:
            data["message"] = message
        
        response = requests.post(
            f"{API_URL}/api/menu-extraction/analyze-menu-images",
            files=files,
            data=data,
            timeout=60  # Longer timeout for multiple image processing
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {str(e)}")
        return {
            "answer": "Sorry, I couldn't analyze the menu images. Please try again later.",
            "menu_data": None,
            "extracted_text": None
        }

def main():
    # Initialize session state
    initialize_session_state()
    
    # Title
    st.title("🍽️ Menu Extraction Assistant")
    st.write("Upload menu images for analysis or chat about menu items.")
    
    # Sidebar
    with st.sidebar:
        st.header("About Menu Extraction")
        st.info("""
        This tool helps you extract and understand menu items from restaurant menus.
        
        Upload images of a menu to extract:
        - Menu items and prices
        - Descriptions and categories
        - Dietary information
        
        You can also chat about the extracted menu data or ask general questions.
        """)
        
        st.header("Instructions")
        st.markdown("""
        1. Upload menu images using the upload button in the chat input
        2. Type your message or question (optional)
        3. View the extracted menu data in the right panel
        4. Continue the conversation by asking questions about the menu
        """)
        
        # Check API connection
        if st.button("Check API Connection"):
            if check_api_connection():
                st.success("✅ API connection successful!")
            else:
                st.error("❌ API connection failed. Please make sure the API server is running.")
        
        # Reset conversation
        if st.button("Reset Conversation"):
            st.session_state.conversation_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.menu_data = None
            st.session_state.extracted_text = None
            st.session_state.uploaded_images = []
            st.success("Conversation reset!")
    
    # Main content - two columns
    col1, col2 = st.columns([3, 2])
    
    # Chat column
    with col1:
        st.header("Chat")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                # Display text content
                st.markdown(message["content"])
                
                # Display images if any
                if "images" in message and message["images"]:
                    # Create a grid for images
                    num_images = len(message["images"])
                    if num_images > 0:
                        image_cols = st.columns(min(3, num_images))
                        for i, img in enumerate(message["images"]):
                            with image_cols[i % min(3, num_images)]:
                                st.image(img, caption=f"Image {i+1}", use_container_width=True)
        
        # Chat input with file uploader
        chat_container = st.container()
        with chat_container:
            # Create a form for chat input and file upload
            with st.form(key="chat_form", clear_on_submit=True):
                # Create columns for text input and file upload
                col_input, col_upload = st.columns([6, 1])
                
                with col_input:
                    user_input = st.text_input(
                        "Type your message here...",
                        key="chat_input",
                        placeholder="Ask about menu items or upload a menu image..."
                    )
                
                with col_upload:
                    uploaded_files = st.file_uploader(
                        "Upload menu images",
                        type=["jpg", "jpeg", "png"],
                        accept_multiple_files=True,
                        key="file_uploader",
                        label_visibility="collapsed"
                    )
                
                # Submit button
                submit_button = st.form_submit_button(label="Send", use_container_width=True)
                
                if submit_button:
                    # Process the input
                    if uploaded_files or user_input:
                        # Add user message to chat
                        user_message = user_input if user_input else "I'm uploading menu images for analysis."
                        
                        # Create message object with text and images
                        user_msg_obj = {
                            "role": "user",
                            "content": user_message,
                            "images": uploaded_files if uploaded_files else []
                        }
                        
                        # Add to session state
                        st.session_state.messages.append(user_msg_obj)
                        
                        # Display user message
                        with st.chat_message("user"):
                            st.markdown(user_message)
                            
                            # Display uploaded images if any
                            if uploaded_files:
                                num_images = len(uploaded_files)
                                if num_images > 0:
                                    st.write(f"Uploaded {num_images} image(s):")
                                    image_cols = st.columns(min(3, num_images))
                                    for i, img in enumerate(uploaded_files):
                                        with image_cols[i % min(3, num_images)]:
                                            st.image(img, caption=f"Image {i+1}", use_container_width=True)
                        
                        # Process the request
                        with st.spinner("Processing..."):
                            if uploaded_files:
                                # Analyze images
                                result = analyze_menu_images(uploaded_files, user_input)
                                
                                # Store menu data and extracted text in session state
                                if result.get("menu_data"):
                                    st.session_state.menu_data = result["menu_data"]
                                    st.session_state.extracted_text = result.get("extracted_text", "")
                                
                                # Add AI response to chat
                                with st.chat_message("assistant"):
                                    st.markdown(result["answer"])
                                
                                # Add to session state
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": result["answer"],
                                    "images": []
                                })
                            else:
                                # Just text chat
                                response = send_chat_message(user_input)
                                
                                # Add AI response to chat
                                with st.chat_message("assistant"):
                                    st.markdown(response["answer"])
                                
                                # Add to session state
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": response["answer"],
                                    "images": []
                                })
    
    # Menu data column
    with col2:
        # Tabs for Menu Data and Raw Text
        tab1, tab2 = st.tabs(["Extracted Menu", "Raw Text"])
        
        # Menu Data Tab
        with tab1:
            st.header("Extracted Menu Data")
            
            if st.session_state.menu_data:
                # Display restaurant name if available
                if "restaurant_name" in st.session_state.menu_data and st.session_state.menu_data["restaurant_name"]:
                    st.subheader(st.session_state.menu_data["restaurant_name"])
                
                # Display menu categories and items
                if "menu_categories" in st.session_state.menu_data:
                    for category in st.session_state.menu_data["menu_categories"]:
                        with st.expander(category["category_name"], expanded=True):
                            for item in category["items"]:
                                col_a, col_b = st.columns([3, 1])
                                with col_a:
                                    # Item name with dietary info if available
                                    item_name = item["name"]
                                    if "dietary_info" in item and item["dietary_info"]:
                                        dietary_badges = " ".join([f"[{info}]" for info in item["dietary_info"]])
                                        st.markdown(f"**{item_name}** {dietary_badges}")
                                    else:
                                        st.markdown(f"**{item_name}**")
                                    
                                    # Description if available
                                    if "description" in item and item["description"]:
                                        st.markdown(f"*{item['description']}*")
                                
                                with col_b:
                                    # Price
                                    if "price" in item and item["price"]:
                                        st.markdown(f"**{item['price']}**")
                                
                                st.divider()
                
                # Option to view raw JSON
                with st.expander("View Raw JSON"):
                    st.json(st.session_state.menu_data)
            else:
                st.info("No menu data available. Upload menu images and ask a question to extract data.")
        
        # Raw Text Tab
        with tab2:
            st.header("Extracted Raw Text")
            if st.session_state.extracted_text:
                st.text_area("Raw text extracted from images:", st.session_state.extracted_text, height=400)
            else:
                st.info("No extracted text available. Upload menu images and ask a question to extract text.")

if __name__ == "__main__":
    main()
