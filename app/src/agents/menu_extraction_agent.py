import os
import json
import logging
import base64
import requests
from typing import Dict, Any, List, Optional, Union

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool, StructuredTool, tool
from pydantic import BaseModel, Field
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_core.tools import Tool
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MenuExtractionAgent:
    """
    Agent for extracting and analyzing restaurant menu images.
    
    This agent can:
    1. Extract text from menu images using OpenAI's vision model
    2. Analyze the extracted text to provide structured menu data
    3. Answer questions about the menu
    4. Handle multiple images at once
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, api_url: str = "https://trt-demo-ai-bots.demotrt.com/api"):
        """
        Initialize the Menu Extraction Agent.
        
        Args:
            openai_api_key: OpenAI API key for vision and text analysis
            api_url: URL of the API server
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        self.api_url = api_url
        
        # Initialize LLM for text processing
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=self.openai_api_key
        )
        
        # Initialize vision model for image analysis
        self.vision_model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=self.openai_api_key
        )
        
        # Initialize memory for conversation history
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Define tools
        self.tools = self._create_tools()
        
        # Create agent with tools
        self.agent = self._create_agent()
        
        # Initialize system prompts
        self.menu_analysis_prompt = """
        You are an expert menu analyzer. Your task is to extract structured information from restaurant menu images.
        Analyze the text extracted from the menu image and provide a structured JSON output with the following information:
        
        1. Restaurant name (if available)
        2. Menu sections (e.g., Appetizers, Main Course, Desserts)
        3. Menu items within each section, including:
           - Name of the item
           - Description (if available)
           - Price
           - Any dietary information (vegetarian, vegan, gluten-free, etc.)
        
        Format your response as a valid JSON object with the following structure:
        {
            "restaurant_name": "Name of the restaurant",
            "menu_sections": [
                {
                    "section_name": "Name of the section",
                    "items": [
                        {
                            "name": "Name of the item",
                            "description": "Description of the item",
                            "price": "Price of the item",
                            "dietary_info": ["vegetarian", "gluten-free"]
                        }
                    ]
                }
            ]
        }
        
        If any information is not available, use null or an empty array as appropriate.
        """
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent to use."""
        
        def process_menu_images(image_urls: List[str]) -> Dict:
            """
            Process menu images and extract menu items
            """
            try:
                logging.info(f"Processing {len(image_urls)} menu images")
                
                if not image_urls:
                    return {"status": "error", "response": "No image URLs provided"}
                
                try:
                    # Create OpenAI client
                    openai_client = OpenAI(api_key=self.openai_api_key)
                    logger.info("OpenAI client created")
                    # Process each image to extract text
                    extracted_texts = []
                    
                    for image_url in image_urls:
                        logger.info(f"Processing image: {image_url}=====================================")
                        try:
                            # Fix potential URL format issues
                            # Remove any trailing period that might be causing the error
                            if image_url.endswith('.'):
                                image_url = image_url[:-1]
                                logger.info(f"Fixed URL by removing trailing period: {image_url}")
                            
                            # For pre-signed URLs, ensure they're properly handled
                            if '?' in image_url:
                                logger.info("Detected pre-signed URL")
                            
                            # Extract text using vision model
                            logger.info(f"Sending request to OpenAI with image URL: {image_url}")
                            messages = [
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": "Please extract all text from this restaurant menu image. Maintain the structure as much as possible."},
                                        {"type": "image_url", "image_url": {"url": image_url}},
                                    ],
                                }
                            ]
                            
                            # Log the full request being sent to OpenAI
                            logger.info("Sending OpenAI request with image URL")
                            
                            # Add timeout to OpenAI request
                            response = openai_client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=messages,
                                max_tokens=1500,
                                timeout=60  # Add timeout to prevent hanging
                            )
                            
                            extracted_text = response.choices[0].message.content
                            extracted_texts.append(extracted_text)
                            
                        except Exception as e:
                            error_message = f"Error extracting text from image {image_url}: {str(e)}"
                            logging.error(error_message)
                            raise Exception(f"Error extracting text from image: {str(e)}")
                    
                    # Combine all extracted texts into a single response
                    combined_text = "\n\n---\n\n".join(extracted_texts)
                    
                    return {
                        "status": "success",
                        "response": combined_text
                    }
                    
                except Exception as e:
                    logging.error(f"Error analyzing menu images: {str(e)}")
                    return {"status": "error", "response": str(e)}
            except Exception as e:
                logging.error(f"Error in process_menu_images: {str(e)}")
                return {"status": "error", "response": str(e)}
        
        # Store the process_menu_images function as an instance attribute
        self.process_menu_images = process_menu_images
        
        # Create a tool for the agent to use
        return [
            Tool(
                name="process_menu_images",
                func=process_menu_images,
                description="Process multiple menu images to extract structured menu information"
            )
        ]

    def _create_agent(self) -> AgentExecutor:
        """Create the agent executor with tools and memory."""
        
        # System prompt for the agent
        system_prompt = """
        You are a helpful restaurant menu assistant that can analyze menu images and answer questions about them.
        
        You can:
        1. Analyze menu images to extract structured information
        2. Answer questions about the menu based on the extracted information
        3. Provide recommendations based on the menu
        
        When analyzing a menu image, you'll extract information such as restaurant name, menu sections, 
        item names, descriptions, prices, and dietary information.
        
        Always be helpful, accurate, and concise in your responses.
        """
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("ai", "{agent_scratchpad}")
        ])
        
        # Create the agent
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        
        # Create the agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            memory=self.memory,
            max_iterations=3,
            early_stopping_method="generate"
        )
        
        return agent_executor
    
    async def process_query(self, query: str, image_urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Process a user query, optionally with menu images.
        
        Args:
            query: User's query
            image_urls: Optional list of menu image URLs to analyze
            
        Returns:
            Agent's response
        """
        try:
            # Only process images if they are provided and not empty
            if image_urls and len(image_urls) > 0:
                # Extract text and analyze menu
                menu_analysis = self.process_menu_images(image_urls)
                
                if "error" in menu_analysis:
                    return {
                        "status": "error",
                        "error": menu_analysis["error"]
                    }
                
                # Store menu data and raw text in memory
                self.memory.chat_memory.add_user_message(f"I've uploaded {len(image_urls)} menu image(s).")
                self.memory.chat_memory.add_ai_message("I've analyzed the menu images. You can now ask me questions about the menu.")
                
                # Return only status, response and raw_extracted_text (exclude menu_data)
                return {
                    "status": "success",
                    "response": "I've analyzed the menu images. You can now ask me questions about the menu.",
                    "raw_extracted_text": menu_analysis["response"]
                }
            else:
                # If no images provided, just process the query directly
                # Process the query using the agent
                response = self.agent.invoke({"input": query})
                
                return {
                    "status": "success",
                    "response": response["output"]
                }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
