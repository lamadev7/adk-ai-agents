import logging
from pydantic import BaseModel
from fastapi import APIRouter, Request
from app.agents.dispatcher import DispatcherAgent

router = APIRouter(
    prefix="/dispatcher",
    tags=["chat"],
);

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(request: Request):
    """Chat with the dispatcher agent."""
    logging.info(f"Chat request: {request}")
    return {"message": "Hello, world!"}
