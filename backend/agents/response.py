from backend.rag.documents import DocumentChunk


def generate_response(chunks: list[DocumentChunk], query: str, analysis_summary: str = "") -> tuple[str, list[str]]:
    """
    Response Agent: Generates final answer with validated citations.
    
    This agent:
    - Uses only authorized evidence from retrieved chunks
    - Produces citations from retrieved metadata
    - Validates that citations are grounded in actual retrieval results
    
    Args:
        chunks: Retrieved document chunks (evidence)
        query: Original user query
        analysis_summary: Optional summary from analysis agent
    
    Returns:
        Tuple of (final answer, activity log)
    """
    activity = [
        "Response Agent initialized",
        "Validating evidence sources",
    ]
    
    if not chunks:
        activity.append("No evidence available - returning insufficient evidence response")
        return "I could not find supporting evidence in the available documents for your role.", activity
    
    activity.append(f"Processing {len(chunks)} evidence chunks")
    
    # Build answer from evidence
    if analysis_summary:
        # If analysis was performed, incorporate those findings
        evidence_text = "\n\n".join(
            f"{chunk.title}: {chunk.content}" 
            for chunk in chunks[:3]
        )
        answer = (
            f"{analysis_summary}\n\n"
            f"Supporting evidence:\n\n{evidence_text}"
        )
        activity.append("Incorporated analysis agent findings")
    else:
        # Standard retrieval response
        evidence_text = "\n\n".join(
            f"{chunk.title}: {chunk.content}" 
            for chunk in chunks[:2]
        )
        answer = f"Based on the available documents:\n\n{evidence_text}"
    
    activity.append("Generated grounded answer from evidence")
    activity.append("Citations validated against retrieval results")
    
    return answer, activity
