# LLM Client Design

## Problem Statement

Building a multi-agent RAG system requires interaction with multiple LLM providers and capabilities:

1. **Multi-Provider Support**: Need to support OpenAI, Anthropic, Google Gemini, and others
2. **Unified Interface**: Different providers have different APIs (OpenAI SDK vs Anthropic SDK vs Google SDK)
3. **Operational Features**: Need automatic retries, fallbacks, rate limiting, and cost tracking
4. **Dual Capabilities**: Both completion/chat and embeddings in a single interface
5. **Agent Integration**: Need to work with both direct API calls (RAG) and agent frameworks (LangChain/LangGraph)
6. **Prompt Management**: Centralized prompt storage with versioning and A/B testing

---

## Solution: LiteLLM as Unified Router

This system uses **LiteLLM Proxy** as a centralized LLM gateway that provides:

- **Unified API**: OpenAI-compatible API for 100+ LLM providers
- **Automatic Fallbacks**: If primary model fails, automatically try backup models
- **Retries**: Built-in retry logic with exponential backoff
- **Rate Limiting**: Respect provider rate limits and quotas
- **Cost Tracking**: Track token usage and costs per model/user
- **Caching**: Redis-backed response caching to reduce costs and latency
- **Prompt Management**: Centralized prompt storage with .prompt files

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ RAG Service  │  │    Agents    │  │  Evaluation  │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                  │                  │
│         └─────────────────┴──────────────────┘                  │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LiteLLM Proxy (Port 4000)                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Model Router: Route requests based on model name         │ │
│  │  - claude-3-5-sonnet  → Anthropic API                     │ │
│  │  - gpt-4-turbo        → OpenAI API                        │ │
│  │  - gemini-1.5-flash   → Google API                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Features: Retries, Fallbacks, Rate Limits, Caching       │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   OpenAI     │ │  Anthropic   │ │    Google    │
    │     API      │ │     API      │ │     API      │
    └──────────────┘ └──────────────┘ └──────────────┘
```

**Key Insight**: By using LiteLLM Proxy, we decouple the application from specific provider APIs. The application only knows about the OpenAI SDK interface, regardless of the underlying provider.

**For detailed rationale on why we chose LiteLLM Proxy, see [../../architecture/architecture-decisions.md](../../architecture/architecture-decisions.md#2-litellm-proxy-as-llm-router).**

---

## Implementation Choices

### Two Provider Implementations

This codebase provides **two LLM client providers**:

#### 1. LiteLLM Provider (Direct API)
**Location**: `tools/llm/client/litellm/main.py:1`

**Purpose**: Direct API calls for RAG and completion tasks

**Key Features**:
- Uses OpenAI SDK pointing to LiteLLM proxy
- Supports traditional prompts and dotprompt templates
- Implements `BaseLLM` interface: `generate()` and `embed()`
- Used by: RAG service, Synthesis agent, evaluation scripts

**Example Usage**:
```python
from tools.llm.client.selector import LLMClientSelector

# Create client
client = LLMClientSelector.create(
    provider="litellm",
    proxy_url="http://localhost:4000",
    completion_model="gpt-4-turbo",
    embedding_model="text-embedding-3-small"
)

# Traditional prompt mode
response = client.generate(
    prompt="What is retrieval-augmented generation?",
    system_prompt="You are an AI expert.",
    temperature=0.7,
    max_tokens=500
)

# Dotprompt mode (with Langfuse prompt management)
response = client.generate(
    prompt_variables={
        "context": "RAG combines retrieval and generation...",
        "question": "How does RAG work?"
    },
    temperature=0.0
)

