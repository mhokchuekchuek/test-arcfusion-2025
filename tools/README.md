# Tools Module

## Module Overview

The `tools/` module provides **reusable infrastructure with swappable providers** using the Provider Pattern. This enables clean separation of concerns, configuration-driven tool selection, and easy swapping of implementations without changing application code.

**Purpose**: Reusable infrastructure components
**Pattern**: Base → Selector → Provider implementations
**Benefits**: Testability, extensibility, configuration-driven behavior

## Architecture

```
tools/
├── base/               # BaseToolSelector (factory pattern)
├── llm/                # LLM-related tools
│   ├── client/         # LLM API clients
│   ├── parser/         # Document parsers
│   ├── chunking/       # Text chunkers
│   └── websearch/      # Web search APIs
├── database/           # Database tools
│   ├── vector/         # Vector stores
│   └── memory/         # Session memory stores
├── observability/      # Monitoring (Langfuse)
└── logger/             # Logging utilities
```

## Provider Pattern Explained

The provider pattern implements a factory method that allows dynamic selection of implementations at runtime based on configuration.

### Step 1: Define Interface

```python
# tools/llm/client/base.py
from abc import ABC, abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text completion from prompt."""
        pass
```

### Step 2: Create Selector with Provider Mapping

```python
# tools/llm/client/selector.py
from tools.base.selector import BaseToolSelector

class LLMClientSelector(BaseToolSelector):
    _PROVIDERS = {
        "litellm": "tools.llm.client.litellm.main.LLMClient",
        "langchain": "tools.llm.client.langchain.main.LLMClient",
    }
```

### Step 3: Use Anywhere - Swappable via Config!

```python
# In your application code
from tools.llm.client.selector import LLMClientSelector

# Provider selection from config or environment variable
client = LLMClientSelector.create(
    provider="litellm",  # Change to "langchain" without code changes!
    proxy_url="http://localhost:4000"
)

response = client.generate("What is RAG?")
```

## Key Benefits

- **Extensibility**: Add new providers without changing existing code (Open/Closed Principle)
- **Testability**: Mock providers easily in tests via dependency injection
- **Configuration**: Switch providers via config/env vars, not code changes
- **Dependency Isolation**: Provider-specific dependencies are contained in provider modules

## Available Tool Categories

| Category | Purpose | Selectors Available |
|----------|---------|---------------------|
| `llm/client` | LLM API clients | LiteLLM, LangChain |
| `llm/parser` | Document parsers | Docling |
| `llm/chunking` | Text chunkers | RecursiveCharacterTextSplitter |
| `llm/websearch` | Web search | Tavily |
| `database/vector` | Vector stores | Qdrant |
| `database/memory` | Session memory | Redis |
| `observability` | Monitoring | Langfuse |

## How to Use Selectors

### Basic Usage

```python
from tools.llm.client.selector import LLMClientSelector
from tools.database.vector.selector import VectorStoreSelector

# Create LLM client (from config or explicit params)
llm = LLMClientSelector.create(
    provider="litellm",
    proxy_url="http://localhost:4000",
    completion_model="gpt-4"
)

# Create vector store
vectordb = VectorStoreSelector.create(
    provider="qdrant",
    host="localhost",
    port=6333,
    collection_name="documents"
)
```

### Configuration-Driven Usage

```python
from src.configs.settings import Settings

settings = Settings()

# Provider selection from environment variables
llm = LLMClientSelector.create(
    provider=settings.LLM_PROVIDER,  # From .env: LLM_PROVIDER=litellm
    proxy_url=settings.LITELLM_PROXY_URL
)
```

## Adding a New Provider

### Step 1: Implement the Base Interface

```python
# tools/llm/client/openai/main.py
from tools.llm.client.base import BaseLLM

class LLMClient(BaseLLM):
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        # Initialize OpenAI client

    def generate(self, prompt: str) -> str:
        # Implementation using OpenAI SDK
        pass
```

### Step 2: Register in Selector

