import os
import time
import streamlit as st
import requests
from typing import Dict, Any, Optional
import tempfile
import json

# Configure Streamlit page
st.set_page_config(
    page_title="Video Transcription & Q&A",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE_URL = "http://localhost:8000/api"  # Update with your API URL
ALLOWED_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_available" not in st.session_state:
    st.session_state.api_available = False

# Helper functions
def check_api_connection():
    """Check if the API is available"""
    try:
        response = requests.get(f"{API_BASE_URL}/video-transcription/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def upload_video(file) -> Dict[str, Any]:
    """Upload a video file to the API"""
    try:
        files = {"file": (file.name, file.getvalue(), "video/mp4")}
        response = requests.post(
            f"{API_BASE_URL}/video-transcription/upload",
            files=files,
            timeout=300  # 5 minutes timeout for large videos
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error uploading video: {str(e)}")
        return {"status": "error", "error": str(e)}

def query_video(question: str) -> Dict[str, Any]:
    """Query the video transcription with a question"""
    try:
        payload = {"question": question}
        response = requests.post(
            f"{API_BASE_URL}/video-transcription/query",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error querying video: {str(e)}")
        return {"answer": f"Error: {str(e)}"}

# Sidebar
with st.sidebar:
    st.title("🎬 Video Transcription")
    
    # API Connection
    st.header("API Connection")
    if st.button("Check API Connection"):
        with st.spinner("Checking API connection..."):
            st.session_state.api_available = check_api_connection()
    
    if st.session_state.api_available:
        st.success("✅ Connected to API")
    else:
        st.error("❌ API not available")
        st.info("Please make sure the API server is running at " + API_BASE_URL)
    
    # Conversation
    st.header("Conversation")
    if st.button("New Conversation"):
        st.session_state.messages = []
        st.rerun()
    
    # About
    with st.expander("About Video Transcription"):
        st.markdown("""
        This app allows you to:
        1. Upload video files
        2. Process videos to extract transcriptions
        3. Ask questions about the video content
        4. Get AI-generated answers based on the video transcription
        
        The system uses:
        - Whisper for transcription
        - Vector search for finding relevant content
        - LLMs for generating answers
        
        **Note**: Videos are processed in memory and not stored on disk.
        Only the transcription data is stored in the vector database.
        """)

# Main content
st.title("🎬 Video Transcription & Q&A")

# Create tabs
tab1, tab2 = st.tabs(["Upload", "Chat"])

# Upload tab
with tab1:
    st.header("Upload Video")
    
    if not st.session_state.api_available:
        st.warning("API not available. Please check the connection.")
    else:
        uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"])
        
        if uploaded_file is not None:
            # Check file extension
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                st.error(f"Unsupported file format. Please upload one of: {', '.join(ALLOWED_EXTENSIONS)}")
            else:
                # Show video preview
                st.video(uploaded_file)
                
                # Upload button
                if st.button("Process Video"):
                    with st.spinner("Uploading and processing video... This may take a few minutes for large videos."):
                        result = upload_video(uploaded_file)
                        
                        if result.get("status") == "success":
                            st.success("Video processed successfully!")
                            
                            # Show processing details in an expander
                            with st.expander("Processing Details"):
                                st.json(result)
                            
                            # Switch to chat tab
                            st.info("You can now ask questions about the video in the Chat tab.")
                        else:
                            st.error(f"Error processing video: {result.get('error', 'Unknown error')}")

# Chat tab
with tab2:
    st.header("Video Q&A")
    
    if not st.session_state.api_available:
        st.warning("API not available. Please check the connection.")
    else:
        # Create containers for chat messages and input
        chat_container = st.container()
        input_container = st.container()
        
        # Input container at the bottom
        with input_container:
            prompt = st.chat_input("Ask a question about the video...")
            if prompt:
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Get AI response
                with st.spinner("Thinking..."):
                    response = query_video(prompt)
                    answer = response.get("answer", "Sorry, I couldn't process your question.")
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Rerun to update the chat history display
                st.rerun()
        
        # Display chat messages from session state (above the input)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
