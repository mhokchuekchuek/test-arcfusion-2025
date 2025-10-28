# Synthesis Agent Design

## Agent Responsibility

The **Answer Synthesis Agent** (AnswerSynthesisAgent) generates the final coherent answer from research observations and tool outputs. It combines information from multiple sources, formats responses with appropriate structure, and calculates confidence scores based on the evidence gathered.

**Location**: `src/agents/synthesis.py:1`

**Key Responsibilities**:
- Synthesize coherent answers from research observations
- Combine results from PDF and web search tools
- Format responses with clear structure
- Calculate confidence scores
- Handle cases where insufficient information was found
- Add final answer to conversation history

---

## Response Generation Strategy

The Synthesis Agent follows a structured approach to generate final answers:

### 1. Extract Original Query

```python
# Get the original user query from message history
query = "Unknown query"
for msg in messages:
    if isinstance(msg, HumanMessage):
        query = msg.content
        break
```

**Location**: `src/agents/synthesis.py:51`

**Purpose**: Identifies the original user question to ensure the answer is relevant.

---

### 2. Gather Research Context

```python
# Get research results from state
observations = state["context"].get("observations", [])
final_output = state["context"].get("final_output", "")

# Combine all observations
all_observations = "\n\n".join(observations)
if final_output:
    all_observations += f"\n\nFinal Output:\n{final_output}"
```

**Location**: `src/agents/synthesis.py:58`

**Context Components**:
- `observations`: List of tool usage indicators (e.g., "Used tool: pdf_retrieval")
- `final_output`: Research agent's synthesized summary from ReAct loop

---

### 3. Generate Synthesis Prompt

```python
prompt_variables = {
    "query": query,
    "observations": all_observations if all_observations else "No observations available.",
}
```

**Location**: `src/agents/synthesis.py:70`

---

### 4. Fetch Prompt from Langfuse

```python
if self.langfuse_client and self.prompt_config.get("provider") == "langfuse":
    # Get prompt from Langfuse
    prompt = self.langfuse_client.get_prompt(
        name=prompt_id,  # "synthesis"
        version=prompt_version,
        label=prompt_env  # "production" or "dev"
    )

    # Compile template with variables
    compiled_prompt = prompt.compile(**prompt_variables)

    # Generate answer
    answer = self.llm_client.generate(prompt=compiled_prompt)
```

**Location**: `src/agents/synthesis.py:76`

---

### 5. Generate Final Answer

**Prompt Structure** (stored in Langfuse as `synthesis`):
```
You are the Synthesis agent in a multi-agent RAG system. Your role is to generate
a clear, coherent final answer based on research observations.

User Query:
{{query}}

Research Observations:
{{observations}}

Guidelines:
1. Synthesize information from all observations into a coherent answer
2. Ensure grounding: only use information from observations, don't hallucinate
3. If observations are insufficient: clearly state "I couldn't find information about X"
4. Maintain source attribution when possible
5. Structure the answer clearly (use paragraphs, bullet points if needed)
6. Be concise but comprehensive

Generate a well-structured answer:
```

---

### 6. Calculate Confidence Score

```python
def _calculate_confidence(self, observations: list) -> float:
    """Calculate confidence score based on number of observations."""
    num_observations = len(observations)
    if num_observations == 0:
        return 0.0
    elif num_observations == 1:
        return 0.6
    elif num_observations == 2:
        return 0.8
    else:
        return 0.95
```

**Location**: `src/agents/synthesis.py:143`

**Confidence Mapping**:

| Observations | Confidence | Meaning |
|--------------|------------|---------|
| 0 | 0.0 | No research performed |
| 1 | 0.6 | Single source (moderate confidence) |
| 2 | 0.8 | Two sources (high confidence) |
| 3+ | 0.95 | Multiple sources (very high confidence) |

**Note**: This is a simple heuristic. Future improvements could consider:
- Similarity scores from retrieval
- Source quality/authority
- Cross-source agreement
- Query complexity

---

## Citation Formatting

### PDF Sources

The Research Agent's output includes source attribution:

