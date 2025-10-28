# Tavily Web Search API Reference

Web search client implementation using Tavily's AI-optimized search API for real-time information retrieval.

## Class Definition

```python
from tools.llm.websearch.tavily.main import TavilyWebSearchClient

class TavilyWebSearchClient(BaseWebSearchClient):
    """Web search client using Tavily API."""
```

**File**: `tools/llm/websearch/tavily/main.py`

## Constructor

### `__init__(api_key: str)`

Initialize Tavily web search client.

```python
client = TavilyWebSearchClient(api_key="tvly-...")
```

#### Parameters

- `api_key` (str, required): Tavily API key
  - Get API key from: https://tavily.com

#### Example

```python
from tools.llm.websearch.selector import WebSearchSelector

search_client = WebSearchSelector.create(
    provider="tavily",
    api_key="tvly-..."
)
```

## Methods

### `search(query: str, max_results: int = 5) -> list[dict[str, Any]]`

Search the web using Tavily API.

#### Parameters

- `query` (str, required): Search query string
- `max_results` (int, optional): Maximum number of results to return
  - Default: 5
  - Range: 1-100

#### Returns

List of dictionaries, one per search result:
- `title` (str): Page title
- `url` (str): URL of the page
- `snippet` (str): First 200 characters of content
- `content` (str): Full content extracted from page

#### Raises

- `ValueError`: If query is empty or invalid
- `Exception`: If API call fails (network error, rate limit, etc.)

#### Example

```python
from tools.llm.websearch.selector import WebSearchSelector

client = WebSearchSelector.create(
    provider="tavily",
    api_key="tvly-..."
)

results = client.search(
    query="latest AI research 2024",
    max_results=5
)

for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Snippet: {result['snippet']}")
    print()
```

## Configuration

### Environment Variables

```bash
# Required
TAVILY_API_KEY=tvly-...
```

### Dependencies

- `tavily-python`: Official Tavily Python SDK
  ```bash
  pip install tavily-python
  ```

## Usage Patterns

### Basic Web Search

```python
from tools.llm.websearch.selector import WebSearchSelector

# Create client
search = WebSearchSelector.create(
    provider="tavily",
    api_key="tvly-..."
)

# Search
results = search.search("Python async programming", max_results=3)

# Process results
for i, result in enumerate(results, 1):
    print(f"{i}. {result['title']}")
    print(f"   {result['url']}")
```

### Integration with Research Agent

```python
from langchain.tools import Tool
from tools.llm.websearch.selector import WebSearchSelector

# Create search client
search_client = WebSearchSelector.create(
    provider="tavily",
    api_key="tvly-..."
)

# Wrap as LangChain tool
web_search_tool = Tool(
    name="web_search",
    description="Search the web for current information",
    func=lambda q: search_client.search(q, max_results=5)
)

# Use in agent
agent = create_agent(
    model=llm,
    tools=[pdf_tool, web_search_tool]
)
```

## Features

### Supported Queries

- ✅ Natural language queries
- ✅ Keyword-based searches
- ✅ Multi-word phrases
- ✅ Questions ("What is...?", "How to...?")

### Response Format

Each result contains:
- **Title**: Page/article title
- **URL**: Direct link to source
- **Snippet**: First 200 characters (preview)
- **Content**: Full extracted text (cleaned HTML)

### AI Optimization

Tavily is optimized for LLM usage:
- Content cleaned and formatted
- Removes ads, navigation, boilerplate
- Extracts main article content
- Provides structured results

---

## See Also

- [Web Search Selector](../../websearch/selector.py) - Factory for creating search clients
- [Base Web Search](../../websearch/base.py) - Abstract base class
- [Tavily Documentation](https://docs.tavily.com) - Official Tavily API docs
- [Research Agent](../../../../../src/agents/research.py) - Agent using web search
