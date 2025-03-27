import streamlit as st
import os
import sys
import PyPDF2
from io import StringIO

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

# Import prompts
from app.src.prompts.prompt import (
    GRAMMAR_PROMPT, 
    PLAGIARISM_PROMPT, 
    VOICE_CONVERSION_PROMPT, 
    THEME_PROMPT, 
    STYLE_SUGGESTIONS_PROMPT, 
    READABILITY_PROMPT, 
    AI_DETECTION_PROMPT, 
    ESSAY_GENERATION_PROMPT, 
    ESSAY_EVALUATION_PROMPT
)

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

model = ChatOpenAI(
    api_key=os.environ.get('OPENAI_API_KEY'),
    model="gpt-4o-mini",
    temperature=0,
)

def run_task(prompt, text, **kwargs):
    try:
        prompt_template = PromptTemplate(
            template=prompt,
            input_variables=["context", "word_count", "role"] if "context" in prompt else ["context", "voice_conversion"],
        )

        chain = prompt_template | model

        input_vars = {
            'context': text,
            'word_count': st.session_state.get('word_count', None),
            'role': st.session_state.get('role', None),
            'voice_conversion': st.session_state.get('voice_conversion', 'Active to Passive'),
            **kwargs
        }
        
        result = chain.invoke(input_vars)
        
        return result.content
    except Exception as e:
        return f"Error: {str(e)}"

def plagiarism_check(text_or_file):
    try:
        if isinstance(text_or_file, str):
            text = text_or_file
        elif hasattr(text_or_file, 'type'):
            if text_or_file.type == "text/plain":
                text = text_or_file.read().decode("utf-8")
            elif text_or_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(text_or_file)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
            else:
                return "Error: Unsupported file type. Please upload a text or PDF file."
        else:
            return "Error: Invalid input. Please provide text or a file."

        output = run_task(PLAGIARISM_PROMPT, text)
        return output
    except Exception as e:
        return f"Error: {str(e)}"

def detect_ai_generated_content(text_or_file):
    try:
        if isinstance(text_or_file, str):
            text = text_or_file
        elif hasattr(text_or_file, 'type'):
            if text_or_file.type == "text/plain":
                text = text_or_file.read().decode("utf-8")
            elif text_or_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(text_or_file)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
            else:
                return "Error: Unsupported file type. Please upload a text or PDF file."
        else:
            return "Error: Invalid input. Please provide text or a file."

        output = run_task(AI_DETECTION_PROMPT, text)
        return output
    except Exception as e:
        return f"Error: {str(e)}"

def evaluate_essay(essay, achievements, degree_program, college_name):
    try:
        input_variables = {
            'essay': essay,
            'academic_achievement': achievements.get('academic_achievement', ''),
            'professional_achievement': achievements.get('professional_achievement', ''),
            'international_experience': achievements.get('international_experience', ''),
            'degree_program': degree_program,
            'college_name': college_name
        }
        output = run_task(ESSAY_EVALUATION_PROMPT, input_variables['essay'], **input_variables)
        return output
    except Exception as e:
        return f"Error: {str(e)}"

st.title("Chatbot 🤖")

if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""

if 'word_count' not in st.session_state:
    st.session_state['word_count'] = None

if 'role' not in st.session_state:
    st.session_state['role'] = None

if 'achievements' not in st.session_state:
    st.session_state['achievements'] = {
        'academic_achievement': '',
        'professional_achievement': '',
        'international_experience': ''
    }

if 'degree_program' not in st.session_state:
    st.session_state['degree_program'] = ''

if 'college_name' not in st.session_state:
    st.session_state['college_name'] = ''

user_input = st.text_area("Enter your text here:", value=st.session_state['user_input'], height=200)

selected_task = st.selectbox("Select a task", ["Grammar Check", "Plagiarism Check", "Detect AI Generated Content", "Voice Conversion", "Analyze Theme", "Style Suggestions", "Readability Analysis", "Essay Generation", "Evaluate Essay"])

match selected_task:
    case "Grammar Check":
        if st.button("Grammar Check"):
            if user_input.strip():
                output = run_task(GRAMMAR_PROMPT, user_input)
                st.write(output)
            else:
                st.warning("Please enter some text to check.")
    case "Plagiarism Check":
        uploaded_file = st.file_uploader("Upload a file", type=["txt", "pdf"])
        if st.button("Plagiarism Check"):
            if uploaded_file is not None:
                output = plagiarism_check(uploaded_file)
                st.write(output)
            elif user_input.strip():
                output = plagiarism_check(user_input)
                st.write(output)
            else:
                st.warning("Please enter text or upload a file to check for plagiarism.")
    case "Detect AI Generated Content":
        uploaded_file = st.file_uploader("Upload a file", type=["txt", "pdf"])
        if st.button("Detect AI Generated Content"):
            if uploaded_file is not None:
                output = detect_ai_generated_content(uploaded_file)
                st.write(output)
            elif user_input.strip():
                output = detect_ai_generated_content(user_input)
                st.write(output)
            else:
                st.warning("Please enter text or upload a file to detect AI-generated content.")
    case "Voice Conversion":
        voice_conversion_type = st.selectbox("Select the conversion type:", ["Active to Passive", "Passive to Active"])
        st.session_state['voice_conversion'] = voice_conversion_type
        if st.button("Convert Voice"):
            if user_input.strip():
                output = run_task(VOICE_CONVERSION_PROMPT, user_input)
                st.write(output)
            else:
                st.warning("Please enter some text or to convert.")
    case "Analyze Theme":
        if st.button("Analyze Theme"):
            if user_input.strip():
                theme = run_task(THEME_PROMPT, user_input)
                st.write(theme)
            else:
                st.warning("Please enter some text to analyze.")
    case "Style Suggestions":
        if st.button("Style Suggestions"):
            if user_input.strip():
                style_output = run_task(STYLE_SUGGESTIONS_PROMPT, user_input)
                st.write(style_output)
            else:
                st.warning("Please enter some text to get style suggestions.")
    case "Readability Analysis":
        if st.button("Analyze Readability"):
            if user_input.strip():
                readability_output = run_task(READABILITY_PROMPT, user_input)
                st.write(readability_output)
            else:
                st.warning("Please enter some text to analyze.")
    case "Essay Generation":
        st.session_state['word_count'] = st.number_input("Enter the desired word count:", min_value=100, max_value=5000, value=500, step=100)
        st.session_state['role'] = st.text_input("Enter your role:", value=st.session_state.get('role', ''))
        if st.button("Generate Essay"):
            if user_input.strip(): 
                output = run_task(ESSAY_GENERATION_PROMPT, user_input)
                st.write(output)
            else:
                st.warning("Please enter an essay topic.")

if st.button("Clear"):
    st.session_state['user_input'] = ""
    st.session_state['achievements'] = {
        'academic_achievement': '',
        'professional_achievement': '',
        'international_experience': ''
    }
    st.session_state['degree_program'] = ''
    st.session_state['college_name'] = ''
    user_input = "" 