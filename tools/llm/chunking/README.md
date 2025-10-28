# Text Chunking Tools

## Purpose

Split large documents into smaller, semantically meaningful chunks for embedding generation and retrieval. Proper chunking is critical for RAG system performance - chunks must be small enough to fit in context windows while large enough to maintain semantic coherence.

## Available Providers

### RecursiveCharacterTextSplitter

**Provider**: `recursive`

**Description**: LangChain's recursive text splitter that intelligently splits text while preserving semantic boundaries.

**Key Features**:
- **Hierarchical splitting**: Tries to split on paragraphs, then sentences, then words
- **Configurable chunk size**: Set target chunk size in characters
- **Overlap support**: Maintains context across chunks with configurable overlap
- **Separator customization**: Define custom split delimiters
- **Length function**: Custom length calculation (characters, tokens, etc.)

**Why RecursiveCharacterTextSplitter Was Chosen**:
- Preserves semantic meaning better than naive character splitting
- Battle-tested in production (LangChain standard)
- Configurable for different document types
- Handles edge cases (code, lists, tables)

**Strategy**:
1. Try to split on double newlines (paragraphs)
2. If chunks still too large, split on single newlines
3. If still too large, split on sentences
4. As last resort, split on characters

## Usage Examples

### Basic Chunking

```python
from tools.llm.chunking.selector import TextChunkerSelector

chunker = TextChunkerSelector.create(
    provider="recursive",
    chunk_size=1000,
    chunk_overlap=200
)

# Split document text
document_text = """
Long document content here...
Multiple paragraphs...
"""

chunks = chunker.split(document_text)
print(f"Created {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1} ({len(chunk)} chars): {chunk[:100]}...")
```

### Optimized for Model Context

```python
# For models with 4096 token context, use smaller chunks
chunker = TextChunkerSelector.create(
    provider="recursive",
    chunk_size=512,  # ~600 tokens
    chunk_overlap=100
)

chunks = chunker.split(text)
```

### With Custom Separators

```python
# For code or structured content
chunker = TextChunkerSelector.create(
    provider="recursive",
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n\n", "\n", " ", ""]  # Custom hierarchy
)
```

### Chunking Pipeline

```python
from tools.llm.parser.selector import ParserSelector
from tools.llm.chunking.selector import TextChunkerSelector
from tools.llm.client.selector import LLMClientSelector

# 1. Parse PDF
parser = ParserSelector.create(provider="docling")
text = parser.parse("document.pdf")

# 2. Chunk text
chunker = TextChunkerSelector.create(
    provider="recursive",
    chunk_size=1000,
    chunk_overlap=200
)
chunks = chunker.split(text)

# 3. Generate embeddings
llm = LLMClientSelector.create(provider="litellm", proxy_url="...")
embeddings = llm.embed(chunks)

print(f"Processed {len(chunks)} chunks with {len(embeddings)} embeddings")
```

## Configuration

### Environment Variables

```bash
# Chunking provider
CHUNKER_PROVIDER=recursive

# Chunk parameters
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Chunk Size Guidelines

| Model Context | Chunk Size | Chunk Overlap | Use Case |
|--------------|------------|---------------|----------|
| 4096 tokens | 512 chars | 100 chars | Small context models |
| 8192 tokens | 1000 chars | 200 chars | Standard RAG (default) |
| 16384 tokens | 2000 chars | 400 chars | Large context models |
| 32768+ tokens | 4000 chars | 800 chars | Very large contexts |

**Rule of thumb**: 1 token ≈ 4 characters for English text

## Base Interface

All chunking providers implement the `BaseChunker` interface:

```python
from abc import ABC, abstractmethod

class BaseChunker(ABC):
    @abstractmethod
    def split(self, text: str) -> list[str]:
        """Split text into chunks."""
        pass

    @abstractmethod
    def split_with_metadata(self, text: str) -> list[dict]:
        """Split text into chunks with metadata."""
        pass
```

## Integration Points

The chunker is used by:

- **`ingestor/`**: Document ingestion pipeline
  - Chunks parsed PDFs before embedding
  - Stores chunks in vector database

- **`src/rag/`**: Dynamic query processing
  - Re-chunks retrieved documents if needed
  - Adjusts chunk size based on context window

## Chunking Strategies

### Semantic Chunking

Preserve meaning by splitting on natural boundaries:

```python
chunker = TextChunkerSelector.create(
    provider="recursive",
    chunk_size=1000,
    chunk_overlap=200,
    separators=[
        "\n\n\n",  # Section breaks
        "\n\n",    # Paragraph breaks
        "\n",      # Line breaks
        ". ",      # Sentences
        " ",       # Words
        ""         # Characters
    ]
)
```

### Fixed-Size Chunking

For consistent embedding dimensions:

```python
chunker = TextChunkerSelector.create(
    provider="recursive",
    chunk_size=512,  # Fixed size
    chunk_overlap=0  # No overlap
)
```

### Overlapping Chunks

Maintain context across boundaries:

```python
chunker = TextChunkerSelector.create(
    provider="recursive",
    chunk_size=1000,
    chunk_overlap=300  # 30% overlap
)
```

## Chunk Overlap Explained

Overlap helps preserve context across chunk boundaries:

```
Chunk 1: [The quick brown fox jumps over the lazy]
Chunk 2:                    [fox jumps over the lazy dog near the]
Chunk 3:                                [lazy dog near the river bank]
         |------------ overlap ------------|
