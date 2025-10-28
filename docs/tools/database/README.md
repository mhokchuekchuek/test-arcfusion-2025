# Database Tools

Tools for data persistence and retrieval.

## Available Tools

### 1. Vector Store

**Purpose**: Semantic search over embeddings

**Providers**:
- **Qdrant**: High-performance vector database

**Use Cases**:
- Document retrieval for RAG
- Semantic similarity search
- Nearest neighbor queries

**Quick Start**:
```python
from tools.database.vector.selector import VectorStoreSelector

vector_store = VectorStoreSelector.create(
    provider="qdrant",
    host="localhost",
    port=6333,
    collection_name="documents"
)

# Search
results = vector_store.search(
    query_vector=embedding,
    top_k=5
)
```

**Documentation**:
- [Qdrant API Reference](./vector/qdrant/api-reference.md)

---

### 2. Memory Store

**Purpose**: Session and conversation memory

**Providers**:
- **Redis**: Fast in-memory key-value store

**Use Cases**:
- Conversation history storage
- Session management
- Response caching

**Quick Start**:
```python
from tools.database.memory.selector import MemorySelector

memory = MemorySelector.create(
    provider="redis",
    host="localhost",
    port=6379
)

# Store and retrieve
memory.set("session:123", conversation_data)
data = memory.get("session:123")
```

**Documentation**:
- [Redis API Reference](./memory/redis/api-reference.md)

---

## Architecture

```
Database Tools
├─ Vector Store ──→ Semantic search (Qdrant)
└─ Memory Store ──→ Session/cache (Redis)
```

---

## Configuration

```bash
# Vector Store
VECTOR_STORE_PROVIDER=qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=documents

# Memory Store
MEMORY_PROVIDER=redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## Common Patterns

### RAG Pipeline

```python
# Embed query
embedding = llm.embed(query)

# Search vector store
results = vector_store.search(embedding, top_k=5)

# Cache results
memory.set(f"cache:{query_hash}", results)
```

---

## Related Documentation

- [Tools Overview](../README.md)
- [Vector Search in RAG](../../architecture/rag-architecture.md)
