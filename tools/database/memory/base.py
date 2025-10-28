"""Base abstraction for memory databases."""

from abc import ABC, abstractmethod
from typing import Any


class BaseMemory(ABC):
    """Abstract base class for memory database implementations."""

    @abstractmethod
    def add(self, **kwargs) -> None:
        """Add a message to session history.

        Args:
            **kwargs: Implementation-specific parameters

        Raises:
            ValueError: If parameters are invalid
        """
        pass

    @abstractmethod
    def get(self, **kwargs) -> list[dict[str, Any]]:
        """Get conversation history for a session.

        Args:
            **kwargs: Implementation-specific parameters

        Returns:
            List of messages in chronological order
        """
        pass

    @abstractmethod
    def clear(self, **kwargs) -> None:
        """Clear all messages in a session.

        Args:
            **kwargs: Implementation-specific parameters
        """
        pass

    @abstractmethod
    def exists(self, **kwargs) -> bool:
        """Check if a session exists.

        Args:
            **kwargs: Implementation-specific parameters

        Returns:
            True if session exists
        """
        pass
