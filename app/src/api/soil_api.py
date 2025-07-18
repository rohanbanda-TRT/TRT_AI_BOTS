"""
Router logic for the Soil Suitability Analysis System.
"""
from pydantic import BaseModel, Field
import logging
from fastapi import APIRouter, Depends
from app.src.agents.soil_logic import SoilAnalysisRequest, SoilAnalysisResult, SoilSuitabilityAnalyzer, get_analyzer

logging.basicConfig(level=logging.INFO)

# --- MODELS ---
class SoilParameters(BaseModel):
    ph: float = Field(..., description="Soil pH value")
    organic_matter: float = Field(..., description="Organic matter percentage")
    sand: float = Field(..., description="Sand percentage in soil texture")
    silt: float = Field(..., description="Silt percentage in soil texture")
    clay: float = Field(..., description="Clay percentage in soil texture")
    electrical_conductivity: float = Field(..., description="Electrical conductivity (EC) in dS/m")
    moisture: float = Field(..., description="Soil moisture percentage")
    temperature: float = Field(..., description="Soil temperature in Celsius")

class SoilAnalysisRequest(BaseModel):
    soil_parameters: SoilParameters
    crop_name: str

# --- API ROUTER LOGIC ---
router = APIRouter(tags=["soil"])

from fastapi import Request
from langchain.memory import ConversationBufferMemory

# In-memory conversation memory store (simple dict for demo)
conversation_memories = {}

@router.post("/soil/analyze", response_model=SoilAnalysisResult)
def analyze_soil(request: SoilAnalysisRequest, analyzer: SoilSuitabilityAnalyzer = Depends(get_analyzer), req: Request = None):
    """Analyze soil suitability for a specific crop. Optionally supports conversational memory via conversation_id in query params."""
    conversation_id = None
    if req:
        conversation_id = req.query_params.get("conversation_id")
    memory = None
    if conversation_id:
        if conversation_id not in conversation_memories:
            conversation_memories[conversation_id] = ConversationBufferMemory(return_messages=True)
        memory = conversation_memories[conversation_id]
        # Add user message to memory (just soil parameters/crop for demo)
        user_message = f"Soil: {request.soil_parameters.json()}\nCrop: {request.crop_name}"
        memory.chat_memory.add_user_message(user_message)
    # Use memory-enabled analyzer if memory is set
    analyzer_with_memory = SoilSuitabilityAnalyzer(analyzer.client.api_key, memory=memory) if memory else analyzer
    result = analyzer_with_memory.analyze(request.soil_parameters.dict(), request.crop_name)
    if memory:
        memory.chat_memory.add_ai_message(result["summary"])
    return SoilAnalysisResult(summary=result["summary"])
