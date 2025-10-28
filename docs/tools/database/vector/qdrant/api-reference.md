# Qdrant Vector Store API Reference

Semantic similarity search with high-performance vector database.

**Location**: `tools/database/vector/qdrant/main.py`

---

## Class Definition

```python
class VectorStoreClient(BaseVectorStore):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "pdf_documents",
        vector_size: int = 1536,
        distance: str = "Cosine",
        create_collection: bool = True
    )
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | str | `localhost` | Qdrant server host |
| `port` | int | 6333 | Qdrant REST API port |
| `collection_name` | str | `pdf_documents` | Collection name |
| `vector_size` | int | 1536 | Embedding dimension |
| `distance` | str | `Cosine` | Distance metric (Cosine/Euclid/Dot) |
| `create_collection` | bool | True | Auto-create collection |

### Quick Start

```python
from tools.database.vector.selector import VectorStoreSelector

vector_store = VectorStoreSelector.create(
    provider="qdrant",
    host="localhost",
    port=6333,
    collection_name="documents",
    vector_size=1536
)
```

---

## Methods

### add()

Store embeddings with metadata.

```python
def add(
    self,
    embeddings: list[list[float]],
    metadata: list[dict],
    ids: Optional[list[str]] = None
) -> None
```

**Example:**
```python
embeddings = [[0.1, 0.2, ...], [0.3, 0.4, ...]]
metadata = [
    {"text": "First chunk", "source": "doc.pdf", "page": 1},
    {"text": "Second chunk", "source": "doc.pdf", "page": 2}
]

vector_store.add(embeddings=embeddings, metadata=metadata)
```

---

### search()

Find similar vectors by semantic similarity.

```python
def search(
    self,
    query_embedding: list[float],
    k: int = 5,
    filter: Optional[dict] = None
) -> list[dict]
```

**Returns:** List of `{"id": str, "score": float, "metadata": dict}`

**Example:**
```python
# Generate query embedding
llm = LLMClientSelector.create(provider="litellm")
query_emb = llm.embed(["What is RAG?"])[0]

# Search
results = vector_store.search(
    query_embedding=query_emb,
    k=5,
    filter={"source": "paper.pdf"}
)

# Use results
for r in results:
    print(f"{r['score']:.2f}: {r['metadata']['text'][:50]}...")
```

---

### count()

Get vector count in collection.

```python
def count(self) -> int
```

---

### delete()

Remove vectors by ID.

```python
def delete(self, ids: list[str]) -> None
```

---

### clear()

Remove all vectors from collection.

```python
def clear(self) -> None
```

---

## Configuration

```bash
# Environment variables
QDRANT_HOST=localhost
QDRANT_PORT=6333
VECTOR_COLLECTION_NAME=pdf_documents
VECTOR_SIZE=1536
```

### Docker Setup

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
```

---

## Common Use Cases

### RAG Retrieval

```python
# Search for relevant documents
llm = LLMClientSelector.create(provider="litellm")
vector_store = VectorStoreSelector.create(provider="qdrant")

query_emb = llm.embed(["What is RAG?"])[0]
results = vector_store.search(query_emb, k=5)

# Build context
context = "\n\n".join([r['metadata']['text'] for r in results])
```

### Document Ingestion

```python
# Embed and store documents
texts = ["chunk 1", "chunk 2", "chunk 3"]
embeddings = llm.embed(texts)
metadata = [{"text": t, "source": "doc.pdf"} for t in texts]

vector_store.add(embeddings=embeddings, metadata=metadata)
```

---

## Key Features

### Distance Metrics

| Metric | Best For | Score Range |
|--------|----------|-------------|
| Cosine | LLM embeddings (normalized) | 0.0-1.0 |
| Euclid | Absolute distance | 0.0-∞ |
| Dot | Non-normalized vectors | -∞ to +∞ |

### Metadata Filtering

```python
# Filter by source
results = vector_store.search(
    query_embedding=emb,
    k=5,
    filter={"source": "paper.pdf"}
)
```

---

## See Also

- [Database Tools](../../README.md)
- [Vector Store Selector](../../selector.py)
- [Qdrant Docs](https://qdrant.tech/documentation/)
