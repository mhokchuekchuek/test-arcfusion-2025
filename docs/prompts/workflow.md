# Prompt Development Workflow

Step-by-step guide to creating, testing, and deploying prompts.

## Quick Start

```bash
# 1. Create new prompt
cp prompts/agent/orchestrator/v1.prompt prompts/agent/orchestrator/v2.prompt

# 2. Edit prompt
vim prompts/agent/orchestrator/v2.prompt

# 3. Configure version
# Edit configs/prompts/uploader.yaml: version: v2

# 4. Upload to Langfuse
python scripts/upload_prompts_to_langfuse.py

# 5. Test in agents
# Run system with new prompt version
```

---

## Detailed Workflow

### Step 1: Create New Prompt Version

Copy the current version to create a new version:

```bash
# Copy v1 to v2
cp prompts/agent/orchestrator/v1.prompt prompts/agent/orchestrator/v2.prompt
```

**Best Practice**: Always copy from the current version to preserve history.

---

### Step 2: Edit Prompt Content

Open the new prompt file and make changes:

```bash
vim prompts/agent/orchestrator/v2.prompt
```

**Example Changes**:
- Add few-shot examples
- Improve output format instructions
- Clarify role and task description
- Add chain-of-thought reasoning

**File Format**:
```yaml
---
model: gpt-4-turbo
temperature: 0.3
max_tokens: 1000
---

# Your prompt content here
You are an intent classifier...

# Current Query
{{ query }}
```

---

### Step 3: Update Configuration

Edit `configs/prompts/uploader.yaml` to use the new version:

```yaml
prompts:
  version: v2        # Changed from v1
  label: dev         # Test in dev first
```

**Important**: Always test in `dev` before promoting to `production`.

---

### Step 4: Upload to Langfuse

Run the upload script:

```bash
# Activate your Python environment first
conda activate your-env  # or source venv/bin/activate

# Upload prompts
python scripts/upload_prompts_to_langfuse.py
```

**Expected Output**:
```
Uploading prompts to Langfuse...
✓ agent_orchestrator (v2, dev)
✓ agent_clarification (v1, dev)
✓ agent_research (v1, dev)
✓ agent_synthesis (v1, dev)
Uploaded 4/4 prompts successfully
```

---

### Step 5: Test in Development

Test the new prompt with your agents:

```bash
# Run agent system
python src/main.py

# Or run tests
pytest tests/agents/test_orchestrator.py
```

**Monitor**:
- Check Langfuse dashboard for traces
- Verify correct prompt version is used
- Compare output quality with v1

---

### Step 6: Compare Performance

Use Langfuse dashboard to compare versions:

1. Navigate to "Prompts" → `agent_orchestrator`
2. View metrics for v1 vs v2
3. Compare:
   - Success rate
   - Average latency
   - Token usage
   - User feedback

---

### Step 7: A/B Test (Optional)

Run both versions simultaneously:

```yaml
# Deploy v1 to production
prompts:
  version: v1
  label: production

# Deploy v2 to staging for 20% traffic
prompts:
  version: v2
  label: staging
```

**Monitor results** and promote winner to production.

---

### Step 8: Promote to Production

If v2 performs better, promote to production:

```yaml
# Edit configs/prompts/uploader.yaml
prompts:
  version: v2
  label: production
```

```bash
# Re-upload with production label
python scripts/upload_prompts_to_langfuse.py
```

---

### Step 9: Document Changes

Commit changes to Git with clear message:

```bash
git add prompts/agent/orchestrator/v2.prompt
git add configs/prompts/uploader.yaml
git commit -m "feat(prompts): add few-shot examples to orchestrator v2

- Added 3 examples of RESEARCH vs CLARIFICATION
- Improved output format instructions
- Langfuse metrics show 15% improvement in accuracy"
```

---

## Rollback Procedure

If a new version causes issues:

### Step 1: Revert Configuration

```yaml
# Edit configs/prompts/uploader.yaml
prompts:
  version: v1  # Revert to previous version
  label: production
```

### Step 2: Re-upload

```bash
python scripts/upload_prompts_to_langfuse.py
```

### Step 3: Verify

Check Langfuse dashboard to confirm v1 is active.

---

## Best Practices

### Version Control

✅ **Do**:
- Copy previous version before editing
- Keep all versions in Git
- Use descriptive version numbers
- Document changes in commits

❌ **Don't**:
- Overwrite existing versions
- Delete old prompt files
- Skip version numbers
- Commit without testing

---

### Testing Strategy

1. **Local Testing**: Test prompt locally before uploading
2. **Dev Environment**: Upload to `dev` label first
3. **Staging**: Validate with representative traffic
4. **Production**: Promote after confirming success

---

### Prompt Iteration

**Good Iteration Cycle**:
```
v1 → Test → Metrics → v2 → Test → Metrics → v3
```

**Bad Iteration Cycle**:
```
v1 → v2 → v3 → v4 (no testing between versions)
```

---

### Collaboration

**For Engineers**:
- Create new versions via Git
- Upload to Langfuse
- Monitor metrics
- Promote to production

**For Non-Engineers**:
- Propose changes via Git PRs
- Review prompts in Langfuse
- Provide feedback on output quality
- No code changes needed

---

## Troubleshooting

### Upload Failed

**Check**:
```bash
# Verify credentials
echo $LANGFUSE_PUBLIC_KEY

# Verify config
cat configs/prompts/uploader.yaml

# Verify file exists
ls prompts/agent/orchestrator/v2.prompt
```

### Wrong Version Active

**Check**:
```bash
# What's configured?
cat configs/prompts/uploader.yaml

# What's uploaded?
# Check Langfuse dashboard

# Re-upload if needed
python scripts/upload_prompts_to_langfuse.py
```

### Prompt Not Working

**Debug**:
1. Check Langfuse trace for exact prompt used
2. Verify template variables are passed correctly
3. Check model/temperature settings in frontmatter
4. Compare with previous working version

---

## Common Tasks

### Creating Your First Prompt

```bash
# 1. Create directory
mkdir -p prompts/custom/my_agent

# 2. Create v1.prompt
cat > prompts/custom/my_agent/v1.prompt << 'EOF'
---
model: gpt-4-turbo
temperature: 0.3
max_tokens: 1000
---

You are a helpful assistant...

# Input
{{ query }}
EOF

# 3. Upload
python scripts/upload_prompts_to_langfuse.py
```

### Updating Existing Prompt

```bash
# 1. Copy to new version
cp prompts/custom/my_agent/v1.prompt prompts/custom/my_agent/v2.prompt

# 2. Edit v2.prompt
vim prompts/custom/my_agent/v2.prompt

# 3. Update config version to v2
# Edit configs/prompts/uploader.yaml

# 4. Upload
python scripts/upload_prompts_to_langfuse.py
```

### Testing Multiple Versions

```bash
# Upload v1 with dev label
export PROMPTS__VERSION=v1
export PROMPTS__LABEL=dev
python scripts/upload_prompts_to_langfuse.py

# Upload v2 with staging label
export PROMPTS__VERSION=v2
export PROMPTS__LABEL=staging
python scripts/upload_prompts_to_langfuse.py

# Compare in Langfuse dashboard
```

---

## Next Steps

- [Configuration](./configuration.md) - Detailed configuration options
- [API Reference](./api-reference.md) - PromptUploader implementation
- [Versioning](./versioning.md) - Version management strategy