# Embeddings
embeddings = client.embed([
    "Document chunk 1",
    "Document chunk 2",
    "Document chunk 3"
])
```

#### 2. LangChain Provider (Agent Framework)
**Location**: `tools/llm/client/langchain/main.py:1`

**Purpose**: Integration with LangChain/LangGraph for agent workflows

**Key Features**:
- Returns `ChatOpenAI` instances configured for LiteLLM proxy
- Does NOT implement `BaseLLM` (different interface)
- Used by: Orchestrator, Clarification, Research agents

**Example Usage**:
```python
from tools.llm.client.selector import LLMClientSelector

# Create client
client = LLMClientSelector.create(
    provider="langchain",
    proxy_url="http://localhost:4000"
)

# Get ChatOpenAI instance
chat = client.get_client(
    model="gpt-4-turbo",
    temperature=0.0,
    max_tokens=1000
)

# Use with LangChain
from langchain.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("user", "{input}")
])

chain = prompt | chat
response = chain.invoke({"input": "Explain RAG"})
```

### Why Both Providers?

| Provider | Use Case | Reason |
|----------|----------|--------|
| **litellm** | RAG, Synthesis, Evaluation | Direct API = Lower latency, simpler interface |
| **langchain** | Orchestrator, Clarification, Research | Agent framework = Tool calling, state management |

**Design Decision**: Use the **simplest tool for the job**. RAG doesn't need agent capabilities, so use direct API. Agents need tool calling and state management, so use LangChain.

---

## Configuration

### LiteLLM Proxy Config

**Location**: `configs/litellm/proxy_config.yaml`

**Key Sections**:

#### 1. Model List
Define available models with aliases:

```yaml
model_list:
  # Anthropic Claude
  - model_name: claude-3-5-sonnet
    litellm_params:
      model: claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY

  # OpenAI GPT-4
  - model_name: gpt-4-turbo
    litellm_params:
      model: gpt-4-turbo-preview
      api_key: os.environ/OPENAI_API_KEY
      max_tokens: 4096
    model_info:
      tpm: 80000  # Tokens per minute limit
      rpm: 500    # Requests per minute limit

  # Google Gemini
  - model_name: gemini-1.5-flash
    litellm_params:
      model: gemini/gemini-1.5-flash
      api_key: os.environ/GEMINI_API_KEY

  # Embeddings
  - model_name: text-embedding-3-small
    litellm_params:
      model: text-embedding-3-small
      api_key: os.environ/OPENAI_API_KEY
```

#### 2. LiteLLM Settings
Operational features:

```yaml
litellm_settings:
  # Prompt management
  global_prompt_directory: "./prompts"

  # Caching (optional)
  cache: true
  cache_params:
    type: redis
    host: os.environ/REDIS_HOST
    port: os.environ/REDIS_PORT
    ttl: 3600  # 1 hour

  # Retry configuration
  num_retries: 3
  request_timeout: 600  # 10 minutes

  # Drop unsupported params instead of erroring
  drop_params: true
```

#### 3. Router Settings
Load balancing strategy:

```yaml
router_settings:
  routing_strategy: simple-shuffle  # Options: simple-shuffle, least-busy, usage-based-routing
```

### Environment Variables

**Location**: `.env`

```bash
# LLM Provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# LiteLLM Proxy
LITELLM_MASTER_KEY=sk-litellm-...
LITELLM_PROXY_URL=http://localhost:4000

# Optional: Observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

---

## Prompt Management with Dotprompt

LiteLLM Proxy supports **dotprompt files** for centralized prompt management:

### Prompt File Structure

**Location**: `prompts/synthesis.prompt`

```yaml
---
model: gpt-4-turbo
temperature: 0.0
max_tokens: 1000
---
You are a helpful AI assistant that synthesizes information from multiple sources.

Context:
{{context}}

User Question:
{{question}}

Provide a comprehensive answer with citations.
```

### Using Prompts

```python
# Load prompt from file
response = client.generate(
    prompt_variables={
        "context": "Retrieved context from RAG...",
        "question": "What is quantum computing?"
    }
    # Model, temperature, max_tokens loaded from .prompt file
)
```

### Benefits

