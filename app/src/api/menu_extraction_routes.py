from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
import os
import uuid
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
import json
from pydantic import BaseModel

from app.src.agents.menu_extraction_agent import MenuExtractionAgent
from app.src.utils.session_manager import SessionManager, get_session_manager

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '.env'))

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Menu Extraction"])

# Initialize menu extraction agent
menu_extraction_agent = MenuExtractionAgent()

# S3 configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

logger.info(f"S3 Bucket Name: {S3_BUCKET_NAME}")
logger.info(f"AWS Region: {AWS_REGION}")
logger.info(f"AWS Access Key ID available: {bool(AWS_ACCESS_KEY)}")
logger.info(f"AWS Secret Access Key available: {bool(AWS_SECRET_KEY)}")

# Initialize S3 client with explicit credentials
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Local upload directory for fallback
UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class QueryRequest(BaseModel):
    query: str
    image_urls: Optional[List[str]] = None
    session_id: Optional[str] = None

@router.get("/menu-extraction/health")
async def health_check():
    """Health check endpoint for the Menu Extraction API."""
    return {"status": "healthy"}

@router.post("/menu-extraction/upload-images")
async def upload_images(
    files: List[UploadFile] = File(...),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Upload multiple menu images and return their URLs.
    
    Args:
        files: List of image files to upload
        session_manager: Session manager for tracking user sessions
        
    Returns:
        JSON response with image URLs
    """
    try:
        logger.info(f"Uploading {len(files)} images")
        
        # Create a new session ID if one doesn't exist
        session_id = str(uuid.uuid4())
        
        image_urls = []
        
        for file in files:
            try:
                # Read file content
                contents = await file.read()
                
                # Generate a unique filename
                filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
                
                logger.info(f"Attempting to upload file to S3: {filename}")
                
                try:
                    # Upload to S3 with public-read ACL to make it accessible
                    s3_client.put_object(
                        Bucket=S3_BUCKET_NAME,
                        Key=f"menu_images/{filename}",
                        Body=contents,
                        ContentType=file.content_type,
                        ACL='public-read'  # Make the object publicly readable
                    )
                    
                    # Generate direct S3 URL without pre-signed parameters
                    direct_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/menu_images/{filename}"
                    logger.info(f"Successfully uploaded to S3. Direct URL: {direct_url}")
                    image_urls.append(direct_url)
                
                except ClientError as e:
                    logger.error(f"AWS S3 ClientError: {e.response.get('Error', {}).get('Code', 'Unknown')} - {e.response.get('Error', {}).get('Message', str(e))}")
                    # Fall back to local storage
                    local_path = os.path.join(UPLOAD_DIR, filename)
                    with open(local_path, "wb") as f:
                        f.write(contents)
                    
                    # Generate local URL
                    image_url = f"/static/uploads/{filename}"
                    logger.warning(f"Falling back to local storage. URL: {image_url}")
                    image_urls.append(image_url)
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error processing file {file.filename}: {str(e)}")
        
        # Store the image URLs in a custom session dictionary
        # We'll use a simple dictionary approach since we don't need the full agent functionality
        if not hasattr(session_manager, 'custom_sessions'):
            session_manager.custom_sessions = {}
        
        session_manager.custom_sessions[session_id] = {
            "image_urls": image_urls
        }
        
        return {
            "status": "success",
            "session_id": session_id, 
            "image_urls": image_urls
        }
        
    except Exception as e:
        logger.error(f"Error uploading images: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading images: {str(e)}")

@router.post("/menu-extraction/process-query")
async def process_query(
    request: QueryRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Process a user query, optionally with menu images.
    
    Args:
        request: Query request containing the query text and optional image URLs
        session_manager: Session manager for tracking user sessions
        
    Returns:
        JSON response with the agent's response
    """
    try:
        query = request.query
        image_urls = request.image_urls
        session_id = request.session_id
        
        logger.info(f"Processing query: {query}")
        
        # If session_id is provided, retrieve image URLs from session
        if session_id and hasattr(session_manager, 'custom_sessions'):
            if session_id in session_manager.custom_sessions:
                session_data = session_manager.custom_sessions[session_id]
                # If image_urls not provided in request, use the ones from session
                if not image_urls and "image_urls" in session_data:
                    image_urls = session_data["image_urls"]
        
        # Process query with agent
        result = await menu_extraction_agent.process_query(query, image_urls)
        
        # If there's an error, return it
        if "error" in result:
            return {"status": "error", "response": result["error"]}
        
        # Return the result
        return {
            "status": "success", 
            "response": result.get("raw_extracted_text") or result.get("response")
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return {"status": "error", "response": str(e)}
