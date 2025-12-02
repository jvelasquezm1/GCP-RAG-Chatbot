"""FastAPI application - Step 2: Basic Chat Endpoint."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

# Create FastAPI app
app = FastAPI(
    title="GCP RAG Chatbot API",
    version="0.2.0"
)

# Configure CORS - allow localhost for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "version": "0.2.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Basic chat endpoint - Step 2.
    Returns a simple echo response (no RAG yet).
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Simple echo response for Step 2 (no AI, no RAG yet)
    # Just returns a friendly acknowledgment
    response_text = f"You said: '{request.message}'. This is Step 2 - basic chat endpoint working! (RAG coming in next steps)"
    
    return ChatResponse(
        answer=response_text,
        message=request.message
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
