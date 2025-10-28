# LangChain Client API Reference

**Source**: `tools/llm/client/langchain/main.py`

## Class: LLMClient

```python
class LLMClient
```

**Note**: Does NOT inherit from `BaseLLM` (different interface than litellm client)

**Location**: Line 16

---

## Constructor

```python
def __init__(
    self,
    proxy_url: str = "http://litellm-proxy:4000",
    api_key: str = "sk-1234",
    default_model: str = "gpt-4",
    default_temperature: float = 0.7,
    default_max_tokens: int = 2000,
    **kwargs
)
```

**Location**: Lines 43-71

### Parameters (from code)

| Parameter | Type | Default | From Docstring |
|-----------|------|---------|----------------|
| `proxy_url` | `str` | `"http://litellm-proxy:4000"` | LiteLLM proxy URL |
| `api_key` | `str` | `"sk-1234"` | API key for proxy (use dummy if auth disabled) |
| `default_model` | `str` | `"gpt-4"` | Default model name from proxy config |
| `default_temperature` | `float` | `0.7` | Default sampling temperature (0-1) |
| `default_max_tokens` | `int` | `2000` | Default maximum tokens in response |
| `**kwargs` | - | - | Additional default parameters for ChatOpenAI |

### Implementation Details (lines 62-71)

- Sets instance variables: `proxy_url`, `api_key`, `default_model`, `default_temperature`, `default_max_tokens`, `default_kwargs`
- Logs initialization message

---

## Methods

### get_client()

```python
def get_client(
    self,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    extra_body: Optional[Dict[str, Any]] = None,
    **kwargs
) -> ChatOpenAI
```

**Location**: Lines 73-130

**Docstring says**: "Get ChatOpenAI instance configured for LiteLLM proxy" with two modes:
1. Standard mode: For LangChain agents, chains, direct chat
2. Dotprompt mode: Pass `extra_body={"prompt_variables": {...}}`

**Implementation** (from code):

- **Lines 110-118**: Builds `chat_kwargs` dict with:
  - `model`: Uses provided model or `self.default_model`
  - `openai_api_base`: Set to `self.proxy_url`
  - `openai_api_key`: Set to `self.api_key`
  - `temperature`: Uses provided or default
  - `max_tokens`: Uses provided or default
  - Merges `self.default_kwargs` and `**kwargs`
- **Lines 121-128**: If `extra_body` provided:
  - Adds `chat_kwargs["extra_body"] = extra_body`
  - Logs with debug level
- **Line 130**: Returns `ChatOpenAI(**chat_kwargs)`

**Return Type**: `ChatOpenAI` (from `langchain_openai`)

---

## Dependencies (from imports)

- `langchain_openai.ChatOpenAI` (line 9)
- `tools.logger.logger.get_logger` (line 11)

---

## Notes from Code

- Class docstring (lines 17-40) includes usage examples but not verified
- Method docstring (lines 97-108) includes usage examples but not verified
- Does not implement `BaseLLM` interface (no `generate()` or `embed()` methods)
- Returns `ChatOpenAI` objects for use with LangChain/LangGraph frameworks
