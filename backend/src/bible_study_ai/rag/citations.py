
import re


REFERENCE_PATTERN = re.compile(
    r"^(.+?)\s+(\d+):(\d+)(?:-(\d+))?$"
)


def parse_reference(reference: str) -> tuple[str, int, int, int] | None:
    """Parse a Bible reference into book, chapter, start verse and end verse."""

    match = REFERENCE_PATTERN.fullmatch(reference.strip())

    if not match:
        return None

    book, chapter, start_verse, end_verse = match.groups()

    chapter = int(chapter)
    start_verse = int(start_verse)
    end_verse = int(end_verse) if end_verse else start_verse

    if chapter < 1 or start_verse < 1 or end_verse < start_verse:
        return None

    return book.strip().casefold(), chapter, start_verse, end_verse


def is_reference_covered(
    reference: str,
    supplied_references: set[str],
) -> bool:
    """Check whether a cited verse or verse range is within supplied passages."""

    candidate = parse_reference(reference)

    if candidate is None:
        return False

    candidate_book, candidate_chapter, candidate_start, candidate_end = (
        candidate
    )

    for supplied_reference in supplied_references:
        supplied = parse_reference(supplied_reference)

        if supplied is None:
            continue

        supplied_book, supplied_chapter, supplied_start, supplied_end = (
            supplied
        )

        if (
            candidate_book == supplied_book
            and candidate_chapter == supplied_chapter
            and candidate_start >= supplied_start
            and candidate_end <= supplied_end
        ):
            return True

    return False
