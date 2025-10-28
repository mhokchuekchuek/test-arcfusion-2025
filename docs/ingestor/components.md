# Ingestion Components

Deep dive into each component of the ingestion pipeline.

---

## 1. PDF Parser (Docling)

**Location**: `tools/llm/parser/`

Extracts text and metadata from PDF documents.

### Usage

```python
from tools.llm.parser.selector import ParserSelector

parser = ParserSelector.create(provider="docling")

# Parse PDF
result = parser.parse("paper.pdf")

print(result.text)      # Extracted text
print(result.metadata)  # Page numbers, title, authors
```

### Output Format

```python
{
    'text': "Full paper text...",
    'metadata': {
        'pages': 12,
        'title': "Paper Title",
        'authors': ["Author 1", "Author 2"]
    }
}
```

### Why Docling?

- Handles complex layouts (multi-column, tables, equations)
- Better for academic papers than simple text extraction
- Trade-off: Slower than basic parsers

### Configuration

`configs/ingestor/ingestion.yaml`:

```yaml
parser:
  provider: docling
```

---

## 2. Text Chunker (LangChain)

**Location**: `tools/llm/chunking/`

Splits text into overlapping chunks for embedding.

### Usage

```python
from tools.llm.chunking.selector import TextChunkerSelector

chunker = TextChunkerSelector.create(
    provider="langchain",
    chunk_size=1000,
    chunk_overlap=200
)

# Chunk text
chunks = chunker.chunk(text)

print(f"Created {len(chunks)} chunks")
```

### Output Format

```python
[
    {
        'text': "Chunk text...",
        'metadata': {
            'source': 'paper.pdf',
            'page': 1,
            'chunk_index': 0
        }
    },
    # ... more chunks
]
```

### Chunk Settings

| Setting | Value | Rationale |
|---------|-------|-----------|
| **chunk_size** | 1000 tokens | Captures full paragraphs |
| **chunk_overlap** | 200 tokens | Prevents splitting mid-concept |
| **overlap %** | 20% | Maintains context between chunks |

### Configuration

`configs/ingestor/ingestion.yaml`:

```yaml
ingestion:
  chunk_size: 512        # Characters per chunk
  chunk_overlap: 50      # Character overlap
```

---

## 3. Embedding Generator (LiteLLM)

**Location**: `tools/llm/client/`

Generates vector embeddings for text chunks.

### Usage

```python
from tools.llm.client.selector import LLMClientSelector

llm = LLMClientSelector.create(
    provider="litellm",
    embedding_model="text-embedding-3-small"
)

# Generate embeddings (batched)
embeddings = llm.embed_batch(
    texts=[chunk['text'] for chunk in chunks],
    batch_size=100
)

print(f"Generated {len(embeddings)} embeddings")
```

### Output Format

```python
# List of 1536-dimensional vectors
[
    [0.123, -0.456, 0.789, ...],  # 1536 dimensions
    [0.321, 0.654, -0.987, ...],
    # ...
]
```

### Batch Processing

**Batch Size: 100**
- Reduces API calls (100 chunks = 1 call)
- Balances throughput vs rate limits
- Configured in `configs/ingestor/ingestion.yaml`

### Configuration

`configs/ingestor/ingestion.yaml`:

```yaml
ingestion:
  batch_size: 32  # Embeddings per batch

  llm:
    provider: litellm
    proxy_url: http://localhost:4000
    embedding_model: text-embedding-3-small
```

### Model Details

- **Model**: text-embedding-3-small
- **Dimensions**: 1536
- **Provider**: OpenAI (via LiteLLM proxy)

---

## 4. Vector Store (Qdrant)

**Location**: `tools/database/vector/`

Stores embeddings with metadata for semantic search.

### Usage

```python
from tools.database.vector.selector import VectorStoreSelector

vector_store = VectorStoreSelector.create(
    provider="qdrant",
    collection_name="pdf_documents"
)

# Store vectors
vector_store.add_embeddings(
    embeddings=embeddings,
    texts=[chunk['text'] for chunk in chunks],
    metadatas=[chunk['metadata'] for chunk in chunks]
)
```

### Metadata Structure

Each vector is stored with metadata:

```python
{
    'text': "The actual chunk text for reconstruction",
    'source': "paper.pdf",
    'page': 1,
    'chunk_index': 0,
    'title': "Paper Title",
    'authors': ["Author 1"]
}
```

### Collection Management

**Check if data exists:**

```python
count = vector_store.count()

if count > 0:
    print(f"Vector store has {count} vectors")
```

**Clear collection:**

```python
vector_store.delete_collection()
vector_store.create_collection()
```

### Configuration

`configs/ingestor/ingestion.yaml`:

```yaml
ingestion:
  vectordb:
    provider: qdrant
    host: localhost
    port: 6333
    collection_name: pdf_documents
```

---

## Component Flow

```
PDF File
    ↓
Parser (Docling)
    ↓ text + metadata
Chunker (LangChain)
    ↓ chunks with metadata
Embedding Generator (LiteLLM)
    ↓ vectors (1536-dim)
Vector Store (Qdrant)
    ↓
Searchable Knowledge Base
```

---

## Testing Components

### Test Parser

```python
def test_parser():
    parser = ParserSelector.create(provider="docling")
    result = parser.parse("test.pdf")

    assert len(result.text) > 0
    assert result.metadata['pages'] > 0
```

### Test Chunker

```python
def test_chunker():
    chunker = TextChunkerSelector.create(
        provider="langchain",
        chunk_size=500
    )

    chunks = chunker.chunk("Long text...")

    assert len(chunks) > 0
    assert all('text' in c for c in chunks)
```

### Test Embedding Generator

```python
def test_embeddings():
    llm = LLMClientSelector.create(provider="litellm")

    embeddings = llm.embed_batch(["text1", "text2"])

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 1536  # Dimension check
```

### Test Vector Store

```python
def test_vector_store():
    store = VectorStoreSelector.create(provider="qdrant")

    store.add_embeddings(
        embeddings=[[0.1] * 1536],
        texts=["test"],
        metadatas=[{"source": "test.pdf"}]
    )

    count = store.count()
    assert count > 0
```

---

## See Also

- [Pipeline](./pipeline.md) - How components work together
- [Usage](./usage.md) - Programmatic usage examples
- [Ingestion Module](./README.md) - Back to overview