```

**Benefits**:
- Prevents loss of context at boundaries
- Improves retrieval recall
- Helps with queries spanning chunk boundaries

**Trade-offs**:
- Increases storage requirements
- More chunks to process during retrieval
- Potential for redundant information

**Recommended**: 15-25% overlap (e.g., 200 chars for 1000 char chunks)

## Best Practices

1. **Test Different Sizes**: Experiment with chunk_size based on your data
2. **Balance Size vs. Granularity**: Larger chunks = more context, but less precise retrieval
3. **Use Overlap**: 15-25% overlap helps maintain context
4. **Consider Token Limits**: Account for model context window and prompt overhead
5. **Validate Chunks**: Check that chunks are semantically coherent
6. **Preserve Structure**: Use appropriate separators for content type
7. **Monitor Performance**: Track retrieval accuracy with different chunk sizes

## Performance Considerations

**Chunking Speed**:
- RecursiveCharacterTextSplitter is fast (pure Python, regex-based)
- Can process ~1MB of text per second
- Negligible overhead in ingestion pipeline

**Memory Usage**:
- Minimal - processes text in single pass
- Output size = input size + overhead from overlap

**Optimization**:
```python
# For very large documents, chunk in batches
def chunk_large_document(text: str, chunker):
    batch_size = 100000  # 100KB batches
    all_chunks = []

    for i in range(0, len(text), batch_size):
        batch = text[i:i+batch_size]
        chunks = chunker.split(batch)
        all_chunks.extend(chunks)

    return all_chunks
```

## Chunk Quality Assessment

### Good Chunk Characteristics

- Self-contained and coherent
- Contains complete thoughts/sentences
- Maintains context from surrounding text
- Appropriate length for embedding model
- Overlaps meaningfully with adjacent chunks

### Poor Chunk Characteristics

- Cuts off mid-sentence
- Too short to provide context
- Too long for model context window
- No semantic coherence
- Arbitrary character splits

### Validation

```python
def validate_chunks(chunks: list[str], min_size=100, max_size=2000):
    issues = []

    for i, chunk in enumerate(chunks):
        # Check size
        if len(chunk) < min_size:
            issues.append(f"Chunk {i} too short: {len(chunk)} chars")
        if len(chunk) > max_size:
            issues.append(f"Chunk {i} too long: {len(chunk)} chars")

        # Check for incomplete sentences
        if chunk and chunk[-1] not in ".!?":
            issues.append(f"Chunk {i} ends mid-sentence")

    return issues
```

## Troubleshooting

**Issue**: Chunks are too large for embedding model
**Solution**: Reduce chunk_size parameter

**Issue**: Retrieval missing relevant information
**Solution**: Increase chunk_overlap to maintain more context

**Issue**: Chunks split mid-sentence
**Solution**: Add ". " to separators list with higher priority

**Issue**: Too many chunks generated (high cost)
**Solution**: Increase chunk_size and reduce overlap

**Issue**: Chunks lack context
**Solution**: Increase chunk_size or chunk_overlap

## Chunking for Different Content Types

### Academic Papers

```python
# Preserve section structure
chunker = TextChunkerSelector.create(
    provider="recursive",
    chunk_size=1500,  # Longer for detailed content
    chunk_overlap=300,
    separators=["\n## ", "\n\n", "\n", ". "]
)
```

### Code Documentation

```python
# Split on code blocks and headings
chunker = TextChunkerSelector.create(
    provider="recursive",
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n```\n", "\n## ", "\n\n", "\n"]
)
```

### Q&A / FAQs

```python
# Keep questions and answers together
chunker = TextChunkerSelector.create(
    provider="recursive",
    chunk_size=500,  # Shorter for Q&A pairs
    chunk_overlap=50,
    separators=["\n\n", "\n"]
)
```

## See Also

- [Parser Tools](../parser/README.md) - Document parsing before chunking
- [LLM Client](../client/README.md) - Embedding generation after chunking
- [Vector Store](../../database/vector/README.md) - Storing chunked embeddings
- [Ingestion Pipeline](../../../docs/ingestor.md) - Full ingestion workflow
