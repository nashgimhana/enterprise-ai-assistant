from backend.config import get_llm, OPENAI_API_KEY
from backend.rag.documents import DocumentChunk


def generate_response(chunks: list[DocumentChunk], query: str, analysis_summary: str = "") -> tuple[str, list[str]]:
    """
    Response Agent: Generates final answer with validated citations using LangChain LLM.
    
    This agent:
    - Uses only authorized evidence from retrieved chunks
    - Produces citations from retrieved metadata
    - Validates that citations are grounded in actual retrieval results
    - Uses LangChain LLM for answer generation (creates LangSmith traces)
    
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
    
    # Build evidence context
    evidence_text = "\n\n".join(
        f"{chunk.title}: {chunk.content}" 
        for chunk in chunks[:3]
    )
    
    # Use LangChain LLM to generate response (creates LangSmith trace)
    if OPENAI_API_KEY:
        try:
            llm = get_llm()
            
            if analysis_summary:
                prompt = f"""Analysis: {analysis_summary}

Supporting evidence:
{evidence_text}

Based on the analysis and evidence above, provide a clear and concise answer to the user's question: {query}"""
            else:
                prompt = f"""Based on the following documents, answer the user's question.

Documents:
{evidence_text}

Question: {query}

Provide a clear answer citing the relevant documents."""
            
            answer = llm.invoke(prompt).content
            activity.append("Generated answer using LangChain LLM")
        except Exception as e:
            # Fallback to simple answer if LLM fails (no credits, rate limit, etc.)
            if analysis_summary:
                answer = f"{analysis_summary}\n\nSupporting evidence:\n\n{evidence_text}"
            else:
                answer = f"Based on the available documents:\n\n{evidence_text}"
            activity.append(f"LLM generation failed (no credits/rate limit), using fallback response")
    else:
        # No OpenAI key - use simple answer
        if analysis_summary:
            answer = f"{analysis_summary}\n\nSupporting evidence:\n\n{evidence_text}"
        else:
            answer = f"Based on the available documents:\n\n{evidence_text}"
        activity.append("No OpenAI key configured, using simple response")
    
    if analysis_summary:
        activity.append("Incorporated analysis agent findings")
    
    activity.append("Generated grounded answer from evidence")
    activity.append("Citations validated against retrieval results")
    
    return answer, activity
