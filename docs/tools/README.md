# Tools Documentation

Provider-agnostic abstractions for external services: LLMs, databases, and observability.

## Quick Start

**New to the tools system?** Start here:
1. [Provider Pattern](#provider-pattern) - Understand the design
2. [Tool Categories](#tool-categories) - Available tools
3. [Usage Examples](#usage-examples) - Get started quickly

---

## Architecture Overview

```
Application Layer
    │
    ├─→ LLM Tools ────────┐
    │   ├─ Client         │  Generate completions, embeddings
    │   ├─ Parser         │  Extract content from PDFs
    │   ├─ WebSearch      │  Search the web (Tavily)
    │   └─ Chunking       │  Split documents
    │
    ├─→ Database Tools ───┤
    │   ├─ Vector Store   │  Semantic search (Qdrant)
    │   └─ Memory Store   │  Session/cache (Redis)
    │
    └─→ Observability ────┘
        └─ Langfuse       │  Tracing and prompt management
```

---

## Design

All tools use the **Provider Pattern** for swappable implementations. Switch providers (LiteLLM → OpenAI, Qdrant → Pinecone) via configuration, not code changes.

```python
# Use selector to create provider
llm = LLMClientSelector.create(
    provider="litellm",  # Change to switch provider
    model="gpt-4"
)
```

**See [Provider Pattern Architecture](../architecture/tool-provider-pattern.md) for implementation details.**

## Tool Categories

### 1. LLM Tools

**Purpose**: Interact with language models and process documents

| Tool | Location | Providers | Primary Use |
|------|----------|-----------|-------------|
| **Client** | `tools/llm/client/` | LiteLLM, LangChain | Text generation, embeddings |
| **Parser** | `tools/llm/parser/` | Docling | PDF to markdown conversion |
| **WebSearch** | `tools/llm/websearch/` | Tavily | Real-time web search |
| **Chunking** | `tools/llm/chunking/` | LangChain | Document splitting |

**Documentation:**
- [LLM Client Design](./llm/client/design.md)
- [LiteLLM API Reference](./llm/client/litellm/api-reference.md)
- [LangChain API Reference](./llm/client/langchain/api-reference.md)

---

### 2. Database Tools

**Purpose**: Store and retrieve data

| Tool | Location | Providers | Primary Use |
|------|----------|-----------|-------------|
| **Vector Store** | `tools/database/vector/` | Qdrant | Semantic search for RAG |
| **Memory Store** | `tools/database/memory/` | Redis | Session management, caching |

**Documentation:**
- [Qdrant API Reference](./database/vector/qdrant/api-reference.md)
- [Redis API Reference](./database/memory/redis/api-reference.md)

---

### 3. Observability

**Purpose**: Monitor, trace, and debug LLM applications

| Tool | Location | Providers | Primary Use |
|------|----------|-----------|-------------|
| **Langfuse** | `tools/observability/` | Langfuse | Tracing, prompt management |

**Documentation:**
- [Langfuse API Reference](./observability/langfuse/api-reference.md)

---

## Usage Examples

### Basic Usage

```python
from tools.llm.client.selector import LLMClientSelector

# Create client
llm = LLMClientSelector.create(
    provider="litellm",
    model="gpt-4"
)

# Use interface
response = llm.generate("What is RAG?")
```

### Configuration-Driven

```python
from src.configs.settings import Settings

settings = Settings()

# Provider from environment
llm = LLMClientSelector.create(
    provider=settings.LLM_PROVIDER,  # From .env
    model=settings.LLM_MODEL
)
```

### Dependency Injection

```python
class MyAgent:
    def __init__(self, llm_client: BaseLLM):
        self.llm = llm_client

# Inject via constructor
llm = LLMClientSelector.create(provider="litellm", model="gpt-4")
agent = MyAgent(llm_client=llm)
```

---

## Configuration

Tools are configured via environment variables:

```bash
# LLM
LLM_PROVIDER=litellm
LLM_MODEL=gpt-4
OPENAI_API_KEY=sk-...

# Vector Store
VECTOR_STORE_PROVIDER=qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Memory
MEMORY_PROVIDER=redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Observability
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
```

---

## Testing

### Mock for Unit Tests

```python
class MockLLM(BaseLLM):
    def generate(self, prompt: str) -> str:
        return "mocked response"

agent = MyAgent(llm_client=MockLLM())
```

### Real Provider for Integration Tests

```python
llm = LLMClientSelector.create(provider="litellm", model="gpt-4")
response = llm.generate("test")
assert len(response) > 0
```

---

## Common Patterns

### Fallback Provider

```python
try:
    llm = LLMClientSelector.create(provider="primary")
    response = llm.generate(prompt)
except Exception:
    llm = LLMClientSelector.create(provider="fallback")
    response = llm.generate(prompt)
```

### Tool Composition

```python
llm = LLMClientSelector.create(provider="litellm")
vector = VectorStoreSelector.create(provider="qdrant")
rag = RAGService(llm=llm, vector_store=vector)
```

---

## Directory Structure

```
tools/
├── llm/
│   ├── client/          # LLM text generation and embeddings
│   │   ├── litellm/     # Direct API via LiteLLM proxy
│   │   └── langchain/   # LangChain integration
│   ├── parser/          # PDF to markdown (Docling)
│   ├── websearch/       # Web search (Tavily)
│   └── chunking/        # Document splitting
│
├── database/
│   ├── vector/          # Semantic search (Qdrant)
│   └── memory/          # Session storage (Redis)
│
└── observability/       # Tracing and monitoring (Langfuse)
```

---

## Quick Reference

| Need | Tool | Selector |
|------|------|----------|
| **Generate text** | LLM Client | `LLMClientSelector` |
| **Semantic search** | Vector Store | `VectorStoreSelector` |
| **Web search** | WebSearch | `WebSearchSelector` |
| **Parse PDFs** | Parser | `ParserSelector` |
| **Cache/sessions** | Memory Store | `MemorySelector` |
| **Trace LLMs** | Langfuse | `ObservabilitySelector` |

---

## Related Documentation

- [Provider Pattern Architecture](../architecture/tool-provider-pattern.md) - How the provider pattern works
- [LLM Client Design](./llm/client/design.md) - Detailed LLM client architecture
- [API References](#tool-categories) - Provider-specific documentation
