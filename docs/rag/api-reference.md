# API Reference

Component APIs for the RAG module.

---

## DocumentRetriever

**Location**: `src/rag/retriever/document_retriever.py`

**Purpose**: Semantic search over vector embeddings

### Constructor

```python
DocumentRetriever(
    llm_client: BaseLLM,
    vector_store: BaseVectorStore
)
```

### Methods

#### retrieve()

```python
retrieve(
    query: str,
    top_k: int = 5,
    filter: dict | None = None
) -> list[dict]
```

**Returns:**
```python
[{
    "text": str,
    "source": str,
    "page": int,
    "score": float,
    "metadata": dict
}]
```

### Example

```python
from src.rag.retriever.document_retriever import DocumentRetriever

retriever = DocumentRetriever(llm_client, vector_store)
docs = retriever.retrieve("What is RAG?", top_k=5)

for doc in docs:
    print(f"{doc['source']} p.{doc['page']} (score: {doc['score']:.3f})")
```

---

## RAGService

**Location**: `src/rag/service.py`

**Purpose**: High-level Q&A pipeline (stateless)

### Constructor

```python
RAGService(
    document_retriever: DocumentRetriever,
    llm_client: BaseLLM = None
)
```

### Methods

#### answer_question()

```python
answer_question(
    question: str,
    session_id: str | None = None,
    top_k: int = 5
) -> dict
```

**Returns:**
```python
{
    "answer": str,
    "sources": list[dict],
    "session_id": str,
    "message_count": int
}
```

**Note**: Stateless. LangGraph manages state in multi-agent system.

### Example

```python
from src.rag.service import RAGService

rag_service = RAGService(retriever, llm_client)
response = rag_service.answer_question("What is RAG?", top_k=5)

print(response['answer'])
```

---

## SessionMemory

**Location**: `src/rag/memory/session_memory.py`

**Purpose**: Conversation history (optional, not used by agents)

### Constructor

```python
SessionMemory(memory_client: BaseMemory)
```

### Methods

| Method | Signature | Purpose |
|--------|-----------|---------|
| `add()` | `add(session_id, role, content, metadata=None)` | Add message |
| `get()` | `get(session_id, limit=None) -> list[dict]` | Get history |
| `clear()` | `clear(session_id)` | Clear session |
| `exists()` | `exists(session_id) -> bool` | Check session |
| `count()` | `count(session_id) -> int` | Count messages |

### Example

```python
from src.rag.memory.session_memory import SessionMemory

session_memory = SessionMemory(memory_client)
session_memory.add("user-123", "user", "What is RAG?")

history = session_memory.get("user-123", limit=10)
```

---

## Configuration

```yaml
# configs/rag.yaml
vector_store:
  provider: qdrant
  host: localhost
  port: 6333
  collection: documents

embeddings:
  model: text-embedding-3-small
  dimensions: 1536

retrieval:
  top_k: 5
```

---

## Agent Integration

Research agent uses `DocumentRetriever` via `PDFRetrievalTool`:

```python
from src.agents.tools.pdf_retrieval import PDFRetrievalTool

pdf_tool = PDFRetrievalTool(retriever=retriever, top_k=5)
research_agent = ResearchSupervisor(llm, tools=[pdf_tool])
```

---

**See**: [Retrieval Strategy](./retrieval-strategy.md) | [Research Agent](../agents/research/design.md)
