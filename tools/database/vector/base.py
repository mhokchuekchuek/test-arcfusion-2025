"""Base abstraction for vector databases."""

from abc import ABC, abstractmethod
from typing import Any


class BaseVectorStore(ABC):
    """Abstract base class for vector databases.

    All vector store implementations must inherit from this class and implement
    all abstract methods. This enables swapping between different vector databases
    (FAISS, Pinecone, Weaviate, etc.) without changing application code.

    Note: Implementation-specific methods like count(), save(), load() are not
    included in the base class as they vary by vector DB type.
    """

    @abstractmethod
    def add(
        self,
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None
    ) -> None:
        """Add embeddings to the store.

        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dicts (must match embeddings length if provided)
            ids: Optional list of IDs for the embeddings

        Raises:
            ValueError: If embeddings and metadata lengths don't match
            Exception: If addition fails
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        k: int = 5,
        filter: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search for similar embeddings.

        Args:
            query_embedding: Query vector
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of results, each containing:
            {
                "id": str,
                "score": float,
                "metadata": dict,
                "text": str (if available)
            }

        Raises:
            Exception: If search fails
        """
        pass

    @abstractmethod
    def delete(self, **kwargs) -> None:
        """Delete embeddings.

        Args:
            **kwargs: Implementation-specific deletion parameters
                      (e.g., ids, filter, conditions)

        Raises:
            Exception: If deletion fails
        """
        pass
