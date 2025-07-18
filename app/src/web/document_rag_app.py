"""
Streamlit app for Document RAG (Retrieval Augmented Generation).
"""
import streamlit as st
import os
import uuid
import tempfile
import time
from datetime import datetime
import requests
import json
from typing import List, Dict, Any

# Set page configuration
st.set_page_config(
    page_title="Document RAG",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE_URL = "https://trt-demo-ai-bots.demotrt.com/api"  # Update with your API URL
ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.ppt', '.xlsx', '.xls', '.html', '.htm', '.txt']

# Initialize session state
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "documents" not in st.session_state:
    st.session_state.documents = []

if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("OPENAI_API_KEY", "")

if "retrieval_k" not in st.session_state:
    st.session_state.retrieval_k = 3

# Helper functions
def fetch_conversation_history():
    """Fetch conversation history from API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/conversation/{st.session_state.conversation_id}"
        )
        if response.status_code == 200:
            history = response.json()
            st.session_state.messages = history.get("messages", [])
    except Exception as e:
        st.error(f"Error fetching conversation history: {str(e)}")

def fetch_documents():
    """Fetch list of documents from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        if response.status_code == 200:
            result = response.json()
            if result["status"] == "success":
                st.session_state.documents = result.get("documents", [])
            else:
                st.error(f"Error fetching documents: {result.get('message', 'Unknown error')}")
        else:
            st.error(f"Error fetching documents: {response.text}")
    except Exception as e:
        st.error(f"Error fetching documents: {str(e)}")

def upload_document(file, title=None):
    """Upload a document to the API"""
    try:
        if not title:
            title = file.name
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
            tmp.write(file.getbuffer())
            tmp_path = tmp.name
        
        # Upload the file
        with open(tmp_path, "rb") as f:
            files = {"file": (file.name, f)}
            data = {"title": title}
            response = requests.post(
                f"{API_BASE_URL}/documents/upload",
                files=files,
                data=data
            )
        
        # Clean up the temporary file
        os.unlink(tmp_path)
        
        if response.status_code == 200:
            result = response.json()
            st.success(f"Document uploaded successfully: {title}")
            # Fetch updated document list
            fetch_documents()
            return result
        else:
            st.error(f"Error uploading document: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error uploading document: {str(e)}")
        return None

def delete_document(document_id):
    """Delete a document from the API"""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/documents/{document_id}"
        )
        if response.status_code == 200:
            st.success("Document deleted successfully")
            fetch_documents()
        else:
            st.error(f"Error deleting document: {response.text}")
    except Exception as e:
        st.error(f"Error deleting document: {str(e)}")

def query_documents(query):
    """Query documents using the API"""
    try:
        payload = {
            "query": query,
            "conversation_id": st.session_state.conversation_id,
            "k": st.session_state.retrieval_k
        }
        response = requests.post(
            f"{API_BASE_URL}/query",
            json=payload
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error querying documents: {response.text}")
            return {"answer": "Error querying documents", "sources": []}
    except Exception as e:
        st.error(f"Error querying documents: {str(e)}")
        return {"answer": f"Error: {str(e)}", "sources": []}

def clear_conversation():
    """Clear the current conversation"""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/conversation/{st.session_state.conversation_id}"
        )
        if response.status_code == 200:
            st.session_state.messages = []
            st.session_state.conversation_id = str(uuid.uuid4())
            st.success("Conversation cleared")
        else:
            st.error(f"Error clearing conversation: {response.text}")
    except Exception as e:
        st.error(f"Error clearing conversation: {str(e)}")

