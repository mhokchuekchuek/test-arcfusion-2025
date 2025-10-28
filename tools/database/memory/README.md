# Memory Store Tools

## Purpose

Store session-based conversation history and user context for multi-turn conversations. Memory stores enable the RAG system to maintain context across multiple interactions within a session.

## Available Providers

### Redis

**Provider**: `redis`

**Description**: Fast in-memory key-value store with built-in TTL (time-to-live) support for automatic session expiration.

**Key Features**:
- **In-memory speed**: Microsecond latency for reads/writes
- **TTL support**: Automatic expiration of old sessions
- **Persistence options**: Optional disk snapshots (RDB) or append-only logs (AOF)
- **Data structures**: Lists, hashes, sets beyond simple key-value
- **Atomic operations**: Thread-safe operations for concurrent access
- **Pub/Sub**: Event notifications (optional feature)

**Why Redis Was Chosen**:
- Industry standard for session storage
- Excellent performance (sub-millisecond latency)
- Simple TTL management (critical for session cleanup)
- Mature, battle-tested in production
- Easy Docker deployment

**Use Cases**:
- Conversation history for multi-turn chat
- User session management
- Rate limiting and throttling
- Caching frequently accessed data

## Usage Examples

### Basic Session Management

```python
from tools.database.memory.selector import MemorySelector

# Initialize memory store
memory = MemorySelector.create(
    provider="redis",
    host="localhost",
    port=6379,
    db=0
)

# Store conversation history
session_id = "user_123_session_456"
history = [
    {"role": "user", "content": "What is RAG?"},
    {"role": "assistant", "content": "RAG stands for Retrieval-Augmented Generation..."}
]

# Save with 1 hour TTL
memory.set(session_id, history, ttl=3600)

# Retrieve history
retrieved_history = memory.get(session_id)
print(retrieved_history)
```

### Multi-Turn Conversation

```python
from tools.database.memory.selector import MemorySelector
from tools.llm.client.selector import LLMClientSelector

memory = MemorySelector.create(provider="redis", host="localhost", port=6379)
llm = LLMClientSelector.create(provider="litellm", proxy_url="...")

def chat(session_id: str, user_message: str) -> str:
    """Handle multi-turn conversation with memory."""
    # Get or initialize history
    history = memory.get(session_id) or []

    # Add user message
    history.append({"role": "user", "content": user_message})

    # Build prompt with history
    prompt = format_conversation(history)

    # Generate response
    response = llm.generate(prompt)

    # Add assistant response
    history.append({"role": "assistant", "content": response})

    # Save updated history (1 hour TTL)
    memory.set(session_id, history, ttl=3600)

    return response

# Example conversation
session = "user_123"
print(chat(session, "What is RAG?"))
print(chat(session, "How does it differ from traditional search?"))  # Has context!
print(chat(session, "Give me an example"))  # Knows "it" refers to RAG
```

### Session Management

```python
# Check if session exists
if memory.exists(session_id):
    history = memory.get(session_id)
else:
    history = []

# Delete session (logout, clear context)
memory.delete(session_id)

# Extend session TTL (user is active)
memory.expire(session_id, ttl=3600)

# Get all sessions for a user
user_sessions = memory.keys(pattern=f"user_{user_id}_*")
```

### Rate Limiting

```python
def check_rate_limit(user_id: str, max_requests: int = 10, window: int = 60):
    """Rate limit using Redis."""
    key = f"ratelimit:{user_id}"

    # Increment counter
    count = memory.incr(key)

    # Set TTL on first request
    if count == 1:
        memory.expire(key, ttl=window)

    # Check limit
    if count > max_requests:
        raise Exception(f"Rate limit exceeded: {count}/{max_requests} in {window}s")

    return count
```

### Caching

```python
from functools import wraps
import hashlib
import json

def cache_result(ttl: int = 300):
    """Cache function results in Redis."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = json.dumps({"func": func.__name__, "args": args, "kwargs": kwargs})
            cache_key = f"cache:{hashlib.md5(key_data.encode()).hexdigest()}"

            # Check cache
            cached = memory.get(cache_key)
            if cached is not None:
                return cached

            # Compute and cache result
            result = func(*args, **kwargs)
            memory.set(cache_key, result, ttl=ttl)
            return result

        return wrapper
    return decorator

@cache_result(ttl=600)
def expensive_operation(query: str):
    # Expensive LLM call or computation
    return llm.generate(query)
```

