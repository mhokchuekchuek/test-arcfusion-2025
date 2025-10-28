# LLM Tools

Tools for interacting with language models and processing documents.

## Available Tools

### 1. Client

**Purpose**: Generate text completions and embeddings

**Providers**:
- **LiteLLM**: Direct API via LiteLLM proxy (OpenAI, Anthropic, etc.)
- **LangChain**: Agent framework integration

**Use Cases**:
- Text generation for RAG and synthesis
- Embedding generation for vector search
- Multi-agent tool calling

**Quick Start**:
```python
from tools.llm.client.selector import LLMClientSelector

llm = LLMClientSelector.create(
    provider="litellm",
    model="gpt-4"
)
response = llm.generate("What is RAG?")
```

**Documentation**:
- [Design Document](./client/design.md)
- [LiteLLM API Reference](./client/litellm/api-reference.md)
- [LangChain API Reference](./client/langchain/api-reference.md)

---

### 2. Parser

**Purpose**: Extract and convert document content

**Providers**:
- **Docling**: PDF to markdown with layout preservation

**Use Cases**:
- PDF ingestion pipeline
- Document preprocessing
- Content extraction

**Quick Start**:
```python
from tools.llm.parser.selector import ParserSelector

parser = ParserSelector.create(provider="docling")
markdown = parser.parse("document.pdf")
```

**Documentation**:
- [Docling API Reference](./parser/docling/api-reference.md)

---

### 3. WebSearch

**Purpose**: Search the web for current information

**Providers**:
- **Tavily**: AI-optimized search API

**Use Cases**:
- Research agent web searches
- Real-time information retrieval
- Fact verification

**Quick Start**:
```python
from tools.llm.websearch.selector import WebSearchSelector

search = WebSearchSelector.create(
    provider="tavily",
    api_key="tvly-..."
)
results = search.search("latest AI news", max_results=5)
```

**Documentation**:
- [Tavily API Reference](./websearch/tavily/api-reference.md)

---

### 4. Chunking

**Purpose**: Split documents into manageable chunks

**Providers**:
- **LangChain**: Text splitting with overlap

**Use Cases**:
- Document preprocessing
- Context window management
- Embedding optimization

---

## Architecture

```
LLM Tools
├─ Client ──────→ Generate text, embeddings
├─ Parser ──────→ PDF to markdown
├─ WebSearch ───→ Real-time web search
└─ Chunking ────→ Document splitting
```

---

## Configuration

```bash
# LLM Client
LLM_PROVIDER=litellm
LLM_MODEL=gpt-4
OPENAI_API_KEY=sk-...

# Web Search
TAVILY_API_KEY=tvly-...
```

---

## Related Documentation

- [Tools Overview](../README.md)
- [LLM Client Design](./client/design.md)
