from backend.agents.retrieval import retrieve_knowledge
from backend.agents.analysis import analyze_documents
from backend.agents.response import generate_response
from backend.agents.supervisor import route_request
from backend.graph.state import AgentState
from backend.rag.documents import DocumentChunk


def retrieval_node(state: AgentState) -> AgentState:
    """
    Retrieval Agent node in LangGraph.
    Performs RAG operations and retrieves relevant documents.
    """
    chunks, activity = retrieve_knowledge(state["query"], state["role"])
    
    # Convert DocumentChunk objects to dicts for state serialization
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
    
    state["chunks"] = chunk_dicts
    state["activity"].extend(activity)
    return state


def analysis_node(state: AgentState) -> AgentState:
    """
    Analysis/RLM Agent node in LangGraph.
    Performs deep investigation and recursive exploration.
    """
    # Convert dicts back to DocumentChunk objects
    chunks = [
        DocumentChunk(
            chunk_id=c["chunk_id"],
            document_id=c["document_id"],
            title=c["title"],
            department=c["department"],
            document_type=c["document_type"],
            access_level=c["access_level"],
            source=c["source"],
            content=c["content"],
            score=c.get("score", 0.0),
        )
        for c in state["chunks"]
    ]
    
    summary, activity = analyze_documents(chunks, state["query"])
    state["analysis_summary"] = summary
    state["activity"].extend(activity)
    return state


def response_node(state: AgentState) -> AgentState:
    """
    Response Agent node in LangGraph.
    Generates final answer with validated citations.
    """
    # Convert dicts back to DocumentChunk objects
    chunks = [
        DocumentChunk(
            chunk_id=c["chunk_id"],
            document_id=c["document_id"],
            title=c["title"],
            department=c["department"],
            document_type=c["document_type"],
            access_level=c["access_level"],
            source=c["source"],
            content=c["content"],
            score=c.get("score", 0.0),
        )
        for c in state["chunks"]
    ]
    
    answer, activity = generate_response(chunks, state["query"], state["analysis_summary"])
    state["answer"] = answer
    state["activity"].extend(activity)
    return state


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor Agent node in LangGraph.
    Classifies intent and routes to appropriate agent.
    """
    route, activity = route_request(state["query"], state["role"])
    state["route"] = route
    state["activity"].extend(activity)
    return state


def should_analyze(state: AgentState) -> str:
    """
    Conditional edge: Decide whether to route to analysis or skip to response.
    """
    if state["route"] == "analysis":
        return "analyze"
    return "respond"


def run_workflow(query: str, role: str) -> dict:
    """
    Execute the LangGraph workflow.
    
    This is a simplified synchronous workflow that demonstrates the agent orchestration.
    In a full LangGraph implementation, this would use StateGraph with proper edges.
    
    Args:
        query: User's question
        role: User's role for RBAC
    
    Returns:
        Final state with answer and activity log
    """
    # Initialize state
    state: AgentState = {
        "query": query,
        "role": role,
        "chunks": [],
        "analysis_summary": "",
        "answer": "",
        "activity": ["Workflow started"],
        "route": "",
    }
    
    # Execute workflow nodes
    state = supervisor_node(state)
    
    if state["route"] == "forbidden_analysis":
        state["answer"] = "Your role cannot run analysis tools."
        state["activity"].append("Workflow terminated: forbidden route")
        return state
    
    state = retrieval_node(state)
    
    if state["route"] == "analysis":
        state = analysis_node(state)
    
    state = response_node(state)
    state["activity"].append("Workflow completed")
    
    return state
