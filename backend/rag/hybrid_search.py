from backend.rag.bm25 import bm25_search
from backend.rag.documents import DocumentChunk
from backend.rag.embeddings import EmbeddingConfigurationError, get_embedding_client
from backend.rag.pinecone_store import PineconeConfigurationError, PineconeDocumentStore


def search_documents(query: str, role: str, limit: int = 4) -> list[DocumentChunk]:
    keyword_results = bm25_search(query, role, limit=limit * 2)
    vector_results = _vector_search(query, role, limit=limit * 2)

    if not vector_results:
        return keyword_results[:limit]

    return _fuse_results(keyword_results, vector_results, limit=limit)


def _vector_search(query: str, role: str, limit: int) -> list[DocumentChunk]:
    try:
        embedding = get_embedding_client().embed_query(query)
        return PineconeDocumentStore().query(embedding, role, limit=limit)
    except (EmbeddingConfigurationError, PineconeConfigurationError):
        return []
    except Exception:
        # External embedding/vector providers must not break the local demo path.
        return []


def _fuse_results(keyword_results: list[DocumentChunk], vector_results: list[DocumentChunk], limit: int) -> list[DocumentChunk]:
    fused_scores: dict[str, float] = {}
    chunks_by_id: dict[str, DocumentChunk] = {}

    for rank, chunk in enumerate(keyword_results, start=1):
        fused_scores[chunk.chunk_id] = fused_scores.get(chunk.chunk_id, 0.0) + 1 / (60 + rank)
        chunks_by_id[chunk.chunk_id] = chunk

    for rank, chunk in enumerate(vector_results, start=1):
        fused_scores[chunk.chunk_id] = fused_scores.get(chunk.chunk_id, 0.0) + 1 / (60 + rank)
        chunks_by_id[chunk.chunk_id] = chunk

    ranked_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)
    return [_with_score(chunks_by_id[chunk_id], fused_scores[chunk_id]) for chunk_id in ranked_ids[:limit]]


def _with_score(chunk: DocumentChunk, score: float) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        title=chunk.title,
        department=chunk.department,
        document_type=chunk.document_type,
        access_level=chunk.access_level,
        source=chunk.source,
        content=chunk.content,
        score=score,
    )
