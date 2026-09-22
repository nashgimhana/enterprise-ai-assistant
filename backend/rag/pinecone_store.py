from backend.config import (
    EMBEDDING_DIMENSION,
    PINECONE_API_KEY,
    PINECONE_CLOUD,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE,
    PINECONE_REGION,
)
from backend.rag.documents import DocumentChunk
from backend.security.auth import allowed_access_levels


class PineconeConfigurationError(RuntimeError):
    pass


class PineconeDocumentStore:
    def __init__(
        self,
        api_key: str = PINECONE_API_KEY,
        index_name: str = PINECONE_INDEX_NAME,
        namespace: str = PINECONE_NAMESPACE,
    ) -> None:
        if not api_key:
            raise PineconeConfigurationError("PINECONE_API_KEY is not configured")
        if not index_name:
            raise PineconeConfigurationError("PINECONE_INDEX_NAME is not configured")

        try:
            from pinecone import Pinecone
        except ImportError as exc:
            raise PineconeConfigurationError("Install the pinecone package to use Pinecone") from exc

        self.index_name = index_name
        self.namespace = namespace
        self.client = Pinecone(api_key=api_key)
        self.index = self.client.Index(index_name)

    def upsert_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> int:
        vectors = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            metadata = chunk.metadata()
            metadata["text"] = chunk.content
            vectors.append({"id": chunk.chunk_id, "values": embedding, "metadata": metadata})

        if vectors:
            self.index.upsert(vectors=vectors, namespace=self.namespace)
        return len(vectors)

    def query(self, embedding: list[float], role: str, limit: int = 6) -> list[DocumentChunk]:
        response = self.index.query(
            vector=embedding,
            top_k=limit,
            include_metadata=True,
            namespace=self.namespace,
            filter={"access_level": {"$in": sorted(allowed_access_levels(role))}},
        )

        matches = response.get("matches", []) if isinstance(response, dict) else getattr(response, "matches", [])
        chunks: list[DocumentChunk] = []
        for match in matches:
            if isinstance(match, dict):
                metadata = match.get("metadata", {}) or {}
                match_id = match.get("id", "")
                score = match.get("score", 0.0)
            else:
                metadata = getattr(match, "metadata", {}) or {}
                match_id = getattr(match, "id", "")
                score = getattr(match, "score", 0.0)

            chunks.append(
                DocumentChunk(
                    chunk_id=metadata.get("chunk_id", match_id),
                    document_id=metadata.get("document_id", ""),
                    title=metadata.get("title", ""),
                    department=metadata.get("department", ""),
                    document_type=metadata.get("document_type", ""),
                    access_level=metadata.get("access_level", "internal"),
                    source=metadata.get("source", ""),
                    content=metadata.get("text", ""),
                    score=float(score),
                )
            )
        return chunks


def ensure_pinecone_index() -> None:
    if not PINECONE_API_KEY:
        raise PineconeConfigurationError("PINECONE_API_KEY is not configured")
    if not PINECONE_INDEX_NAME:
        raise PineconeConfigurationError("PINECONE_INDEX_NAME is not configured")

    try:
        from pinecone import Pinecone, ServerlessSpec
    except ImportError as exc:
        raise PineconeConfigurationError("Install the pinecone package to use Pinecone") from exc

    client = Pinecone(api_key=PINECONE_API_KEY)
    indexes = client.list_indexes()
    if hasattr(indexes, "names"):
        existing_names = set(indexes.names())
    else:
        existing_names = {index["name"] if isinstance(index, dict) else index.name for index in indexes}
    if PINECONE_INDEX_NAME in existing_names:
        return

    client.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
    )
