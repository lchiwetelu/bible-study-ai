
import re
from typing import Any

from bible_study_ai.ingestion.usfm_tokenizer import Token, tokenize


CHAPTER_MARKER = "c"
VERSE_MARKER = "v"

STRUCTURAL_MARKERS = {
    "p", "m", "po", "pr",
    "q1", "q2", "q3", "q4",
    "b", "nb",
    "li1", "li2", "li3", "li4",
    "ili", "pi1", "pi2",
    "pc", "mi",
    "s1", "s2", "s3",
    "ms1", "ms2", "ms3",
    "is1", "is2",
    "mt1", "mt2", "mt3",
    "ip", "im", "imi",
    "d", "sp", "cl", "cp",
}

NON_SCRIPTURE_SPANS = {"f", "x"}

VERSE_NUMBER_PATTERN = re.compile(
    r"^\s*(\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?)\s*(.*)$",
    re.DOTALL,
)

CHAPTER_NUMBER_PATTERN = re.compile(
    r"^\s*(\d+)\s*(.*)$",
    re.DOTALL,
)


def _text_node(value: str) -> dict[str, Any]:
    return {"type": "text", "value": value}


def _marker_node(token: Token) -> dict[str, Any]:
    node: dict[str, Any] = {
        "type": "marker",
        "name": token.marker,
    }

    if token.attributes:
        node["attributes"] = token.attributes

    if token.is_closing:
        node["is_closing"] = True

    return node


def _parse_number(
    tokens: list[Token],
    index: int,
    pattern: re.Pattern,
) -> tuple[str, str, int]:
    if index >= len(tokens) or tokens[index].type != "text":
        raise ValueError(
            f"Expected text containing a number at token index {index}"
        )

    match = pattern.match(tokens[index].value)

    if not match:
        raise ValueError(
            f"Could not parse number from {tokens[index].value!r}"
        )

    return match.group(1), match.group(2), index + 1


def _has_verse_content_before_boundary(
    tokens: list[Token],
    start: int,
) -> bool:
    """Check whether a structural marker introduces content within a verse."""

    for token in tokens[start:]:
        if (
            token.type == "marker"
            and not token.is_closing
            and token.marker in {CHAPTER_MARKER, VERSE_MARKER}
        ):
            return False

        if token.type == "text":
            if token.value.strip():
                return True
            continue

        if (
            token.type == "marker"
            and not token.is_closing
            and token.marker in STRUCTURAL_MARKERS
        ):
            continue

        return True

    return False


def _parse_inline(
    tokens: list[Token],
    start: int,
    stop_markers: set[str],
    closing_markers: set[str],
) -> tuple[list[dict[str, Any]], int]:
    """Parse nested inline spans and verse-level structure."""

    roots: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []

    def current_children() -> list[dict[str, Any]]:
        return stack[-1]["children"] if stack else roots

    index = start

    while index < len(tokens):
        token = tokens[index]

        if token.type == "text":
            if token.value:
                current_children().append(_text_node(token.value))

            index += 1
            continue

        marker = token.marker or ""

        if marker in stop_markers:
            break

        # A structural marker belongs to the current verse when it
        # introduces content before the next verse/chapter boundary.
        # Otherwise, leave it at chapter level.
        if (
            marker in STRUCTURAL_MARKERS
            and not token.is_closing
            and not _has_verse_content_before_boundary(tokens, index + 1)
        ):
            break

        if token.is_closing:
            matching_index = next(
                (
                    i
                    for i in range(len(stack) - 1, -1, -1)
                    if stack[i]["name"] == marker
                ),
                None,
            )

            if matching_index is None:
                current_children().append(_marker_node(token))
            else:
                # Close the matching span and any malformed
                # unclosed spans nested inside it.
                del stack[matching_index:]

            index += 1
            continue

        if marker in closing_markers:
            node: dict[str, Any] = {
                "type": "span",
                "name": marker,
                "children": [],
            }

            if token.attributes:
                node["attributes"] = token.attributes

            current_children().append(node)
            stack.append(node)
        else:
            current_children().append(_marker_node(token))

        index += 1

    return roots, index


