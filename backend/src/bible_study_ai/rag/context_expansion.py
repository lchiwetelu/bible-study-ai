
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.orm import Session

from bible_study_ai.database import engine
from bible_study_ai.models.book import Book
from bible_study_ai.models.chapter import Chapter
from bible_study_ai.models.translation import Translation
from bible_study_ai.models.verse import Verse


def expand_passage_context(
    passage: dict,
    window: int = 2,
) -> dict:
    """
    Expand a retrieved passage with neighbouring verses.

    The original passage is preserved. Expanded context is added separately.
    """

    if window < 0:
        raise ValueError("Context window cannot be negative.")

    metadata = passage["metadata"]

    with Session(engine) as session:
        # Find the chapter containing the retrieved passage.
        chapter_statement = (
            select(Chapter.id)
            .join(Chapter.book)
            .join(Book.translation)
            .where(
                Translation.code == metadata["translation"],
                Book.usfm_id == metadata["book"],
                Chapter.number == metadata["chapter"],
            )
        )

        chapter_id = session.scalar(chapter_statement)

        if chapter_id is None:
            raise ValueError(
                f"Chapter not found: "
                f"{metadata['book']} {metadata['chapter']}."
            )

        # Assign each verse a numerical position within its chapter.
        # The suffix ordering supports verse numbers such as 3a and 3b.
        verse_number = cast(
            func.substring(Verse.number, r"^\d+"),
            Integer,
        )

        verse_suffix = func.coalesce(
            func.substring(Verse.number, r"[a-z]+$"),
            "",
        )

        numbered_verses = (
            select(
                Verse.number,
                Verse.text,
                func.row_number()
                .over(
                    order_by=(verse_number, verse_suffix)
                )
                .label("position"),
            )
            .where(Verse.chapter_id == chapter_id)
            .cte("numbered_verses")
        )

        # Find the positions of the original passage boundaries.
        start_position = (
            select(numbered_verses.c.position)
            .where(
                numbered_verses.c.number == metadata["start_verse"]
            )
            .scalar_subquery()
        )

        end_position = (
            select(numbered_verses.c.position)
            .where(
                numbered_verses.c.number == metadata["end_verse"]
            )
            .scalar_subquery()
        )

        positions = session.execute(
            select(
                start_position.label("start_position"),
                end_position.label("end_position"),
            )
        ).one()

        if positions.start_position is None:
            raise ValueError(
                f"Starting verse {metadata['start_verse']} "
                f"not found in {metadata['book']} "
                f"{metadata['chapter']}."
            )

        if positions.end_position is None:
            raise ValueError(
                f"Ending verse {metadata['end_verse']} "
                f"not found in {metadata['book']} "
                f"{metadata['chapter']}."
            )

        if positions.start_position > positions.end_position:
            raise ValueError("Starting verse occurs after ending verse.")

        # Fetch only the original passage and its neighbouring verses.
        context_statement = (
            select(
                numbered_verses.c.number,
                numbered_verses.c.text,
            )
            .where(
                numbered_verses.c.position.between(
                    positions.start_position - window,
                    positions.end_position + window,
                )
            )
            .order_by(numbered_verses.c.position)
        )

        context_verses = session.execute(
            context_statement
        ).all()

    context_text = "\n".join(
        f"{verse.number}. {verse.text}"
        for verse in context_verses
    )

    return {
        **passage,
        "context_text": context_text,
        "context_start_verse": context_verses[0].number,
        "context_end_verse": context_verses[-1].number,
    }
