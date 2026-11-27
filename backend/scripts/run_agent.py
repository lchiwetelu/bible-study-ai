
from bible_study_ai.agent.graph import build_graph


def main():
    graph = build_graph()

    result = graph.invoke({
        "original_query": "What does the Bible teach about loving your enemies?",
        "search_queries": [],
        "retrieved_passages": [],
        "expanded_passages": [],
        "answer": {},
    })

    print("\nOriginal question:")
    print(result["original_query"])

    print("\nGenerated search queries:")
    for index, query in enumerate(result["search_queries"], start=1):
        print(f"{index}. {query}")

    print("\n" + "=" * 70)
    print("RETRIEVED PASSAGES AFTER RERANKING")
    print("=" * 70)

    for index, passage in enumerate(
        result["retrieved_passages"], start=1
    ):
        metadata = passage["metadata"]

        reference = (
            f"{metadata['book']} "
            f"{metadata['chapter']}:"
            f"{metadata['start_verse']}-"
            f"{metadata['end_verse']}"
        )

        print(f"\n{index}. {reference}")
        print(f"   Relevance score: {passage['relevance_score']}/5")
        print(f"   Vector distance: {passage['distance']:.4f}")
        print(f"   Text: {passage['text']}")

    print("\n" + "=" * 70)
    print("RETRIEVAL SUMMARY")
    print("=" * 70)

    print(f"Retrieved passages: {len(result['retrieved_passages'])}")
    print(f"Expanded passages: {len(result['expanded_passages'])}")

    answer = result["answer"]

    print("\n" + "=" * 70)
    print("GENERATED ANSWER")
    print("=" * 70)

    print(answer["answer"])

    print("\nSupporting points:")
    for point in answer["points"]:
        print(f"- {point['claim']}")
        print(f"  Scripture: {point['reference']}")

    print("\nScripture references:")
    for citation in answer["citations"]:
        print(f"- {citation['reference']}")

    print(f"\nSufficient evidence: {answer['sufficient_evidence']}")


if __name__ == "__main__":
    main()
