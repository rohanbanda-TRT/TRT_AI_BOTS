from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..agents.performance_analyzer import PerformanceAnalyzerAgent
from ..core.config import get_settings
from ..agents import ContentGeneratorAgent, DriverScreeningAgent, CompanyAdminAgent
from typing import Optional, List
from ..managers.company_questions_factory import get_company_questions_manager
from ..models.question_models import Question
import logging
import tempfile
import os
from fastapi import UploadFile, File, Form
from ..services.answer_verification.answer_verifier import AnswerVerifier

logger = logging.getLogger(__name__)

# Main router
router = APIRouter()

# Create separate routers for different API groups
main_router = APIRouter(tags=["Main"])
driver_router = APIRouter(tags=["Driver Screening"])
company_router = APIRouter(tags=["Company Admin"])
answer_verifier_router = APIRouter(tags=["Answer Verification"])

settings = get_settings()
content_agent = ContentGeneratorAgent(settings.OPENAI_API_KEY)
driver_screening_agent = DriverScreeningAgent(settings.OPENAI_API_KEY)
company_admin_agent = CompanyAdminAgent(settings.OPENAI_API_KEY)
performance_analyzer = PerformanceAnalyzerAgent(settings.OPENAI_API_KEY)
answer_verifier = AnswerVerifier()

class PerformanceRequest(BaseModel):
    messages: str

class ChatRequest(BaseModel):
    message: str
    
    session_id: str = Field(
        ...,  
        min_length=1,
        description="Unique session identifier for conversation tracking"
    )
    name: str = Field(
        ...,
        min_length=2,
        description="Name of the user"
    )
    company: str = Field(
        ...,
        min_length=2,
        description="Company name of the user"
    )
    subject: str = Field(
        ...,
        min_length=2,
        description="Subject or topic for the conversation"
    )

class DriverScreeningRequest(BaseModel):
    message: str
    
    session_id: str = Field(
        ...,
        min_length=1,
        description="Unique session identifier for screening conversation"
    )
    dsp_code: Optional[str] = Field(
        None,
        description="Optional DSP code to use company-specific questions"
    )

class CompanyAdminRequest(BaseModel):
    message: str
    
    session_id: str = Field(
        ...,
        min_length=1,
        description="Unique session identifier for company admin conversation"
    )
    dsp_code: str = Field(
        ...,
        min_length=1,
        description="DSP code to associate with questions"
    )

class CompanyQuestionsRequest(BaseModel):
    dsp_code: str
    questions: List[Question]

# Answer Verification Models
class AnswerVerificationRequest(BaseModel):
    question: str
    student_answer: str

class VerificationResponse(BaseModel):
    score: int
    verification: str

@main_router.post("/analyze-performance",
              summary="Analyze performance",
              description="Analyze the performance of a conversation")
