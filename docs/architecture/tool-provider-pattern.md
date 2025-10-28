# Tool Provider Pattern

## Overview

The tool provider pattern is a core architectural pattern used throughout this codebase to enable **swappable implementations** without changing interfaces. This pattern allows you to switch providers (e.g., from LiteLLM to direct OpenAI, or from Qdrant to Pinecone) simply by changing configuration values.

### Why Provider Pattern?

**Problem**: Direct dependencies on specific implementations make code rigid and difficult to test.

**Solution**: Define abstract interfaces and use a factory pattern to select implementations at runtime.

**Example Benefit**: Switch from LiteLLM to direct OpenAI API without modifying any application code:
```python
# Before: using LiteLLM
client = LLMClientSelector.create(provider="litellm", proxy_url="http://localhost:4000")

# After: using direct OpenAI (if implemented)
client = LLMClientSelector.create(provider="openai", api_key="sk-...")

# Application code remains unchanged
response = client.generate("What is RAG?")
```

---

## Pattern Structure

Each tool category follows this standardized directory structure:

```
tools/{category}/
  ├── base.py           # Abstract base class defining interface
  ├── selector.py       # Factory for provider selection
  └── {provider}/
      ├── __init__.py
      └── main.py       # Concrete implementation
```

### Example: LLM Client Structure

```
tools/llm/client/
  ├── base.py                    # BaseLLM abstract interface
  ├── selector.py                # LLMClientSelector factory
  ├── litellm/
  │   ├── __init__.py
  │   └── main.py                # LiteLLM implementation
  └── langchain/
      ├── __init__.py
      └── main.py                # LangChain implementation
```

---

## How It Works

### 1. Define Abstract Interface

All implementations must conform to a base class:

```python
# tools/llm/client/base.py
from abc import ABC, abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None, **kwargs) -> str:
        """Generate text completion."""
        pass

    @abstractmethod
    def embed(self, texts: list[str], **kwargs) -> list[list[float]]:
        """Generate embeddings."""
        pass
```

**Location**: `tools/llm/client/base.py`

### 2. Create Factory Selector

The selector uses a provider registry and dynamic imports:

```python
# tools/llm/client/selector.py
from tools.base.selector import BaseToolSelector

class LLMClientSelector(BaseToolSelector):
    _PROVIDERS = {
        "litellm": "tools.llm.client.litellm.main.LLMClient",
        "langchain": "tools.llm.client.langchain.main.LLMClient",
    }
```

**Location**: `tools/llm/client/selector.py`

### 3. Implement Concrete Provider

Each provider implements the abstract interface:

```python
# tools/llm/client/litellm/main.py
from tools.llm.client.base import BaseLLM

class LLMClient(BaseLLM):
    def __init__(self, proxy_url: str, completion_model: str, embedding_model: str):
        self.proxy_url = proxy_url
        self.completion_model = completion_model
        self.embedding_model = embedding_model
        # Initialize OpenAI client pointing to LiteLLM proxy
        self.client = OpenAI(base_url=proxy_url)

    def generate(self, prompt: str, system_prompt: str | None = None, **kwargs) -> str:
        # Implementation details...
        pass

    def embed(self, texts: list[str], **kwargs) -> list[list[float]]:
        # Implementation details...
        pass
```

**Location**: `tools/llm/client/litellm/main.py:1`

### 4. Use via Selector

Application code uses the factory to instantiate providers:

```python
from tools.llm.client.selector import LLMClientSelector

# Create provider instance
client = LLMClientSelector.create(
    provider="litellm",  # Select provider by name
    proxy_url="http://localhost:4000",
    completion_model="gpt-4",
    embedding_model="text-embedding-ada-002"
)

# Use abstract interface
response = client.generate("Explain quantum computing")
embeddings = client.embed(["Hello", "World"])
```

**Location**: Example usage in `src/apis/dependencies/rag.py:32`

---

## Dynamic Import Mechanism

The `BaseToolSelector` implements the factory pattern core:

