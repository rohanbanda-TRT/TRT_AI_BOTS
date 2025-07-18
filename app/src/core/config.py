from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    LANGSMITH_TRACING: bool = True
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: str = "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"
    LANGSMITH_PROJECT: str = "Report-Generation"
    
    # MongoDB settings
    MONGODB_PASSWORD: str = os.environ.get("MONGODB_PASSWORD", "")
    MONGODB_URI: str = f"mongodb+srv://suyog:{quote_plus(os.environ.get('MONGODB_PASSWORD', ''))}@dsp-lokitech.dbvpz.mongodb.net/?retryWrites=true&w=majority&appName=dsp-lokitech"
    MONGODB_DB_NAME: str = "TRT_DB"
    
    # Storage settings
    # Only MongoDB is supported
    COMPANY_QUESTIONS_STORAGE: str = "mongodb"
    
    # Pinecone settings for test verification system
    PINECONE_API_KEY: str = os.environ.get("PINECONE_API_KEY", "")
    
    # AWS settings
    AWS_ACCESS_KEY_ID: str = os.environ.get("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.environ.get("AWS_REGION", "ap-south-1")
    S3_BUCKET_NAME: str = os.environ.get("S3_BUCKET_NAME", "auction-listing-poc")

    openai_api_key_tpn: str | None = None  
    runway_api_key: str | None = None
    n8n_webhook_url: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings():
    return Settings()