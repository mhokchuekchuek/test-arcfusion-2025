# Orchestrator Agent Design

## Agent Responsibility

The **Orchestrator** is the master router that analyzes user queries to determine the next action in the workflow. It classifies user intent and routes to appropriate downstream agents:

- **Clarification Agent**: When query is vague, ambiguous, or underspecified
- **Research Agent**: When query is clear and needs information retrieval
- **END**: When workflow should terminate

**Location**: `src/agents/orchestrator.py:1`

---

## Decision Logic

The Orchestrator uses a **three-layer system** for intelligent routing with loop prevention:

### Layer 1: Counter Limit (Emergency Brake)

**Purpose**: Guarantee no infinite clarification loops

```python
# Check clarification count first
if state["clarification_count"] >= self.max_clarifications:
    # Force research after max clarifications
    state["next_agent"] = "research"
    state["clarification_count"] = 0
    logger.info(f"Max clarifications ({self.max_clarifications}) reached. Forcing research.")
    return state
```

**Configuration**: `max_clarifications = 2` (configurable in `configs/agents/langgraph.yaml`)

**Behavior**:
- Tracks total clarifications in conversation
- After 2 clarifications, forces research even if query still vague
- Resets counter when research begins

---

### Layer 2: Pattern Detection (Smart Skip)

**Purpose**: Detect when user responds to clarification question

```python
# Check if last agent was clarification and user just responded
last_agent = state.get("last_agent")
messages = state.get("messages", [])

if last_agent == "clarification" and len(messages) >= 2:
    # Check AI→Human pattern (clarification followed by user response)
    if isinstance(messages[-2], AIMessage) and isinstance(messages[-1], HumanMessage):
        # User is responding to clarification, skip LLM and go to research
        state["next_agent"] = "research"
        state["last_agent"] = "orchestrator"
        logger.info("User responded to clarification. Routing directly to research.")
        return state
```

**Detection Logic**:
1. Check if `last_agent == "clarification"`
2. Verify message pattern: `[..., AIMessage (clarification), HumanMessage (response)]`
3. If pattern matches, user is providing requested context
4. Skip expensive LLM call and route directly to research

**Benefits**:
- Reduces latency (no LLM call needed)
- Saves costs (one less API call per conversation)
- Better UX (faster response)

---

### Layer 3: LLM Decision (Context-Aware)

**Purpose**: Intelligent routing based on conversation context

```python
# Format conversation history
formatted_history = self._format_conversation_history(
    messages=messages[-self.max_history:]
)

# Get prompt from Langfuse (or fallback)
prompt_variables = {
    "conversation_history": formatted_history,
    "clarification_count": clarification_count,
    "max_clarifications": self.max_clarifications,
}

# LLM analyzes intent
decision = self.llm_client.generate(
    prompt_variables=prompt_variables,
    prompt=self.prompt_obj,
    temperature=self.temperature,
)

# Parse decision
if "CLARIFICATION" in decision.upper():
    state["next_agent"] = "clarification"
    state["clarification_count"] = clarification_count + 1
elif "RESEARCH" in decision.upper():
    state["next_agent"] = "research"
    state["clarification_count"] = 0  # Reset on successful research
else:
    # Default to research
    state["next_agent"] = "research"
```

**Prompt Structure** (Langfuse: `agent_orchestrator`):
```
You are the Orchestrator agent in a multi-agent RAG system.

Conversation History:
{{conversation_history}}

Current Clarification Count: {{clarification_count}}/{{max_clarifications}}

Analyze the latest message and decide:
- CLARIFICATION: If query is vague, ambiguous, or missing key context
- RESEARCH: If query is clear and actionable

Think carefully about:
- Is the user's intent clear?
- Are there ambiguous pronouns ("it", "that", "this")?
- Is the scope well-defined?
- Has the user already provided sufficient context?

Decision: [CLARIFICATION | RESEARCH]
Reasoning: [Brief explanation]
```

**Configuration**:
- Model: `gpt-4-turbo` (configurable)
- Temperature: `0.3` (low for consistent routing)
- Max history: `10` messages
- Prompt source: Langfuse with fallback to dotprompt

---

## Autonomous Decision-Making

The Orchestrator uses **context-aware LLM analysis** rather than hard-coded rules.

### What It Does NOT Do

❌ **No keyword matching**:
```python
# Bad: Hard-coded rules
if "latest" in query or "current" in query:
    return "web_search"
if "paper" in query or "study" in query:
    return "pdf_search"
```

