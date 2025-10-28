# Langfuse Observability API Reference

LLM observability and prompt management client for tracing, monitoring, and debugging agent executions.

## Class Definition

```python
from tools.observability.langfuse.main import LangfuseClient

class LangfuseClient(BaseObservability):
    """Client for Langfuse observability and prompt management."""
```

**File**: `tools/observability/langfuse/main.py`

**Reference**: https://langfuse.com/docs

## Constructor

### `__init__(public_key=None, secret_key=None, host=None)`

Initialize Langfuse client for observability and prompt management.

```python
langfuse = LangfuseClient(
    public_key="pk-...",
    secret_key="sk-...",
    host="https://cloud.langfuse.com"
)
```

#### Parameters

- `public_key` (str, optional): Langfuse public API key
  - Default: From `LANGFUSE_PUBLIC_KEY` environment variable
  - Get from: https://cloud.langfuse.com (Settings → API Keys)

- `secret_key` (str, optional): Langfuse secret API key
  - Default: From `LANGFUSE_SECRET_KEY` environment variable
  - Keep secure, never commit to Git

- `host` (str, optional): Langfuse host URL
  - Default: From `LANGFUSE_HOST` env var, or `"http://localhost:3000"`
  - Cloud: `"https://cloud.langfuse.com"`
  - Self-hosted: `"http://your-langfuse-instance:3000"`

#### Raises

- `ValueError`: If public_key or secret_key are missing

#### Example

```python
from tools.observability.selector import ObservabilitySelector

# From environment variables
langfuse = ObservabilitySelector.create(provider="langfuse")

# Or explicit credentials
langfuse = ObservabilitySelector.create(
    provider="langfuse",
    public_key="pk-...",
    secret_key="sk-...",
    host="https://cloud.langfuse.com"
)
```

## Methods

### `get_prompt(name, version=None, label=None)`

Retrieve a prompt from Langfuse prompt management.

#### Parameters

- `name` (str, required): Prompt name
  - Example: `"agent_orchestrator"`, `"agent_research"`
  - Matches uploaded prompt names

- `version` (int, optional): Specific version number
  - Example: `1`, `2`, `3`
  - Use for pinned versions

- `label` (str, optional): Environment label
  - Options: `"production"`, `"staging"`, `"dev"`
  - Default: Latest version for that label

#### Returns

Prompt object with:
- `prompt` (str): Template content with variables
- `config` (dict): Metadata (model, temperature, etc.)
- `compile(**kwargs)`: Method to render template with variables

#### Raises

- `Exception`: If prompt not found or API error

#### Example

```python
from tools.observability.selector import ObservabilitySelector

langfuse = ObservabilitySelector.create(provider="langfuse")

# Get latest production prompt
prompt = langfuse.get_prompt("agent_orchestrator", label="production")

# Compile with variables
compiled = prompt.compile(
    query="What is RAG?",
    history="Previous conversation..."
)

# Use in LLM call
response = llm.generate(compiled)
```

### `trace_generation(name, input_data, output, model, metadata=None, session_id=None)`

Trace an LLM generation call for observability.

#### Parameters

- `name` (str, required): Name of the generation
  - Example: `"orchestrator_decision"`, `"research_agent"`
  - Appears in Langfuse dashboard

- `input_data` (dict, required): Input to the LLM
  - Prompt variables, messages, context
  - Example: `{"query": "...", "history": "..."}`

- `output` (str, required): LLM response
  - Generated text from the model

- `model` (str, required): Model identifier
  - Example: `"gpt-4-turbo"`, `"claude-3-5-sonnet"`

- `metadata` (dict, optional): Additional metadata
  - Custom fields for filtering/analysis
  - Example: `{"agent": "orchestrator", "iteration": 1}`

- `session_id` (str, optional): Session identifier
  - Groups traces by conversation
  - Also used as trace_id (deterministic)
  - Example: `"user-123-conv-456"`

#### Returns

None (traces sent asynchronously)

#### Example

```python
from tools.observability.selector import ObservabilitySelector

langfuse = ObservabilitySelector.create(provider="langfuse")

# Trace LLM generation
langfuse.trace_generation(
    name="orchestrator_decision",
    input_data={
        "query": "What is RAG?",
        "history": "Previous conversation..."
    },
    output="RESEARCH",
    model="gpt-4-turbo",
    metadata={"agent": "orchestrator", "temperature": 0.3},
    session_id="user-123-conv-1"
)
```

### `flush()`

Flush pending traces to Langfuse (send immediately).

#### Returns

None

#### Example

```python
# Trace multiple generations
langfuse.trace_generation(...)
langfuse.trace_generation(...)

# Ensure all traces are sent
langfuse.flush()
```

## Configuration

### Environment Variables

```bash
# Required
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...

# Optional
LANGFUSE_HOST=https://cloud.langfuse.com  # Default: http://localhost:3000
```

