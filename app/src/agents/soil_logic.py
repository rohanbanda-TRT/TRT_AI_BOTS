from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Models ---
class SoilParameters(BaseModel):
    ph: float = Field(..., description="Soil pH value")
    nitrogen: float = Field(..., description="Nitrogen content in mg/kg")
    phosphorus: float = Field(..., description="Phosphorus content in mg/kg")
    potassium: float = Field(..., description="Potassium content in mg/kg")
    organic_matter: float = Field(..., description="Organic matter percentage")
    moisture: float = Field(..., description="Soil moisture percentage")
    temperature: float = Field(..., description="Soil temperature in Celsius")

class SoilAnalysisRequest(BaseModel):
    soil_parameters: SoilParameters
    crop_name: str

class SoilAnalysisResult(BaseModel):
    summary: Optional[str] = None

# --- Core Logic ---
class SoilSuitabilityAnalyzer:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)

    def analyze(self, soil_data: dict, crop_name: str) -> dict:
        # Parse input
        try:
            soil_params = SoilParameters(**soil_data)
            crop_name = str(crop_name).strip() if crop_name is not None else ""
        except Exception as e:
            return {"summary": f"Input parsing error: {str(e)}"}
        # LLM analysis
        prompt = f"Analyze the suitability of the following soil for growing {crop_name}:\n{soil_params.json()}"
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            llm_result = response.choices[0].message.content.strip()
        except Exception as e:
            llm_result = f"LLM analysis failed: {str(e)}"
        # Format summary
        summary = f"**Crop:** {crop_name.capitalize()}\n**LLM Analysis:** {llm_result}"
        return {"summary": summary}

# --- FastAPI Router ---
router = APIRouter()

def get_analyzer() -> SoilSuitabilityAnalyzer:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return SoilSuitabilityAnalyzer(openai_api_key=api_key)
