
from bible_study_ai.agent.graph import build_graph


def main():
    graph = build_graph()

    result = graph.invoke({
        "original_query": "What does the Bible teach about forgiveness?",
        "search_queries": [],
        "retrieved_passages": [],
        "expanded_passages": [],
        "answer": {},
    })

    answer = result["answer"]

    print("\nOriginal question:")
    print(result["original_query"])

    print("\nGenerated search queries:")
    for index, query in enumerate(result["search_queries"], start=1):
        print(f"{index}. {query}")

    print(f"\nRetrieved passages: {len(result['retrieved_passages'])}")
    print(f"Expanded passages: {len(result['expanded_passages'])}")

    print("\n" + "=" * 60)
    print("GENERATED ANSWER")
    print("=" * 60)

    print(answer["answer"])

    print("\nScripture references:")
    for citation in answer["citations"]:
        print(f"- {citation['reference']}")

    print(f"\nSufficient evidence: {answer['sufficient_evidence']}")


if __name__ == "__main__":
    main()
