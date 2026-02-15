"""
Orthopedic Agent - Basic AI Agent using Google Gemini
"""
from typing import Dict

from opik import configure 
from opik.integrations.adk import OpikTracer, track_adk_agent_recursive

from google.adk.runners import Runner
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService

from app.agents.orthopedics.tools import getOrthopedicTools
from app.agents.orthopedics.prompt import getOrthopedicPrompt

# Singleton session service - persists across all requests
_session_service = InMemorySessionService()

# configure opik for log tracing
configure();

class OrthopedicAgent:
    """
    Basic AI agent powered by Google Gemini.
    Handles conversations and can be extended for orthopedic related tasks.
    """
    
    def __init__(self, user: Dict, session_id: str):
        """
        Initialize the Orthopedic Agent.
        
        Args:
            model: The Gemini model to use
        """
        self.agent_name = "orthopedic"
        self.model = "gemini-flash-latest"
        self.description = "Manages orthopedic related tasks including searching for orthopedic information, analyzing data, and performing custom computations."
        self.instructions = getOrthopedicPrompt()


        self.user = user
        self.session_id=session_id
    
    def get_llm_agent(self):
        """
        Get the orthopedic LLM agent.
        """

        # get orthopedic tools
        tools = getOrthopedicTools()
        
        return LlmAgent(
            name=self.agent_name,
            model=self.model,
            description=self.description,
            instruction=self.instructions,
            tools=tools,
        )

    async def get_agent(self):
        """
        Get the orthopedic agent.
        """

        user_id = self.user.get("id");

        if not user_id:
            raise ValueError("User ID is required")

        # create session
        session_service, session = await self.get_session(user_id, self.session_id)

        # create the agent
        llm_agent = await self.get_llm_agent();

        # opic tracer
        tracer = OpikTracer(
            name="orthopedic_agent",
            metadata={
                "user_id": user_id,
                "session_id": self.session_id,
            }
        );
        track_adk_agent_recursive(llm_agent, tracer);

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
                state={
                    "token": self.user.get("token"),
                    "user": self.user,
                }
            )
            
        return _session_service, session