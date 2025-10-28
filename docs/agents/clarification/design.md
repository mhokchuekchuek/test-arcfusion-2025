# Clarification Agent Design

## Agent Responsibility

The **Clarification Agent** detects and resolves vague, ambiguous, or underspecified queries by generating targeted clarifying questions. It works in tandem with the Orchestrator to prevent infinite clarification loops while ensuring user intent is properly understood.

**Location**: `src/agents/clarification.py:1`

---

## Vagueness Detection

The Clarification Agent handles three types of unclear queries:

### 1. Missing Context

Queries that reference previous information not in conversation history.

**Examples**:
| Vague Query | Issue | Clarifying Question |
|-------------|-------|---------------------|
| "Tell me more about it" | Pronoun "it" lacks antecedent | "What specific topic would you like to know more about?" |
| "How does that work?" | "That" is undefined | "What system or approach are you asking about?" |
| "Use the method from the paper" | Which paper? | "Which paper are you referring to?" |

### 2. Ambiguous References

Queries with multiple possible interpretations.

**Examples**:
| Ambiguous Query | Issue | Clarifying Question |
|-----------------|-------|---------------------|
| "The best approach" | Best for what metric? What problem? | "Best approach for what specific task and evaluation metric?" |
| "Recent advances" | How recent? Which field? | "Recent advances in which specific area of research?" |
| "Compare them" | Which entities? | "Which specific methods or systems would you like compared?" |

### 3. Underspecified Parameters

Queries missing critical details for proper response.

**Examples**:
| Underspecified Query | Issue | Clarifying Question |
|---------------------|-------|---------------------|
| "How many examples are enough?" | Enough for what task/accuracy? | "Enough examples for what task and desired accuracy level?" |
| "Which dataset should I use?" | For what problem? What constraints? | "What task are you working on and what are your dataset requirements?" |
| "What's a good learning rate?" | For which model/optimizer? | "For which model architecture and training setup?" |

---

## Loop Prevention Strategy

The Clarification Agent implements a **multi-layer defense** against infinite loops:

### Layer 1: State Tracking

The agent marks its execution in state for the Orchestrator to detect:

```python
def execute(self, state: AgentState) -> AgentState:
    # Generate clarifying question
    clarification = self._generate_clarification(state)

    # Mark execution
    state["last_agent"] = "clarification"

    # Add question to conversation
    state["messages"].append(AIMessage(content=clarification))

    # Set as final answer (returned to user)
    state["final_answer"] = clarification

    # End workflow (wait for user response)
    state["next_agent"] = "END"

    return state
```

**Key Insight**: By setting `last_agent = "clarification"`, the Orchestrator can detect when user responds and skip clarification.

---

### Layer 2: Orchestrator Counter

The Orchestrator tracks total clarifications:

```python
# In Orchestrator
if state["clarification_count"] >= self.max_clarifications:
    # Force research after max clarifications
    state["next_agent"] = "research"
    state["clarification_count"] = 0
```

**Configuration**: `max_clarifications = 2` (configurable in `configs/agents/langgraph.yaml`)

---

### Layer 3: Pattern Detection

The Orchestrator detects AI→Human message pattern:

```python
# In Orchestrator
if last_agent == "clarification" and len(messages) >= 2:
    if isinstance(messages[-2], AIMessage) and isinstance(messages[-1], HumanMessage):
        # User responded to clarification, skip LLM and route to research
        state["next_agent"] = "research"
```

**Behavior**: When user responds to clarification, Orchestrator bypasses LLM decision and routes directly to research.

---

### Visual Loop Prevention Flow

```
User: "Tell me more about it" (vague)
  │
  ▼
Orchestrator (Layer 3: LLM decides)
  ├─→ Decision: CLARIFICATION
  └─→ clarification_count: 0 → 1
  │
  ▼
Clarification Agent
  ├─→ Generates: "What would you like to know more about?"
  ├─→ Sets: last_agent = "clarification"
  └─→ Returns to user
  │
  ▼
User: "The DAIL-SQL approach" (responds)
  │
  ▼
Orchestrator (Layer 2: Pattern Detection)
  ├─→ Detects: last_agent == "clarification" + AI→Human pattern
  ├─→ Skips: LLM call (saves latency)
  └─→ Routes: directly to research
  │
  ▼
Research Agent (uses PDF tool)
  │
  ▼
Synthesis Agent (generates final answer)

---

If user responds vaguely AGAIN:

User: "Tell me more about that" (still vague)
  │
  ▼
Orchestrator (Layer 3: LLM decides)
  ├─→ Decision: CLARIFICATION
  └─→ clarification_count: 1 → 2
  │
  ▼
Clarification Agent (second attempt)
  └─→ Generates: "About which specific aspect?"
  │
  ▼
User: "The methodology" (third response)
  │
  ▼
Orchestrator (Layer 1: Counter Limit)
  ├─→ Checks: clarification_count == 2 (max reached!)
  ├─→ Forces: next_agent = "research"
  └─→ Resets: clarification_count = 0
  │
  ▼
Research Agent (proceeds with best-effort search)
```

