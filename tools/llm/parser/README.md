# Document Parser Tools

## Purpose

Extract text and structured content from PDF documents for ingestion into the RAG system. The parser tools handle complex document layouts including academic papers, tables, equations, and multi-column formats.

## Available Providers

### Docling

**Provider**: `docling`

**Description**: Advanced PDF parser specifically designed for academic and technical documents with complex layouts.

**Key Features**:
- **Table extraction**: Preserves table structure and formatting
- **Equation handling**: Extracts mathematical equations (LaTeX when possible)
- **Multi-column layouts**: Correctly handles academic paper formats
- **Section detection**: Identifies document structure (headings, paragraphs)
- **Metadata extraction**: Page numbers, sections, document properties
- **High accuracy**: Better than traditional PDF parsers for complex documents

**Output Format**: Markdown text with preserved structure

**Why Docling Was Chosen**:
- Superior handling of academic PDFs compared to PyPDF2, pdfplumber
- Maintains semantic structure (important for chunking)
- Handles edge cases like rotated pages, embedded images
- Active development and maintenance

## Usage Examples

### Basic PDF Parsing

```python
from tools.llm.parser.selector import ParserSelector

parser = ParserSelector.create(provider="docling")

# Parse PDF to markdown
document_text = parser.parse("research_paper.pdf")
print(document_text)
```

### With Metadata

```python
parser = ParserSelector.create(provider="docling")

# Get structured output with metadata
result = parser.parse_with_metadata("document.pdf")

print(f"Title: {result['metadata']['title']}")
print(f"Pages: {result['metadata']['pages']}")
print(f"Content:\n{result['text']}")
```

### Batch Processing

```python
from pathlib import Path

parser = ParserSelector.create(provider="docling")
pdf_dir = Path("./documents")

for pdf_file in pdf_dir.glob("*.pdf"):
    try:
        text = parser.parse(str(pdf_file))
        output_file = pdf_file.with_suffix(".md")
        output_file.write_text(text)
        print(f"Processed: {pdf_file.name}")
    except Exception as e:
        print(f"Failed to parse {pdf_file.name}: {e}")
```

## Configuration

### Environment Variables

```bash
# Parser provider selection
PARSER_PROVIDER=docling

# Optional: Parser-specific settings
PARSER_TIMEOUT=300  # Timeout in seconds for large PDFs
```

### Advanced Options

```python
parser = ParserSelector.create(
    provider="docling",
    timeout=300,  # Max processing time
    extract_images=False,  # Skip image extraction
    preserve_layout=True  # Maintain visual layout
)
```

## Base Interface

All parser providers implement the `BaseParser` interface:

```python
from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Parse document and return text content."""
        pass

    @abstractmethod
    def parse_with_metadata(self, file_path: str) -> dict:
        """Parse document and return text with metadata."""
        pass
```

## Integration Points

The parser is primarily used by:

- **`ingestor/`**: Main ingestion pipeline
  - Converts PDFs to markdown
  - Extracts text for chunking
  - Processes uploaded documents

- **`scripts/`**: Batch processing scripts
  - Bulk document conversion
  - Data preparation

## Output Format

### Markdown Structure

Docling outputs clean markdown with preserved structure:

```markdown
# Document Title

## Section 1: Introduction

This is the introduction paragraph...

## Section 2: Methods

### 2.1 Methodology

Description of methods...

| Parameter | Value | Unit |
|-----------|-------|------|
| Temperature | 298 | K |
| Pressure | 1.0 | atm |

### 2.2 Equations

The Einstein equation is: E = mc²

## Section 3: Results

...
```

### Metadata Structure

```python
{
    "text": "Full document text in markdown...",
    "metadata": {
        "title": "Document Title",
        "pages": 15,
        "sections": ["Introduction", "Methods", "Results"],
        "file_path": "/path/to/document.pdf",
        "processed_at": "2024-01-15T10:30:00Z"
    }
}
```

## Best Practices

