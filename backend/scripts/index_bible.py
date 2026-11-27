
from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager

from bible_study_ai.database import engine
from bible_study_ai.models.book import Book
from bible_study_ai.models.chapter import Chapter
from bible_study_ai.rag.chunking import build_chunks
from bible_study_ai.rag.vector_store import VectorStore


TRANSLATION = "WEB"
BATCH_SIZE = 100


def load_chunks() -> list:
    """Load Bible chapters from PostgreSQL and generate passage chunks."""

    all_chunks = []

    with Session(engine) as session:
        statement = (
            select(Chapter)
            .join(Chapter.book)
            .options(contains_eager(Chapter.book))
            .order_by(Book.position, Chapter.number)
        )

        chapters = session.scalars(statement).unique().all()

        print(f"Loaded {len(chapters)} chapters from PostgreSQL.")

        for chapter in chapters:
            elements = chapter.structure.get("elements", [])

            chunks = build_chunks(
                elements=elements,
                translation=TRANSLATION,
                book=chapter.book.usfm_id,
                chapter=chapter.number,
            )

            all_chunks.extend(chunks)

    return all_chunks


def index_bible():
    print("\nStarting Bible indexing...\n")

    # Step 1: Generate passage chunks.
    chunks = load_chunks()

    print(f"Generated {len(chunks)} passage chunks.")

    if not chunks:
        print("No chunks found. Nothing to index.")
        return

    # Step 2: Initialise the vector store.
    vector_store = VectorStore()

    existing_count = vector_store.count()

    print(f"Existing ChromaDB records: {existing_count}")

    # Step 3: Generate embeddings and store chunks in batches.
    total_indexed = 0

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]

        indexed = vector_store.upsert_chunks(batch)

        total_indexed += indexed

        print(
            f"Indexed {total_indexed}/{len(chunks)} chunks"
        )

    # Step 4: Verify the final collection count.
    final_count = vector_store.count()

    print("\n--- Indexing Complete ---")
    print(f"Chunks generated: {len(chunks)}")
    print(f"Chunks indexed: {total_indexed}")
    print(f"ChromaDB records before indexing: {existing_count}")
    print(f"ChromaDB records after indexing: {final_count}")

    if final_count < len(chunks):
        raise RuntimeError(
            "ChromaDB contains fewer records than expected."
        )

    print("\nBible indexing completed successfully!")


if __name__ == "__main__":
    index_bible()
