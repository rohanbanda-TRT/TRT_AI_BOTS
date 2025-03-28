"""
Streamlit application for the Answer Verifier.
"""
import os
import sys
import requests

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
    page_title="Answer Verifier",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables"""
    if "pdf_uploaded" not in st.session_state:
        st.session_state.pdf_uploaded = False
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "Text Answer"

# Function to upload PDFs
def upload_pdfs(files):
    if not files:
        return {"success": False, "message": "No files selected"}
    
    # Prepare the files for upload
    files_data = [("files", (file.name, file.getvalue(), "application/pdf")) for file in files]
    
    # Send the files to the API
    response = requests.post(f"{API_URL}/upload-pdfs", files=files_data)
    
    if response.status_code == 200:
        return {"success": True, "message": response.json()["message"]}
    else:
        return {"success": False, "message": f"Error: {response.text}"}

# Function to verify an answer
def verify_answer(question, student_answer):
    # Prepare the data
    data = {
        "question": question,
        "student_answer": student_answer
    }
    
    # Send the data to the API
    response = requests.post(f"{API_URL}/verify-answer", json=data)
    
    if response.status_code == 200:
        return {"success": True, "result": response.json()}
    else:
        return {"success": False, "message": f"Error: {response.text}"}

# Function to verify an answer from an image
def verify_answer_from_image(question, image_file):
    if not image_file:
        return {"success": False, "message": "No image selected"}
    
    # Prepare the data
    files = {"answer_image": (image_file.name, image_file.getvalue(), image_file.type)}
    data = {"question": question}
    
    # Send the data to the API
    response = requests.post(f"{API_URL}/verify-answer-from-image", files=files, data=data)
    
    if response.status_code == 200:
        return {"success": True, "result": response.json()}
    else:
        return {"success": False, "message": f"Error: {response.text}"}

# Function to clear the vector store
def clear_vector_store():
    response = requests.post(f"{API_URL}/clear-vector-store")
    
    if response.status_code == 200:
        return {"success": True, "message": response.json()["message"]}
    else:
        return {"success": False, "message": f"Error: {response.text}"}

def main():
    # Initialize session state
    initialize_session_state()
    
    # Title
    st.title("📚 Answer Verifier")
    st.write("Upload reference PDFs and verify student answers against them.")
    
    # Sidebar
    st.sidebar.title("Options")
    
    # PDF Upload Section
    st.sidebar.header("Upload Reference PDFs")
    pdf_files = st.sidebar.file_uploader("Select PDF files", type=["pdf"], accept_multiple_files=True)
    
    if st.sidebar.button("Process PDFs"):
        with st.sidebar:
            with st.spinner("Processing PDFs..."):
                result = upload_pdfs(pdf_files)
                if result["success"]:
                    st.success(result["message"])
                    st.session_state.pdf_uploaded = True
                else:
                    st.error(result["message"])
    
    # Clear Vector Store
    if st.sidebar.button("Clear Reference Materials"):
        with st.sidebar:
            with st.spinner("Clearing reference materials..."):
                result = clear_vector_store()
                if result["success"]:
                    st.success(result["message"])
                    st.session_state.pdf_uploaded = False
                else:
                    st.error(result["message"])
    
    # Main content
    tab1, tab2 = st.tabs(["Text Answer Verification", "Image Answer Verification"])
    
    # Text Answer Verification Tab
    with tab1:
        st.header("Verify Text Answer")
        
        # Question input
        question = st.text_area("Question", height=100, placeholder="Enter the question here...")
        
        # Student answer input
        student_answer = st.text_area("Student Answer", height=200, placeholder="Enter the student's answer here...")
        
        # Verify button
        if st.button("Verify Answer", key="verify_text"):
            if not question:
                st.error("Please enter a question.")
            elif not student_answer:
                st.error("Please enter the student's answer.")
            elif not st.session_state.pdf_uploaded:
                st.warning("Please upload reference PDF documents first.")
            else:
                with st.spinner("Verifying answer..."):
                    result = verify_answer(question, student_answer)
                    
                    if result["success"]:
                        verification = result["result"]["verification"]
                        score = result["result"]["score"]
                        
                        # Display the score with color coding
                        score_color = "red" if score < 4 else "orange" if score < 7 else "green"
                        st.markdown(f"<h3 style='color: {score_color}'>Score: {score}/10</h3>", unsafe_allow_html=True)
                        
                        # Display the verification result
                        st.markdown("### Verification Result")
                        st.write(verification)
                    else:
                        st.error(result["message"])
    
    # Image Answer Verification Tab
    with tab2:
        st.header("Verify Answer from Image")
        
        # Question input
        image_question = st.text_area("Question", height=100, placeholder="Enter the question here...", key="image_question")
        
        # Image upload
        answer_image = st.file_uploader("Upload Answer Image", type=["jpg", "jpeg", "png"], key="answer_image")
        
        # Display the uploaded image
        if answer_image:
            st.image(answer_image, caption="Uploaded Answer Image", use_container_width=True)
        
        # Verify button
        if st.button("Verify Answer from Image", key="verify_image"):
            if not image_question:
                st.error("Please enter a question.")
            elif not answer_image:
                st.error("Please upload an answer image.")
            elif not st.session_state.pdf_uploaded:
                st.warning("Please upload reference PDF documents first.")
            else:
                with st.spinner("Analyzing image and verifying answer..."):
                    result = verify_answer_from_image(image_question, answer_image)
                    
                    if result["success"]:
                        verification = result["result"]["verification"]
                        score = result["result"]["score"]
                        
                        # Display the score with color coding
                        score_color = "red" if score < 4 else "orange" if score < 7 else "green"
                        st.markdown(f"<h3 style='color: {score_color}'>Score: {score}/10</h3>", unsafe_allow_html=True)
                        
                        # Display the verification result
                        st.markdown("### Verification Result")
                        st.write(verification)
                    else:
                        st.error(result["message"])

if __name__ == "__main__":
    main()
