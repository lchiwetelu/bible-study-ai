
from pathlib import Path

import chromadb

from bible_study_ai.config import settings
from bible_study_ai.rag.chunking import PassageChunk
from bible_study_ai.rag.embeddings import EmbeddingService


class VectorStore:
    def __init__(
        self,
        persist_directory: Path | None = None,
        collection_name: str | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        self.persist_directory = (
            persist_directory or settings.chroma_persist_directory
        )

        self.collection_name = (
            collection_name or settings.chroma_collection_name
        )

        self.persist_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
        )

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        self.embedding_service = (
            embedding_service or EmbeddingService()
        )

    @staticmethod
    def _build_id(chunk: PassageChunk) -> str:
        return (
            f"{chunk.translation}:"
            f"{chunk.book}:"
            f"{chunk.chapter}:"
            f"{chunk.start_verse}-"
            f"{chunk.end_verse}"
        )

    def upsert_chunks(
        self,
        chunks: list[PassageChunk],
        batch_size: int = 100,
    ) -> int:
        if not chunks:
            return 0

        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero")

        total_upserted = 0

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]

            documents = [
                chunk.text
                for chunk in batch
            ]

            embeddings = self.embedding_service.embed_batch(
                documents
            )

            ids = [
                self._build_id(chunk)
                for chunk in batch
            ]

            metadatas = [
                {
                    "translation": chunk.translation,
                    "book": chunk.book,
                    "chapter": chunk.chapter,
                    "start_verse": chunk.start_verse,
                    "end_verse": chunk.end_verse,
                    "word_count": chunk.word_count,
                }
                for chunk in batch
            ]

            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            total_upserted += len(batch)

        return total_upserted

    def search(
        self,
        query: str,
        n_results: int = 5,
    ) -> dict:
        if not query.strip():
            raise ValueError("Search query cannot be empty")

        if n_results < 1:
            raise ValueError("n_results must be greater than zero")

        query_embedding = self.embedding_service.embed(query)

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.collection.count()),
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

    def count(self) -> int:
        return self.collection.count()
