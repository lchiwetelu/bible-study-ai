
from bible_study_ai.rag.chunking import build_chunks


def make_verse(number: str, text: str) -> dict:
    return {
        "type": "verse",
        "number": number,
        "text": text,
        "children": [],
    }


def make_marker(name: str) -> dict:
    return {
        "type": "marker",
        "name": name,
    }


def test_builds_chunk_from_verses():
    elements = [
        make_verse("1", "The Lord is my shepherd."),
        make_verse("2", "He makes me lie down in green pastures."),
    ]

    chunks = build_chunks(
        elements=elements,
        translation="WEB",
        book="PSA",
        chapter=23,
    )

    assert len(chunks) == 1
    assert chunks[0].start_verse == "1"
    assert chunks[0].end_verse == "2"
    assert chunks[0].translation == "WEB"
    assert chunks[0].book == "PSA"
    assert chunks[0].chapter == 23


def test_respects_paragraph_boundaries():
    elements = [
        make_verse("1", "First paragraph."),
        make_marker("p"),
        make_verse("2", "Second paragraph."),
    ]

    chunks = build_chunks(
        elements=elements,
        translation="WEB",
        book="ROM",
        chapter=8,
    )

    assert len(chunks) == 2


def test_splits_when_target_word_count_is_exceeded():
    elements = [
        make_verse("1", " ".join(["word"] * 120)),
        make_verse("2", " ".join(["word"] * 100)),
    ]

    chunks = build_chunks(
        elements=elements,
        translation="WEB",
        book="ROM",
        chapter=8,
        target_words=200,
    )

    assert len(chunks) == 2
    assert chunks[0].end_verse == "1"
    assert chunks[1].start_verse == "2"
    assert all(chunk.word_count <= 200 for chunk in chunks)


def test_preserves_all_verses_exactly_once():
    elements = [
        make_verse("1", "First verse."),
        make_verse("2", "Second verse."),
        make_verse("3", "Third verse."),
    ]

    chunks = build_chunks(
        elements=elements,
        translation="WEB",
        book="ROM",
        chapter=8,
    )

    covered_verses = []

    for chunk in chunks:
        start = int(chunk.start_verse)
        end = int(chunk.end_verse)
        covered_verses.extend(range(start, end + 1))

    assert covered_verses == [1, 2, 3]


def test_splits_large_paragraph_without_losing_verses():
    elements = [
        make_verse("1", " ".join(["word"] * 120)),
        make_verse("2", " ".join(["word"] * 120)),
        make_verse("3", " ".join(["word"] * 120)),
    ]

    chunks = build_chunks(
        elements=elements,
        translation="WEB",
        book="ROM",
        chapter=8,
        target_words=200,
    )

    assert len(chunks) == 3
    assert [chunk.start_verse for chunk in chunks] == ["1", "2", "3"]
    assert [chunk.end_verse for chunk in chunks] == ["1", "2", "3"]
