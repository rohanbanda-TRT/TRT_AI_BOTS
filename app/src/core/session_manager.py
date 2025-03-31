"""
Session manager for managing agent sessions.
"""
import logging
from typing import Dict, Any, Optional
import uuid

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import AIMessage, HumanMessage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manager for agent sessions.
    """
    
    def __init__(self):
        """
        Initialize the session manager.
        """
        self.sessions = {}
    
    def get_or_create_session(
        self,
        session_id: str,
        llm: Any,
        tools: list,
        prompt: ChatPromptTemplate,
        memory_k: int = 10
    ) -> AgentExecutor:
        """
        Get or create a session for the given session ID.
        
        Args:
            session_id: The session ID
            llm: The language model to use
            tools: The tools to use
            prompt: The prompt template to use
            memory_k: The number of messages to keep in memory
            
        Returns:
            The agent executor for the session
        """
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Create memory
        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history",
            input_key="input",
            output_key="output",
            k=memory_k
        )
        
        # Create agent
        agent = create_openai_tools_agent(llm, tools, prompt)
        
        # Create executor
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
        
        # Store session
        self.sessions[session_id] = executor
        
        return executor

# Singleton instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """
    Get the session manager singleton instance.
    
    Returns:
        The session manager singleton instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
