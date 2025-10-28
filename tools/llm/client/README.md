# LLM Client Tools

## Purpose

Unified interface to LLM providers (OpenAI, Anthropic, Google, etc.) for text generation and embeddings. The client tools abstract away provider-specific APIs and provide a consistent interface for the application.

## Available Providers

### LiteLLM

**Provider**: `litellm`

**Description**: Unified API gateway supporting 100+ LLM providers with built-in fallbacks, retries, and load balancing.

**Key Features**:
- Single API interface for OpenAI, Anthropic, Google, Azure, and more
- Automatic retries and exponential backoff
- Provider fallbacks (e.g., OpenAI → Anthropic)
- Request/response logging
- Cost tracking per model

**Best For**:
- Direct completions and embeddings
- RAG pipelines (fast, low overhead)
- Evaluation tasks
- Production deployments requiring reliability

**Configuration**:
```python
client = LLMClientSelector.create(
    provider="litellm",
    proxy_url="http://localhost:4000",
    completion_model="gpt-4",
    embedding_model="text-embedding-3-small"
)
```

### LangChain

**Provider**: `langchain`

**Description**: LangChain-native LLM wrapper that integrates with the LangChain ecosystem while still using LiteLLM as the backend.

**Key Features**:
- Compatible with LangChain agents and chains
- Tool calling and function calling support
- Structured output parsing
- Memory and context management
- Prompt templating

**Best For**:
- Multi-agent systems with tool calling
- Complex reasoning chains
- LangChain-specific features (memory, callbacks)
- Workflows requiring structured outputs

**Configuration**:
```python
client = LLMClientSelector.create(
    provider="langchain",
    proxy_url="http://localhost:4000"
)
chat_model = client.get_client(model="gpt-4", temperature=0.0)
```

## When to Use Which Provider

| Use Case | Provider | Reason |
|----------|----------|--------|
| RAG retrieval/generation | LiteLLM | Lower overhead, faster responses |
| Document embeddings | LiteLLM | Optimized for batch processing |
| Quality evaluation | LiteLLM | Direct API calls, simpler |
| Agent with tool calling | LangChain | Built-in tool/function support |
| Multi-step reasoning | LangChain | Chain composition |
| Structured output parsing | LangChain | Pydantic integration |

## Usage Examples

### LiteLLM: Direct Completions

```python
from tools.llm.client.selector import LLMClientSelector

client = LLMClientSelector.create(
    provider="litellm",
    proxy_url="http://localhost:4000",
    completion_model="gpt-4"
)

# Generate text
response = client.generate(
    prompt="What is retrieval-augmented generation?",
    temperature=0.0,
    max_tokens=500
)
print(response)
```

### LiteLLM: Embeddings

```python
client = LLMClientSelector.create(
    provider="litellm",
    proxy_url="http://localhost:4000",
    embedding_model="text-embedding-3-small"
)

# Generate embeddings
texts = ["Document 1 content", "Document 2 content"]
embeddings = client.embed(texts)
print(f"Generated {len(embeddings)} embeddings of dimension {len(embeddings[0])}")
```

### LangChain: Agent with Tools

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import Tool

client = LLMClientSelector.create(
    provider="langchain",
    proxy_url="http://localhost:4000"
)

# Get LangChain chat model
llm = client.get_client(model="gpt-4", temperature=0.0)

# Define tools
tools = [
    Tool(
        name="Search",
        func=search_function,
        description="Search for information"
    )
]

# Create agent
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

# Run agent
result = executor.invoke({"input": "Research AI trends"})
```

### LangChain: Structured Output

```python
from pydantic import BaseModel, Field

class Answer(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning")
    answer: str = Field(description="Final answer")
    confidence: float = Field(description="Confidence score 0-1")

client = LLMClientSelector.create(provider="langchain", proxy_url="...")
llm = client.get_client(model="gpt-4")

# Get structured output
structured_llm = llm.with_structured_output(Answer)
result = structured_llm.invoke("What is 2+2?")
print(f"Answer: {result.answer}, Confidence: {result.confidence}")
```

## Configuration

### Environment Variables

```bash
# LiteLLM Proxy
LITELLM_PROXY_URL=http://localhost:4000

# Model Selection
COMPLETION_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-small

# LLM Parameters (optional)
TEMPERATURE=0.0
MAX_TOKENS=1000
```

### LiteLLM Proxy Setup

The LLM clients connect to a LiteLLM proxy server that handles provider routing:

```yaml
# litellm_config.yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: gpt-4
      api_key: sk-...

  - model_name: claude-3
    litellm_params:
      model: anthropic/claude-3-opus
      api_key: sk-ant-...
```

Start proxy:
```bash
litellm --config litellm_config.yaml --port 4000
```

## Base Interface

Both providers implement the `BaseLLM` interface:

```python
from abc import ABC, abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text completion from prompt."""
        pass

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for list of texts."""
        pass
```

## Integration Points

The LLM client is used throughout the application:

- **`src/agents/`**: All agents use LLM client for reasoning
  - Orchestrator: LangChain for tool calling
  - Research: LiteLLM for fast completions
  - Synthesis: LiteLLM for response generation

- **`src/rag/`**: Uses LiteLLM for embeddings and retrieval
  - Document embedding generation
  - Query embedding
  - Response synthesis

- **`evaluation/`**: Uses LiteLLM for quality scoring
  - LLM-as-a-Judge evaluation
  - Metric computation

- **`ingestor/`**: Uses LiteLLM for embeddings
  - Chunk embedding generation

## Best Practices

1. **Use LiteLLM by Default**: Start with LiteLLM for simplicity and performance
2. **Switch to LangChain When Needed**: Only use LangChain when you need tool calling or chains
3. **Connection Pooling**: Reuse client instances instead of creating new ones
4. **Error Handling**: Implement retries and fallbacks for API failures
5. **Cost Tracking**: Monitor token usage via Langfuse or LiteLLM proxy
6. **Model Selection**: Use cheaper models (gpt-3.5-turbo) for development
7. **Streaming**: Use streaming for long completions to improve UX

## Performance Optimization

**Batch Embeddings**:
```python
# Good: Batch embedding generation
texts = ["doc1", "doc2", "doc3", ...]
embeddings = client.embed(texts)  # Single API call

# Bad: Individual calls
embeddings = [client.embed([text]) for text in texts]  # Multiple API calls
```

**Caching**:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str):
    return client.embed([text])[0]
```

**Async Operations** (for LangChain):
```python
# Use async for parallel operations
results = await asyncio.gather(
    llm.ainvoke("Query 1"),
    llm.ainvoke("Query 2"),
    llm.ainvoke("Query 3")
)
```

## Troubleshooting

**Issue**: Connection refused to LiteLLM proxy
**Solution**: Ensure proxy is running on configured port (`litellm --port 4000`)

**Issue**: API key errors
**Solution**: Check proxy configuration has correct API keys

**Issue**: Model not found
**Solution**: Verify model name matches proxy configuration

**Issue**: Slow response times
**Solution**: Check proxy logs for errors, consider using streaming

**Issue**: Rate limit errors
**Solution**: Configure retries in proxy or implement request throttling

## See Also

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [LangChain Documentation](https://python.langchain.com/)
- [Tool Provider Pattern](../../../docs/architecture/tool-provider-pattern.md)
- [Agent Documentation](../../../docs/agents/README.md)
