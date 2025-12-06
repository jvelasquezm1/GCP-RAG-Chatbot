"""Firestore client for document storage and retrieval."""
import os
from typing import Optional, List, Dict, Any
from google.cloud import firestore
import logging

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


