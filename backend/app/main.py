"""FastAPI application - Step 4: Firestore Integration."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import logging
from app.config import settings
from app.services.gemini_client import GeminiClient
from app.services.firestore_client import FirestoreClient

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
# This is non-blocking - the app will start even if Gemini is not configured
gemini_client = None
try:
    if settings.gemini_api_key:
        gemini_client = GeminiClient(api_key=settings.gemini_api_key)
        logger.info("Gemini client initialized successfully")
    else:
        logger.warning("GEMINI_API_KEY not set - Gemini features will be unavailable")
except Exception as e:
    logger.warning(f"Gemini client initialization failed: {str(e)}")
    gemini_client = None

# Initialize Firestore client (will fail if project ID is not set)
# This is non-blocking - the app will start even if Firestore is not configured
firestore_client = None
try:
    if settings.gcp_project_id:
        firestore_client = FirestoreClient(
            project_id=settings.gcp_project_id,
            collection_name=settings.firestore_collection
        )
        logger.info("Firestore client initialized successfully")
    else:
        logger.warning("GCP_PROJECT_ID not set - Firestore features will be unavailable")
except Exception as e:
    logger.warning(f"Firestore client initialization failed: {str(e)}")
    firestore_client = None


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
    
    # Test Firestore connection if client is initialized
    firestore_status = "unavailable"
    if firestore_client:
        try:
            if firestore_client.test_connection():
                firestore_status = "available"
            else:
                firestore_status = "connection_failed"
        except Exception as e:
            logger.warning(f"Firestore health check failed: {str(e)}")
            firestore_status = "error"
    
    return {
        "status": "healthy",
        "gemini": gemini_status,
        "firestore": firestore_status
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

port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)