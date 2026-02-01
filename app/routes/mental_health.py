import logging
from pydantic import BaseModel
from fastapi import APIRouter, Request, Response
from app.controllers.mental_health import MentalHealthController

router = APIRouter(
    prefix="/mental-health",
    tags=["chat"],
);

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(request: Request):
    """Chat with the mental health agent."""
    controller = MentalHealthController()
    return await controller.chat(request);
