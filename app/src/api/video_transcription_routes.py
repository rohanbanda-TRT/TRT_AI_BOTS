"""
API routes for the Video Transcription Agent.
"""
import os
import logging
import uuid
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional
from ..agents.video_transcription_agent import VideoTranscriptionAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/video-transcription", tags=["video-transcription"])

# Initialize agent
video_agent = VideoTranscriptionAgent()

# Create upload directory if it doesn't exist
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "videos")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Request models
class VideoQueryRequest(BaseModel):
    question: str

# Routes
@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
):
    """
    Upload a video file and process it.
    
    Args:
        file: The video file to upload
        
    Returns:
        Dictionary with upload and processing results
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            # Write the uploaded file content to the temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process the video using the temporary file
            logger.info(f"Processing video: {file.filename}")
            processing_result = await video_agent.process_video(temp_file_path, file.filename)
            
            return {
                "status": "success",
                "message": "Video processed successfully",
                "original_filename": file.filename,
                "processing": processing_result
            }
        finally:
            # Always clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.info(f"Temporary file removed: {temp_file_path}")
        
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")

@router.post("/query")
async def query_video(payload: VideoQueryRequest = Body(...)):
    """
    Answer a question based on video transcription.
    
    Args:
        payload: Query request with question
        
    Returns:
        Dictionary with query results
    """
    try:
        # Query the video using similarity search across all transcriptions
        result = await video_agent.query_video(
            question=payload.question
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error querying video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error querying video: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the Video Transcription API.
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "video-transcription"}
