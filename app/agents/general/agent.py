"""
General Agent (Orchestrator) - Routes user queries to the appropriate specialist agent
"""
from typing import Dict

from opik import configure
from opik.integrations.adk import OpikTracer, track_adk_agent_recursive

from google.adk.runners import Runner
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService

# Import specialist agents' tools and prompts
from app.agents.orthopedics import OrthopedicAgent
from app.agents.mental_health import MentalHealthAgent
from app.agents.general.prompt import getOrchestratorPrompt

# Singleton session service - persists across all requests
_session_service = InMemorySessionService()

# configure opik for log tracing
configure()


class GeneralAgent:
    """
    Orchestrator Agent powered by Google Gemini.
    Analyzes user queries and routes them to the appropriate specialist agent:
    - mental_health_agent: For anxiety, depression, stress, sleep issues, etc.
    - orthopedics_agent: For joint pain, back pain, fractures, sports injuries, etc.
    """

    def __init__(self, user: Dict, session_id: str):
        """
        Initialize the General Orchestrator Agent.

        Args:
            user: Dictionary containing user info (id, token, etc.)
            session_id: Unique session identifier
        """
        self.agent_name = "general_orchestrator"
        self.model = "gemini-flash-latest"
        self.description = (
            "Main orchestrator agent that understands user health queries "
            "and routes them to the appropriate medical specialist agent."
        )
        self.instructions = getOrchestratorPrompt()

        self.user = user
        self.session_id = session_id

    async def get_agent(self):
        """
        Build the orchestrator agent with specialist sub-agents and return the runner.
        """
        user_id = self.user.get("id")

        if not user_id:
            raise ValueError("User ID is required")

        # create session
        session_service, session = await self.get_session(user_id, self.session_id)

        # build specialist sub-agents
        mental_health_agent = MentalHealthAgent(self.user, self.session_id);
        orthopedics_agent = OrthopedicAgent(self.user, self.session_id);

        # create the orchestrator agent with sub-agents
        orchestrator = LlmAgent(
            name=self.agent_name,
            model=self.model,
            description=self.description,
            instruction=self.instructions,
            sub_agents=[
                mental_health_agent.get_llm_agent(), 
                orthopedics_agent.get_llm_agent()
            ],
        )

        # opik tracer
        tracer = OpikTracer(
            name="general_orchestrator",
            metadata={
                "user_id": user_id,
                "session_id": self.session_id,
            }
        )
        track_adk_agent_recursive(orchestrator, tracer);

        # running the agent
        runner = Runner(
            app_name=self.agent_name,
            agent=orchestrator,
            session_service=session_service,
        )

        return runner, session

    async def get_session(self, user_id: str, session_id: str):
        """
        Get or create a session for the user.
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