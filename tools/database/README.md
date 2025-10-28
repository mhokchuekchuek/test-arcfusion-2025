# Database Tools

## Module Overview

The `tools/database/` module provides data persistence and storage infrastructure for the RAG system. This includes vector stores for semantic search and memory stores for conversation history.

**Purpose**: Data persistence (vectors, session memory)
**Categories**: Vector stores, Memory stores

## Available Tools

### Vector Stores (`database/vector/`)

**Purpose**: Store and retrieve document embeddings for semantic search

**Providers**:
- **Qdrant**: High-performance vector database with filtering and hybrid search

**Use Cases**:
- Document retrieval for RAG
- Semantic search over knowledge base
- Similarity matching
- Hybrid search (vector + keyword)

**See**: [vector/README.md](./vector/README.md)

### Memory Stores (`database/memory/`)

**Purpose**: Session-based conversation memory and history

**Providers**:
- **Redis**: Fast in-memory key-value store with TTL support

**Use Cases**:
- Multi-turn conversation history
- Session management
- User context tracking
- Caching frequently accessed data

**See**: [memory/README.md](./memory/README.md)

## Architecture Pattern

Both database tools follow the provider pattern for easy swapping:

```
database/
├── vector/
│   ├── base.py          # BaseVectorStore interface
│   ├── selector.py      # VectorStoreSelector factory
│   └── qdrant/          # Qdrant implementation
│       └── main.py
└── memory/
    ├── base.py          # BaseMemory interface
    ├── selector.py      # MemorySelector factory
    └── redis/           # Redis implementation
        └── main.py
```

## Usage Examples

### Complete RAG Pipeline with Storage

```python
from tools.llm.client.selector import LLMClientSelector
from tools.llm.parser.selector import ParserSelector
from tools.llm.chunking.selector import TextChunkerSelector
from tools.database.vector.selector import VectorStoreSelector

# 1. Parse and chunk document
parser = ParserSelector.create(provider="docling")
text = parser.parse("document.pdf")

chunker = TextChunkerSelector.create(provider="recursive", chunk_size=1000)
chunks = chunker.split(text)

# 2. Generate embeddings
llm = LLMClientSelector.create(provider="litellm", proxy_url="...")
embeddings = llm.embed(chunks)

# 3. Store in vector database
vectordb = VectorStoreSelector.create(
    provider="qdrant",
    host="localhost",
    port=6333,
    collection_name="documents"
)

# Store chunks with metadata
for chunk, embedding in zip(chunks, embeddings):
    vectordb.add(
        vector=embedding,
        payload={"text": chunk, "source": "document.pdf"}
    )

# 4. Retrieve relevant chunks
query = "What is the main finding?"
query_embedding = llm.embed([query])[0]
results = vectordb.search(query_embedding, limit=5)

for result in results:
    print(f"Score: {result['score']}")
    print(f"Text: {result['payload']['text']}")
```

### Conversation with Memory

```python
from tools.database.memory.selector import MemorySelector
from tools.llm.client.selector import LLMClientSelector

# Initialize memory store
memory = MemorySelector.create(
    provider="redis",
    host="localhost",
    port=6379
)

llm = LLMClientSelector.create(provider="litellm", proxy_url="...")

# Conversation loop
session_id = "user_123"

def chat(user_message: str):
    # Get conversation history
    history = memory.get(session_id) or []

    # Add user message
    history.append({"role": "user", "content": user_message})

    # Generate response
    prompt = format_history(history)
    response = llm.generate(prompt)

    # Add assistant response
    history.append({"role": "assistant", "content": response})

    # Save to memory with 1 hour TTL
    memory.set(session_id, history, ttl=3600)

    return response

# Multi-turn conversation
print(chat("What is RAG?"))
print(chat("How does it work?"))  # Has context from previous message
```

## Integration Points

The database tools are used throughout the application:

- **`ingestor/`**: Uses vector store
  - Stores document embeddings
  - Creates vector collections

- **`src/rag/`**: Uses vector store
  - Retrieves relevant documents
  - Performs similarity search

- **`src/apis/`**: Uses both vector and memory stores
  - RAG endpoints use vector store
  - Chat endpoints use memory store

- **`src/agents/`**: Uses memory store
  - Maintains conversation context
  - Tracks agent state

## Configuration

### Environment Variables

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
REDIS_DB=0
REDIS_TTL=3600  # 1 hour default TTL
```

### Docker Compose Setup

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  qdrant_data:
  redis_data:
```