### Dependencies

- `langfuse`: Official Langfuse Python SDK
  ```bash
  pip install langfuse
  ```

## Usage Patterns

### Prompt Management

```python
from tools.observability.selector import ObservabilitySelector

# Initialize client
langfuse = ObservabilitySelector.create(provider="langfuse")

# Fetch prompt
prompt = langfuse.get_prompt("agent_orchestrator", label="production")

# Compile with variables
compiled = prompt.compile(
    query="What is RAG?",
    history="User: Hello\nAssistant: Hi there!"
)

# Use compiled prompt in LLM call
from tools.llm.client.selector import LLMClientSelector
llm = LLMClientSelector.create(provider="litellm")
response = llm.generate(compiled)
```

### Agent Tracing

```python
from tools.observability.selector import ObservabilitySelector

langfuse = ObservabilitySelector.create(provider="langfuse")

# Agent makes decision
input_data = {
    "query": user_query,
    "history": conversation_history,
    "clarification_count": state.get("clarification_count", 0)
}

# Call LLM
decision = llm.generate(prompt_variables=input_data)

# Trace the generation
langfuse.trace_generation(
    name="orchestrator_decision",
    input_data=input_data,
    output=decision,
    model="gpt-4-turbo",
    metadata={
        "agent": "orchestrator",
        "temperature": 0.3,
        "next_agent": decision
    },
    session_id=session_id
)

# Flush to ensure sent
langfuse.flush()
```

### Multi-Agent Workflow Tracing

```python
from tools.observability.selector import ObservabilitySelector

langfuse = ObservabilitySelector.create(provider="langfuse")
session_id = "user-123-conv-1"

# Trace orchestrator
langfuse.trace_generation(
    name="orchestrator",
    input_data={"query": query},
    output="RESEARCH",
    model="gpt-4-turbo",
    session_id=session_id
)

# Trace research agent
langfuse.trace_generation(
    name="research_agent",
    input_data={"query": query, "tools": ["pdf", "web"]},
    output="Retrieved 5 documents...",
    model="gpt-4-turbo",
    session_id=session_id
)

# Trace synthesis
langfuse.trace_generation(
    name="synthesis",
    input_data={"observations": observations},
    output="Final answer: RAG is...",
    model="gpt-4-turbo",
    session_id=session_id
)

# All traces grouped by session_id in Langfuse dashboard
langfuse.flush()
```

## Features

### Prompt Management

- **Versioning**: Track prompt evolution over time
- **Labels**: Environment-specific prompts (dev, staging, production)
- **A/B Testing**: Compare prompt performance
- **Centralized**: Single source of truth for all prompts
- **Compilation**: Template variables rendered at runtime

### Observability & Tracing

- **Generation Traces**: Track every LLM call
- **Session Grouping**: Group traces by conversation
- **Metadata**: Custom fields for filtering and analysis
- **Input/Output**: Full visibility into LLM behavior
- **Model Tracking**: See which models were used

### Analytics

- **Latency**: Track response times
- **Token Usage**: Monitor costs
- **Success Rates**: Track failures and errors
- **User Sessions**: Analyze conversation patterns

## Integration Examples

### With Agents

```python
# In src/agents/orchestrator.py
from tools.observability.selector import ObservabilitySelector

class OrchestratorAgent:
    def __init__(self, langfuse_client):
        self.langfuse = langfuse_client

    def execute(self, state):
        # Get prompt
        prompt = self.langfuse.get_prompt(
            "agent_orchestrator",
            label="production"
        )

        # Compile
        compiled = prompt.compile(
            query=state["query"],
            history=state["history"]
        )

        # Generate
        decision = self.llm.generate(compiled)

        # Trace
        self.langfuse.trace_generation(
            name="orchestrator_decision",
            input_data={"query": state["query"]},
            output=decision,
            model="gpt-4-turbo",
            session_id=state["session_id"]
        )

        return decision
```

### With Prompt Uploader

```python
# In prompts/uploader.py
from tools.observability.selector import ObservabilitySelector

langfuse = ObservabilitySelector.create(provider="langfuse")

# Upload prompt to Langfuse
langfuse.client.create_prompt(
    name="agent_orchestrator",
    prompt=template_content,
    config={"model": "gpt-4-turbo", "temperature": 0.3},
    labels=["production"],
    tags=["v1", "agent"]
)
```

---

## See Also

- [Observability Selector](../../selector.py) - Factory for creating observability clients
- [Base Observability](../../base.py) - Abstract base class
- [Langfuse Documentation](https://langfuse.com/docs) - Official docs
- [Prompt Management](../../../../prompts/README.md) - Prompt versioning system
- [Agent Implementation](../../../../../src/agents/orchestrator.py) - Agent using Langfuse
