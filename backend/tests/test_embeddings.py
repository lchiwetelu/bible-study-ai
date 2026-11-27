
from bible_study_ai.rag.embeddings import EmbeddingService


def test_generates_embedding():
    service = EmbeddingService()

    embedding = service.embed("The Lord is my shepherd")

    assert len(embedding) == 768
    assert all(isinstance(value, float) for value in embedding)


def test_generates_batch_embeddings():
    service = EmbeddingService()

    embeddings = service.embed_batch([
        "The Lord is my shepherd",
        "Jesus is the son of God",
    ])

    assert len(embeddings) == 2
    assert all(len(embedding) == 768 for embedding in embeddings)


def test_empty_batch_returns_empty_list():
    service = EmbeddingService()

    assert service.embed_batch([]) == []
