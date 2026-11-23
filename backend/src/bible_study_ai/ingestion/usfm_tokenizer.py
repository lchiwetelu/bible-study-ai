
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    type: str
    value: str
    marker: str | None = None
    attributes: dict[str, str] | None = None
    is_closing: bool = False


MARKER_PATTERN = re.compile(
    r"\\(?P<marker>\+?[A-Za-z][A-Za-z0-9]*)(?P<closing>\*)?"
)

ATTRIBUTE_PATTERN = re.compile(
    r'([A-Za-z][A-Za-z0-9_-]*)="([^"]*)"'
)


def _parse_attributes(raw: str) -> dict[str, str]:
    attributes: dict[str, str] = {}

    for match in ATTRIBUTE_PATTERN.finditer(raw):
        name, value = match.groups()
        attributes[name] = value

    return attributes


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    position = 0

    while position < len(source):
        match = MARKER_PATTERN.search(source, position)

        if match is None:
            remaining = source[position:]

            if remaining:
                tokens.append(Token(type="text", value=remaining))

            break

        preceding_text = source[position:match.start()]

        if preceding_text:
            tokens.append(Token(type="text", value=preceding_text))

        marker = match.group("marker")
        is_closing = match.group("closing") is not None
        marker_end = match.end()

        attributes = None
        word = None

        # Extract attributes from opening word markers.
        if marker in ("w", "+w") and not is_closing:
            next_marker = MARKER_PATTERN.search(source, marker_end)

            if next_marker is not None:
                marker_content = source[marker_end:next_marker.start()]
                attribute_separator = marker_content.find("|")

                if attribute_separator != -1:
                    word = marker_content[:attribute_separator]
                    raw_attributes = marker_content[attribute_separator + 1:]
                    attributes = _parse_attributes(raw_attributes)
                    marker_end = next_marker.start()

        # Emit the opening marker before its content.
        tokens.append(
            Token(
                type="marker",
                value=match.group(0)[1:],
                marker=marker,
                attributes=attributes,
                is_closing=is_closing,
            )
        )

        if word:
            tokens.append(Token(type="text", value=word))

        position = marker_end

    return tokens
