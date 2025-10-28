# Vector Store Tools

## Purpose

Store and retrieve document embeddings for semantic search in the RAG system. Vector stores enable finding similar documents based on semantic meaning rather than keyword matching.

## Available Providers

### Qdrant

**Provider**: `qdrant`

**Description**: High-performance vector database designed for production-scale similarity search with filtering capabilities.

**Key Features**:
- **Fast similarity search**: Optimized HNSW index for approximate nearest neighbor search
- **Payload filtering**: Filter by metadata before/during vector search
- **Hybrid search**: Combine vector similarity with keyword matching
- **Scalability**: Handles millions of vectors efficiently
- **Persistence**: In-memory or disk-based storage
- **Docker-friendly**: Easy deployment with Docker

**Why Qdrant Was Chosen**:
- Production-ready with excellent performance
- Rich filtering capabilities (essential for multi-document RAG)
- Active development and community
- Better performance than Chroma, easier than Weaviate
- Good Python SDK and documentation

**Modes**:
- **In-memory**: Fast, for development/testing
- **Persistent**: Disk-backed, for production

## Usage Examples

### Basic Vector Operations

```python
from tools.database.vector.selector import VectorStoreSelector

# Initialize vector store
vectordb = VectorStoreSelector.create(
    provider="qdrant",
    host="localhost",
    port=6333,
    collection_name="documents"
)

# Create collection with schema
vectordb.create_collection(
    collection_name="documents",
    vector_size=768,  # Dimension of embeddings
    distance="Cosine"  # or "Euclidean", "Dot"
)

# Add vectors with metadata
vectordb.add(
    id="doc_1_chunk_0",
    vector=[0.1, 0.2, ...],  # 768-dimensional embedding
    payload={
        "text": "Document chunk text...",
        "source": "document.pdf",
        "page": 1,
        "chunk_index": 0
    }
)

# Search for similar vectors
results = vectordb.search(
    query_vector=[0.15, 0.18, ...],
    limit=5
)

for result in results:
    print(f"Score: {result['score']}")
    print(f"Text: {result['payload']['text']}")
```

### Batch Operations

```python
# Batch insert (more efficient)
vectors = [embedding1, embedding2, embedding3, ...]
payloads = [
    {"text": chunk1, "source": "doc1.pdf", "page": 1},
    {"text": chunk2, "source": "doc1.pdf", "page": 2},
    {"text": chunk3, "source": "doc2.pdf", "page": 1},
]

vectordb.add_batch(
    ids=[f"doc_{i}" for i in range(len(vectors))],
    vectors=vectors,
    payloads=payloads
)
```

### Filtered Search

```python
# Search with metadata filtering
results = vectordb.search(
    query_vector=query_embedding,
    limit=10,
    filter={
        "must": [
            {"key": "source", "match": {"value": "research_paper.pdf"}}
        ]
    }
)

# Complex filter
results = vectordb.search(
    query_vector=query_embedding,
    limit=10,
    filter={
        "must": [
            {"key": "category", "match": {"value": "machine_learning"}}
        ],
        "should": [
            {"key": "year", "range": {"gte": 2020}}
        ]
    }
)
```

### Complete RAG Pipeline

```python
from tools.llm.client.selector import LLMClientSelector
from tools.llm.parser.selector import ParserSelector
from tools.llm.chunking.selector import TextChunkerSelector
from tools.database.vector.selector import VectorStoreSelector

# 1. Setup
parser = ParserSelector.create(provider="docling")
chunker = TextChunkerSelector.create(provider="recursive", chunk_size=1000)
llm = LLMClientSelector.create(provider="litellm", proxy_url="...")
vectordb = VectorStoreSelector.create(provider="qdrant", host="localhost", port=6333)

# 2. Ingest document
text = parser.parse("document.pdf")
chunks = chunker.split(text)
embeddings = llm.embed(chunks)

vectordb.add_batch(
    ids=[f"doc_chunk_{i}" for i in range(len(chunks))],
    vectors=embeddings,
    payloads=[{"text": chunk, "source": "document.pdf"} for chunk in chunks]
)

# 3. Query
query = "What is the main finding?"
query_embedding = llm.embed([query])[0]
results = vectordb.search(query_embedding, limit=5)

# 4. Generate answer
context = "\n\n".join([r['payload']['text'] for r in results])
answer = llm.generate(f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:")
print(answer)
```

