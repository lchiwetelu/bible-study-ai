from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    conversation_id: UUID | None = None

class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: str
    sources: list[str]