**Guarantees**:
- Maximum 2 clarification turns
- No infinite loops possible
- User always gets answer (even if suboptimal)

---

## Example Clarifications

### Example 1: Pronoun Ambiguity

**Conversation**:
```
User: "What's the state-of-the-art for text-to-SQL?"
AI: "Several approaches exist, including DAIL-SQL, DIN-SQL, and RESDSQL..."

User: "Tell me more about it"
```

**Clarification**:
```
What specific aspect would you like to know more about? Please clarify which
approach (DAIL-SQL, DIN-SQL, or RESDSQL) and which details (architecture,
performance, training data, etc.) you're interested in.
```

---

### Example 2: Missing Metric

**Conversation**:
```
User: "What's the best approach for text-to-SQL?"
```

**Clarification**:
```
To help you find the best approach, I need more context:
- What metric are you optimizing for? (accuracy, speed, interpretability)
- What's your dataset size and complexity?
- Do you have constraints on model size or computational resources?
```

---

### Example 3: Underspecified Task

**Conversation**:
```
User: "How many examples do I need?"
```

**Clarification**:
```
To determine the appropriate number of examples, please clarify:
- What task are you working on? (classification, text-to-SQL, etc.)
- What accuracy or performance target do you have?
- Are you doing few-shot prompting or fine-tuning?
```

---

### Example 4: Ambiguous Reference

**Conversation**:
```
User: "Compare them"
```

**Clarification**:
```
Which specific methods or systems would you like me to compare? Please provide
the names or describe the approaches you're interested in comparing.
```

---

## State Updates

```python
def execute(self, state: AgentState) -> AgentState:
    # 1. Extract conversation context
    messages = state.get("messages", [])
    session_id = state.get("session_id", "default")

    # 2. Generate clarification
    clarification = self._generate_clarification(state)

    # 3. Update state
    state["last_agent"] = "clarification"               # Mark execution
    state["messages"].append(AIMessage(content=clarification))  # Add to history
    state["final_answer"] = clarification               # Set as output
    state["clarification_needed"] = False               # Reset flag
    state["next_agent"] = "END"                         # End workflow (wait for user)

    # Note: clarification_count updated by Orchestrator, not here

    return state
```

### State Fields Modified

| Field | Type | Value | Purpose |
|-------|------|-------|---------|
| `last_agent` | str | `"clarification"` | Enable pattern detection |
| `messages` | Sequence[BaseMessage] | `+ AIMessage(clarification)` | Add question to history |
| `final_answer` | str | `clarification` | Return to user |
| `clarification_needed` | bool | `False` | Reset flag |
| `next_agent` | str | `"END"` | Stop workflow (wait for user) |

**Important**: `clarification_count` is managed by the **Orchestrator**, not the Clarification Agent.

---

## Clarification Generation Process

### 1. Format Conversation History

```python
def _format_conversation_history(self, messages: Sequence[BaseMessage]) -> str:
    formatted = []
    for msg in messages[-self.max_history:]:  # Last 10 messages
        if isinstance(msg, HumanMessage):
            formatted.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage):
            formatted.append(f"AI: {msg.content}")
    return "\n".join(formatted)
```

---

### 2. Prepare Prompt Variables

```python
prompt_variables = {
    "conversation_history": formatted_history,
    "latest_query": latest_query,
}
```

---

### 3. Fetch Prompt from Langfuse

**Prompt Name**: `agent_clarification`

**Prompt Structure** (stored in Langfuse):
```
You are the Clarification agent in a multi-agent RAG system. Your goal is to
generate clear, specific clarifying questions when user queries are vague or ambiguous.

Conversation History:
{{conversation_history}}

Latest Query:
{{latest_query}}

Analyze the latest query for:
- Missing context or undefined references
- Ambiguous pronouns ("it", "that", "them")
- Underspecified parameters or constraints
- Multiple possible interpretations

Generate a concise, helpful clarifying question that will enable the research
agent to provide an accurate answer. Be specific about what information you need.

Clarifying Question:
```

---

### 4. Generate Clarification

```python
clarification = self.llm_client.generate(
    prompt_variables=prompt_variables,
    prompt=self.prompt_obj,
    temperature=self.temperature,
)
```

---

### 5. Trace to Langfuse

```python
self.langfuse_client.trace_generation(
    name=f"{self.name}_clarification",
    session_id=session_id,
    input_data=prompt_variables,
    output=clarification,
    model=self.llm_client.completion_model,
    prompt_name=self.prompt,
    metadata={"agent": self.name}
)
```

---

## Configuration

### Settings File

**Location**: `configs/agents/langgraph.yaml`

```yaml
clarification:
  name: "clarification"
  model: "gpt-4-turbo"
  temperature: 0.5  # Moderate for natural questions
  max_history: 10   # Context window
  prompt: "agent_clarification"  # Langfuse prompt
```

### Initialization

**Location**: `src/apis/dependencies/agents.py:95`

