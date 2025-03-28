"""
Answer Verifier module for verifying student answers against reference material.
"""
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

from ..document_processing.pdf_processor import PDFProcessor
from ..vector_storage.vector_store import VectorStore
from .qa_chain import QAChain
from ..image_processing.image_processor import ImageProcessor

class AnswerVerifier:
    """
    Main class for verifying student answers against reference material.
    """
    def __init__(self, 
                 vector_store_dir: str = "pinecone_index", 
                 qa_model: str = "gpt-3.5-turbo",
                 embedding_model: str = "text-embedding-3-large"):
        """
        Initialize the answer verifier.
        
        Args:
            vector_store_dir: Namespace for the Pinecone vector store
            qa_model: Name of the LLM model to use for QA
            embedding_model: Name of the embedding model to use
        """
        self.pdf_processor = PDFProcessor(embedding_model=embedding_model)
        self.vector_store = VectorStore(persist_directory=vector_store_dir, index_name="testverifier")
        self.qa_chain = QAChain(vector_store=self.vector_store, model_name=qa_model)
        self.image_processor = ImageProcessor()
        
    def process_pdfs(self, pdf_paths: List[str]) -> int:
        """
        Process PDF files and store them in the vector store.
        
        Args:
            pdf_paths: List of paths to PDF files
            
        Returns:
            Number of document chunks processed
        """
        # Process the PDFs
        documents = self.pdf_processor.process_multiple_pdfs(pdf_paths)
        
        # Add the documents to the vector store
        self.vector_store.add_documents(documents)
        
        return len(documents)
    
    def verify_answer(self, question: str, student_answer: str) -> Dict[str, Any]:
        """
        Verify a student's answer to a question.
        
        Args:
            question: The question
            student_answer: The student's answer
            
        Returns:
            Verification result with score and assessment
        """
        try:
            verification_result = self.qa_chain.verify_answer(question, student_answer)
            
            # Check if there was an error with the vector store
            if verification_result.startswith("Error:"):
                return {
                    "score": 0,
                    "verification": verification_result
                }
            
            # Parse the verification result
            lines = verification_result.strip().split('\n')
            score_line = next((line for line in lines if line.startswith("Score:")), "")
            score = int(score_line.replace("Score:", "").strip()) if score_line else 0
            
            return {
                "score": score,
                "verification": verification_result
            }
        except Exception as e:
            error_msg = str(e)
            if "No reference materials found" in error_msg:
                return {
                    "score": 0,
                    "verification": "Please upload PDF documents first before verifying answers."
                }
            else:
                return {
                    "score": 0,
                    "verification": f"Error verifying answer: {error_msg}"
                }
    
    def verify_answer_from_image(self, question: str, image_bytes: bytes) -> Dict[str, Any]:
        """
        Verify a student's answer from an image.
        
        Args:
            question: The question
            image_bytes: The image containing the student's answer
            
        Returns:
            Verification result with score and assessment
        """
        try:
            # Get relevant reference material for the question
            try:
                docs = self.vector_store.similarity_search(question)
                reference_material = "\n\n".join([doc.page_content for doc in docs])
            except ValueError:
                return {
                    "score": 0,
                    "verification": "Error: No reference materials found. Please upload PDF documents first."
                }
            
            # Analyze the image
            result = self.image_processor.analyze_image_with_vision_model(
                image_bytes=image_bytes,
                question=question,
                reference_material=reference_material
            )
            
            # Return the result with any additional data from the image processor
            return result
        except Exception as e:
            error_msg = str(e)
            if "No reference materials found" in error_msg:
                return {
                    "score": 0,
                    "verification": "Please upload PDF documents first before verifying answers."
                }
            else:
                return {
                    "score": 0,
                    "verification": f"Error verifying answer from image: {error_msg}"
                }
    
    def clear_vector_store(self) -> None:
        """
        Clear the vector store.
        """
        self.vector_store.clear()
