import json
import logging
from google.genai import types
from typing import AsyncGenerator
from app.agents.mental_health import MentalHealthAgent
from fastapi.responses import JSONResponse, StreamingResponse

class MentalHealthController:
    def __init__(self):
        self.agent = None

    async def chat(self, request):
        try:
            body = await request.json()
            user = body.get("user")
            user_id = user.get("id")
            message = body.get("message")
            session_id = body.get("session_id")

            # validate the request
            if not user:
                return JSONResponse(
                    status_code=400,
                    content={
                        "data": None,
                        "error": "User is required!"
                    }
                )
            if not message:
                return JSONResponse(
                    status_code=400,
                    content={
                        "data": None,
                        "error": "Message is required!"
                    }
                )

            # create the content    
            content = types.Content(role="user", parts=[types.Part(text=message)])
            
            # call the agent
            agent = MentalHealthAgent(user, session_id)
            runner, session = await agent.get_agent()

            return StreamingResponse(
                self._stream_events(runner, user_id, session.id, content),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )

        except Exception as e:
            logging.error(f"Error: {e}")
            return JSONResponse(
                status_code=500,
                content={"data": None, "error": "Internal server error"}
            )

    async def _stream_events(
        self, 
        runner, 
        user_id: str, 
        session_id: str, 
        content
    ) -> AsyncGenerator[str, None]:
        """Stream events from the agent as Server-Sent Events."""
        try:
            runner_events = runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            )

            async for event in runner_events:
                print(f"Event ID: {event.id}, Author: {event.author}")
                has_specific_part = False

                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "executable_code") and part.executable_code:
                            # Stream executable code
                            data = {
                                "type": "code",
                                "content": part.executable_code.code
                            }
                            yield f"data: {json.dumps(data)}\n\n"
                            has_specific_part = True

                        elif hasattr(part, "code_execution_result") and part.code_execution_result:
                            # Stream code execution result
                            data = {
                                "type": "code_result",
                                "outcome": str(part.code_execution_result.outcome),
                                "output": part.code_execution_result.output
                            }
                            yield f"data: {json.dumps(data)}\n\n"
                            has_specific_part = True

                        elif hasattr(part, "text") and part.text and not part.text.isspace():
                            # Stream text content
                            data = {
                                "type": "text",
                                "content": part.text
                            }
                            yield f"data: {json.dumps(data)}\n\n"
                        else:
                            data = {
                                "type": "text",
                                "content": part.text
                            }
                            yield f"data: {json.dumps(data)}\n\n"

                # Check for final response
                if not has_specific_part and hasattr(event, "is_final_response") and event.is_final_response():
                    if (
                        event.content
                        and event.content.parts
                        and hasattr(event.content.parts[0], "text")
                        and event.content.parts[0].text
                    ):
                        data = {
                            "type": "final",
                            "content": event.content.parts[0].text.strip()
                        }
                        yield f"data: {json.dumps(data)}\n\n"

            # Send done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logging.error(f"Streaming error: {e}")
            error_data = {"type": "error", "content": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"