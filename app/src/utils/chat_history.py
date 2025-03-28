"""
Chat history utilities for managing conversation history.
"""
import logging
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class InMemoryChatHistory:
    """
    In-memory chat history manager for storing conversation history.
    """
    _history_store = {}  # Class variable to store all conversations

    @classmethod
    def get_history(cls, conversation_id):
        """
        Get or create a chat history for a conversation ID
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            List of message dictionaries
        """
        if conversation_id not in cls._history_store:
            cls._history_store[conversation_id] = []
        return cls._history_store[conversation_id]

    @classmethod
    def add_message(cls, conversation_id, role, content):
        """
        Add a message to the conversation history
        
        Args:
            conversation_id: Unique identifier for the conversation
            role: Role of the message sender (human/ai)
            content: Content of the message
            
        Returns:
            Updated history list
        """
        history = cls.get_history(conversation_id)
        history.append({"type": role, "content": content})
        return history

    @classmethod
    def clear_history(cls, conversation_id):
        """
        Clear the history for a conversation ID
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Empty list
        """
        if conversation_id in cls._history_store:
            cls._history_store[conversation_id] = []
        return []

def get_chat_history(conversation_id: str) -> BaseChatMessageHistory:
    """
    Get a chat history object for the given conversation ID
    
    Args:
        conversation_id: Unique identifier for the conversation
        
    Returns:
        Chat history object compatible with LangChain
    """
    try:
        # Try to use Redis for chat history
        return RedisChatMessageHistory(conversation_id)
    except Exception as e:
        logger.warning(f"Could not initialize Redis chat history: {str(e)}. Falling back to in-memory.")
        # Fall back to in-memory chat history
        return ChatMessageHistory()
