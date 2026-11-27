
import ollama


class EmbeddingService:
    def __init__(
        self,
        model: str = "nomic-embed-text",
    ):
        self.model = model
        self.client = ollama.Client()

    def embed(self, text: str) -> list[float]:
        response = self.client.embed(
            model=self.model,
            input=text,
        )

        return response.embeddings[0]

    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        response = self.client.embed(
            model=self.model,
            input=texts,
        )

        return response.embeddings
