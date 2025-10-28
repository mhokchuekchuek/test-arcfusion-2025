# PDF Ingestion Module

Automated pipeline for ingesting PDF documents into the vector database.

## Quick Start

**Prerequisites:**
- Python 3.13+ with venv/conda activated
- `pip install -r requirements.txt` completed
- Docker services running (`docker-compose up -d`)

**1. Place your PDF files:**
```bash
# Create directory if it doesn't exist
mkdir -p data/pdfs/papers

# Copy your PDFs (default location configured in configs/ingestor/ingestion.yaml)
cp your_paper.pdf data/pdfs/papers/
```

**2. Run ingestion script:**
```bash
# With venv/conda activated
python scripts/ingest.py
```

Output:
```
Vector store currently has 0 vectors
Starting ingestion from: data/pdfs/papers
Found 3 .pdf files to process

Processing file 1/3: paper1.pdf
[1/4] Parsing paper1.pdf → 12 pages
[2/4] Chunking text → 45 chunks
[3/4] Generating embeddings → 45 embeddings
[4/4] Storing vectors → ✓

Ingestion Summary:
  Files processed: 3
  Successful: 3
  Total chunks: 128
  Total vectors: 128
```

---

## Pipeline Overview

```
PDF → Parse → Chunk → Embed → Store
```

**Steps:**
1. **Parse** - Docling extracts text + metadata
2. **Chunk** - Split into 1000-token chunks (200 overlap)
3. **Embed** - Generate embeddings (batch size: 100)
4. **Store** - Save to Qdrant with metadata

---

## Configuration

`configs/ingestor/ingestion.yaml`:

```yaml
ingestion:
  directory: data/pdfs/papers    # PDF source directory (place your PDFs here!)
  file_type: pdf                 # File extension
  chunk_size: 512                # Characters per chunk
  chunk_overlap: 50              # Character overlap
  batch_size: 32                 # Embeddings per batch

  llm:
    provider: litellm
    proxy_url: http://localhost:4000        # LiteLLM proxy
    embedding_model: text-embedding-3-small

  vectordb:
    provider: qdrant
    host: localhost              # Qdrant host (uses localhost for local runs)
    port: 6333
    collection_name: pdf_documents
```

**PDF Directory**: The script reads PDFs from `data/pdfs/papers/` by default. Create this directory and place your PDF files there before running ingestion.

---

## Programmatic Usage

### Basic Usage

```python
from ingestor.processor import IngestionProcessor

# Create processor
processor = IngestionProcessor()

# Run ingestion
results = processor.process()

# Check results
for result in results:
    if result['success']:
        print(f"✓ {result['filename']}: {result['num_chunks']} chunks")
    else:
        print(f"✗ {result['filename']}: {result['error']}")
```

---

### Process Single File

```python
from ingestor.processor import IngestionProcessor

processor = IngestionProcessor()

# Process specific file
result = processor.process_file("./pdfs/paper.pdf")

print(f"Pages: {result['num_pages']}")
print(f"Chunks: {result['num_chunks']}")
print(f"Success: {result['success']}")
```

---

### Custom Configuration

```python
from ingestor.processor import IngestionProcessor

# Custom settings
processor = IngestionProcessor(
    directory="./custom_pdfs",
    chunk_size=500,
    chunk_overlap=100,
    batch_size=50
)

results = processor.process()
```

---

## Components

### 1. PDF Parser (Docling)

```python
from tools.llm.parser.selector import ParserSelector

parser = ParserSelector.create(provider="docling")

# Parse PDF
result = parser.parse("paper.pdf")

print(result.text)      # Extracted text
print(result.metadata)  # Page numbers, etc.
```

**Why Docling?**
- Handles complex layouts (multi-column, tables, equations)
- Better for academic papers
- Trade-off: Slower than simple parsers

---

### 2. Text Chunker (LangChain)

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

**Chunk Settings:**
- **Size: 1000 tokens** - Captures full paragraphs
- **Overlap: 200 tokens** - Prevents splitting mid-concept
- **20% overlap** - Maintains context

---

### 3. Embedding Generator (LiteLLM)

```python
from tools.llm.client.selector import LLMClientSelector

llm = LLMClientSelector.create(
    provider="litellm",
    embedding_model="text-embedding-3-small"
)

# Generate embeddings (batched)
embeddings = llm.embed_batch(
    texts=chunks,
    batch_size=100
)

print(f"Generated {len(embeddings)} embeddings")
```

**Batch Size: 100**
- Reduces API calls (100 chunks = 1 call)
- Balances throughput vs rate limits

---

### 4. Vector Store (Qdrant)

```python
from tools.database.vector.selector import VectorStoreSelector

vector_store = VectorStoreSelector.create(
    provider="qdrant",
    collection_name="documents"
)

# Store vectors
vector_store.add_embeddings(
    embeddings=embeddings,
    texts=chunks,
    metadatas=[
        {"source": "paper.pdf", "page": 1},
        {"source": "paper.pdf", "page": 2},
        # ...
    ]
)
```

---

## Skip Logic

The script checks if data already exists:

