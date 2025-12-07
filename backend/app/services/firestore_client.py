"""Firestore client for document storage and retrieval."""
import os
from typing import Optional, List, Dict, Any, Tuple
from google.cloud import firestore
import logging
import math

logger = logging.getLogger(__name__)


class FirestoreClient:
    """Client for interacting with Firestore database."""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        """
        Initialize Firestore client.
        
        Args:
            project_id: GCP project ID (defaults to GCP_PROJECT_ID env var)
            collection_name: Firestore collection name (defaults to FIRESTORE_COLLECTION env var)
            
        Raises:
            ValueError: If project_id is not provided
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        
        self.collection_name = collection_name or os.getenv("FIRESTORE_COLLECTION", "documents")
        
        try:
            # Initialize Firestore client
            # When running on GCP (Cloud Run), it will use default credentials
            # For local development, use: gcloud auth application-default login
            self.db = firestore.Client(project=self.project_id)
            self.collection = self.db.collection(self.collection_name)
            logger.info(f"Firestore client initialized for project: {self.project_id}, collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {str(e)}")
            raise
    
    def get_document_count(self) -> int:
        """
        Get the total number of documents in the collection.
        
        Returns:
            Number of documents in the collection
        """
        try:
            # Count documents (this may be expensive for large collections)
            # For better performance, consider maintaining a counter document
            docs = list(self.collection.stream())
            return len(docs)
        except Exception as e:
            logger.error(f"Error counting documents: {str(e)}")
            raise
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by its ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data as dictionary, or None if not found
        """
        try:
            doc_ref = self.collection.document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {str(e)}")
            raise
    
    def add_document(self, data: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """
        Add a document to the collection.
        
        Args:
            data: Document data as dictionary
            doc_id: Optional document ID (auto-generated if not provided)
            
        Returns:
            Document ID
        """
        try:
            if doc_id:
                doc_ref = self.collection.document(doc_id)
                doc_ref.set(data)
                return doc_id
            else:
                # Auto-generate document ID
                doc_ref = self.collection.add(data)
                return doc_ref[1].id
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            raise
    
    def query_documents(
        self,
        filters: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents from the collection.
        
        Args:
            filters: List of filter tuples (field, operator, value)
                     e.g., [("metadata.source", "==", "docs")]
            limit: Maximum number of documents to return
            order_by: Field name to order by
            
        Returns:
            List of document dictionaries
        """
        try:
            query = self.collection
            
            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            # Apply ordering
            if order_by:
                query = query.order_by(order_by)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Execute query
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error querying documents: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test Firestore connection by attempting a simple operation.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to access the collection (doesn't require reading documents)
            # This will fail if credentials are invalid or project doesn't exist
            _ = self.collection.limit(1).stream()
            return True
        except Exception as e:
            logger.warning(f"Firestore connection test failed: {str(e)}")
            return False
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have the same length")
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def search_similar_documents(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        max_documents: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query embedding using cosine similarity.
        
        Note: Firestore doesn't have native vector search, so this method:
        1. Retrieves documents from Firestore (up to max_documents)
        2. Calculates cosine similarity for each document
        3. Returns top_k most similar documents
        
        For production use with large collections, consider using a dedicated
        vector database or implementing a more efficient search strategy.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top similar documents to return
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            max_documents: Maximum number of documents to retrieve for comparison
                          (None = retrieve all documents, use with caution)
            
        Returns:
            List of document dictionaries with similarity scores, sorted by similarity
            Each document includes a 'similarity' field
        """
        try:
            # Retrieve documents from Firestore
            query = self.collection
            
            # Limit documents retrieved for performance
            # In production, you'd want to use a proper vector database
            if max_documents:
                query = query.limit(max_documents)
            
            docs = query.stream()
            
            # Calculate similarity for each document
            scored_docs = []
            for doc in docs:
                doc_data = doc.to_dict()
                
                # Skip documents without embeddings
                if 'embedding' not in doc_data or not doc_data['embedding']:
                    continue
                
                doc_embedding = doc_data['embedding']
                
                # Calculate cosine similarity
                similarity = self.cosine_similarity(query_embedding, doc_embedding)
                
                # Filter by threshold
                if similarity >= similarity_threshold:
                    # Add similarity score and document ID to result
                    result_doc = {
                        **doc_data,
                        'similarity': similarity,
                        'doc_id': doc.id
                    }
                    scored_docs.append(result_doc)
            
            # Sort by similarity (descending) and return top_k
            scored_docs.sort(key=lambda x: x['similarity'], reverse=True)
            
            return scored_docs[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {str(e)}")
            raise


