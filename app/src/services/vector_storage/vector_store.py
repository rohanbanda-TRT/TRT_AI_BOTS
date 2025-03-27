"""
Vector store module for managing document storage and retrieval.
"""
import os
from typing import List, Optional, Dict, Any
import uuid

from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from pinecone import Pinecone

class VectorStore:
    """
    Manages the vector store for document storage and retrieval.
    """
    def __init__(self, persist_directory: str = "pinecone_index"):
        """
        Initialize the vector store manager.
        
        Args:
            persist_directory: Directory name for the Pinecone index (used as namespace)
        """
        self.namespace = persist_directory
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.vector_store = None
        self.index_name = "testverifier"  # Using the existing index name
        
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