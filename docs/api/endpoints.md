# API Endpoints

REST API specification - quick reference.

**Base URL:** `http://localhost:8000`

---

## POST /chat

Ask questions using multi-agent RAG.

### Request

```json
{
  "message": "What is the accuracy?",
  "session_id": "user-123",  // optional
  "top_k": 5                  // optional, default: 5
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | ✓ | User question |
| `session_id` | string | - | Session ID (auto-generated if not provided) |
| `top_k` | integer | - | Number of chunks to retrieve (1-20) |

### Response

```json
{
  "answer": "According to Zhang et al...",
  "sources": [],
  "session_id": "user-123",
  "message_count": 2
}
```

### Example

```bash
# Without session_id (auto-generated)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is DAIL-SQL?"}'

# With specific session_id
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the main contribution of Zhang et al. 2024?", "session_id": "user-session-123"}'
```

**Code:** `src/apis/routes/chat.py:50`

---

## GET /memory/{session_id}

Get conversation history.

### Response

```json
{
  "session_id": "user-123",
  "message_count": 4,
  "messages": [
    {
      "role": "user",
      "content": "What is the accuracy?",
      "timestamp": "2024-01-15T10:30:00Z",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "According to...",
      "timestamp": "2024-01-15T10:30:03Z",
      "metadata": {}
    }
  ]
}
```

### Example

```bash
curl http://localhost:8000/memory/user-123
```

**Code:** `src/apis/routes/memory.py:42`

---

## DELETE /memory/{session_id}

Clear conversation history.

### Response

```json
{
  "message": "Session cleared successfully",
  "session_id": "user-123"
}
```

### Example

```bash
curl -X DELETE http://localhost:8000/memory/user-123
```

**Code:** `src/apis/routes/memory.py:113`

---

## GET /health

Health check.

### Response

```json
{
  "status": "healthy",
  "service": "pdf-chat-agent",
  "version": "1.0.0"
}
```

### Example

```bash
curl http://localhost:8000/health
```

**Code:** `src/apis/routes/health.py:23`

---

## Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Success |
| 400 | Bad Request | Invalid JSON, missing fields |
| 404 | Not Found | Session not found, empty vector DB |
| 500 | Server Error | LLM failure, DB error |

---

## Error Format

```json
{
  "detail": "Error message"
}
```

---

## Multi-Turn Example

First message:
```bash
curl -X POST http://localhost:8000/chat \
  -d '{"message": "What is DAIL-SQL?", "session_id": "s1"}'
```

Follow-up (uses history):
```bash
curl -X POST http://localhost:8000/chat \
  -d '{"message": "What accuracy?", "session_id": "s1"}'
```

---

## See Also

- [Examples](./examples.md) - More usage examples
- [Design](./design.md) - Architecture details
