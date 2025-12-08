from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import logging
from app.config import settings
from app.services.gemini_client import GeminiClient
from app.services.firestore_client import FirestoreClient
from app.services.ingestion_service import IngestionService
from app.middleware.ip_whitelist import ip_whitelist_middleware

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

# Configure CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",  # Allow all origins using regex
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add IP whitelist middleware for ingestion endpoints
@app.middleware("http")
async def ip_whitelist_middleware_handler(request: Request, call_next):
    """IP whitelist middleware wrapper."""
    try:
        return await ip_whitelist_middleware(request, call_next)
    
    except HTTPException as exc:
        response = JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers
        )
        
        response.headers["Access-Control-Allow-Origin"] = "*" 
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response

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


class IngestionResponse(BaseModel):
    """Response model for ingestion endpoint."""
    success: bool = Field(..., description="Whether ingestion was successful")
    filename: str = Field(..., description="Name of the uploaded file")
    chunks_created: int = Field(..., description="Number of chunks created")
    total_chunks: int = Field(..., description="Total number of chunks processed")
    message: str = Field(..., description="Status message")


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
    Chat endpoint - RAG Retrieval.
    Uses RAG (Retrieval-Augmented Generation) to provide context-aware responses.
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
        # RAG Retrieval Flow
        context_text = ""
        retrieved_docs = []
        
        # Check if RAG is enabled and Firestore is available
        if settings.rag_enabled and firestore_client:
            try:
                # 1. Generate query embedding
                query_embedding = gemini_client.get_embedding(
                    request.message,
                    task_type="retrieval_query"
                )
                
                # 2. Search for similar documents
                retrieved_docs = firestore_client.search_similar_documents(
                    query_embedding=query_embedding,
                    top_k=settings.rag_top_k,
                    similarity_threshold=settings.rag_similarity_threshold,
                    max_documents=1000  # Limit for performance (adjust as needed)
                )
                
                # 3. Build context from retrieved documents
                if retrieved_docs:
                    context_parts = []
                    for i, doc in enumerate(retrieved_docs, 1):
                        text = doc.get('text', '')
                        metadata = doc.get('metadata', {})
                        source = metadata.get('source_file', 'document')
                        context_parts.append(f"[Document {i} from {source}]:\n{text}")
                    
                    context_text = "\n\n".join(context_parts)
                    logger.info(f"Retrieved {len(retrieved_docs)} relevant documents for RAG")
                else:
                    logger.info("No relevant documents found in Firestore")
                    
            except Exception as e:
                # If RAG retrieval fails, log but continue without context
                logger.warning(f"RAG retrieval failed, continuing without context: {str(e)}")
                context_text = ""
        
        # 4. Build prompt with context (if available)
        if context_text:
            # Enhanced system prompt for RAG
            rag_system_prompt = (
                f"{settings.system_prompt}\n\n"
                "Use the following retrieved documents to answer the user's question. "
                "If the documents contain relevant information, use it to provide a comprehensive answer. "
                "If the documents don't contain relevant information, answer based on your general knowledge, "
                "but mention that the information wasn't found in the provided documents."
            )
            
            # Build prompt with context
            full_prompt = (
                f"Context from retrieved documents:\n\n{context_text}\n\n"
                f"User question: {request.message}\n\n"
                "Please provide a helpful answer based on the context above."
            )
        else:
            # No context available - use standard prompt
            rag_system_prompt = settings.system_prompt
            full_prompt = request.message
        
        # 5. Generate response using Gemini with context
        response_text = gemini_client.generate_response(
            prompt=full_prompt,
            system_instruction=rag_system_prompt,
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


@app.post("/ingest", response_model=IngestionResponse)
async def ingest_document(
    file: UploadFile = File(..., description="Document file to ingest (PDF, Markdown, or Text)")
):
    """
    Document ingestion endpoint.
    
    Accepts file uploads and ingests them into Firestore with embeddings.
    Only accessible from whitelisted IP addresses.
    
    Supported file types:
    - PDF (.pdf)
    - Markdown (.md, .markdown)
    - Plain text (.txt)
    """
    # Check if ingestion is enabled
    if not settings.ingestion_enabled:
        raise HTTPException(
            status_code=503,
            detail="Document ingestion is currently disabled"
        )
    
    # Check if required services are available
    if not gemini_client:
        raise HTTPException(
            status_code=503,
            detail="Gemini API is not configured. Please set GEMINI_API_KEY environment variable."
        )
    
    if not firestore_client:
        raise HTTPException(
            status_code=503,
            detail="Firestore is not configured. Please set GCP_PROJECT_ID environment variable."
        )
    
    # Validate file type
    allowed_extensions = ['.pdf', '.md', '.markdown', '.txt']
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Supported types: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    
    try:
        # Initialize ingestion service
        ingestion_service = IngestionService(
            gemini_client=gemini_client,
            firestore_client=firestore_client
        )
        
        # Ingest document
        result = ingestion_service.ingest_document(
            content=content,
            filename=file.filename or "uploaded_file",
            metadata={
                "upload_source": "api",
                "content_type": file.content_type
            }
        )
        
        if result["success"]:
            return IngestionResponse(
                success=True,
                filename=result["filename"],
                chunks_created=result["chunks_created"],
                total_chunks=result["total_chunks"],
                message=f"Successfully ingested {result['chunks_created']} chunks from {result['filename']}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to ingest document")
            )
            
    except ValueError as e:
        # Handle validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error ingesting document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting document: {str(e)}"
        )


port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)