## Configuration

### Environment Variables

```bash
# Memory store provider
MEMORY_PROVIDER=redis

# Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Optional

# Session settings
SESSION_TTL=3600  # 1 hour default
MAX_HISTORY_LENGTH=20  # Keep last N messages
```

### Docker Setup

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes  # Enable persistence
    environment:
      - REDIS_PASSWORD=your_password  # Optional

volumes:
  redis_data:
```

Start Redis:
```bash
docker-compose up -d redis
```

### Connection Pooling

```python
# Create memory store with connection pool
memory = MemorySelector.create(
    provider="redis",
    host="localhost",
    port=6379,
    connection_pool_size=10,  # Reuse connections
    socket_timeout=5,
    socket_connect_timeout=5
)
```

## Base Interface

All memory store providers implement the `BaseMemory` interface:

```python
from abc import ABC, abstractmethod

class BaseMemory(ABC):
    @abstractmethod
    def get(self, key: str) -> any:
        """Get value by key."""
        pass

    @abstractmethod
    def set(self, key: str, value: any, ttl: int = None):
        """Set value with optional TTL."""
        pass

    @abstractmethod
    def delete(self, key: str):
        """Delete key."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    def expire(self, key: str, ttl: int):
        """Set expiration on existing key."""
        pass
```

## Integration Points

The memory store is used by:

- **`src/apis/`**: API endpoints
  - Session management for chat endpoints
  - Rate limiting
  - Response caching

- **`src/agents/`**: Multi-turn agents
  - Conversation context
  - Agent state persistence
  - User preferences

- **`src/rag/`**: RAG pipeline
  - Query history
  - Retrieval caching

## Session Design Patterns

### Bounded History

```python
def add_to_history(session_id: str, message: dict, max_length: int = 20):
    """Keep conversation history bounded."""
    history = memory.get(session_id) or []

    history.append(message)

    # Trim to max length (keep most recent)
    if len(history) > max_length:
        history = history[-max_length:]

    memory.set(session_id, history, ttl=3600)
```

### Sliding Window TTL

```python
def update_session(session_id: str, data: dict):
    """Update session and reset TTL (sliding window)."""
    memory.set(session_id, data, ttl=1800)  # 30 min sliding window
```

### Hierarchical Keys

```python
# Organize keys by namespace
session_key = f"session:{user_id}:{session_id}"
user_pref_key = f"user:{user_id}:preferences"
cache_key = f"cache:{resource_type}:{resource_id}"

# Easy cleanup by pattern
memory.delete_pattern("session:user_123:*")  # Clear all user sessions
```

## Best Practices

1. **Key Naming**: Use consistent naming patterns (`namespace:entity:id`)
2. **TTL Management**: Always set TTL to prevent memory leaks
3. **Bounded Data**: Limit conversation history length
4. **Serialization**: Use efficient serialization (JSON, msgpack)
5. **Connection Pooling**: Reuse connections for better performance
6. **Error Handling**: Handle Redis unavailability gracefully
7. **Monitoring**: Track memory usage and key count

## Performance Optimization

### Batch Operations

```python
# Pipeline for multiple operations
pipe = memory.pipeline()
for session_id, history in sessions.items():
    pipe.set(session_id, history, ttl=3600)
results = pipe.execute()

# Efficient multi-get
keys = ["session:1", "session:2", "session:3"]
values = memory.mget(keys)
```

### Connection Pooling

```python
# Good: Connection pool (reuse connections)
memory = MemorySelector.create(
    provider="redis",
    host="localhost",
    connection_pool_size=10
)

# Bad: New connection per request
for i in range(100):
    m = MemorySelector.create(provider="redis", host="localhost")
    m.get(f"key_{i}")
```

### Serialization

```python
import json
import msgpack

# JSON (human-readable, slower)
memory.set("session", json.dumps(history))

# MessagePack (binary, faster, smaller)
memory.set("session", msgpack.packb(history))
```

## Memory Management

### Eviction Policies

Configure Redis eviction when max memory is reached:

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru  # Evict least recently used keys
```

Eviction policies:
- `allkeys-lru`: Best for cache use case
- `volatile-lru`: Only evict keys with TTL
- `allkeys-lfu`: Evict least frequently used
- `volatile-ttl`: Evict keys with shortest TTL

### Monitoring Memory Usage

```python
# Get Redis info
info = memory.info()
print(f"Used memory: {info['used_memory_human']}")
print(f"Peak memory: {info['used_memory_peak_human']}")
print(f"Keys: {memory.dbsize()}")

# Check specific key size
import sys
value = memory.get(session_id)
size_bytes = sys.getsizeof(value)
print(f"Session size: {size_bytes} bytes")
```

## Persistence Options

### RDB Snapshots (Periodic)

```conf
# redis.conf
save 900 1      # Save if 1 key changed in 15 min
save 300 10     # Save if 10 keys changed in 5 min
save 60 10000   # Save if 10000 keys changed in 1 min
```

### AOF (Append-Only File)

```conf
# redis.conf
appendonly yes
appendfsync everysec  # Sync every second (balanced)
```

**Trade-offs**:
- RDB: Smaller files, faster restart, but potential data loss
- AOF: Durability, but larger files and slower restart

## Troubleshooting

**Issue**: Connection refused
**Solution**: Verify Redis is running (`docker ps`), check host/port

**Issue**: Out of memory
**Solution**: Increase maxmemory, enable eviction policy, reduce TTL

**Issue**: Slow operations
**Solution**: Use pipelining for batches, check network latency

**Issue**: Data not persisting after restart
**Solution**: Enable RDB or AOF persistence in redis.conf

**Issue**: Keys not expiring
**Solution**: Verify TTL is set (`memory.ttl(key)`), check Redis config

## Monitoring

### Key Metrics

```python
# Connection stats
info = memory.info('clients')
print(f"Connected clients: {info['connected_clients']}")

# Memory stats
info = memory.info('memory')
print(f"Used memory: {info['used_memory_human']}")
print(f"Fragmentation: {info['mem_fragmentation_ratio']}")

# Command stats
info = memory.info('stats')
print(f"Total commands: {info['total_commands_processed']}")
print(f"Commands/sec: {info['instantaneous_ops_per_sec']}")

# Slow log (commands taking >10ms)
slow_log = memory.slowlog_get(10)
for entry in slow_log:
    print(f"Duration: {entry['duration']}μs - Command: {entry['command']}")
```

## Scaling Considerations

### Vertical Scaling

- Redis is single-threaded per instance
- More RAM = more data capacity
- Faster CPU = better throughput

### Horizontal Scaling

**Redis Cluster** (automatic sharding):
```python
from redis.cluster import RedisCluster

# Connect to cluster
memory = MemorySelector.create(
    provider="redis",
    host="redis-cluster-node1",
    port=6379,
    cluster_mode=True
)
```

**Separate Instances by Use Case**:
```python
# Separate Redis instances
session_store = MemorySelector.create(provider="redis", host="redis-sessions", port=6379)
cache_store = MemorySelector.create(provider="redis", host="redis-cache", port=6379)
queue_store = MemorySelector.create(provider="redis", host="redis-queue", port=6379)
```

## Security

### Authentication

```python
memory = MemorySelector.create(
    provider="redis",
    host="localhost",
    port=6379,
    password="your_strong_password"
)
```

### TLS/SSL

```python
memory = MemorySelector.create(
    provider="redis",
    host="redis.example.com",
    port=6380,
    ssl=True,
    ssl_cert_reqs="required"
)
```

## See Also

- [Vector Store](../vector/README.md) - Document embedding storage
- [Database Tools Overview](../README.md) - All database tools
- [Agent Documentation](../../../docs/agents/README.md) - How agents use memory
- [Redis Documentation](https://redis.io/documentation)
