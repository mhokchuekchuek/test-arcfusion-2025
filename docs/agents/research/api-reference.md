# Research Supervisor API Reference

## Class Definition

```python
class ResearchSupervisor(BaseAgent):
    def __init__(
        self,
        llm,
        tools: List[BaseTool],
        langfuse_client: Optional[any] = None,
        agent_config: Optional[dict] = None
    ):
        """Initialize research supervisor.

        Args:
            llm: LangChain-compatible model (e.g., ChatOpenAI) configured with research-dotprompt
            tools: List of tools (PDFRetrievalTool, WebSearchTool)
            langfuse_client: Optional Langfuse client for observability
            agent_config: Optional agent configuration (name, prompt)
        """
```

**Location**: `src/agents/research.py:14`

## Constructor Parameters

- `llm` (ChatModel, required): LangChain-compatible model (e.g., `ChatOpenAI`, `ChatAnthropic`)
  - Used with `langchain.agents.create_agent()` for ReAct pattern
- `tools` (List[BaseTool], required): List of LangChain tools for research
  - `PDFRetrievalTool`: Retrieves relevant documents from vector store
  - `WebSearchTool`: Performs web searches via Tavily
- `langfuse_client` (Optional[any]): Langfuse client for prompt management and observability tracing
- `agent_config` (Optional[dict]): Configuration dictionary with the following keys:
  - `name` (str): Agent name for tracing. Default: `"research"`
  - `prompt` (dict): Prompt configuration for Langfuse
    - `provider` (str): Prompt provider, set to `"langfuse"` to use Langfuse
    - `id` (str): Prompt ID in Langfuse. Default: `"agent_research"`
    - `version` (int): Specific prompt version (optional)
    - `environment` (str): Prompt environment/label. Default: `"dev"`
  - `max_history` (int): Maximum conversation history to process. Default: `10`

## Architecture

The Research Supervisor uses the **ReAct pattern** (Reasoning + Acting):

1. **Reasoning**: LLM decides which tool to use and why
2. **Acting**: Executes selected tool and observes result
3. **Iteration**: Repeats until LLM decides it has sufficient information
4. **Final Answer**: Generates response based on accumulated observations

Built using LangChain v1.0's `create_agent()` (LangGraph-based, replacing deprecated `create_react_agent`).

## Methods

### execute()

```python
def execute(self, state: AgentState) -> AgentState:
    """Execute research with ReAct loop.

    Args:
        state: Current agent state

    Returns:
        Updated state with research observations and final output
    """
```

**Behavior**:
1. Invokes LangChain agent with message history (limited by `max_history`)
2. Agent autonomously selects and chains tools using ReAct pattern
3. Extracts tool call information from agent messages
4. Stores observations and tool history in `state["context"]`
5. Appends only final AI response to message history (filters out intermediate tool messages)
6. Routes to synthesis agent

**Tool Selection**: The LLM autonomously decides:
- Which tools to use (PDF retrieval, web search)
- How many tools to call
- In what sequence
- When to stop and generate final answer

## State Schema

### Input State Fields

- `state["messages"]` (Sequence[BaseMessage]): Full conversation history
- `state.get("session_id")` (str): Session ID for tracing

### Output State Fields

- `state["messages"]` (Sequence[BaseMessage]): Updated with final AI response (not intermediate tool messages)
- `state["context"]["observations"]` (List[str]): List of tool execution summaries
- `state["context"]["tool_history"]` (List[str]): List of tool names used (e.g., `["pdf_retrieval", "web_search"]`)
- `state["context"]["final_output"]` (str): Final research output from agent
- `state["next_agent"]` (str): Set to `"synthesis"`
- `state["last_agent"]` (str): Set to `"research"`
- `state["iteration"]` (int): Incremented iteration counter

### Error State

On failure:
- `state["context"]["observations"]` = `[f"Research failed: {error}"]`
- `state["context"]["final_output"]` = `"Unable to complete research due to an error."`
- `state["next_agent"]` = `"synthesis"` (still routes to synthesis)

## Configuration

### LLM Model
Configured via `llm` parameter. Recommended models:
- **GPT-4**: Best reasoning, tool selection, and planning
- **Claude-3**: Strong reasoning with cost efficiency
- **GPT-3.5-turbo**: Fast and cheap (may miss optimal tool selection)

