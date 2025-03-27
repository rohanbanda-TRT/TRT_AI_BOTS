"""
QA Chain module for answer verification.
"""
from typing import List, Dict, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

from ..vector_storage.vector_store import VectorStore

class QAChain:
    """
    Handles answer verification using LangChain.
    """
    def __init__(self, vector_store: VectorStore, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize the QA chain.
        
        Args:
            vector_store: Vector store for document retrieval
            model_name: Name of the LLM model to use
        """
        self.vector_store = vector_store
        self.llm = ChatOpenAI(model_name=model_name, temperature=0)
        
        # Create the answer verification chain
        self.verification_chain = self._create_verification_chain()
    
    def _create_verification_chain(self):
        """
        Create the answer verification chain using LCEL.
        
        Returns:
            The verification chain
        """
        # Define the verification prompt
        verification_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a teacher evaluating a student's answer to a question.
            
Question: {question}
Reference Material:
{context}

Student's Answer: {student_answer}

Evaluate the student's answer based on the reference material. Consider:
1. Factual accuracy
2. Completeness
3. Relevance to the question

Provide a detailed assessment and a score from 0-10, where:
0-3: Incorrect or mostly incorrect
4-6: Partially correct with significant gaps
7-8: Mostly correct with minor issues
9-10: Completely correct and comprehensive

Format your response as follows:
Score: [score]
Assessment: [your detailed assessment]
Correct Answer: [the correct answer based on the reference material]
"""),
            ("human", "Please evaluate the student's answer.")
        ])
        
        # Create the verification chain
        verification_chain = (
            {
                "context": lambda x: "\n\n".join([doc.page_content for doc in x["docs"]]),
                "question": lambda x: x["question"],
                "student_answer": lambda x: x["student_answer"]
            }
            | verification_prompt
            | self.llm
            | StrOutputParser()
        )
        
        return verification_chain
    
    def verify_answer(self, question: str, student_answer: str) -> str:
        """
        Verify a student's answer to a question.
        
        Args:
            question: The question
            student_answer: The student's answer
            
        Returns:
            Verification result
        """
        # Retrieve relevant documents
        try:
            docs = self.vector_store.similarity_search(question)
        except ValueError:
            # Handle case when vector store is empty
            return "Error: No reference materials found. Please upload PDF documents first."
        
        # Invoke the verification chain
        return self.verification_chain.invoke({
            "docs": docs,
            "question": question,
            "student_answer": student_answer
        })
