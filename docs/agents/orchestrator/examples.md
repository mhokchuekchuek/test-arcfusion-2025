# Master Orchestrator Examples

Simple, practical examples showing how to use the orchestrator agent.

## Basic Usage

```python
from langchain_core.messages import HumanMessage
from src.graph.state import create_initial_state
from src.agents.orchestrator import MasterOrchestrator
from tools.llm.client.selector import LLMClientSelector

# Create LLM client
llm_client = LLMClientSelector.create(
    provider="litellm",
    completion_model="gpt-4-turbo"
)

# Create orchestrator
orchestrator = MasterOrchestrator(
    llm_client=llm_client,
    agent_config={
        "name": "orchestrator",
        "max_history": 10,
        "max_clarifications": 2
    }
)

# Create state with clear query
state = create_initial_state(
    messages=[HumanMessage(content="What's in Zhang et al. Table 2?")],
    session_id="session-123"
)

# Execute
result = orchestrator.execute(state)

# Check result
print(result["next_agent"])           # "research" (clear query)
print(result["clarification_needed"]) # False
```

---

## Vague Query → Clarification

```python
# Vague query
state = create_initial_state(
    messages=[HumanMessage(content="Tell me about it")],
    session_id="session-456"
)

result = orchestrator.execute(state)

# Routes to clarification
print(result["next_agent"])           # "clarification"
print(result["clarification_needed"]) # True
print(result["clarification_count"])  # 1
```

---

## Pattern Detection (Layer 2)

```python
from langchain_core.messages import AIMessage

# Simulate user responding to clarification
state = create_initial_state(
    messages=[
        HumanMessage(content="Tell me about it"),
        AIMessage(content="What topic are you asking about?"),
        HumanMessage(content="Zhang et al. paper")
    ],
    session_id="session-789"
)

# Mark that clarification agent just executed
state["last_agent"] = "clarification"
state["clarification_count"] = 1

result = orchestrator.execute(state)

# Pattern detection: AI→Human after clarification
# Skips LLM call and routes directly to research
print(result["next_agent"])          # "research"
print(result["clarification_count"]) # 0 (reset)
```

---

## Max Clarifications (Layer 1)

```python
# User has been asked twice already
state = create_initial_state(
    messages=[HumanMessage(content="Still unclear")],
    session_id="session-101"
)
state["clarification_count"] = 2  # Already at max

# Create orchestrator with max_clarifications=2
orchestrator = MasterOrchestrator(
    llm_client=llm_client,
    agent_config={"max_clarifications": 2}
)

result = orchestrator.execute(state)

# Forces research (emergency brake)
print(result["next_agent"])          # "research"
print(result["clarification_count"]) # 0 (reset)
```

---

## With Langfuse Integration

```python
from tools.observability.selector import ObservabilitySelector

# Create clients
llm_client = LLMClientSelector.create(
    provider="litellm",
    completion_model="gpt-4-turbo"
)

langfuse = ObservabilitySelector.create(
    provider="langfuse",
    public_key="pk-...",
    secret_key="sk-..."
)

# Create orchestrator with Langfuse
orchestrator = MasterOrchestrator(
    llm_client=llm_client,
    langfuse_client=langfuse,
    agent_config={
        "name": "orchestrator",
        "max_history": 10,
        "max_clarifications": 2,
        "prompt": {
            "provider": "langfuse",
            "id": "agent_orchestrator",
            "environment": "production"
        }
    }
)

# Execute
state = create_initial_state(
    messages=[HumanMessage(content="What is RAG?")],
    session_id="prod-session"
)
result = orchestrator.execute(state)

# Langfuse automatically traces:
# - Layer triggered (1, 2, or 3)
# - Decision: CLARIFICATION or RESEARCH
# - Session: "prod-session"
```

---

## Error Handling

```python
# Orchestrator handles errors gracefully

# Even if LLM fails, orchestrator defaults to research
try:
    result = orchestrator.execute(state)
except Exception:
    pass  # Caught internally

# Fallback behavior
print(result["next_agent"])  # "research" (safe default)
```