## Data Flow

### Ingestion Flow

```
PDF Document
    ↓
[Parser] → Text
    ↓
[Chunker] → Chunks
    ↓
[LLM] → Embeddings
    ↓
[Vector Store] → Stored for retrieval
```

### Retrieval Flow

```
User Query
    ↓
[LLM] → Query Embedding
    ↓
[Vector Store] → Similar Documents
    ↓
[LLM] → Generated Answer
```

### Conversation Flow

```
User Message
    ↓
[Memory Store] → Load History
    ↓
[LLM] → Generate Response (with context)
    ↓
[Memory Store] → Save Updated History
```

## Best Practices

### Vector Store

1. **Collection Design**: Use separate collections for different document types
2. **Batch Operations**: Insert embeddings in batches for better performance
3. **Metadata**: Store rich metadata for filtering and debugging
4. **Index Optimization**: Configure appropriate vector index settings
5. **Backup**: Regular backups of vector database

### Memory Store

1. **TTL Management**: Set appropriate TTL based on session duration
2. **Key Namespacing**: Use prefixes to organize keys (e.g., `session:{id}`)
3. **Data Size**: Keep conversation history bounded (e.g., last 10 messages)
4. **Serialization**: Use efficient serialization (JSON, msgpack)
5. **Cleanup**: Implement periodic cleanup of expired sessions

## Performance Optimization

### Vector Store

```python
# Batch insertion (faster than individual inserts)
vectordb.add_batch(
    vectors=embeddings,
    payloads=[{"text": chunk, "id": i} for i, chunk in enumerate(chunks)]
)

# Parallel search (for multiple queries)
import asyncio

async def parallel_search(queries):
    tasks = [vectordb.asearch(q) for q in queries]
    return await asyncio.gather(*tasks)
```

### Memory Store

```python
# Use connection pooling
memory = MemorySelector.create(
    provider="redis",
    host="localhost",
    connection_pool_size=10
)

# Batch operations
pipe = memory.pipeline()
for key, value in items:
    pipe.set(key, value)
pipe.execute()
```

## Scaling Considerations

### Vector Store

**Vertical Scaling**:
- Increase RAM for in-memory indexes
- Add CPU cores for parallel search
- Use SSD for persistent storage

**Horizontal Scaling**:
- Qdrant supports sharding and replication
- Distribute collections across nodes
- Read replicas for query load

**Capacity Planning**:
- 1M vectors (768-dim) ≈ 3-4GB RAM
- Consider growth over time
- Plan for 3-5x headroom

### Memory Store

**Vertical Scaling**:
- Redis is single-threaded per instance
- More RAM for larger working set
- Use Redis Cluster for distribution

**Horizontal Scaling**:
- Redis Cluster for automatic sharding
- Separate instances by use case
- Read replicas for read-heavy workloads

## Monitoring

### Vector Store Metrics

```python
# Collection stats
stats = vectordb.get_collection_stats("documents")
print(f"Vectors: {stats['vectors_count']}")
print(f"Index size: {stats['index_size_mb']}MB")

# Query performance
import time
start = time.time()
results = vectordb.search(query_vector, limit=10)
print(f"Search latency: {(time.time() - start)*1000:.2f}ms")
```

### Memory Store Metrics

```python
# Redis stats
info = memory.info()
print(f"Used memory: {info['used_memory_human']}")
print(f"Connected clients: {info['connected_clients']}")
print(f"Keys: {memory.dbsize()}")
```

## Troubleshooting

### Vector Store Issues

**Issue**: Slow search performance
**Solution**: Optimize index settings, use approximate search, add more RAM

**Issue**: Out of memory
**Solution**: Use persistent storage, increase RAM, archive old data

**Issue**: Connection errors
**Solution**: Check Qdrant is running, verify host/port, check firewall

### Memory Store Issues

**Issue**: Redis out of memory
**Solution**: Increase maxmemory, enable eviction policy, reduce TTL

**Issue**: Lost data after restart
**Solution**: Enable persistence (RDB or AOF), configure backup

**Issue**: Slow operations
**Solution**: Use pipeline for batch ops, check network latency, monitor slow log

## See Also

- [Vector Store Details](./vector/README.md) - Qdrant setup and usage
- [Memory Store Details](./memory/README.md) - Redis configuration
- [RAG Pipeline](../../docs/rag/README.md) - How databases fit in RAG
- [Tool Provider Pattern](../../docs/architecture/tool-provider-pattern.md)