```
Source: DAIL-SQL_paper.pdf (Page 3)
Content: DAIL-SQL uses example-based learning...
Similarity: 0.89
```

The Synthesis Agent incorporates this into the final answer:

```
Based on the research papers, DAIL-SQL uses example-based learning with carefully
selected demonstrations (DAIL-SQL_paper.pdf, Page 3). The selection algorithm
ranks examples by similarity to the target query (DAIL-SQL_paper.pdf, Page 5).
```

---

### Web Sources

The Research Agent's output includes URLs:

```
Title: OpenAI Announces GPT-4.5 Turbo
URL: https://openai.com/blog/gpt-4-5-turbo
Content: OpenAI today released GPT-4.5 Turbo...
```

The Synthesis Agent incorporates this:

```
According to recent announcements, OpenAI released GPT-4.5 Turbo with improved
reasoning capabilities [Source: https://openai.com/blog/gpt-4-5-turbo].
```

---

### Multiple Sources

When combining multiple sources:

```
The state-of-the-art approach for text-to-SQL is DAIL-SQL (DAIL-SQL_paper.pdf),
which was developed by researchers at [institution name] according to web sources
[https://scholar.google.com/...]. The method achieves 89.2% execution accuracy
on the Spider benchmark (DAIL-SQL_paper.pdf, Page 7).
```

---

## Quality Controls

### 1. Relevance Check

The synthesis prompt instructs the LLM to:
- Only use information from observations
- Stay grounded in the evidence
- Avoid hallucination beyond context

```
Guideline: Ensure grounding - only use information from observations,
don't hallucinate
```

---

### 2. Completeness Check

If research observations are insufficient:

```python
if not observations:
    answer = "I couldn't find relevant information about your query in the available sources."
```

**Example Response**:
```
I couldn't find information about "quantum computing applications in finance" in
the provided academic papers. The available papers focus on natural language
processing and text-to-SQL systems. You may want to try a more specific query or
ask about topics covered in the paper collection.
```

---

### 3. Disclaimer When Uncertain

Low confidence score triggers disclaimer:

```python
confidence = self._calculate_confidence(observations)
if confidence < 0.5:
    answer += "\n\nNote: This answer is based on limited evidence. Please verify with additional sources."
```

---

## State Updates

```python
def execute(self, state: AgentState) -> AgentState:
    # 1. Extract query and observations
    query = self._extract_query(messages)
    observations = state["context"].get("observations", [])
    final_output = state["context"].get("final_output", "")

    # 2. Generate synthesis
    answer = self._generate_answer(query, observations, final_output)

    # 3. Calculate confidence
    confidence = self._calculate_confidence(observations)

    # 4. Update state
    state["messages"].append(AIMessage(content=answer))
    state["final_answer"] = answer
    state["confidence_score"] = confidence
    state["next_agent"] = "END"
    state["last_agent"] = "synthesis"

    return state
```

**Location**: `src/agents/synthesis.py:37`

### State Fields Modified

| Field | Type | Value | Purpose |
|-------|------|-------|---------|
| `messages` | Sequence[BaseMessage] | + AIMessage(answer) | Add answer to conversation |
| `final_answer` | str | Synthesized answer | Return to user |
| `confidence_score` | float | 0.0-0.95 | Quality indicator |
| `next_agent` | str | `"END"` | End workflow |
| `last_agent` | str | `"synthesis"` | Mark execution |

---

## Configuration

### Settings File

**Location**: `configs/agents/langgraph.yaml`

```yaml
synthesis:
  name: "synthesis"
  model: "gpt-4-turbo"
  temperature: 0.7  # Moderate for natural language
  max_history: 10   # Context window

  # Prompt configuration
  prompt:
    provider: "langfuse"
    id: "synthesis"
    environment: "production"
    version: null  # null = latest version
```

### Initialization

**Location**: `src/apis/dependencies/agents.py`