def _normalize_reading_text(
    nodes: list[dict[str, Any]],
) -> str:
    fragments: list[str] = []

    def append_text(value: str, is_word_span: bool = False) -> None:
        if is_word_span and fragments:
            previous = "".join(fragments)

            # USFM word markers can split a word across the
            # marker boundary. Remove formatting whitespace
            # only when the previous text ends mid-word.
            if previous and not previous[-1].isspace():
                value = value.lstrip()

        if value:
            fragments.append(value)

    def walk(items: list[dict[str, Any]]) -> None:
        for node in items:
            if node["type"] == "text":
                append_text(node["value"])

            elif node["type"] == "span":
                name = node["name"]

                if name in NON_SCRIPTURE_SPANS:
                    continue

                if name in {"w", "+w"}:
                    word_text = _normalize_reading_text(
                        node["children"]
                    )
                    append_text(word_text, is_word_span=True)
                else:
                    walk(node["children"])

    walk(nodes)

    return re.sub(r"\s+", " ", "".join(fragments)).strip()


def parse_usfm(source: str) -> dict[str, Any]:
    tokens = tokenize(source)

    closing_markers = {
        token.marker
        for token in tokens
        if token.type == "marker" and token.is_closing
    }

    book: dict[str, Any] = {
        "usfm_id": None,
        "metadata": {},
        "chapters": [],
    }

    index = 0

    # Parse book-level metadata before the first chapter.
    while index < len(tokens):
        token = tokens[index]

        if (
            token.type == "marker"
            and token.marker == CHAPTER_MARKER
            and not token.is_closing
        ):
            break

        if token.type == "marker" and not token.is_closing:
            marker = token.marker or ""
            value = ""

            if (
                index + 1 < len(tokens)
                and tokens[index + 1].type == "text"
            ):
                value = tokens[index + 1].value.strip()

            book["metadata"].setdefault(marker, []).append(value)

            if marker == "id" and value:
                book["usfm_id"] = value.split()[0]

        index += 1

    # Parse chapters and their ordered elements.
    while index < len(tokens):
        token = tokens[index]

        if not (
            token.type == "marker"
            and token.marker == CHAPTER_MARKER
            and not token.is_closing
        ):
            index += 1
            continue

        chapter_number, remaining_text, index = _parse_number(
            tokens,
            index + 1,
            CHAPTER_NUMBER_PATTERN,
        )

        chapter: dict[str, Any] = {
            "number": int(chapter_number),
            "elements": [],
        }

        if remaining_text:
            chapter["elements"].append(_text_node(remaining_text))

        while index < len(tokens):
            current = tokens[index]

            if (
                current.type == "marker"
                and current.marker == CHAPTER_MARKER
                and not current.is_closing
            ):
                break

            if (
                current.type == "marker"
                and current.marker == VERSE_MARKER
                and not current.is_closing
            ):
                verse_number, remaining_text, index = _parse_number(
                    tokens,
                    index + 1,
                    VERSE_NUMBER_PATTERN,
                )

                verse: dict[str, Any] = {
                    "type": "verse",
                    "number": verse_number,
                    "children": [],
                }

                if remaining_text:
                    verse["children"].append(
                        _text_node(remaining_text)
                    )

                inline_nodes, index = _parse_inline(
                    tokens,
                    index,
                    {CHAPTER_MARKER, VERSE_MARKER},
                    closing_markers,
                )

                verse["children"].extend(inline_nodes)
                verse["text"] = _normalize_reading_text(
                    verse["children"]
                )

                chapter["elements"].append(verse)
                continue

            if current.type == "marker":
                chapter["elements"].append(_marker_node(current))
            elif current.value.strip():
                chapter["elements"].append(_text_node(current.value))

            index += 1

        chapter["verses"] = [
            {
                "number": element["number"],
                "text": element["text"],
            }
            for element in chapter["elements"]
            if element["type"] == "verse"
        ]

        book["chapters"].append(chapter)

    return book
