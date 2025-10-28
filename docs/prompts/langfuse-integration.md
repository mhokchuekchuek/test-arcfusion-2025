# Langfuse Integration

Centralized prompt management with observability and version tracking.

## Why Langfuse?

- **Centralized Management**: All prompts in one place
- **Version Tracking**: Link traces to specific prompt versions
- **A/B Testing**: Compare performance across versions
- **Observability**: Monitor success rates, latency, token usage
- **Team Collaboration**: Non-engineers can view/propose changes

---

## Prompt Naming Convention

Prompts are uploaded with structured names:

```
{category}_{name}

Examples:
- agent/orchestrator/v1.prompt → agent_orchestrator
- rag/document_retrieval/v1.prompt → rag_document_retrieval
- evaluation/quality/v1.prompt → evaluation_quality
```

---

## Uploading Prompts

### Prerequisites

- Python 3.13+ with venv/conda activated
- `pip install -r requirements.txt` completed
- Langfuse credentials set in `.env` file

### Directory Setup

The script reads `.prompt` files from the `prompts/` directory (configured in `configs/prompts/uploader.yaml`)

### Upload Command

```bash
# Upload all prompts to Langfuse (with venv/conda activated)
python scripts/upload_prompts_to_langfuse.py
```

### What Happens

1. Scans `prompts/` directory for `.prompt` files (recursive)
2. Parses YAML frontmatter + template content
3. Uploads to Langfuse with naming: `{category}_{name}`
   - Example: `prompts/agent/orchestrator/v1.prompt` → `agent_orchestrator`
4. Tags with version (`v1`) and label (`dev`)
5. Links metadata (uploaded_at, source_file, category)

---

## Environment Setup

Set Langfuse credentials in `.env`:

```bash
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Override via environment variables:**

```bash
export PROMPTS__VERSION=v2
export PROMPTS__LABEL=production
export LANGFUSE_PUBLIC_KEY=pk-...
export LANGFUSE_SECRET_KEY=sk-...
```

---

## Using Prompts in Code

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

---

## Observability Features

### Version Tracking

Every LLM request is linked to:
- Exact prompt version used
- Timestamp of request
- Environment label (dev/staging/production)

### Performance Metrics

Track per-prompt metrics:
- Success rate
- Average latency
- Token usage (prompt + completion)
- Cost per request

### A/B Testing

Compare multiple prompt versions:
1. Deploy v1 to 80% of traffic
2. Deploy v2 to 20% of traffic
3. Compare success rates in Langfuse dashboard
4. Promote winner to 100% traffic

---

## Langfuse Dashboard

### Viewing Prompts

1. Navigate to Langfuse dashboard
2. Click "Prompts" in sidebar
3. Filter by label (dev/staging/production)
4. View version history and metrics

### Comparing Versions

1. Select prompt (e.g., `agent_orchestrator`)
2. View all versions (v1, v2, v3)
3. Compare metrics side-by-side
4. Identify best-performing version

### Tracing Requests

1. Click on specific trace
2. View which prompt version was used
3. See input variables and output
4. Link to performance metrics

---

## Integration with Agents

All agents use Langfuse prompts:

| Agent | Prompt Name | Label |
|-------|-------------|-------|
| Orchestrator | `agent_orchestrator` | production |
| Clarification | `agent_clarification` | production |
| Research | `agent_research` | production |
| Synthesis | `agent_synthesis` | production |

**Configuration**: `configs/agents/langgraph.yaml`

---

## Best Practices

### Prompt Updates

1. **Test in dev first**: Deploy to `dev` label before production
2. **Monitor metrics**: Check success rates before promoting
3. **Gradual rollout**: Use A/B testing for validation
4. **Document changes**: Track reasoning in Git commits

### Version Management

1. **Keep old versions**: Never delete previous prompt versions
2. **Tag clearly**: Use descriptive labels (dev/staging/production)
3. **Link to metrics**: Reference Langfuse data in decisions
4. **Audit trail**: Maintain complete history of changes

### Security

1. **Protect credentials**: Never commit API keys to Git
2. **Use .env files**: Store credentials securely
3. **Rotate keys**: Update keys periodically
4. **Limit access**: Control who can upload prompts

---

## Troubleshooting

### Prompts not uploading

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

### Agent using wrong prompt version

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

---

## Next Steps

- [Configuration](./configuration.md) - Detailed configuration options
- [Workflow](./workflow.md) - Step-by-step prompt development
- [API Reference](./api-reference.md) - PromptUploader class documentation
