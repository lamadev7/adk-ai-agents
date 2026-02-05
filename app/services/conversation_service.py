"""
Conversation Service - Handles saving conversations and embeddings to external API
"""
import logging
import httpx
from typing import List, Dict, Any, Optional
import uuid
logger = logging.getLogger(__name__)

# External API base URL
CONVERSATION_API_BASE_URL = "http://localhost:3333/api"


class ConversationService:
    """
    Service for managing conversation history and embeddings via external API.
    """

    def __init__(self):
        self.base_url = CONVERSATION_API_BASE_URL
        self.timeout = 30.0  # 30 seconds timeout

    async def save_conversation_history(
        self,
        user_id: str | int,
        session_id: str,
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Save conversation history (user message + assistant response).
        
        Args:
            user_id: The user's ID
            session_id: The session ID for the conversation
            messages: List of messages with 'content' and 'role' keys
                     role can be: 'user', 'assistant', 'system'
        
        Returns:
            API response with saved conversation data
        
        Example:
            await service.save_conversation_history(
                user_id=2,
                session_id="uuid",
                messages=[
                    {"content": "Hello", "role": "user"},
                    {"content": "Hi there!", "role": "assistant"}
                ]
            )
        """
        endpoint = f"{self.base_url}/chat/messages/batch"
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "messages": messages,
            "conversation_id": str(uuid.uuid4())
        };

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("success"):
                    logger.info(
                        f"Saved {len(messages)} messages for user {user_id}, "
                        f"session {session_id}"
                    )
                else:
                    logger.warning(
                        f"Failed to save conversation: {result.get('error')}"
                    )
                
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error saving conversation: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"Request error saving conversation: {str(e)}")
            return {"success": False, "error": f"Request error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error saving conversation: {str(e)}")
            return {"success": False, "error": str(e)}

    async def create_conversation_summary(
        self,
        summary_text: str,
        conversation_ids: List[str],
        summary_embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Create a conversation summary with optional embedding.
        
        Args:
            summary_text: Text summary of the conversation(s)
            conversation_ids: List of conversation UUIDs included in summary
            summary_embedding: Optional 1536-dimensional embedding vector
        
        Returns:
            API response with created summary data
        """
        endpoint = f"{self.base_url}/conversation-summaries"
        payload = {
            "summary_text": summary_text,
            "conversation_ids": conversation_ids
        }
        
        if summary_embedding:
            payload["summary_embedding"] = summary_embedding

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("success"):
                    logger.info(f"Created conversation summary for {len(conversation_ids)} conversations")
                else:
                    logger.warning(f"Failed to create summary: {result.get('error')}")
                
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating summary: {e.response.status_code}")
            return {"success": False, "error": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"Request error creating summary: {str(e)}")
            return {"success": False, "error": f"Request error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error creating summary: {str(e)}")
            return {"success": False, "error": str(e)}

    async def semantic_search(
        self,
        query_embedding: List[float],
        query_text: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Search for similar conversation summaries using vector similarity.
        
        Args:
            query_embedding: 1536-dimensional embedding vector
            query_text: Optional original text for reference
            limit: Max results to return (default: 5, max: 20)
            similarity_threshold: Minimum similarity score (default: 0.7)
        
        Returns:
            API response with matching summaries and similarity scores
        """
        endpoint = f"{self.base_url}/conversation-summaries/semantic-search"
        payload = {
            "query_embedding": query_embedding,
            "limit": limit,
            "similarity_threshold": similarity_threshold
        }
        
        if query_text:
            payload["query_text"] = query_text

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in semantic search: {e.response.status_code}")
            return {"success": False, "error": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"Request error in semantic search: {str(e)}")
            return {"success": False, "error": f"Request error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error in semantic search: {str(e)}")
            return {"success": False, "error": str(e)}

    async def text_search(
        self,
        query: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Fallback text search when embeddings are unavailable.
        
        Args:
            query: Search query text
            limit: Max results to return
        
        Returns:
            API response with matching summaries
        """
        endpoint = f"{self.base_url}/conversation-summaries/text-search"
        payload = {
            "query": query,
            "limit": limit
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in text search: {e.response.status_code}")
            return {"success": False, "error": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"Request error in text search: {str(e)}")
            return {"success": False, "error": f"Request error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error in text search: {str(e)}")
            return {"success": False, "error": str(e)}


# Singleton instance for easy import
conversation_service = ConversationService()