```python
# Check vector count
count = vector_store.count()

if count > 0:
    print(f"Vector store has {count} vectors - skipping ingestion")
    exit()

# Proceed with ingestion
```

**Behavior:**
- Any data present → Skip entire ingestion
- Empty collection → Process all PDFs

**To re-ingest:** Clear the collection first:
```python
vector_store.delete_collection()
vector_store.create_collection()
```

---

## Error Handling

Each file is processed independently:

```python
results = []

for pdf_file in pdf_files:
    try:
        result = processor.process_file(pdf_file)
        results.append({
            'filename': pdf_file,
            'success': True,
            'num_chunks': result['num_chunks']
        })
    except Exception as e:
        results.append({
            'filename': pdf_file,
            'success': False,
            'error': str(e)
        })

# One failure doesn't stop the pipeline
```

---

## Processing Steps Detail

### Step 1: Parse PDF

```python
# Docling extracts text and structure
parsed = parser.parse("paper.pdf")

# Result
{
    'text': "Full paper text...",
    'metadata': {
        'pages': 12,
        'title': "Paper Title",
        'authors': ["Author 1", "Author 2"]
    }
}
```

---

### Step 2: Chunk Text

```python
# Split into overlapping chunks
chunks = chunker.chunk(parsed.text)

# Each chunk
{
    'text': "Chunk text...",
    'metadata': {
        'source': 'paper.pdf',
        'page': 1,
        'chunk_index': 0
    }
}
```

---

### Step 3: Generate Embeddings

```python
# Batch embedding generation
embeddings = llm.embed_batch(
    texts=[chunk['text'] for chunk in chunks],
    batch_size=100
)

# Result: List of 1536-dim vectors
# [[0.123, -0.456, ...], [0.789, ...], ...]
```

---

### Step 4: Store Vectors

```python
# Store in Qdrant
vector_store.add_embeddings(
    embeddings=embeddings,
    texts=[chunk['text'] for chunk in chunks],
    metadatas=[chunk['metadata'] for chunk in chunks]
)
```

---

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `Directory not found` | Config path incorrect | Ensure `data/pdfs/papers/` directory exists |
| `No .pdf files found` | Empty directory | Place PDF files in `data/pdfs/papers/` |
| `Failed to parse PDF` | Corrupted/encrypted PDF | Fix source file |
| `Vector store has data` | Collection not empty | Clear collection to re-ingest |
| `Rate limit error` | Too many API calls | Reduce batch_size or add delay |
| `Connection refused` | Services not running | Start Docker services: `docker-compose up -d` |

---

## Provider Pattern

All components are swappable via configuration:

```yaml
# Change any provider without code changes
ingestion:
  llm:
    provider: litellm              # or openai, anthropic
    embedding_model: text-embedding-3-small

  vectordb:
    provider: qdrant               # or pinecone, weaviate

  parser:
    provider: docling              # or pypdf, pdfplumber

  chunker:
    provider: langchain            # or custom
```

Code automatically selects the right implementation:

```python
# Runtime provider selection
parser = ParserSelector.create(provider=config.parser.provider)
vector_store = VectorStoreSelector.create(provider=config.vectordb.provider)
```

---

## Testing

```python
def test_ingestion():
    """Test PDF ingestion pipeline."""
    processor = IngestionProcessor(
        directory="./test_pdfs",
        chunk_size=500
    )

    results = processor.process()

    assert len(results) > 0
    assert all(r['success'] for r in results)
    assert sum(r['num_chunks'] for r in results) > 0


def test_single_file():
    """Test processing single PDF."""
    processor = IngestionProcessor()

    result = processor.process_file("test.pdf")

    assert result['success'] is True
    assert result['num_pages'] > 0
    assert result['num_chunks'] > 0
```

---

## Limitations

- **No deduplication** - Re-ingesting same file creates duplicates
- **Sequential processing** - One file at a time (not parallel)
- **All-or-nothing skip** - Any data present = skip all files
- **In-memory mode** - Qdrant data lost on restart (use persistent mode in production)

---

## Performance Tips

### Large Documents

```yaml
# For large PDFs (100+ pages)
ingestion:
  chunk_size: 500        # Smaller chunks
  batch_size: 50         # Smaller batches
```

---

### Many Small Documents

```yaml
# For many small PDFs
ingestion:
  chunk_size: 2000       # Larger chunks
  batch_size: 200        # Larger batches
```

---

### Rate Limiting

```python
import time

for batch in batches:
    embeddings = llm.embed_batch(batch)
    time.sleep(1)  # Add delay between batches
```

---

## Files

```
ingestor/
└── processor.py           # Main ingestion pipeline

scripts/
└── ingest.py              # CLI runner

configs/ingestor/
└── ingestion.yaml         # Configuration

tools/llm/
├── parser/                # PDF parsing
├── chunking/              # Text chunking
└── client/                # Embedding generation

tools/database/vector/     # Vector storage
```

---

## See Also

- [RAG Strategy](../rag/retrieval-strategy.md) - How retrieved chunks are used
- [Vector Store](../../tools/database/vector/README.md) - Qdrant setup
- [System Overview](../architecture/system-overview.md) - Full system architecture
