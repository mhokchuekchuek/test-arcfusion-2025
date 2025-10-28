# API Design

Architecture and design decisions for the REST API layer.

---

## Architecture

```
FastAPI Application
    ↓
Dependency Injection (get_services)
    ↓
Route Handlers (/chat, /memory)
    ↓
Multi-Agent Graph (Orchestrator → Research → Synthesis)
    ↓
Redis (Session Memory) + Qdrant (Vector Store)
```

---

## Core Components

### 1. FastAPI App

```python
# src/main.py
from fastapi import FastAPI

app = FastAPI(
    title="Multi-Agent RAG API",
    version="1.0.0"
)

@app.get("/health")
def health():
    return {"status": "healthy"}
```

**Why FastAPI?**
- Async support for concurrent requests
- Automatic OpenAPI docs (`/docs`, `/redoc`)
- Type validation with Pydantic

---

### 2. Dependency Injection

```python
# src/apis/dependencies.py
def get_services():
    """Initialize services once per request."""
    return {
        "graph": create_agent_graph(),
        "memory": get_memory_service(),
        "rag": get_rag_service()
    }

# src/apis/routes/chat.py
@router.post("/chat")
async def chat(
    request: ChatRequest,
    services: dict = Depends(get_services)
):
    graph = services["graph"]
    # Use services...
```

**Why DI?**
- Services initialized once per request
- Easy to mock in tests
- Centralized configuration

---

### 3. Session Management (Redis)

```python
# Store conversation history
memory.add_message(
    session_id="abc-123",
    message="What is RAG?"
)

# Retrieve history
history = memory.get_messages(session_id="abc-123")
```

**Why Redis?**
- Fast in-memory storage
- Automatic session expiry (TTL)
- Scales across API instances

---

### 4. Agent Graph

```python
# Agent execution
result = graph.invoke(state)

# State flows through:
# Orchestrator → Research → Synthesis → END
```

**Why LangGraph?**
- Explicit state management
- Conditional routing between agents
- Built-in history tracking

---

## Request Flow

### POST /chat

```
1. Request arrives with message
   ↓
2. get_services() creates graph + memory + rag
   ↓
3. Load conversation history from Redis
   ↓
4. Create initial state with messages
   ↓
5. graph.invoke(state) executes agents:
   - Orchestrator routes query
   - Research retrieves information
   - Synthesis formats answer
   ↓
6. Save new messages to Redis
   ↓
7. Return response
```

**Code:**
```python
@router.post("/chat")
async def chat(request: ChatRequest, services: dict = Depends(get_services)):
    # 1. Get services
    graph = services["graph"]
    memory = services["memory"]

    # 2. Load history
    session_id = request.session_id or str(uuid.uuid4())
    history = memory.get_messages(session_id)

    # 3. Create state
    state = create_initial_state(
        messages=history + [HumanMessage(content=request.message)],
        session_id=session_id
    )

    # 4. Execute
    result = graph.invoke(state)

    # 5. Save to memory
    memory.add_message(session_id, request.message)
    memory.add_message(session_id, result["final_answer"])

    # 6. Return
    return ChatResponse(
        answer=result["final_answer"],
        session_id=session_id,
        message_count=len(result["messages"])
    )
```

---

## Key Design Decisions

### Stateless API
- No in-memory session storage
- All state in Redis
- API instances can scale horizontally

### Session ID Management
- Client provides session_id (optional)
- Server generates UUID if not provided
- Enables multi-turn conversations

### Error Handling
```python
try:
    result = graph.invoke(state)
except Exception as e:
    logger.error(f"Graph execution failed: {e}")
    return {"answer": "I encountered an error processing your request."}
```

### Configuration
```yaml
# configs/api/api.yaml
api:
  host: 0.0.0.0
  port: 8000
  cors_origins: ["*"]
  timeout: 300
```

---

## Data Models

### Request
```python
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
```

### Response
```python
class ChatResponse(BaseModel):
    answer: str
    session_id: str
    message_count: int
    confidence_score: Optional[float] = None
```

---

## Files

```
src/
├── main.py                      # FastAPI app
├── apis/
│   ├── dependencies.py          # DI setup
│   └── routes/
│       ├── chat.py              # /chat endpoint
│       └── memory.py            # /memory endpoints
└── graph/
    ├── builder.py               # Create agent graph
    └── state.py                 # AgentState schema

configs/api/
└── api.yaml                     # API configuration
```

---

## Performance

- **Async handlers**: Non-blocking I/O
- **Connection pooling**: Reuse Redis/Qdrant connections
- **Request timeout**: 5 minutes max
- **CORS**: Configurable origins

---

## See Also

- [Agent System](../agents/README.md) - Multi-agent workflow
- [Endpoints Reference](./endpoints.md) - API specs
- [Examples](./examples.md) - Usage examples
- [System Overview](../architecture/system-overview.md) - Full architecture
