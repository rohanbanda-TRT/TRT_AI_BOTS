"""
Medical Bot Agent for answering health-related questions.
"""
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from ..prompts.medical_bot import MEDICAL_BOT_PROMPT
from ..utils.chat_history import InMemoryChatHistory

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class MedicalBotAgent:
    """
    Agent for answering medical and health-related questions.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        """
        Initialize the Medical Bot Agent.
        
        Args:
            model_name: The name of the OpenAI model to use
            temperature: The temperature setting for the model
        """
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=1024
        )
        
        # Create prompt template
        self.system_prompt = SystemMessage(content=MEDICAL_BOT_PROMPT)
    
    async def consult(self, question: str, conversation_id: str) -> Dict[str, Any]:
        """
        Process a medical question and return an AI-generated response.
        
        Args:
            question: The medical question to be answered
            conversation_id: The ID of the conversation
            
        Returns:
            Dict containing the answer
        """
        try:
            # Add user message to history
            InMemoryChatHistory.add_message(conversation_id, "human", question)
            
            # Create messages with the actual question
            messages = [
                self.system_prompt,
                HumanMessage(content=question)
            ]
            
            # Get response from the LLM
            response = await self.llm.ainvoke(messages)
            answer = response.content
            
            # Add AI response to history
            InMemoryChatHistory.add_message(conversation_id, "ai", answer)
            
            return {
                "answer": answer
            }
        except Exception as e:
            logger.error(f"Error processing medical question: {str(e)}")
            error_message = f"An error occurred while processing your question: {str(e)}"
            InMemoryChatHistory.add_message(conversation_id, "ai", error_message)
            return {"answer": error_message}
