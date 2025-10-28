# Ingestion Usage

Programmatic usage examples for the ingestion pipeline.

---

## Basic Usage

### Process All PDFs

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

**Output:**
```
✓ paper1.pdf: 45 chunks
✓ paper2.pdf: 28 chunks
✓ paper3.pdf: 55 chunks
```

---

## Single File Processing

### Process Specific File

```python
from ingestor.processor import IngestionProcessor

processor = IngestionProcessor()

# Process specific file
result = processor.process_file("./pdfs/paper.pdf")

print(f"Pages: {result['num_pages']}")
print(f"Chunks: {result['num_chunks']}")
print(f"Success: {result['success']}")
```

**Output:**
```python
{
    'filename': 'paper.pdf',
    'success': True,
    'num_pages': 12,
    'num_chunks': 45
}
```

---

## Custom Configuration

### Override Default Settings

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

### Custom Components

```python
from ingestor.processor import IngestionProcessor
from tools.llm.parser.selector import ParserSelector
from tools.llm.chunking.selector import TextChunkerSelector

# Create custom parser
parser = ParserSelector.create(provider="docling")

# Create custom chunker
chunker = TextChunkerSelector.create(
    provider="langchain",
    chunk_size=800,
    chunk_overlap=150
)

# Use with processor
processor = IngestionProcessor(
    parser=parser,
    chunker=chunker
)

results = processor.process()
```

---

## Error Handling

### Graceful Failure

Each file is processed independently:

```python
results = processor.process()

successful = [r for r in results if r['success']]
failed = [r for r in results if not r['success']]

print(f"Processed: {len(successful)}/{len(results)}")

for failure in failed:
    print(f"Failed: {failure['filename']}")
    print(f"  Error: {failure['error']}")
```

**Output:**
```
Processed: 2/3
Failed: corrupted.pdf
  Error: Unable to parse PDF: Invalid file format
```

### Retry Logic

```python
from ingestor.processor import IngestionProcessor

processor = IngestionProcessor()

for pdf_file in pdf_files:
    try:
        result = processor.process_file(pdf_file)
        print(f"✓ {pdf_file}")
    except Exception as e:
        print(f"✗ {pdf_file}: {e}")
        # Optionally retry or log
```

---

## Skip Logic

### Check Existing Data

```python
from tools.database.vector.selector import VectorStoreSelector

vector_store = VectorStoreSelector.create(
    provider="qdrant",
    collection_name="pdf_documents"
)

# Check vector count
count = vector_store.count()

if count > 0:
    print(f"Vector store has {count} vectors - skipping ingestion")
    exit()

# Proceed with ingestion
processor = IngestionProcessor()
results = processor.process()
```

### Force Re-ingestion

```python
from tools.database.vector.selector import VectorStoreSelector

vector_store = VectorStoreSelector.create(provider="qdrant")

# Clear existing data
vector_store.delete_collection()
vector_store.create_collection()

# Re-ingest
processor = IngestionProcessor()
results = processor.process()
```

---

## Batch Processing

### Process in Batches

```python
from ingestor.processor import IngestionProcessor
import os

processor = IngestionProcessor()

# Get all PDFs
pdf_dir = "data/pdfs/papers"
pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

# Process in batches of 10
batch_size = 10
for i in range(0, len(pdf_files), batch_size):
    batch = pdf_files[i:i+batch_size]
    print(f"Processing batch {i//batch_size + 1}/{len(pdf_files)//batch_size + 1}")

    for pdf_file in batch:
        result = processor.process_file(os.path.join(pdf_dir, pdf_file))
        print(f"  {pdf_file}: {result['num_chunks']} chunks")
```

---

## Component-Level Usage

### Use Components Individually

```python
from tools.llm.parser.selector import ParserSelector
from tools.llm.chunking.selector import TextChunkerSelector
from tools.llm.client.selector import LLMClientSelector
from tools.database.vector.selector import VectorStoreSelector

# 1. Parse PDF
parser = ParserSelector.create(provider="docling")
parsed = parser.parse("paper.pdf")

# 2. Chunk text
chunker = TextChunkerSelector.create(
    provider="langchain",
    chunk_size=1000,
    chunk_overlap=200
)
chunks = chunker.chunk(parsed.text)

# 3. Generate embeddings
llm = LLMClientSelector.create(provider="litellm")
embeddings = llm.embed_batch(
    texts=[c['text'] for c in chunks],
    batch_size=100
)

# 4. Store vectors
vector_store = VectorStoreSelector.create(provider="qdrant")
vector_store.add_embeddings(
    embeddings=embeddings,
    texts=[c['text'] for c in chunks],
    metadatas=[c['metadata'] for c in chunks]
)
```

---

## Monitoring Progress

### Track Progress

```python
from ingestor.processor import IngestionProcessor
import os

processor = IngestionProcessor()

pdf_dir = "data/pdfs/papers"
pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

print(f"Found {len(pdf_files)} PDF files")

total_chunks = 0
for i, pdf_file in enumerate(pdf_files, 1):
    print(f"\nProcessing file {i}/{len(pdf_files)}: {pdf_file}")

    result = processor.process_file(os.path.join(pdf_dir, pdf_file))

    if result['success']:
        print(f"  ✓ {result['num_pages']} pages → {result['num_chunks']} chunks")
        total_chunks += result['num_chunks']
    else:
        print(f"  ✗ Error: {result['error']}")

print(f"\n=== Summary ===")
print(f"Total chunks: {total_chunks}")
```

**Output:**
```
Found 3 PDF files

Processing file 1/3: paper1.pdf
  ✓ 12 pages → 45 chunks

Processing file 2/3: paper2.pdf
  ✓ 8 pages → 28 chunks

Processing file 3/3: paper3.pdf
  ✓ 15 pages → 55 chunks

=== Summary ===
Total chunks: 128
```

---

## CLI Usage

### Using the Script

```bash
# Run ingestion script
python scripts/ingest.py

# Output
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

## Testing

### Test Full Pipeline

```python
def test_ingestion_pipeline():
    """Test full ingestion pipeline."""
    processor = IngestionProcessor(
        directory="./test_pdfs",
        chunk_size=500
    )

    results = processor.process()

    assert len(results) > 0
    assert all(r['success'] for r in results)
    assert sum(r['num_chunks'] for r in results) > 0
```

### Test Single File

```python
def test_single_file_ingestion():
    """Test processing single PDF."""
    processor = IngestionProcessor()

    result = processor.process_file("test.pdf")

    assert result['success'] is True
    assert result['num_pages'] > 0
    assert result['num_chunks'] > 0
```

### Test Skip Logic

```python
def test_skip_existing_data():
    """Test skip logic when data exists."""
    processor = IngestionProcessor()

    # First run
    results1 = processor.process()
    count1 = sum(r['num_chunks'] for r in results1)

    # Second run (should skip)
    results2 = processor.process()
    count2 = sum(r['num_chunks'] for r in results2)

    assert count1 > 0
    assert count2 == 0  # Skipped
```

---

## See Also

- [Pipeline](./pipeline.md) - How the pipeline works
- [Components](./components.md) - Deep dive on each component
- [Ingestion Module](./README.md) - Back to overview
