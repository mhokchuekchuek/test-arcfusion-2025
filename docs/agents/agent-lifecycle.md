# Agent Lifecycle

How agents execute, manage state, and transition through the workflow.

## Table of Contents
- [Standard Execution Pattern](#standard-execution-pattern)
- [State Schema](#state-schema)
- [State Transitions](#state-transitions)
- [Base Agent Interface](#base-agent-interface)
- [Message History Management](#message-history-management)

---

## Standard Execution Pattern

Every agent follows a consistent four-step execution pattern:

```python
┌─────────────────────────────────────────┐
│ 1. RECEIVE: AgentState from LangGraph  │
│    - Previous messages                 │
│    - Session context                   │
│    - Routing information               │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│ 2. PROCESS: Execute agent logic        │
│    - Call LLM                          │
│    - Use tools (if applicable)         │
│    - Make decisions                    │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│ 3. UPDATE: Modify state                │
│    - Add messages                      │
│    - Set next_agent                    │
│    - Store context/results             │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│ 4. RETURN: Updated AgentState          │
│    - LangGraph routes to next agent    │
│    - State persisted in checkpointer   │
└─────────────────────────────────────────┘
```

### Code Example

```python
from src.agents.base import BaseAgent
from src.graph.state import AgentState

class ExampleAgent(BaseAgent):
    def execute(self, state: AgentState) -> AgentState:
        # Step 1: RECEIVE - Extract data from state
        query = state["messages"][-1].content
        session_id = state["session_id"]

        # Step 2: PROCESS - Execute agent logic
        result = self.llm_client.generate(
            prompt_variables={"query": query}
        )

        # Step 3: UPDATE - Modify state
        state["next_agent"] = "synthesis"
        state["context"]["result"] = result
        state["iteration"] += 1

        # Step 4: RETURN - Return updated state
        return state
```

---

## State Schema

The `AgentState` TypedDict defines the contract between agents.

### Full State Definition

**Location**: `src/graph/state.py`

```python
from typing import TypedDict, Sequence, Dict, Any
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """State object shared between all agents."""

    # Conversation
    messages: Sequence[BaseMessage]  # Full conversation history
    session_id: str                  # Session identifier

    # Routing
    next_agent: str                  # Which agent to execute next
    last_agent: str | None           # Which agent just executed

    # Clarification tracking
    clarification_needed: bool       # Whether clarification is needed
    clarification_count: int         # Number of clarification turns
    missing_context: list[str]       # What context is missing

    # Research context
    context: Dict[str, Any]          # Agent-specific context storage

    # Workflow tracking
    iteration: int                   # Number of workflow steps

    # Final output
    final_answer: str | None         # Final response to user
    confidence_score: float | None   # Confidence in answer
```

### State Field Categories

| Category | Fields | Purpose |
|----------|--------|---------|
| **Conversation** | `messages`, `session_id` | Track chat history and session |
| **Routing** | `next_agent`, `last_agent` | Control workflow navigation |
| **Clarification** | `clarification_needed`, `clarification_count`, `missing_context` | Prevent clarification loops |
| **Context** | `context` | Store agent-specific data |
| **Tracking** | `iteration` | Monitor workflow progress |
| **Output** | `final_answer`, `confidence_score` | Store final results |

### Context Field Usage

The `context` field is a dictionary where agents store intermediate results:

```python
# Research agent stores observations
state["context"]["observations"] = ["Used tool: pdf_retrieval"]
state["context"]["tool_history"] = ["pdf_retrieval", "web_search"]
state["context"]["final_output"] = "Research summary..."

# Synthesis agent reads from context
observations = state["context"]["observations"]
tool_history = state["context"]["tool_history"]
final_output = state["context"]["final_output"]
```

---

## State Transitions

How state evolves as it flows through the workflow.

### Example: Orchestrator → Research → Synthesis

```python
# 1. Initial state (after user query)
state = {
    "messages": [HumanMessage("What's the accuracy?")],
    "session_id": "abc123",
    "next_agent": "orchestrator",
    "last_agent": None,
    "clarification_needed": False,
    "clarification_count": 0,
    "missing_context": [],
    "context": {},
    "iteration": 0,
    "final_answer": None,
    "confidence_score": None,
}

# 2. After Orchestrator executes
state = orchestrator.execute(state)
# state["next_agent"] = "research"
# state["last_agent"] = "orchestrator"
# state["iteration"] = 1

# 3. After Research executes
state = research.execute(state)
# state["context"]["observations"] = ["Used tool: pdf_retrieval"]
# state["context"]["final_output"] = "Found 5 results..."
# state["next_agent"] = "synthesis"
# state["last_agent"] = "research"
# state["iteration"] = 2
# state["messages"] += [AIMessage("Research summary...")]

# 4. After Synthesis executes
state = synthesis.execute(state)
# state["final_answer"] = "The accuracy is 87.2% (Zhang et al. Table 2)"
# state["confidence_score"] = 0.95
# state["next_agent"] = "END"
# state["last_agent"] = "synthesis"
# state["iteration"] = 3
```

### Clarification Loop Example

```python
# 1. Initial vague query
state = {
    "messages": [HumanMessage("Tell me about it")],
    "next_agent": "orchestrator",
    "clarification_count": 0,
}

# 2. Orchestrator routes to clarification
state = orchestrator.execute(state)
# state["next_agent"] = "clarification"
# state["clarification_needed"] = True
# state["clarification_count"] = 1

# 3. Clarification generates question
state = clarification.execute(state)
# state["messages"] += [AIMessage("What topic are you asking about?")]
# state["next_agent"] = "END"  # Wait for user

# 4. User responds
state["messages"] += [HumanMessage("Zhang et al. paper")]
state["next_agent"] = "orchestrator"

# 5. Orchestrator detects response pattern
state = orchestrator.execute(state)
# Pattern detection: AI → Human after clarification
# state["next_agent"] = "research"  # Skip LLM call!
# state["clarification_count"] = 0  # Reset

# 6. Continue to research
state = research.execute(state)
```

---

## Base Agent Interface

All agents inherit from `BaseAgent` abstract class.

### Base Class Definition

**Location**: `src/agents/base.py:6`

```python
from abc import ABC, abstractmethod
from src.graph.state import AgentState

class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, state: AgentState) -> AgentState:
        """Execute agent logic and return updated state.

        Args:
            state: Current agent state from LangGraph

        Returns:
            Updated state with agent's modifications
        """
        pass
```

### Implementation Example

```python
from src.agents.base import BaseAgent

class MasterOrchestrator(BaseAgent):
    def __init__(self, llm_client, langfuse_client=None, agent_config=None):
        super().__init__("MasterOrchestrator")
        self.llm_client = llm_client
        self.langfuse_client = langfuse_client
        self.agent_config = agent_config or {}

    def execute(self, state: AgentState) -> AgentState:
        """Analyze query and decide routing."""
        # 1. Extract query
        query = state["messages"][-1].content

        # 2. Make decision
        decision = self.llm_client.generate(
            prompt_variables={"query": query}
        )

        # 3. Update state
        if "CLARIFICATION" in decision:
            state["next_agent"] = "clarification"
            state["clarification_needed"] = True
            state["clarification_count"] += 1
        else:
            state["next_agent"] = "research"
            state["clarification_needed"] = False

        state["last_agent"] = self.name
        state["iteration"] += 1

        return state
```

### Agent Responsibilities

| Method | Responsibility |
|--------|---------------|
| `__init__()` | Initialize dependencies (LLM clients, tools, config) |
| `execute()` | Process state and return updated state |
| Helper methods | Internal logic (don't modify state directly) |

---

## Message History Management

Agents must manage conversation history carefully to avoid token limits.

### History Limiting Pattern

```python
def execute(self, state: AgentState) -> AgentState:
    # Limit history to prevent token overflow
    max_history = self.agent_config.get("max_history", 10)
    messages = state["messages"][-max_history:]  # Last N messages

    # Use limited history for LLM call
    response = self.llm_client.generate(
        prompt_variables={
            "conversation_history": self._format_history(messages)
        }
    )

    return state
```

**Location**: Common pattern in `orchestrator.py:87`, `research.py:96`

### Message Format Conversion

```python
def _format_conversation_history(
    self,
    messages: Sequence[BaseMessage]
) -> str:
    """Convert LangChain messages to formatted string."""
    formatted = []
    for msg in messages:
        if hasattr(msg, 'type'):
            role = "User" if msg.type == "human" else "AI"
            formatted.append(f"{role}: {msg.content}")
    return "\n".join(formatted)
```

### Adding Messages to State

```python
from langchain_core.messages import AIMessage, HumanMessage

# Add AI response
state["messages"].append(
    AIMessage(content="This is the agent's response")
)

# Add human message (from user input)
state["messages"].append(
    HumanMessage(content="User's follow-up question")
)
```

**Important**: Only append the **final** message from an agent, not intermediate tool calls.

### Research Agent Message Management

```python
# Research agent uses tools (creates many intermediate messages)
result = self.agent.invoke({"messages": messages})
# result["messages"] contains: [Human, AI Tool Call, Tool Response, AI Final]

# Only append the FINAL AI message to state
final_ai_message = None
for msg in reversed(result["messages"]):
    if msg.type == 'ai' and not hasattr(msg, 'tool_calls'):
        final_ai_message = msg
        break

if final_ai_message:
    state["messages"].append(final_ai_message)
```

**Location**: `src/agents/research.py:156`

---

## LangGraph Integration

Agents are integrated into LangGraph workflows.

### Workflow Definition

**Location**: `src/graph/workflow.py:45`

```python
from langgraph.graph import StateGraph, END

class AgentWorkflow:
    def __init__(self, orchestrator, clarification, research, synthesis):
        self.orchestrator = orchestrator
        self.clarification = clarification
        self.research = research
        self.synthesis = synthesis

    def build(self):
        # Create graph
        workflow = StateGraph(AgentState)

        # Add nodes (each node is an agent's execute method)
        workflow.add_node("orchestrator", self.orchestrator.execute)
        workflow.add_node("clarification", self.clarification.execute)
        workflow.add_node("research", self.research.execute)
        workflow.add_node("synthesis", self.synthesis.execute)

        # Define entry point
        workflow.set_entry_point("orchestrator")

        # Add conditional routing
        workflow.add_conditional_edges(
            "orchestrator",
            self._route_orchestrator,
            {
                "clarification": "clarification",
                "research": "research",
            }
        )

        # Add fixed edges
        workflow.add_edge("clarification", END)
        workflow.add_edge("research", "synthesis")
        workflow.add_edge("synthesis", END)

        return workflow.compile()

    def _route_orchestrator(self, state: AgentState) -> str:
        """Route based on orchestrator's decision."""
        return state["next_agent"]
```

### Execution Flow

```python
# Create workflow
workflow = agent_workflow.build()

# Execute with initial state
initial_state = {
    "messages": [HumanMessage("What is RAG?")],
    "session_id": "abc123",
    # ... other fields
}

# LangGraph handles routing automatically
final_state = workflow.invoke(initial_state)

# Access final answer
print(final_state["final_answer"])
```

---

## State Persistence

LangGraph supports state checkpointing for conversation history.

### Checkpointer Setup

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# Create checkpointer
memory = SqliteSaver.from_conn_string(":memory:")

# Compile workflow with checkpointer
workflow = graph.compile(checkpointer=memory)

# Execute with thread_id for persistence
config = {"configurable": {"thread_id": "conversation-123"}}
result = workflow.invoke(initial_state, config)

# Continue conversation (state is restored)
follow_up = workflow.invoke(
    {"messages": [HumanMessage("Follow-up question")]},
    config  # Same thread_id
)
```

---

## Key Takeaways

1. **Consistent Pattern**: All agents follow RECEIVE → PROCESS → UPDATE → RETURN
2. **Typed State**: `AgentState` provides type safety and clear contracts
3. **Explicit Updates**: Agents modify state explicitly and return it
4. **History Management**: Limit message history to control token usage
5. **Message Filtering**: Only append final messages, not intermediate tool calls
6. **LangGraph Integration**: Agents integrate seamlessly with LangGraph routing
7. **State Persistence**: LangGraph checkpointers enable conversation continuity

---

## See Also

- [Design Philosophy](./design-philosophy.md) - Core design principles
- [Development Guide](./development.md) - How to implement agents
- [Orchestrator Design](./orchestrator/design.md) - Routing logic
- [Research Design](./research/design.md) - Tool usage and ReAct pattern
