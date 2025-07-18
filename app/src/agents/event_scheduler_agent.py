from ..tools.googleCalender import CreateGoogleCalendarEvent
from ..tools.indetity import identity
from ..tools.mailvalidation import validate_email
from google.oauth2 import service_account
from googleapiclient.discovery import build
from langchain_core.output_parsers import JsonOutputParser
from ..utils.event_scheduler_function import create_agent
from ..models.event_scheduler_models import (
    ColorTrendVariables,
    ComparisonVariables,
    GetEventsSchema,
    PrechatVariables
)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
import os
from ..prompts.event_scheduler import (
    COMPARISON_PROMPT,
    COLOR_TREND_PROMPT,
    GREETING_PROMPT,
    PRECHAT_PROMPT,
    FEEDBACK_PROMPT,
    SCHEDULER_PROMPT,
    FALLBACK_PROMPT,
)
from dotenv import load_dotenv
load_dotenv()

# Service Account Authentication
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Load service account credentials
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Build the calendar service
calendar_service = build('calendar', 'v3', credentials=credentials)

createeventtool = CreateGoogleCalendarEvent.from_api_resource(calendar_service)

llm = ChatOpenAI(temperature=0)

# Rest of your code remains the same...
comparison_parser = JsonOutputParser(pydantic_object=ComparisonVariables)

comparison_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            COMPARISON_PROMPT,
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
).partial(format_instructions=comparison_parser.get_format_instructions())

comparison = create_agent(
    llm=llm, tools=[identity], system_prompt=comparison_prompt_template
)

coolortrend_parser = JsonOutputParser(pydantic_object=ColorTrendVariables)

trend_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            COLOR_TREND_PROMPT,
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
).partial(format_instructions=coolortrend_parser.get_format_instructions())

colortrend = create_agent(llm, [identity], trend_prompt_template)

greet_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            GREETING_PROMPT,
        ),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
greet_agent = create_agent(llm, [identity], greet_prompt_template)

prechat_parser = JsonOutputParser(pydantic_object=PrechatVariables)

prechat_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            PRECHAT_PROMPT,
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
).partial(format_instructions=prechat_parser.get_format_instructions())

prechat_agent = create_agent(llm, [validate_email, identity], prechat_prompt_template)

feedback_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            FEEDBACK_PROMPT,
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
feedback_agent = create_agent(llm, [identity], feedback_prompt_template)

scheduler_parser = JsonOutputParser(pydantic_object=GetEventsSchema)

scheduler_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            SCHEDULER_PROMPT,
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ],
).partial(
    format_instructions=scheduler_parser.get_format_instructions(),
)

scheduler_agent = create_agent(
    llm=llm,
    tools=[createeventtool, validate_email, identity],
    system_prompt=scheduler_prompt_template,
)

fallback_prompt_template = ChatPromptTemplate.from_messages(
[
    (
        "system",
        FALLBACK_PROMPT,
        
    ),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
],
)

fallback_agent = create_agent(
    llm=llm,
    tools=[identity],
    system_prompt=fallback_prompt_template,
)