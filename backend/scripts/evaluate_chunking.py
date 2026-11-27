
from statistics import mean, median

from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager

from bible_study_ai.database import engine
from bible_study_ai.models.book import Book
from bible_study_ai.models.chapter import Chapter
from bible_study_ai.rag.chunking import build_chunks


def main():
    all_chunks = []
    chapters_verified = 0

    with Session(engine) as session:
        statement = (
            select(Chapter)
            .join(Chapter.book)
            .options(contains_eager(Chapter.book))
            .order_by(Book.position, Chapter.number)
        )

        chapters = session.scalars(statement).unique().all()

        for chapter in chapters:
            elements = chapter.structure.get("elements", [])

            chunks = build_chunks(
                elements=elements,
                translation="WEB",
                book=chapter.book.usfm_id,
                chapter=chapter.number,
            )

            # Get all non-empty source verses.
            source_verses = [
                element
                for element in elements
                if element["type"] == "verse"
                and element.get("text", "").strip()
            ]

            # Verify verse text preservation.
            source_text = " ".join(
                verse["text"].strip()
                for verse in source_verses
            )

            chunked_text = " ".join(
                chunk.text
                for chunk in chunks
            )

            if source_text != chunked_text:
                raise ValueError(
                    f"Verse text integrity check failed: "
                    f"{chapter.book.usfm_id} {chapter.number}"
                )

            # Verify every individual verse reference.
            source_verse_numbers = [
                verse["number"]
                for verse in source_verses
            ]

            chunked_verse_numbers = [
                verse_number
                for chunk in chunks
                for verse_number in chunk.verse_numbers
            ]

            if source_verse_numbers != chunked_verse_numbers:
                raise ValueError(
                    f"Verse reference integrity check failed: "
                    f"{chapter.book.usfm_id} {chapter.number}"
                )

            # Verify the first and last verse references.
            if source_verses and chunks:
                if chunks[0].start_verse != source_verses[0]["number"]:
                    raise ValueError(
                        f"Incorrect starting verse: "
                        f"{chapter.book.usfm_id} {chapter.number}"
                    )

                if chunks[-1].end_verse != source_verses[-1]["number"]:
                    raise ValueError(
                        f"Incorrect ending verse: "
                        f"{chapter.book.usfm_id} {chapter.number}"
                    )

            chapters_verified += 1
            all_chunks.extend(chunks)

    if not all_chunks:
        print("No chunks were generated.")
        return

    word_counts = [chunk.word_count for chunk in all_chunks]

    print("\n--- Chunking Evaluation ---")
    print(f"Chapters processed: {len(chapters)}")
    print(f"Chapters passing integrity checks: {chapters_verified}")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Average words: {mean(word_counts):.1f}")
    print(f"Median words: {median(word_counts)}")
    print(f"Maximum words: {max(word_counts)}")
    print(
        f"Chunks over 200 words: "
        f"{sum(count > 200 for count in word_counts)}"
    )


if __name__ == "__main__":
    main()
