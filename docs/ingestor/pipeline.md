# Ingestion Pipeline

How PDFs are processed and stored in the vector database.

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

## Step 1: Parse PDF

**Tool:** Docling (via `ParserSelector`)

```python
from tools.llm.parser.selector import ParserSelector

parser = ParserSelector.create(provider="docling")
parsed = parser.parse("paper.pdf")
```

**Output:**
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

**Why Docling?**
- Handles complex layouts (multi-column, tables, equations)
- Better for academic papers
- Trade-off: Slower than simple parsers

---

## Step 2: Chunk Text

**Tool:** LangChain RecursiveCharacterTextSplitter

```python
from tools.llm.chunking.selector import TextChunkerSelector

chunker = TextChunkerSelector.create(
    provider="langchain",
    chunk_size=1000,
    chunk_overlap=200
)

chunks = chunker.chunk(parsed.text)
```

**Output:**
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

**Chunk Settings:**
- **Size: 1000 tokens** - Captures full paragraphs
- **Overlap: 200 tokens** - Prevents splitting mid-concept
- **20% overlap** - Maintains context between chunks

---

## Step 3: Generate Embeddings

**Tool:** LiteLLM (OpenAI text-embedding-3-small)

```python
from tools.llm.client.selector import LLMClientSelector

llm = LLMClientSelector.create(
    provider="litellm",
    embedding_model="text-embedding-3-small"
)

# Batch embedding generation
embeddings = llm.embed_batch(
    texts=[chunk['text'] for chunk in chunks],
    batch_size=100
)
```

**Output:**
```python
# List of 1536-dimensional vectors
[
    [0.123, -0.456, 0.789, ...],  # 1536 dimensions
    [0.321, 0.654, -0.987, ...],
    # ...
]
```

**Batch Size: 100**
- Reduces API calls (100 chunks = 1 call)
- Balances throughput vs rate limits

---

## Step 4: Store Vectors

**Tool:** Qdrant

```python
from tools.database.vector.selector import VectorStoreSelector

vector_store = VectorStoreSelector.create(
    provider="qdrant",
    collection_name="pdf_documents"
)

# Store vectors with metadata
vector_store.add_embeddings(
    embeddings=embeddings,
    texts=[chunk['text'] for chunk in chunks],
    metadatas=[chunk['metadata'] for chunk in chunks]
)
```

**Metadata Structure:**
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

---

## Skip Logic

The pipeline checks if data already exists:

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

## Full Example

```python
from ingestor.processor import IngestionProcessor

# Initialize
processor = IngestionProcessor()

# For each PDF file
for pdf_path in pdf_files:
    # 1. Parse
    parsed = parser.parse(pdf_path)

    # 2. Chunk
    chunks = chunker.chunk(parsed.text)

    # 3. Embed
    embeddings = llm.embed_batch([c['text'] for c in chunks])

    # 4. Store
    vector_store.add_embeddings(
        embeddings=embeddings,
        texts=[c['text'] for c in chunks],
        metadatas=[c['metadata'] for c in chunks]
    )
```

---

## Output Example

```
Vector store currently has 0 vectors
Starting ingestion from: data/pdfs/papers
Found 3 .pdf files to process

Processing file 1/3: paper1.pdf
[1/4] Parsing paper1.pdf → 12 pages
[2/4] Chunking text → 45 chunks
[3/4] Generating embeddings → 45 embeddings
[4/4] Storing vectors → ✓

Processing file 2/3: paper2.pdf
[1/4] Parsing paper2.pdf → 8 pages
[2/4] Chunking text → 28 chunks
[3/4] Generating embeddings → 28 embeddings
[4/4] Storing vectors → ✓

Processing file 3/3: paper3.pdf
[1/4] Parsing paper3.pdf → 15 pages
[2/4] Chunking text → 55 chunks
[3/4] Generating embeddings → 55 embeddings
[4/4] Storing vectors → ✓

Ingestion Summary:
  Files processed: 3
  Successful: 3
  Total chunks: 128
  Total vectors: 128
```

---

## See Also

- [Components](./components.md) - Deep dive on each component
- [Usage](./usage.md) - Programmatic usage examples
- [Ingestion Module](./README.md) - Back to overview