## Configuration

### Environment Variables

```bash
# Vector store provider
VECTOR_STORE_PROVIDER=qdrant

# Qdrant connection
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=documents

# Optional: API key for Qdrant Cloud
QDRANT_API_KEY=...
```

### Docker Setup

```yaml
# docker-compose.yml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"  # gRPC port
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT_CONFIG=/qdrant/config/production.yaml

volumes:
  qdrant_data:
```

Start Qdrant:
```bash
docker-compose up -d qdrant
```

### Collection Configuration

```python
# Create collection with custom settings
vectordb.create_collection(
    collection_name="documents",
    vector_size=768,
    distance="Cosine",
    hnsw_config={
        "m": 16,  # Number of connections per node
        "ef_construct": 100  # Construction time quality
    },
    optimizers_config={
        "indexing_threshold": 20000
    }
)
```

## Base Interface

All vector store providers implement the `BaseVectorStore` interface:

```python
from abc import ABC, abstractmethod

class BaseVectorStore(ABC):
    @abstractmethod
    def create_collection(self, collection_name: str, vector_size: int, **kwargs):
        """Create a vector collection."""
        pass

    @abstractmethod
    def add(self, id: str, vector: list[float], payload: dict):
        """Add single vector with metadata."""
        pass

    @abstractmethod
    def add_batch(self, ids: list[str], vectors: list, payloads: list[dict]):
        """Add multiple vectors in batch."""
        pass

    @abstractmethod
    def search(self, query_vector: list[float], limit: int, **kwargs) -> list[dict]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    def delete(self, ids: list[str]):
        """Delete vectors by IDs."""
        pass
```

## Integration Points

The vector store is used by:

- **`ingestor/`**: Document ingestion
  - Creates collections for new document types
  - Stores document embeddings
  - Handles batch uploads

- **`src/rag/`**: Retrieval pipeline
  - Searches for relevant documents
  - Applies filters based on query
  - Reranks results

- **`src/apis/`**: API endpoints
  - Serves search queries
  - Manages document uploads
  - Provides collection stats

## Search Strategies

### Basic Similarity Search

```python
# Find most similar vectors
results = vectordb.search(
    query_vector=embedding,
    limit=5
)
```

### Filtered Similarity Search

```python
# Search within specific document
results = vectordb.search(
    query_vector=embedding,
    limit=5,
    filter={"must": [{"key": "source", "match": {"value": "doc.pdf"}}]}
)
```

### Hybrid Search (Vector + Keyword)

```python
# Combine semantic and keyword search
results = vectordb.search(
    query_vector=embedding,
    limit=10,
    filter={
        "must": [
            {"key": "text", "match": {"text": "machine learning"}}
        ]
    }
)
```

### Diversity-Aware Retrieval

```python
# Get diverse results using MMR (Maximal Marginal Relevance)
def diversified_search(vectordb, query_vector, limit=10, lambda_param=0.5):
    # Get more candidates than needed
    candidates = vectordb.search(query_vector, limit=limit * 3)

    selected = [candidates[0]]  # Start with top result
    candidates = candidates[1:]

    while len(selected) < limit and candidates:
        # Score combining relevance and diversity
        scores = []
        for candidate in candidates:
            relevance = candidate['score']
            max_similarity = max([
                cosine_similarity(candidate['vector'], s['vector'])
                for s in selected
            ])
            diversity = 1 - max_similarity
            score = lambda_param * relevance + (1 - lambda_param) * diversity
            scores.append(score)

        # Select best candidate
        best_idx = scores.index(max(scores))
        selected.append(candidates.pop(best_idx))

    return selected
```

## Performance Optimization

### Indexing

```python
# Configure HNSW index for your use case
vectordb.create_collection(
    collection_name="documents",
    vector_size=768,
    hnsw_config={
        "m": 16,          # Higher = better recall, more memory
        "ef_construct": 100  # Higher = better quality, slower indexing
    }
)

# Adjust search-time parameters
results = vectordb.search(
    query_vector=embedding,
    limit=10,
    search_params={"hnsw_ef": 128}  # Higher = better recall, slower search
)
```