```python
# Create LLM client
synthesis_llm = LLMClientSelector.create(
    provider=settings.rag.llm.provider,  # "litellm"
    proxy_url=settings.llm.proxy_url,
    completion_model=settings.synthesis.model,
    temperature=settings.synthesis.temperature,
)

# Create synthesis agent
synthesis = AnswerSynthesisAgent(
    llm_client=synthesis_llm,
    langfuse_client=langfuse_client,
    agent_config={
        "name": settings.synthesis.name,
        "prompt": settings.synthesis.prompt,
        "max_history": settings.synthesis.max_history,
    }
)
```

---

## Integration with LangGraph

### Workflow Definition

**Location**: `src/graph/workflow.py`

```python
from langgraph.graph import StateGraph, END

# Add synthesis node
workflow.add_node("synthesis", self.synthesis.execute)

# Synthesis always ends workflow
workflow.add_edge("synthesis", END)
```

### Visual Flow

```
research
  │
  ▼
synthesis (AnswerSynthesisAgent)
  ├─ Combines observations
  ├─ Generates final answer
  ├─ Calculates confidence
  └─→ END (return to user)
```

**Note**: Synthesis is always the final step before returning to the user.

---

## Observability & Tracing

### Langfuse Tracking

```python
self.langfuse_client.trace_generation(
    name=self.agent_name,  # "synthesis"
    input_data={
        "query": query,
        "observations": all_observations,
    },
    output=answer,
    model=self.llm_client.completion_model,
    metadata={"agent": "AnswerSynthesisAgent"},
    session_id=session_id
)
```

**Location**: `src/agents/synthesis.py:98`

### Logged Information

- **Input**: Original query, all observations
- **Output**: Final synthesized answer
- **Metadata**: Agent name, confidence score
- **Session**: Grouped by `session_id`

---

## Error Handling

### Synthesis Failure Recovery

```python
except Exception as e:
    logger.error(f"Synthesis agent failed: {e}", exc_info=True)
    # Fallback answer
    fallback = final_output if final_output else "I encountered an error while processing your request."
    state["messages"].append(AIMessage(content=fallback))
    state["final_answer"] = fallback
    state["confidence_score"] = 0.0
    state["next_agent"] = "END"
    return state
```

**Location**: `src/agents/synthesis.py:133`

**Fallback Strategy**:
1. Try to use research agent's final output as fallback
2. If no final output, return generic error message
3. Set confidence to 0.0 to indicate failure
4. Still ends workflow (graceful degradation)

---

### No Observations Handling

```python
if not observations:
    all_observations = "No observations available."
```

**Behavior**: Synthesis agent still generates a response explaining that no information was found.

**Example**:
```
I couldn't find relevant information about your query in the available sources.
This could be because:
- The topic is not covered in the academic paper collection
- The query was too specific or used terminology not in the papers
- The web search didn't return relevant results

Please try rephrasing your question or asking about a different topic.
```

---

## Performance Considerations

### Latency

| Component | Time |
|-----------|------|
| Extract query & observations | ~5ms |
| Fetch Langfuse prompt | ~50ms (cached) |
| Compile prompt template | ~10ms |
| LLM generation | ~1-2s |
| Calculate confidence | ~1ms |
| Trace to Langfuse | ~100ms |
| **Total** | **~1.2-2.2s** |

---

### Token Usage

| Component | Tokens |
|-----------|--------|
| System prompt | ~400 |
| Query | ~50 |
| Observations | ~500-2000 (varies) |
| Final answer | ~200-500 |
| **Average** | **~1,150-2,950 tokens** |

**Variable cost**: Depends on length of research observations.

---

### Optimization Strategies

1. **History Limiting**: Only last 10 messages sent (line 48)
2. **Prompt Caching**: Langfuse caches prompts
3. **Observation Truncation**: Could limit observation length if too large
4. **Temperature Control**: 0.7 balances quality and consistency

---

## Testing

### Unit Tests

