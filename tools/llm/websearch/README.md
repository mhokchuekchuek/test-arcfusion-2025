# Web Search Tools

## Purpose

Search the web for current information, real-time data, and out-of-scope content that isn't available in the document corpus. Web search is essential for handling queries about recent events, current statistics, and general knowledge beyond the RAG system's indexed documents.

## Available Providers

### Tavily

**Provider**: `tavily`

**Description**: AI-optimized search API designed specifically for LLM applications and RAG systems.

**Key Features**:
- **LLM-optimized results**: Clean, structured data ready for LLM consumption
- **Answer-focused**: Provides direct answers when available
- **Source attribution**: Returns URLs and citations for verification
- **Content extraction**: Fetches and cleans page content automatically
- **Relevance ranking**: Results ranked by relevance to query
- **Multiple result types**: Web pages, news, academic papers

**Why Tavily Was Chosen**:
- Designed for AI/LLM use cases (vs. traditional search APIs)
- Clean, structured results without ads or clutter
- Good price/performance ratio
- Simple API, easy integration
- Better than Google Custom Search for RAG applications

**Output Format**: Structured JSON with clean text and citations

## Usage Examples

### Basic Web Search

```python
from tools.llm.websearch.selector import WebSearchSelector

search = WebSearchSelector.create(
    provider="tavily",
    api_key="tvly-..."
)

# Search for information
results = search.search("latest AI research trends 2024")

for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Content: {result['content'][:200]}...")
    print("---")
```

### Integration with Research Agent

```python
from tools.llm.websearch.selector import WebSearchSelector
from tools.llm.client.selector import LLMClientSelector

# Initialize tools
search = WebSearchSelector.create(provider="tavily", api_key="tvly-...")
llm = LLMClientSelector.create(provider="litellm", proxy_url="...")

# Search and synthesize
query = "What are the latest developments in quantum computing?"
search_results = search.search(query, max_results=5)

# Format results for LLM
context = "\n\n".join([
    f"Source: {r['title']} ({r['url']})\n{r['content']}"
    for r in search_results
])

# Generate answer with citations
prompt = f"""Based on these web search results, answer the query:

Query: {query}

Search Results:
{context}

Provide a comprehensive answer with citations."""

answer = llm.generate(prompt)
print(answer)
```

### Filtered Search

```python
search = WebSearchSelector.create(provider="tavily", api_key="tvly-...")

# Search with filters
results = search.search(
    query="machine learning papers",
    max_results=10,
    search_depth="advanced",  # More thorough search
    include_domains=["arxiv.org", "scholar.google.com"]  # Academic sources only
)
```

### Answer-Focused Search

```python
# Get direct answer when available
result = search.search_with_answer("What is the capital of France?")

if result.get("answer"):
    print(f"Answer: {result['answer']}")
    print(f"Sources: {', '.join([r['url'] for r in result['results']])}")
```

## Configuration

### Environment Variables

```bash
# Web search provider
WEBSEARCH_PROVIDER=tavily

# Tavily API credentials
TAVILY_API_KEY=tvly-...

# Search parameters (optional)
WEBSEARCH_MAX_RESULTS=5
WEBSEARCH_DEPTH=basic  # or 'advanced'
```

### Search Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | Required | Search query string |
| `max_results` | int | 5 | Number of results to return |
| `search_depth` | str | "basic" | "basic" or "advanced" (slower, more thorough) |
| `include_domains` | list | None | Whitelist domains |
| `exclude_domains` | list | None | Blacklist domains |
| `include_answer` | bool | False | Include direct answer if available |

## Base Interface

All web search providers implement the `BaseWebSearch` interface:

```python
from abc import ABC, abstractmethod

class BaseWebSearch(ABC):
    @abstractmethod
    def search(self, query: str, **kwargs) -> list[dict]:
        """Search the web and return results."""
        pass

    @abstractmethod
    def search_with_answer(self, query: str, **kwargs) -> dict:
        """Search with direct answer extraction."""
        pass
```

## Integration Points

The web search tool is used by:

- **`src/agents/research.py`**: Research agent
  - Handles out-of-scope queries
  - Fetches current information
  - Supplements RAG with web data

- **`src/agents/orchestrator.py`**: Query classification
  - Determines if query requires web search
  - Routes to research agent when needed

## Result Structure

### Standard Search Results

```python
[
    {
        "title": "Article Title",
        "url": "https://example.com/article",
        "content": "Clean extracted content...",
        "score": 0.95,  # Relevance score
        "published_date": "2024-01-15"  # When available
    },
    ...
]
```

### Answer-Focused Results

```python
{
    "answer": "Direct answer to the query",
    "results": [
        {
            "title": "Source Title",
            "url": "https://source.com",
            "content": "Supporting content...",
            "score": 0.98
        }
    ],
    "query": "Original search query"
}
```

## Use Cases

