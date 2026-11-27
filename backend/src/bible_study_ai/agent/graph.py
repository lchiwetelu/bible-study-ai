
from langgraph.graph import END, START, StateGraph

from bible_study_ai.agent.nodes import (
    rerank_passages,
    retrieve_passages,
    transform_query,
)
from bible_study_ai.agent.state import AgentState


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("transform_query", transform_query)
    builder.add_node("retrieve_passages", retrieve_passages)
    builder.add_node("rerank_passages", rerank_passages)

    builder.add_edge(START, "transform_query")
    builder.add_edge("transform_query", "retrieve_passages")
    builder.add_edge("retrieve_passages", "rerank_passages")
    builder.add_edge("rerank_passages", END)

    return builder.compile()
