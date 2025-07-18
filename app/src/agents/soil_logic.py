from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
print("DEBUG: Loaded OpenAI API key:", os.environ.get("OPENAI_API_KEY"))
# --- Models ---
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

class SoilAnalysisResult(BaseModel):
    summary: Optional[str] = None

# --- Core Logic ---
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI

class SoilSuitabilityAnalyzer:
    def __init__(self, openai_api_key: str, memory: ConversationBufferMemory = None):
        self.client = OpenAI(api_key=openai_api_key)
        self.memory = memory
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_api_key)

    def analyze(self, soil_data: dict, crop_name: str) -> dict:
        # If LangChain memory is provided, use it for context management
        if self.memory is not None:
            # Add user message to memory
            user_message = soil_data.get("user_message") or soil_data.get("chat_context") or ""
            if user_message:
                self.memory.chat_memory.add_user_message(user_message)
            # Get full conversation history from memory
            messages = self.memory.chat_memory.messages
            response = self.llm(messages)
            ai_response = response.content
            self.memory.chat_memory.add_ai_message(ai_response)
            summary = f"**SOIL BOT:** {ai_response}"
            return {"summary": summary}
        # Fallback: original logic
        # Chat-based: if 'chat_context' is present, use it directly as the prompt
        if soil_data and "chat_context" in soil_data:
            prompt = (
                "You are an expert in soil, fertilizer, and crop science. "
                "If the user mentions a region (such as South Asia, East region, North America, etc.), always tailor your answer to the specific region mentioned, considering local climate, soil, and crop practices. "
                "If no region is mentioned, give a general answer. "
                "Answer the user's question or analyze the scenario below.\n\n"
                f"{soil_data['chat_context']}"
            )
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )
                llm_result = response.choices[0].message.content.strip()
            except Exception as e:
                llm_result = f"LLM analysis failed: {str(e)}"
            summary = f"**SOIL BOT:** {llm_result}"
            return {"summary": summary}
        # Otherwise, use structured soil parameters as before
        try:
            soil_params = SoilParameters(**soil_data)
            crop_name = str(crop_name).strip() if crop_name is not None else ""
        except Exception as e:
            return {"summary": f"Input parsing error: {str(e)}"}
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
        summary = f"**Crop:** {crop_name.capitalize()}\n**SOIL BOT:** {llm_result}"
        return {"summary": summary}

# --- FastAPI Router ---
router = APIRouter()

def get_analyzer() -> SoilSuitabilityAnalyzer:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return SoilSuitabilityAnalyzer(openai_api_key=api_key)
