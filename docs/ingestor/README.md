# PDF Ingestion Module

Automated pipeline for ingesting PDF documents into the vector database.

---

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

**Output:**
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

**See [Pipeline](./pipeline.md)** for detailed step-by-step breakdown.

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

## Documentation

### [Pipeline](./pipeline.md)
Detailed breakdown of the 4-step ingestion process:
- Step 1: Parse PDF (Docling)
- Step 2: Chunk Text (LangChain)
- Step 3: Generate Embeddings (LiteLLM)
- Step 4: Store Vectors (Qdrant)

### [Components](./components.md)
Deep dive on each component:
- PDF Parser (Docling)
- Text Chunker (LangChain)
- Embedding Generator (LiteLLM)
- Vector Store (Qdrant)

### [Usage](./usage.md)
Programmatic usage examples:
- Basic usage
- Single file processing
- Custom configuration
- Error handling
- Batch processing
- CLI usage

---

## Quick Examples

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

**See [Usage](./usage.md)** for more examples.

---

## Components

| Component | Provider | Purpose |
|-----------|----------|---------|
| **Parser** | Docling | Extract text + metadata from PDFs |
| **Chunker** | LangChain | Split text into overlapping chunks |
| **Embedder** | LiteLLM | Generate 1536-dim vectors |
| **Vector Store** | Qdrant | Store embeddings + metadata |

**See [Components](./components.md)** for detailed documentation.

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
