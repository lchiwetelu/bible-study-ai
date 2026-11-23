
import re
from dataclasses import dataclass


MARKER_PATTERN = re.compile(
    r"\\(?P<marker>\+?[A-Za-z][A-Za-z0-9]*)(?P<closing>\*)?"
)

ATTRIBUTE_PATTERN = re.compile(
    r'([A-Za-z][A-Za-z0-9_-]*)="([^"]*)"'
)


@dataclass(frozen=True)
class Token:
    type: str
    value: str
    marker: str | None = None
    attributes: dict[str, str] | None = None
    is_closing: bool = False


def parse_attributes(raw: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2)
        for match in ATTRIBUTE_PATTERN.finditer(raw)
    }


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    position = 0

    for match in MARKER_PATTERN.finditer(source):
        if match.start() > position:
            tokens.append(
                Token(
                    type="text",
                    value=source[position:match.start()],
                )
            )

        marker = match.group("marker")
        is_closing = match.group("closing") is not None

        tokens.append(
            Token(
                type="marker",
                value=match.group(0)[1:],
                marker=marker,
                is_closing=is_closing,
            )
        )

        position = match.end()

    if position < len(source):
        tokens.append(
            Token(type="text", value=source[position:])
        )

    # USFM character attributes appear in the text immediately
    # following their opening marker, separated by a pipe.
    # Keep the text and attributes separate without consuming
    # subsequent markers or nested content.
    normalized: list[Token] = []

    for token in tokens:
        if (
            token.type == "text"
            and normalized
            and normalized[-1].type == "marker"
            and not normalized[-1].is_closing
            and "|" in token.value
        ):
            text, raw_attributes = token.value.split("|", 1)

            previous = normalized[-1]
            normalized[-1] = Token(
                type="marker",
                value=previous.value,
                marker=previous.marker,
                attributes=parse_attributes(raw_attributes),
                is_closing=False,
            )

            if text:
                normalized.append(
                    Token(type="text", value=text)
                )
        else:
            normalized.append(token)

    return normalized
