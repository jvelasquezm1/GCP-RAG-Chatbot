"""Document ingestion service for processing uploaded files."""
import io
import logging
from pathlib import Path
from typing import Optional, Dict, List
from PyPDF2 import PdfReader

from app.config import settings
from app.services.gemini_client import GeminiClient
from app.services.firestore_client import FirestoreClient
from app.utils.text_processing import chunk_text, sanitize_input
from google.cloud import firestore

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting documents into Firestore."""
    
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        firestore_client: Optional[FirestoreClient] = None
    ):
        """
        Initialize ingestion service.
        
        Args:
            gemini_client: Gemini client instance (creates new if not provided)
            firestore_client: Firestore client instance (creates new if not provided)
        """
        self.gemini_client = gemini_client
        self.firestore_client = firestore_client
        
        if not self.gemini_client:
            if not settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY is required for ingestion")
            self.gemini_client = GeminiClient()
        
        if not self.firestore_client:
            if not settings.gcp_project_id:
                raise ValueError("GCP_PROJECT_ID is required for ingestion")
            self.firestore_client = FirestoreClient()
    
    def read_markdown(self, content: bytes) -> str:
        """Read markdown content from bytes."""
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"Error decoding markdown content: {str(e)}")
            raise ValueError(f"Invalid UTF-8 encoding: {str(e)}")
    
    def read_pdf(self, content: bytes) -> str:
        """Read PDF content from bytes."""
        try:
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error reading PDF: {str(e)}")
            raise ValueError(f"Failed to read PDF: {str(e)}")
    
    def read_text(self, content: bytes) -> str:
        """Read plain text content from bytes."""
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"Error decoding text content: {str(e)}")
            raise ValueError(f"Invalid UTF-8 encoding: {str(e)}")
    
    def read_document(self, content: bytes, filename: str) -> str:
        """
        Read document content based on file extension.
        
        Args:
            content: File content as bytes
            filename: Original filename (used to determine file type)
            
        Returns:
            Document text content
        """
        suffix = Path(filename).suffix.lower()
        
        if suffix in ['.md', '.markdown']:
            return self.read_markdown(content)
        elif suffix == '.pdf':
            return self.read_pdf(content)
        elif suffix == '.txt':
            return self.read_text(content)
        else:
            raise ValueError(f"Unsupported file type: {suffix}. Supported: .md, .markdown, .pdf, .txt")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text using Gemini.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            return self.gemini_client.get_embedding(
                text,
                task_type="retrieval_document"
            )
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise
    
    def ingest_document(
        self,
        content: bytes,
        filename: str,
        metadata: Optional[Dict] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Ingest a document into Firestore.
        
        Args:
            content: File content as bytes
            filename: Original filename
            metadata: Optional metadata to attach to chunks
            chunk_size: Chunk size (defaults to settings)
            chunk_overlap: Chunk overlap (defaults to settings)
            
        Returns:
            Dictionary with ingestion results:
            - chunks_created: Number of chunks created
            - filename: Original filename
            - success: Whether ingestion was successful
        """
        logger.info(f"Processing document: {filename}")
        
        # Read document
        text = self.read_document(content, filename)
        text = sanitize_input(text)
        
        if not text or not text.strip():
            logger.warning(f"Document {filename} is empty or contains no valid text")
            return {
                "chunks_created": 0,
                "filename": filename,
                "success": False,
                "error": "Document is empty or contains no valid text"
            }
        
        # Chunk text
        chunks = chunk_text(
            text,
            chunk_size=chunk_size or settings.chunk_size,
            overlap=chunk_overlap or settings.chunk_overlap
        )
        
        logger.info(f"Created {len(chunks)} chunks from {filename}")
        
        # Prepare metadata
        doc_metadata = {
            "source_file": filename,
            "source_type": "uploaded",
            **(metadata or {})
        }
        
        # Process each chunk
        chunks_created = 0
        errors = []
        
        for i, chunk in enumerate(chunks):
            try:
                # Get embedding
                embedding = self.get_embedding(chunk)
                
                # Store in Firestore
                chunk_metadata = {
                    **doc_metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                
                self.firestore_client.collection.add({
                    "text": chunk,
                    "embedding": embedding,
                    "metadata": chunk_metadata,
                    "created_at": firestore.SERVER_TIMESTAMP
                })
                
                chunks_created += 1
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(chunks)} chunks...")
                    
            except Exception as e:
                error_msg = f"Error processing chunk {i} from {filename}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        result = {
            "chunks_created": chunks_created,
            "filename": filename,
            "success": chunks_created > 0,
            "total_chunks": len(chunks)
        }
        
        if errors:
            result["errors"] = errors[:5]  # Limit to first 5 errors
        
        logger.info(f"Successfully ingested {chunks_created} chunks from {filename}")
        return result
