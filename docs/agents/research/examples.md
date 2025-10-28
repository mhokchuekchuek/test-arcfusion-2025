# Research Supervisor Examples

Simple, practical examples showing how to use the research agent.

## Basic Usage

```python
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from src.graph.state import create_initial_state
from src.agents.research import ResearchSupervisor
from src.agents.tools.pdf_retrieval import PDFRetrievalTool
from src.agents.tools.web_search import WebSearchTool

# Create LangChain ChatOpenAI client (for create_agent)
llm = ChatOpenAI(
    model="gpt-4-turbo",
    temperature=0.7,
    base_url="http://localhost:4000"  # LiteLLM proxy
)

# Create tools
pdf_tool = PDFRetrievalTool(rag_service=rag_service)
web_tool = WebSearchTool(websearch_client=tavily_client)

# Create research agent
research = ResearchSupervisor(
    llm=llm,
    tools=[pdf_tool, web_tool],
    agent_config={"name": "research", "max_history": 10}
)

# Create state
state = create_initial_state(
    messages=[HumanMessage(content="What is DAIL-SQL?")],
    session_id="session-123"
)

# Execute
result = research.execute(state)

# Check result
print(result["context"]["tool_history"])   # ['pdf_retrieval']
print(result["context"]["final_output"])   # Research summary
print(result["next_agent"])                # "synthesis"
```

---

## PDF Search Example

```python
# Query about paper content
state = create_initial_state(
    messages=[HumanMessage(content="What accuracy is in Zhang et al. Table 2?")],
    session_id="pdf-search"
)

result = research.execute(state)

# Agent uses PDF tool
print(result["context"]["tool_history"])  # ['pdf_retrieval']
print(result["context"]["observations"])  # ['Used tool: pdf_retrieval']
```

---

## Web Search Example

```python
# Query about current events
state = create_initial_state(
    messages=[HumanMessage(content="What did OpenAI release this month?")],
    session_id="web-search"
)

result = research.execute(state)

# Agent uses web search tool
print(result["context"]["tool_history"])  # ['web_search']
print(result["context"]["observations"])  # ['Used tool: web_search']
```

---

## Multi-Step Research

```python
# Complex query requiring multiple tools
state = create_initial_state(
    messages=[HumanMessage(
        content="Find the state-of-the-art approach in papers, then search the authors online"
    )],
    session_id="multi-step"
)

result = research.execute(state)

# Agent uses both tools autonomously
print(result["context"]["tool_history"])
# ['pdf_retrieval', 'web_search']

print(result["context"]["final_output"])
# "The state-of-the-art is DAIL-SQL by Dawei Gao..."
```

---

## With Langfuse Integration

```python
from tools.observability.selector import ObservabilitySelector

# Create Langfuse client
langfuse = ObservabilitySelector.create(
    provider="langfuse",
    public_key="pk-...",
    secret_key="sk-..."
)

# Create research agent with Langfuse
research = ResearchSupervisor(
    llm=llm,
    tools=[pdf_tool, web_tool],
    langfuse_client=langfuse,
    agent_config={
        "name": "research",
        "max_history": 10,
        "prompt": {
            "id": "agent_research",
            "environment": "production"
        }
    }
)

# Execute
result = research.execute(state)

# Langfuse automatically traces:
# - Tools used
# - Research output
# - Session: "session-id"
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

# Research agent with max_history=10
research = ResearchSupervisor(
    llm=llm,
    tools=[pdf_tool, web_tool],
    agent_config={"max_history": 10}
)

result = research.execute(state)
# Uses only last 10 messages for context
```

---

## Error Handling

```python
# Research agent handles errors gracefully

try:
    result = research.execute(state)
except Exception:
    pass  # Caught internally

# Check error context
if "error" in result["context"]:
    print(result["context"]["error"])

# Still routes to synthesis
print(result["next_agent"])  # "synthesis"
```

---

## Testing

```python
def test_research_agent():
    """Test research agent uses tools."""
    # Mock tools
    class MockPDFTool:
        name = "pdf_retrieval"
        description = "Search PDFs"
        def _run(self, query: str):
            return "Mock PDF result"

    class MockLLM:
        model_name = "gpt-4"
        def invoke(self, messages):
            return {"content": "Research complete"}

    # Create agent
    research = ResearchSupervisor(
        llm=MockLLM(),
        tools=[MockPDFTool()],
        agent_config={"name": "test"}
    )

    # Create state
    state = create_initial_state(
        messages=[HumanMessage(content="What is RAG?")],
        session_id="test"
    )

    # Execute
    result = research.execute(state)

    # Assert
    assert result["next_agent"] == "synthesis"
    assert result["last_agent"] == "research"
    assert "tool_history" in result["context"]
```

---

## Configuration Options

```python
research = ResearchSupervisor(
    llm=llm,                    # LangChain ChatOpenAI
    tools=[pdf_tool, web_tool],  # List of tools
    langfuse_client=langfuse,    # Optional
    agent_config={
        "name": "research",       # Agent name for tracing
        "max_history": 10,        # Number of messages to consider
        "prompt": {               # Langfuse prompt config
            "id": "agent_research",
            "version": None,      # None = latest
            "environment": "production"
        }
    }
)
```

---

## State Fields

### Input (what research reads):
```python
state["messages"]       # Conversation history
state["session_id"]     # Session ID
```

### Output (what research updates):
```python
state["context"]["observations"]   # Tools used
state["context"]["tool_history"]   # List of tool names
state["context"]["final_output"]   # Research summary
state["messages"]                  # + Final AI message
state["next_agent"]                # "synthesis"
state["last_agent"]                # "research"
state["iteration"]                 # Incremented
```

---

## Creating Custom Tools

```python
from langchain.tools import BaseTool

class CustomSearchTool(BaseTool):
    """Custom search tool."""
    name = "custom_search"
    description = "Search custom database for information"

    def _run(self, query: str) -> str:
        """Execute search."""
        # Your search logic here
        results = custom_search(query)
        return format_results(results)

# Add to research agent
research = ResearchSupervisor(
    llm=llm,
    tools=[pdf_tool, web_tool, CustomSearchTool()],
    agent_config={"name": "research"}
)
```

---

## ReAct Pattern

The research agent uses the ReAct (Reasoning + Acting) pattern:

```
Thought: What do I need to find?
Action: pdf_retrieval
Action Input: "DAIL-SQL methodology"
Observation: [PDF results]

Thought: Now I need more info about authors
Action: web_search
Action Input: "Dawei Gao DAIL-SQL"
Observation: [Web results]

Thought: I have enough information
Final Answer: [Combined research]
```

This happens automatically via LangChain's `create_agent()`.

---

## See Also

- [Research Design](./design.md) - ReAct pattern explained
- [API Reference](./api-reference.md) - Full API docs
- [Synthesis Examples](../synthesis/examples.md) - Next step after research
