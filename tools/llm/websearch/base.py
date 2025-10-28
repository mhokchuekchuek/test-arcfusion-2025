"""Base abstraction for web search clients."""

from abc import ABC, abstractmethod
from typing import Any


class BaseWebSearchClient(ABC):
    """Abstract base class for web search providers.

    All web search client implementations must inherit from this class and implement
    all abstract methods. This enables swapping between different search providers
    (Tavily, SerpAPI, DuckDuckGo, etc.) without changing application code.
    """

    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 5
    ) -> list[dict[str, Any]]:
        """Search the web for query.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results, each containing:
            {
                "title": str,
                "url": str,
                "snippet": str,
                "content": str (optional - full page content)
            }

        Raises:
            ValueError: If query is empty
            Exception: If search fails
        """
        pass
