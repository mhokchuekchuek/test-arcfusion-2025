# Observability Tools

Tools for monitoring, tracing, and debugging LLM applications.

## Available Tools

### Langfuse

**Purpose**: End-to-end LLM observability and prompt management

**Features**:
- Trace LLM calls and agent executions
- Track token usage and costs
- Manage prompts with versioning
- Debug complex multi-agent workflows
- Session grouping for conversations

**Quick Start**:
```python
from tools.observability.selector import ObservabilitySelector

langfuse = ObservabilitySelector.create(
    provider="langfuse",
    public_key="pk-lf-...",
    secret_key="sk-lf-..."
)

# Trace generation
langfuse.trace_generation(
    name="research_agent",
    input_data={"query": "What is RAG?"},
    output="RAG stands for...",
    model="gpt-4",
    session_id="session-123"
)
```

**Documentation**:
- [Langfuse API Reference](./langfuse/api-reference.md)

---

## What Gets Traced

### Agent Executions

```python
# Automatically traced by agents
- Agent name
- Input messages
- Output response
- Model used
- Session ID
- Custom metadata
```

### LLM Calls

```python
# Traced by LLM client
- Prompt
- Completion
- Token usage
- Latency
- Cost
```

### Tool Calls

```python
# Research agent traces
- Tools used
- Tool inputs/outputs
- Number of steps
```

---

## Configuration

```bash
# Langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional
```

---

## Common Use Cases

### 1. Debug Agent Workflows

View complete execution trace:
- Which agents were triggered
- What tools were called
- How state flowed through system

### 2. Monitor Production

Track metrics:
- Token usage per session
- Average response time
- Error rates
- Model distribution

### 3. Prompt Engineering

Manage prompts:
- Version control
- A/B testing
- Rollback to previous versions
- Environment-specific prompts

### 4. Cost Tracking

Monitor spending:
- Costs per user/session
- Most expensive queries
- Model comparison

---

## Integration Points

### Agents

All agents automatically trace to Langfuse:
```python
# In agent.execute()
self.langfuse_client.trace_generation(
    name=self.agent_name,
    input_data=input,
    output=output,
    session_id=state["session_id"]
)
```

### RAG Service

Traces retrieval and generation:
```python
# Trace retrieval
langfuse.trace("pdf_retrieval", query, results)

# Trace generation
langfuse.trace_generation("synthesis", context, answer)
```

---

## Related Documentation

- [Tools Overview](../README.md)
- [Prompt Management](../../prompts/README.md)
- [Agent Observability](../../agents/README.md#observability)
