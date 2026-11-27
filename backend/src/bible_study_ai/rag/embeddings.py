
import ollama


class EmbeddingService:
    def __init__(
        self,
        model: str = "nomic-embed-text",
    ):
        self.model = model
        self.client = ollama.Client()

    def embed(self, text: str) -> list[float]:
        """Generate an embedding for a search query."""

        response = self.client.embed(
            model=self.model,
            input=f"search_query: {text}",
        )

        return response.embeddings[0]

    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate embeddings for documents being indexed."""

        if not texts:
            return []

        prefixed_texts = [
            f"search_document: {text}"
            for text in texts
        ]

        response = self.client.embed(
            model=self.model,
            input=prefixed_texts,
        )

        return response.embeddings