```python
# tools/llm/client/selector.py
class LLMClientSelector(BaseToolSelector):
    _PROVIDERS = {
        "litellm": "tools.llm.client.litellm.main.LLMClient",
        "langchain": "tools.llm.client.langchain.main.LLMClient",
        "openai": "tools.llm.client.openai.main.LLMClient",  # NEW
    }
```

### Step 3: Use It!

```python
client = LLMClientSelector.create(
    provider="openai",
    api_key="sk-..."
)
```

## Design Philosophy

The tools module follows SOLID principles:

- **Single Responsibility**: Each tool does one thing well
- **Open/Closed**: Open for extension (add providers), closed for modification
- **Liskov Substitution**: All providers of same type are interchangeable
- **Interface Segregation**: Base classes define minimal required interfaces
- **Dependency Inversion**: Depend on abstractions (base classes), not concretions

**Configuration over Code**: Switch behavior via config, not code changes

## Directory Guides

- [llm/README.md](./llm/README.md) - LLM tools overview
- [database/README.md](./database/README.md) - Database tools overview

## Common Usage Patterns

### Pattern 1: Dependency Injection

```python
class DocumentRetriever:
    def __init__(self, llm_client: BaseLLM, vector_store: BaseVectorStore):
        """Inject dependencies via constructor for testability."""
        self.llm = llm_client
        self.vector_store = vector_store

# Create and inject
llm = LLMClientSelector.create(provider="litellm", proxy_url="...")
vectordb = VectorStoreSelector.create(provider="qdrant", host="...")
retriever = DocumentRetriever(llm_client=llm, vector_store=vectordb)
```

### Pattern 2: Provider Fallback

```python
try:
    client = LLMClientSelector.create(provider="primary_provider", **config)
except Exception:
    client = LLMClientSelector.create(provider="fallback_provider", **config)
```

### Pattern 3: Multi-Tool Composition

```python
# Combine multiple tools for complex workflows
llm = LLMClientSelector.create(provider="litellm", proxy_url="...")
parser = ParserSelector.create(provider="docling")
chunker = TextChunkerSelector.create(provider="recursive", chunk_size=1000)

# Use in pipeline
document_text = parser.parse("paper.pdf")
chunks = chunker.split(document_text)
embeddings = llm.embed(chunks)
```

## Testing

### Unit Tests with Mocks

```python
from tools.llm.client.base import BaseLLM

class MockLLM(BaseLLM):
    def generate(self, prompt: str) -> str:
        return "mocked response"

# Test application logic without real API calls
agent = ResearchAgent(llm_client=MockLLM())
result = agent.run("test query")
assert "mocked response" in result
```

### Integration Tests

```python
# Test with real providers (use cheaper models)
llm = LLMClientSelector.create(
    provider="litellm",
    proxy_url="http://localhost:4000",
    completion_model="gpt-3.5-turbo"
)
response = llm.generate("test prompt")
assert len(response) > 0
```

## Best Practices

1. **Depend on Abstractions**: Import and type-hint with base classes, not implementations
2. **Use Selectors**: Never import concrete implementations directly in application code
3. **Configuration Over Code**: Use environment variables for provider selection
4. **Fail Fast**: Validate configuration at startup (check for missing API keys, invalid providers)
5. **Document Parameters**: Each provider's `**kwargs` should be documented
6. **Consistent Interfaces**: New providers must fully implement base class interface

## Troubleshooting

**Issue**: `ValueError: Unknown provider 'xyz'`
**Solution**: Check provider name spelling or add to selector's `_PROVIDERS` dict

**Issue**: `ImportError: No module named 'provider_package'`
**Solution**: Install provider-specific dependencies (see provider README)

**Issue**: Missing API keys or configuration
**Solution**: Set required environment variables in `.env` file

## See Also

- [Architecture Documentation](../docs/architecture/tool-provider-pattern.md) - Detailed design decisions
- [LLM Tools](./llm/README.md) - LLM-related tooling
- [Database Tools](./database/README.md) - Data persistence tooling
