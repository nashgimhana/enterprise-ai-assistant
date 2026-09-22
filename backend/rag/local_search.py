from backend.rag.bm25 import bm25_search
from backend.rag.documents import DocumentChunk


def search_documents(query: str, role: str, limit: int = 4) -> list[DocumentChunk]:
    return bm25_search(query, role, limit)
