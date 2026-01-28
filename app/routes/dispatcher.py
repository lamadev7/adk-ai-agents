import logging
from pydantic import BaseModel
from fastapi import APIRouter, Request, Response
from app.controllers.dispatcher import DispatcherController

router = APIRouter(
    prefix="/dispatcher",
    tags=["chat"],
);

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(request: Request):
    """Chat with the dispatcher agent."""
    controller = DispatcherController()
    return await controller.chat(request);