### What It DOES Do

✅ **Contextual analysis**:
```python
# Good: LLM understands context
decision = llm.analyze(
    query="Tell me more about it",
    conversation_history=[
        "User: What's the best approach for text-to-SQL?",
        "AI: Several approaches include...",
        "User: Tell me more about it"  # "it" is ambiguous
    ]
)
# Returns: CLARIFICATION (pronoun "it" lacks clear antecedent)
```

### Why This Matters

**Handles complex scenarios** that rules cannot:
- Multi-turn context dependencies
- Implicit references and pronouns
- Scope ambiguity ("best" for what metric?)
- Intent changes mid-conversation

---

## Example Decisions

| Query | Conversation Context | Decision | Reasoning |
|-------|---------------------|----------|-----------|
| "Tell me more about it" | Previous: "RAG systems use retrieval..." | **CLARIFICATION** | Pronoun "it" is ambiguous. Ask what aspect user wants to know. |
| "Which prompt gave highest accuracy in Zhang 2024?" | First message | **RESEARCH** | Specific paper and metric. Clear intent for PDF search. |
| "What did OpenAI release this month?" | First message | **RESEARCH** | Time-sensitive query. Research agent will use web search. |
| "The best approach" | First message | **CLARIFICATION** | Missing context: best for what problem? What metric? |
| "How many examples are enough?" | Previous: "I'm working on classification" | **CLARIFICATION** | Underspecified: enough for what accuracy target? |
| "Use the approach from the paper" | No previous paper mentioned | **CLARIFICATION** | Missing context: which paper? |
| "I meant the DAIL-SQL approach" | After clarification | **RESEARCH** | User responded to clarification. Pattern detection triggers research. |

---

## State Updates

The Orchestrator modifies state to control workflow routing:

```python
def execute(self, state: AgentState) -> AgentState:
    # 1. Analyze and decide
    decision = self._make_routing_decision(state)

    # 2. Update routing state
    state["next_agent"] = decision["next_agent"]  # "clarification" | "research"
    state["last_agent"] = "orchestrator"           # Mark execution

    # 3. Update clarification tracking
    if decision["next_agent"] == "clarification":
        state["clarification_count"] = state.get("clarification_count", 0) + 1
    elif decision["next_agent"] == "research":
        state["clarification_count"] = 0  # Reset on research

    # 4. Update iteration counter
    state["iteration"] = state.get("iteration", 0) + 1

    # 5. Preserve conversation history (managed by LangGraph)
    # state["messages"] automatically accumulated by LangGraph

    return state
```

### State Fields Modified

| Field | Type | Purpose |
|-------|------|---------|
| `next_agent` | str | Controls LangGraph conditional edge |
| `last_agent` | str | Enables pattern detection |
| `clarification_count` | int | Loop prevention counter |
| `iteration` | int | Tracks workflow steps |
| `messages` | Sequence[BaseMessage] | Preserved by LangGraph |

---

## Integration with LangGraph

### Workflow Definition

**Location**: `src/graph/workflow.py:45`

```python
# Add orchestrator node
workflow.add_node("orchestrator", self.orchestrator.execute)

# Conditional routing based on orchestrator decision
workflow.add_conditional_edges(
    "orchestrator",
    self._route_from_orchestrator,
    {
        "clarification": "clarification",
        "research": "research",
    }
)

def _route_from_orchestrator(self, state: AgentState) -> str:
    """Route based on orchestrator's decision."""
    return state["next_agent"]
```

### Visual Flow

```
START
  │
  ▼
orchestrator (analyze intent)
  │
  ├─→ "clarification" → clarification_agent → END (wait for user)
  │                         │
  │                         └─→ orchestrator (user responds)
  │                                │
  └─→ "research" ──────────────────┘
                  │
                  ▼
              research_agent → synthesis_agent → END
```

---

## Configuration

### Settings File

**Location**: `configs/agents/langgraph.yaml`

```yaml
orchestrator:
  name: "orchestrator"
  model: "gpt-4-turbo"
  temperature: 0.3  # Low for consistent routing
  max_history: 10   # Context window (messages)
  max_clarifications: 2  # Loop prevention limit
  prompt: "agent_orchestrator"  # Langfuse prompt name
```

### Initialization

**Location**: `src/apis/dependencies/agents.py:87`

