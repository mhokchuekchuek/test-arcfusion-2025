# Prompt Management System

Production-ready prompt engineering with versioning, centralized management, and observability.

## Overview

This module implements **centralized prompt management** for all agents and evaluation pipelines. Prompts are:

- **Separated from code**: Iterate without deployments
- **Version-controlled**: Track evolution via Git + Langfuse
- **Centrally managed**: Uploaded to Langfuse for observability
- **Template-based**: Support variable substitution
- **Environment-aware**: Dev, staging, production labels

## Why Separate Prompts from Code?

### Benefits

1. **Iteration Speed**: Update prompts in minutes vs hours
   - No code changes required
   - No redeployment needed
   - Test new versions immediately

2. **Version Control**: Track prompt evolution
   - Git history for all changes
   - Langfuse tracks which version was used
   - Easy rollback to previous versions

3. **A/B Testing**: Compare performance
   - Run multiple versions simultaneously
   - Track success rates per version
   - Data-driven prompt improvements

4. **Team Collaboration**: Non-engineers can contribute
   - Product managers can refine messaging
   - Domain experts can improve accuracy
   - UX designers can tune tone

5. **Observability**: Link prompts to outcomes
   - See which prompts perform best
   - Track token usage per version
   - Monitor quality metrics

6. **Reproducibility**: Exact version tracking
   - Every request traces to specific prompt
   - Audit trail for compliance
   - Debugging is deterministic

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

### Frontmatter Fields

- `model`: LLM model to use (e.g., `gpt-4-turbo`, `claude-3-5-sonnet`)
- `temperature`: Randomness (0.0 = deterministic, 1.0 = creative)
- `max_tokens`: Maximum response length

### Template Variables

Common variables used across prompts:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{ query }}` | Current user query | "What is the highest accuracy?" |
| `{{ history }}` | Conversation history | "User: ...\nAssistant: ..." |
| `{{ context }}` | Retrieved documents | "[Doc 1] ...\n[Doc 2] ..." |
| `{{ sources }}` | Source attributions | "Zhang et al. 2024, p. 5" |
| `{{ observations }}` | ReAct tool outputs | "PDF Tool: Found 3 docs..." |

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

### RAG Prompts (`rag/`)

**Document Retrieval** (`rag/document_retrieval/v1.prompt`)
- **Purpose**: Generate effective retrieval queries
- **Key Logic**: Query reformulation, context injection
- **Output**: Optimized search query
- **Code**: src/rag/retriever/document_retriever.py:12

### Evaluation Prompts (`evaluation/`)

**Quality** (`evaluation/quality/v1.prompt`)
- **Purpose**: Score response quality (LLM-as-a-Judge)
- **Key Logic**: Relevance, accuracy, completeness, citations
- **Output**: JSON with scores (1-5) and reasoning
- **Code**: evaluation/llm_judge.py

## Versioning Strategy

### File Naming Convention

```
v1.prompt  # Initial version
v2.prompt  # Added few-shot examples
v3.prompt  # Improved reasoning steps
```

Each version is a **separate file** (no overwrites). History is preserved in Git.

### Version Evolution Example

```bash
# Initial prompt
prompts/agent/orchestrator/v1.prompt

# Improved with examples
prompts/agent/orchestrator/v2.prompt  # New file, v1 preserved

# Added chain-of-thought
prompts/agent/orchestrator/v3.prompt  # New file, v1+v2 preserved
```

### Active Version Configuration

Active version is set in `configs/prompts/uploader.yaml`:

```yaml
prompts:
  version: v1        # Current active version
  label: dev         # Environment (dev, staging, production)
```

## Langfuse Integration

### Why Langfuse?

- **Centralized Management**: All prompts in one place
- **Version Tracking**: Link traces to specific prompt versions
- **A/B Testing**: Compare performance across versions
- **Observability**: Monitor success rates, latency, token usage
- **Team Collaboration**: Non-engineers can view/propose changes

### Prompt Naming Convention

Prompts are uploaded with structured names:

```
{category}_{name}

