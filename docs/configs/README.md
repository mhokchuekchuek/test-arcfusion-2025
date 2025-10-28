# Configuration Guide

All system settings are managed through YAML files using [Dynaconf](https://www.dynaconf.com/).

## Directory Structure

```
configs/
├── agents/
│   ├── langgraph.yaml    # Agent settings (models, temperatures, prompts)
│   ├── rag.yaml          # RAG retrieval settings
│   └── shared.yaml       # Shared settings (API, databases, logging)
├── evaluation/
│   └── evaluation.yaml   # Evaluation scenarios and LLM-as-a-Judge
├── ingestor/
│   └── ingestion.yaml    # PDF ingestion pipeline
├── litellm/
│   └── proxy_config.yaml # LLM provider routing (OpenAI, Anthropic, etc.)
└── prompts/
    └── uploader.yaml     # Prompt upload to Langfuse
```

## Quick Start

### 1. Basic Usage

Configurations are loaded automatically from YAML files:

```python
from dynaconf import Dynaconf

settings = Dynaconf(settings_files=["configs/agents/*.yaml"])

# Access settings
model = settings.orchestrator.model  # "gpt-4-turbo"
temp = settings.orchestrator.temperature  # 0.3
```

### 2. Environment Variables

Override any setting using environment variables with `__` (double underscore):

```bash
# Format: SECTION__SUBSECTION__KEY=value

# Override orchestrator model
export ORCHESTRATOR__MODEL=gpt-4o

# Override Redis host
export MEMORYDB__REDIS__HOST=localhost

# Override API keys
export API_KEYS__TAVILY_API_KEY=tvly-xxxxx
export LANGFUSE_PUBLIC_KEY=pk-xxxxx
export LANGFUSE_SECRET_KEY=sk-xxxxx
```

### 3. Using .env File

Create `.env` in project root:

```bash
# .env file
ORCHESTRATOR__MODEL=gpt-4o
MEMORYDB__REDIS__HOST=localhost
API_KEYS__TAVILY_API_KEY=tvly-xxxxx
LANGFUSE_PUBLIC_KEY=pk-xxxxx
LANGFUSE_SECRET_KEY=sk-xxxxx
```

Dynaconf automatically loads `.env` files.

---

## Configuration Files

### `agents/langgraph.yaml`

**Agent behavior and LLM settings**

```yaml
orchestrator:
  model: gpt-4-turbo           # Which LLM to use
  temperature: 0.3             # Randomness (0=deterministic)
  max_clarifications: 2        # Loop prevention limit

research:
  model: gpt-4-turbo
  temperature: 0.7
  max_iterations: 10           # ReAct loop limit

tools:
  pdf_retrieval:
    top_k: 100                 # Documents to retrieve
  web_search:
    max_results: 100           # Web results per search
```

**Common overrides:**
```bash
export ORCHESTRATOR__MODEL=gpt-4o-mini
export RESEARCH__TEMPERATURE=0.5
export TOOLS__PDF_RETRIEVAL__TOP_K=5
```

---

### `agents/shared.yaml`

**Infrastructure and API settings**

```yaml
api:
  host: 0.0.0.0
  port: 8000

llm:
  proxy_url: http://litellm-proxy:4000

memorydb:
  redis:
    host: redis
    port: 6379
    session_ttl: 86400         # 24 hours

vectordb:
  qdrant:
    host: qdrant
    port: 6333
    collection_name: pdf_documents
    vector_size: 1536

observability:
  langfuse:
    enabled: true
    host: https://cloud.langfuse.com
```

**Common overrides:**
```bash
export API__PORT=9000
export MEMORYDB__REDIS__HOST=localhost
export VECTORDB__QDRANT__HOST=localhost
export OBSERVABILITY__LANGFUSE__ENABLED=false
```

---

### `agents/rag.yaml`

**RAG retrieval settings**

```yaml
rag:
  llm:
    embedding_model: text-embedding-3-small
    default_top_k: 1000
    max_context_length: 4000

  retrieval:
    min_similarity_score: 0.5  # Filter threshold (0-1)
```

**Common overrides:**
```bash
export RAG__LLM__DEFAULT_TOP_K=5
export RAG__RETRIEVAL__MIN_SIMILARITY_SCORE=0.7
```

---

### `ingestor/ingestion.yaml`

**PDF ingestion pipeline**

```yaml
ingestion:
  directory: ./pdfs            # PDF source directory
  file_type: pdf
  chunk_size: 1000             # Tokens per chunk
  chunk_overlap: 200           # Overlap between chunks
  batch_size: 100              # Embeddings per batch

  llm:
    provider: litellm
    embedding_model: text-embedding-3-small

  vectordb:
    provider: qdrant
    collection_name: documents
```

**Common overrides:**
```bash
export INGESTION__DIRECTORY=/path/to/pdfs
export INGESTION__CHUNK_SIZE=500
export INGESTION__BATCH_SIZE=50
```

---

### `evaluation/evaluation.yaml`

**Evaluation and testing**

```yaml
evaluation:
  api_url: http://localhost:8000  # API to test

  llm:
    provider: litellm
    model: gpt-4o                  # Judge model
    temperature: 0                 # Deterministic
```

**Common overrides:**
```bash
export EVALUATION__API_URL=http://api:8000
export EVALUATION__LLM__MODEL=gpt-4o-mini
```

---

### `litellm/proxy_config.yaml`

**LLM provider routing and models**

Defines which LLM providers and models are available. See [LiteLLM docs](https://docs.litellm.ai/docs/proxy/configs) for full syntax.

```yaml
model_list:
  - model_name: gpt-4-turbo
    litellm_params:
      model: gpt-4-turbo-preview
      api_key: os.environ/OPENAI_API_KEY

  - model_name: claude-3-5-sonnet
    litellm_params:
      model: claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY
```

---

### `prompts/uploader.yaml`

**Prompt upload to Langfuse**

```yaml
prompts:
  directory: prompts             # Directory containing .prompt files
  version: v1                    # Active version
  label: dev                     # Environment label
```

**Common overrides:**
```bash
export PROMPTS__VERSION=v2
export PROMPTS__LABEL=production
```

---

## Common Tasks

### Change LLM Models

```bash
# Use GPT-4o for all agents
export ORCHESTRATOR__MODEL=gpt-4o
export RESEARCH__MODEL=gpt-4o
export CLARIFICATION__MODEL=gpt-4o
export SYNTHESIS__MODEL=gpt-4o
```

### Run Locally (without Docker)

```bash
export MEMORYDB__REDIS__HOST=localhost
export VECTORDB__QDRANT__HOST=localhost
export LLM__PROXY_URL=http://localhost:4000
```

### Disable Langfuse Observability

```bash
export OBSERVABILITY__LANGFUSE__ENABLED=false
```

### Use Different Embedding Model

```bash
export RAG__LLM__EMBEDDING_MODEL=text-embedding-ada-002
export INGESTION__LLM__EMBEDDING_MODEL=text-embedding-ada-002
```

---

## Tips

1. **Environment variables override YAML** - Useful for secrets and environment-specific settings
2. **Use `.env` file** - Keeps overrides organized and out of version control
3. **Double underscores** - `SECTION__SUBSECTION__KEY` maps to nested YAML
4. **Arrays use index** - `ARRAY__0=value` for first element
5. **Check loaded config** - Use `settings.as_dict()` to debug

---

## Related Documentation

- [Dynaconf Documentation](https://www.dynaconf.com/)
- [LiteLLM Proxy Config](https://docs.litellm.ai/docs/proxy/configs)
- [Agent Configuration](../agents/README.md)
- [RAG Strategy](../rag/retrieval-strategy.md)
- [Prompt Management](../../prompts/README.md)
