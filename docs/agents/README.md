# Agent System Documentation

Multi-agent orchestration system for RAG (Retrieval-Augmented Generation) with intelligent routing, clarification loops, and autonomous research.

## Quick Start

**New to the agent system?** Start here:
1. [Design Philosophy](./design-philosophy.md) - Understand core principles
2. [Agent Lifecycle](./agent-lifecycle.md) - Learn how agents execute
3. [Agent Types](#agent-types) - Overview of available agents
4. [Development Guide](./development.md) - Add your own agents

---

## Architecture Overview

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
│Clarifica-│  │ Research │  PDF search + Web search
│  tion    │  │          │  (ReAct pattern)
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

---

## Agent Types

### 1. Routing Agents

**Purpose**: Decide which agent to execute next

| Agent | Location | Responsibility |
|-------|----------|----------------|
| **Master Orchestrator** | `src/agents/orchestrator.py` | Analyze user query intent and route to clarification or research |

**Characteristics:**
- Fast models (GPT-4o-mini, GPT-3.5-turbo)
- Focus on classification/decision-making
- No tool usage
- Execution time: ~300ms

**Documentation:**
- [Design](./orchestrator/design.md)
- [API Reference](./orchestrator/api-reference.md)
- [Examples](./orchestrator/examples.md)

---

### 2. Interaction Agents

**Purpose**: Communicate with users to gather context

| Agent | Location | Responsibility |
|-------|----------|----------------|
| **Clarification Agent** | `src/agents/clarification.py` | Ask clarifying questions when query is vague or ambiguous |

**Characteristics:**
- Generate questions or explanations
- Handle ambiguity and vagueness
- Terminate workflow (wait for user response)
- Track interaction count for loop prevention

**Documentation:**
- [Design](./clarification/design.md)
- [API Reference](./clarification/api-reference.md)
- [Examples](./clarification/examples.md)

---

### 3. Execution Agents

**Purpose**: Perform actions using tools

| Agent | Location | Responsibility |
|-------|----------|----------------|
| **Research Supervisor** | `src/agents/research.py` | Autonomous information retrieval from PDFs and web using ReAct pattern |

**Characteristics:**
- Multi-step reasoning (ReAct pattern)
- Tool selection and execution (PDF retrieval, web search)
- Observation and reflection
- Execution time: 1-5s depending on tool calls

**Documentation:**
- [Design](./research/design.md)
- [API Reference](./research/api-reference.md)
- [Examples](./research/examples.md)

---

### 4. Processing Agents

**Purpose**: Transform data into final output

| Agent | Location | Responsibility |
|-------|----------|----------------|
| **Answer Synthesis** | `src/agents/synthesis.py` | Combine research results and format final answer with citations |

**Characteristics:**
- Combine multiple inputs
- Format for user consumption
- Add metadata (citations, confidence)
- Generate final response

**Documentation:**
- [Design](./synthesis/design.md)
- [API Reference](./synthesis/api-reference.md)
- [Examples](./synthesis/examples.md)

---

## Core Concepts

### 1. Single Responsibility

Each agent does **one thing well**:

- **Orchestrator**: Route (not research)
- **Clarification**: Ask (not answer)
- **Research**: Gather (not synthesize)
- **Synthesis**: Format (not gather)

[Learn more →](./design-philosophy.md#1-single-responsibility-principle)

### 2. Composability

Agents are **building blocks** that can be rearranged:

```python
# Standard workflow
Orchestrator → Research → Synthesis

# With reranker
Orchestrator → Research → Reranker → Synthesis

# With verification
Orchestrator → Research → Synthesis → Verifier
```

[Learn more →](./design-philosophy.md#2-composability)

### 3. LLM-Powered Decisions

Use **semantic understanding** instead of hard-coded rules:

```python
# ❌ Hard-coded rules
if "latest" in query:
    return "web_search"

# ✅ Semantic understanding
decision = llm.analyze(query, context)
```

[Learn more →](./design-philosophy.md#3-llm-powered-decision-making)

### 4. Explicit State Management

Agents communicate via **typed state objects**:

```python
def execute(self, state: AgentState) -> AgentState:
    # Read state → Process → Update state → Return
    query = state["messages"][-1].content
    state["next_agent"] = "synthesis"
    return state
```

[Learn more →](./design-philosophy.md#4-explicit-state-management)

---

## Example Workflows

### Scenario 1: Clear Query

```
User: "What's the accuracy in Zhang et al. Table 2?"
  ↓
Orchestrator: Query is clear → Route to research
  ↓
Research: Search PDFs → Find Table 2
  ↓
Synthesis: Format answer with citation
  ↓
Answer: "87.2% accuracy (Zhang et al. 2024, Table 2)"
```

### Scenario 2: Vague Query with Clarification

```
User: "Tell me about accuracy"
  ↓
Orchestrator: Query is vague → Route to clarification
  ↓
Clarification: "Which paper's accuracy are you asking about?"
  ↓
User: "Zhang et al. 2024"
  ↓
Orchestrator: Pattern detection → Route to research
  ↓
Research: Search PDFs for Zhang et al. accuracy
  ↓
Synthesis: Format answer
  ↓
Answer: "Zhang et al. 2024 reports 87.2% accuracy..."
```

### Scenario 3: Multi-Step Research

```
User: "Find state-of-the-art in papers, then search authors online"
  ↓
Orchestrator: Query is clear → Route to research
  ↓
Research (Step 1): pdf_retrieval → "DAIL-SQL achieves SOTA"
Research (Step 2): web_search → "Authors: Dawei Gao, Haibin Wang"
  ↓
Synthesis: Combine findings
  ↓
Answer: "DAIL-SQL by Dawei Gao and Haibin Wang achieves SOTA..."
```

---

## Developer Resources

### Adding New Agents

Follow the step-by-step guide to add custom agents:
1. Create agent class inheriting from `BaseAgent`
2. Implement `execute()` method
3. Add to LangGraph workflow
4. Write tests

[Full guide →](./development.md#adding-new-agents)

### Testing

- **Unit Tests**: Test individual agents in isolation
- **Integration Tests**: Test complete workflows
- **Mocking**: Mock LLMs, tools, and external services

[Testing guide →](./development.md#testing-agents)

### Best Practices

- Keep agents stateless
- Use type hints everywhere
- Log decisions and context
- Handle errors gracefully
- Make agents observable

[Best practices →](./development.md#best-practices)

### Performance Optimization

- Limit message history
- Use fast models for routing
- Cache prompts
- Batch operations
- Use async where possible

[Optimization guide →](./development.md#performance-optimization)

---

## Configuration

Agent configuration is stored in `configs/agents/langgraph.yaml`:

```yaml
orchestrator:
  model: "gpt-4-turbo"
  temperature: 0.3
  max_history: 10
  max_clarifications: 2

research:
  model: "gpt-4-turbo"
  temperature: 0.7
  max_history: 10

synthesis:
  model: "gpt-4-turbo"
  temperature: 0.5
```

---

## Observability

### Langfuse Integration

All agents trace execution to Langfuse:
- **Input/Output**: Query and response
- **Model**: Which LLM was used
- **Prompt**: Which prompt version
- **Metadata**: Agent name, routing, iteration
- **Session**: Grouped by conversation

### Logging

Structured logging with context:
```python
logger.info(
    f"{self.name}: Routing to {next_agent}",
    extra={
        "agent": self.name,
        "session_id": state["session_id"],
        "next_agent": next_agent
    }
)
```

---

## Related Documentation

### Core Concepts
- [Design Philosophy](./design-philosophy.md) - Architecture principles
- [Agent Lifecycle](./agent-lifecycle.md) - Execution flow and state management

### Development
- [Development Guide](./development.md) - Adding agents, testing, best practices
- [Prompt Management](../prompts/README.md) - Versioned prompts with Langfuse

### Architecture
- [System Overview](../architecture/system-overview.md) - Full system architecture
- [Multi-Agent Orchestration](../architecture/multi-agent-orchestration.md) - Workflow details

### Individual Agents
- [Orchestrator](./orchestrator/) - Intent classification and routing
- [Clarification](./clarification/) - Handling vague queries
- [Research](./research/) - Information retrieval with tools
- [Synthesis](./synthesis/) - Final answer formatting

---

## Quick Reference

| Topic | Document |
|-------|----------|
| **Getting Started** | [Design Philosophy](./design-philosophy.md) |
| **How Agents Work** | [Agent Lifecycle](./agent-lifecycle.md) |
| **Adding Agents** | [Development Guide](./development.md#adding-new-agents) |
| **Testing** | [Development Guide](./development.md#testing-agents) |
| **Best Practices** | [Development Guide](./development.md#best-practices) |
| **Routing Logic** | [Orchestrator Design](./orchestrator/design.md) |
| **Tool Usage** | [Research Design](./research/design.md) |
| **Prompt Versioning** | [Prompt Management](../prompts/README.md) |

---

## Contributing

When adding new agents:
1. Follow the [Development Guide](./development.md)
2. Write tests (unit + integration)
3. Document in agent-specific folder (design.md, api-reference.md, examples.md)
4. Update this README with new agent entry

---

## Directory Structure

```
docs/agents/
├── README.md                    # This file - overview and navigation
├── design-philosophy.md         # Core design principles
├── agent-lifecycle.md           # State management and execution flow
├── development.md               # Adding agents, testing, best practices
│
├── orchestrator/                # Master Orchestrator documentation
│   ├── design.md               # Routing logic and decision layers
│   ├── api-reference.md        # API and configuration
│   └── examples.md             # Usage examples
│
├── clarification/               # Clarification Agent documentation
│   ├── design.md
│   ├── api-reference.md
│   └── examples.md
│
├── research/                    # Research Supervisor documentation
│   ├── design.md               # ReAct pattern and tool integration
│   ├── api-reference.md
│   └── examples.md
│
└── synthesis/                   # Synthesis Agent documentation
    ├── design.md
    ├── api-reference.md
    └── examples.md
```

---

**Questions?** Refer to the detailed documentation linked above or check individual agent folders for specific implementation details
