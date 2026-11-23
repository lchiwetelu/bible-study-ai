
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from bible_study_ai.database import engine
from bible_study_ai.ingestion.usfm_parser import parse_usfm
from bible_study_ai.models import Book, Chapter, Testament, Translation, Verse
from bible_study_ai.config import settings


CORPUS_PATH = settings.usfm_corpus_path

# OSIS identifier and testament for each canonical USFM book ID.
# Dictionary insertion order defines canonical book position.
BOOK_METADATA = {
    "GEN": ("Gen", Testament.OLD),
    "EXO": ("Exod", Testament.OLD),
    "LEV": ("Lev", Testament.OLD),
    "NUM": ("Num", Testament.OLD),
    "DEU": ("Deut", Testament.OLD),
    "JOS": ("Josh", Testament.OLD),
    "JDG": ("Judg", Testament.OLD),
    "RUT": ("Ruth", Testament.OLD),
    "1SA": ("1Sam", Testament.OLD),
    "2SA": ("2Sam", Testament.OLD),
    "1KI": ("1Kgs", Testament.OLD),
    "2KI": ("2Kgs", Testament.OLD),
    "1CH": ("1Chr", Testament.OLD),
    "2CH": ("2Chr", Testament.OLD),
    "EZR": ("Ezra", Testament.OLD),
    "NEH": ("Neh", Testament.OLD),
    "EST": ("Esth", Testament.OLD),
    "JOB": ("Job", Testament.OLD),
    "PSA": ("Ps", Testament.OLD),
    "PRO": ("Prov", Testament.OLD),
    "ECC": ("Eccl", Testament.OLD),
    "SNG": ("Song", Testament.OLD),
    "ISA": ("Isa", Testament.OLD),
    "JER": ("Jer", Testament.OLD),
    "LAM": ("Lam", Testament.OLD),
    "EZK": ("Ezek", Testament.OLD),
    "DAN": ("Dan", Testament.OLD),
    "HOS": ("Hos", Testament.OLD),
    "JOL": ("Joel", Testament.OLD),
    "AMO": ("Amos", Testament.OLD),
    "OBA": ("Obad", Testament.OLD),
    "JON": ("Jonah", Testament.OLD),
    "MIC": ("Mic", Testament.OLD),
    "NAM": ("Nah", Testament.OLD),
    "HAB": ("Hab", Testament.OLD),
    "ZEP": ("Zeph", Testament.OLD),
    "HAG": ("Hag", Testament.OLD),
    "ZEC": ("Zech", Testament.OLD),
    "MAL": ("Mal", Testament.OLD),
    "MAT": ("Matt", Testament.NEW),
    "MRK": ("Mark", Testament.NEW),
    "LUK": ("Luke", Testament.NEW),
    "JHN": ("John", Testament.NEW),
    "ACT": ("Acts", Testament.NEW),
    "ROM": ("Rom", Testament.NEW),
    "1CO": ("1Cor", Testament.NEW),
    "2CO": ("2Cor", Testament.NEW),
    "GAL": ("Gal", Testament.NEW),
    "EPH": ("Eph", Testament.NEW),
    "PHP": ("Phil", Testament.NEW),
    "COL": ("Col", Testament.NEW),
    "1TH": ("1Thess", Testament.NEW),
    "2TH": ("2Thess", Testament.NEW),
    "1TI": ("1Tim", Testament.NEW),
    "2TI": ("2Tim", Testament.NEW),
    "TIT": ("Titus", Testament.NEW),
    "PHM": ("Phlm", Testament.NEW),
    "HEB": ("Heb", Testament.NEW),
    "JAS": ("Jas", Testament.NEW),
    "1PE": ("1Pet", Testament.NEW),
    "2PE": ("2Pet", Testament.NEW),
    "1JN": ("1John", Testament.NEW),
    "2JN": ("2John", Testament.NEW),
    "3JN": ("3John", Testament.NEW),
    "JUD": ("Jude", Testament.NEW),
    "REV": ("Rev", Testament.NEW),
}


def metadata_value(metadata: dict, key: str) -> str:
    """Return the first non-empty value for a book metadata field."""
    values = metadata.get(key, [])
    return next((value.strip() for value in values if value.strip()), "")


