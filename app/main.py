from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .src.api.routes import router
from .src.api.document_routes import router as document_router
from .src.api.medical_bot_routes import router as medical_bot_router
from .src.api.video_transcription_routes import router as video_transcription_router
from .src.api.interior_design_routes import router as interior_design_router

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)