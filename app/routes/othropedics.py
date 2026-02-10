import logging
from pydantic import BaseModel
from fastapi import APIRouter, Request
from app.controllers.orthopedics import OrthopedicController

router = APIRouter(
    prefix="/orthopedic",
    tags=["chat"],
);

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(request: Request):
    """Chat with the orthopedic agent."""
    controller = OrthopedicController()
    return await controller.chat(request);
