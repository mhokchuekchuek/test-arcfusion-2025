# Agent Design Philosophy

Core principles guiding the agent system architecture and implementation patterns.

## Table of Contents
- [1. Single Responsibility Principle](#1-single-responsibility-principle)
- [2. Composability](#2-composability)
- [3. LLM-Powered Decision-Making](#3-llm-powered-decision-making)
- [4. Explicit State Management](#4-explicit-state-management)

---

## 1. Single Responsibility Principle

Each agent has **one clear job**:

- **Orchestrator**: Decide where to route (not execute research)
- **Clarification**: Ask questions (not answer them)
- **Research**: Gather information (not synthesize)
- **Synthesis**: Format answers (not gather data)

### Benefits

- Simpler prompts (focused on one task)
- Easier debugging (isolate which step failed)
- Better testability (unit test individual capabilities)
- Clearer observability (track per-agent performance)

### Anti-Pattern

```python
# BAD: Agent tries to do everything
class SuperAgent:
    def execute(self, query):
        if self.is_vague(query):
            return self.clarify(query)
        results = self.search_pdf(query)
        if not results:
            results = self.search_web(query)
        return self.synthesize(results)
```

**Problems:**
- Too many responsibilities
- Hard to test individual capabilities
- Difficult to debug failures
- Tight coupling between concerns

### Good Pattern

```python
# GOOD: Specialized agents with single responsibility
class OrchestratorAgent:
    def execute(self, state):
        return self.decide_routing(state)  # Only routing

class ResearchAgent:
    def execute(self, state):
        return self.gather_information(state)  # Only research
```

**Benefits:**
- Clear separation of concerns
- Easy to test each capability
- Simple to debug and trace
- Loose coupling between agents

---

## 2. Composability

Agents are **building blocks** that can be:
- Rearranged in different workflows
- Reused in multiple graphs
- Combined in novel ways
- Tested independently

### Example Workflows

```python
# Workflow 1: Standard flow
Entry → Orchestrator → Research → Synthesis → END

# Workflow 2: Add reranker
Entry → Orchestrator → Research → Reranker → Synthesis → END

# Workflow 3: Add verification
Entry → Orchestrator → Research → Synthesis → Verifier → END

# Workflow 4: Complex routing
Entry → Orchestrator → Research → Synthesis
                  ↓
              Clarification → (back to Orchestrator)
```

### Implementation Pattern

```python
# Each agent is independent and composable
class AgentWorkflow:
    def __init__(self, orchestrator, research, synthesis, reranker=None):
        self.orchestrator = orchestrator
        self.research = research
        self.synthesis = synthesis
        self.reranker = reranker  # Optional component

    def build_graph(self):
        workflow = StateGraph(AgentState)

        # Add core agents
        workflow.add_node("orchestrator", self.orchestrator.execute)
        workflow.add_node("research", self.research.execute)
        workflow.add_node("synthesis", self.synthesis.execute)

        # Optionally add reranker
        if self.reranker:
            workflow.add_node("reranker", self.reranker.execute)
            workflow.add_edge("research", "reranker")
            workflow.add_edge("reranker", "synthesis")
        else:
            workflow.add_edge("research", "synthesis")

        return workflow
```

### Benefits

- **Flexibility**: Change workflow without rewriting agents
- **Reusability**: Same agents in different workflows
- **Testability**: Test agents in isolation
- **Maintainability**: Update one agent without breaking others

---

## 3. LLM-Powered Decision-Making

Use **semantic understanding** instead of brittle rule-based logic.

### Rule-Based Approach (Anti-Pattern)

```python
# BAD: Brittle rules that break easily
def route_query(query):
    if "latest" in query:
        return "web_search"
    elif "Table" in query:
        return "pdf_search"
    elif "compare" in query:
        return "clarification"
    else:
        return "research"
```

**Problems:**
- Misses synonyms ("newest", "current", "recent")
- Ignores context ("latest paper in our database" should use PDF)
- Case-sensitive ("table" vs "Table")
- Cannot handle nuance ("latest paper" vs "latest news")
- Requires constant rule updates

### LLM-Powered Approach

```python
# GOOD: Semantic understanding via LLM
def route_query(query, conversation_history):
    decision = llm.analyze(
        prompt=f"""
        Analyze this query and choose the best action:
        Query: {query}

        Conversation History:
        {conversation_history}

        Consider:
        - Semantic intent (not just keywords)
        - Conversation context
        - Query clarity and specificity
        - Temporal requirements (current vs historical)

        Decision: [CLARIFICATION | RESEARCH]
        Reasoning: [Brief explanation]
        """
    )
    return decision
```

**Benefits:**
- Handles synonyms automatically ("latest" = "newest" = "current" = "recent")
- Context-aware decisions based on conversation history
- No manual rule updates needed
- Natural language reasoning
- Understands nuance and intent

### Real-World Examples

| Query | Rule-Based | LLM-Powered | Winner |
|-------|-----------|-------------|--------|
| "Show me the newest approach" | ❌ web_search (keyword "newest") | ✅ pdf_search (context: paper discussion) | LLM |
| "Latest OpenAI release" | ✅ web_search (keyword "latest") | ✅ web_search (temporal query) | Both |
| "Tell me more about it" | ❌ research (no keywords) | ✅ clarification (ambiguous pronoun) | LLM |
| "Table 2 accuracy" | ✅ pdf_search (keyword "Table") | ✅ pdf_search (paper reference) | Both |

---

## 4. Explicit State Management

Agents communicate via **typed state objects** (not implicit globals or hidden state).

### State Object Pattern

```python
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """Explicit state contract between agents."""
    messages: Sequence[BaseMessage]
    session_id: str
    next_agent: str
    context: Dict[str, Any]
    clarification_count: int
    iteration: int
    final_answer: str | None
    # ... other fields
```

**Location**: `src/graph/state.py`

### Agent Implementation

```python
def execute(self, state: AgentState) -> AgentState:
    """Execute agent logic with explicit state."""
    # 1. Read from state
    query = state["messages"][-1].content
    session_id = state["session_id"]

    # 2. Process
    decision = self.llm_client.generate(query)

    # 3. Update state
    state["next_agent"] = "research"
    state["context"]["plan"] = decision
    state["iteration"] += 1

    # 4. Explicit return
    return state
```

### Benefits

**Type Safety:**
```python
# IDE autocomplete works
state["messages"]  # ✅ Type: Sequence[BaseMessage]
state["next_agent"]  # ✅ Type: str
```

**Clear Data Contracts:**
```python
# Each agent knows exactly what it receives and returns
def execute(self, state: AgentState) -> AgentState:
    # Input contract: state must have messages, session_id, etc.
    # Output contract: state with updated next_agent, iteration, etc.
```

**Testability:**
```python
# Easy to create mock states for testing
def test_orchestrator():
    mock_state = {
        "messages": [HumanMessage("test query")],
        "session_id": "test-123",
        "clarification_count": 0,
        # ... other required fields
    }
    result = orchestrator.execute(mock_state)
    assert result["next_agent"] == "research"
```

**Serializability:**
```python
# State can be persisted to database or cache
import json
state_json = json.dumps(state)

# State can be loaded from checkpoints
state = json.loads(state_json)
```

### Anti-Pattern: Implicit State

```python
# BAD: Hidden state in instance variables
class BadAgent:
    def __init__(self):
        self.current_query = None  # Hidden state
        self.last_result = None    # Hidden state

    def execute(self, state):
        self.current_query = state["messages"][-1].content
        # State is now split between instance and state object
```

**Problems:**
- Hard to test (must mock instance state)
- Not serializable (state lives in memory)
- Race conditions in async/concurrent scenarios
- Difficult to debug (state scattered across objects)

---

## Applying All Four Principles Together

### Example: Adding a Reranker Agent

```python
# 1. Single Responsibility: Reranker only reranks
class RerankerAgent(BaseAgent):
    """Rerank documents by relevance."""

    def execute(self, state: AgentState) -> AgentState:
        # Only reranking logic, nothing else
        documents = state["context"]["pdf_results"]
        reranked = self.rerank_model.rerank(documents)

        state["context"]["pdf_results"] = reranked
        state["next_agent"] = "synthesis"
        return state

# 2. Composability: Easy to add to workflow
workflow.add_node("reranker", reranker.execute)
workflow.add_edge("research", "reranker")
workflow.add_edge("reranker", "synthesis")

# 3. LLM-Powered: Semantic reranking
rerank_model = SentenceTransformerReranker()  # Uses LLM embeddings

# 4. Explicit State: Clear data contract
# Input: state["context"]["pdf_results"]
# Output: state["context"]["pdf_results"] (reranked)
```

---

## Key Takeaways

1. **Single Responsibility**: Each agent does one thing well
2. **Composability**: Agents are interchangeable building blocks
3. **LLM-Powered**: Semantic understanding beats hard-coded rules
4. **Explicit State**: Typed state objects for clarity and testability

These principles make the agent system:
- Easy to understand (clear responsibilities)
- Easy to test (isolated components)
- Easy to debug (observable state transitions)
- Easy to extend (composable architecture)
- Robust (semantic reasoning handles edge cases)

---

## See Also

- [Agent Lifecycle](./agent-lifecycle.md) - How agents execute and manage state
- [Development Guide](./development.md) - How to add new agents
- [Agent Types](./README.md#agent-types) - Overview of different agent categories
