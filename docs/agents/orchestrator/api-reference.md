# Master Orchestrator API Reference

## Class Definition

```python
class MasterOrchestrator(BaseAgent):
    def __init__(
        self,
        llm_client: BaseLLM,
        langfuse_client: Optional[any] = None,
        agent_config: Optional[dict] = None
    ):
        """Initialize orchestrator.

        Args:
            llm_client: LLM client configured with orchestrator-dotprompt model
            langfuse_client: Optional Langfuse client for observability
            agent_config: Optional agent configuration (name, prompt)
        """
```

**Location**: `src/agents/orchestrator.py:14`

## Constructor Parameters

- `llm_client` (BaseLLM, required): LLM client for generating routing decisions
- `langfuse_client` (Optional[any]): Langfuse client for prompt management and observability tracing
- `agent_config` (Optional[dict]): Configuration dictionary with the following keys:
  - `name` (str): Agent name for tracing. Default: `"orchestrator"`
  - `prompt` (dict): Prompt configuration for Langfuse
    - `provider` (str): Prompt provider, set to `"langfuse"` to use Langfuse
    - `id` (str): Prompt ID in Langfuse. Default: `"orchestrator_intent"`
    - `version` (int): Specific prompt version (optional)
    - `environment` (str): Prompt environment/label. Default: `"dev"`
  - `max_history` (int): Maximum conversation history to process. Default: `10`
  - `max_clarifications` (int): Maximum consecutive clarification turns before forcing research. Default: `2`

## Methods

### execute()

```python
def execute(self, state: AgentState) -> AgentState:
    """Analyze query and decide routing with three-layer protection against clarification loops.

    Protection layers:
    1. Counter limit: Max clarifications before forcing research
    2. Pattern detection: Detect AI->Human after clarification agent
    3. LLM decision: Context-aware prompt for intelligent routing

    Args:
        state: Current agent state

    Returns:
        State with next_agent set to "clarification" or "research"
    """
```

**Routing Logic**: The orchestrator uses a three-layer protection mechanism:

1. **Layer 1 - Counter Limit (Emergency Brake)**: If `clarification_count >= max_clarifications`, forces routing to research
2. **Layer 2 - Pattern Detection**: If last agent was clarification and user responded (AI→Human pattern), routes to research
3. **Layer 3 - LLM Decision**: Uses LLM to analyze query clarity and make routing decision

**Routing Outcomes**:
- Routes to `"clarification"` if query is vague/ambiguous (sets `clarification_needed = True`)
- Routes to `"research"` if query is clear (sets `clarification_needed = False`)

## State Schema

### Input State Fields

- `state["messages"]` (Sequence[BaseMessage]): Full conversation history
- `state["clarification_count"]` (int): Number of consecutive clarification turns
- `state.get("last_agent")` (Optional[str]): Previous agent that executed

### Output State Fields

- `state["next_agent"]` (str): Next agent to execute (`"clarification"` | `"research"`)
- `state["clarification_needed"]` (bool): Whether clarification is needed
- `state["missing_context"]` (List[str]): List of missing information (set if clarification needed)
- `state["clarification_count"]` (int): Updated counter (incremented on clarification, reset on research)
- `state["iteration"]` (int): Incremented iteration counter

## Configuration

### LLM Model
Configured via `llm_client` parameter. Recommended models:
- GPT-4 for nuanced intent classification
- GPT-3.5-turbo for cost-effective routing

### Prompt Template
- **Provider**: Langfuse (optional, falls back to direct LLM call)
- **Prompt ID**: `orchestrator_intent` (default)
- **Location**: `prompts/agent/orchestrator/v1.prompt` (if using dotprompt format)

### Environment Variables
No direct environment variables. Configuration passed via `agent_config`.

## Observability

### Langfuse Tracing
If `langfuse_client` is provided, the agent traces:
- **Name**: Value from `agent_config.name` (default: `"orchestrator"`)
- **Session ID**: Value from `state.get("session_id")`
- **Input**: `{"query": str, "history": str}`
- **Output**: Routing decision string
- **Model**: Value from `llm_client.completion_model`
- **Metadata**: `{"agent": "MasterOrchestrator"}`

## Error Handling

- **LLM failures**: Defaults to routing to `"research"`
- **Prompt fetch failures**: Falls back to direct LLM call
- **All errors logged**: Using structured logger with traceback

## Example Usage

```python
from tools.llm.client.selector import LLMClientSelector
from tools.observability.selector import ObservabilitySelector
from src.agents.orchestrator import MasterOrchestrator

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
    "name": "orchestrator",
    "max_history": 10,
    "max_clarifications": 2,
    "prompt": {
        "provider": "langfuse",
        "id": "orchestrator_intent",
        "environment": "production"
    }
}

# Initialize agent
orchestrator = MasterOrchestrator(
    llm_client=llm_client,
    langfuse_client=langfuse_client,
    agent_config=config
)

# Execute
result_state = orchestrator.execute(state)
print(f"Next agent: {result_state['next_agent']}")
```

## See Also

- [Clarification Agent API Reference](../clarification/api-reference.md)
- [Research Agent API Reference](../research/api-reference.md)
- [Agent State Schema](../../architecture/multi-agent-orchestration.md#state-schema)
