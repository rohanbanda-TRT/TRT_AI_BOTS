import streamlit as st
import requests

st.set_page_config(page_title="Your Personal Wine Sommelier", page_icon="🍷")

st.markdown(""" 
<style>
    /* Move the user avatar to the right */
    .stChatMessage[data-testid="chat-message-container-user"] {
        flex-direction: row-reverse;
    }
    .stChatMessage .st-emotion-cache-1c7y2kd {
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

st.title("🍷 Your Personal Wine Sommelier")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Hi! I'm your wine expert assistant. Ask me anything about wine, food pairings, celebrations, or just for fun! 🍷"}
    ]

# Display chat messages from history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle user input
if prompt := st.chat_input("What would you like to know?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    st.rerun()

# Generate and display new response
if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("WineBot is thinking..."):
            try:
                last_prompt = st.session_state.chat_history[-1]["content"]
                url = "http://127.0.0.1:8000/query/"
                response = requests.post(url, params={"question": last_prompt})
                response.raise_for_status() # Raise an exception for bad status codes
                answer = response.json().get("answer", "Sorry, I couldn't find an answer.")
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            except requests.exceptions.RequestException as e:
                error_msg = f"Failed to connect to the wine service: {e}"
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
            st.rerun()