```python
def test_synthesis_with_observations():
    state = {
        "messages": [HumanMessage(content="What is DAIL-SQL?")],
        "session_id": "test",
        "context": {
            "observations": ["Used tool: pdf_retrieval"],
            "final_output": "DAIL-SQL is a text-to-SQL approach..."
        },
        "iteration": 2,
    }

    result = synthesis.execute(state)

    assert result["last_agent"] == "synthesis"
    assert result["next_agent"] == "END"
    assert result["final_answer"] != ""
    assert result["confidence_score"] == 0.6  # 1 observation
    assert isinstance(result["messages"][-1], AIMessage)

def test_synthesis_no_observations():
    state = {
        "messages": [HumanMessage(content="What is X?")],
        "session_id": "test",
        "context": {"observations": [], "final_output": ""},
        "iteration": 2,
    }

    result = synthesis.execute(state)

    assert result["confidence_score"] == 0.0
    assert "couldn't find" in result["final_answer"].lower() or "error" in result["final_answer"].lower()

def test_synthesis_multi_observations():
    state = {
        "messages": [HumanMessage(content="Query")],
        "session_id": "test",
        "context": {
            "observations": ["Used tool: pdf_retrieval", "Used tool: web_search"],
            "final_output": "Combined results..."
        },
        "iteration": 2,
    }

    result = synthesis.execute(state)

    assert result["confidence_score"] == 0.8  # 2 observations
```

---

### Integration Tests

```python
def test_full_workflow_with_synthesis():
    workflow = AgentWorkflow(...)

    # Execute full workflow
    result = workflow.invoke({
        "messages": [HumanMessage(content="What is DAIL-SQL?")],
        "session_id": "integration-test",
    })

    # Verify synthesis executed
    assert result["last_agent"] == "synthesis"
    assert result["final_answer"] != ""
    assert result["confidence_score"] > 0
    assert result["next_agent"] == "END"

    # Verify answer quality
    assert "dail" in result["final_answer"].lower() or "sql" in result["final_answer"].lower()
```

---

## Example Synthesis Flows

### Example 1: Single PDF Source

**Input State**:
```python
{
    "context": {
        "observations": ["Used tool: pdf_retrieval"],
        "final_output": "DAIL-SQL is an example-based text-to-SQL approach that achieves state-of-the-art results on the Spider benchmark with 89.2% execution accuracy. (Source: DAIL-SQL_paper.pdf, Page 3)"
    }
}
```

**Output**:
```
DAIL-SQL is an example-based text-to-SQL approach that achieves state-of-the-art
results on benchmarks. According to DAIL-SQL_paper.pdf (Page 3), it uses carefully
selected demonstrations to improve query generation and achieves 89.2% execution
accuracy on the Spider benchmark.

Confidence: 0.6 (single source)
```

---

### Example 2: Multiple Sources

**Input State**:
```python
{
    "context": {
        "observations": ["Used tool: pdf_retrieval", "Used tool: web_search"],
        "final_output": "DAIL-SQL from papers + recent updates from web about authors"
    }
}
```

**Output**:
```
DAIL-SQL is a state-of-the-art text-to-SQL approach developed by researchers at
[institution]. Based on academic papers (DAIL-SQL_paper.pdf), the method uses
example-based learning with carefully selected demonstrations. Recent web sources
indicate that the research team has continued to improve the approach with new
benchmarks and applications.

Confidence: 0.8 (multiple sources)
```

---

### Example 3: No Information Found

**Input State**:
```python
{
    "context": {
        "observations": [],
        "final_output": ""
    }
}
```

**Output**:
```
I couldn't find relevant information about your query in the available sources.
The academic paper collection doesn't appear to contain information on this topic,
and web search didn't return relevant results. Please try:

1. Rephrasing your question
2. Asking about a different aspect of the topic
3. Using different terminology that might be in the papers

Confidence: 0.0 (no sources)
```

---

## Key Takeaways

1. **Final Step**: Always the last agent before returning to user
2. **Context Combination**: Merges all research observations and outputs
3. **Confidence Scoring**: Simple heuristic based on number of observations
4. **Grounding**: Prompt enforces using only provided evidence
5. **Source Attribution**: Maintains citations from research
6. **Error Handling**: Graceful fallback to research output or error message
7. **Quality Controls**: Relevance check, completeness check, uncertainty disclaimer
8. **Observability**: Full tracing to Langfuse with session tracking

The Synthesis Agent is the **final answer generator** that takes fragmented research observations and creates a coherent, well-structured response with appropriate confidence scoring and source attribution.
