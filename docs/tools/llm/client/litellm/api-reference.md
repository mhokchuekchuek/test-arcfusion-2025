# LiteLLM Client API Reference

Direct API client for text generation and embeddings via LiteLLM proxy.

**Location**: `tools/llm/client/litellm/main.py`

---

## Class Definition

```python
class LLMClient(BaseLLM):
    def __init__(
        self,
        proxy_url: str = "http://litellm-proxy:4000",
        completion_model: Optional[str] = None,
        embedding_model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        api_key: str = "dummy"
    )
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `proxy_url` | str | `http://litellm-proxy:4000` | LiteLLM proxy URL |
| `completion_model` | str | None | Model for text (e.g., `gpt-4`, `claude-3-5-sonnet`) |
| `embedding_model` | str | None | Model for embeddings (e.g., `text-embedding-3-small`) |
| `temperature` | float | 0.7 | Sampling temperature (0-1) |
| `max_tokens` | int | 2000 | Max response tokens |
| `api_key` | str | `"dummy"` | Proxy API key |

**Note**: Model names must match those in `configs/litellm/proxy_config.yaml`

---

## Methods

### generate()

Generate text completion.

```python
def generate(
    self,
    prompt: Optional[str] = None,
    system_prompt: Optional[str] = None,
    prompt_variables: Optional[dict] = None,
    **kwargs
) -> str
```

#### Usage

**Traditional Mode** (direct strings):
```python
response = client.generate(
    prompt="What is RAG?",
    system_prompt="You are a helpful assistant.",
    temperature=0.0
)
```

**Dotprompt Mode** (template variables):
```python
response = client.generate(
    prompt_variables={
        "context": "RAG combines retrieval...",
        "question": "How does RAG work?"
    }
)
```

---

### embed()

Generate embeddings for text.

```python
def embed(self, texts: list[str], **kwargs) -> list[list[float]]
```

#### Usage

```python
embeddings = client.embed([
    "Document chunk 1",
    "Document chunk 2",
    "Document chunk 3"
])
# Returns: [[0.1, 0.2, ...], [0.3, 0.4, ...], ...]
```

---

## Example: Complete Setup

```python
from tools.llm.client.selector import LLMClientSelector

# Create client
client = LLMClientSelector.create(
    provider="litellm",
    proxy_url="http://localhost:4000",
    completion_model="gpt-4",
    embedding_model="text-embedding-3-small",
    temperature=0.0
)

# Generate text
answer = client.generate(
    prompt="Explain RAG",
    system_prompt="You are an AI expert."
)

# Generate embeddings
query_embedding = client.embed(["user query"])[0]
```

---

## Configuration

Model names from `configs/litellm/proxy_config.yaml`:

```yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: gpt-4-turbo-preview
      api_key: os.environ/OPENAI_API_KEY

  - model_name: text-embedding-3-small
    litellm_params:
      model: text-embedding-3-small
      api_key: os.environ/OPENAI_API_KEY
```

---

## See Also

- [LLM Client Design](../design.md)
- [LangChain Client](../langchain/api-reference.md)
- [LiteLLM Proxy Setup](../../../../architecture/llm-proxy-setup.md)
