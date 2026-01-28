"""
Dispatcher Agent - Basic AI Agent using Google Gemini
"""
from typing import Dict
from google.adk.runners import Runner
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService

# Singleton session service - persists across all requests
_session_service = InMemorySessionService()

class DispatcherAgent:
    """
    Basic AI agent powered by Google Gemini.
    Handles conversations and can be extended for task dispatching.
    """
    
    def __init__(self, user: Dict, session_id: str):
        """
        Initialize the Dispatcher Agent.
        
        Args:
            model: The Gemini model to use
        """
        self.agent_name = "dispatcher"
        self.model = "gemini-flash-latest"
        self.description = "You are a helpful AI assistant. You provide clear, accurate, and concise responses. When you don't know something, you say so honestly."


        self.user = user
        self.session_id=session_id
    
    async def get_agent(self):
        """
        Get the dispatcher agent.
        """

        user_id = self.user.get("id");

        if not user_id:
            raise ValueError("User ID is required")

        # create session
        session_service, session = await self.get_session(user_id, self.session_id)
        
        # create the agent
        llm_agent = LlmAgent(
            name=self.agent_name,
            model=self.model,
            description=self.description,
        )

        # running the agent
        runner = Runner(
            app_name=self.agent_name,
            agent=llm_agent,
            session_service=session_service,
        )

        return runner, session
    
    async def get_session(self, user_id: str, session_id: str):
        """
        Get the session.
        """
        session = await _session_service.get_session(
            app_name=self.agent_name,
            user_id=user_id,
            session_id=session_id,
        )
        if not session:
            print(f"Creating session for user {user_id} and session {session_id}")
            session = await _session_service.create_session(
                app_name=self.agent_name,
                user_id=user_id,
                session_id=session_id,
            )
            
        return _session_service, session