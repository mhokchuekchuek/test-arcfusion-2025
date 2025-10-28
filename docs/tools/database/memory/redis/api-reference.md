# Redis Memory Store API Reference

Redis-backed session memory client for storing conversation history with automatic TTL expiration.

## Class Definition

```python
from tools.database.memory.redis.main import MemoryClient

class MemoryClient(BaseMemory):
    """Redis client for storing conversation history.

    Stores session-based messages in Redis with automatic TTL expiration.
    Each session is a Redis list containing JSON-encoded messages.
    """
```

**File**: `tools/database/memory/redis/main.py`

## Constructor

### `__init__(...)`

Initialize Redis memory client for session storage.

```python
memory = MemoryClient(
    host="localhost",
    port=6379,
    password=None,
    db=0,
    session_ttl=3600,
    key_prefix="session:"
)
```

#### Parameters

- `host` (str, optional): Redis server host
  - Default: `"localhost"`
  - Docker Compose: `"redis"` (service name)

- `port` (int, optional): Redis server port
  - Default: `6379`

- `password` (str | None, optional): Redis password
  - Default: `None` (no authentication)
  - Set if Redis requires AUTH

- `db` (int, optional): Redis database number
  - Default: `0`
  - Range: 0-15 (default Redis config)

- `session_ttl` (int, optional): Session TTL in seconds
  - Default: `3600` (1 hour)
  - After TTL, session is automatically deleted
  - Common values: 1800 (30min), 7200 (2hr), 86400 (24hr)

- `key_prefix` (str, optional): Prefix for Redis keys
  - Default: `"session:"`
  - Format: `{key_prefix}{session_id}`
  - Example: `"session:user-123-abc"`

#### Raises

- `redis.ConnectionError`: If cannot connect to Redis server

#### Example

```python
from tools.database.memory.selector import MemoryClientSelector

memory = MemoryClientSelector.create(
    provider="redis",
    host="localhost",
    port=6379,
    session_ttl=3600
)
```

## Methods

### `add(session_id, role, content, metadata=None, **kwargs)`

Add a message to session history.

#### Parameters

- `session_id` (str, required): Unique session identifier
  - Format: Any string (recommend: UUID)
  - Example: `"user-123-abc"`, `"conv-2024-01-15"`

- `role` (str, required): Message role
  - Options: `"user"` or `"assistant"`
  - Case-sensitive

- `content` (str, required): Message content
  - User query or assistant response
  - Can be empty string

- `metadata` (dict | None, optional): Additional metadata
  - Custom fields for tracking
  - Example: `{"model": "gpt-4", "tokens": 150}`

- `**kwargs`: Extra parameters (ignored for compatibility)

#### Raises

- `ValueError`: If role is not "user" or "assistant"
- `redis.RedisError`: If Redis operation fails

#### Example

```python
# Add user message
memory.add(
    session_id="user-123",
    role="user",
    content="What is RAG?"
)

# Add assistant response
memory.add(
    session_id="user-123",
    role="assistant",
    content="RAG stands for Retrieval-Augmented Generation...",
    metadata={"model": "gpt-4", "tokens": 120}
)
```

### `get(session_id, limit=None)`

Get conversation history for a session.

#### Parameters

- `session_id` (str, required): Session identifier to retrieve

- `limit` (int | None, optional): Maximum number of messages
  - Default: `None` (return all messages)
  - If set, returns last N messages
  - Useful for context window management

#### Returns

List of message dictionaries, ordered chronologically:
- `role` (str): Message role ("user" or "assistant")
- `content` (str): Message content
- `timestamp` (str): ISO format timestamp
- `metadata` (dict): Additional metadata (if provided)

Returns empty list if session doesn't exist or has expired.

#### Example

```python
# Get all messages
history = memory.get(session_id="user-123")
for msg in history:
    print(f"{msg['role']}: {msg['content']}")
    print(f"  Timestamp: {msg['timestamp']}")

# Get last 10 messages only
recent = memory.get(session_id="user-123", limit=10)
```

### `clear(session_id)`

Delete all messages for a session.

#### Parameters

- `session_id` (str, required): Session identifier to clear

#### Returns

None

#### Example

```python
# Clear session history
memory.clear(session_id="user-123")

# Verify cleared
history = memory.get(session_id="user-123")
assert len(history) == 0
```

### `exists(session_id) -> bool`

Check if a session exists (has messages).

#### Parameters

- `session_id` (str, required): Session identifier to check

#### Returns

`True` if session exists and has messages, `False` otherwise.

#### Example

```python
if memory.exists(session_id="user-123"):
    print("Session found, loading history")
else:
    print("New session, starting fresh")
```

## Configuration

### Environment Variables

```bash
# Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Optional
REDIS_DB=0

# Session settings
SESSION_TTL=3600  # 1 hour
KEY_PREFIX=session:
```

### Docker Compose

```yaml
services:
  redis:
    image: redis/redis-stack-server:latest
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
```

### Dependencies

- `redis`: Official Redis Python client
  ```bash
  pip install redis
  ```

## Usage Patterns

### Multi-Turn Conversation

```python
from tools.database.memory.selector import MemoryClientSelector

memory = MemoryClientSelector.create(provider="redis")
session_id = "user-123-conv-1"

# Turn 1
memory.add(session_id=session_id, role="user", content="What is RAG?")
memory.add(session_id=session_id, role="assistant", content="RAG is...")

# Turn 2 (with context)
memory.add(session_id=session_id, role="user", content="How does it work?")
history = memory.get(session_id=session_id)
# Use history for context in LLM call
```

### Session Management

```python
import uuid

# Create new session
session_id = str(uuid.uuid4())

# Add initial message
memory.add(session_id=session_id, role="user", content="Hello")

# Return session_id to user for continuation
return {"session_id": session_id, "response": "Hi!"}
```

### Context Window Management

```python
# Get last 10 messages to fit context window
history = memory.get(session_id="user-123", limit=10)

# Build prompt
messages = [{"role": msg["role"], "content": msg["content"]}
            for msg in history]
```

### Integration with LangGraph

```python
from tools.database.memory.selector import MemoryClientSelector

# Initialize memory
memory = MemoryClientSelector.create(provider="redis")

# After agent execution
final_state = agent_workflow.invoke(state, config=config)

# Store conversation
for msg in final_state["messages"]:
    memory.add(
        session_id=state["session_id"],
        role="assistant" if msg.type == "ai" else "user",
        content=msg.content
    )
```

## Features

### Automatic Expiration

Sessions automatically expire after `session_ttl`:
- No manual cleanup required
- Saves memory
- Privacy-friendly (conversations auto-deleted)

### JSON Storage

Messages stored as JSON with metadata:
```json
{
  "role": "user",
  "content": "What is RAG?",
  "timestamp": "2024-01-15T10:30:00",
  "metadata": {"client": "web", "ip": "192.168.1.1"}
}
```

### Ordered History

Messages stored in Redis LIST (FIFO):
- Chronological order preserved
- Efficient retrieval (O(N) where N = limit)
- Can get last N messages efficiently

---

## See Also

- [Memory Selector](../../selector.py) - Factory for creating memory clients
- [Base Memory](../../base.py) - Abstract base class
- [Redis Documentation](https://redis.io/docs/) - Official Redis docs
- [LangGraph Checkpointer](../../../../../src/graph/workflow.py) - State persistence
- [RAG Service](../../../../../src/rag/service.py) - Service using memory