Examples:
- agent/orchestrator/v1.prompt → agent_orchestrator
- rag/document_retrieval/v1.prompt → rag_document_retrieval
- evaluation/quality/v1.prompt → evaluation_quality
```

### Uploading Prompts

**Prerequisites:**
- Python 3.13+ with venv/conda activated
- `pip install -r requirements.txt` completed
- Langfuse credentials set in `.env` file

**Directory**: The script reads `.prompt` files from the `prompts/` directory (configured in `configs/prompts/uploader.yaml`)

```bash
# Upload all prompts to Langfuse (with venv/conda activated)
python scripts/upload_prompts_to_langfuse.py
```

**What happens:**
1. Scans `prompts/` directory for `.prompt` files (recursive)
2. Parses YAML frontmatter + template content
3. Uploads to Langfuse with naming: `{category}_{name}`
   - Example: `prompts/agent/orchestrator/v1.prompt` → `agent_orchestrator`
4. Tags with version (`v1`) and label (`dev`)
5. Links metadata (uploaded_at, source_file, category)

**Note**: For local execution, ensure Langfuse credentials are set in `.env`:
```bash
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Using Prompts in Code

Agents load prompts from Langfuse at runtime:

```python
from tools.observability.selector import ObservabilitySelector

# Initialize Langfuse client
langfuse = ObservabilitySelector.create(
    provider="langfuse",
    public_key="pk-...",
    secret_key="sk-...",
    host="https://cloud.langfuse.com"
)

# Fetch prompt (latest version for environment)
prompt = langfuse.client.get_prompt(
    name="agent_orchestrator",
    label="production"  # or "dev", "staging"
)

# Compile with variables
compiled = prompt.compile(
    query=user_query,
    history=chat_history
)

# Use in LLM call
response = llm.generate(compiled)
```

**Code reference**: src/agents/orchestrator.py:42

## Configuration

All settings are in `configs/prompts/uploader.yaml`:

```yaml
# Prompt Uploader Configuration
prompts:
  directory: prompts             # Directory containing .prompt files
  file_pattern: "*.prompt"       # File pattern to match
  version: v1                    # Prompt version tag
  label: dev                     # Environment label
  batch_upload: true             # Upload all prompts in batch
  overwrite_existing: true       # Overwrite existing prompts

# Langfuse Configuration
observability:
  langfuse:
    enabled: true
    provider: langfuse
    public_key: null             # Set via LANGFUSE_PUBLIC_KEY env var
    secret_key: null             # Set via LANGFUSE_SECRET_KEY env var
    host: https://cloud.langfuse.com
```

**Override via environment variables:**

```bash
export PROMPTS__VERSION=v2
export PROMPTS__LABEL=production
export LANGFUSE_PUBLIC_KEY=pk-...
export LANGFUSE_SECRET_KEY=sk-...
```

## Prompt Engineering Best Practices

### Structure

1. **Clear Role Definition**
   ```
   You are an intent classifier for a PDF Q&A system...
   ```

2. **Task Description**
   ```
   Your job is to analyze queries and determine if they are clear enough...
   ```

3. **Input Format** (clearly labeled sections)
   ```
   # Current Query
   {{ query }}

   # Chat History
   {{ history }}
   ```

4. **Output Format** (specify expected format)
   ```
   Respond with exactly one word: RESEARCH or CLARIFICATION
   ```

5. **Examples** (few-shot learning)
   ```
   Examples:
   - "What accuracy did davinci-codex achieve?" → RESEARCH
   - "Tell me more about it" → CLARIFICATION
   ```

### Variables

Use `{{ variable }}` for Jinja2-style templating:

```yaml
Common patterns:
- {{ query }} - Current user query
- {{ history }} - Conversation context
- {{ context }} - Retrieved documents
- {{ sources }} - Source references
```

### Metadata (Frontmatter)

```yaml
---
model: gpt-4-turbo        # Which LLM to use
temperature: 0.3          # 0.0 = deterministic, 1.0 = creative
max_tokens: 1000          # Response length limit
---
```

