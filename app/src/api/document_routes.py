"""
API routes for document management and RAG functionality.
"""
import os
import uuid
import logging
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from pydantic import BaseModel

from ..agents.document_rag_agent import DocumentRagAgent
from ..utils.chat_history import InMemoryChatHistory

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["documents"])

# Initialize Document RAG Agent
document_agent = DocumentRagAgent()

# Models
class QueryRequest(BaseModel):
    query: str
    conversation_id: str
    k: int = 3

class DocumentResponse(BaseModel):
    document_id: str
    title: str
    upload_time: str
    status: str
    message: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

class ConversationResponse(BaseModel):
    conversation_id: str
    messages: List[Dict[str, Any]]

class DeleteResponse(BaseModel):
    status: str
    message: str

class DocumentListResponse(BaseModel):
    status: str
    documents: List[Dict[str, Any]]
    message: Optional[str] = None

# Routes
@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(None)
):
    """
    Upload a document for RAG processing
    """
    try:
        # Generate document ID and use filename if title not provided
        document_id = str(uuid.uuid4())
        if not title:
            title = file.filename
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Process document in background
        result = document_agent.process_document(tmp_path, document_id, title)
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        if result["status"] == "error":
            return DocumentResponse(
                document_id=document_id,
                title=title,
                upload_time=datetime.now().isoformat(),
                status="error",
                message=result["message"]
            )
        
        return DocumentResponse(
            document_id=document_id,
            title=title,
            upload_time=datetime.now().isoformat(),
            status="success"
        )
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """
    List all documents in the vector store
    """
    try:
        result = document_agent.list_documents()
        
        if result["status"] == "error":
            return DocumentListResponse(
                status="error",
                documents=[],
                message=result.get("message", "Error listing documents")
            )
        
        return DocumentListResponse(
            status="success",
            documents=result.get("documents", [])
        )
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def query_documents(query_request: QueryRequest):
    """
    Query documents using RAG
    """
    try:
        result = document_agent.query(
            query_request.query,
            query_request.conversation_id
        )
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        logger.error(f"Error querying documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error querying documents: {str(e)}")

@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(document_id: str):
    """
    Delete a document from the vector store
    """
    try:
        result = document_agent.delete_document(document_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["message"])
        
        return DeleteResponse(
            status="success",
            message=result["message"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.get("/conversation/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """
    Get conversation history
    """
    try:
        messages = InMemoryChatHistory.get_history(conversation_id)
        
        return ConversationResponse(
            conversation_id=conversation_id,
            messages=messages
        )
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting conversation: {str(e)}")

@router.delete("/conversation/{conversation_id}", response_model=DeleteResponse)
async def clear_conversation(conversation_id: str):
    """
    Clear conversation history
    """
    try:
        InMemoryChatHistory.clear_history(conversation_id)
        
        return DeleteResponse(
            status="success",
            message=f"Conversation {conversation_id} cleared successfully"
        )
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")
