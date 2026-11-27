
from dataclasses import dataclass


@dataclass
class PassageChunk:
    translation: str
    book: str
    chapter: int
    start_verse: str
    end_verse: str
    verse_numbers: list[str]
    text: str
    word_count: int


def build_chunks(
    elements: list[dict],
    translation: str,
    book: str,
    chapter: int,
    target_words: int = 200,
) -> list[PassageChunk]:

    chunks = []
    current_verses = []

    def flush():
        if not current_verses:
            return

        text = " ".join(
            verse["text"].strip()
            for verse in current_verses
            if verse.get("text", "").strip()
        )

        if text:
            chunks.append(
                PassageChunk(
                    translation=translation,
                    book=book,
                    chapter=chapter,
                    start_verse=current_verses[0]["number"],
                    end_verse=current_verses[-1]["number"],
                    text=text,
                    word_count=len(text.split()),
                    verse_numbers=[verse["number"] for verse in current_verses],
                )
            )

        current_verses.clear()

    for element in elements:

        # Start a new paragraph.
        if (
            element["type"] == "marker"
            and element["name"] in {"p", "pi1"}
        ):
            flush()
            continue

        if element["type"] != "verse":
            continue

        verse_text = element.get("text", "").strip()

        if not verse_text:
            continue

        current_words = sum(
            len(v["text"].split())
            for v in current_verses
        )

        verse_words = len(verse_text.split())

        # Flush before adding a verse that exceeds the target.
        if current_verses and current_words + verse_words > target_words:
            flush()

        current_verses.append(element)

    flush()

    return chunks
