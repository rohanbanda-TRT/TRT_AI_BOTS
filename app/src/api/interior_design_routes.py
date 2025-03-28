import os
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel

from app.src.agents.interior_design_agent import InteriorDesignAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/interior-design", tags=["Interior Design"])

# Initialize agent
def get_interior_design_agent():
    """
    Dependency to get the Interior Design Agent instance.
    """
    try:
        return InteriorDesignAgent()
    except Exception as e:
        logger.error(f"Error initializing Interior Design Agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing agent: {str(e)}")

# Request models
class DesignRequest(BaseModel):
    """Request model for design generation."""
    room_type: str
    style: str
    requirements: str

class ModificationRequest(BaseModel):
    """Request model for image modification."""
    image_url: str
    modifications: str

class CostEstimateRequest(BaseModel):
    """Request model for cost estimation."""
    image_url: str
    room_type: str
    style: str
    requirements: str

# API endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Interior Design API is running"}

@router.post("/generate-image")
async def generate_design_image(
    request: DesignRequest = Body(...),
    agent: InteriorDesignAgent = Depends(get_interior_design_agent)
) -> Dict[str, Any]:
    """
    Generate an interior design image based on user requirements.
    
    Args:
        request: Design request containing room type, style, and requirements
        agent: Interior Design Agent instance
        
    Returns:
        Design image URL and related information
    """
    try:
        result = await agent.generate_design_image(
            room_type=request.room_type,
            style=request.style,
            requirements=request.requirements
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except Exception as e:
        logger.error(f"Error generating design image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating design image: {str(e)}")

@router.post("/modify-image")
async def modify_design_image(
    request: ModificationRequest = Body(...),
    agent: InteriorDesignAgent = Depends(get_interior_design_agent)
) -> Dict[str, Any]:
    """
    Modify an existing interior design image.
    
    Args:
        request: Modification request containing image URL and modifications
        agent: Interior Design Agent instance
        
    Returns:
        Modified image URL and related information
    """
    try:
        result = await agent.modify_design_image(
            image_url=request.image_url,
            modifications=request.modifications
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except Exception as e:
        logger.error(f"Error modifying design image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error modifying design image: {str(e)}")

@router.post("/estimate-cost")
async def estimate_cost(
    request: CostEstimateRequest = Body(...),
    agent: InteriorDesignAgent = Depends(get_interior_design_agent)
) -> Dict[str, Any]:
    """
    Estimate the cost of implementing a design shown in an image.
    
    Args:
        request: Cost estimate request containing image URL and design details
        agent: Interior Design Agent instance
        
    Returns:
        Cost estimate breakdown
    """
    try:
        result = await agent.estimate_cost(
            image_url=request.image_url,
            room_type=request.room_type,
            style=request.style,
            requirements=request.requirements
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except Exception as e:
        logger.error(f"Error estimating cost: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error estimating cost: {str(e)}")

@router.post("/generate-design")
async def generate_design(
    request: DesignRequest = Body(...),
    agent: InteriorDesignAgent = Depends(get_interior_design_agent)
) -> Dict[str, Any]:
    """
    Generate a design based on room type, style, and requirements.
    
    Args:
        request: Design request containing room type, style, and requirements
        agent: Interior Design Agent instance
        
    Returns:
        Design description and related information
    """
    try:
        result = await agent.generate_design(
            room_type=request.room_type,
            style=request.style,
            requirements=request.requirements
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except Exception as e:
        logger.error(f"Error generating design: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating design: {str(e)}")

@router.post("/process-design")
async def process_design(
    request: DesignRequest = Body(...),
    agent: InteriorDesignAgent = Depends(get_interior_design_agent)
) -> Dict[str, Any]:
    """
    Process a complete design request, generating both design and cost estimate.
    
    Args:
        request: Design request containing room type, style, and requirements
        agent: Interior Design Agent instance
        
    Returns:
        Complete design and cost information
    """
    try:
        result = await agent.process_design_request(
            room_type=request.room_type,
            style=request.style,
            requirements=request.requirements
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except Exception as e:
        logger.error(f"Error processing design request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing design request: {str(e)}")