```python
# Create LLM client
orchestrator_llm = LLMClientSelector.create(
    provider=settings.rag.llm.provider,
    proxy_url=settings.llm.proxy_url,
    completion_model=settings.orchestrator.model,
    temperature=settings.orchestrator.temperature,
)

# Create orchestrator agent
orchestrator = OrchestratorAgent(
    llm_client=orchestrator_llm,
    langfuse_client=langfuse_client,
    prompt=settings.orchestrator.prompt,
    name=settings.orchestrator.name,
    max_history=settings.orchestrator.max_history,
    max_clarifications=settings.orchestrator.max_clarifications,
)
```

---

## Observability & Tracing

### Langfuse Integration

```python
# Trace orchestrator decision
self.langfuse_client.trace_generation(
    name=f"{self.name}_decision",
    session_id=state["session_id"],
    input_data={
        "conversation_history": formatted_history,
        "clarification_count": clarification_count,
    },
    output=decision,
    model=self.llm_client.completion_model,
    prompt_name=self.prompt,
    metadata={
        "agent": self.name,
        "next_agent": state["next_agent"],
        "iteration": state["iteration"],
    }
)
```

### Logged Information

- **Input**: Conversation history, clarification count
- **Output**: Routing decision + reasoning
- **Metadata**: Agent name, next agent, iteration number
- **Session**: Grouped by `session_id` for conversation tracking

---

## Error Handling

### Fallback Strategy

```python
try:
    decision = self.llm_client.generate(prompt_variables)
except Exception as e:
    logger.error(f"Orchestrator LLM call failed: {e}")
    # Fallback to research (safer than clarification loop)
    state["next_agent"] = "research"
    state["last_agent"] = "orchestrator"
    return state
```

### Why Fallback to Research?

- **Safer default**: Research can handle any query
- **Avoids loops**: Clarification could trap user if LLM fails repeatedly
- **Better UX**: User gets best-effort answer vs. stuck in error state

---

## Performance Considerations

### Latency Optimization

**Pattern Detection** (Layer 2) saves ~500-1000ms per conversation turn:

| Scenario | Layer 1 | Layer 2 | Layer 3 (LLM) | Total Time |
|----------|---------|---------|---------------|------------|
| Initial query | ✓ | ✓ | ✓ (LLM call) | ~800ms |
| Response to clarification | ✓ | ✓ (skip LLM) | ✗ | ~10ms |
| Max clarifications | ✓ (force research) | ✗ | ✗ | ~5ms |

**Cost Savings**: ~50% reduction in orchestrator LLM calls for clarification workflows

### Context Window Management

```python
# Limit history to prevent token overflow
formatted_history = self._format_conversation_history(
    messages=messages[-self.max_history:]  # Last 10 messages
)
```

**Token Budget**:
- Max history: 10 messages
- Average: ~200 tokens/message
- Total context: ~2,000 tokens
- Leaves headroom for prompt and completion

---

## Testing

### Unit Tests

```python
def test_orchestrator_clarification_routing():
    state = {
        "messages": [HumanMessage(content="Tell me more about it")],
        "clarification_count": 0,
    }

    result = orchestrator.execute(state)

    assert result["next_agent"] == "clarification"
    assert result["clarification_count"] == 1

def test_orchestrator_max_clarifications():
    state = {
        "messages": [HumanMessage(content="Still unclear")],
        "clarification_count": 2,  # Already at max
    }

    result = orchestrator.execute(state)

    assert result["next_agent"] == "research"  # Forced
    assert result["clarification_count"] == 0   # Reset
```

### Integration Tests

```python
def test_orchestrator_pattern_detection():
    state = {
        "messages": [
            AIMessage(content="What aspect would you like to know about?"),
            HumanMessage(content="The implementation details")
        ],
        "last_agent": "clarification",
        "clarification_count": 1,
    }

    result = orchestrator.execute(state)

    # Should skip LLM and route to research
    assert result["next_agent"] == "research"
    assert result["clarification_count"] == 1  # Not incremented
```

---

## Key Takeaways

1. **Three-Layer System**: Counter limit, pattern detection, LLM decision
2. **Loop Prevention**: Guaranteed termination after 2 clarifications
3. **Context-Aware**: LLM analyzes full conversation, not just keywords
4. **Pattern Detection**: Skips LLM call when user responds to clarification
5. **State Management**: Updates routing flags for LangGraph conditional edges
6. **Observability**: Full tracing to Langfuse for debugging
7. **Fallback Strategy**: Defaults to research on errors
8. **Performance**: Optimized for latency and cost

The Orchestrator routes requests through the multi-agent workflow using a three-layer system to prevent infinite clarification loops.