async def analyze_performance(request: PerformanceRequest):
    try:
        settings = get_settings()
        
        # Analyze the performance data
        result = performance_analyzer.analyze_performance(request.messages)
        
        return {"analysis": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@main_router.post("/chat",
              summary="Chat with the bot",
              description="Chat with the bot")
async def chat(request: ChatRequest):
    try:
        message = (
            f"I am {request.name} from {request.company} and I want your help with {request.subject}"
            if not request.message or request.message.strip() == ""
            else request.message
        )
        
        # Process message using agent with session_id
        result = content_agent.process_message(message, request.session_id)
        
        return {
            "response": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@driver_router.post("/driver-screening",
                summary="Driver screening",
                description="Start or continue a driver screening conversation")
async def driver_screening(request: DriverScreeningRequest):
    try:
        # Validate session_id
        session_id = request.session_id
        if not session_id or session_id.strip() == "":
            # Generate a unique session ID if none provided
            import uuid
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session_id: {session_id}")
        
        # Validate dsp_code
        dsp_code = request.dsp_code
        if not dsp_code or dsp_code.strip() == "":
            dsp_code = "DEMO"  # Use a default DSP code
            logger.info(f"Using default dsp_code: {dsp_code}")
        
        # Validate message
        default_message = f"Start [DSP: {dsp_code}, Session: {session_id}]"
        message = (
            default_message
            if not request.message or request.message.strip() == ""
            else request.message
        )
        
        # Process message using driver screening agent with dsp_code if provided
        try:
            result = driver_screening_agent.process_message(
                message, 
                session_id,
                dsp_code
            )
            
            return {
                "response": result,
                "session_id": session_id,
                "dsp_code": dsp_code
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing message: {str(e)}"
            )
    
    except Exception as e:
        logger.error(f"Unexpected error in driver_screening endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error: {str(e)}"
        )

@company_router.post("/company-admin",
                 summary="Company admin",
                 description="Start or continue a company admin conversation")
async def company_admin(request: CompanyAdminRequest):
    try:
        # Process message using company admin agent
        result = company_admin_agent.process_message(
            request.message,
            request.session_id,
            request.dsp_code
        )
        
        return {
            "response": result,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@company_router.get("/company-questions/{dsp_code}",
                summary="Get company questions",
                description="Get company questions for a DSP code")
async def get_company_questions(dsp_code: str):
    try:
        questions_manager = get_company_questions_manager()
        questions = questions_manager.get_questions(dsp_code)
        
        return {
            "dsp_code": dsp_code,
            "questions": questions
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@company_router.post("/company-questions",
                 summary="Save company questions",
                 description="Save company questions for a DSP code")
async def save_company_questions(request: CompanyQuestionsRequest):
    try:
        questions_manager = get_company_questions_manager()
        questions = [q.model_dump() for q in request.questions]
        success = questions_manager.create_questions(request.dsp_code, questions)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save questions")
        
        return {
            "success": True,
            "dsp_code": request.dsp_code,
            "question_count": len(request.questions)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@answer_verifier_router.post("/upload-pdfs",
                         summary="Upload reference PDFs",
                         description="Upload PDF files for processing as reference materials")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload PDF files for processing.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Create a temporary directory to store the uploaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_paths = []
        
        # Save the uploaded files to the temporary directory
        for file in files:
            if not file.filename.endswith('.pdf'):
                continue
                
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            pdf_paths.append(file_path)
        
        if not pdf_paths:
            raise HTTPException(status_code=400, detail="No PDF files provided")
        
        # Process the PDFs
        try:
            num_chunks = answer_verifier.process_pdfs(pdf_paths)
            return {"message": f"Successfully processed {len(pdf_paths)} PDFs with {num_chunks} chunks"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing PDFs: {str(e)}")

@answer_verifier_router.post("/verify-answer",
                         response_model=VerificationResponse,
                         summary="Verify text answer",
                         description="Verify a student's text answer against reference materials")
async def verify_answer(request: AnswerVerificationRequest):
    """
    Verify a student's answer to a question.
    """
    try:
        result = answer_verifier.verify_answer(request.question, request.student_answer)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying answer: {str(e)}")

@answer_verifier_router.post("/verify-answer-from-image",
                         response_model=VerificationResponse,
                         summary="Verify answer from image",
                         description="Verify a student's answer from an uploaded image")
async def verify_answer_from_image(question: str = Form(...), answer_image: UploadFile = File(...)):
    """
    Verify a student's answer from an uploaded image.
    """
    if not answer_image:
        raise HTTPException(status_code=400, detail="No image file provided")
    
    # Check if the file is an image
    if not answer_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image")
    
    try:
        # Read the image file
        image_bytes = await answer_image.read()
        
        # Verify the answer from the image
        result = answer_verifier.verify_answer_from_image(question, image_bytes)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying answer from image: {str(e)}")

@answer_verifier_router.post("/clear-vector-store",
                         summary="Clear reference materials",
                         description="Clear all reference materials from the vector store")
async def clear_vector_store():
    """
    Clear the vector store.
    """
    answer_verifier.clear_vector_store()
    return {"message": "Vector store cleared successfully"}

# Include all routers in the main router
router.include_router(main_router)
router.include_router(driver_router)
router.include_router(company_router)
router.include_router(answer_verifier_router)