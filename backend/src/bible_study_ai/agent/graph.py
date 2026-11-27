
from langgraph.graph import END, START, StateGraph

from bible_study_ai.agent.nodes import (
    expand_context,
    generate_answer,
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
    builder.add_node("expand_context", expand_context)
    builder.add_node("generate_answer", generate_answer)

    builder.add_edge(START, "transform_query")
    builder.add_edge("transform_query", "retrieve_passages")
    builder.add_edge("retrieve_passages", "rerank_passages")
    builder.add_edge("rerank_passages", "expand_context")
    builder.add_edge("expand_context", "generate_answer")
    builder.add_edge("generate_answer", END)

    return builder.compile()
