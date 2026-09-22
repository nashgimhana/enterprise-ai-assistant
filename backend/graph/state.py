from typing import Annotated, TypedDict
from typing_extensions import TypedDict as TypedDictExt


class AgentState(TypedDict):
    """
    LangGraph state for the multi-agent workflow.
    
    This state is passed between agents and maintains:
    - User query and context
    - Retrieved document chunks
    - Analysis results
    - Final response
    - Activity log for observability
    - User role for RBAC
    """
    query: str
    role: str
    chunks: list[dict]
    analysis_summary: str
    answer: str
    activity: list[str]
    route: str
