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

@router.post("/soil/analyze", response_model=SoilAnalysisResult)
def analyze_soil(request: SoilAnalysisRequest, analyzer: SoilSuitabilityAnalyzer = Depends(get_analyzer)):
    """Analyze soil suitability for a specific crop."""
    result = analyzer.analyze(request.soil_parameters.dict(), request.crop_name)
    return SoilAnalysisResult(summary=result["summary"])