## Prompt Versioning Workflow

### Creating a New Version

```bash
# 1. Copy current version
cp prompts/agent/orchestrator/v1.prompt prompts/agent/orchestrator/v2.prompt

# 2. Edit v2.prompt with improvements
vim prompts/agent/orchestrator/v2.prompt

# 3. Update config to use v2
# Edit configs/prompts/uploader.yaml:
#   prompts:
#     version: v2

# 4. Upload to Langfuse (with venv/conda activated)
python scripts/upload_prompts_to_langfuse.py

# 5. Test and compare performance
# Use Langfuse dashboard to compare v1 vs v2 metrics

# 6. Promote to production (if successful)
# Edit configs/prompts/uploader.yaml:
#   prompts:
#     label: production
python scripts/upload_prompts_to_langfuse.py
```

### Rollback to Previous Version

```bash
# 1. Update config to previous version
# Edit configs/prompts/uploader.yaml:
#   prompts:
#     version: v1

# 2. Re-upload (with venv/conda activated)
python scripts/upload_prompts_to_langfuse.py

# 3. Verify in Langfuse dashboard
# Check that v1 is now active for your environment
```

## API Reference

### PromptUploader Class

**File**: `prompts/uploader.py`

```python
class PromptUploader:
    """Uploads .prompt files to Langfuse for centralized management."""

    def __init__(self):
        """Initialize from config (configs/prompts/uploader.yaml).

        Loads all settings from Dynaconf configuration.
        Override via environment variables if needed.

        Example:
            >>> uploader = PromptUploader()
        """

    def parse_prompt_file(self, filepath: Path) -> Dict:
        """Parse .prompt file with YAML frontmatter.

        Args:
            filepath: Path to .prompt file

        Returns:
            Dict with:
                - config: Parsed YAML frontmatter
                - template: Prompt template content

        Example:
            >>> parsed = uploader.parse_prompt_file(Path("agent/orchestrator/v1.prompt"))
            >>> print(parsed['config']['temperature'])
            0.3
        """

    def upload_prompt(self, filepath: Path) -> bool:
        """Upload single prompt file to Langfuse.

        Generates prompt name from directory structure:
        - prompts/agent/orchestrator/v1.prompt → agent_orchestrator
        - prompts/rag/document_retrieval/v1.prompt → rag_document_retrieval

        Args:
            filepath: Path to .prompt file

        Returns:
            True if successful, False otherwise
        """

    def upload_all(self) -> List[Dict]:
        """Upload all .prompt files in directory (recursive scan).

        Returns:
            List of results with:
                - filename: Name of .prompt file
                - prompt_name: Generated Langfuse prompt name
                - success: Upload success status

        Example:
            >>> results = uploader.upload_all()
            >>> successful = [r for r in results if r['success']]
            >>> print(f"Uploaded {len(successful)}/{len(results)} prompts")
        """
```

## Example Prompts

### Orchestrator Prompt

**File**: `prompts/agent/orchestrator/v1.prompt`

**Purpose**: Classify user intent (RESEARCH vs CLARIFICATION)

**Key Features**:
- Detects clarification follow-ups (prevents infinite loops)
- Handles brief responses like "everything" or "all"
- Context-aware decision making

**Output**: Single word (`RESEARCH` or `CLARIFICATION`)

### Clarification Prompt

**File**: `prompts/agent/clarification/v1.prompt`

**Purpose**: Generate clarifying questions for vague queries

**Key Features**:
- Identifies missing context
- Detects ambiguous references (pronouns without antecedents)
- Avoids asking obvious questions

**Output**: Targeted clarifying question

### Quality Evaluation Prompt

**File**: `prompts/evaluation/quality/v1.prompt`

**Purpose**: Score response quality (LLM-as-a-Judge)

**Criteria**:
- **Relevance** (1-5): Does answer address the question?
- **Accuracy** (1-5): Is information correct?
- **Completeness** (1-5): Is answer thorough?
- **Citations** (1-5): Are sources properly attributed?

