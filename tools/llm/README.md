# LLM Tools

## Module Overview

The `tools/llm/` module provides all LLM and AI-related infrastructure components. These tools handle interactions with language models, document processing, text chunking, and web search capabilities.

**Purpose**: LLM/AI-related infrastructure
**Categories**: Clients, Parsers, Chunkers, Web Search

## Available Tools

### LLM Clients (`llm/client/`)

**Purpose**: Interface to LLM providers (OpenAI, Anthropic, etc.)

**Providers**:
- **LiteLLM**: Unified API for 100+ LLM providers with fallbacks and retries
- **LangChain**: Agent-compatible LLM wrapper with tool calling support

**Use Cases**:
- Text generation for agents
- Embedding generation for RAG
- Multi-model support with provider fallbacks

**See**: [client/README.md](./client/README.md)

### Document Parsers (`llm/parser/`)

**Purpose**: Extract and parse text from various document formats

**Providers**:
- **Docling**: Advanced PDF parser handling academic papers, tables, equations, and multi-column layouts

**Use Cases**:
- PDF to markdown conversion
- Document ingestion pipeline
- Structured content extraction

**See**: [parser/README.md](./parser/README.md)

### Text Chunkers (`llm/chunking/`)

**Purpose**: Split documents into manageable chunks for embedding and retrieval

**Providers**:
- **RecursiveCharacterTextSplitter**: Semantic-aware text splitting with configurable overlap

**Use Cases**:
- Document preprocessing for RAG
- Context window management
- Embedding optimization

**See**: [chunking/README.md](./chunking/README.md)

### Web Search (`llm/websearch/`)

**Purpose**: Search the web for current information and real-time data

**Providers**:
- **Tavily**: LLM-optimized search API with clean, answer-focused results

**Use Cases**:
- Research agent web searches
- Out-of-scope query handling
- Current events and fact-checking

**See**: [websearch/README.md](./websearch/README.md)

## Usage Examples

### Complete RAG Pipeline

```python
from tools.llm.client.selector import LLMClientSelector
from tools.llm.parser.selector import ParserSelector
from tools.llm.chunking.selector import TextChunkerSelector

# 1. Parse PDF document
parser = ParserSelector.create(provider="docling")
document_text = parser.parse("research_paper.pdf")

# 2. Chunk text for embeddings
chunker = TextChunkerSelector.create(
    provider="recursive",
    chunk_size=1000,
    chunk_overlap=200
)
chunks = chunker.split(document_text)

# 3. Generate embeddings and completions
llm = LLMClientSelector.create(
    provider="litellm",
    proxy_url="http://localhost:4000",
    completion_model="gpt-4"
)
embeddings = llm.embed(chunks)
response = llm.generate("What is the main finding of this paper?")
```

### Research with Web Search

```python
from tools.llm.client.selector import LLMClientSelector
from tools.llm.websearch.selector import WebSearchSelector

# Search the web
search = WebSearchSelector.create(
    provider="tavily",
    api_key="tvly-..."
)
results = search.search("latest AI developments", max_results=5)

# Synthesize findings with LLM
llm = LLMClientSelector.create(provider="litellm", proxy_url="...")
synthesis = llm.generate(f"Summarize these findings: {results}")
```

## Integration Points

The LLM tools are used throughout the application:

- **`src/agents/`**: Agents use LLM clients for reasoning and tool calling
- **`ingestor/`**: Uses parsers and chunkers for document processing
- **`evaluation/`**: Uses LLM clients for quality assessment
- **`src/rag/`**: Uses all LLM tools for retrieval pipeline

## Configuration

All LLM tools are configured via environment variables:

```bash
# LLM Client
LLM_PROVIDER=litellm
LITELLM_PROXY_URL=http://localhost:4000
COMPLETION_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-small

# Web Search
WEBSEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-...

# Chunking (optional overrides)
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

See `configs/` directory for detailed configuration options.

## Tool Selection Strategy

### When to Use LiteLLM vs LangChain

**LiteLLM** (`provider="litellm"`):
- Direct completions and embeddings
- RAG pipelines
- Evaluation tasks
- Lower overhead, faster responses

**LangChain** (`provider="langchain"`):
- Agents with tool calling
- Complex chains and workflows
- LangChain ecosystem integration
- Advanced prompt templates

### Example: Provider Selection

```python
# For RAG retrieval (use LiteLLM for speed)
llm_rag = LLMClientSelector.create(provider="litellm", proxy_url="...")

# For agent reasoning (use LangChain for tools)
llm_agent = LLMClientSelector.create(provider="langchain", proxy_url="...")
```

## Adding New Providers

Each tool category follows the provider pattern. To add a new provider:

1. Create provider directory: `tools/llm/{category}/{provider_name}/`
2. Implement base interface: `main.py` with provider logic
3. Register in selector: Update `_PROVIDERS` in `selector.py`
4. Document usage: Add to provider README

See [../README.md](../README.md) for detailed provider addition steps.

## Best Practices

1. **Use Selectors**: Always use selector classes, never import providers directly
2. **Configuration**: Load provider settings from config/environment
3. **Error Handling**: Implement retries and fallbacks for LLM API calls
4. **Cost Management**: Use cheaper models for development/testing
5. **Observability**: Track LLM calls with Langfuse for monitoring

## Performance Considerations

**LLM Client**:
- Use streaming for long responses
- Implement request batching for embeddings
- Cache embeddings when possible

**Parsers**:
- Docling can be CPU-intensive for large PDFs
- Consider async processing for multiple documents

**Chunking**:
- Optimize chunk_size based on model context window
- Balance chunk_overlap vs. storage costs

**Web Search**:
- Tavily has rate limits - implement request queuing
- Cache search results when appropriate

## Troubleshooting

**Issue**: LLM API timeouts
**Solution**: Increase timeout settings or use streaming mode

**Issue**: Poor chunking quality
**Solution**: Adjust chunk_size and chunk_overlap parameters

**Issue**: Parser failing on PDFs
**Solution**: Ensure PDF is not corrupted or password-protected

**Issue**: Web search rate limits
**Solution**: Implement exponential backoff and request throttling

## See Also

- [LLM Client Design](./client/README.md) - Detailed client architecture
- [Tool Provider Pattern](../../docs/architecture/tool-provider-pattern.md) - Design philosophy
- [Agent Documentation](../../docs/agents/README.md) - How agents use LLM tools
