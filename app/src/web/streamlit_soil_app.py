import streamlit as st
import os
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from app.src.agents.soil_logic import SoilSuitabilityAnalyzer
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Soil Crop Suitability Analyzer", layout="centered")
st.title("🌱 Soil Crop Suitability Analyzer")

# --- Chat Section ---
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "memory" not in st.session_state:
    st.session_state["memory"] = ConversationBufferMemory(return_messages=True)

st.markdown("## 💬 Soil/Crop Chatbot")

# Display chat history
for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input box
user_prompt = st.chat_input("Ask about soil, fertilizer, or crops...")

# Handle new user input (step 1: show instantly)
if user_prompt:
    st.session_state["chat_history"].append({"role": "user", "content": user_prompt})
    st.session_state["chat_history"].append({"role": "ai", "content": "_SOIL BOT is thinking..._"})
    st.session_state["pending_llm"] = True
    st.session_state["pending_user_message"] = user_prompt
    st.rerun()

# Handle pending LLM response (step 2: generate answer)
if st.session_state.get("pending_llm", False):
    user_message = st.session_state.get("pending_user_message", "")
    if user_message:
        st.session_state["memory"].chat_memory.add_user_message(user_message)
        api_key = os.environ.get("OPENAI_API_KEY")
        analyzer = SoilSuitabilityAnalyzer(openai_api_key=api_key, memory=st.session_state["memory"])
        result = analyzer.analyze({"user_message": user_message}, crop_name="")
        ai_response = result["summary"] if isinstance(result, dict) else str(result)
        st.session_state["memory"].chat_memory.add_ai_message(ai_response)
        st.session_state["chat_history"][-1] = {"role": "ai", "content": ai_response}
    st.session_state["pending_llm"] = False
    st.session_state["pending_user_message"] = ""
    st.rerun()

# Sidebar for API key
if not os.environ.get("OPENAI_API_KEY"):
    st.sidebar.warning("Please set your OPENAI_API_KEY in your environment or .env file.")
