
from bible_study_ai.ingestion.usfm_parser import parse_usfm


def test_parses_book_metadata_and_chapter():
    source = r"""
\id EPH World English Bible
\h Ephesians
\c 1
\p
\v 1 Paul, an apostle of Christ Jesus.
\v 2 Grace to you and peace.
"""

    book = parse_usfm(source)

    assert book["usfm_id"] == "EPH"
    assert book["metadata"]["h"] == ["Ephesians"]
    assert len(book["chapters"]) == 1
    assert book["chapters"][0]["number"] == 1

    assert book["chapters"][0]["verses"] == [
        {
            "number": "1",
            "text": "Paul, an apostle of Christ Jesus.",
        },
        {
            "number": "2",
            "text": "Grace to you and peace.",
        },
    ]


def test_preserves_strongs_annotations_and_reading_text():
    source = r"""
\id JHN World English Bible
\c 1
\v 1 In the beginning was the \w Word|strong="G3056"\w*.
"""

    book = parse_usfm(source)
    verse = book["chapters"][0]["elements"][0]

    assert verse["text"] == "In the beginning was the Word."

    word = next(
        child
        for child in verse["children"]
        if child["type"] == "span" and child["name"] == "w"
    )

    assert word["attributes"] == {"strong": "G3056"}
    assert word["children"] == [
        {"type": "text", "value": " Word"}
    ]


def test_excludes_footnotes_from_reading_text():
    source = r"""
\id EPH World English Bible
\c 1
\v 1 Paul\f + \fr 1:1 \ft A footnote.\f* is an apostle.
"""

    book = parse_usfm(source)
    verse = book["chapters"][0]["verses"][0]

    assert verse["text"] == "Paul is an apostle."
    assert "A footnote" not in verse["text"]

    footnote = next(
        child
        for child in book["chapters"][0]["elements"][0]["children"]
        if child["type"] == "span" and child["name"] == "f"
    )

    assert footnote["name"] == "f"


def test_preserves_nested_inline_spans():
    source = r"""
\id JHN World English Bible
\c 1
\v 1 \wj I am the \+w Word|strong="G3056"\+w*.\wj*
"""

    book = parse_usfm(source)
    verse = book["chapters"][0]["elements"][0]

    assert verse["text"] == "I am the Word."

    jesus_words = next(
        child
        for child in verse["children"]
        if child["type"] == "span" and child["name"] == "wj"
    )

    nested_word = next(
        child
        for child in jesus_words["children"]
        if child["type"] == "span" and child["name"] == "+w"
    )

    assert nested_word["attributes"] == {"strong": "G3056"}


def test_preserves_paragraph_markers_in_chapter_order():
    source = r"""
\id EPH World English Bible
\c 1
\p
\v 1 First verse.
\p
\v 2 Second verse.
"""

    book = parse_usfm(source)
    elements = book["chapters"][0]["elements"]

    assert [element["type"] for element in elements] == [
        "marker",
        "verse",
        "marker",
        "verse",
    ]

    assert elements[0]["name"] == "p"
    assert elements[2]["name"] == "p"


def test_preserves_words_split_by_inline_markers():
    source = r"""
\id EPH World English Bible
\c 1
\v 1 They don’\w t|strong="G3756"\w* know.
"""

    book = parse_usfm(source)
    verse = book["chapters"][0]["verses"][0]

    assert verse["text"] == "They don’t know."

def test_preserves_footnote_structure_without_including_it_in_reading_text():
    source = r'''
    \id PSA World English Bible
    \c 1
    \v 2 The LORD\f + \fr 1:2 \ft God's Proper Name is Hebrew "\+wh יהוה\+wh*".\f* is great.
    '''

    book = parse_usfm(source)

    verse = book["chapters"][0]["verses"][0]

    assert verse["text"] == "The LORD is great."

    children = book["chapters"][0]["elements"][0]["children"]

    footnotes = [
        node for node in children
        if node.get("type") == "span" and node.get("name") == "f"
    ]

    assert len(footnotes) == 1

    footnote = footnotes[0]
    assert any(
        node.get("type") == "marker" and node.get("name") == "fr"
        for node in footnote["children"]
    )
    assert any(
        node.get("type") == "marker" and node.get("name") == "ft"
        for node in footnote["children"]
    )

    assert any(
        node.get("type") == "span" and node.get("name") == "+wh"
        for node in footnote["children"]
    )