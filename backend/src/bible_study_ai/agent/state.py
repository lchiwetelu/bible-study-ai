from typing import TypedDict


class AgentState(TypedDict):
    original_query: str
    search_queries: list[str]
    retrieved_passages: list[dict]