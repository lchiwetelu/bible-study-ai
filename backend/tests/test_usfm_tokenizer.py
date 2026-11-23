
from bible_study_ai.ingestion.usfm_tokenizer import tokenize


def test_tokenizes_word_with_strongs_attribute():
    source = r'\w Word|strong="G3056"\w*'

    tokens = tokenize(source)

    assert len(tokens) == 3

    assert tokens[0].marker == "w"
    assert tokens[0].attributes == {"strong": "G3056"}
    assert not tokens[0].is_closing

    assert tokens[1].type == "text"
    assert tokens[1].value == " Word"

    assert tokens[2].marker == "w"
    assert tokens[2].is_closing


def test_tokenizes_jesus_words_with_nested_word_marker():
    source = r'\wj I am the \+w Word|strong="G3056"\+w*.\wj*'

    tokens = tokenize(source)

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


def test_extracts_attributes_from_nested_word_marker():
    source = r'\wj I am the \+w Word|strong="G3056"\+w*.\wj*'

    tokens = tokenize(source)

    nested_word_marker = next(
        token
        for token in tokens
        if token.type == "marker" and token.marker == "+w"
        and not token.is_closing
    )

    assert nested_word_marker.attributes == {"strong": "G3056"}



def test_tokenizes_footnote_markers():
    source = r'\f + \fr 1:1 \ft A footnote.\f*'

    tokens = tokenize(source)

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


def test_preserves_text_and_whitespace():
    source = r'\p\v 1 In the beginning'

    tokens = tokenize(source)

    text = "".join(
        token.value
        for token in tokens
        if token.type == "text"
    )

    assert text == " 1 In the beginning"
