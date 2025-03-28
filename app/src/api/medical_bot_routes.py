"""
API routes for the Medical Bot.
"""
import logging
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uuid
from ..agents.medical_bot_agent import MedicalBotAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/medical-bot", tags=["medical-bot"])

# Initialize agent
medical_bot_agent = MedicalBotAgent()

# Request models
class ConsultRequest(BaseModel):
    question: str
    conversation_id: str = None

# Routes
@router.post("/consult")
async def consult(payload: ConsultRequest = Body(...)) -> Dict[str, Any]:
    """
    Process a medical question and return an AI-generated response.
    """
    try:
        # Generate a conversation ID if not provided
        conversation_id = payload.conversation_id or str(uuid.uuid4())
        
        # Process the question
        result = await medical_bot_agent.consult(payload.question, conversation_id)
        
        # Return the result with conversation ID
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "answer": result.get("answer", "")
        }
    except Exception as e:
        logger.error(f"Error in medical bot consult endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")