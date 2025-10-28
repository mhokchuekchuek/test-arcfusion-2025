"""Web search tool for LangChain agents."""

from langchain.tools import BaseTool
from typing import Callable
from tools.llm.websearch.base import BaseWebSearchClient


class WebSearchTool(BaseTool):
    """Tool for searching the web using configured search client.

    Provides current information not available in academic papers.
    """

    name: str = "web_search"
    description: str = """Search the web for current information.

Use this tool when the query asks about:
- Recent events or releases ("this month", "latest", "current")
- Information not in the academic papers
- Author backgrounds, company information, news
- General knowledge or context outside the paper corpus
- Real-world applications or industry updates

Input: A search query string
Output: Web search results with titles, URLs, and content snippets"""

    websearch_client: BaseWebSearchClient
    max_results: int = 5

    def _run(self, query: str) -> str:
        """Execute web search and format for agent."""
        # Search using configured client
        results = self.websearch_client.search(
            query=query,
            max_results=self.max_results
        )

        if not results:
            return f"No web results found for: {query}"

        # Format for LLM consumption
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"[Result {i}] {result.get('title', 'No title')}\n"
                f"URL: {result.get('url', 'N/A')}\n"
                f"{result.get('content', 'No content available')}\n"
            )

        return "\n".join(formatted)

    async def _arun(self, query: str) -> str:
        """Async version (not used yet)."""
        return self._run(query)
