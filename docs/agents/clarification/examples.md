# Clarification Agent Examples

Simple, practical examples showing how to use the clarification agent.

## Basic Usage

```python
from langchain_core.messages import HumanMessage
from src.graph.state import create_initial_state
from src.agents.clarification import ClarificationAgent
from tools.llm.client.selector import LLMClientSelector

# Create LLM client
llm_client = LLMClientSelector.create(
    provider="litellm",
    completion_model="gpt-4-turbo"
)

# Create clarification agent
clarification = ClarificationAgent(
    llm_client=llm_client,
    agent_config={"name": "clarification", "max_history": 10}
)

# Create state
state = create_initial_state(
    messages=[HumanMessage(content="Tell me about AI")],
    session_id="session-123"
)

# Execute
result = clarification.execute(state)

# Check result
print(result["final_answer"])  # Clarification question
print(result["next_agent"])    # "END"
print(result["last_agent"])    # "clarification"
```

---

## With Langfuse Integration

```python
from tools.observability.selector import ObservabilitySelector

# Create LLM client
llm_client = LLMClientSelector.create(
    provider="litellm",
    completion_model="gpt-4-turbo"
)

# Create Langfuse client
langfuse = ObservabilitySelector.create(
    provider="langfuse",
    public_key="pk-...",
    secret_key="sk-..."
)

# Create agent with Langfuse
clarification = ClarificationAgent(
    llm_client=llm_client,
    langfuse_client=langfuse,
    agent_config={
        "name": "clarification",
        "max_history": 10,
        "prompt": {
            "provider": "langfuse",
            "id": "agent_clarification",
            "environment": "production"
        }
    }
)

# Execute
state = create_initial_state(
    messages=[HumanMessage(content="How do I use it?")],
    session_id="prod-session"
)
result = clarification.execute(state)

# Langfuse automatically traces:
# - Input: {"query": "...", "history": "..."}
# - Output: clarification question
# - Session: "prod-session"
```

---

## With Conversation History

```python
from langchain_core.messages import HumanMessage, AIMessage

# Create state with history
state = create_initial_state(
    messages=[
        HumanMessage(content="What is LangChain?"),
        AIMessage(content="LangChain is a framework..."),
        HumanMessage(content="How does it compare?")  # Vague follow-up
    ],
    session_id="session-456"
)

# Execute
result = clarification.execute(state)

print(result["final_answer"])
# → "What would you like to compare LangChain to?"
```

---

## Error Handling

```python
# Agent automatically handles errors with fallback

try:
    result = clarification.execute(state)
except Exception as e:
    # Agent catches internally and returns fallback
    pass

# Even if LLM fails, agent returns:
# "Could you please provide more details about your question?"
print(result["final_answer"])
print(result["next_agent"])  # Still "END"
```

---

## History Limiting

```python
# Long conversation - agent only uses last N messages

messages = []
for i in range(20):  # 20 messages
    messages.append(HumanMessage(content=f"Question {i}"))
    messages.append(AIMessage(content=f"Answer {i}"))
messages.append(HumanMessage(content="Tell me more"))

state = create_initial_state(messages=messages, session_id="long-session")

# Agent with max_history=10
clarification = ClarificationAgent(
    llm_client=llm_client,
    agent_config={"max_history": 10}  # Only last 10 messages
)

result = clarification.execute(state)
# Uses only last 10 messages, ignores rest
```

---

## Testing

```python
def test_clarification():
    """Test clarification agent."""
    # Mock LLM
    class MockLLM:
        completion_model = "gpt-4"
        def generate(self, **kwargs):
            return "What aspect are you interested in?"

    # Create agent
    agent = ClarificationAgent(
        llm_client=MockLLM(),
        agent_config={"name": "test"}
    )

    # Create state
    state = create_initial_state(
        messages=[HumanMessage(content="Tell me about it")],
        session_id="test"
    )

    # Execute
    result = agent.execute(state)

    # Assert
    assert result["last_agent"] == "clarification"
    assert result["next_agent"] == "END"
    assert result["final_answer"] is not None
    assert len(result["messages"]) == 2
```

---

## Configuration Options

```python
clarification = ClarificationAgent(
    llm_client=llm_client,
    langfuse_client=langfuse,  # Optional
    agent_config={
        "name": "clarification",        # Agent name for tracing
        "max_history": 10,              # Number of messages to consider
        "prompt": {                      # Langfuse prompt config
            "provider": "langfuse",
            "id": "agent_clarification",
            "version": None,             # None = latest
            "environment": "production"  # or "dev"
        }
    }
)
```

---

## State Fields

### Input (what agent reads):
```python
state["messages"]       # Conversation history
state["session_id"]     # Session ID
```

### Output (what agent updates):
```python
state["messages"]       # + AIMessage with clarification
state["final_answer"]   # Clarification question
state["next_agent"]     # "END"
state["last_agent"]     # "clarification"
```

---

## See Also

- [Clarification Design](./design.md) - How it works
- [API Reference](./api-reference.md) - Full API docs
- [Orchestrator Examples](../orchestrator/examples.md) - Routing examples
