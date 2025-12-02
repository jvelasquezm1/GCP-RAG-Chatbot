"""FastAPI application - Step 3: Gemini API Integration."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
from app.config import settings
from app.services.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client (will fail if API key is not set)
try:
    gemini_client = GeminiClient(api_key=settings.gemini_api_key)
    logger.info("Gemini client initialized successfully")
except Exception as e:
    logger.warning(f"Gemini client initialization failed: {str(e)}")
    gemini_client = None


# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=1000, description="User's message")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str = Field(..., description="The generated answer")
    message: str = Field(..., description="Original user message")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "GCP RAG Chatbot API",
        "version": settings.api_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    gemini_status = "available" if gemini_client else "unavailable"
    return {
        "status": "healthy",
        "gemini": gemini_status
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - Step 3.
    Uses Gemini API to generate AI responses.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Check if Gemini client is available
    if not gemini_client:
        raise HTTPException(
            status_code=503,
            detail="Gemini API is not configured. Please set GEMINI_API_KEY environment variable."
        )
    
    try:
        # Generate response using Gemini
        response_text = gemini_client.generate_response(
            prompt=request.message,
            system_instruction=settings.system_prompt,
            temperature=settings.gemini_temperature
        )
        
        return ChatResponse(
            answer=response_text,
            message=request.message
        )
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
