# API Examples

Practical examples for using the REST API.

---

## Basic Chat Request

### cURL

```bash
# Without session_id (auto-generated)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is DAIL-SQL?"}'

# With specific session_id
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is DAIL-SQL?", "session_id": "user-123"}'
```

Response:
```json
{
  "answer": "DAIL-SQL is a text-to-SQL approach that...",
  "session_id": "user-123",
  "message_count": 2,
  "confidence_score": 0.85
}
```

---

## Multi-Turn Conversation

### Continue Session

```bash
# First message with session_id
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the accuracy?", "session_id": "my-conversation"}'

# Follow-up message (uses same session_id for history)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What about the dataset?", "session_id": "my-conversation"}'
```

The second request has access to conversation history because it uses the same `session_id`.

---

## Python Client

### Simple Request

```python
import requests

url = "http://localhost:8000/chat"

response = requests.post(
    url,
    json={"message": "What is RAG?"}
)

data = response.json()
print(data["answer"])
print(f"Session: {data['session_id']}")
```

---

### Multi-Turn Conversation

```python
import requests

url = "http://localhost:8000/chat"
session_id = None

# First question
response = requests.post(url, json={
    "message": "Find papers about text-to-SQL"
})
data = response.json()
session_id = data["session_id"]
print(f"Answer 1: {data['answer']}")

# Follow-up question
response = requests.post(url, json={
    "message": "What's the best one?",
    "session_id": session_id
})
data = response.json()
print(f"Answer 2: {data['answer']}")
```

---

### Client Class

```python
import requests
from typing import Optional

class RAGClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None

    def chat(self, message: str) -> dict:
        """Send message and get response."""
        response = requests.post(
            f"{self.base_url}/chat",
            json={
                "message": message,
                "session_id": self.session_id
            }
        )
        data = response.json()

        # Save session ID for next request
        self.session_id = data["session_id"]
        return data

    def reset(self):
        """Start new conversation."""
        self.session_id = None

# Usage
client = RAGClient()

# Conversation 1
response1 = client.chat("What is DAIL-SQL?")
print(response1["answer"])

response2 = client.chat("Who are the authors?")
print(response2["answer"])

# New conversation
client.reset()
response3 = client.chat("Different topic")
```

---

## Memory Management

### Get Conversation History

```bash
curl -X GET http://localhost:8000/memory/abc-123
```

Response:
```json
{
  "session_id": "abc-123",
  "messages": [
    {"role": "user", "content": "What is DAIL-SQL?"},
    {"role": "assistant", "content": "DAIL-SQL is..."},
    {"role": "user", "content": "What's the accuracy?"},
    {"role": "assistant", "content": "The accuracy is..."}
  ],
  "message_count": 4
}
```

---

### Clear Conversation

```bash
curl -X DELETE http://localhost:8000/memory/abc-123
```

Response:
```json
{
  "message": "Conversation history cleared",
  "session_id": "abc-123"
}
```

---

### Python Memory Management

```python
import requests

base_url = "http://localhost:8000"
session_id = "abc-123"

# Get history
response = requests.get(f"{base_url}/memory/{session_id}")
history = response.json()
print(f"Messages: {history['message_count']}")

# Clear history
requests.delete(f"{base_url}/memory/{session_id}")
```

---

## Different Query Types

### PDF-Specific Query

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What accuracy is reported in Table 2 of Zhang et al.?", "session_id": "pdf-query"}'
```

Agent uses PDF retrieval tool only.

---

### Web Search Query

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What did OpenAI announce this month?", "session_id": "web-query"}'
```

Agent uses web search tool.

---

### Multi-Step Research

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find SOTA text-to-SQL approaches in papers, then search for recent improvements", "session_id": "research-query"}'
```

Agent autonomously uses both PDF and web tools.

---

### Clarification Needed

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about the accuracy", "session_id": "clarify-session"}'
```

Response:
```json
{
  "answer": "Could you clarify which accuracy you're referring to? For example: model accuracy, dataset accuracy, or accuracy from a specific paper?",
  "session_id": "clarify-session",
  "message_count": 2
}
```

---

## Error Handling

### Connection Error

```python
import requests

try:
    response = requests.post(
        "http://localhost:8000/chat",
        json={"message": "What is RAG?"},
        timeout=10
    )
    response.raise_for_status()
    print(response.json()["answer"])
except requests.exceptions.ConnectionError:
    print("API is not running")
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
```

---

### Validation Error

```bash
# Missing message field
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{}'
```

Response (422):
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy"
}
```

---

## Interactive Docs

### Swagger UI

Open browser: http://localhost:8000/docs

- Try out endpoints
- See request/response schemas
- Generate code snippets

### ReDoc

Open browser: http://localhost:8000/redoc

- Clean API documentation
- Schema definitions
- Examples

---

## Streaming (Future)

```python
# Not yet implemented - example for reference
import requests

response = requests.post(
    "http://localhost:8000/chat/stream",
    json={"message": "What is RAG?"},
    stream=True
)

for chunk in response.iter_lines():
    if chunk:
        print(chunk.decode(), end="", flush=True)
```

---

## Complete Example

```python
import requests
from typing import Optional

class SimpleRAGClient:
    """Minimal RAG API client."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None

    def ask(self, question: str) -> str:
        """Ask a question and get an answer."""
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "message": question,
                    "session_id": self.session_id
                },
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            self.session_id = data["session_id"]
            return data["answer"]

        except Exception as e:
            return f"Error: {e}"

    def clear(self):
        """Clear conversation history."""
        if self.session_id:
            requests.delete(f"{self.base_url}/memory/{self.session_id}")
            self.session_id = None

# Usage
client = SimpleRAGClient()

# Ask questions
print(client.ask("What is DAIL-SQL?"))
print(client.ask("What's the accuracy?"))  # Uses context

# Clear and start fresh
client.clear()
print(client.ask("New topic"))
```

---

## Testing

### Unit Test

```python
def test_chat_endpoint():
    """Test chat endpoint returns answer."""
    response = requests.post(
        "http://localhost:8000/chat",
        json={"message": "What is RAG?"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "session_id" in data
    assert len(data["answer"]) > 0
```

---

### Integration Test

```python
def test_multi_turn_conversation():
    """Test conversation maintains context."""
    # First message
    response1 = requests.post(
        "http://localhost:8000/chat",
        json={"message": "What is DAIL-SQL?"}
    )
    session_id = response1.json()["session_id"]

    # Follow-up
    response2 = requests.post(
        "http://localhost:8000/chat",
        json={
            "message": "What's the accuracy?",
            "session_id": session_id
        }
    )

    answer = response2.json()["answer"]
    assert "accuracy" in answer.lower()
```

---

## See Also

- [API Design](./design.md) - Architecture details
- [Endpoints Reference](./endpoints.md) - Full API specs
- [Agent System](../agents/README.md) - How agents work
