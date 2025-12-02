"""Gemini API client for LLM interactions."""
import os
import google.generativeai as genai
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
    
    def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a response using Gemini LLM.
        
        Args:
            prompt: The prompt to send to the model
            system_instruction: Optional system instruction (prepended to prompt)
            temperature: Sampling temperature (0.0-1.0)
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If API call fails
        """
        try:
            # Configure generation config as a dictionary
            generation_config = {
                "temperature": temperature,
            }
            
            # Build the full prompt with system instruction if provided
            # Note: system_instruction is not supported as a constructor parameter
            # in google-generativeai 0.3.1, so we include it in the prompt
            if system_instruction:
                full_prompt = f"{system_instruction}\n\nUser: {prompt}\nAssistant:"
            else:
                full_prompt = prompt
            
            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini API")
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

