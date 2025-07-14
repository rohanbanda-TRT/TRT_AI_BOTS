from fastapi import FastAPI
from .routes import router

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Soil Crop Suitability API")

app.include_router(router)
