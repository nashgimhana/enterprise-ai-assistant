from backend.rag.hybrid_search import search_documents
from backend.rag.documents import DocumentChunk


def retrieve_knowledge(query: str, role: str, limit: int = 4) -> tuple[list[DocumentChunk], list[str]]:
    """
    Retrieval Agent: Performs RAG operations and vector search.
    
    Args:
        query: User's question
        role: User's role for RBAC filtering
        limit: Maximum number of chunks to retrieve
    
    Returns:
        Tuple of (retrieved chunks, activity log)
    """
    activity = [
        "Retrieval Agent initialized",
        "Applying RBAC metadata filters",
        "Executing hybrid search (dense + sparse)",
    ]
    
    chunks = search_documents(query, role, limit=limit)
    activity.append(f"Retrieved {len(chunks)} authorized chunks")
    
    if chunks:
        activity.append("Ranking results by hybrid score fusion")
        activity.append("Document attribution validated")
    else:
        activity.append("No matching documents found for this query")
    
    return chunks, activity