**Output**: JSON with scores and reasoning

## Why This Matters for Production

### Production-Ready Benefits

1. **Reproducibility**: Every request traces back to exact prompt version
   - Debugging: "Which prompt was used for request X?"
   - Auditing: "What changed between v1 and v2?"

2. **Rapid Iteration**: Update prompts in minutes, not hours
   - No code changes required
   - No deployment needed
   - Test immediately in production-like environment

3. **Safety**: Test new prompts without touching code
   - A/B test with small traffic percentage
   - Rollback instantly if issues arise
   - No risk of breaking production

4. **Collaboration**: Product/UX teams can improve prompts
   - Non-engineers view prompts in Langfuse
   - Propose improvements via Git PRs
   - Review changes before deployment

5. **Observability**: Track which prompts perform best
   - Success rate per prompt version
   - Latency per prompt
   - Token usage per prompt
   - User feedback per prompt

6. **Governance**: Audit trail of prompt changes
   - Git history shows who changed what
   - Langfuse shows when version was deployed
   - Compliance requirements met

### Key Differentiator from Toy Projects

**Toy Project**: Prompts hardcoded in Python strings
```python
# Bad: Hard to maintain, version, or track
prompt = f"You are a helpful assistant. Answer: {question}"
```

**Production Project**: Versioned, managed, observable
```python
# Good: Centralized, versioned, tracked
prompt = langfuse.get_prompt("agent_orchestrator", label="production")
compiled = prompt.compile(query=question, history=history)
```

## Integration with Other Modules

### Agents Module
- All agents load prompts from Langfuse
- See `src/agents/README.md` for agent architecture
- See `src/agents/orchestrator.py:42` for usage example

### Evaluation Module
- Quality evaluation uses `evaluation/quality/v1.prompt`
- See `evaluation/README.md` for evaluation framework
- See `evaluation/llm_judge.py` for implementation

### Tools Module
- Observability selector creates Langfuse client
- See `tools/observability/langfuse/` for implementation
- See `tools/README.md` for provider pattern

## Troubleshooting

### Issue: Prompts not uploading

**Check:**
1. Langfuse credentials set: `echo $LANGFUSE_PUBLIC_KEY`
2. Langfuse host reachable: `curl https://cloud.langfuse.com`
3. Config is correct: `cat configs/prompts/uploader.yaml`

**Fix:**
```bash
export LANGFUSE_PUBLIC_KEY=pk-...
export LANGFUSE_SECRET_KEY=sk-...
python scripts/upload_prompts_to_langfuse.py
```

### Issue: Agent using wrong prompt version

**Check:**
1. Which version is active: `cat configs/prompts/uploader.yaml`
2. Which version was uploaded: Check Langfuse dashboard
3. Which label agent is fetching: `cat configs/agents/langgraph.yaml`

**Fix:**
```bash
# Update active version
# Edit configs/prompts/uploader.yaml: version: v2

# Re-upload
python scripts/upload_prompts_to_langfuse.py

# Verify in Langfuse dashboard
```

### Issue: Template variables not working

**Check:**
1. Variable names match: `{{ query }}` not `{{ question }}`
2. Variables passed to compile: `prompt.compile(query=...)`
3. Template syntax is correct: Use `{{ }}` not `{ }`

## Future Improvements

**See [../architecture/architecture-decisions.md](../architecture/architecture-decisions.md#retrospective)** for planned future enhancements.

## Summary

This prompt management system demonstrates **production-grade LLM operations**:

- ✅ **Separation of Concerns**: Prompts independent of code
- ✅ **Version Control**: Git + Langfuse tracking
- ✅ **Centralized Management**: Single source of truth
- ✅ **Observability**: Link prompts to outcomes
- ✅ **Team Collaboration**: Non-engineers can iterate
- ✅ **Experimentation**: Safe A/B testing
- ✅ **Governance**: Audit trail and reproducibility

**This is a key differentiator for senior-level candidates!** It shows understanding of prompt engineering at scale, not just throwing prompts into code.
