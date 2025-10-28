# RAG System Documentation

Semantic document retrieval for the multi-agent system using vector embeddings and Qdrant.

## Quick Start

**New to the RAG module?** Start here:
1. [Retrieval Strategy](./retrieval-strategy.md) - Chunking and search design
2. [API Reference](./api-reference.md) - Component APIs

---

## Architecture Overview

```
User Query
    │
    ▼
┌──────────────────┐
│ DocumentRetriever│  Embed query → Search Qdrant
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Top-K Documents  │  Ranked by similarity
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Research Agent  │  Use docs to answer
└────────┬─────────┘
         │
         ▼
   Final Answer
```

---

## Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **DocumentRetriever** | `src/rag/retriever/document_retriever.py` | Semantic search in Qdrant |
| **SessionMemory** | `src/rag/memory/session_memory.py` | Conversation history (optional) |
| **RAGService** | `src/rag/service.py` | High-level orchestrator |

---

## How It Works

### Ingestion Pipeline

```
PDF → Docling Parser → Text Chunks → Embeddings → Qdrant
```

| Step | Details |
|------|---------|
| **Parse** | Extract text, tables, equations with Docling |
| **Chunk** | 1000 tokens per chunk, 200 overlap |
| **Embed** | text-embedding-3-small (1536 dim) |
| **Store** | Qdrant vector database |

**Configuration**: `configs/ingestor/`

### Retrieval Pipeline

```
Query → Embedding → Similarity Search → Top-K Docs → Agent
```

| Step | Time |
|------|------|
| Generate embedding | 50-100ms |
| Vector search | 5-20ms |
| **Total** | **60-150ms** |

**Configuration**: `configs/agents/langgraph.yaml`

---

## Key Features

### Semantic Search

**Characteristics:**
- Dense vector embeddings for semantic similarity
- Cosine similarity ranking
- Sub-50ms search latency
- Metadata filtering (source, page, section)

### Chunking Strategy

| Parameter | Value | Why |
|-----------|-------|-----|
| **Chunk Size** | 1000 tokens | Optimal for semantic coherence |
| **Overlap** | 200 tokens | Prevent concept splitting |
| **Splitter** | RecursiveCharacterTextSplitter | Preserve structure |

**Example:**
```
Document (3000 tokens):
Chunk 1: [0 ───── 1000]
Chunk 2:    [800 ───── 1800]  ← 200 overlap
Chunk 3:        [1600 ───── 2600]
```

### Integration Points

| Integration | Usage |
|-------------|-------|
| **Research Agent** | PDFRetrievalTool uses DocumentRetriever |
| **Direct API** | RAGService for standalone Q&A |
| **Observability** | Langfuse traces all operations |

---

## Configuration

```yaml
# configs/rag.yaml
vector_store:
  provider: qdrant
  host: localhost
  port: 6333
  collection: documents

embeddings:
  model: text-embedding-3-small
  dimensions: 1536

retrieval:
  top_k: 5
  chunk_size: 1000
  chunk_overlap: 200
```

---

## Performance

| Metric | Value |
|--------|-------|
| Embedding generation | ~50-100ms |
| Vector search | ~5-20ms |
| **Total retrieval** | **~60-150ms** |
| Context size (5 docs) | 2000-5000 tokens |

---

## Usage Example

```python
from src.rag.retriever.document_retriever import DocumentRetriever

# Create retriever
retriever = DocumentRetriever(llm_client, vector_store)

# Search documents
docs = retriever.retrieve("What is RAG?", top_k=5)

# Display results
for doc in docs:
    print(f"{doc['source']} p.{doc['page']} (score: {doc['score']:.3f})")
    print(f"  {doc['text'][:100]}...\n")
```

---

## Related Documentation

### Core Concepts
- [Retrieval Strategy](./retrieval-strategy.md) - Design decisions
- [API Reference](./api-reference.md) - Component APIs

### Integration
- [Research Agent](../agents/research/design.md) - How agents use retrieval
- [PDF Ingestion](../ingestor/README.md) - Document processing

---

## Quick Reference

| Topic | Document |
|-------|----------|
| **Chunking** | [Retrieval Strategy](./retrieval-strategy.md#chunking-strategy) |
| **Top-K Selection** | [Retrieval Strategy](./retrieval-strategy.md#retrieval-parameters) |
| **API Methods** | [API Reference](./api-reference.md#documentretriever) |
| **Vector Store Setup** | [Architecture Decisions](../architecture/architecture-decisions.md) |

---

**Questions?** See [Retrieval Strategy](./retrieval-strategy.md) for design decisions or [API Reference](./api-reference.md) for implementation details.
