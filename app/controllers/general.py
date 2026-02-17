import json
import logging
from typing import AsyncGenerator
from google.genai import types, Client
from fastapi.responses import JSONResponse, StreamingResponse

from app.agents.general.agent import GeneralAgent
from app.services.conversation_service import conversation_service

logger = logging.getLogger(__name__)


class GeneralController:
    def __init__(self):
        self.agent = None
        self.client = Client()

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
            agent = GeneralAgent(user, session_id)
            runner, session = await agent.get_agent()

            return StreamingResponse(
                self._stream_events(
                    runner=runner,
                    user_id=user_id,
                    session_id=session.id,
                    content=content,
                    user_message=message  # Pass original message for saving
                ),
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
        content,
        user_message: str
    ) -> AsyncGenerator[str, None]:
        """Stream events from the agent as Server-Sent Events."""
        # Collect assistant response for saving to database
        assistant_response_parts = []
        final_response = None
        
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
                            text_content = part.text
                            assistant_response_parts.append(text_content)
                            data = {
                                "type": "text",
                                "content": text_content
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
                        final_response = event.content.parts[0].text.strip()
                        data = {
                            "type": "final",
                            "content": final_response
                        }
                        yield f"data: {json.dumps(data)}\n\n"

            # Send done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            # Save conversation to database after streaming completes
            await self._save_conversation(
                user_id=user_id,
                session_id=session_id,
                user_message=user_message,
                assistant_response=final_response or "".join(assistant_response_parts)
            )

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_data = {"type": "error", "content": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    async def _generate_summary(self, text: str) -> str:
        """Generate a summary of the conversation using Gemini."""
        try:
            response = self.client.models.generate_content(
                model="gemini-flash-latest",
                contents=f"Summarize this conversation concisely between a user and a mental health assistant:\n\n{text}",
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return ""

    async def _generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding for the text using Gemini."""
        try:
            response = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=1536),
            )
            return response.embeddings[0].values
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    async def _save_conversation(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        assistant_response: str
    ) -> None:
        """
        Save conversation (user message + assistant response) to database.
        This runs asynchronously after streaming completes.
        """
        if not assistant_response or not assistant_response.strip():
            logger.warning("No assistant response to save")
            return

        try:
            messages = [
                {"content": user_message, "role": "user"},
                {"content": assistant_response.strip(), "role": "assistant"}
            ]

            result = await conversation_service.save_conversation_history(
                user_id=user_id,
                session_id=session_id,
                messages=messages
            )

            if result.get("success"):
                logger.info(
                    f"Successfully saved conversation for user {user_id}, "
                    f"session {session_id}"
                )
                
                # Extract conversation_ids for potential embedding creation
                saved_data = result.get("data", [])
                if saved_data:
                    conversation_ids = [
                        item.get("conversation_id") 
                        for item in saved_data 
                        if item.get("conversation_id")
                    ]
                    logger.debug(f"Saved conversation IDs: {conversation_ids}")

                    # Generate summary and embedding
                    full_text = f"User: {user_message}\nAssistant: {assistant_response}"
                    summary = await self._generate_summary(full_text)
                    
                    if summary:
                        embedding = await self._generate_embedding(summary)
                        
                        # Save summary
                        await conversation_service.create_conversation_summary(
                            summary_text=summary,
                            conversation_ids=conversation_ids,
                            summary_embedding=embedding
                        )
            else:
                logger.error(
                    f"Failed to save conversation: {result.get('error')}"
                )

        except Exception as e:
            # Log error but don't fail - conversation saving is non-critical
            logger.error(f"Error saving conversation to database: {str(e)}")