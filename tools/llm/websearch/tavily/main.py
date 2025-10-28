"""Tavily web search client implementation."""

from typing import Any
from tavily import TavilyClient

from tools.llm.websearch.base import BaseWebSearchClient
from tools.logger import get_logger

logger = get_logger(__name__)


class TavilyWebSearchClient(BaseWebSearchClient):
    """Web search client using Tavily API."""

    def __init__(self, api_key: str):
        """Initialize Tavily client.

        Args:
            api_key: Tavily API key
        """
        self.client = TavilyClient(api_key=api_key)
        logger.info("TavilyWebSearchClient initialized")

    def search(
        self,
        query: str,
        max_results: int = 5
    ) -> list[dict[str, Any]]:
        """Search the web using Tavily.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, url, snippet, content
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            logger.debug(f"Searching Tavily for: {query}")
            response = self.client.search(
                query=query,
                max_results=max_results
            )

            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", "")[:200],
                    "content": item.get("content", ""),
                })

            logger.info(f"Retrieved {len(results)} results from Tavily")
            return results

        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            raise Exception(f"Web search failed: {e}") from e