### System Prompt
- **Provider**: Langfuse (optional, falls back to LangChain default)
- **Prompt ID**: `agent_research` (default)
- **Location**: `prompts/agent/research/v1.prompt` (if using dotprompt format)
- **Content**: Instructs agent on:
  - When to use PDF retrieval vs web search
  - How to chain multiple tools
  - When to stop researching

### Tools
Must be LangChain `BaseTool` implementations:
```python
tools = [
    PDFRetrievalTool(vector_store=vector_store),
    WebSearchTool(tavily_client=tavily_client)
]
```

### Environment Variables
No direct environment variables. Configuration passed via `agent_config`.

## Observability

### Langfuse Tracing
If `langfuse_client` is provided, the agent traces:
- **Name**: Value from `agent_config.name` (default: `"research"`)
- **Session ID**: Value from `state.get("session_id")`
- **Input**: First N messages (up to `max_history`)
- **Output**: Final research output string
- **Model**: Value from `llm.model_name` (if available)
- **Metadata**:
  - `agent`: `"ResearchSupervisor"`
  - `tools_used`: List of tool names
  - `num_observations`: Count of observations

## Error Handling

- **Agent execution failures**: Routes to synthesis with error context
- **Tool failures**: Handled by LangChain agent (reported as tool errors)
- **Prompt fetch failures**: Falls back to LangChain default system prompt
- **All errors logged**: Using structured logger with traceback

## Example Usage

```python
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool
from tools.observability.selector import ObservabilitySelector
from src.agents.research import ResearchSupervisor
from src.agents.tools.pdf_retrieval import PDFRetrievalTool
from src.agents.tools.web_search import WebSearchTool

# Create LangChain model
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.0
)

# Create tools
tools = [
    PDFRetrievalTool(vector_store=vector_store),
    WebSearchTool(api_key="tvly-...")
]

# Create observability client
langfuse_client = ObservabilitySelector.create(
    provider="langfuse",
    public_key="pk-...",
    secret_key="sk-..."
)

# Configure agent
config = {
    "name": "research",
    "max_history": 10,
    "prompt": {
        "provider": "langfuse",
        "id": "agent_research",
        "environment": "production"
    }
}

# Initialize agent
research_agent = ResearchSupervisor(
    llm=llm,
    tools=tools,
    langfuse_client=langfuse_client,
    agent_config=config
)

# Execute
result_state = research_agent.execute(state)
print(f"Tools used: {result_state['context']['tool_history']}")
print(f"Observations: {len(result_state['context']['observations'])}")
print(f"Final output: {result_state['context']['final_output']}")
print(f"Next agent: {result_state['next_agent']}")  # "synthesis"
```

## Tool Integration

### PDFRetrievalTool
Retrieves documents from vector store:
```python
from src.agents.tools.pdf_retrieval import PDFRetrievalTool

tool = PDFRetrievalTool(
    vector_store=qdrant_client,
    collection_name="documents",
    top_k=5
)
```

**Location**: `src/agents/tools/pdf_retrieval.py`

### WebSearchTool
Performs web searches:
```python
from src.agents.tools.web_search import WebSearchTool

tool = WebSearchTool(
    api_key="tvly-...",
    max_results=5
)
```

**Location**: `src/agents/tools/web_search.py`

## Best Practices

1. **Provide clear system prompts**: Guide the agent on when to use each tool
2. **Limit history**: Use `max_history` to prevent token overflow on long conversations
3. **Tool naming**: Use descriptive tool names and descriptions for better LLM understanding
4. **Error handling**: Always route to synthesis even on failure (let synthesis explain the error)
5. **Observe tool usage**: Monitor `tool_history` to understand agent behavior

## See Also

- [Synthesis Agent API Reference](../synthesis/api-reference.md)
- [PDF Retrieval Tool](../../tools/llm/parser/docling/api-reference.md)
- [Web Search Tool](../../tools/llm/websearch/tavily/api-reference.md)
- [ReAct Pattern Documentation](../../architecture/multi-agent-orchestration.md#research-agent)
