"""Session memory wrapper for RAG conversations."""

from typing import Any

from tools.database.memory.base import BaseMemory
from tools.logger import get_logger

logger = get_logger(__name__)


class SessionMemory:
    """Wrapper for session-based conversation memory.

    Provides a simple interface for storing and retrieving conversation
    history using any BaseMemory implementation (Redis, in-memory, etc.).

    Example:
        >>> from tools.factory import ToolFactory
        >>> memory_client = ToolFactory.create(
        ...     tool_selector="database/memory",
        ...     provider="redis",
        ...     class_name="MemoryClient",
        ...     host="localhost"
        ... )
        >>> memory = SessionMemory(memory_client)
        >>> memory.add("session-1", "user", "What is RAG?")
        >>> history = memory.get("session-1")
    """

    def __init__(self, memory_client: BaseMemory):
        """Initialize session memory.

        Args:
            memory_client: Memory database client (Redis, etc.)
        """
        self.client = memory_client
        logger.info(f"SessionMemory initialized with {type(memory_client).__name__}")

    def add(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to session history.

        Args:
            session_id: Session identifier
            role: Message role ("user" or "assistant")
            content: Message content
            metadata: Optional metadata (sources, model, etc.)

        Raises:
            ValueError: If role is invalid
        """
        self.client.add(
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata,
        )

    def get(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Max number of messages to return (most recent)

        Returns:
            List of messages in chronological order:
            [
                {
                    "role": str,
                    "content": str,
                    "timestamp": str,
                    "metadata": dict (optional)
                }
            ]
        """
        return self.client.get(session_id=session_id, limit=limit)

    def clear(self, session_id: str) -> None:
        """Clear all messages in a session.

        Args:
            session_id: Session identifier
        """
        self.client.clear(session_id=session_id)

    def exists(self, session_id: str) -> bool:
        """Check if a session exists.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists
        """
        return self.client.exists(session_id=session_id)

    def count(self, session_id: str) -> int:
        """Get number of messages in a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of messages (0 if session doesn't exist)
        """
        # Try to use count method if available
        if hasattr(self.client, "count"):
            return self.client.count(session_id=session_id)

        # Fallback: get all messages and count
        messages = self.client.get(session_id=session_id)
        return len(messages)
