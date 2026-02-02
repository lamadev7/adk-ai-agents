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
                
                # Debug: log the full event structure
                if event.content and event.content.parts:
                    for i, part in enumerate(event.content.parts):
                        print(f"  Part {i}: {type(part).__name__}, attrs: {[a for a in dir(part) if not a.startswith('_')]}")

                if event.content and event.content.parts:
                    for part in event.content.parts:
                        # Handle function calls (tool invocations)
                        if hasattr(part, "function_call") and part.function_call:
                            data = {
                                "type": "tool_call",
                                "name": part.function_call.name,
                                "args": dict(part.function_call.args) if part.function_call.args else {}
                            }
                            yield f"data: {json.dumps(data)}\n\n"
                            print(f"  Tool call: {part.function_call.name}")

                        # Handle function responses (tool results)
                        elif hasattr(part, "function_response") and part.function_response:
                            response_data = part.function_response.response
                            data = {
                                "type": "tool_response",
                                "name": part.function_response.name,
                                "response": response_data if isinstance(response_data, (dict, list, str)) else str(response_data)
                            }
                            yield f"data: {json.dumps(data)}\n\n"
                            print(f"  Tool response: {part.function_response.name}")

                        elif hasattr(part, "executable_code") and part.executable_code:
                            # Stream executable code
                            data = {
                                "type": "code",
                                "content": part.executable_code.code
                            }
                            yield f"data: {json.dumps(data)}\n\n"

                        elif hasattr(part, "code_execution_result") and part.code_execution_result:
                            # Stream code execution result
                            data = {
                                "type": "code_result",
                                "outcome": str(part.code_execution_result.outcome),
                                "output": part.code_execution_result.output
                            }
                            yield f"data: {json.dumps(data)}\n\n"

                        elif hasattr(part, "text") and part.text and part.text.strip():
                            # Stream text content (only if not empty/whitespace)
                            data = {
                                "type": "text",
                                "content": part.text
                            }
                            yield f"data: {json.dumps(data)}\n\n"

                # Check for final response
                if hasattr(event, "is_final_response") and event.is_final_response():
                    if (
                        event.content
                        and event.content.parts
                        and hasattr(event.content.parts[0], "text")
                        and event.content.parts[0].text
                        and event.content.parts[0].text.strip()
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