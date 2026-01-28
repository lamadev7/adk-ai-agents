"""
Dispatcher Agent - Basic AI Agent using Google Gemini
"""
from google import genai
from google.genai import types
from settings import settings


class DispatcherAgent:
    """
    Basic AI agent powered by Google Gemini.
    Handles conversations and can be extended for task dispatching.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize the Dispatcher Agent.
        
        Args:
            model: The Gemini model to use
        """
        self.model = model
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.system_instruction = """You are a helpful AI assistant. You provide clear, accurate, and concise responses. When you don't know something, you say so honestly."""
    
    def chat(self, message: str):
        """
        Chat with the dispatcher agent.
        
        Args:
            message: The message to chat with the agent
        """
        response = self.client.models.generate_content(
            model=self.model,
            contents=message,
        )
        return response.text