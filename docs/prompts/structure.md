# Prompt Structure

Directory organization and file format for prompt management.

## Directory Structure

```
prompts/
├── agent/                        # Agent system prompts
│   ├── orchestrator/
│   │   └── v1.prompt            # Intent classification
│   ├── clarification/
│   │   └── v1.prompt            # Vagueness detection
│   ├── research/
│   │   └── v1.prompt            # ReAct planning
│   └── synthesis/
│       └── v1.prompt            # Answer formatting
├── rag/                          # RAG prompts
│   └── document_retrieval/
│       └── v1.prompt            # Retrieval query generation
├── evaluation/                   # Evaluation prompts
│   └── quality/
│       └── v1.prompt            # LLM-as-judge scoring
├── config.py                     # Config loader (Dynaconf)
└── uploader.py                   # Langfuse upload utility
```

---

## Prompt File Format

Each `.prompt` file uses **YAML frontmatter** + **template content**:

```yaml
---
# Metadata (YAML frontmatter)
model: gpt-4-turbo
temperature: 0.3
max_tokens: 1000
---

# Prompt Template (Jinja2-style variables)
You are an intent classifier for a PDF Q&A system...

# Current Query
{{ query }}

# Chat History
{{ history }}

# Task
Determine if the query is CLEAR or needs CLARIFICATION...
```

---

## Frontmatter Fields

Required metadata in the YAML header:

| Field | Description | Example |
|-------|-------------|---------|
| `model` | LLM model to use | `gpt-4-turbo`, `claude-3-5-sonnet` |
| `temperature` | Randomness (0.0-1.0) | `0.3` (deterministic) |
| `max_tokens` | Maximum response length | `1000` |

---

## Template Variables

Common variables used across prompts:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{ query }}` | Current user query | "What is the highest accuracy?" |
| `{{ history }}` | Conversation history | "User: ...\nAssistant: ..." |
| `{{ context }}` | Retrieved documents | "[Doc 1] ...\n[Doc 2] ..." |
| `{{ sources }}` | Source attributions | "Zhang et al. 2024, p. 5" |
| `{{ observations }}` | ReAct tool outputs | "PDF Tool: Found 3 docs..." |

---

## Prompt Categories

### Agent Prompts (`agent/`)

**Orchestrator** (`agent/orchestrator/v1.prompt`)
- **Purpose**: Route queries to appropriate agents
- **Key Logic**: Detect clarification follow-ups, check query clarity
- **Output**: Single word decision (`RESEARCH` or `CLARIFICATION`)
- **Code**: src/agents/orchestrator.py:42

**Clarification** (`agent/clarification/v1.prompt`)
- **Purpose**: Generate clarifying questions for vague queries
- **Key Logic**: Identify missing context, ambiguous references
- **Output**: Clarifying question
- **Code**: src/agents/clarification.py:37

**Research** (`agent/research/v1.prompt`)
- **Purpose**: Plan and execute multi-step research
- **Key Logic**: ReAct pattern (Think → Act → Observe → Reflect)
- **Output**: Research plan and final observations
- **Code**: src/agents/research.py:81

**Synthesis** (`agent/synthesis/v1.prompt`)
- **Purpose**: Format final answer with citations
- **Key Logic**: Combine observations, add source attribution
- **Output**: Formatted answer with citations
- **Code**: src/agents/synthesis.py:37

---

### RAG Prompts (`rag/`)

**Document Retrieval** (`rag/document_retrieval/v1.prompt`)
- **Purpose**: Generate effective retrieval queries
- **Key Logic**: Query reformulation, context injection
- **Output**: Optimized search query
- **Code**: src/rag/retriever/document_retriever.py:12

---

### Evaluation Prompts (`evaluation/`)

**Quality** (`evaluation/quality/v1.prompt`)
- **Purpose**: Score response quality (LLM-as-a-Judge)
- **Key Logic**: Relevance, accuracy, completeness, citations
- **Output**: JSON with scores (1-5) and reasoning
- **Code**: evaluation/llm_judge.py

---

## File Naming Convention

Prompt files follow a consistent naming pattern:

```
{version}.prompt

Examples:
- v1.prompt  # Initial version
- v2.prompt  # Second iteration
- v3.prompt  # Third iteration
```

Each version is a **separate file** (no overwrites). History is preserved in Git.

---

## Next Steps

- [Versioning Strategy](./versioning.md) - Learn how to version prompts
- [Langfuse Integration](./langfuse-integration.md) - Upload prompts to Langfuse
- [Workflow](./workflow.md) - Create and deploy prompts
