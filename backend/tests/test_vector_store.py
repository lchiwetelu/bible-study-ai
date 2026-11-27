
from unittest.mock import MagicMock

from bible_study_ai.rag.chunking import PassageChunk
from bible_study_ai.rag.vector_store import VectorStore


def test_upserts_and_searches_chunks(tmp_path):
    embedding_service = MagicMock()

    embedding_service.embed_batch.return_value = [
        [0.1] * 768
    ]

    embedding_service.embed.return_value = [0.2] * 768

    store = VectorStore(
        persist_directory=tmp_path / "chroma",
        collection_name="test_bible_passages",
        embedding_service=embedding_service,
    )

    chunk = PassageChunk(
        translation="WEB",
        book="PSA",
        chapter=23,
        start_verse="1",
        end_verse="6",
        verse_numbers=["1", "2", "3", "4", "5", "6"],
        text="The Lord is my shepherd.",
        word_count=114,
    )

    upserted = store.upsert_chunks([chunk])

    assert upserted == 1
    assert store.count() == 1

    results = store.search(
        "Who is my shepherd?",
        n_results=1,
    )

    assert results["documents"][0][0] == "The Lord is my shepherd."
    assert results["metadatas"][0][0]["book"] == "PSA"
    assert results["metadatas"][0][0]["chapter"] == 23


def test_upsert_does_not_create_duplicates(tmp_path):
    embedding_service = MagicMock()
    embedding_service.embed_batch.return_value = [[0.1] * 768]

    store = VectorStore(
        persist_directory=tmp_path / "chroma",
        collection_name="test_bible_passages",
        embedding_service=embedding_service,
    )

    chunk = PassageChunk(
        translation="WEB",
        book="PSA",
        chapter=23,
        start_verse="1",
        end_verse="6",
        verse_numbers=["1", "2", "3", "4", "5", "6"],
        text="The Lord is my shepherd.",
        word_count=114,
    )

    store.upsert_chunks([chunk])
    store.upsert_chunks([chunk])

    assert store.count() == 1
