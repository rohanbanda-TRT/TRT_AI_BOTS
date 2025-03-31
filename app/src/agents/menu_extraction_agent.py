"""
Menu Extraction Agent for analyzing menu images and extracting structured data.
"""
import logging
import base64
import os
import json
import re
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import io

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferMemory
from ..utils.chat_history import InMemoryChatHistory
from ..services.image_processing.image_processor import ImageProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# System prompt for menu extraction
MENU_EXTRACTION_PROMPT = """
You are a specialized AI assistant that helps users extract and understand menu items from restaurant menus.

Your capabilities:
1. Extract menu items, prices, descriptions, and categories from menu images
2. Organize menu data into structured JSON format
3. Answer questions about menu items, prices, and categories
4. Maintain a conversational memory to reference previously extracted menus

When analyzing a menu image:
- Extract all menu items with their names, prices, descriptions (if available), and categories
- Identify special items, daily specials, or chef's recommendations
- Note dietary information (vegetarian, vegan, gluten-free, etc.) when specified
- Organize items by categories (appetizers, mains, desserts, etc.)
- Handle different currencies and price formats
- Return the data in a structured JSON format with the following schema:
```json
{
  "restaurant_name": "Name if visible in the menu",
  "menu_categories": [
    {
      "category_name": "Category Name",
      "items": [
        {
          "name": "Item Name",
          "price": "Price",
          "description": "Description if available",
          "dietary_info": ["vegetarian", "gluten-free", etc.] if specified
        }
      ]
    }
  ]
}
```

When answering questions:
- Reference previously extracted menu data
- Provide accurate information about prices and descriptions
- Be helpful and conversational
- If information is not available, acknowledge that and offer to help with what is known

Always maintain a professional, helpful tone and provide accurate information based on the menu data.
"""

class MenuExtractionAgent:
    """
    Agent for extracting and analyzing menu data from images.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.2):
        """
        Initialize the Menu Extraction Agent.
        
        Args:
            model_name: The name of the OpenAI model to use
            temperature: The temperature setting for the model
        """
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=1500,
            verbose=True
        )
        
        # Create system prompt
        self.system_prompt = SystemMessage(content=MENU_EXTRACTION_PROMPT)
        
        # Initialize image processor
        self.image_processor = ImageProcessor()
    
    async def chat(self, message: str, conversation_id: str) -> Dict[str, Any]:
        """
        Process a user message and return an AI-generated response.
        
        Args:
            message: The user's message
            conversation_id: The ID of the conversation
            
        Returns:
            Dict containing the answer
        """
        try:
            # Get conversation history
            history = InMemoryChatHistory.get_history(conversation_id)
            
            # Create messages with history and the new message
            messages = [self.system_prompt]
            
            # Add history messages
            for msg in history:
                if msg["type"] == "human":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["type"] == "ai":
                    messages.append(AIMessage(content=msg["content"]))
            
            # Add the new message
            messages.append(HumanMessage(content=message))
            
            # Add user message to history
            InMemoryChatHistory.add_message(conversation_id, "human", message)
            
            # Get response from the LLM
            response = await self.llm.ainvoke(messages)
            answer = response.content
            
            # Add AI response to history
            InMemoryChatHistory.add_message(conversation_id, "ai", answer)
            
            return {
                "answer": answer
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            error_message = f"An error occurred while processing your message: {str(e)}"
            InMemoryChatHistory.add_message(conversation_id, "ai", error_message)
            return {"answer": error_message}
    
    async def extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Extract text from an image using the vision model.
        
        Args:
            image_bytes: The image bytes
            
        Returns:
            Extracted text from the image
        """
        try:
            # Encode the image to base64
            base64_image = self.image_processor.encode_image_bytes_to_base64(image_bytes)
            
            # Create a message with just the image for text extraction
            image_message = HumanMessage(
                content=[
                    {"type": "text", "text": "Extract all text from this image."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            )
            
            # Get response from the LLM
            response = await self.llm.ainvoke([image_message])
            extracted_text = response.content
            
            return extracted_text
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            return f"Error extracting text: {str(e)}"
    
    async def analyze_menu_images(self, image_bytes_list: List[bytes], conversation_id: str) -> Dict[str, Any]:
        """
        Analyze multiple menu images and extract structured data.
        
        Args:
            image_bytes_list: List of image bytes
            conversation_id: The ID of the conversation
            
        Returns:
            Dict containing the extracted menu data and analysis
        """
        try:
            # Extract text from all images
            extracted_texts = []
            for i, image_bytes in enumerate(image_bytes_list):
                text = await self.extract_text_from_image(image_bytes)
                extracted_texts.append(f"--- IMAGE {i+1} ---\n{text}")
            
            # Combine all extracted texts
            combined_text = "\n\n".join(extracted_texts)
            
            # Add a message to history about the image uploads
            InMemoryChatHistory.add_message(
                conversation_id, 
                "human", 
                f"I've uploaded {len(image_bytes_list)} menu image(s) for analysis."
            )
            
            # Get conversation history
            history = InMemoryChatHistory.get_history(conversation_id)
            
            # Create messages with history
            messages = [self.system_prompt]
            
            # Add history messages (excluding the last one which we just added)
            for msg in history[:-1]:
                if msg["type"] == "human":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["type"] == "ai":
                    messages.append(AIMessage(content=msg["content"]))
            
            # Prepare the prompt for menu extraction using the extracted text
            prompt = f"""
I've extracted text from {len(image_bytes_list)} menu image(s). Here's the extracted content:

{combined_text}

Based on this extracted text, please:
1. Identify the restaurant name if available
2. Extract all menu items, prices, and descriptions
3. Organize them by categories (appetizers, mains, desserts, etc.)
4. Format the data as a structured JSON with the format specified in your instructions
5. Provide a brief summary of the menu (cuisine type, price range, etc.)

Please ensure the JSON is properly formatted and contains all the information from the extracted text.
"""
            
            # Add the prompt as a new message
            messages.append(HumanMessage(content=prompt))
            
            # Get response from the LLM
            response = await self.llm.ainvoke(messages)
            answer = response.content
            
            # Extract JSON data if present
            json_data = self._extract_json_from_response(answer)
            
            # Add AI response to history
            InMemoryChatHistory.add_message(conversation_id, "ai", answer)
            
            return {
                "answer": answer,
                "menu_data": json_data,
                "extracted_text": combined_text
            }
        except Exception as e:
            logger.error(f"Error analyzing menu images: {str(e)}")
            error_message = f"An error occurred while analyzing the menu images: {str(e)}"
            InMemoryChatHistory.add_message(conversation_id, "ai", error_message)
            return {"answer": error_message, "menu_data": None, "extracted_text": ""}
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON data from the response text.
        
        Args:
            response_text: The response text
            
        Returns:
            Extracted JSON data or None if not found
        """
        import json
        import re
        
        # Look for JSON between triple backticks
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(1)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # If no JSON found between backticks, try to find a JSON object in the text
        try:
            # Find anything that looks like a JSON object
            json_match = re.search(r'({[\s\S]*})', response_text)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        return None
