# Answer Synthesis Agent API Reference

## Class Definition

```python
class AnswerSynthesisAgent(BaseAgent):
    def __init__(
        self,
        llm_client: BaseLLM,
        langfuse_client: Optional[any] = None,
        agent_config: Optional[dict] = None
    ):
        """Initialize synthesis agent.

        Args:
            llm_client: LLM client configured with synthesis-dotprompt model
            langfuse_client: Optional Langfuse client for observability
            agent_config: Optional agent configuration (name, prompt)
        """
```

**Location**: `src/agents/synthesis.py:14`

## Constructor Parameters

- `llm_client` (BaseLLM, required): LLM client for generating final synthesized answers
- `langfuse_client` (Optional[any]): Langfuse client for prompt management and observability tracing
- `agent_config` (Optional[dict]): Configuration dictionary with the following keys:
  - `name` (str): Agent name for tracing. Default: `"synthesis"`
  - `prompt` (dict): Prompt configuration for Langfuse
    - `provider` (str): Prompt provider, set to `"langfuse"` to use Langfuse
    - `id` (str): Prompt ID in Langfuse. Default: `"synthesis"`
    - `version` (int): Specific prompt version (optional)
    - `environment` (str): Prompt environment/label. Default: `"dev"`
  - `max_history` (int): Maximum conversation history to process. Default: `10`

## Methods

### execute()

```python
def execute(self, state: AgentState) -> AgentState:
    """Synthesize coherent answer from tool results.

    Args:
        state: Current agent state

    Returns:
        State with synthesized final_answer and confidence_score
    """
```

**Behavior**:
1. Extracts user query from message history (first HumanMessage)
2. Retrieves research observations and final output from `state["context"]`
3. Combines all observations into single context string
4. Uses LLM to synthesize coherent, well-formatted answer
5. Calculates confidence score based on number of observations
6. Appends AIMessage with final answer to message history
7. Sets `next_agent = "END"` to complete workflow

**Fallback**: On error, returns research output directly or generic error message

### _calculate_confidence()

```python
def _calculate_confidence(self, observations: list) -> float:
    """Calculate confidence score based on observations.

    Args:
        observations: List of observation strings

    Returns:
        Confidence score between 0.0 and 1.0
    """
```

**Confidence Calculation Logic**:
- 0 observations → 0.0 (no information found)
- 1 observation → 0.6 (single source)
- 2 observations → 0.8 (multiple sources)
- 3+ observations → 0.95 (comprehensive research)

## State Schema

### Input State Fields

- `state["messages"]` (Sequence[BaseMessage]): Full conversation history
- `state["context"]["observations"]` (List[str]): Tool execution summaries from research
- `state["context"]["final_output"]` (str): Final research output
- `state.get("session_id")` (str): Session ID for tracing

### Output State Fields

- `state["messages"]` (Sequence[BaseMessage]): Updated with final AIMessage containing synthesized answer
- `state["final_answer"]` (str): Synthesized answer text
- `state["confidence_score"]` (float): Confidence score (0.0-1.0)
- `state["next_agent"]` (str): Set to `"END"` (completes workflow)
- `state["last_agent"]` (str): Set to `"synthesis"`

### Error State

On failure:
- `state["final_answer"]` = Research output or "I encountered an error while processing your request."
- `state["confidence_score"]` = 0.0
- `state["next_agent"]` = `"END"`

## Configuration

### LLM Model
Configured via `llm_client` parameter. Recommended models:
- **GPT-4**: Best quality, coherent answers
- **GPT-4-turbo**: Faster with good quality
- **Claude-3**: Strong at long-form synthesis
- **GPT-3.5-turbo**: Fast and cheap (acceptable quality)

### Prompt Template
- **Provider**: Langfuse (optional, falls back to direct LLM call)
- **Prompt ID**: `synthesis` (default)
- **Location**: `prompts/agent/synthesis/v1.prompt` (if using dotprompt format)
- **Variables**:
  - `query` (str): Original user query
  - `observations` (str): Combined observations and research output

### Environment Variables
No direct environment variables. Configuration passed via `agent_config`.

## Observability

### Langfuse Tracing
If `langfuse_client` is provided, the agent traces:
- **Name**: Value from `agent_config.name` (default: `"synthesis"`)
- **Session ID**: Value from `state.get("session_id")`
- **Input**: `{"query": str, "observations": str}`
- **Output**: Synthesized answer
- **Model**: Value from `llm_client.completion_model`
- **Metadata**: `{"agent": "AnswerSynthesisAgent"}`

## Error Handling

- **LLM failures**: Returns research output or generic error message
- **Prompt fetch failures**: Falls back to direct LLM call
- **Missing observations**: Handles gracefully with "No observations available"
- **All errors logged**: Using structured logger with traceback

## Example Usage

```python
from tools.llm.client.selector import LLMClientSelector
from tools.observability.selector import ObservabilitySelector
from src.agents.synthesis import AnswerSynthesisAgent
from src.graph.state import AgentState
from langchain_core.messages import HumanMessage, AIMessage

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
    "name": "synthesis",
    "max_history": 10,
    "prompt": {
        "provider": "langfuse",
        "id": "synthesis",
        "environment": "production"
    }
}

# Initialize agent
synthesis_agent = AnswerSynthesisAgent(
    llm_client=llm_client,
    langfuse_client=langfuse_client,
    agent_config=config
)

# Prepare state with research results
state = AgentState(
    messages=[
        HumanMessage(content="What are the benefits of RAG?"),
        AIMessage(content="Research output...")
    ],
    session_id="session-123",
    next_agent="synthesis",
    last_agent="research",
    iteration=2,
    context={
        "observations": [
            "Used tool: pdf_retrieval",
            "Used tool: web_search"
        ],
        "tool_history": ["pdf_retrieval", "web_search"],
        "final_output": "RAG combines retrieval with generation..."
    },
    clarification_needed=False,
    missing_context=[],
    clarification_count=0,
    final_answer=None,
    confidence_score=None
)

# Execute
result_state = synthesis_agent.execute(state)
print(f"Answer: {result_state['final_answer']}")
print(f"Confidence: {result_state['confidence_score']}")
print(f"Next agent: {result_state['next_agent']}")  # "END"
```

## Output Format

The synthesis agent should produce:

1. **Well-structured answers**: Clear paragraphs, bullet points where appropriate
2. **Source attribution**: Mention if information came from documents or web
3. **Comprehensive coverage**: Address all aspects of the user's query
4. **Natural language**: Conversational tone, not robotic
5. **Error transparency**: If research failed, explain what went wrong

## Best Practices

1. **Prompt engineering**: Design synthesis prompt to produce desired format (markdown, citations, etc.)
2. **Context window**: Monitor combined observation length to avoid token overflow
3. **Confidence scoring**: Adjust `_calculate_confidence()` logic based on your quality metrics
4. **Error messages**: Provide helpful error messages that guide users on next steps
5. **Quality assurance**: Log low-confidence answers for review

## See Also

- [Research Agent API Reference](../research/api-reference.md)
- [Agent State Schema](../../architecture/multi-agent-orchestration.md#state-schema)
- [Workflow Completion](../../architecture/multi-agent-orchestration.md#end-state)
