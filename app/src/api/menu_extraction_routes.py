"""
API routes for the Menu Extraction Agent.
"""
import logging
from fastapi import APIRouter, Body, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
import io

from ..agents.menu_extraction_agent import MenuExtractionAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/menu-extraction", tags=["menu-extraction"])

# Initialize agent
menu_extraction_agent = MenuExtractionAgent()

# Request models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str = "ok"

# Routes
@router.get("/health")
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    """
    return HealthResponse()

@router.post("/chat")
async def chat(payload: ChatRequest = Body(...)) -> Dict[str, Any]:
    """
    Process a chat message and return an AI-generated response.
    """
    try:
        # Generate a conversation ID if not provided
        conversation_id = payload.conversation_id or str(uuid.uuid4())
        
        # Process the message
        result = await menu_extraction_agent.chat(payload.message, conversation_id)
        
        # Return the result with conversation ID
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "answer": result.get("answer", "")
        }
    except Exception as e:
        logger.error(f"Error in menu extraction chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/analyze-menu-images")
async def analyze_menu_images(
    menu_images: List[UploadFile] = File(...),
    conversation_id: Optional[str] = Form(None),
    message: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Analyze multiple menu images and extract structured data.
    
    Args:
        menu_images: List of menu image files
        conversation_id: Optional conversation ID
        message: Optional user message to include with the images
    """
    try:
        # Generate a conversation ID if not provided
        conversation_id = conversation_id or str(uuid.uuid4())
        
        # Read all image files
        image_bytes_list = []
        for image in menu_images:
            image_bytes = await image.read()
            image_bytes_list.append(image_bytes)
        
        # Process the images
        result = await menu_extraction_agent.analyze_menu_images(image_bytes_list, conversation_id)
        
        # If a message was provided, add it to the conversation history
        if message:
            # Add the message to the conversation history
            from ..utils.chat_history import InMemoryChatHistory
            InMemoryChatHistory.add_message(conversation_id, "human", message)
            
            # Update the result to include the message context
            if "answer" in result:
                result["answer"] = f"In response to your message: \"{message}\"\n\n{result['answer']}"
        
        # Return the result with conversation ID
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "answer": result.get("answer", ""),
            "menu_data": result.get("menu_data", {}),
            "extracted_text": result.get("extracted_text", "")
        }
    except Exception as e:
        logger.error(f"Error in menu extraction image analysis endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
