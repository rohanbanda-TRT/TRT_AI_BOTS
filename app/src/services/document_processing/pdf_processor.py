"""
PDF Processor module for loading, chunking, and storing PDF documents.
"""
import os
from typing import List, Dict, Any
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

class PDFProcessor:
    """
    Handles PDF document processing, including loading, chunking, and storing in a vector database.
    """
    def __init__(self, embedding_model: str = "text-embedding-3-large"):
        """
        Initialize the PDF processor with the specified embedding model.
        
        Args:
            embedding_model: The OpenAI embedding model to use
        """
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vector_store = None
        
    def process_pdf(self, pdf_path: str) -> List[Document]:
        """
        Process a PDF file by loading and chunking it.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of document chunks
        """
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)
        return chunks
    
    def process_multiple_pdfs(self, pdf_paths: List[str]) -> List[Document]:
        """
        Process multiple PDF files.
        
        Args:
            pdf_paths: List of paths to PDF files
            
        Returns:
            List of document chunks from all PDFs
        """
        all_chunks = []
        for pdf_path in pdf_paths:
            chunks = self.process_pdf(pdf_path)
            all_chunks.extend(chunks)
        return all_chunks
    
    def create_vector_store(self, documents: List[Document], persist_directory: str = None) -> Any:
        """
        Create a vector store from the document chunks.
        
        Args:
            documents: List of document chunks
            persist_directory: Directory to persist the vector store (optional)
            
        Returns:
            FAISS vector store
        """
        if persist_directory:
            # Create the directory if it doesn't exist
            os.makedirs(persist_directory, exist_ok=True)
            
            # Create and save the vector store
            self.vector_store = FAISS.from_documents(
                documents, 
                self.embeddings
            )
            self.vector_store.save_local(persist_directory)
        else:
            # Create in-memory vector store
            self.vector_store = FAISS.from_documents(
                documents, 
                self.embeddings
            )
        
        return self.vector_store
    
    def load_vector_store(self, persist_directory: str) -> Any:
        """
        Load a vector store from a directory.
        
        Args:
            persist_directory: Directory where the vector store is persisted
            
        Returns:
            FAISS vector store
        """
        if os.path.exists(persist_directory):
            self.vector_store = FAISS.load_local(
                persist_directory, 
                self.embeddings
            )
            return self.vector_store
        else:
            raise FileNotFoundError(f"Vector store not found at {persist_directory}")
    
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
            raise ValueError("Vector store not initialized. Process documents first.")
        
        return self.vector_store.similarity_search(query, k=k)
