"""
Router logic for the Wine Agentic RAG System.
"""

import logging
from fastapi import APIRouter, UploadFile, File
from app.src.agents.wine_agents import AgenticRAGService, QueryRequest, QueryResponse

logging.basicConfig(level=logging.INFO)

# --- API ROUTER LOGIC ---
router = APIRouter(tags=["wine"])
rag_service = AgenticRAGService()

@router.post("/wine/process-document/")
def process_document(file: UploadFile = File(...)):
    """Process and index a new document (PDF or PPTX)."""
    return rag_service.process_document(file)

@router.post("/wine/query/", response_model=QueryResponse)
async def query_agent(request: QueryRequest = None, question: str = None):
    """Agentic RAG endpoint for answering wine questions.
    
    Can be called with either a JSON body (QueryRequest) or a query parameter (question).
    """
    # Get question from either the request body or query parameter
    query = question
    if request:
        query = request.question
    
    if not query:
        return QueryResponse(answer="No question provided. Please ask a wine-related question.")
        
    return rag_service.query(query)