---

## History Limiting

```python
# Long conversation - orchestrator only uses last N messages

messages = []
for i in range(20):  # 20 messages
    messages.append(HumanMessage(content=f"Question {i}"))
    messages.append(AIMessage(content=f"Answer {i}"))
messages.append(HumanMessage(content="What about this?"))

state = create_initial_state(messages=messages, session_id="long")

# Orchestrator with max_history=10
orchestrator = MasterOrchestrator(
    llm_client=llm_client,
    agent_config={"max_history": 10}
)

result = orchestrator.execute(state)
# Uses only last 10 messages for decision
```

---

## Testing

```python
def test_orchestrator_clear_query():
    """Test orchestrator routes clear query to research."""
    # Mock LLM
    class MockLLM:
        completion_model = "gpt-4"
        def generate(self, **kwargs):
            return "RESEARCH: Query is clear"

    # Create orchestrator
    orchestrator = MasterOrchestrator(
        llm_client=MockLLM(),
        agent_config={"name": "test"}
    )

    # Create state
    state = create_initial_state(
        messages=[HumanMessage(content="What is 2+2?")],
        session_id="test"
    )

    # Execute
    result = orchestrator.execute(state)

    # Assert
    assert result["next_agent"] == "research"
    assert result["clarification_needed"] is False


def test_orchestrator_vague_query():
    """Test orchestrator routes vague query to clarification."""
    class MockLLM:
        completion_model = "gpt-4"
        def generate(self, **kwargs):
            return "CLARIFICATION: Query is vague"

    orchestrator = MasterOrchestrator(
        llm_client=MockLLM(),
        agent_config={"name": "test"}
    )

    state = create_initial_state(
        messages=[HumanMessage(content="Tell me about it")],
        session_id="test"
    )

    result = orchestrator.execute(state)

    assert result["next_agent"] == "clarification"
    assert result["clarification_needed"] is True
    assert result["clarification_count"] == 1
```

---

## Configuration Options

```python
orchestrator = MasterOrchestrator(
    llm_client=llm_client,
    langfuse_client=langfuse,  # Optional
    agent_config={
        "name": "orchestrator",       # Agent name for tracing
        "max_history": 10,            # Number of messages to consider
        "max_clarifications": 2,      # Max clarification loops
        "prompt": {                   # Langfuse prompt config
            "provider": "langfuse",
            "id": "agent_orchestrator",
            "version": None,          # None = latest
            "environment": "production"
        }
    }
)
```

---

## State Fields

### Input (what orchestrator reads):
```python
state["messages"]           # Conversation history
state["session_id"]         # Session ID
state["last_agent"]         # Previous agent (for pattern detection)
state["clarification_count"] # Number of clarifications so far
```

### Output (what orchestrator updates):
```python
state["next_agent"]           # "clarification" or "research"
state["clarification_needed"] # True or False
state["clarification_count"]  # Incremented or reset
state["missing_context"]      # What's missing (if clarification)
state["iteration"]            # Incremented
```

---

## Three-Layer Protection

### Layer 1: Counter Limit
```python
# Emergency brake - forces research after max clarifications
if state["clarification_count"] >= max_clarifications:
    state["next_agent"] = "research"
```

### Layer 2: Pattern Detection
```python
# Detects user response to clarification
# AI→Human pattern after clarification agent
if last_agent == "clarification" and pattern_matches:
    state["next_agent"] = "research"  # Skip LLM
```

### Layer 3: LLM Decision
```python
# Context-aware semantic analysis
decision = llm.analyze(query, history)
if "CLARIFICATION" in decision:
    state["next_agent"] = "clarification"
else:
    state["next_agent"] = "research"
```

---

## See Also

- [Orchestrator Design](./design.md) - Three-layer system explained
- [API Reference](./api-reference.md) - Full API docs
- [Clarification Examples](../clarification/examples.md) - Clarification usage