```python
# tools/base/selector.py
import importlib

class BaseToolSelector:
    _PROVIDERS: dict[str, str] = {}  # Override in subclass

    @classmethod
    def create(cls, provider: str, **kwargs):
        """Dynamically import and instantiate provider."""
        if provider not in cls._PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}")

        # Get full module path (e.g., "tools.llm.client.litellm.main.LLMClient")
        full_path = cls._PROVIDERS[provider]
        module_path, class_name = full_path.rsplit(".", 1)

        # Import module dynamically
        module = importlib.import_module(module_path)

        # Get class and instantiate
        ToolClass = getattr(module, class_name)
        return ToolClass(**kwargs)

    @classmethod
    def list_providers(cls) -> list[str]:
        """List available providers."""
        return list(cls._PROVIDERS.keys())
```

**Location**: `tools/base/selector.py:1`

**How it works:**
1. **Provider Lookup**: Maps provider name to full module path
2. **Dynamic Import**: Uses `importlib.import_module()` to load module at runtime
3. **Class Extraction**: Uses `getattr()` to get class from module
4. **Instantiation**: Creates instance with provided kwargs
5. **Error Handling**: Validates provider names and provides clear error messages

---

## Benefits

### 1. Testability
Easily mock providers for unit testing:

```python
from unittest.mock import Mock

# Mock LLM client
mock_llm = Mock(spec=BaseLLM)
mock_llm.generate.return_value = "Mocked response"

# Inject mock into service
rag_service = RAGService(llm_client=mock_llm, vector_store=...)
```

### 2. Extensibility
Add new providers without modifying existing code:

```python
# 1. Create new provider: tools/llm/client/openai/main.py
class LLMClient(BaseLLM):
    def generate(self, prompt: str, **kwargs) -> str:
        # Direct OpenAI implementation
        pass

# 2. Register in selector: tools/llm/client/selector.py
class LLMClientSelector(BaseToolSelector):
    _PROVIDERS = {
        "litellm": "tools.llm.client.litellm.main.LLMClient",
        "langchain": "tools.llm.client.langchain.main.LLMClient",
        "openai": "tools.llm.client.openai.main.LLMClient",  # New!
    }

# 3. Use immediately
client = LLMClientSelector.create("openai", api_key="sk-...")
```

### 3. Configuration-Driven
Switch providers via environment variables:

```python
# configs/settings.py
class Settings:
    llm_provider: str = "litellm"  # Change to "openai" to switch

# src/apis/dependencies/rag.py
client = LLMClientSelector.create(
    provider=settings.llm_provider,  # Configured externally
    **settings.llm_config
)
```

### 4. Dependency Isolation
Provider-specific dependencies are contained:

```
tools/llm/client/litellm/
  └── requirements.txt    # Only litellm dependencies

tools/llm/client/openai/
  └── requirements.txt    # Only openai dependencies
```

### 5. Consistent Interface
All tools in a category use the same API, reducing cognitive load:

```python
# All vector stores have the same interface
vector_store = VectorStoreSelector.create(provider="qdrant", ...)
vector_store.add(embeddings, metadata)
results = vector_store.search(query_embedding, k=5)

# Easy to swap to Pinecone
vector_store = VectorStoreSelector.create(provider="pinecone", ...)
vector_store.add(embeddings, metadata)  # Same API!
results = vector_store.search(query_embedding, k=5)
```

---

## Available Tool Categories

The provider pattern is consistently applied across all tool categories:

### 1. LLM Client
- **Base**: `BaseLLM`
- **Selector**: `LLMClientSelector`
- **Providers**: `litellm`, `langchain`
- **Purpose**: Text generation and embeddings

**Location**: `tools/llm/client/`

### 2. Vector Database
- **Base**: `BaseVectorStore`
- **Selector**: `VectorStoreSelector`
- **Providers**: `qdrant`
- **Purpose**: Semantic search and storage

**Location**: `tools/database/vector/`

### 3. Memory Store
- **Base**: `BaseMemory`
- **Selector**: `MemoryClientSelector`
- **Providers**: `redis`
- **Purpose**: Session-based conversation memory

**Location**: `tools/database/memory/`

### 4. PDF Parser
- **Base**: `BasePDFParser`
- **Selector**: `ParserSelector`
- **Providers**: `docling`
- **Purpose**: Extract text and structure from PDFs

**Location**: `tools/llm/parser/`

### 5. Text Chunker
- **Base**: `BaseChunker`
- **Selector**: `TextChunkerSelector`
- **Providers**: `recursive`
- **Purpose**: Split text into semantic chunks

**Location**: `tools/llm/chunking/`

### 6. Web Search
- **Base**: `BaseWebSearchClient`
- **Providers**: `tavily` (no selector yet)
- **Purpose**: Search the web for current information