### Out-of-Scope Queries

When query is outside document corpus:

```python
def handle_query(query: str, rag_system, web_search):
    # Try RAG first
    rag_results = rag_system.retrieve(query)

    if rag_results.confidence < 0.5:
        # Fall back to web search for out-of-scope queries
        web_results = web_search.search(query, max_results=5)
        return synthesize_web_results(web_results)
    else:
        return synthesize_rag_results(rag_results)
```

### Current Events

```python
# Query requires recent information
if is_current_event_query(query):
    results = search.search(
        query,
        max_results=5,
        search_depth="advanced"
    )
```

### Fact Verification

```python
# Verify fact with multiple sources
def verify_fact(claim: str, search):
    results = search.search(claim, max_results=10)

    sources = [r['url'] for r in results]
    evidence = [r['content'] for r in results]

    # Use LLM to assess consensus
    return assess_claim(claim, evidence, sources)
```

## Best Practices

1. **Rate Limiting**: Implement request throttling to avoid API limits
2. **Caching**: Cache search results for identical queries (TTL: 1-24 hours)
3. **Cost Management**: Use `max_results` wisely - more results = higher cost
4. **Fallback**: Have fallback for API failures or rate limits
5. **Source Quality**: Filter by domain for higher quality sources
6. **Result Validation**: Check that results are relevant before using
7. **Citation**: Always include source URLs in final answers

## Performance Considerations

**API Latency**:
- Basic search: 1-2 seconds
- Advanced search: 3-5 seconds
- Consider timeout configuration

**Cost Management**:
```python
# Track search costs
class ManagedWebSearch:
    def __init__(self, search_tool):
        self.search = search_tool
        self.request_count = 0
        self.max_requests_per_hour = 100

    def search_with_limit(self, query: str, **kwargs):
        if self.request_count >= self.max_requests_per_hour:
            raise Exception("Search rate limit exceeded")

        self.request_count += 1
        return self.search.search(query, **kwargs)
```

**Caching Strategy**:
```python
from functools import lru_cache
import hashlib

class CachedWebSearch:
    def __init__(self, search_tool, cache_size=100):
        self.search = search_tool
        self.cache = lru_cache(maxsize=cache_size)(self._search_impl)

    def _search_impl(self, query_hash: str, query: str, **kwargs):
        return self.search.search(query, **kwargs)

    def search(self, query: str, **kwargs):
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return self.cache(query_hash, query, **kwargs)
```

## Error Handling

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def robust_search(search_tool, query: str):
    try:
        return search_tool.search(query, max_results=5)
    except RateLimitError:
        # Wait and retry
        raise
    except APIError as e:
        # Log error and fall back
        logger.error(f"Search API error: {e}")
        return []
```

## Comparison with Alternatives

| Provider | LLM-Optimized | Content Quality | Price | Use Case |
|----------|---------------|-----------------|-------|----------|
| **Tavily** | ✅ Excellent | ✅ High | Medium | AI/RAG applications |
| Google Custom Search | ❌ No | ⚠️ Mixed | Low | General search |
| Bing Search API | ❌ No | ⚠️ Mixed | Medium | Microsoft ecosystem |
| SerpAPI | ⚠️ Partial | ⚠️ Mixed | High | SEO/research tools |
| Brave Search | ⚠️ Partial | ⚠️ Good | Low | Privacy-focused |

## Troubleshooting

**Issue**: Rate limit exceeded
**Solution**: Implement request throttling and caching

**Issue**: Poor result quality
**Solution**: Use `search_depth="advanced"` or filter by domain

**Issue**: API key errors
**Solution**: Verify TAVILY_API_KEY is set correctly

**Issue**: Slow response times
**Solution**: Use `search_depth="basic"` or reduce `max_results`

**Issue**: Irrelevant results
**Solution**: Refine query or use `include_domains` filter

## Advanced Features

### Multi-Source Aggregation

```python
def aggregate_sources(query: str, search):
    # Get both web and news results
    web_results = search.search(query, max_results=5)
    news_results = search.search(
        query,
        max_results=3,
        include_domains=["reuters.com", "apnews.com", "bbc.com"]
    )

    return {
        "web": web_results,
        "news": news_results
    }
```

### Smart Query Expansion

```python
def expand_and_search(original_query: str, llm, search):
    # Use LLM to generate alternative queries
    expanded_queries = llm.generate(
        f"Generate 3 alternative search queries for: {original_query}"
    ).split("\n")

    all_results = []
    for query in expanded_queries:
        results = search.search(query, max_results=3)
        all_results.extend(results)

    # Deduplicate by URL
    return deduplicate_results(all_results)
```

## See Also

- [Research Agent](../../../docs/agents/research/design.md) - How web search is used
- [LLM Client](../client/README.md) - Synthesizing search results
- [Tool Provider Pattern](../../../docs/architecture/tool-provider-pattern.md)
