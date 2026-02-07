"""Gemini AI client using LangChain for content summarization."""

import os
from typing import Optional
from pathlib import Path
import logging
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Gemini API interactions using LangChain."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client with LangChain.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            logger.warning("Gemini API key not found. AI summarization will be disabled.")
            self.enabled = False
            return
        
        try:
            # Initialize LangChain Gemini model
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=self.api_key,
                temperature=0.3,  # Lower temperature for more focused summaries
                convert_system_message_to_human=True
            )
            
            # For vision tasks (images)
            self.vision_llm = ChatGoogleGenerativeAI(
                model="gemini-pro-vision",
                google_api_key=self.api_key,
                temperature=0.3,
                convert_system_message_to_human=True
            )
            
            self.enabled = True
            logger.info("Gemini AI client initialized successfully with LangChain")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.enabled = False
    
    def summarize_table(self, csv_data: str, caption: Optional[str] = None) -> Optional[str]:
        """
        Generate a summary of table data using LangChain.
        
        Args:
            csv_data: Table data in CSV format
            caption: Optional table caption
            
        Returns:
            Summary text or None if failed
        """
        if not self.enabled:
            return None
        
        try:
            # Truncate CSV if too long
            if len(csv_data) > 10000:
                csv_data = csv_data[:10000] + "\n... (truncated)"
            
            system_msg = "You are a data analyst expert at summarizing tabular data."
            user_msg = f"""Analyze the following table data and provide a concise summary (2-3 sentences) 
highlighting the key information, trends, or insights.

{f'Table Caption: {caption}' if caption else ''}

Table Data (CSV format):
{csv_data}

Provide a clear, concise summary:"""
            
            messages = [
                SystemMessage(content=system_msg),
                HumanMessage(content=user_msg)
            ]
            
            response = self.llm.invoke(messages)
            summary = response.content.strip()
            logger.info(f"Generated table summary: {summary[:100]}...")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate table summary: {e}")
            return None
    
    def describe_image(self, image_path: str, caption: Optional[str] = None) -> Optional[str]:
        """
        Generate a description of an image using LangChain.
        
        Args:
            image_path: Path to the image file
            caption: Optional image caption
            
        Returns:
            Description text or None if failed
        """
        if not self.enabled:
            return None
        
        try:
            from PIL import Image
            import base64
            from io import BytesIO
            
            # Load and encode image
            image = Image.open(image_path)
            
            # Convert to base64
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            prompt = f"""Describe this image in 2-3 sentences. Focus on the main content, 
any text visible, charts/graphs, or key visual elements.

{f'Image Caption: {caption}' if caption else ''}

Provide a clear description:"""
            
            # Note: LangChain's vision support may vary
            # For now, we'll use a text-based approach
            # In production, you might want to use the Vision API directly
            
            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/png;base64,{img_base64}"
                        }
                    ]
                )
            ]
            
            response = self.vision_llm.invoke(messages)
            description = response.content.strip()
            logger.info(f"Generated image description: {description[:100]}...")
            return description
            
        except Exception as e:
            logger.error(f"Failed to generate image description: {e}")
            # Fallback: return basic info
            return f"Image file: {Path(image_path).name}"
    
    def summarize_document(self, text: str, max_length: int = 500) -> Optional[str]:
        """
        Generate a summary of document text using LangChain.
        
        Args:
            text: Document text to summarize
            max_length: Maximum length of summary in words
            
        Returns:
            Summary text or None if failed
        """
        if not self.enabled:
            return None
        
        try:
            # Truncate text if too long
            if len(text) > 30000:
                text = text[:30000] + "..."
            
            system_msg = "You are an expert at summarizing documents concisely and accurately."
            user_msg = f"""Provide a comprehensive summary of the following document text 
in approximately {max_length} words. Focus on the main topics, key points, and conclusions.

Document Text:
{text}

Summary:"""
            
            messages = [
                SystemMessage(content=system_msg),
                HumanMessage(content=user_msg)
            ]
            
            response = self.llm.invoke(messages)
            summary = response.content.strip()
            logger.info(f"Generated document summary: {summary[:100]}...")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate document summary: {e}")
            return None


# Global client instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create global Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
