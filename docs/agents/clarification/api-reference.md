# Clarification Agent API Reference

## Class Definition

```python
class ClarificationAgent(BaseAgent):
    def __init__(
        self,
        llm_client: BaseLLM,
        langfuse_client: Optional[any] = None,
        agent_config: Optional[dict] = None
    ):
        """Initialize clarification agent.

        Args:
            llm_client: LLM client configured with clarification-dotprompt model
            langfuse_client: Optional Langfuse client for observability
            agent_config: Optional agent configuration (name, prompt)
        """
```

**Location**: `src/agents/clarification.py:14`

## Constructor Parameters

- `llm_client` (BaseLLM, required): LLM client for generating clarifying questions
- `langfuse_client` (Optional[any]): Langfuse client for prompt management and observability tracing
- `agent_config` (Optional[dict]): Configuration dictionary with the following keys:
  - `name` (str): Agent name for tracing. Default: `"clarification"`
  - `prompt` (dict): Prompt configuration for Langfuse
    - `provider` (str): Prompt provider, set to `"langfuse"` to use Langfuse
    - `id` (str): Prompt ID in Langfuse. Default: `"clarification"`
    - `version` (int): Specific prompt version (optional)
    - `environment` (str): Prompt environment/label. Default: `"dev"`
  - `max_history` (int): Maximum conversation history to process. Default: `10`

## Methods

### execute()

```python
def execute(self, state: AgentState) -> AgentState:
    """Generate clarifying question for vague query.

    Args:
        state: Current agent state

    Returns:
        State with clarifying question as final_answer
    """
```

**Behavior**:
1. Extracts current query from last message in history
2. Formats conversation history for context
3. Uses LLM to generate targeted clarifying question
4. Appends AIMessage with clarification to message history
5. Sets `next_agent = "END"` to return control to user

**Fallback**: On any error, returns generic clarification: "Could you please provide more details about your question?"

## State Schema

### Input State Fields

- `state["messages"]` (Sequence[BaseMessage]): Full conversation history
- `state.get("session_id")` (str): Session ID for tracing

### Output State Fields

- `state["messages"]` (Sequence[BaseMessage]): Updated with new AIMessage containing clarification question
- `state["final_answer"]` (str): The clarifying question text
- `state["next_agent"]` (str): Set to `"END"` (returns control to user)
- `state["last_agent"]` (str): Set to `"clarification"` (for pattern detection)

## Configuration

### LLM Model
Configured via `llm_client` parameter. Recommended models:
- GPT-4 for nuanced, context-aware questions
- GPT-3.5-turbo for cost-effective clarifications

### Prompt Template
- **Provider**: Langfuse (optional, falls back to direct LLM call)
- **Prompt ID**: `clarification` (default)
- **Location**: `prompts/agent/clarification/v1.prompt` (if using dotprompt format)
- **Variables**:
  - `query` (str): Current user query
  - `history` (str): Formatted conversation history

### Environment Variables
No direct environment variables. Configuration passed via `agent_config`.

## Observability

### Langfuse Tracing
If `langfuse_client` is provided, the agent traces:
- **Name**: Value from `agent_config.name` (default: `"clarification"`)
- **Session ID**: Value from `state.get("session_id")`
- **Input**: `{"query": str, "history": str}`
- **Output**: Generated clarification question
- **Model**: Value from `llm_client.completion_model`
- **Metadata**: `{"agent": "ClarificationAgent"}`

## Error Handling

- **LLM failures**: Returns fallback message: "Could you please provide more details about your question?"
- **Prompt fetch failures**: Falls back to direct LLM call
- **All errors logged**: Using structured logger with traceback

## Example Usage

```python
from tools.llm.client.selector import LLMClientSelector
from tools.observability.selector import ObservabilitySelector
from src.agents.clarification import ClarificationAgent
from src.graph.state import AgentState
from langchain_core.messages import HumanMessage

# Create dependencies
llm_client = LLMClientSelector.create(
    provider="litellm",
    model="gpt-4"
)

langfuse_client = ObservabilitySelector.create(
    provider="langfuse",
    public_key="pk-...",
    secret_key="sk-..."
)

# Configure agent
config = {
    "name": "clarification",
    "max_history": 10,
    "prompt": {
        "provider": "langfuse",
        "id": "clarification",
        "environment": "production"
    }
}

# Initialize agent
clarification_agent = ClarificationAgent(
    llm_client=llm_client,
    langfuse_client=langfuse_client,
    agent_config=config
)

# Prepare state with vague query
state = AgentState(
    messages=[HumanMessage(content="Tell me about AI")],
    session_id="session-123",
    next_agent="clarification",
    last_agent="orchestrator",
    iteration=1,
    context={},
    clarification_needed=True,
    missing_context=["Query is vague"],
    clarification_count=1,
    final_answer=None,
    confidence_score=None
)

# Execute
result_state = clarification_agent.execute(state)
print(f"Clarification: {result_state['final_answer']}")
print(f"Next agent: {result_state['next_agent']}")  # "END"
```

## Best Practices

1. **Keep questions focused**: The LLM should ask about ONE missing piece of information
2. **Provide context**: Include conversation history so clarifications build on previous exchanges
3. **Limit clarification loops**: Use orchestrator's `max_clarifications` to prevent infinite loops
4. **Track last_agent**: The `last_agent = "clarification"` field helps orchestrator detect follow-up responses

## See Also

- [Master Orchestrator API Reference](../orchestrator/api-reference.md)
- [Clarification Loop Prevention](../../architecture/multi-agent-orchestration.md#clarification-protection)
- [Agent State Schema](../../architecture/multi-agent-orchestration.md#state-schema)
