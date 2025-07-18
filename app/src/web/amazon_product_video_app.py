import streamlit as st
import requests
import json
import time

# This should be the URL where your FastAPI app is running
FASTAPI_BACKEND_URL = "http://localhost:8000/api/n8n-webhook/amazon-product"

st.set_page_config(
    page_title="Amazon Product Processor", 
    page_icon="🛒",
    layout="centered"
)

st.title("🛒 Amazon Product Processor")
st.markdown("---")

st.write("Enter an Amazon product URL below to trigger the n8n workflow for product processing.")

# Input field for the Amazon URL
url = st.text_input(
    "Amazon Product URL", 
    placeholder="https://www.amazon.com/dp/B08N5WRWNW",
    help="Paste the full Amazon product URL here"
)

# Optional user ID input
user_id = st.text_input(
    "User ID (Optional)",
    placeholder="Enter your user ID",
    help="Optional user identifier for tracking"
)

# Create two columns for better layout
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("🚀 Process Product", type="primary"):
        if url:
            # Basic URL validation
            if not url.startswith(('http://', 'https://')):
                st.error("❌ Please enter a valid URL starting with http:// or https://")
            
            try:
                with st.spinner("Processing Amazon product..."):
                    # The payload for our FastAPI endpoint
                    payload = {
                        "product_url": url,
                        "user_id": user_id if user_id else None
                    }
                    
                    # Make a POST request to our FastAPI backend
                    response = requests.post(
                        FASTAPI_BACKEND_URL, 
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ Workflow triggered successfully!")
                        
                        # Display the response
                        result = response.json()
                        
                        # Create expandable sections for better organization
                        with st.expander("📋 Response Details", expanded=True):
                            col_status, col_message = st.columns(2)
                            
                            with col_status:
                                st.info(f"**Status:** {result.get('status', 'Unknown')}")
                            
                            with col_message:
                                st.info(f"**Message:** {result.get('message', 'No message')}")
                            
                            if result.get('workflow_id'):
                                st.success(f"**Workflow ID:** {result.get('workflow_id')}")
                            
                            if result.get('execution_id'):
                                st.success(f"**Execution ID:** {result.get('execution_id')}")
                        
                        # Show full response in a code block
                        with st.expander("🔍 Full Response", expanded=False):
                            st.json(result)
                            
                    else:
                        st.error(f"❌ Error triggering workflow")
                        
                        # Try to parse error response
                        try:
                            error_data = response.json()
                            st.error(f"**Status Code:** {response.status_code}")
                            st.error(f"**Error:** {error_data.get('detail', 'Unknown error')}")
                            
                            # Show full error details
                            with st.expander("🔍 Error Details", expanded=False):
                                st.json(error_data)
                        except:
                            st.error(f"**Status Code:** {response.status_code}")
                            st.error(f"**Error:** {response.text}")
                        
            except requests.exceptions.ConnectionError:
                st.error("❌ Failed to connect to the backend. Is the FastAPI server running?")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request failed: {e}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
        else:
            st.warning("⚠️ Please enter an Amazon product URL.")

with col2:
    if st.button("🔧 Test Connection"):
        try:
            with st.spinner("Testing connection..."):
                # Test if backend is reachable
                test_response = requests.get(
                    "http://localhost:8000/api/n8n-webhook/test-webhook-connection"
                )
                
                if test_response.status_code == 200:
                    st.success("✅ Backend connection successful!")
                    
                    test_result = test_response.json()
                    
                    with st.expander("🔍 Connection Test Results", expanded=False):
                        st.json(test_result)
                else:
                    st.error(f"❌ Backend test failed: {test_response.status_code}")
                    
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to FastAPI backend. Is it running on localhost:8000?")
        except Exception as e:
            st.error(f"❌ Connection test failed: {e}")

# Add some helpful information
st.markdown("---")
st.markdown("### ℹ️ Instructions")
st.markdown("""
1. **Enter Amazon URL**: Paste the full Amazon product URL
2. **Add User ID**: (Optional) Enter your user identifier
3. **Click Process**: Start the n8n workflow
4. **View Results**: Check the response for workflow status

**Example URLs:**
- `https://www.amazon.com/dp/B08N5WRWNW`
- `https://amazon.com/gp/product/B08N5WRWNW`
- `https://www.amazon.com/product-name/dp/B08N5WRWNW`
""")

# Add status information
st.markdown("---")
st.markdown("### 🔧 System Status")

status_col1, status_col2 = st.columns(2)

with status_col1:
    st.markdown("**FastAPI Backend:**")
    st.code("http://localhost:8000")

with status_col2:
    st.markdown("**n8n Webhook:**")
    st.code("Check via Test Connection")

# Add a refresh button for the page
if st.button("🔄 Refresh Page"):
    st.rerun()