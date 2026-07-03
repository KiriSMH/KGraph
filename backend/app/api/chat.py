from fastapi import APIRouter

from app.schemas.requests import ChatRequest
from app.schemas.responses import ChatResponse
from app.services.agent import chat as agent_chat


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> dict:
    return agent_chat(request.message)
