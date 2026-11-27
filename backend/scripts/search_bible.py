import argparse

from bible_study_ai.rag.vector_store import VectorStore


def format_reference(metadata: dict) -> str:
    """Format passage metadata into a readable Bible reference."""
    book = metadata["book"]
    chapter = metadata["chapter"]
    start_verse = metadata["start_verse"]
    end_verse = metadata["end_verse"]

    if start_verse == end_verse:
        verses = start_verse
    else:
        verses = f"{start_verse}-{end_verse}"

    return f"{book} {chapter}:{verses}"


def search_bible(query: str, limit: int = 5):
    """Search the Bible vector store and display matching passages."""
    vector_store = VectorStore()

    total_chunks = vector_store.count()

    if total_chunks == 0:
        print("The Bible vector store is empty. Run index_bible.py first.")
        return

    results = vector_store.search(
        query=query,
        n_results=limit,
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    print(f"\nQuestion: {query}")
    print(f"Found {len(documents)} matching passages.\n")

    for index, (document, metadata, distance) in enumerate(
        zip(documents, metadatas, distances),
        start=1,
    ):
        reference = format_reference(metadata)

        print(f"{'=' * 60}")
        print(f"Result {index}: {reference}")
        print(f"Distance: {distance:.4f}")
        print(f"{'-' * 60}")
        print(document)
        print()

    print("=" * 60)
    print("Search complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Search the World English Bible using semantic search."
    )

    parser.add_argument(
        "query",
        type=str,
        help="The question or phrase to search for.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of passages to retrieve (default: 5).",
    )

    args = parser.parse_args()

    if not args.query.strip():
        parser.error("The search query cannot be empty.")

    if args.limit < 1:
        parser.error("--limit must be greater than zero.")

    search_bible(
        query=args.query,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()