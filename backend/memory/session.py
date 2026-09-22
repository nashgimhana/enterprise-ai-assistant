from typing import Dict, List


class SessionMemory:
    """
    Session-scoped conversational memory.
    
    Maintains user context, previous questions, and relevant historical interactions
    across multiple turns during a session.
    
    Design decision: Using in-memory dictionary for POC. Production would use
    a durable encrypted store (e.g., Redis with encryption) for persistence
    across server restarts and horizontal scaling.
    """
    
    def __init__(self):
        self._sessions: Dict[str, List[Dict[str, str]]] = {}
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to the session history.
        
        Args:
            session_id: Unique session identifier (e.g., auth token)
            role: Message role (user/assistant)
            content: Message content
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        
        self._sessions[session_id].append({"role": role, "content": content})
    
    def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Unique session identifier
            limit: Maximum number of recent messages to return
        
        Returns:
            List of message dictionaries
        """
        history = self._sessions.get(session_id, [])
        return history[-limit:] if limit else history
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear session history (e.g., on logout).
        
        Args:
            session_id: Unique session identifier
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def get_context(self, session_id: str) -> str:
        """
        Get formatted context string from recent history.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            Formatted context string for LLM
        """
        history = self.get_history(session_id, limit=5)
        if not history:
            return ""
        
        context_lines = []
        for msg in history:
            context_lines.append(f"{msg['role']}: {msg['content']}")
        
        return "\n".join(context_lines)


# Global session memory instance
session_memory = SessionMemory()
