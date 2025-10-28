# Research Agent Design

## Agent Responsibility

The **Research Agent** (ResearchSupervisor) executes autonomous information retrieval from PDFs and/or web using a **ReAct (Reasoning + Acting) pattern**. It can perform multi-step research by intelligently selecting and sequencing tool calls based on the query requirements.

**Location**: `src/agents/research.py:1`

**Key Capabilities**:
- Search academic papers in vector store (PDF Retrieval Tool)
- Search the web for current information (Web Search Tool)
- Multi-step reasoning: Plan → Execute → Reflect → Iterate
- Autonomous tool selection and orchestration
- Source attribution and metadata preservation

---

## Tool Integration

The Research Agent uses **LangChain's create_agent** function (v1.0 API) to enable autonomous tool calling with the ReAct pattern.

### Architecture

```python
from langchain.agents import create_agent

self.agent = create_agent(
    model=llm,              # ChatOpenAI configured for LiteLLM proxy
    tools=tools,            # [PDFRetrievalTool, WebSearchTool]
    system_prompt=prompt,   # From Langfuse
)
```

**Location**: `src/agents/research.py:74`

**Note**: Uses LangChain's `create_agent` (built on LangGraph internally), which replaces the deprecated `create_react_agent` API.

---

### Tool 1: PDF Retrieval Tool

**Location**: `src/agents/tools/pdf_retrieval.py:1`

**Purpose**: Search academic papers in Qdrant vector store using RAG

#### Implementation

```python
from langchain.tools import BaseTool

class PDFRetrievalTool(BaseTool):
    name: str = "pdf_retrieval"
    description: str = (
        "Search academic papers for information. Use this for questions about "
        "research papers, methodologies, experiments, or specific citations."
    )

    def _run(self, query: str) -> str:
        """Execute PDF search via RAG service."""
        results = self.rag_service.retriever.retrieve(
            query=query,
            top_k=5,
            min_similarity_score=self.min_similarity_score
        )

        # Format results with source attribution
        formatted = []
        for result in results:
            formatted.append(
                f"Source: {result['metadata']['source']} (Page {result['metadata']['page']})\n"
                f"Content: {result['content']}\n"
                f"Similarity: {result['score']:.2f}"
            )

        return "\n\n---\n\n".join(formatted)
```

#### Key Features

- **LangChain BaseTool**: Inherits from `BaseTool` for agent compatibility
- **RAG Integration**: Uses RAGService for retrieval
- **Similarity Filtering**: Only returns chunks above threshold (default: 0.5)
- **Source Attribution**: Includes filename and page number
- **Metadata Preservation**: Maintains document context

#### Example Usage by Agent

```
Agent Thought: User asks about DAIL-SQL methodology. I should search papers.

Action: pdf_retrieval
Action Input: "DAIL-SQL methodology implementation details"

Observation:
Source: DAIL-SQL_paper.pdf (Page 3)
Content: DAIL-SQL uses example-based learning with carefully selected demonstrations...
Similarity: 0.89

Source: DAIL-SQL_paper.pdf (Page 5)
Content: The selection algorithm ranks examples by similarity to target query...
Similarity: 0.82
```

---

### Tool 2: Web Search Tool

**Location**: `src/agents/tools/web_search.py:1`

**Purpose**: Search the web for current information using Tavily API

#### Implementation

```python
from langchain.tools import BaseTool

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search the web for current information not available in papers. "
        "Use this for recent news, latest releases, or out-of-scope topics."
    )

    def _run(self, query: str) -> str:
        """Execute web search via Tavily."""
        results = self.websearch_client.search(
            query=query,
            max_results=self.max_results
        )

        # Format results
        formatted = []
        for result in results:
            formatted.append(
                f"Title: {result['title']}\n"
                f"URL: {result['url']}\n"
                f"Content: {result['content']}"
            )

        return "\n\n---\n\n".join(formatted)
```

#### Key Features

- **LangChain BaseTool**: Inherits from `BaseTool` for agent compatibility
- **Tavily Integration**: Uses Tavily API for high-quality web search
- **Current Information**: Provides up-to-date content not in PDFs
- **URL Attribution**: Maintains source links
- **Configurable Results**: Default 5 results, adjustable

#### Example Usage by Agent

