import os
import json
import logging
from typing import Dict, Any, List, Optional
import base64
from io import BytesIO
import requests

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, SystemMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteriorDesignAgent:
    """
    Agent for interior design visualization and cost estimation.
    
    This agent can:
    1. Generate interior design images based on user requirements
    2. Allow modifications to the generated images
    3. Provide cost estimates for implementing designs shown in images
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the Interior Design Agent.
        
        Args:
            openai_api_key: OpenAI API key for generating designs and cost estimates
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=self.openai_api_key
        )
        
        # Initialize image generation model
        self.image_model = ChatOpenAI(
            model="gpt-4o-mini",
            max_tokens=1024,
            temperature=0.5,
            api_key=self.openai_api_key
        )
        
        # Initialize system prompts
        self.image_prompt = """
        You are an expert interior designer specializing in creating visual representations of interior designs.
        Based on the user's requirements, create a detailed DALL-E prompt that will generate a photorealistic
        interior design image. The prompt should include:
        
        - Room layout and dimensions
        - Furniture placement and specific items
        - Color schemes and materials
        - Lighting and ambiance
        - Style-specific details
        - Decorative elements
        
        Make the prompt detailed enough to generate a high-quality, realistic interior design image.
        """
        
        self.cost_system_prompt = """
        You are an expert interior designer and cost estimator.
        Based on the interior design image described, create a detailed cost breakdown.
        Include:
        - Furniture items with price ranges
        - Decor elements
        - Materials (flooring, paint, etc.)
        - Lighting fixtures
        - Labor costs for installation
        
        Provide both budget-friendly and premium options.
        Format the response as a structured table with components, descriptions, and cost ranges in INR.
        End with a total estimated cost range for both basic and premium options.
        """
    
    async def generate_design_image(self, room_type: str, style: str, requirements: str) -> Dict[str, Any]:
        """
        Generate an interior design image based on user requirements.
        
        Args:
            room_type: Type of room (e.g., living room, bedroom)
            style: Design style (e.g., contemporary, minimalist)
            requirements: Specific user requirements for the room
            
        Returns:
            Dictionary containing the image URL and prompt used
        """
        try:
            # Create prompt for DALL-E prompt generation
            dalle_prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.image_prompt),
                ("human", f"I want to design a {room_type} with {style} style. My requirements include: {requirements}. Create a DALL-E prompt to generate this image.")
            ])
            
            # Create chain for DALL-E prompt generation
            dalle_prompt_chain = dalle_prompt_template | self.llm | StrOutputParser()
            
            # Generate DALL-E prompt
            dalle_prompt = await dalle_prompt_chain.ainvoke({})
            
            # Call OpenAI API to generate image
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}"
                },
                json={
                    "model": "dall-e-3",
                    "prompt": dalle_prompt,
                    "n": 1,
                    "size": "1024x1024"
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Error generating image: {response.text}")
            
            # Extract image URL from response
            response_data = response.json()
            image_url = response_data["data"][0]["url"]
            
            return {
                "status": "success",
                "room_type": room_type,
                "style": style,
                "requirements": requirements,
                "prompt": dalle_prompt,
                "image_url": image_url
            }
        except Exception as e:
            logger.error(f"Error generating design image: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def modify_design_image(self, image_url: str, modifications: str) -> Dict[str, Any]:
        """
        Modify an existing interior design image based on user specifications.
        
        Args:
            image_url: URL of the existing image
            modifications: Specific modifications requested by the user
            
        Returns:
            Dictionary containing the new image URL
        """
        try:
            # Create prompt for modified DALL-E prompt
            modification_prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.image_prompt),
                ("human", f"I have an interior design image that I want to modify. The modifications I want are: {modifications}. Create a DALL-E prompt to generate this modified image.")
            ])
            
            # Create chain for modified DALL-E prompt
            modification_prompt_chain = modification_prompt_template | self.llm | StrOutputParser()
            
            # Generate modified DALL-E prompt
            modified_dalle_prompt = await modification_prompt_chain.ainvoke({})
            
            # Call OpenAI API to generate modified image
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}"
                },
                json={
                    "model": "dall-e-3",
                    "prompt": modified_dalle_prompt,
                    "n": 1,
                    "size": "1024x1024"
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Error modifying image: {response.text}")
            
            # Extract image URL from response
            response_data = response.json()
            new_image_url = response_data["data"][0]["url"]
            
            return {
                "status": "success",
                "modifications": modifications,
                "prompt": modified_dalle_prompt,
                "image_url": new_image_url
            }
        except Exception as e:
            logger.error(f"Error modifying design image: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def estimate_cost(self, image_url: str, room_type: str, style: str, requirements: str) -> Dict[str, Any]:
        """
        Estimate the cost of implementing a design shown in an image.
        
        Args:
            image_url: URL of the design image
            room_type: Type of room
            style: Design style
            requirements: Specific user requirements
            
        Returns:
            Dictionary containing the cost estimate breakdown
        """
        try:
            # Create messages for vision model
            messages = [
                {
                    "role": "system",
                    "content": self.cost_system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"This is a {style} {room_type} design with these requirements: {requirements}. Please provide a detailed cost estimate for implementing this design."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ]
            
            # Call OpenAI API directly for vision analysis
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "max_tokens": 1500
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Error estimating cost: {response.text}")
            
            # Extract cost estimate from response
            response_data = response.json()
            cost_estimate = response_data["choices"][0]["message"]["content"]
            
            return {
                "status": "success",
                "room_type": room_type,
                "style": style,
                "requirements": requirements,
                "cost_estimate": cost_estimate
            }
        except Exception as e:
            logger.error(f"Error estimating cost: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