1. **Version Control**: Prompts tracked in git
2. **A/B Testing**: Easy to test prompt variations
3. **Non-Technical Editing**: Product managers can edit prompts without code changes
4. **Consistency**: Same prompt used across dev/staging/prod

**Note**: Currently using traditional prompts in code, but dotprompt support is available for future migration.

---

## Request Flow

### Completion Request

```
1. Application calls: client.generate("What is RAG?")
   ↓
2. LiteLLM Provider formats OpenAI-compatible request
   ↓
3. HTTP POST to: http://localhost:4000/v1/chat/completions
   Body: {
     "model": "gpt-4-turbo",
     "messages": [{"role": "user", "content": "What is RAG?"}],
     "temperature": 0.7
   }
   ↓
4. LiteLLM Proxy receives request
   ↓
5. LiteLLM checks cache (if enabled)
   ↓ (cache miss)
6. LiteLLM routes to OpenAI API
   ↓
7. OpenAI responds with completion
   ↓
8. LiteLLM caches response (if enabled)
   ↓
9. LiteLLM returns OpenAI-formatted response
   ↓
10. LiteLLM Provider extracts text: "RAG stands for..."
    ↓
11. Application receives string response
```

### Embedding Request

```
1. Application calls: client.embed(["text1", "text2"])
   ↓
2. LiteLLM Provider formats OpenAI-compatible request
   ↓
3. HTTP POST to: http://localhost:4000/v1/embeddings
   Body: {
     "model": "text-embedding-3-small",
     "input": ["text1", "text2"]
   }
   ↓
4. LiteLLM Proxy routes to OpenAI API
   ↓
5. OpenAI returns embeddings
   ↓
6. LiteLLM Provider extracts vectors: [[0.1, 0.2, ...], [0.3, 0.4, ...]]
   ↓
7. Application receives list[list[float]]
```

---

## Error Handling and Retries

### Automatic Retries

LiteLLM Proxy automatically retries failed requests:

```yaml
litellm_settings:
  num_retries: 3
  request_timeout: 600
```

**Retry Behavior**:
- **Transient Errors**: Network errors, rate limits (429), server errors (500+)
- **Exponential Backoff**: Wait increases between retries (1s, 2s, 4s)
- **Final Failure**: After 3 attempts, raise exception to application

### Fallback Models

Configure fallback models for high availability:

```yaml
model_list:
  - model_name: primary
    litellm_params:
      model: gpt-4-turbo
      api_key: os.environ/OPENAI_API_KEY
    fallbacks:
      - model: gpt-4
      - model: claude-3-5-sonnet
```

**Fallback Behavior**:
1. Try `gpt-4-turbo`
2. If fails, try `gpt-4`
3. If fails, try `claude-3-5-sonnet`
4. If all fail, raise exception

---

## Testing

### Mocking LLM Clients

```python
from unittest.mock import Mock
from tools.llm.client.base import BaseLLM

def test_rag_service():
    # Mock LLM client
    mock_llm = Mock(spec=BaseLLM)
    mock_llm.generate.return_value = "Mocked response"
    mock_llm.embed.return_value = [[0.1, 0.2, 0.3]]

    # Inject mock
    rag_service = RAGService(llm_client=mock_llm, vector_store=...)

    # Test without calling real API
    response = rag_service.generate_answer("test query")
    assert response == "Mocked response"
    mock_llm.generate.assert_called_once()
```

### Integration Testing

```python
def test_litellm_integration():
    # Real LiteLLM client (requires proxy running)
    client = LLMClientSelector.create(
        provider="litellm",
        proxy_url="http://localhost:4000",
        completion_model="gpt-4-turbo",
        embedding_model="text-embedding-3-small"
    )

    # Test completion
    response = client.generate("Say 'test'")
    assert "test" in response.lower()

    # Test embeddings
    embeddings = client.embed(["hello", "world"])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 1536  # text-embedding-3-small dimension
```

