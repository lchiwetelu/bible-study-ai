
from pydantic import BaseModel, Field


class QueryTransformation(BaseModel):
    search_queries: list[str] = Field(
        min_length=1,
        max_length=2,
        description="Two alternative search queries that preserve the user's original intent.",
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


class ScriptureCitation(BaseModel):
    reference: str = Field(
        description="The Bible reference supporting the answer."
    )
    explanation: str = Field(
        description="Briefly explain how this passage supports the answer."
    )


class GeneratedAnswer(BaseModel):
    answer: str = Field(
        description="A clear, coherent answer to the user's question."
    )
    citations: list[ScriptureCitation] = Field(
        description="Scripture references supporting the answer."
    )
    sufficient_evidence: bool = Field(
        description="Whether the retrieved passages provide sufficient evidence to answer the question."
    )
