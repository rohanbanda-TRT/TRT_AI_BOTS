"""
Router logic for the Soil Suitability Analysis System.
"""

import logging
from fastapi import APIRouter, Depends
from app.src.agents.soil_logic import SoilAnalysisRequest, SoilAnalysisResult, SoilSuitabilityAnalyzer, get_analyzer

logging.basicConfig(level=logging.INFO)

# --- API ROUTER LOGIC ---
router = APIRouter(tags=["soil"])

@router.post("/soil/analyze", response_model=SoilAnalysisResult)
def analyze_soil(request: SoilAnalysisRequest, analyzer: SoilSuitabilityAnalyzer = Depends(get_analyzer)):
    """Analyze soil suitability for a specific crop."""
    result = analyzer.analyze(request.soil_parameters.model_dump(), request.crop_name)
    return SoilAnalysisResult(summary=result["summary"])
