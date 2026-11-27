
from bible_study_ai.agent.graph import build_graph


def main():
    graph = build_graph()

    result = graph.invoke({
        "original_query": "How can I show compassion to someone who has wronged me?",
        "search_queries": [],
        "retrieved_passages": [],
        "expanded_passages": [],
    })

    print("\nOriginal question:")
    print(result["original_query"])

    print("\nGenerated search queries:")
    for index, query in enumerate(result["search_queries"], start=1):
        print(f"{index}. {query}")

    print("\nExpanded passages:")

    for index, passage in enumerate(
        result["expanded_passages"], start=1
    ):
        metadata = passage["metadata"]

        reference = (
            f"{metadata['book']} "
            f"{metadata['chapter']}:"
            f"{metadata['start_verse']}-"
            f"{metadata['end_verse']}"
        )

        context_reference = (
            f"{metadata['book']} "
            f"{metadata['chapter']}:"
            f"{passage['context_start_verse']}-"
            f"{passage['context_end_verse']}"
        )

        print(f"\n{'=' * 60}")
        print(f"{index}. Retrieved passage: {reference}")
        print(f"Relevance score: {passage['relevance_score']}/5")
        print(f"Vector distance: {passage['distance']:.4f}")

        print("\nOriginal chunk:")
        print(passage["text"])

        print(f"\nExpanded context: {context_reference}")
        print(passage["context_text"])


if __name__ == "__main__":
    main()
