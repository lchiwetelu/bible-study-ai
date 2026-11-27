
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
        description="A Bible reference that directly supports the answer."
    )


class SupportingPoint(BaseModel):
    claim: str = Field(
        description="A specific biblical teaching or practical application."
    )
    reference: str = Field(
        description="The exact Bible reference supporting this point."
    )


class GeneratedAnswer(BaseModel):
    answer: str = Field(
        description="A coherent, natural-language answer to the user's question."
    )
    points: list[SupportingPoint] = Field(
        description="Key claims in the answer, each linked to its supporting scripture."
    )
    citations: list[ScriptureCitation] = Field(
        description="All Bible passages used as evidence in the answer."
    )
    sufficient_evidence: bool = Field(
        description="Whether the supplied passages adequately answer the question."
    )