def ingest_book(
    session: Session,
    translation: Translation,
    parsed_book: dict,
    position: int,
) -> tuple[int, int]:
    usfm_id = parsed_book["usfm_id"]

    if usfm_id not in BOOK_METADATA:
        raise ValueError(f"Unsupported canonical book ID: {usfm_id}")

    osis_id, testament = BOOK_METADATA[usfm_id]

    name = (
        metadata_value(parsed_book["metadata"], "toc2")
        or metadata_value(parsed_book["metadata"], "h")
    )

    if not name:
        raise ValueError(f"Missing book name for {usfm_id}")

    book = session.scalar(
        select(Book).where(
            Book.translation_id == translation.id,
            Book.usfm_id == usfm_id,
        )
    )

    if book is None:
        book = Book(
            translation_id=translation.id,
            usfm_id=usfm_id,
            osis_id=osis_id,
            name=name,
            position=position,
            testament=testament,
        )
        session.add(book)
        session.flush()
    else:
        book.osis_id = osis_id
        book.name = name
        book.position = position
        book.testament = testament

    chapter_count = 0
    verse_count = 0

    for parsed_chapter in parsed_book["chapters"]:
        chapter_number = parsed_chapter["number"]

        chapter = session.scalar(
            select(Chapter).where(
                Chapter.book_id == book.id,
                Chapter.number == chapter_number,
            )
        )

        structure = {"elements": parsed_chapter["elements"]}

        if chapter is None:
            chapter = Chapter(
                book_id=book.id,
                number=chapter_number,
                structure=structure,
            )
            session.add(chapter)
            session.flush()
        else:
            chapter.structure = structure

        chapter_count += 1

        for parsed_verse in parsed_chapter["verses"]:
            verse_number = parsed_verse["number"]

            verse = session.scalar(
                select(Verse).where(
                    Verse.chapter_id == chapter.id,
                    Verse.number == verse_number,
                )
            )

            if verse is None:
                verse = Verse(
                    chapter_id=chapter.id,
                    number=verse_number,
                    text=parsed_verse["text"],
                )
                session.add(verse)
            else:
                verse.text = parsed_verse["text"]

            verse_count += 1

    return chapter_count, verse_count


def ingest_corpus() -> None:
    if not CORPUS_PATH.is_dir():
        raise FileNotFoundError(
            f"USFM corpus directory not found: {CORPUS_PATH}"
        )

    with Session(engine) as session:
        with session.begin():
            translation = session.scalar(
                select(Translation).where(Translation.code == "WEB")
            )

            if translation is None:
                translation = Translation(
                    code="WEB",
                    name="World English Bible",
                    language_code="en",
                    description="World English Bible",
                    source="World English Bible USFM corpus",
                )
                session.add(translation)
                session.flush()

            total_chapters = 0
            total_verses = 0
            imported_books = 0

            for position, (usfm_id, _) in enumerate(
                BOOK_METADATA.items(), start=1
            ):
                matches = list(CORPUS_PATH.glob(f"*-{usfm_id}engwebu.usfm"))

                if len(matches) != 1:
                    raise ValueError(
                        f"Expected exactly one file for {usfm_id}; "
                        f"found {len(matches)}"
                    )

                source = matches[0].read_text(encoding="utf-8")
                parsed_book = parse_usfm(source)

                if parsed_book["usfm_id"] != usfm_id:
                    raise ValueError(
                        f"Book ID mismatch in {matches[0].name}: "
                        f"expected {usfm_id}, "
                        f"got {parsed_book['usfm_id']}"
                    )

                chapters, verses = ingest_book(
                    session,
                    translation,
                    parsed_book,
                    position,
                )

                imported_books += 1
                total_chapters += chapters
                total_verses += verses

                print(
                    f"{usfm_id}: {chapters} chapters, "
                    f"{verses} verses"
                )

            print("\nIngestion completed:")
            print(f"Books: {imported_books}")
            print(f"Chapters: {total_chapters}")
            print(f"Verses: {total_verses}")


if __name__ == "__main__":
    ingest_corpus()
