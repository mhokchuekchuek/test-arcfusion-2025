# Retrieval Strategy

Design decisions for chunking, embeddings, and search.

---

## Chunking

| Parameter | Value | Why |
|-----------|-------|-----|
| **Chunk Size** | 1000 tokens | Semantic coherence |
| **Overlap** | 200 tokens | Prevent concept splits |
| **Splitter** | RecursiveCharacterTextSplitter | Preserve structure |

**Example:**
```
Chunk 1: [0 ───── 1000]
Chunk 2:    [800 ───── 1800]  ← 200 overlap
Chunk 3:        [1600 ───── 2600]
```

**Metadata:**
```python
{"text": "...", "source": "paper.pdf", "page": 3}
```
Enables citations: "paper.pdf, p. 3"

---

## Embeddings

**Model**: `text-embedding-3-small`

| Property | Value |
|----------|-------|
| Dimensions | 1536 |
| Context | 8192 tokens |
| Cost | $0.00002/1K tokens |

---

## Retrieval

**Top-K**: Default 5 documents

**Similarity**: Cosine distance

**Performance**:
- Embedding: 50-100ms
- Search: 5-20ms
- Total: 60-150ms

---

## Token Budget

```
Query:      100 tokens
History:   2000 tokens
Context:   5000 tokens (5 × 1000)
Prompt:     500 tokens
──────────────────────
Total:     7600 tokens ✓ Fits in 16K
```

**Strategy**: Limit history to 10 messages, fix K=5

---

## Trade-offs

| Choice | Pro | Con |
|--------|-----|-----|
| 1000 tokens/chunk | More context | Less precise |
| Top-K=5 | Fast | May miss info |
| 200 overlap | No splits | Redundancy |

---

**See**: [API Reference](./api-reference.md)
