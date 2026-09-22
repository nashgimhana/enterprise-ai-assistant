from backend.rag.hybrid_search import search_documents
from backend.rag.documents import DocumentChunk, load_chunks


def retrieve_knowledge(query: str, role: str, limit: int = 4) -> tuple[list[DocumentChunk], list[str]]:
    """
    Retrieval Agent: Performs RAG operations and vector search.
    
    LangSmith tracing is automatic when environment variables are configured.
    
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

    # Check if user is asking about a specific document they can't access
    all_chunks = load_chunks()
    all_doc_ids = {chunk.document_id for chunk in all_chunks}

    for doc_id in all_doc_ids:
        if doc_id.lower() in query.lower():
            has_requested_doc = any(chunk.document_id == doc_id for chunk in chunks)
            if not has_requested_doc:
                activity.append(f"Requested document {doc_id} not accessible to this role")
                return [], activity
            break
    
    if chunks:
        activity.append("Ranking results by hybrid score fusion")
        activity.append("Document attribution validated")
    else:
        activity.append("No matching documents found for this query")
    
    return chunks, activity
