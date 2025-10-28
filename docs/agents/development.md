# Agent Development Guide

How to add new agents, write tests, and follow best practices.

## Table of Contents
- [Adding New Agents](#adding-new-agents)
- [Testing Agents](#testing-agents)
- [Best Practices](#best-practices)
- [Performance Optimization](#performance-optimization)
- [Prompt Management](#prompt-management)
- [Observability](#observability)

---

## Adding New Agents

Follow these steps to add a new agent to the system.

### Step 1: Create Agent Class

Create a new file in `src/agents/` following the naming pattern `{agent_name}.py`.

```python
# src/agents/reranker.py
from src.agents.base import BaseAgent
from src.graph.state import AgentState
from typing import List

class RerankerAgent(BaseAgent):
    """Rerank retrieved documents for better relevance."""

    def __init__(self, rerank_model, langfuse_client=None, agent_config=None):
        super().__init__("RerankerAgent")
        self.rerank_model = rerank_model
        self.langfuse_client = langfuse_client
        self.agent_config = agent_config or {}

    def execute(self, state: AgentState) -> AgentState:
        """Rerank documents from research agent."""
        # 1. Extract documents from context
        pdf_results = state["context"].get("pdf_results", [])
        query = state["messages"][-1].content

        # 2. Rerank documents
        reranked = self.rerank_model.rerank(
            query=query,
            documents=pdf_results,
            top_k=5
        )

        # 3. Update context with reranked results
        state["context"]["pdf_results"] = reranked
        state["context"]["reranked"] = True

        # 4. Update routing
        state["next_agent"] = "synthesis"
        state["last_agent"] = "reranker"
        state["iteration"] += 1

        # 5. Optional: Trace to Langfuse
        if self.langfuse_client:
            self.langfuse_client.trace_generation(
                name=self.name,
                input_data={"query": query, "num_docs": len(pdf_results)},
                output={"num_reranked": len(reranked)},
                session_id=state.get("session_id")
            )

        return state
```

### Step 2: Add to Workflow

Update `src/graph/workflow.py` to integrate the new agent.

```python
# src/graph/workflow.py
from src.agents.reranker import RerankerAgent

class AgentWorkflow:
    def __init__(
        self,
        orchestrator,
        clarification,
        research,
        synthesis,
        reranker=None  # New optional agent
    ):
        self.orchestrator = orchestrator
        self.clarification = clarification
        self.research = research
        self.synthesis = synthesis
        self.reranker = reranker  # Store reranker

    def build(self):
        workflow = StateGraph(AgentState)

        # Add core nodes
        workflow.add_node("orchestrator", self.orchestrator.execute)
        workflow.add_node("clarification", self.clarification.execute)
        workflow.add_node("research", self.research.execute)
        workflow.add_node("synthesis", self.synthesis.execute)

        # Add reranker if provided
        if self.reranker:
            workflow.add_node("reranker", self.reranker.execute)
            # Insert reranker between research and synthesis
            workflow.add_edge("research", "reranker")
            workflow.add_edge("reranker", "synthesis")
        else:
            workflow.add_edge("research", "synthesis")

        # ... rest of workflow setup

        return workflow.compile()
```

### Step 3: Update State Schema (if needed)

If your agent needs new state fields, update `src/graph/state.py`.

```python
# src/graph/state.py
class AgentState(TypedDict):
    # ... existing fields

    # NEW: Reranking metadata
    rerank_scores: List[float]  # Reranking confidence scores
```

**Important**: Only add state fields if they need to be shared across agents. Use `context` dict for agent-specific data.

### Step 4: Initialize in Dependency Injection

Add agent initialization to `src/apis/dependencies/agents.py`.

```python
# src/apis/dependencies/agents.py
from src.agents.reranker import RerankerAgent
from some_reranker_library import SentenceTransformerReranker

def create_agents(settings, langfuse_client):
    # ... create other agents

    # Create reranker (optional based on config)
    reranker = None
    if settings.reranker.enabled:
        rerank_model = SentenceTransformerReranker(
            model_name=settings.reranker.model
        )
        reranker = RerankerAgent(
            rerank_model=rerank_model,
            langfuse_client=langfuse_client,
            agent_config={
                "name": settings.reranker.name,
                "top_k": settings.reranker.top_k
            }
        )

    # Create workflow with reranker
    workflow = AgentWorkflow(
        orchestrator=orchestrator,
        clarification=clarification,
        research=research,
        synthesis=synthesis,
        reranker=reranker  # Pass reranker
    )

    return workflow.build()
```

### Step 5: Add Configuration

Add configuration in `configs/agents/langgraph.yaml`.

```yaml
reranker:
  enabled: true
  name: "reranker"
  model: "cross-encoder/ms-marco-MiniLM-L-12-v2"
  top_k: 5
```

### Step 6: Write Tests

Create tests in `tests/agents/test_reranker.py`.

```python
# tests/agents/test_reranker.py
import pytest
from src.agents.reranker import RerankerAgent
from src.graph.state import create_initial_state
from langchain_core.messages import HumanMessage

def test_reranker_agent():
    """Test reranker reorders documents by relevance."""
    # Mock rerank model
    class MockReranker:
        def rerank(self, query, documents, top_k):
            # Reverse order for testing
            return list(reversed(documents))

    # Create agent
    reranker = RerankerAgent(rerank_model=MockReranker())

    # Create state with documents
    state = create_initial_state(
        messages=[HumanMessage("test query")],
        session_id="test-123"
    )
    state["context"]["pdf_results"] = [
        {"text": "doc1", "score": 0.5},
        {"text": "doc2", "score": 0.8},
        {"text": "doc3", "score": 0.3},
    ]

    # Execute
    result = reranker.execute(state)

    # Verify reranking happened
    assert result["context"]["reranked"] is True
    assert result["next_agent"] == "synthesis"
    assert len(result["context"]["pdf_results"]) == 3
    # Check order reversed (doc3, doc2, doc1)
    assert result["context"]["pdf_results"][0]["text"] == "doc3"
```

---

## Testing Agents

### Unit Testing Individual Agents

Test each agent in isolation with mock dependencies.

#### Testing Orchestrator

```python
# tests/agents/test_orchestrator.py
import pytest
from src.agents.orchestrator import MasterOrchestrator
from src.graph.state import create_initial_state
from langchain_core.messages import HumanMessage

def test_orchestrator_routes_to_clarification():
    """Test vague query routes to clarification."""
    # Mock LLM client
    class MockLLM:
        def generate(self, prompt_variables, **kwargs):
            return "CLARIFICATION: Query is too vague"

    orchestrator = MasterOrchestrator(
        llm_client=MockLLM(),
        agent_config={"max_clarifications": 2}
    )

    state = create_initial_state(
        messages=[HumanMessage("Tell me more about it")],
        session_id="test-123"
    )

    result = orchestrator.execute(state)

    assert result["next_agent"] == "clarification"
    assert result["clarification_needed"] is True
    assert result["clarification_count"] == 1


def test_orchestrator_routes_to_research():
    """Test clear query routes to research."""
    class MockLLM:
        def generate(self, prompt_variables, **kwargs):
            return "RESEARCH: Query is clear"

    orchestrator = MasterOrchestrator(llm_client=MockLLM())

    state = create_initial_state(
        messages=[HumanMessage("What's in Zhang et al. Table 2?")],
        session_id="test-123"
    )

    result = orchestrator.execute(state)

    assert result["next_agent"] == "research"
    assert result["clarification_needed"] is False


def test_orchestrator_max_clarifications():
    """Test emergency brake prevents infinite loops."""
    orchestrator = MasterOrchestrator(
        llm_client=MockLLM(),
        agent_config={"max_clarifications": 2}
    )

    state = create_initial_state(
        messages=[HumanMessage("Still unclear")],
        session_id="test-123"
    )
    state["clarification_count"] = 2  # Already at max

    result = orchestrator.execute(state)

    assert result["next_agent"] == "research"  # Forced to research
    assert result["clarification_count"] == 0  # Reset
```

#### Testing Research Agent

```python
# tests/agents/test_research.py
def test_research_uses_pdf_tool():
    """Test research uses PDF tool for paper queries."""
    # Mock LangChain agent
    class MockAgent:
        def invoke(self, inputs):
            return {
                "messages": [
                    AIMessage(content="Found results in papers",
                             tool_calls=[{"name": "pdf_retrieval"}])
                ]
            }

    research = ResearchSupervisor(
        llm=mock_llm,
        tools=[mock_pdf_tool],
        agent_config={}
    )
    research.agent = MockAgent()

    state = create_initial_state(
        messages=[HumanMessage("What is DAIL-SQL?")],
        session_id="test"
    )

    result = research.execute(state)

    assert "pdf_retrieval" in result["context"]["tool_history"]
    assert result["next_agent"] == "synthesis"
```

### Integration Testing Workflows

Test complete workflows with multiple agents.

```python
# tests/integration/test_workflow.py
def test_full_clarification_loop():
    """Test clarification → user response → research flow."""
    workflow = create_test_workflow()

    # Round 1: Vague query triggers clarification
    state1 = workflow.invoke({
        "messages": [HumanMessage("Tell me about accuracy")],
        "session_id": "test-integration"
    })

    assert "clarification" in state1["final_answer"].lower()
    assert state1["clarification_needed"] is True

    # Round 2: User clarifies, workflow proceeds to research
    state2 = workflow.invoke({
        "messages": state1["messages"] + [
            HumanMessage("Zhang et al. 2024 Table 2")
        ],
        "session_id": "test-integration"
    })

    assert state2["final_answer"] is not None
    assert "Zhang et al." in state2["final_answer"]
    assert state2["clarification_needed"] is False
```

### Mocking for Tests

#### Mock LLM Responses

```python
class MockLLM:
    def generate(self, prompt_variables, **kwargs):
        query = prompt_variables.get("query", "")
        if "vague" in query.lower():
            return "CLARIFICATION: Query is ambiguous"
        else:
            return "RESEARCH: Query is clear"
```

#### Mock Tools

```python
class MockPDFTool:
    name = "pdf_retrieval"
    description = "Search academic papers"

    def _run(self, query: str) -> str:
        return json.dumps([
            {"text": "Mock result", "source": "paper.pdf", "page": 1}
        ])
```

#### Mock Langfuse Client

```python
class MockLangfuse:
    def trace_generation(self, **kwargs):
        pass  # No-op for testing

    def get_prompt(self, name, label=None):
        return MockPrompt()

class MockPrompt:
    def compile(self, **kwargs):
        return "Mock prompt template"
```

---

## Best Practices

### 1. Keep Agents Stateless

**Good:**
```python
def execute(self, state: AgentState) -> AgentState:
    # All state passed explicitly
    query = state["messages"][-1].content
    return state
```

**Bad:**
```python
def execute(self, state: AgentState) -> AgentState:
    # Don't store state in instance
    self.current_query = state["messages"][-1].content  # ❌ BAD
    return state
```

**Why:** Instance state causes issues with serialization, testing, and concurrency.

### 2. Use Type Hints Everywhere

```python
from typing import Optional, Dict, Any

def execute(self, state: AgentState) -> AgentState:
    messages: Sequence[BaseMessage] = state["messages"]
    next_agent: str = "research"
    config: Dict[str, Any] = self.agent_config

    return state
```

**Benefits:** IDE autocomplete, type checking, self-documenting code.

### 3. Log Decisions and Context

```python
import logging

logger = logging.getLogger(__name__)

def execute(self, state: AgentState) -> AgentState:
    query = state["messages"][-1].content

    logger.info(
        f"{self.name}: Processing query",
        extra={
            "agent": self.name,
            "session_id": state["session_id"],
            "query_length": len(query),
            "iteration": state["iteration"]
        }
    )

    # ... agent logic

    logger.info(
        f"{self.name}: Routing to {next_agent}",
        extra={
            "agent": self.name,
            "next_agent": next_agent,
            "decision_reason": "..."
        }
    )

    return state
```

### 4. Handle Errors Gracefully

```python
def execute(self, state: AgentState) -> AgentState:
    try:
        result = self.llm_client.generate(...)
    except Exception as e:
        logger.error(
            f"{self.name}: LLM call failed: {e}",
            exc_info=True
        )
        # Fallback behavior
        state["next_agent"] = "synthesis"
        state["context"]["error"] = str(e)
        state["iteration"] += 1
        return state

    # Normal flow
    return state
```

**Key Points:**
- Always catch exceptions
- Log with stack trace (`exc_info=True`)
- Provide fallback behavior
- Don't break the workflow

### 5. Make Agents Observable

```python
def execute(self, state: AgentState) -> AgentState:
    query = state["messages"][-1].content

    # Trace with Langfuse
    if self.langfuse_client:
        self.langfuse_client.trace_generation(
            name=self.name,
            session_id=state.get("session_id"),
            input_data={"query": query},
            output=response,
            model=self.llm_client.completion_model,
            metadata={
                "agent": self.name,
                "iteration": state["iteration"],
                "next_agent": state["next_agent"]
            }
        )

    return state
```

### 6. Document Agent Responsibilities

```python
class RerankerAgent(BaseAgent):
    """Rerank retrieved documents for better relevance.

    Responsibility:
        - Reorder documents from research agent by relevance
        - Store reranked results in context
        - Route to synthesis

    Dependencies:
        - Rerank model (e.g., cross-encoder)
        - Langfuse client (optional)

    State Inputs:
        - context["pdf_results"]: Documents to rerank
        - messages[-1]: User query for relevance scoring

    State Outputs:
        - context["pdf_results"]: Reranked documents
        - next_agent: "synthesis"
    """
```

---

## Performance Optimization

### 1. Limit Message History

```python
def execute(self, state: AgentState) -> AgentState:
    # Don't send full conversation history to LLM
    max_history = 10
    messages = state["messages"][-max_history:]  # Only last 10

    response = self.llm_client.generate(
        prompt_variables={"history": self._format_history(messages)}
    )

    return state
```

**Benefit:** Reduces tokens, latency, and cost.

### 2. Use Fast Models for Routing

```python
# Orchestrator: Fast model (GPT-4o-mini, GPT-3.5-turbo)
orchestrator_llm = create_llm("gpt-4o-mini", temperature=0.3)

# Research: Powerful model (GPT-4o, GPT-4-turbo)
research_llm = create_llm("gpt-4o", temperature=0.7)
```

**Why:** Routing doesn't need advanced reasoning, save cost with fast models.

### 3. Cache Prompts

```python
def __init__(self, llm_client, langfuse_client, agent_config):
    super().__init__(agent_config.get("name", "agent"))

    # Load prompt once at init
    self.system_prompt = self._load_prompt(
        langfuse_client,
        agent_config.get("prompt")
    )

def execute(self, state: AgentState) -> AgentState:
    # Reuse cached prompt
    response = self.llm_client.generate(
        prompt=self.system_prompt,
        prompt_variables={"query": query}
    )
```

### 4. Batch Operations

```python
# Bad: Sequential API calls
for document in documents:
    embedding = embed_model.embed(document)

# Good: Batch API call
embeddings = embed_model.embed_batch(documents)
```

### 5. Use Async Where Possible

```python
import asyncio

async def execute_async(self, state: AgentState) -> AgentState:
    """Async version for concurrent execution."""
    query = state["messages"][-1].content

    # Concurrent LLM and tool calls
    response, metadata = await asyncio.gather(
        self.llm_client.generate_async(query),
        self.fetch_metadata_async(query)
    )

    return state
```

---

## Prompt Management

Each agent uses versioned prompts stored in Langfuse (or dotprompt files).

### Agent Prompts

| Agent | Prompt ID | Purpose |
|-------|-----------|---------|
| Orchestrator | `agent_orchestrator` | Intent classification (RESEARCH vs CLARIFICATION) |
| Clarification | `agent_clarification` | Generate clarifying questions for vague queries |
| Research | `agent_research` | ReAct planning and tool execution |
| Synthesis | `agent_synthesis` | Format final answer with citations |

### Loading Prompts at Runtime

```python
def __init__(self, llm_client, langfuse_client, agent_config):
    self.llm_client = llm_client
    self.langfuse_client = langfuse_client

    # Load prompt from Langfuse
    if langfuse_client:
        prompt_config = agent_config.get("prompt", {})
        self.prompt_obj = langfuse_client.get_prompt(
            name=prompt_config.get("id", "agent_default"),
            label=prompt_config.get("environment", "dev"),
            version=prompt_config.get("version")  # None = latest
        )
    else:
        self.prompt_obj = None

def execute(self, state: AgentState) -> AgentState:
    # Use prompt in generation
    response = self.llm_client.generate(
        prompt=self.prompt_obj,
        prompt_variables={"query": query}
    )
```

### Benefits of Langfuse Prompts

- **Version Control**: Track prompt changes over time
- **A/B Testing**: Compare prompt versions
- **Hot Reload**: Update prompts without code changes
- **Environment Separation**: Dev/staging/production prompts

See [Prompt Management Documentation](../prompts/README.md) for comprehensive guide.

---

## Observability

### Langfuse Integration

```python
if self.langfuse_client:
    self.langfuse_client.trace_generation(
        name=f"{self.name}_execution",
        session_id=state["session_id"],
        input_data={
            "query": query,
            "conversation_history": formatted_history,
        },
        output=response,
        model=self.llm_client.completion_model,
        prompt_name=self.prompt_obj.name if self.prompt_obj else None,
        metadata={
            "agent": self.name,
            "next_agent": state["next_agent"],
            "iteration": state["iteration"],
            "clarification_count": state.get("clarification_count", 0)
        }
    )
```

### Logged Information

- **Input**: User query and conversation history
- **Output**: Agent decision or response
- **Metadata**: Agent name, routing, iteration, etc.
- **Session**: Grouped by `session_id` for conversation tracking
- **Model**: Which LLM was used
- **Prompt**: Which prompt version was used

---

## Key Takeaways

1. **Follow the Pattern**: Inherit from `BaseAgent`, implement `execute()`
2. **Update Workflow**: Add nodes and edges to LangGraph
3. **Test Thoroughly**: Unit tests for agents, integration tests for workflows
4. **Keep It Stateless**: Don't store state in instance variables
5. **Log Everything**: Use structured logging for debugging
6. **Handle Errors**: Graceful degradation, don't break the workflow
7. **Optimize Performance**: Limit history, use fast models for routing
8. **Manage Prompts**: Use Langfuse for versioning and hot-reload
9. **Trace Execution**: Langfuse integration for observability

---

## See Also

- [Design Philosophy](./design-philosophy.md) - Core design principles
- [Agent Lifecycle](./agent-lifecycle.md) - State management and execution flow
- [Orchestrator Design](./orchestrator/design.md) - Routing implementation
- [Research Design](./research/design.md) - Tool usage patterns
- [Prompt Management](../prompts/README.md) - Prompt versioning strategy
