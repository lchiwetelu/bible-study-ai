
from pydantic import BaseModel, Field


class QueryTransformation(BaseModel):
    search_queries: list[str] = Field(
        min_length=1,
        max_length=2,
        description="Alternative search queries that preserve the user's original intent.",
    )


class PassageScore(BaseModel):
    id: str = Field(description="The exact ID of the retrieved passage.")
    score: int = Field(
        ge=0,
        le=5,
        description="How relevant the passage is to answering the original question.",
    )


class PassageReranking(BaseModel):
    passages: list[PassageScore]
