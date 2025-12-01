#!/usr/bin/env python3
"""
Document ingestion script for RAG chatbot.

This script processes documents (markdown, PDF, or text files) and stores them
in Firestore with embeddings for retrieval.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import logging
from dotenv import load_dotenv

# Add parent directory to path to import backend utilities
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import google.generativeai as genai
from google.cloud import firestore
from pypdf2 import PdfReader

# Import utilities from backend
from app.utils.text_processing import chunk_text, sanitize_input
from app.config import settings

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentIngester:
    """Handles document ingestion and embedding generation."""
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        collection: Optional[str] = None
    ):
        """
        Initialize document ingester.
        
        Args:
            gemini_api_key: Gemini API key (defaults to env/settings)
            project_id: GCP project ID (defaults to env/settings)
            collection: Firestore collection name (defaults to settings)
        """
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY") or settings.gemini_api_key
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID") or settings.gcp_project_id
        self.collection_name = collection or os.getenv("FIRESTORE_COLLECTION") or settings.firestore_collection
        
        # Initialize Gemini
        genai.configure(api_key=self.gemini_api_key)
        self.embedding_model = settings.gemini_embedding_model
        
        # Initialize Firestore
        try:
            self.db = firestore.Client(project=self.project_id)
            self.collection = self.db.collection(self.collection_name)
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {str(e)}")
            raise
    
    def read_markdown(self, file_path: Path) -> str:
        """Read markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading markdown file {file_path}: {str(e)}")
            raise
    
    def read_pdf(self, file_path: Path) -> str:
        """Read PDF file and extract text."""
        try:
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error reading PDF file {file_path}: {str(e)}")
            raise
    
    def read_text(self, file_path: Path) -> str:
        """Read plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {str(e)}")
            raise
    
    def read_document(self, file_path: Path) -> str:
        """
        Read document based on file extension.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Document text content
        """
        suffix = file_path.suffix.lower()
        
        if suffix == '.md' or suffix == '.markdown':
            return self.read_markdown(file_path)
        elif suffix == '.pdf':
            return self.read_pdf(file_path)
        elif suffix == '.txt':
            return self.read_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text using Gemini.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            
            # Handle different response formats
            if isinstance(result, dict):
                embedding = result.get('embedding', [])
            else:
                embedding = getattr(result, 'embedding', None) or []
            
            if not embedding:
                raise ValueError("Empty embedding returned from API")
            
            return list(embedding) if not isinstance(embedding, list) else embedding
            
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise
    
    def ingest_document(
        self,
        file_path: Path,
        metadata: Optional[Dict] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> int:
        """
        Ingest a single document into Firestore.
        
        Args:
            file_path: Path to document file
            metadata: Optional metadata to attach to chunks
            chunk_size: Chunk size (defaults to settings)
            chunk_overlap: Chunk overlap (defaults to settings)
            
        Returns:
            Number of chunks created
        """
        logger.info(f"Processing document: {file_path}")
        
        # Read document
        text = self.read_document(file_path)
        text = sanitize_input(text)
        
        if not text or not text.strip():
            logger.warning(f"Document {file_path} is empty or contains no valid text")
            return 0
        
        # Chunk text
        chunks = chunk_text(
            text,
            chunk_size=chunk_size or settings.chunk_size,
            overlap=chunk_overlap or settings.chunk_overlap
        )
        
        logger.info(f"Created {len(chunks)} chunks from {file_path}")
        
        # Prepare metadata
        doc_metadata = {
            "source_file": str(file_path.name),
            "source_path": str(file_path),
            **(metadata or {})
        }
        
        # Process each chunk
        chunks_created = 0
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
                
                self.collection.add({
                    "text": chunk,
                    "embedding": embedding,
                    "metadata": chunk_metadata,
                    "created_at": firestore.SERVER_TIMESTAMP
                })
                
                chunks_created += 1
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(chunks)} chunks...")
                    
            except Exception as e:
                logger.error(f"Error processing chunk {i} from {file_path}: {str(e)}")
                continue
        
        logger.info(f"Successfully ingested {chunks_created} chunks from {file_path}")
        return chunks_created
    
    def ingest_directory(
        self,
        directory: Path,
        pattern: str = "*.{md,markdown,pdf,txt}",
        recursive: bool = True,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Ingest all documents in a directory.
        
        Args:
            directory: Directory path
            pattern: File pattern to match
            recursive: Whether to search recursively
            metadata: Optional metadata for all documents
            
        Returns:
            Total number of chunks created
        """
        directory = Path(directory)
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        
        # Find all matching files
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))
        
        logger.info(f"Found {len(files)} files to process in {directory}")
        
        total_chunks = 0
        for file_path in files:
            try:
                chunks = self.ingest_document(file_path, metadata=metadata)
                total_chunks += chunks
            except Exception as e:
                logger.error(f"Failed to ingest {file_path}: {str(e)}")
                continue
        
        logger.info(f"Total chunks created: {total_chunks}")
        return total_chunks


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Ingest documents into Firestore for RAG chatbot"
    )
    parser.add_argument(
        "input",
        type=str,
        help="Input file or directory path"
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Recursively process directories"
    )
    parser.add_argument(
        "--pattern",
        "-p",
        type=str,
        default="*.{md,markdown,pdf,txt}",
        help="File pattern to match (default: *.{md,markdown,pdf,txt})"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        help="Chunk size in characters (default: from config)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=None,
        help="Chunk overlap in characters (default: from config)"
    )
    parser.add_argument(
        "--metadata",
        type=str,
        help="Additional metadata as JSON string (e.g., '{\"source\": \"docs\"}')"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing collection before ingestion (USE WITH CAUTION)"
    )
    
    args = parser.parse_args()
    
    # Parse metadata if provided
    metadata = None
    if args.metadata:
        import json
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON metadata: {str(e)}")
            sys.exit(1)
    
    # Initialize ingester
    try:
        ingester = DocumentIngester()
    except Exception as e:
        logger.error(f"Failed to initialize ingester: {str(e)}")
        sys.exit(1)
    
    # Clear collection if requested
    if args.clear:
        logger.warning("Clearing existing collection...")
        try:
            count = 0
            for doc in ingester.collection.stream():
                doc.reference.delete()
                count += 1
            logger.info(f"Deleted {count} documents")
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            sys.exit(1)
    
    # Process input
    input_path = Path(args.input)
    
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)
    
    try:
        if input_path.is_file():
            # Process single file
            chunks = ingester.ingest_document(
                input_path,
                metadata=metadata,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap
            )
            logger.info(f"Successfully processed file: {chunks} chunks created")
        elif input_path.is_dir():
            # Process directory
            chunks = ingester.ingest_directory(
                input_path,
                pattern=args.pattern,
                recursive=args.recursive,
                metadata=metadata
            )
            logger.info(f"Successfully processed directory: {chunks} total chunks created")
        else:
            logger.error(f"Input path is neither a file nor directory: {input_path}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during ingestion: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

