"""
Merged FastAPI entry point and router logic from the original app_2 codebase.
"""

import logging
from fastapi import FastAPI, APIRouter, UploadFile, File
from wine.agents.agents import AgenticRAGService, QueryRequest, QueryResponse

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Wine Agentic RAG System")

# --- API ROUTER LOGIC ---
router = APIRouter()
rag_service = AgenticRAGService()

@router.post("/process-document/")
def process_document(file: UploadFile = File(...)):
    """Process and index a new document (PDF or PPTX)."""
    return rag_service.process_document(file)

@router.post("/query/", response_model=QueryResponse)
def query_agent(question: str):
    """Agentic RAG endpoint for answering wine questions."""
    return rag_service.query(question)

app.include_router(router)
