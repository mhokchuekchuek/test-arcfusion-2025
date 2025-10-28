# Docling PDF Parser API Reference

PDF parsing implementation using IBM's Docling library with modern layout analysis and table extraction.

## Class Definition

```python
from tools.llm.parser.docling.main import PDFParser

class PDFParser(BasePDFParser):
    """PDF parser implementation using Docling library.

    Docling provides modern PDF parsing with layout analysis,
    table extraction, and metadata handling.
    """
```

**File**: `tools/llm/parser/docling/main.py`

## Constructor

### `__init__(**kwargs)`

Initialize Docling PDF parser.

```python
parser = PDFParser()
```

#### Parameters

- `**kwargs` (optional): Additional configuration for Docling DocumentConverter
  - All Docling-specific configuration options

#### Example

```python
from tools.llm.parser.selector import ParserSelector

parser = ParserSelector.create(provider="docling")
```

## Methods

### `parse(pdf_path: str, **kwargs) -> dict[str, Any]`

Parse PDF file and extract content with metadata.

#### Parameters

- `pdf_path` (str): Path to the PDF file
- `**kwargs` (optional): Additional parser-specific parameters

#### Returns

Dictionary containing:
- `text` (str): Extracted text content (all pages combined, in Markdown format)
- `metadata` (dict): File metadata including:
  - `filename` (str): Name of the PDF file
  - `filepath` (str): Absolute path to PDF
  - `file_size` (int): File size in bytes
  - `num_pages` (int): Number of pages
  - `title` (str, optional): Document title if available
  - `author` (str, optional): Document author if available
- `pages` (list): List of page-wise content dictionaries

#### Raises

- `FileNotFoundError`: If PDF file doesn't exist
- `ValueError`: If file is not a PDF or is corrupted

#### Example

```python
from tools.llm.parser.selector import ParserSelector

parser = ParserSelector.create(provider="docling")
result = parser.parse("research_paper.pdf")

print(f"Extracted {len(result['text'])} characters")
print(f"Document has {result['metadata']['num_pages']} pages")
print(f"Title: {result['metadata'].get('title', 'N/A')}")
```

### `parse_pages(pdf_path: str, **kwargs) -> list[dict]`

Parse PDF and return page-by-page content.

#### Parameters

- `pdf_path` (str): Path to the PDF file
- `**kwargs` (optional): Additional parser-specific parameters

#### Returns

List of dictionaries, one per page:
- `page_number` (int): Page number (1-indexed)
- `text` (str): Text content of the page
- `metadata` (dict): Page-specific metadata

#### Example

```python
pages = parser.parse_pages("research_paper.pdf")
for page in pages:
    print(f"Page {page['page_number']}: {len(page['text'])} chars")
```

## Configuration

### Environment Variables

No specific environment variables required. API keys not needed (local processing).

### Dependencies

- `docling`: IBM Docling PDF parsing library
  ```bash
  pip install docling
  ```

## Usage Patterns

### Basic PDF Parsing

```python
from tools.llm.parser.selector import ParserSelector

# Create parser
parser = ParserSelector.create(provider="docling")

# Parse PDF
result = parser.parse("document.pdf")

# Access content
full_text = result["text"]
metadata = result["metadata"]
```

### Integration with Ingestion Pipeline

```python
from tools.llm.parser.selector import ParserSelector
from tools.llm.chunking.selector import TextChunkerSelector

# Parse PDF
parser = ParserSelector.create(provider="docling")
parsed = parser.parse("paper.pdf")

# Chunk text
chunker = TextChunkerSelector.create(
    provider="recursive",
    chunk_size=1000,
    chunk_overlap=200
)
chunks = chunker.split(
    text=parsed["text"],
    metadata=parsed["metadata"]
)
```

## Features

### Supported Content

- ✅ Text extraction with layout preservation
- ✅ Table detection and extraction
- ✅ Metadata extraction (title, author)
- ✅ Page-by-page parsing
- ✅ Markdown export format

### Limitations

- PDF must be text-based (not scanned images)
- Complex layouts may have minor formatting issues
- Processing speed: ~5-30 seconds per document depending on size

---

## See Also

- [Parser Selector](../../parser/selector.py) - Factory for creating parser instances
- [Base PDF Parser](../../parser/base.py) - Abstract base class
- [Docling Documentation](https://github.com/DS4SD/docling) - Official Docling docs
- [Ingestion Pipeline](../../../../../ingestor/README.md) - PDF ingestion workflow
