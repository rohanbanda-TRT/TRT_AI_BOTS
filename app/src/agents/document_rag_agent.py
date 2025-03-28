"""
Document RAG Agent for querying documents using RAG (Retrieval Augmented Generation).
"""
import logging
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..services.vector_storage.vector_store import VectorStore
from ..utils.chat_history import InMemoryChatHistory
from ..services.document_processing.document_processors import load_and_split_document
from ..prompts.document_rag import DOCUMENT_RAG_PROMPT

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class DocumentRagAgent:
    """
    Agent for querying documents using RAG (Retrieval Augmented Generation).
    """
    
    def __init__(self, 
                 model_name: str = "gpt-4o-mini", 
                 vector_store_index: str = "document-index",
                 retrieval_k: int = 3):
        """
        Initialize the Document RAG Agent.
        
        Args:
            model_name: The name of the OpenAI model to use
            vector_store_index: The name of the vector store index
            retrieval_k: Number of documents to retrieve for each query
        """
        self.model_name = model_name
        self.vector_store_index = vector_store_index
        self.retrieval_k = retrieval_k
        self.llm = ChatOpenAI(model=model_name)
        self.vector_store = VectorStore(index_name=vector_store_index)
        
        # Create RAG prompt template
        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", DOCUMENT_RAG_PROMPT)
        ])

    def query(self, question: str, conversation_id: str) -> Dict[str, Any]:
        """
        Query the documents using RAG.
        
        Args:
            question: The question to answer
            conversation_id: The ID of the conversation
            
        Returns:
            Dict containing the answer and sources
        """
        try:
            # Add user message to history
            InMemoryChatHistory.add_message(conversation_id, "human", question)
            
            # Retrieve relevant documents
            docs = self.vector_store.similarity_search(question, k=self.retrieval_k)
            
            # Format context from retrieved documents
            context = ""
            sources = []
            
            if docs:
                context = "\n\n".join([f"Document: {doc.metadata.get('title', 'Unknown')}\nPage: {doc.metadata.get('page', 'N/A')}\nContent: {doc.page_content}" for doc in docs])
                
                # Format sources
                for doc in docs:
                    source = {
                        "title": doc.metadata.get("title", "Unknown"),
                        "document_id": doc.metadata.get("document_id", ""),
                        "page": doc.metadata.get("page", "N/A"),
                        "snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    }
                    sources.append(source)
            
            # Generate answer using RAG prompt
            chain = self.rag_prompt | self.llm
            answer = chain.invoke({"context": context, "question": question})
            
            # Add AI response to history
            InMemoryChatHistory.add_message(conversation_id, "ai", answer.content)
            
            return {
                "answer": answer.content,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Error querying documents: {str(e)}")
            error_message = f"An error occurred while processing your query: {str(e)}"
            InMemoryChatHistory.add_message(conversation_id, "ai", error_message)
            return {"answer": error_message, "sources": []}
    
    def process_document(self, file_path: str, document_id: str, title: str) -> Dict[str, Any]:
        """
        Process and index a document.
        
        Args:
            file_path: Path to the document file
            document_id: Unique ID for the document
            title: Title of the document
            
        Returns:
            Dict containing status and metadata
        """
        try:
            # Load and split document
            chunks = load_and_split_document(file_path)
            
            if not chunks:
                return {
                    "status": "error",
                    "message": "No content could be extracted from the document"
                }
            
            # Add metadata to chunks
            for chunk in chunks:
                chunk.metadata["document_id"] = document_id
                chunk.metadata["title"] = title
            
            # Index chunks to vector store
            self.vector_store.add_documents(chunks)
            
            return {
                "status": "success",
                "document_id": document_id,
                "title": title,
                "chunk_count": len(chunks)
            }
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing document: {str(e)}"
            }
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete a document from the vector store.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            Dict containing status and message
        """
        try:
            # Check if document exists
            exists, _ = self.vector_store.check_document_exists(document_id)
            
            if not exists:
                return {
                    "status": "error",
                    "message": f"Document with ID {document_id} not found"
                }
            
            # Delete document
            self.vector_store.delete_document(document_id)
            
            return {
                "status": "success",
                "message": f"Document with ID {document_id} deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return {
                "status": "error",
                "message": f"Error deleting document: {str(e)}"
            }
    
    def list_documents(self) -> Dict[str, Any]:
        """
        List all documents in the vector store.
        
        Returns:
            Dict containing status and list of documents
        """
        try:
            # Get unique documents from vector store
            documents = self.vector_store.list_documents()
            
            return {
                "status": "success",
                "documents": documents
            }
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return {
                "status": "error",
                "message": f"Error listing documents: {str(e)}",
                "documents": []
            }