**Location**: `tools/llm/websearch/`

### 7. Observability
- **Base**: `BaseObservability`
- **Selector**: `ObservabilitySelector`
- **Providers**: `langfuse`
- **Purpose**: Prompt management and tracing

**Location**: `tools/observability/`

---

## Example: Adding a New Provider

Let's add a **direct OpenAI provider** as an alternative to LiteLLM:

### Step 1: Implement Provider

Create `tools/llm/client/openai/main.py`:

```python
from openai import OpenAI
from tools.llm.client.base import BaseLLM

class LLMClient(BaseLLM):
    def __init__(self, api_key: str, completion_model: str, embedding_model: str):
        self.client = OpenAI(api_key=api_key)
        self.completion_model = completion_model
        self.embedding_model = embedding_model

    def generate(self, prompt: str, system_prompt: str | None = None, **kwargs) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.completion_model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content

    def embed(self, texts: list[str], **kwargs) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        return [item.embedding for item in response.data]
```

### Step 2: Register Provider

Update `tools/llm/client/selector.py`:

```python
class LLMClientSelector(BaseToolSelector):
    _PROVIDERS = {
        "litellm": "tools.llm.client.litellm.main.LLMClient",
        "langchain": "tools.llm.client.langchain.main.LLMClient",
        "openai": "tools.llm.client.openai.main.LLMClient",  # Add this line
    }
```

### Step 3: Use New Provider

```python
# No changes to application code required!
client = LLMClientSelector.create(
    provider="openai",  # Just change this
    api_key="sk-...",
    completion_model="gpt-4",
    embedding_model="text-embedding-ada-002"
)

# Same interface as before
response = client.generate("What is RAG?")
```

---

## Pattern Usage in Codebase

### RAG Service Initialization

**Location**: `src/apis/dependencies/rag.py:32`

```python
# Create LLM client for RAG
rag_llm_client = LLMClientSelector.create(
    provider=settings.rag.llm.provider,  # "litellm" from config
    proxy_url=settings.llm.proxy_url,
    completion_model=settings.rag.llm.completion_model,
    embedding_model=settings.rag.llm.embedding_model,
)

# Create vector store
vector_store = VectorStoreSelector.create(
    provider=settings.rag.vectordb.provider,  # "qdrant" from config
    host=settings.vectordb.qdrant.host,
    port=settings.vectordb.qdrant.port,
    collection_name=settings.vectordb.qdrant.collection_name,
)

# Create RAG service with injected dependencies
rag_service = RAGService(
    llm_client=rag_llm_client,
    vector_store=vector_store,
)
```

### Agent Workflow Initialization

**Location**: `src/apis/dependencies/agents.py`

```python
# Create separate LLM clients for each agent
orchestrator_llm = LLMClientSelector.create(
    provider="litellm",
    completion_model=settings.orchestrator.model,
    temperature=settings.orchestrator.temperature,
)

clarification_llm = LLMClientSelector.create(
    provider="litellm",
    completion_model=settings.clarification.model,
    temperature=settings.clarification.temperature,
)

# Create observability client
langfuse_client = ObservabilitySelector.create(
    provider="langfuse",
    public_key=settings.observability.langfuse.public_key,
    secret_key=settings.observability.langfuse.secret_key,
)
```

---

## Design Patterns Summary

This architecture combines multiple design patterns:

1. **Abstract Factory Pattern**: `BaseToolSelector` provides interface, subclasses register providers
2. **Strategy Pattern**: Base classes define interfaces, concrete implementations provide algorithms
3. **Dependency Injection**: Selectors create and inject dependencies at runtime
4. **Configuration-Driven**: Provider selection based on settings/config files
5. **Fail-Fast**: Clear validation and error messages for invalid providers

---

## Key Takeaways

1. **Abstraction**: All implementations conform to base class interfaces
2. **Factory**: Selectors use dynamic imports to instantiate providers
3. **Registry**: `_PROVIDERS` dict maps provider names to module paths
4. **Consistency**: Pattern applied uniformly across all tool categories
5. **Flexibility**: Add providers without modifying existing code
6. **Testability**: Easy to mock dependencies for unit tests
7. **Configuration**: Switch providers via environment variables

This pattern enables the codebase to remain flexible, testable, and maintainable as requirements evolve.
