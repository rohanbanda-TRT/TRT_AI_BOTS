"""
Video Transcription Agent for processing videos and answering questions based on transcriptions.
"""
import os
import logging
import uuid
import tempfile
from typing import Dict, Any, List, Optional
import whisper
import subprocess
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from ..prompts.video_transcription import VIDEO_TRANSCRIPTION_PROMPT
from ..utils.chat_history import InMemoryChatHistory

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class VideoTranscriptionAgent:
    """
    Agent for processing videos, extracting transcriptions, and answering questions.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.3):
        """
        Initialize the Video Transcription Agent.
        
        Args:
            model_name: The name of the OpenAI model to use
            temperature: The temperature setting for the model
        """
        # Initialize logging first to ensure it's available for all operations
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        try:
            self.logger.debug("Initializing Video Transcription Agent")
            self.model_name = model_name
            self.temperature = temperature
            self.whisper_model = None
            self.index_name = "video-transcriptions"
            self.dimension = 3072
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature
            )
            
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-large",
                dimensions=self.dimension
            )
            
            # Initialize Pinecone
            self._initialize_pinecone()
            
            # Create prompt template
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", VIDEO_TRANSCRIPTION_PROMPT),
                ("human", "Transcription: {transcription}\n\nQuestion: {question}")
            ])
            
            self.logger.info("Video Transcription Agent initialized")
        except Exception as e:
            self.logger.error("Error initializing Video Transcription Agent: %s", str(e))
            raise
    
    def _initialize_pinecone(self):
        """Initialize Pinecone vector store"""
        try:
            self.logger.debug("Initializing Pinecone with index: %s", self.index_name)
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            
            # Check if index exists
            indexes = [index.name for index in pc.list_indexes()]
            
            if self.index_name not in indexes:
                self.logger.info(f"Creating new Pinecone index: {self.index_name}")
                pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
            
            # Initialize vector store
            self.vector_store = PineconeVectorStore(
                index_name=self.index_name,
                embedding=self.embeddings
            )
            
            self.logger.info("Pinecone initialized with index: %s", self.index_name)
        except Exception as e:
            self.logger.error("Error initializing Pinecone: %s", str(e))
            raise
    
    def extract_audio(self, video_path: str, audio_path: str):
        """
        Extract audio from video file using ffmpeg.
        
        Args:
            video_path: Path to the video file
            audio_path: Path where the extracted audio will be saved
        """
        try:
            self.logger.debug("Extracting audio from video: %s", video_path)
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            command = [
                'ffmpeg', '-i', video_path,
                '-vn',  # Disable video
                '-acodec', 'pcm_s16le',  # Audio codec
                '-ar', '16000',  # Sample rate
                '-ac', '1',  # Mono audio
                '-y',  # Overwrite output
                audio_path
            ]
            
            subprocess.run(command, check=True, capture_output=True)
            self.logger.info("Audio extracted to %s", audio_path)
        except subprocess.CalledProcessError as e:
            self.logger.error("FFmpeg error: %s", e.stderr.decode())
            raise
        except Exception as e:
            self.logger.error("Error extracting audio: %s", str(e))
            raise
    
    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file using Whisper model.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcription text
        """
        try:
            self.logger.debug("Starting transcription for audio: %s", audio_path)
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Load model if not already loaded
            if self.whisper_model is None:
                self.whisper_model = whisper.load_model("base")
            
            result = self.whisper_model.transcribe(audio_path)
            transcription = result["text"]
            self.logger.info("Transcription completed for audio: %s", audio_path)
            return transcription
        except Exception as e:
            self.logger.error("Error in audio transcription: %s", str(e))
            raise
    
    def transcribe_video(self, video_path: str) -> str:
        """
        Process video to extract transcription.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Transcription text
        """
        try:
            self.logger.debug("Starting video transcription for: %s", video_path)
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                audio_path = temp_audio.name
            
            # Extract audio and transcribe
            self.extract_audio(video_path, audio_path)
            transcription = self.transcribe_audio(audio_path)
            
            # Clean up temporary file
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            self.logger.info("Transcription completed for video: %s", video_path)
            return transcription
            
        except Exception as e:
            self.logger.error("Error in video transcription: %s", str(e))
            raise
    
    def store_transcription(self, video_id: str, video_name: str, transcription: str) -> str:
        """
        Store transcription in Pinecone vector database.
        
        Args:
            video_id: Unique identifier for the video
            video_name: Name of the video file
            transcription: Transcription text
            
        Returns:
            ID of the stored document
        """
        try:
            self.logger.debug("Storing transcription for video: %s", video_name)
            # Create metadata
            metadata = {
                "video_id": video_id,
                "video_name": video_name,
                "source": "video_transcription"
            }
            
            # Store in vector database
            doc_id = f"video-{video_id}"
            self.vector_store.add_texts(
                texts=[transcription],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            self.logger.info("Transcription stored in Pinecone with ID: %s", doc_id)
            return doc_id
            
        except Exception as e:
            self.logger.error("Error storing transcription: %s", str(e))
            raise
    
    def retrieve_transcription(self, video_id: str) -> Optional[str]:
        """
        Retrieve transcription from Pinecone by video ID.
        
        Args:
            video_id: ID of the video
            
        Returns:
            Transcription text if found, None otherwise
        """
        try:
            self.logger.debug("Retrieving transcription for video ID: %s", video_id)
            doc_id = f"video-{video_id}"
            results = self.vector_store.similarity_search(
                query="",
                k=1,
                filter={"video_id": video_id}
            )
            
            if results and len(results) > 0:
                transcription = results[0].page_content
                self.logger.info("Transcription retrieved for video ID: %s", video_id)
                return transcription
            
            self.logger.warning("No transcription found for video ID: %s", video_id)
            return None
            
        except Exception as e:
            self.logger.error("Error retrieving transcription: %s", str(e))
            return None
    
    def similarity_search(self, question: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Perform similarity search on transcriptions.
        
        Args:
            question: Question to search for
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        try:
            self.logger.debug("Performing similarity search for question: %s", question)
            results = self.vector_store.similarity_search(
                query=question,
                k=k
            )
            
            self.logger.info("Similarity search completed with %d results", len(results))
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in results
            ]
            
        except Exception as e:
            self.logger.error("Error in similarity search: %s", str(e))
            return []
    
    async def process_video(self, video_path: str, video_name: str) -> Dict[str, Any]:
        """
        Process a video file to extract and store transcription.
        
        Args:
            video_path: Path to the video file
            video_name: Name of the video file
            
        Returns:
            Dictionary with processing results
        """
        try:
            self.logger.debug("Starting video processing for: %s", video_name)
            # Generate a unique ID for the video
            video_id = str(uuid.uuid4())
            
            # Transcribe the video
            transcription = self.transcribe_video(video_path)
            self.logger.info("Transcription completed for video: %s", video_name)
            
            # Store transcription in Pinecone
            doc_id = self.store_transcription(video_id, video_name, transcription)
            self.logger.info("Transcription stored for video: %s with document ID: %s", video_name, doc_id)
            
            return {
                "status": "success",
                "video_id": video_id,
                "video_name": video_name,
                "transcription": transcription,
                "document_id": doc_id
            }
            
        except Exception as e:
            self.logger.error("Error processing video: %s", str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def query_video(self, question: str, video_id: Optional[str] = None, conversation_id: str = None) -> Dict[str, Any]:
        """
        Answer a question based on video transcription.
        
        Args:
            question: Question to answer
            video_id: Optional ID of a specific video to query (not used, kept for backward compatibility)
            conversation_id: ID of the conversation
            
        Returns:
            Dictionary with query results
        """
        try:
            self.logger.debug("Starting query for question: %s", question)
            # Generate conversation ID if not provided
            if conversation_id is None:
                conversation_id = str(uuid.uuid4())
            
            # Add user message to history
            InMemoryChatHistory.add_message(conversation_id, "human", question)
            
            # Always perform similarity search across all transcriptions
            results = self.similarity_search(question, k=3)
            if not results:
                error_msg = "No relevant transcriptions found for your question."
                InMemoryChatHistory.add_message(conversation_id, "ai", error_msg)
                return {"answer": error_msg}
            
            # Combine the top results for better context
            combined_transcription = "\n\n".join([r["content"] for r in results])
            
            # Create chain
            chain = self.prompt | self.llm | StrOutputParser()
            
            # Generate answer
            answer = chain.invoke({
                "transcription": combined_transcription,
                "question": question
            })
            
            # Add AI response to history
            InMemoryChatHistory.add_message(conversation_id, "ai", answer)
            
            self.logger.info("Query completed for question: %s", question)
            return {
                "answer": answer,
                "conversation_id": conversation_id,
                "sources": [r["metadata"] for r in results]
            }
            
        except Exception as e:
            self.logger.error("Error querying video: %s", str(e))
            error_msg = f"Error processing your question: {str(e)}"
            InMemoryChatHistory.add_message(conversation_id, "ai", error_msg)
            return {"answer": error_msg}
