
import ollama

from bible_study_ai.agent.prompts import (
    ANSWER_GENERATION_PROMPT,
    PASSAGE_RERANKING_PROMPT,
    QUERY_TRANSFORMATION_PROMPT,
)
from bible_study_ai.agent.schemas import (
    GeneratedAnswer,
    PassageReranking,
    QueryTransformation,
    ScriptureCitation,
)
from bible_study_ai.agent.state import AgentState
from bible_study_ai.rag.context_expansion import expand_passage_context
from bible_study_ai.rag.vector_store import VectorStore

from bible_study_ai.rag.citations import is_reference_covered


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

    result = QueryTransformation.model_validate_json(
        response.message.content
    )

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


def expand_context(state: AgentState) -> dict:
    """Expand the top five reranked passages with surrounding verses."""

    top_passages = state["retrieved_passages"][:5]

    expanded_passages = [
        expand_passage_context(passage, window=2)
        for passage in top_passages
    ]

    return {"expanded_passages": expanded_passages}


def generate_answer(state: AgentState) -> dict:
    """Generate a scripture-grounded answer using Qwen3."""

    passages = state["expanded_passages"]

    if not passages:
        return {
            "answer": {
                "answer": "I couldn't find relevant Bible passages to answer this question.",
                "points": [],
                "citations": [],
                "sufficient_evidence": False,
            }
        }

    passages_for_generation = [
        {
            "reference": (
                f"{passage['metadata']['book']} "
                f"{passage['metadata']['chapter']}:"
                f"{passage['context_start_verse']}-"
                f"{passage['context_end_verse']}"
            ),
            "text": passage["context_text"],
        }
        for passage in passages
    ]

    valid_references = {
        passage["reference"]
        for passage in passages_for_generation
    }

    print("\nANSWER GENERATION INPUT")
    print(f"Number of passages: {len(passages_for_generation)}")
    print(
        "Total passage characters:",
        sum(len(passage["text"]) for passage in passages_for_generation),
    )

    response = ollama.chat(
        model="qwen3:4b",
        messages=[
            {
                "role": "system",
                "content": ANSWER_GENERATION_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"Question:\n{state['original_query']}\n\n"
                    f"Bible passages:\n{passages_for_generation}"
                ),
            },
        ],
        format=GeneratedAnswer.model_json_schema(),
        options={
            "temperature": 0,
            "num_predict": 2048,
        },
        think=False,
    )

    print("\nRAW MODEL RESPONSE")
    print(repr(response.message.content))

    print("\nGENERATION STATISTICS")
    print(f"Done reason: {response.done_reason}")
    print(f"Prompt tokens: {response.prompt_eval_count}")
    print(f"Generated tokens: {response.eval_count}")

    result = GeneratedAnswer.model_validate_json(
        response.message.content
    )

    # Validate each supporting point against the supplied passage ranges.
    valid_points = [
        point
        for point in result.points
        if is_reference_covered(
            point.reference,
            valid_references,
        )
    ]

    invalid_points = [
        point
        for point in result.points
        if not is_reference_covered(
            point.reference,
            valid_references,
        )
    ]

    if invalid_points:
        print("\nREJECTED REFERENCES")
        for point in invalid_points:
            print(f"- {point.reference}")

    # Derive citations from validated supporting points.
    citation_references = sorted({
        point.reference
        for point in valid_points
    })

    answer = result.model_dump()

    answer["points"] = [
        point.model_dump()
        for point in valid_points
    ]

    answer["citations"] = [
        ScriptureCitation(reference=reference).model_dump()
        for reference in citation_references
    ]

    return {"answer": answer}
