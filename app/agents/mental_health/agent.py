"""
Mental Health Agent - Basic AI Agent using Google Gemini
"""
from typing import Dict

from opik import configure 
from opik.integrations.adk import OpikTracer 

from google.adk.runners import Runner
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService

from app.agents.mental_health.tools import getMentalHealthTools
from app.agents.mental_health.prompt import getMentalHealthPrompt
from app.agents.mental_health.sub_agents.index import getSubAgents

# Singleton session service - persists across all requests
_session_service = InMemorySessionService()

# configure opik for log tracing
configure();

class MentalHealthAgent:
    """
    Basic AI agent powered by Google Gemini.
    Handles conversations and can be extended for mental health related tasks.
    """
    
    def __init__(self, user: Dict, session_id: str):
        """
        Initialize the Mental Health Agent.
        
        Args:
            model: The Gemini model to use
        """
        self.agent_name = "mental_health"
        self.model = "gemini-flash-latest"
        self.description = "Manages mental health related tasks including searching for mental health information, analyzing data, and performing custom computations."
        self.instructions = getMentalHealthPrompt()


        self.user = user
        self.session_id=session_id
    
    async def get_agent(self):
        """
        Get the mental health agent.
        """

        user_id = self.user.get("id");

        if not user_id:
            raise ValueError("User ID is required")


        # opic tracer
        tracer = OpikTracer(
            name="mental_health_agent",
            metadata={
                "user_id": self.user.get("id"),
                "session_id": self.session_id,
            }
        );

        # create session
        session_service, session = await self.get_session(user_id, self.session_id)

        # get mental health tools
        tools = getMentalHealthTools()

        # sequence agent
        sub_agents = getSubAgents()
        
        # create the agent
        llm_agent = LlmAgent(
            name=self.agent_name,
            model=self.model,
            description=self.description,
            instruction=self.instructions,
            tools=tools,
            sub_agents=sub_agents,
            before_agent_callback=tracer.before_agent_callback,
            after_agent_callback=tracer.after_agent_callback,
            before_tool_callback=tracer.before_tool_callback,
            after_tool_callback=tracer.after_tool_callback,
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
                state={
                    "token": self.user.get("token"),
                    "user": self.user,
                }
            )
            
        return _session_service, session