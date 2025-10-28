# Multi-Agent Orchestration

High-level architecture of the multi-agent system, autonomous decision-making patterns, and LangGraph workflow design.

## Table of Contents
- [System Overview](#system-overview)
- [Why Multi-Agent Architecture](#why-multi-agent-architecture)
- [Autonomous Decision-Making](#autonomous-decision-making)
- [LangGraph Workflow](#langgraph-workflow)
- [Loop Prevention Mechanisms](#loop-prevention-mechanisms)
- [Performance & Observability](#performance--observability)

---

## System Overview

The system uses a **multi-agent architecture** where specialized agents collaborate to answer queries:

```
User Query
    │
    ▼
┌─────────────────┐
│  Orchestrator   │  Analyze intent → Route to appropriate agent
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────────┐  ┌──────────┐
│Clarifica-│  │ Research │  PDF search + Web search (ReAct)
│  tion    │  │          │
└────┬─────┘  └────┬─────┘
     │             │
     │    ┌────────┘
     │    │
     ▼    ▼
   ┌──────────┐
   │Synthesis │  Format final answer with citations
   └──────────┘
        │
        ▼
   Final Answer
```

### Agent Roles

| Agent | Purpose | Decision Type |
|-------|---------|---------------|
| **Orchestrator** | Route queries to the right agent | Classification |
| **Clarification** | Ask questions when query is vague | Question Generation |
| **Research** | Gather information using tools | Multi-step ReAct |
| **Synthesis** | Format final answer with citations | Data Transformation |

**For detailed agent implementations**, see [Agent Documentation](../agents/README.md).

---

## Why Multi-Agent Architecture

### 1. Separation of Concerns

**Problem with Single Agent:**
```python
# One agent trying to do everything
prompt = """
You are an agent that:
1. Checks if query is clear
2. If vague, ask clarifying questions
3. If clear, search PDFs
4. If not in PDFs, search web
5. Format answer with citations
6. Track conversation state
... (complex 2000-token prompt)
"""
```

**Multi-Agent Solution:**
```python
# Each agent has ONE responsibility
Orchestrator:  "Is this clear or vague?" (50-token prompt)
Clarification: "Generate clarifying question" (100-token prompt)
Research:      "Find information using tools" (200-token prompt)
Synthesis:     "Format answer with citations" (150-token prompt)
```

**Benefits:**
- ✅ **Easier to prompt engineer**: Small, focused prompts
- ✅ **Easier to test**: Unit test each agent independently
- ✅ **Easier to maintain**: Change one agent without breaking others
- ✅ **Easier to optimize**: Use different models per agent

### 2. Testability

**Unit Testing Individual Agents:**
```python
def test_orchestrator_vague_query():
    state = create_state("tell me about it")
    result = orchestrator.execute(state)
    assert result["next_agent"] == "clarification"

def test_research_pdf_retrieval():
    state = create_state("What's in Zhang et al. Table 2?")
    result = research.execute(state)
    assert "pdf_retrieval" in result["context"]["tool_history"]
```

**Integration Testing Workflows:**
```python
def test_full_clarification_loop():
    # Vague query → Clarification
    state1 = workflow.invoke("tell me about accuracy")
    assert "clarification" in state1["messages"][-1].content

    # Clarified query → Research → Answer
    state2 = workflow.invoke("accuracy in Zhang et al.")
    assert state2["final_answer"] is not None
```

### 3. Extensibility

**Adding New Agents:**
```python
# Add a reranking agent between research and synthesis
workflow.add_node("reranker", reranker.execute)
workflow.add_edge("research", "reranker")
workflow.add_edge("reranker", "synthesis")
```

**Adding New Tools:**
```python
# Add database query tool to research agent
tools = [
    PDFRetrievalTool(),
    WebSearchTool(),
    DatabaseQueryTool(),  # NEW
]
research = ResearchSupervisor(llm, tools)
```

### 4. Observability

**Per-Agent Tracing in Langfuse:**
```
Session: user-123-abc
├── orchestrator (50ms)
│   └── decision: research
├── research (3.2s)
│   ├── pdf_retrieval (1.1s)
│   └── web_search (2.1s)
└── synthesis (800ms)
    └── confidence: 0.95
```

Each agent logs independently, making debugging straightforward.

---

## Autonomous Decision-Making

### No Hard-Coded Rules

**Traditional Rule-Based Approach (Anti-Pattern):**
```python
# ❌ Brittle, requires constant updates
if "latest" in query or "recent" in query:
    use_web_search()
elif "paper" in query or "Table" in query:
    use_pdf_retrieval()
else:
    ask_clarification()
```

**Problems:**
- Breaks on synonyms ("newest", "current", "up-to-date")
- Can't handle complex combinations
- Requires manual rule updates
- No context awareness

### LLM-Based Semantic Routing

**Our Approach:**
```python
# ✅ LLM analyzes query semantically
decision = llm.generate(
    prompt=f"""
    Analyze this query and decide the best action:
    Query: {query}
    History: {conversation_history}

    Options:
    - CLARIFICATION: Query is vague or ambiguous
    - RESEARCH: Query is clear and specific

    Consider:
    - Is the user asking about a specific paper/table/metric?
    - Is there enough context to provide a good answer?
    - Has clarification already been attempted?
    """
)
```

**Benefits:**
- ✅ Handles synonyms and paraphrasing naturally
- ✅ Context-aware (considers conversation history)
- ✅ Adapts to edge cases without code changes
- ✅ Explains reasoning (for debugging)

### Structured Output for Reliability

**Using JSON mode for deterministic parsing:**
```python
decision = llm.generate(
    prompt=prompt,
    response_format={
        "type": "json_schema",
        "schema": {
            "action": "CLARIFICATION | RESEARCH",
            "reasoning": "string",
            "confidence": "float"
        }
    }
)

# Parse and route
action = json.loads(decision)["action"]
```

This prevents parsing errors and ensures reliable routing.

---

## LangGraph Workflow

### State Graph Structure

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)

# Add nodes (agents)
workflow.add_node("orchestrator", orchestrator.execute)
workflow.add_node("clarification", clarification.execute)
workflow.add_node("research", research.execute)
workflow.add_node("synthesis", synthesis.execute)

# Entry point
workflow.set_entry_point("orchestrator")

# Conditional routing
def route_after_orchestrator(state):
    return state["next_agent"]  # "clarification" or "research"

workflow.add_conditional_edges(
    "orchestrator",
    route_after_orchestrator,
    {
        "clarification": "clarification",
        "research": "research"
    }
)

# Terminal edges
workflow.add_edge("clarification", END)  # Wait for user
workflow.add_edge("research", "synthesis")
workflow.add_edge("synthesis", END)

# Compile with checkpointer for conversation state
graph = workflow.compile(checkpointer=redis_checkpointer)
```

**Code Reference:** `src/graph/workflow.py:97`

### Why LangGraph?

**Advantages over custom orchestration:**
1. **Built-in state management**: Redis checkpointing for conversation memory
2. **Conditional routing**: Type-safe routing with compile-time validation
3. **Streaming support**: Stream agent outputs in real-time
4. **Visualization**: Auto-generate workflow diagrams
5. **Debugging**: Built-in state inspection and replay
6. **Production-ready**: Handles errors, retries, timeouts

### Agent Communication via Shared State

**State Flow Example:**
```python
# Initial state
state = {
    "messages": [HumanMessage("What's the accuracy?")],
    "session_id": "user-123",
    "next_agent": "orchestrator",
    "context": {}
}

# After orchestrator
state = {
    "messages": [...],
    "next_agent": "research",  # Updated by orchestrator
    "clarification_needed": False
}

# After research
state = {
    "messages": [...],
    "next_agent": "synthesis",
    "context": {
        "observations": ["Used pdf_retrieval", "Found 3 docs"],
        "tool_history": ["pdf_retrieval"],
        "final_output": "Zhang et al. reports 87.3%"
    }
}

# After synthesis
state = {
    "messages": [..., AIMessage("According to Zhang et al...")],
    "final_answer": "According to Zhang et al...",
    "confidence_score": 0.95,
    "next_agent": "END"
}
```

**Code Reference:** `src/graph/state.py:13`

---

## Loop Prevention Mechanisms

### Problem: Infinite Clarification Loops

**Failure Scenario:**
```
User: "Tell me about accuracy"
Agent: "Which accuracy?"
User: "The one in the paper"  (Still vague!)
Agent: "Which paper?"
User: "The main one"  (Still vague!)
Agent: "Which main one?"
... (Infinite loop)
```

### Solution: Three-Layer Protection

#### Layer 1: Counter Limit (Emergency Brake)

```python
MAX_CLARIFICATIONS = 2

if clarification_count >= MAX_CLARIFICATIONS:
    logger.warning("Max clarifications reached, forcing research")
    route_to("research")  # Force progress even if vague
```

**Behavior:** After 2 clarifications, proceed anyway (best effort)

#### Layer 2: Pattern Detection (Follow-up Detection)

```python
if len(messages) >= 2:
    prev_msg = messages[-2]  # AI clarification question
    curr_msg = messages[-1]  # Human response
    last_agent = state.get("last_agent")

    if (isinstance(prev_msg, AIMessage) and
        isinstance(curr_msg, HumanMessage) and
        last_agent == "clarification"):

        logger.info("Clarification follow-up detected, routing to research")
        route_to("research")
```

**Behavior:** If user responds to clarification, assume they provided context

**Code Reference:** `src/agents/orchestrator.py:80`

#### Layer 3: LLM Decision (Context-Aware)

```python
decision = llm.analyze(
    query=current_query,
    history=conversation_history,
    clarification_count=clarification_count
)
```

**Prompt Engineering:**
```
You have already asked for clarification {clarification_count} times.
If the user has provided any additional context, proceed to RESEARCH.
Only request CLARIFICATION if the query is truly impossible to answer.
```

**Behavior:** LLM considers clarification history in decision

### Layer Activation Example

**Conversation:**
```
Turn 1:
User: "Tell me about accuracy"
Orchestrator: Layer 3 → Clarification (count=1)
Clarification: "Which model?"

Turn 2:
User: "The deep learning one"
Orchestrator: Layer 2 → Research (follow-up pattern detected)
Research: Proceeds with best interpretation

Turn 3 (if Layer 2 failed):
User: "What about the neural model?"
Orchestrator: Layer 1 → Research (count=2, emergency brake)
Research: Proceeds with best interpretation
```

**Design Rationale:**
- **Layer 1** ensures forward progress (no infinite loops)
- **Layer 2** improves UX (don't over-clarify)
- **Layer 3** uses semantic understanding (handles edge cases)

---

## Performance & Observability

### Latency Breakdown

| Stage | Typical Latency | Notes |
|-------|----------------|-------|
| Orchestrator | 100-300ms | Fast LLM call (GPT-4o-mini) |
| Clarification | 200-500ms | Question generation |
| Research (PDF only) | 1-2s | Embedding + Qdrant + LLM |
| Research (PDF + Web) | 3-5s | Additional Tavily API call |
| Synthesis | 500-1000ms | Answer formatting |
| **Total (simple)** | **2-3s** | PDF-only research |
| **Total (complex)** | **4-7s** | PDF + Web research |

### Concurrency

**Session Isolation:**
- Each session has unique `thread_id`
- Redis checkpointer prevents cross-contamination
- Parallel requests handled independently

**Future Optimization:**
```python
# Sequential (current)
pdf_results = pdf_tool(query)
web_results = web_tool(query)

# Parallel (future)
pdf_results, web_results = await asyncio.gather(
    pdf_tool_async(query),
    web_tool_async(query)
)
```

### Debugging Strategy

**Structured Logging:**
```python
logger.info(
    f"{agent_name}: Decision={decision}",
    extra={
        "agent": agent_name,
        "session_id": session_id,
        "decision": decision,
        "clarification_count": clarification_count
    }
)
```

**Langfuse Tracing:**
```python
# Automatic tracing per agent
langfuse.trace_generation(
    name=agent_name,
    input_data=prompt_variables,
    output=response,
    model=model_name,
    session_id=session_id
)
```

**State Inspection:**
```python
# Get current state of a session
state = workflow.get_thread_state(thread_id="user-123")
print(f"Messages: {len(state['messages'])}")
print(f"Last agent: {state.get('last_agent')}")
print(f"Clarification count: {state.get('clarification_count')}")
```

---

## Design Decisions

### Why Multiple Agents Instead of One?

**Considered alternatives:**
1. **Single monolithic agent** - Rejected due to complexity, hard to test
2. **Function calling** - Rejected due to lack of control flow
3. **Chain-of-thought** - Rejected due to unpredictable behavior

**Chosen approach: Multi-agent with explicit workflow**

**Rationale:**
- ✅ Clear separation of responsibilities
- ✅ Testable in isolation
- ✅ Observable per-agent metrics
- ✅ Extensible without breaking existing agents
- ✅ Explicit control flow (no LLM decides "what to do next")

### Why LangGraph Instead of Custom Orchestration?

**Considered alternatives:**
1. **Custom state machine** - Rejected due to reinventing the wheel
2. **LangChain LCEL** - Rejected due to lack of conditional routing
3. **Raw function calls** - Rejected due to no state management

**Chosen approach: LangGraph StateGraph**

**Rationale:**
- ✅ Built-in state management (Redis checkpointing)
- ✅ Type-safe conditional routing
- ✅ Production-ready (errors, retries, streaming)
- ✅ Visualization and debugging tools
- ✅ Active development and community support

### Why Autonomous Routing Instead of Rules?

**Considered alternatives:**
1. **Keyword matching** - Rejected due to brittleness
2. **Regex patterns** - Rejected due to complexity
3. **Intent classification model** - Rejected due to training overhead

**Chosen approach: LLM-based semantic routing**

**Rationale:**
- ✅ Handles natural language variations
- ✅ Context-aware decisions
- ✅ No training data required
- ✅ Adapts to edge cases
- ✅ Explainable (LLM provides reasoning)

---

## Next Steps

**For detailed agent information:**
1. [Agent Documentation](../agents/README.md) - Overview of all agents
2. [Orchestrator Design](../agents/orchestrator/design.md) - Routing logic details
3. [Research Design](../agents/research/design.md) - ReAct pattern implementation
4. [Clarification Design](../agents/clarification/design.md) - Vagueness detection

**For related architecture topics:**
1. [RAG Strategy](../rag/retrieval-strategy.md) - Retrieval and reranking
2. [Design Decisions](architecture-decisions.md) - Architectural trade-offs
3. [System Overview](system-overview.md) - Complete system architecture
4. [API Reference](../api/endpoints.md) - API integration examples
