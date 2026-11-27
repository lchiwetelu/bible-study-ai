
import ollama

from bible_study_ai.agent.prompts import (
    PASSAGE_RERANKING_PROMPT,
    QUERY_TRANSFORMATION_PROMPT,
)
from bible_study_ai.agent.schemas import (
    PassageReranking,
    QueryTransformation,
)
from bible_study_ai.agent.state import AgentState
from bible_study_ai.rag.vector_store import VectorStore


def transform_query(state: AgentState) -> dict:
    """Generate retrieval-friendly search queries using Qwen3."""

    response = ollama.chat(
        model="qwen3:4b",
        messages=[
            {"role": "system", "content": QUERY_TRANSFORMATION_PROMPT},
            {"role": "user", "content": state["original_query"]},
        ],
        format=QueryTransformation.model_json_schema(),
        options={"temperature": 0},
        think=False,
    )

    result = QueryTransformation.model_validate_json(response.message.content)

    return {"search_queries": result.search_queries}



def retrieve_passages(state: AgentState) -> dict:
    """Retrieve passages using the original and rewritten queries."""

    vector_store = VectorStore()
    retrieved = {}

    search_queries = [
        state["original_query"],
        *state["search_queries"][:2],
    ]

    for query in search_queries:
        results = vector_store.search(query, n_results=5)

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for document, metadata, distance in zip(
            documents, metadatas, distances
        ):
            passage_id = (
                f"{metadata['translation']}:"
                f"{metadata['book']}:"
                f"{metadata['chapter']}:"
                f"{metadata['start_verse']}-"
                f"{metadata['end_verse']}"
            )

            if (
                passage_id not in retrieved
                or distance < retrieved[passage_id]["distance"]
            ):
                retrieved[passage_id] = {
                    "id": passage_id,
                    "text": document,
                    "metadata": metadata,
                    "distance": distance,
                }

    passages = sorted(
        retrieved.values(),
        key=lambda passage: passage["distance"],
    )

    return {"retrieved_passages": passages}


def rerank_passages(state: AgentState) -> dict:
    """Score retrieved passages against the user's original question."""

    passages = state["retrieved_passages"]

    if not passages:
        return {"retrieved_passages": []}

    passages_for_ranking = [
        {
            "id": passage["id"],
            "text": passage["text"],
        }
        for passage in passages
    ]

    response = ollama.chat(
        model="qwen3:4b",
        messages=[
            {"role": "system", "content": PASSAGE_RERANKING_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Original question:\n{state['original_query']}\n\n"
                    f"Passages to evaluate:\n{passages_for_ranking}"
                ),
            },
        ],
        format=PassageReranking.model_json_schema(),
        options={"temperature": 0},
        think=False,
    )

    result = PassageReranking.model_validate_json(
        response.message.content
    )

    scores = {
        item.id: item.score
        for item in result.passages
    }

    reranked = []

    for passage in passages:
        passage["relevance_score"] = scores.get(passage["id"], 0)
        reranked.append(passage)

    reranked.sort(
        key=lambda passage: (
            -passage["relevance_score"],
            passage["distance"],
        )
    )

    return {"retrieved_passages": reranked}
