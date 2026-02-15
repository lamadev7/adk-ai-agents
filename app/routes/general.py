from fastapi import APIRouter
from pydantic import BaseModel
from fastapi import APIRouter, Request

from app.controllers.general import GeneralController

router = APIRouter(
    prefix="",
    tags=["general"],
);

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(request: Request):
    """Chat with the general agent."""
    controller = GeneralController()
    return await controller.chat(request);