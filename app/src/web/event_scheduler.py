import streamlit as st
import requests
from streamlit_calendar import calendar

# Initialize the session state to keep chat history, event date state, and selected date/time
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "event_date_disabled" not in st.session_state:
    st.session_state.event_date_disabled = False  # Initially disable the event date input

if "selected_datetime" not in st.session_state:
    st.session_state.selected_datetime = ""  # Store the selected date and time

if "user_input" not in st.session_state:
    st.session_state.user_input = ""  # Store the user input

if "event_date_hidden" not in st.session_state:
    st.session_state.event_date_hidden = True  # Initially hide the event date input

if "temp_selected_datetime" not in st.session_state:
    st.session_state.temp_selected_datetime = ""  # Temporarily store the selected date and time

if "time_zone" not in st.session_state:
    st.session_state.time_zone = ""

if "time_zone_disabled" not in st.session_state:
    st.session_state.time_zone_disabled = True

if "time_zone_hidden" not in st.session_state:
    st.session_state.time_zone_hidden = True



st.title("Auto Assist AI Chatbot")

# Create a placeholder for the chat history above the input
chat_placeholder = st.empty()

# Display chat history
with chat_placeholder.container():
    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(message)

# User input at the bottom
st.session_state.user_input = st.text_input("User:", value=st.session_state.user_input, key="input", placeholder="ENTER YOUR MESSAGE")

# Conditionally display the event date input
if not st.session_state.event_date_hidden:
    selected_event = calendar(
        events=[],  # No pre-defined events
        options={"selectable": True, "editable": True},  # Allow date selection and drag/drop
        key="calendar",  # Unique key for this calendar instance
        callbacks=["select"]  # Enable callback for date selection
    )

    # Check if a date range is selected
    if selected_event and "select" in selected_event:
        # Force start and end dates to be the same
        selected_date = selected_event["select"]["end"].split("T")[0]
        st.session_state.temp_selected_datetime = selected_date

    # Time selection inputs
    start_time = st.time_input("Start Time", key="start_time")
    end_time = st.time_input("End Time", key="end_time")
    time_zone = st.selectbox(
        "Please select your time zone",
        ("Default", "Asia/Kolkata", "America/Nework", "Australia/Sydney"),
        key="time_zone",
        index=1,
        placeholder="Select time zone...",
    )

    if st.button("Select Event Details"):
        if st.session_state.temp_selected_datetime and start_time and end_time:
            # Combine the selected date with the start and end times
            st.session_state.selected_datetime = f" At {start_time} to {end_time} On {st.session_state.temp_selected_datetime} and timezone is {st.session_state.time_zone}"
            st.session_state.user_input = f"{st.session_state.selected_datetime}"
            # Hide event date input and button after selection
            st.session_state.event_date_hidden = True
            st.session_state.event_date_disabled = True
            st.session_state.time_zone_disabled = True
            st.rerun()  # Rerun to update chat history and input text

# Send button
if st.button("Send"):
    if st.session_state.user_input:
        with st.spinner("Processing..."):
            try:
                # Send user input to the LangChain API
                response = requests.post(
                    "http://127.0.0.1:8000/api/interact/",
                    json={"messages": [st.session_state.user_input]},
                )
                response.raise_for_status()  # Raise an error for bad responses
                
                # Debug: Print the raw response
                st.write("Raw response:", response.text)
                
                response_data = response.json()
                
                # Debug: Print the parsed response
                st.write("Parsed response data:", response_data)
                
                # Update chat history with the user's input and assistant's responses
                if "response" in response_data:
                    # Append the user's input to the chat history
                    st.session_state.chat_history.append(("user", st.session_state.user_input))
                    
                    # Append each message from the assistant to the chat history
                    for message in response_data["response"]:
                        st.session_state.chat_history.append(("assistant", message))
                        
                        # Debug: Print each message
                        st.write("Assistant response message:", message)
                        
                        # Check if the assistant's response includes the phrase
                        if "date/time" in message.lower():
                            st.session_state.event_date_disabled = False  # Enable the event date input
                            st.session_state.event_date_hidden = False  # Make event date input visible
                            st.session_state.time_zone_disabled = False  # Enable the time zone input
                            st.session_state.time_zone_hidden = False  # Make time zone input visible
                        else:
                            # Hide and disable the event date input if not needed
                            st.session_state.event_date_hidden = True
                            st.session_state.event_date_disabled = True
                            st.session_state.time_zone_disabled = True # Enable the time zone input
                            st.session_state.time_zone_hidden = True
                        
                    st.rerun()  # Rerun the script to update the UI
                else:
                    st.error("Unexpected response format.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error in processing your request: {e}")
    else:
        st.warning("Please enter some text.")

    # Make event date input and button invisible and disabled after send
    st.session_state.event_date_hidden = True
    st.session_state.event_date_disabled = True
    st.session_state.time_zone_disabled = True
    st.session_state.time_zone_hidden = True
    st.rerun()  # Rerun the script to update the UI