```python
# Create LLM client
clarification_llm = LLMClientSelector.create(
    provider=settings.rag.llm.provider,
    proxy_url=settings.llm.proxy_url,
    completion_model=settings.clarification.model,
    temperature=settings.clarification.temperature,
)

# Create clarification agent
clarification = ClarificationAgent(
    llm_client=clarification_llm,
    langfuse_client=langfuse_client,
    prompt=settings.clarification.prompt,
    name=settings.clarification.name,
    max_history=settings.clarification.max_history,
)
```

---

## Integration with LangGraph

### Workflow Definition

**Location**: `src/graph/workflow.py:52`

```python
# Add clarification node
workflow.add_node("clarification", self.clarification.execute)

# Clarification always ends workflow (waits for user)
workflow.add_edge("clarification", END)
```

### Visual Flow

```
orchestrator
  │
  ├─→ clarification → END (wait for user)
  │       │
  │       └─→ User responds → orchestrator → research
  │
  └─→ research → synthesis → END
```

**Key Behavior**: Clarification agent **always** returns to user (sets `next_agent = "END"`). Workflow resumes when user sends next message.

---

## Observability & Tracing

### Langfuse Tracking

```python
self.langfuse_client.trace_generation(
    name=f"{self.name}_clarification",
    session_id=state["session_id"],
    input_data={
        "conversation_history": formatted_history,
        "latest_query": latest_query,
    },
    output=clarification,
    model=self.llm_client.completion_model,
    prompt_name=self.prompt,
    metadata={
        "agent": self.name,
        "clarification_count": state.get("clarification_count", 0),
    }
)
```

### Logged Information

- **Input**: Conversation history, latest query
- **Output**: Generated clarifying question
- **Metadata**: Agent name, clarification count
- **Session**: Grouped by `session_id`

---

## Error Handling

### Fallback Strategy

```python
try:
    clarification = self.llm_client.generate(prompt_variables)
except Exception as e:
    logger.error(f"Clarification generation failed: {e}")
    # Fallback to generic clarification
    clarification = (
        "Could you please provide more details about your question? "
        "Specifically, what aspect are you interested in?"
    )
```

### Why Fallback to Generic Question?

- **User not stuck**: Gets some response vs. error
- **Conversation continues**: User can provide more context
- **Orchestrator retries**: Next turn may succeed

---

## Performance Considerations

### Latency

| Component | Time |
|-----------|------|
| Format history | ~5ms |
| Fetch Langfuse prompt | ~50ms (cached) |
| LLM generation | ~800ms |
| Trace to Langfuse | ~100ms |
| **Total** | **~955ms** |

### Token Usage

| Component | Tokens |
|-----------|--------|
| Conversation history (10 msgs) | ~2,000 |
| Prompt template | ~300 |
| Completion (clarification) | ~100 |
| **Total** | **~2,400 tokens/call** |

---

## Testing

### Unit Tests

```python
def test_clarification_pronoun_ambiguity():
    state = {
        "messages": [
            HumanMessage(content="Tell me more about it"),
        ],
        "session_id": "test-session",
    }

    result = clarification.execute(state)

    assert result["last_agent"] == "clarification"
    assert result["next_agent"] == "END"
    assert len(result["messages"]) == 2  # Original + clarification
    assert isinstance(result["messages"][-1], AIMessage)
    assert "what" in result["messages"][-1].content.lower()  # Contains question

def test_clarification_missing_context():
    state = {
        "messages": [
            HumanMessage(content="Use the approach from the paper"),
        ],
        "session_id": "test-session",
    }

    result = clarification.execute(state)

    clarification_text = result["messages"][-1].content.lower()
    assert "which" in clarification_text or "what" in clarification_text
```

### Integration Tests

```python
def test_clarification_loop_prevention():
    workflow = AgentWorkflow(...)

    # First turn: vague query
    state = workflow.invoke({
        "messages": [HumanMessage(content="Tell me about it")],
        "session_id": "loop-test",
    })
    assert state["next_agent"] == "END"
    assert state["clarification_count"] == 1

    # Second turn: still vague
    state = workflow.invoke({
        "messages": state["messages"] + [HumanMessage(content="That thing")],
        "session_id": "loop-test",
    })
    assert state["clarification_count"] == 2

    # Third turn: max reached, force research
    state = workflow.invoke({
        "messages": state["messages"] + [HumanMessage(content="You know")],
        "session_id": "loop-test",
    })
    assert state["next_agent"] != "clarification"  # Forced to research
    assert state["clarification_count"] == 0  # Reset
```

---

## Key Takeaways

1. **Three Vagueness Types**: Missing context, ambiguous references, underspecified parameters
2. **Loop Prevention**: Three-layer defense (state tracking, counter, pattern detection)
3. **Always Ends Workflow**: Returns to user, waits for response
4. **Pattern Detection**: Orchestrator skips clarification when user responds
5. **Max 2 Clarifications**: Guaranteed termination, forced research after limit
6. **State Marking**: Sets `last_agent = "clarification"` for detection
7. **Generic Fallback**: Returns generic question on LLM failure
8. **Observability**: Full tracing to Langfuse

The Clarification Agent generates clarifying questions for ambiguous queries and coordinates with the Orchestrator to prevent infinite loops using a multi-layer strategy.