```
Agent Thought: User asks about OpenAI's latest release. Papers won't have this.

Action: web_search
Action Input: "OpenAI latest release 2024"

Observation:
Title: OpenAI Announces GPT-4.5 Turbo
URL: https://openai.com/blog/gpt-4-5-turbo
Content: OpenAI today released GPT-4.5 Turbo, featuring improved reasoning...

Title: GPT-4.5 Turbo: What's New
URL: https://techcrunch.com/...
Content: The new model shows significant improvements in code generation...
```

---

## Autonomous Multi-Step Research

The Research Agent can **plan and execute complex multi-step research** autonomously using the ReAct pattern provided by LangChain's `create_agent`.

### ReAct Pattern

```
Thought → Action → Observation → Reflection → Repeat
```

**Example Multi-Step Flow**:

```
User Query: "Find state-of-the-art approach in PDFs, then search web for authors"

---

Thought: I need to first search papers for state-of-the-art approaches.

Action: pdf_retrieval
Action Input: "state-of-the-art text-to-sql approach"

Observation:
Source: DAIL-SQL_paper.pdf
Content: DAIL-SQL achieves state-of-the-art results...
Authors: Dawei Gao, Haibin Wang, et al.

---

Thought: Now I have the approach (DAIL-SQL) and authors. Let me search web for more about them.

Action: web_search
Action Input: "Dawei Gao DAIL-SQL text-to-sql"

Observation:
Title: Dawei Gao's Research Profile
URL: https://scholar.google.com/...
Content: Dawei Gao is a researcher at...

---

Thought: I have sufficient information to answer the query.

Final Answer: The state-of-the-art approach is DAIL-SQL, developed by Dawei Gao
and Haibin Wang. Based on web search, Dawei Gao is a researcher at...
```

### Autonomous Capabilities

