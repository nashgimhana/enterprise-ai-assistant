from backend.config import (
    EMBEDDING_DIMENSION,
    EMBEDDING_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_EMBEDDING_MODEL,
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL,
)


class EmbeddingConfigurationError(RuntimeError):
    pass


class OpenAIEmbeddingClient:
    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = OPENAI_EMBEDDING_MODEL) -> None:
        if not api_key:
            raise EmbeddingConfigurationError("OPENAI_API_KEY is not configured")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise EmbeddingConfigurationError("Install the openai package to use embeddings") from exc

        self.model = model
        self.client = OpenAI(api_key=api_key)

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


class GeminiEmbeddingClient:
    def __init__(
        self,
        api_key: str = GEMINI_API_KEY,
        model: str = GEMINI_EMBEDDING_MODEL,
        dimension: int = EMBEDDING_DIMENSION,
    ) -> None:
        if not api_key:
            raise EmbeddingConfigurationError("GEMINI_API_KEY is not configured")

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise EmbeddingConfigurationError("Install the google-genai package to use Gemini embeddings") from exc

        self.model = model
        self.dimension = dimension
        self.types = types
        self.client = genai.Client(api_key=api_key)

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(f"task: search result | query: {text}")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(f"title: none | text: {text}") for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=self.types.EmbedContentConfig(output_dimensionality=self.dimension),
        )
        return list(response.embeddings[0].values)


def get_embedding_client() -> OpenAIEmbeddingClient | GeminiEmbeddingClient:
    if EMBEDDING_PROVIDER == "gemini":
        return GeminiEmbeddingClient()
    if EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbeddingClient()
    raise EmbeddingConfigurationError(f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")
