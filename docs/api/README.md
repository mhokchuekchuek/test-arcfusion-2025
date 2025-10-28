# API Documentation

REST API for multi-agent RAG system with PDF Q&A.

## Quick Start

```bash
# Start API
uvicorn src.main:app --reload --port 8000

# Ask a question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is RAG?"}'
```

---

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat` | POST | Ask questions |
| `/memory/{session_id}` | GET | Get conversation history |
| `/memory/{session_id}` | DELETE | Clear conversation |
| `/health` | GET | Health check |

[Full API Reference →](./endpoints.md)

---

## Simple Example

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the accuracy in Zhang et al.?"}'
```

Response:
```json
{
  "answer": "According to Zhang et al., the accuracy is 87.3%.",
  "session_id": "abc-123",
  "message_count": 2
}
```

[More Examples →](./examples.md)

---

## How It Works

```
POST /chat
    ↓
Orchestrator → Routes query
    ↓
Research → Retrieves info from PDFs/web
    ↓
Synthesis → Formats answer
    ↓
Response
```

[Design Details →](./design.md)

---

## Documentation

- [Design](./design.md) - API architecture
- [Endpoints](./endpoints.md) - API reference
- [Examples](./examples.md) - Code examples

---

## Interactive Docs

- **Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## See Also

- [Agent System](../agents/README.md) - Multi-agent workflow
- [System Overview](../architecture/system-overview.md) - Full architecture
