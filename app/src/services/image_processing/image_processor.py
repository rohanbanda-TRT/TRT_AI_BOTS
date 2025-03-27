"""
Image Processor module for analyzing answer sheet images using OpenAI's Vision model.
"""
import os
import base64
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import io

import pytesseract
from PIL import Image
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

class ImageProcessor:
    """
    Handles image processing and analysis for answer sheets.
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the image processor.
        
        Args:
            api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.vision_model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=1000,
            api_key=self.api_key
        )
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from an image using OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text
        """
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            raise ValueError(f"Error extracting text from image: {str(e)}")
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode an image to base64.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64-encoded image
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def encode_image_bytes_to_base64(self, image_bytes: bytes) -> str:
        """
        Encode image bytes to base64.
        
        Args:
            image_bytes: Image bytes
            
        Returns:
            Base64-encoded image
        """
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def analyze_image_with_vision_model(self, 
                                        image_path: Optional[str] = None, 
                                        image_bytes: Optional[bytes] = None,
                                        question: str = "",
                                        reference_material: str = "") -> Dict[str, Any]:
        """
        Analyze an answer sheet image using OpenAI's Vision model.
        
        Args:
            image_path: Path to the image file (optional if image_bytes is provided)
            image_bytes: Image bytes (optional if image_path is provided)
            question: The question being answered
            reference_material: Reference material to compare against
            
        Returns:
            Analysis result
        """
        if not image_path and not image_bytes:
            raise ValueError("Either image_path or image_bytes must be provided")
        
        # Encode the image
        if image_path:
            base64_image = self.encode_image_to_base64(image_path)
        else:
            base64_image = self.encode_image_bytes_to_base64(image_bytes)
        
        # Prepare the prompt
        prompt = f"""
You are a teacher evaluating a student's answer to a question.

Question: {question}

Reference Material:
{reference_material}

The image contains the student's handwritten or typed answer. Please:
1. Extract and transcribe the text from the image
2. Evaluate the answer based on the reference material
3. Consider factual accuracy, completeness, and relevance to the question
4. Provide a score from 0-10 and a detailed assessment

First, provide your evaluation in a readable format:
Transcribed Answer: [transcribed text from the image]
Score: [score]
Assessment: [your detailed assessment]
Correct Answer: [the correct answer based on the reference material]

Then, at the end of your response, provide a JSON summary in the following format (enclosed in triple backticks):
```json
{{
  "transcribed_answer": "The full transcribed text from the image",
  "score": [numeric score between 0-10],
  "assessment": "Your detailed assessment of the answer",
  "correct_answer": "The correct answer based on the reference material"
}}
```

Make sure the JSON is properly formatted and contains all the required fields.
"""
        
        # Call the Vision model
        try:
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            )
            
            response = self.vision_model.invoke([message])
            
            # Parse the response
            result_text = response.content
            
            # Extract JSON data if present
            json_data = self._extract_json_from_response(result_text)
            if json_data and "score" in json_data:
                score = json_data["score"]
                return {
                    "score": score,
                    "verification": result_text,
                    "json_data": json_data
                }
            
            # Fallback to text parsing if JSON extraction fails
            score_line = next((line for line in result_text.split('\n') if line.startswith("Score:")), "")
            score = int(score_line.replace("Score:", "").strip()) if score_line else 0
            
            return {
                "score": score,
                "verification": result_text
            }
            
        except Exception as e:
            raise ValueError(f"Error analyzing image: {str(e)}")
    
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
        
        return None
    
    def analyze_image_direct_api(self, 
                                image_path: Optional[str] = None, 
                                image_bytes: Optional[bytes] = None,
                                question: str = "",
                                reference_material: str = "") -> Dict[str, Any]:
        """
        Analyze an answer sheet image using direct OpenAI API call.
        
        Args:
            image_path: Path to the image file (optional if image_bytes is provided)
            image_bytes: Image bytes (optional if image_path is provided)
            question: The question being answered
            reference_material: Reference material to compare against
            
        Returns:
            Analysis result
        """
        if not image_path and not image_bytes:
            raise ValueError("Either image_path or image_bytes must be provided")
        
        # Encode the image
        if image_path:
            base64_image = self.encode_image_to_base64(image_path)
        else:
            base64_image = self.encode_image_bytes_to_base64(image_bytes)
        
        # Prepare the prompt
        prompt = f"""
You are a teacher evaluating a student's answer to a question.

Question: {question}

Reference Material:
{reference_material}

The image contains the student's handwritten or typed answer. Please:
1. Extract and transcribe the text from the image
2. Evaluate the answer based on the reference material
3. Consider factual accuracy, completeness, and relevance to the question
4. Provide a score from 0-10 and a detailed assessment

First, provide your evaluation in a readable format:
Transcribed Answer: [transcribed text from the image]
Score: [score]
Assessment: [your detailed assessment]
Correct Answer: [the correct answer based on the reference material]

Then, at the end of your response, provide a JSON summary in the following format (enclosed in triple backticks):
```json
{{
  "score": [numeric score between 0-10],
}}
```

Make sure the JSON is properly formatted and contains all the required fields.
"""
        
        # Call the OpenAI API directly
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "low"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            
            # Extract JSON data if present
            json_data = self._extract_json_from_response(result_text)
            if json_data and "score" in json_data:
                score = json_data["score"]
                return {
                    "score": score,
                    "verification": result_text,
                    "json_data": json_data
                }
            
            # Fallback to text parsing if JSON extraction fails
            score_line = next((line for line in result_text.split('\n') if line.startswith("Score:")), "")
            score = int(score_line.replace("Score:", "").strip()) if score_line else 0
            
            return {
                "score": score,
                "verification": result_text
            }
            
        except Exception as e:
            raise ValueError(f"Error analyzing image: {str(e)}")