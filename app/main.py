from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
load_dotenv()

from .src.api.script_router import router as script_router
from .src.core.settings import settings

from .src.api.routes import router
from .src.api.document_routes import router as document_router
from .src.api.medical_bot_routes import router as medical_bot_router
from .src.api.video_transcription_routes import router as video_transcription_router
from .src.api.interior_design_routes import router as interior_design_router
from .src.api.menu_extraction_routes import router as menu_extraction_router
from .src.api.wine_api import router as wine_router
from .src.api.soil_api import router as soil_router
from .src.api.n8n_webhook_routes import router as n8n_webhook_router
from .src.api.mail_routes import router as mail_router

app = FastAPI(title="TRT AI Bots API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)
app.include_router(document_router, prefix="/api")
app.include_router(medical_bot_router, prefix="/api")
app.include_router(video_transcription_router, prefix="/api")
app.include_router(interior_design_router, prefix="/api")
app.include_router(menu_extraction_router, prefix="/api")
app.include_router(script_router, prefix="/api")
app.include_router(n8n_webhook_router, prefix="/api")
app.include_router(mail_router, prefix="/api")
app.include_router(wine_router, prefix="/api")
app.include_router(soil_router, prefix="/api")

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)