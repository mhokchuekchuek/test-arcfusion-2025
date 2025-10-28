"""Base abstraction for text chunking strategies."""

from abc import ABC, abstractmethod
from typing import Any


class BaseChunker(ABC):
    """Abstract base class for text chunking strategies.

    All chunker implementations must inherit from this class and implement
    all abstract methods. This enables different chunking strategies
    (recursive, semantic, character-based, etc.) to be used interchangeably.
    """

    @abstractmethod
    def split(
        self,
        text: str,
        metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Split text into chunks.

        Args:
            text: Text to split
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of dicts, each containing:
            {
                "text": str,
                "metadata": dict (if provided, otherwise empty dict)
            }

        Raises:
            ValueError: If text is empty
            Exception: If chunking fails
        """
        pass
