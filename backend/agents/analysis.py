from backend.rag.documents import DocumentChunk


def analyze_documents(chunks: list[DocumentChunk], query: str) -> tuple[str, list[str]]:
    """
    Analysis/RLM Agent: Performs deep investigation and recursive exploration.
    
    LangSmith tracing is automatic when environment variables are configured.
    
    This agent demonstrates simplified Recursive Language Model concepts by:
    - Grouping retrieved documents into batches
    - Analyzing patterns across batches
    - Aggregating findings
    
    Args:
        chunks: Retrieved document chunks
        query: Original user query for context
    
    Returns:
        Tuple of (analysis summary, activity log)
    """
    activity = [
        "Analysis Agent initialized",
        "Decomposing task into analysis batches",
    ]
    
    if not chunks:
        activity.append("No documents available for analysis")
        return "No evidence available for analysis.", activity
    
    # Simplified RLM: Split into batches and analyze
    batch_size = 3
    batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
    activity.append(f"Split {len(chunks)} chunks into {len(batches)} analysis batches")
    
    batch_findings = []
    for i, batch in enumerate(batches, 1):
        activity.append(f"Analyzing batch {i}/{len(batches)}")
        
        # Extract key themes from this batch
        themes = []
        for chunk in batch:
            if chunk.document_type == "incident":
                themes.append(f"Incident: {chunk.title}")
            elif chunk.document_type == "runbook":
                themes.append(f"Procedure: {chunk.title}")
            else:
                themes.append(f"Document: {chunk.title}")
        
        batch_findings.extend(themes)
    
    activity.append("Aggregating findings across batches")
    
    # Generate summary based on findings
    if batch_findings:
        findings_summary = "; ".join(batch_findings[:5])
        summary = (
            f"Analysis completed across {len(batches)} batches. "
            f"Key findings: {findings_summary}. "
            "This demonstrates recursive decomposition and aggregation of document analysis."
        )
    else:
        summary = "Analysis completed but no clear themes identified."
    
    activity.append("Analysis agent completed")
    
    return summary, activity