### Batch Operations

```python
# Good: Batch insert
vectordb.add_batch(ids=ids, vectors=vectors, payloads=payloads)

# Bad: Individual inserts
for id, vector, payload in zip(ids, vectors, payloads):
    vectordb.add(id=id, vector=vector, payload=payload)
```

### Payload Indexing

```python
# Index frequently filtered fields
vectordb.create_field_index(
    collection_name="documents",
    field_name="source",
    field_schema="keyword"  # For exact matching
)

vectordb.create_field_index(
    collection_name="documents",
    field_name="text",
    field_schema="text"  # For full-text search
)
```

## Capacity Planning

### Storage Requirements

```
Storage per vector = vector_size * 4 bytes (float32) + payload size

Example:
- 768-dimensional embedding = 768 * 4 = 3,072 bytes
- Payload (~500 bytes text + metadata) = 500 bytes
- Total per vector ≈ 3.5 KB

For 1M vectors: ~3.5 GB
For 10M vectors: ~35 GB
```

### Memory Requirements

```
RAM for HNSW index ≈ 1.5-2x vector storage

Example for 1M vectors (768-dim):
- Vector storage: 3 GB
- HNSW index: 4-6 GB
- Total RAM: 7-9 GB
```

### Scaling Guidelines

| Vectors | RAM | CPU | Use Case |
|---------|-----|-----|----------|
| < 100K | 2 GB | 2 cores | Development |
| 100K-1M | 8 GB | 4 cores | Small production |
| 1M-10M | 32 GB | 8 cores | Medium production |
| 10M+ | 64+ GB | 16+ cores | Large production |

## Monitoring

```python
# Collection statistics
stats = vectordb.get_collection_stats("documents")
print(f"Vectors: {stats['vectors_count']:,}")
print(f"Indexed: {stats['indexed_vectors_count']:,}")
print(f"Points: {stats['points_count']:,}")

# Performance metrics
import time

start = time.time()
results = vectordb.search(query_vector, limit=10)
latency = (time.time() - start) * 1000
print(f"Search latency: {latency:.2f}ms")

# Health check
health = vectordb.health_check()
print(f"Status: {health['status']}")
```

## Best Practices

1. **Collection Design**: One collection per document type or use case
2. **Batch Operations**: Always use batch insert for multiple vectors
3. **Payload Size**: Keep payloads small (<1KB), store full text elsewhere if needed
4. **Field Indexing**: Index frequently filtered fields
5. **Distance Metric**: Use Cosine for normalized embeddings, Dot for raw scores
6. **Backup**: Regular snapshots of collections
7. **Monitoring**: Track latency, memory usage, and collection growth

## Troubleshooting

**Issue**: Slow search performance
**Solution**: Increase `hnsw_ef` parameter, add more RAM, optimize payload size

**Issue**: Out of memory errors
**Solution**: Enable disk storage, reduce `m` parameter, archive old data

**Issue**: Low recall (missing relevant results)
**Solution**: Increase `ef_construct` during indexing, increase `hnsw_ef` during search

**Issue**: Connection refused
**Solution**: Verify Qdrant is running (`docker ps`), check host/port config

**Issue**: Collection already exists error
**Solution**: Delete existing collection or use different name

## Comparison with Alternatives

| Vector DB | Performance | Features | Scalability | Ease of Use |
|-----------|-------------|----------|-------------|-------------|
| **Qdrant** | ⚡ Excellent | ✅ Rich | ✅ Good | ✅ Easy |
| Pinecone | ⚡ Excellent | ✅ Rich | ✅ Excellent | ✅ Easy (Cloud) |
| Weaviate | ⚡ Good | ✅ Very Rich | ✅ Good | ⚠️ Complex |
| Chroma | ⚠️ Fair | ⚠️ Basic | ⚠️ Limited | ✅ Very Easy |
| Milvus | ⚡ Excellent | ✅ Rich | ✅ Excellent | ⚠️ Complex |

## See Also

- [Memory Store](../memory/README.md) - Session memory storage
- [Database Tools Overview](../README.md) - All database tools
- [RAG Pipeline](../../../docs/rag/README.md) - How vector store fits in RAG
- [Qdrant Documentation](https://qdrant.tech/documentation/)