1. **Validate Input**: Check PDF exists and is readable before parsing
2. **Error Handling**: Wrap parse calls in try/except for corrupted PDFs
3. **Timeout Management**: Set appropriate timeout for large documents
4. **Output Validation**: Verify parsed text is not empty
5. **Encoding**: Always use UTF-8 for markdown output
6. **Cleanup**: Remove temporary files created during parsing

## Performance Considerations

**Processing Time**:
- Small PDFs (< 10 pages): 1-3 seconds
- Medium PDFs (10-50 pages): 5-15 seconds
- Large PDFs (> 50 pages): 20+ seconds

**Memory Usage**:
- Docling loads entire PDF into memory
- Estimate ~50-100MB per document being processed
- For batch processing, use sequential processing or limit concurrency

**Optimization Tips**:
```python
# Process multiple PDFs with controlled concurrency
from concurrent.futures import ThreadPoolExecutor, as_completed

parser = ParserSelector.create(provider="docling")
pdf_files = list(Path("docs").glob("*.pdf"))

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {
        executor.submit(parser.parse, str(pdf)): pdf
        for pdf in pdf_files
    }

    for future in as_completed(futures):
        pdf = futures[future]
        try:
            text = future.result()
            print(f"Completed: {pdf.name}")
        except Exception as e:
            print(f"Failed: {pdf.name} - {e}")
```

## Handling Edge Cases

### Password-Protected PDFs

```python
try:
    text = parser.parse("protected.pdf")
except Exception as e:
    if "password" in str(e).lower():
        print("PDF is password-protected")
        # Handle password-protected case
```

### Corrupted PDFs

```python
try:
    text = parser.parse("document.pdf")
    if not text or len(text) < 100:
        print("Warning: Suspiciously short output")
except Exception as e:
    print(f"Parsing failed: {e}")
    # Try alternative parser or skip
```

### Non-Text PDFs (Scanned Images)

```python
text = parser.parse("scanned.pdf")
if "OCR required" in text or len(text) < 50:
    print("Document appears to be scanned - OCR needed")
    # Use OCR tool or reject document
```

## Troubleshooting

**Issue**: Parser timeout on large PDFs
**Solution**: Increase timeout parameter or split PDF into smaller chunks

**Issue**: Garbled text output
**Solution**: PDF may have encoding issues - try re-exporting PDF with standard fonts

**Issue**: Missing table content
**Solution**: Some table formats may not be detected - verify PDF structure

**Issue**: Empty output
**Solution**: Check if PDF is valid, not password-protected, and not purely images

**Issue**: Import error for Docling
**Solution**: Install dependencies: `pip install docling`

## Comparison with Alternatives

| Parser | Tables | Equations | Layout | Speed | Use Case |
|--------|--------|-----------|--------|-------|----------|
| **Docling** | ✅ Excellent | ✅ Good | ✅ Excellent | Medium | Academic PDFs, complex layouts |
| PyPDF2 | ❌ Poor | ❌ Poor | ❌ Poor | Fast | Simple text extraction |
| pdfplumber | ⚠️ Good | ❌ Poor | ⚠️ Good | Medium | Tables, simple layouts |
| PDFMiner | ⚠️ Fair | ❌ Poor | ⚠️ Fair | Slow | Low-level PDF analysis |
| Unstructured | ⚠️ Good | ⚠️ Fair | ⚠️ Good | Slow | Multi-format support |

## Future Enhancements

Potential improvements to parser functionality:

- **OCR Support**: Add tesseract integration for scanned PDFs
- **Image Extraction**: Extract and process embedded images
- **Multi-Format**: Support DOCX, HTML, and other formats
- **Citation Extraction**: Parse bibliography and citations
- **Language Detection**: Auto-detect document language
- **Quality Scoring**: Assess parse quality automatically

## See Also

- [Chunking Tools](../chunking/README.md) - Text chunking after parsing
- [Ingestion Pipeline](../../../docs/ingestor.md) - How parsing fits in ingestion
- [Tool Provider Pattern](../../../docs/architecture/tool-provider-pattern.md)