The agent (powered by LangChain's create_agent) can:

1. **Plan Steps**: Break down complex queries into sub-tasks
2. **Select Tools**: Choose appropriate tool for each step
3. **Chain Results**: Use output from one tool as input to another
4. **Reflect**: Evaluate if more information is needed
5. **Terminate**: Decide when sufficient information gathered

**Key Insight**: No hard-coded logic for multi-step research. The LLM autonomously plans and executes based on the system prompt and ReAct framework.

---

## Result Combination

The agent automatically combines results from multiple tool calls:

### Tool History Tracking

```python
# Extract tool call information from messages
tool_history = []
for msg in result["messages"]:
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        for tool_call in msg.tool_calls:
            tool_name = tool_call.get('name', 'unknown')
            if tool_name not in tool_history:  # Avoid duplicates
                tool_history.append(tool_name)
```

**Location**: `src/agents/research.py:114`

### Observation Collection

```python
# Collect all tool usage
observations = []
for tool_name in tool_history:
    observations.append(f"Used tool: {tool_name}")

# Store in context for synthesis
state["context"]["observations"] = observations
state["context"]["tool_history"] = tool_history
state["context"]["final_output"] = result["messages"][-1].content
```

**Location**: `src/agents/research.py:124`

### Message Management

```python
# Only append the FINAL AI response, not intermediate tool messages
# Find the last AI message (the final answer after tool use)
final_ai_message = None
for msg in reversed(result["messages"]):
    if hasattr(msg, 'type') and msg.type == 'ai':
        # Make sure it's a final answer, not a tool call request
        if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
            final_ai_message = msg
            break

if final_ai_message:
    state["messages"].append(final_ai_message)
```

**Location**: `src/agents/research.py:156`

**Important**: Only the final AI message is added to state, not intermediate tool calls/responses.

---

## State Updates

```python
def execute(self, state: AgentState) -> AgentState:
    # 1. Limit message history to prevent token overflow
    max_history = self.agent_config.get("max_history", 10)
    messages_to_send = state["messages"][-max_history:]

    # 2. Invoke agent (ReAct loop)
    result = self.agent.invoke({"messages": messages_to_send})

    # 3. Extract tool usage
    tool_history = []
    for msg in result["messages"]:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call.get('name', 'unknown')
                if tool_name not in tool_history:
                    tool_history.append(tool_name)

    # 4. Store context
    state["context"]["observations"] = [f"Used tool: {t}" for t in tool_history]
    state["context"]["tool_history"] = tool_history
    state["context"]["final_output"] = result["messages"][-1].content

    # 5. Add only final AI message to state
    final_ai_message = self._get_final_ai_message(result["messages"])
    if final_ai_message:
        state["messages"].append(final_ai_message)

    # 6. Update routing
    state["next_agent"] = "synthesis"
    state["last_agent"] = "research"
    state["iteration"] += 1

    return state
```

**Location**: `src/agents/research.py:81`

### State Fields Modified

| Field | Type | Value | Purpose |
|-------|------|-------|---------|
| `context["observations"]` | List[str] | Tool names used | Track research actions |
| `context["tool_history"]` | List[str] | Tool names | Which tools were called |
| `context["final_output"]` | str | Agent summary | Research conclusion |
| `messages` | Sequence[BaseMessage] | + final AI message | Conversation history |
| `next_agent` | str | `"synthesis"` | Route to synthesis |
| `last_agent` | str | `"research"` | Mark execution |
| `iteration` | int | +1 | Workflow step counter |

---

## Configuration

### Settings File

**Location**: `configs/agents/langgraph.yaml`

```yaml
research:
  name: "research"
  model: "gpt-4-turbo"
  temperature: 0.7  # Balanced for reasoning
  max_history: 10   # Context window

  # Prompt configuration (Langfuse)
  prompt:
    id: "agent_research"  # Prompt name in Langfuse
    environment: "production"  # or "dev"
    version: null  # null = latest version

  # Tool configurations
  pdf_retrieval:
    min_similarity_score: 0.5
    top_k: 5

  web_search:
    max_results: 5
```

### System Prompt

**Prompt Name**: `agent_research` (stored in Langfuse)

**Prompt Structure**:
```
You are the Research agent in a multi-agent RAG system. Your role is to gather
information from available sources to answer user queries.

Available Tools:
- pdf_retrieval: Search academic papers in vector store
- web_search: Search the web for current information

Guidelines:
1. Use pdf_retrieval for questions about research papers, methodologies, experiments
2. Use web_search for current events, latest releases, or out-of-scope topics
3. You can use multiple tools in sequence if needed
4. Always cite sources in your observations
5. If information is insufficient, use additional tools
6. Synthesize findings into a clear summary

Think step-by-step using the ReAct pattern:
- Thought: What information do I need?
- Action: Which tool should I use?
- Observation: What did I learn?
- Reflection: Is this sufficient or do I need more?
```

**Location**: Langfuse prompt management system

### Initialization

**Location**: `src/apis/dependencies/agents.py`

```python
from langchain_openai import ChatOpenAI

# Create LangChain ChatOpenAI client (for create_agent)
research_llm = ChatOpenAI(
    model=settings.research.model,
    temperature=settings.research.temperature,
    base_url=settings.llm.proxy_url,  # LiteLLM proxy
)

# Create tools
pdf_tool = PDFRetrievalTool(
    rag_service=rag_service,
    min_similarity_score=settings.research.pdf_retrieval.min_similarity_score
)

web_tool = WebSearchTool(
    websearch_client=tavily_client,
    max_results=settings.research.web_search.max_results
)

# Create research agent
research = ResearchSupervisor(
    llm=research_llm,
    tools=[pdf_tool, web_tool],
    langfuse_client=langfuse_client,
    agent_config={
        "name": settings.research.name,
        "prompt": settings.research.prompt,
        "max_history": settings.research.max_history,
    }
)
```

---

## Integration with LangGraph

### Workflow Definition

**Location**: `src/graph/workflow.py`

```python
from langgraph.graph import StateGraph, END

# Add research node
workflow.add_node("research", self.research.execute)

# Research always routes to synthesis
workflow.add_edge("research", "synthesis")
```

### Visual Flow

```
orchestrator
  │
  └─→ research (ResearchSupervisor)
        ├─ (ReAct loop via LangChain create_agent)
        │   ├─→ pdf_retrieval (BaseTool)
        │   └─→ web_search (BaseTool)
        │
        └─→ synthesis → END
```

**Technology Stack**:
- **LangGraph**: Workflow orchestration and state management
- **LangChain**: create_agent for ReAct pattern, BaseTool for tools
- **LiteLLM Proxy**: Unified LLM API

---

## Observability & Tracing

### Langfuse Tracking

```python
if self.langfuse_client:
    self.langfuse_client.trace_generation(
        name=self.agent_name,  # "research"
        input_data={"messages": [m.content for m in original_messages]},
        output=final_output,
        model=str(self.llm.model_name),
        metadata={
            "agent": "ResearchSupervisor",
            "tools_used": tool_history,
            "num_observations": len(observations)
        },
        session_id=session_id
    )
```

**Location**: `src/agents/research.py:132`

### Logged Information

- **Input**: User query and conversation history
- **Output**: Final research summary
- **Metadata**: Tools used, number of observations
- **Session**: Grouped by `session_id` for conversation tracking

---

## Error Handling

### Research Failure Recovery

```python
except Exception as e:
    logger.error(f"Research agent failed: {e}", exc_info=True)
    # On error, move to synthesis with error context
    state["context"]["observations"] = [f"Research failed: {str(e)}"]
    state["context"]["final_output"] = "Unable to complete research due to an error."
    state["next_agent"] = "synthesis"
    state["iteration"] += 1
    return state
```

**Location**: `src/agents/research.py:179`

**Fallback Behavior**:
- Logs error with stack trace
- Sets error context for synthesis
- Still routes to synthesis (graceful degradation)
- Synthesis can generate response explaining research failure

### Tool Failure Handling

Tool failures are handled by LangChain's create_agent:
- Exceptions from `_run()` are caught
- Error message returned as observation
- Agent can retry with different tool or query

---

## Performance Considerations

### Latency

| Component | Time |
|-----------|------|
| Format history | ~5ms |
| Fetch Langfuse prompt | ~50ms (cached) |
| ReAct loop (1 tool call) | ~2-3s |
| ReAct loop (2 tool calls) | ~4-6s |
| ReAct loop (3+ tool calls) | ~6-10s |
| Trace to Langfuse | ~100ms |

**Variable latency**: Depends on number of tool calls agent decides to make.

### Token Usage

| Component | Tokens |
|-----------|--------|
| System prompt | ~500 |
| Conversation history (10 msgs) | ~2,000 |
| Tool descriptions | ~200 |
| Per tool call (input + output) | ~1,000 |
| **Average per execution** | **~4,000-8,000 tokens** |

### Optimization Strategies

1. **History Limiting**: Only send last 10 messages (line 96)
2. **Message Filtering**: Only append final AI response (line 156)
3. **Tool Result Caching**: RAG service caches embeddings
4. **Early Termination**: Agent stops when sufficient info gathered

---

## Testing

### Unit Tests

```python
def test_research_pdf_tool():
    state = {
        "messages": [HumanMessage(content="What is DAIL-SQL?")],
        "session_id": "test",
        "context": {},
        "iteration": 0,
    }

    result = research.execute(state)

    assert result["last_agent"] == "research"
    assert result["next_agent"] == "synthesis"
    assert "pdf_retrieval" in result["context"]["tool_history"]
    assert result["context"]["final_output"] != ""

def test_research_web_tool():
    state = {
        "messages": [HumanMessage(content="Latest OpenAI news")],
        "session_id": "test",
        "context": {},
        "iteration": 0,
    }

    result = research.execute(state)

    assert "web_search" in result["context"]["tool_history"]

def test_research_multi_tool():
    state = {
        "messages": [HumanMessage(content="Find SOTA in papers and search authors online")],
        "session_id": "test",
        "context": {},
        "iteration": 0,
    }

    result = research.execute(state)

    # Should use both tools
    assert "pdf_retrieval" in result["context"]["tool_history"]
    assert "web_search" in result["context"]["tool_history"]
```

---

## Key Takeaways

1. **LangChain create_agent**: Uses `langchain.agents.create_agent` for ReAct pattern (v1.0 API)
2. **LangChain BaseTool**: Tools inherit from `langchain.tools.BaseTool`
3. **Two Tools**: PDF retrieval (papers) and web search (current info)
4. **Multi-Step**: Autonomous planning and execution via ReAct
5. **Message Management**: Only final AI response added to state
6. **State Context**: Stores tool history and observations for synthesis
7. **Error Recovery**: Graceful degradation on failures
8. **Observability**: Full tracing to Langfuse with session tracking

The Research Agent is the **autonomous information gathering engine** that uses LangChain's agent framework to intelligently select and orchestrate tools for answering complex queries from multiple sources.
