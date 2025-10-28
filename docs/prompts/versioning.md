# Prompt Versioning

Version control strategy and workflow for prompt management.

## Versioning Strategy

### File Naming Convention

```
v1.prompt  # Initial version
v2.prompt  # Added few-shot examples
v3.prompt  # Improved reasoning steps
```

Each version is a **separate file** (no overwrites). History is preserved in Git.

---

## Version Evolution Example

```bash
# Initial prompt
prompts/agent/orchestrator/v1.prompt

# Improved with examples
prompts/agent/orchestrator/v2.prompt  # New file, v1 preserved

# Added chain-of-thought
prompts/agent/orchestrator/v3.prompt  # New file, v1+v2 preserved
```

---

## Active Version Configuration

Active version is set in `configs/prompts/uploader.yaml`:

```yaml
prompts:
  version: v1        # Current active version
  label: dev         # Environment (dev, staging, production)
```

---

## Prompt Naming Convention

Prompts are uploaded to Langfuse with structured names:

```
{category}_{name}

Examples:
- agent/orchestrator/v1.prompt → agent_orchestrator
- rag/document_retrieval/v1.prompt → rag_document_retrieval
- evaluation/quality/v1.prompt → evaluation_quality
```

---

## Versioning Workflow

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

---

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

---

## Version Tracking Benefits

1. **Git History**: Every prompt change is tracked in version control
2. **No Overwrites**: Previous versions remain accessible
3. **Easy Rollback**: Revert to any previous version instantly
4. **A/B Testing**: Run multiple versions simultaneously
5. **Audit Trail**: Complete history of prompt evolution
6. **Safe Experimentation**: Test new versions without losing old ones

---

## Environment Labels

Prompts can be tagged with environment labels for different deployment stages:

| Label | Purpose | Use Case |
|-------|---------|----------|
| `dev` | Development testing | Experimental prompts, rapid iteration |
| `staging` | Pre-production validation | Final testing before production |
| `production` | Live deployment | Stable, validated prompts |

**Example:**
```yaml
# configs/prompts/uploader.yaml
prompts:
  version: v3
  label: production  # Use v3 in production
```

---

## Best Practices

### Version Incrementing
- **v1 → v2**: Minor improvements (typo fixes, clarity)
- **v2 → v3**: Significant changes (new examples, different structure)
- **v3 → v4**: Major rewrites (complete prompt redesign)

### Git Commit Messages
```bash
# Good commit messages
git commit -m "feat(prompts): add few-shot examples to orchestrator v2"
git commit -m "fix(prompts): clarify output format in research v3"
git commit -m "refactor(prompts): simplify clarification logic in v2"
```

### Documentation
- Document changes in Git commit messages
- Track reasoning for version changes
- Link Langfuse metrics to version decisions

---

## Next Steps

- [Workflow Guide](./workflow.md) - Step-by-step prompt development
- [Langfuse Integration](./langfuse-integration.md) - Upload and manage prompts
- [Configuration](./configuration.md) - Environment setup
