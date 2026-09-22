from typing import Set


# Role definitions and their permissions
ROLES = {
    "viewer": {
        "allowed_tools": {"knowledge_search"},
        "can_run_analysis": False,
        "can_use_mcp": False,
        "can_access_admin": False,
    },
    "analyst": {
        "allowed_tools": {"knowledge_search", "python_analysis"},
        "can_run_analysis": True,
        "can_use_mcp": True,
        "can_access_admin": False,
    },
    "admin": {
        "allowed_tools": {"knowledge_search", "python_analysis", "mcp_client"},
        "can_run_analysis": True,
        "can_use_mcp": True,
        "can_access_admin": True,
    },
}


def can_use_tool(role: str, tool_name: str) -> bool:
    """
    Check if a role is authorized to use a specific tool.
    
    This enforces RBAC at the tool execution level. The LLM cannot
    bypass these checks - they are enforced server-side before any
    tool execution.
    
    Args:
        role: User role (viewer, analyst, admin)
        tool_name: Name of the tool being invoked
    
    Returns:
        True if authorized, False otherwise
    """
    role_config = ROLES.get(role, ROLES["viewer"])
    return tool_name in role_config["allowed_tools"]


def can_run_analysis(role: str) -> bool:
    """
    Check if a role can run analysis operations.
    
    Args:
        role: User role
    
    Returns:
        True if authorized for analysis
    """
    role_config = ROLES.get(role, ROLES["viewer"])
    return role_config["can_run_analysis"]


def can_access_restricted_documents(role: str, document_access_level: str) -> bool:
    """
    Check if a role can access documents with a specific access level.
    
    Args:
        role: User role
        document_access_level: Document's access_level metadata
    
    Returns:
        True if authorized for this document level
    """
    if document_access_level == "public":
        return True
    
    if document_access_level == "internal":
        return role in {"viewer", "analyst", "admin"}
    
    if document_access_level == "restricted":
        return role in {"analyst", "admin"}
    
    if document_access_level == "confidential":
        return role == "admin"
    
    # Default deny
    return False


def get_allowed_document_types(role: str) -> Set[str]:
    """
    Get the set of document types a role can access.
    
    Args:
        role: User role
    
    Returns:
        Set of accessible document types
    """
    # All roles can access basic document types
    base_types = {"incident", "runbook", "policy", "architecture"}
    
    if role == "viewer":
        return base_types
    
    if role in {"analyst", "admin"}:
        return base_types | {"product", "meeting", "financial"}
    
    return base_types
