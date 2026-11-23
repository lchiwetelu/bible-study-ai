from fastapi import APIRouter, HTTPException

from bible_study_ai.api.schemas import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    raise HTTPException(
        status_code=501,
        detail="Chat functionality is not implemented yet",
    )