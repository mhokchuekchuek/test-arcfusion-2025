# Answer Synthesis Agent Examples

Simple, practical examples showing how to use the synthesis agent.

## Basic Usage

```python
from langchain_core.messages import HumanMessage
from src.graph.state import create_initial_state
from src.agents.synthesis import AnswerSynthesisAgent
from tools.llm.client.selector import LLMClientSelector

# Create LLM client
llm_client = LLMClientSelector.create(
    provider="litellm",
    completion_model="gpt-4-turbo"
)

# Create synthesis agent
synthesis = AnswerSynthesisAgent(
    llm_client=llm_client,
    agent_config={"name": "synthesis", "max_history": 10}
)

# Create state with research results
state = create_initial_state(
    messages=[HumanMessage(content="What is DAIL-SQL?")],
    session_id="session-123"
)

# Add research results to context
state["context"]["observations"] = ["Used tool: pdf_retrieval"]
state["context"]["final_output"] = "DAIL-SQL is a text-to-SQL approach..."

# Execute
result = synthesis.execute(state)

# Check result
print(result["final_answer"])        # Synthesized answer
print(result["confidence_score"])    # 0.0-1.0
print(result["next_agent"])          # "END"
```

---

## With Citations

```python
# Research output with source information
state = create_initial_state(
    messages=[HumanMessage(content="What accuracy is in Table 2?")],
    session_id="session-456"
)

state["context"]["observations"] = ["Used tool: pdf_retrieval"]
state["context"]["final_output"] = """
Found in Zhang et al. 2024, Table 2:
- Accuracy: 87.2%
- Dataset: Spider
"""

result = synthesis.execute(state)

print(result["final_answer"])
# → "According to Zhang et al. 2024 Table 2, the accuracy is 87.2% on the Spider dataset."
```

---

## Multiple Observations

```python
# Research with multiple tool calls
state = create_initial_state(
    messages=[HumanMessage(content="Find SOTA and authors")],
    session_id="multi"
)

state["context"]["observations"] = [
    "Used tool: pdf_retrieval",
    "Used tool: web_search"
]
state["context"]["final_output"] = """
PDF: DAIL-SQL achieves state-of-the-art
Web: Authors are Dawei Gao and Haibin Wang
"""

result = synthesis.execute(state)

print(result["final_answer"])
# → "DAIL-SQL achieves state-of-the-art performance. The authors are Dawei Gao and Haibin Wang."
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

# Create synthesis agent with Langfuse
synthesis = AnswerSynthesisAgent(
    llm_client=llm_client,
    langfuse_client=langfuse,
    agent_config={
        "name": "synthesis",
        "max_history": 10,
        "prompt": {
            "provider": "langfuse",
            "id": "agent_synthesis",
            "environment": "production"
        }
    }
)

# Execute
result = synthesis.execute(state)

# Langfuse automatically traces:
# - Query
# - Observations
# - Final answer
# - Session: "session-id"
```

---

## Empty Observations (Fallback)

```python
# No research results available
state = create_initial_state(
    messages=[HumanMessage(content="What is RAG?")],
    session_id="empty"
)

# Empty context
state["context"]["observations"] = []
state["context"]["final_output"] = ""

result = synthesis.execute(state)

# Agent still generates answer
print(result["final_answer"])
# Uses "No observations available" in prompt
```

---

## Error Handling

```python
# Synthesis agent handles errors gracefully

try:
    result = synthesis.execute(state)
except Exception:
    pass  # Caught internally

# Fallback to research output
print(result["final_answer"])
# Uses final_output or error message
print(result["confidence_score"])  # 0.0
```

---

## History Limiting

```python
# Long conversation - agent only uses last N messages

messages = []
for i in range(20):  # 20 messages
    messages.append(HumanMessage(content=f"Question {i}"))
messages.append(HumanMessage(content="What is the accuracy?"))

state = create_initial_state(messages=messages, session_id="long")
state["context"]["final_output"] = "Accuracy is 87.2%"

# Synthesis agent with max_history=10
synthesis = AnswerSynthesisAgent(
    llm_client=llm_client,
    agent_config={"max_history": 10}
)

result = synthesis.execute(state)
# Uses only last 10 messages for context
```

---

## Testing

```python
def test_synthesis_agent():
    """Test synthesis agent formats answer."""
    # Mock LLM
    class MockLLM:
        completion_model = "gpt-4"
        def generate(self, **kwargs):
            return "The accuracy is 87.2% according to Table 2."

    # Create agent
    synthesis = AnswerSynthesisAgent(
        llm_client=MockLLM(),
        agent_config={"name": "test"}
    )

    # Create state
    state = create_initial_state(
        messages=[HumanMessage(content="What is accuracy?")],
        session_id="test"
    )
    state["context"]["observations"] = ["Used tool: pdf_retrieval"]
    state["context"]["final_output"] = "Found 87.2% in Table 2"

    # Execute
    result = synthesis.execute(state)

    # Assert
    assert result["next_agent"] == "END"
    assert result["last_agent"] == "synthesis"
    assert result["final_answer"] is not None
    assert result["confidence_score"] is not None
```

---

## Configuration Options

```python
synthesis = AnswerSynthesisAgent(
    llm_client=llm_client,
    langfuse_client=langfuse,  # Optional
    agent_config={
        "name": "synthesis",      # Agent name for tracing
        "max_history": 10,        # Number of messages to consider
        "prompt": {               # Langfuse prompt config
            "provider": "langfuse",
            "id": "agent_synthesis",
            "version": None,      # None = latest
            "environment": "production"
        }
    }
)
```

---

## State Fields

### Input (what synthesis reads):
```python
state["messages"]                  # Conversation history
state["session_id"]                # Session ID
state["context"]["observations"]   # Tool usage list
state["context"]["final_output"]   # Research results
```

### Output (what synthesis updates):
```python
state["messages"]          # + AIMessage with answer
state["final_answer"]      # Formatted answer
state["confidence_score"]  # 0.0-1.0
state["next_agent"]        # "END"
state["last_agent"]        # "synthesis"
```

---

## Confidence Score

The agent calculates confidence based on observations:

```python
# High confidence: Multiple tools used
state["context"]["observations"] = [
    "Used tool: pdf_retrieval",
    "Used tool: web_search"
]
# → confidence_score: 0.9

# Medium confidence: Single tool
state["context"]["observations"] = ["Used tool: pdf_retrieval"]
# → confidence_score: 0.7

# Low confidence: No observations
state["context"]["observations"] = []
# → confidence_score: 0.3
```

---

## Formatting Tips

The synthesis agent:
- **Adds citations** when sources are mentioned
- **Combines information** from multiple tools
- **Formats answers** in natural language
- **Includes metadata** (source, page, table)

Example transformations:

| Research Output | Synthesized Answer |
|-----------------|-------------------|
| "Found in Zhang et al. Table 2: 87.2%" | "According to Zhang et al. (Table 2), the accuracy is 87.2%." |
| "PDF: DAIL-SQL\nWeb: Authors..." | "DAIL-SQL was developed by..." |
| "Tool: pdf_retrieval\nResult: ..." | "[Formatted answer with citation]" |

---

## See Also

- [Synthesis Design](./design.md) - How it works
- [API Reference](./api-reference.md) - Full API docs
- [Research Examples](../research/examples.md) - Previous step before synthesis
