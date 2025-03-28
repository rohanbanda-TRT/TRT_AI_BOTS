"""
Vector store module for managing document storage and retrieval.
"""
import os
from typing import List, Optional, Dict, Any, Tuple
import uuid

from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from pinecone import Pinecone

class VectorStore:
    """
    Manages the vector store for document storage and retrieval.
    """
    def __init__(self, persist_directory: str = "pinecone_index", index_name: str = "document-index"):
        """
        Initialize the vector store manager.
        
        Args:
            persist_directory: Directory name for the Pinecone index (used as namespace)
            index_name: Name of the Pinecone index to use
        """
        self.namespace = persist_directory
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.vector_store = None
        self.index_name = index_name
        
        # Initialize Pinecone client
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        
        self.pc = Pinecone(api_key=api_key)
        
        # Load the existing index
        self._load_index()
    
    def _load_index(self) -> None:
        """
        Load the existing Pinecone index.
        """
        try:
            # Check if index exists
            indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in indexes:
                raise ValueError(f"Index '{self.index_name}' does not exist in your Pinecone account")
            
            # Get the index
            index = self.pc.Index(self.index_name)
            
            # Create the vector store
            self.vector_store = PineconeVectorStore(
                index=index,
                embedding=self.embeddings,
                namespace=self.namespace
            )
        except Exception as e:
            raise ValueError(f"Error initializing Pinecone: {str(e)}")
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized")
        
        # Add documents to the vector store
        self.vector_store.add_documents(documents)
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """
        Perform a similarity search on the vector store.
        
        Args:
            query: The query string
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Add documents first.")
        
        return self.vector_store.similarity_search(query, k=k)
    
    def clear(self) -> None:
        """
        Clear the vector store.
        """
        if self.vector_store is not None:
            # Delete all vectors in the namespace
            index = self.pc.Index(self.index_name)
            index.delete(delete_all=True, namespace=self.namespace)
            
            # Reinitialize the vector store
            self._load_index()
    
    def check_document_exists(self, document_id: str) -> Tuple[bool, List[str]]:
        """
        Check if a document with the specified document_id exists in the vector store
        
        Args:
            document_id: The ID of the document to check
            
        Returns:
            tuple: (exists, vector_ids) - Boolean indicating if document exists and list of vector IDs if found
        """
        try:
            if not self.vector_store:
                return False, []
            
            # Get the Pinecone index
            index = self.pc.Index(self.index_name)
            
            # Query for vectors with matching document_id
            # For serverless Pinecone, we need to use a different approach
            # First, get all vectors in the namespace
            stats = index.describe_index_stats()
            
            # If no vectors in the namespace, document doesn't exist
            if stats.namespaces.get(self.namespace, {}).get('vector_count', 0) == 0:
                return False, []
            
            # Use embedding of document_id as a dummy query
            query_embedding = self.embeddings.embed_query(f"document_id:{document_id}")
            
            # Query with high top_k to get many results
            query_results = index.query(
                vector=query_embedding,
                top_k=100,  # Adjust based on expected max chunks per document
                namespace=self.namespace,
                include_metadata=True
            )
            
            # Filter results to find matches with the document_id
            matching_ids = []
            for match in query_results.matches:
                if match.metadata and match.metadata.get('document_id') == document_id:
                    matching_ids.append(match.id)
            
            return len(matching_ids) > 0, matching_ids
        except Exception as e:
            print(f"Error checking if document exists: {str(e)}")
            return False, []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all document chunks with specified document_id from the vector store
        
        Args:
            document_id: The ID of the document to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            if not self.vector_store:
                return False
            
            # Check if document exists and get vector IDs
            exists, vector_ids = self.check_document_exists(document_id)
            
            if not exists or not vector_ids:
                return False
            
            # Get the Pinecone index
            index = self.pc.Index(self.index_name)
            
            # Delete vectors by ID
            index.delete(ids=vector_ids, namespace=self.namespace)
            
            return True
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            return False
            
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all unique documents in the vector store
        
        Returns:
            List of document metadata (document_id, title)
        """
        try:
            if not self.vector_store:
                return []
            
            # Get the Pinecone index
            index = self.pc.Index(self.index_name)
            
            # Use a dummy query to get results
            query_embedding = self.embeddings.embed_query("list all documents")
            
            # Query with high top_k to get many results
            query_results = index.query(
                vector=query_embedding,
                top_k=1000,  # Adjust based on expected number of documents
                namespace=self.namespace,
                include_metadata=True
            )
            
            # Extract unique documents
            document_map = {}
            for match in query_results.matches:
                if match.metadata and 'document_id' in match.metadata and 'title' in match.metadata:
                    doc_id = match.metadata['document_id']
                    if doc_id not in document_map:
                        document_map[doc_id] = {
                            'document_id': doc_id,
                            'title': match.metadata['title']
                        }
            
            # Convert to list
            documents = list(document_map.values())
            return documents
        except Exception as e:
            print(f"Error listing documents: {str(e)}")
            return []