# Sidebar components
def render_sidebar():
    """Render the sidebar with document upload and settings"""
    st.sidebar.title("📚 Document RAG")
    
    # Document upload section
    st.sidebar.header("Upload Documents")
    uploaded_file = st.sidebar.file_uploader("Choose a document", type=["pdf", "docx", "pptx", "ppt", "xlsx", "xls", "html", "htm", "txt"])
    doc_title = st.sidebar.text_input("Document Title (optional)")
    
    if uploaded_file is not None:
        if st.sidebar.button("Upload Document"):
            with st.sidebar.status("Uploading document..."):
                result = upload_document(uploaded_file, doc_title or uploaded_file.name)
                if result:
                    time.sleep(1)  # Give user time to see the success message
                    st.rerun()
    
    # Document management section
    st.sidebar.header("Document Management")
    if not st.session_state.documents:
        st.sidebar.info("No documents uploaded yet")
    else:
        for doc in st.session_state.documents:
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                st.text(doc.get('title', 'Untitled'))
            with col2:
                if st.button("Delete", key=f"delete_{doc.get('document_id')}"):
                    delete_document(doc.get('document_id'))
    
    # Conversation management
    st.sidebar.header("Conversation")
    if st.sidebar.button("New Conversation"):
        clear_conversation()
        st.rerun()
    
    # Current conversation ID display
    st.sidebar.caption(f"Current Conversation ID: {st.session_state.conversation_id[:8]}...")
    
    # Settings section (collapsible)
    with st.sidebar.expander("System Information", expanded=False):
        st.subheader("Known Issues")
        st.markdown("""
        - Document deletion isn't supported with Pinecone Serverless/Starter indexes. 
          Documents can be removed from UI but will still appear in search results.
        """)
        
        st.subheader("Tips")
        st.markdown("""
        - For better results, use more specific questions about your documents
        - If you don't get relevant results, try rephrasing your question
        """)

# Main app components
def render_chat_tab():
    """Render the chat interface tab"""
    st.header("Document Q&A")
    
    # Create a container for the chat history that will scroll
    chat_container = st.container()
    
    # Create a container for the input box that will stay fixed at the bottom
    input_container = st.container()
    
    # Handle input in the fixed container at the bottom
    with input_container:
        query = st.chat_input("Ask a question about your documents...")
        if query:
            # Add to session state
            st.session_state.messages.append({"type": "human", "content": query})
            
            # Query the API
            with st.status("Thinking..."):
                result = query_documents(query)
                answer = result.get("answer", "I couldn't find an answer to your question.")
                sources = result.get("sources", [])
            
            # Add AI response to session state
            st.session_state.messages.append({
                "type": "bot", 
                "content": answer,
                "sources": sources
            })
            
            # Force a rerun to update the chat history
            st.rerun()
    
    # Display conversation history in the scrollable container
    with chat_container:
        for message in st.session_state.messages:
            role = message.get("type", "bot")
            content = message.get("content", "")
            
            if role == "human":
                st.chat_message("user").write(content)
            else:
                with st.chat_message("assistant"):
                    st.write(content)
                    
                    # Display sources if available
                    sources = message.get("sources", [])
                    if sources:
                        with st.expander("Sources"):
                            for i, source in enumerate(sources):
                                st.markdown(f"**Source {i+1}:** {source.get('title', 'Unknown')} (Page {source.get('page', 'N/A')})")
                                st.text(source.get('snippet', ''))

def render_documents_tab():
    """Render the documents tab"""
    st.header("Documents")
    
    # Refresh button
    if st.button("Refresh Documents"):
        fetch_documents()
        st.rerun()
    
    if not st.session_state.documents:
        st.info("No documents uploaded yet. Use the sidebar to upload documents.")
    else:
        for doc in st.session_state.documents:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(doc.get('title', 'Untitled'))
                with col2:
                    if st.button("Delete", key=f"delete_doc_{doc.get('document_id')}"):
                        delete_document(doc.get('document_id'))
                        st.rerun()
                st.divider()

# Main app
def main():
    # Fetch initial data
    fetch_conversation_history()
    fetch_documents()
    
    # Render sidebar
    render_sidebar()
    
    # Create tabs for chat and documents
    tab1, tab2 = st.tabs(["Chat", "Documents"])
    
    with tab1:
        render_chat_tab()
    
    with tab2:
        render_documents_tab()

if __name__ == "__main__":
    main()
