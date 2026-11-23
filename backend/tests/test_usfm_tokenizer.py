
from bible_study_ai.ingestion.usfm_tokenizer import tokenize


def test_tokenizes_structural_markers():
    tokens = tokenize(r"\p\v 1 In the beginning")

    markers = [token.marker for token in tokens if token.type == "marker"]

    assert markers == ["p", "v"]


def test_tokenizes_word_with_strongs_attribute():
    tokens = tokenize(r'\w Word|strong="G3056"\w*')

    assert tokens[0].marker == "w"
    assert tokens[0].attributes == {"strong": "G3056"}
    assert tokens[1].value == " Word"
    assert tokens[2].is_closing


def test_tokenizes_nested_word_marker():
    tokens = tokenize(r'\wj I am the \+w Word|strong="H3068"\+w*.\wj*')

    markers = [
        (token.marker, token.is_closing)
        for token in tokens
        if token.type == "marker"
    ]

    assert markers == [
        ("wj", False),
        ("+w", False),
        ("+w", True),
        ("wj", True),
    ]

    nested_word = next(
        token for token in tokens
        if token.marker == "+w" and not token.is_closing
    )

    assert nested_word.attributes == {"strong": "H3068"}


def test_tokenizes_footnotes():
    tokens = tokenize(r'\f + \fr 1:1 \ft A footnote.\f*')

    markers = [
        (token.marker, token.is_closing)
        for token in tokens
        if token.type == "marker"
    ]

    assert markers == [
        ("f", False),
        ("fr", False),
        ("ft", False),
        ("f", True),
    ]


def test_preserves_whitespace():
    source = r"\p\v 1 In the beginning"

    tokens = tokenize(source)

    text = "".join(
        token.value
        for token in tokens
        if token.type == "text"
    )

    assert text == " 1 In the beginning"
