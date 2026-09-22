from backend.rag.hybrid_search import search_documents
from backend.rag.documents import DocumentChunk


def knowledge_search_tool(query: str, role: str, limit: int = 4) -> tuple[list[dict], str]:
    """
    Knowledge Search Tool: Search indexed documents with RBAC filtering.
    
    This tool can be called by agents to retrieve relevant document chunks.
    It applies role-based access control through metadata filtering.
    
    Args:
        query: Search query
        role: User role for RBAC
        limit: Maximum number of results
    
    Returns:
        Tuple of (chunk dictionaries, status message)
    """
    chunks = search_documents(query, role, limit=limit)
    
    # Convert to serializable dicts
    chunk_dicts = [
        {
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "title": c.title,
            "department": c.department,
            "document_type": c.document_type,
            "access_level": c.access_level,
            "source": c.source,
            "content": c.content,
            "score": c.score,
        }
        for c in chunks
    ]
    
    status = f"Retrieved {len(chunks)} chunks for role '{role}'"
    return chunk_dicts, status
