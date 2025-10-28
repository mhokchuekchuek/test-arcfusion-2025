# Prompt Management System

Production-ready prompt engineering with versioning, centralized management, and observability.

## Quick Start

**New to the prompt system?** Start here:
1. [Structure](./structure.md) - Directory organization and file format
2. [Versioning](./versioning.md) - Version control and workflow
3. [Langfuse Integration](./langfuse-integration.md) - Centralized management
4. [Development Guide](./workflow.md) - Create and deploy prompts

---

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

---

## Prompt Categories

### Agent Prompts (`agent/`)

**Orchestrator** - Route queries to appropriate agents
- [Design Documentation](./agent/orchestrator/design.md)
- [API Reference](./agent/orchestrator/api-reference.md)
- [Examples](./agent/orchestrator/examples.md)

**Clarification** - Generate clarifying questions for vague queries
- [Design Documentation](./agent/clarification/design.md)
- [API Reference](./agent/clarification/api-reference.md)
- [Examples](./agent/clarification/examples.md)

**Research** - Plan and execute multi-step research (ReAct pattern)
- [Design Documentation](./agent/research/design.md)
- [API Reference](./agent/research/api-reference.md)
- [Examples](./agent/research/examples.md)

**Synthesis** - Format final answer with citations
- [Design Documentation](./agent/synthesis/design.md)
- [API Reference](./agent/synthesis/api-reference.md)
- [Examples](./agent/synthesis/examples.md)

### RAG Prompts (`rag/`)

**Document Retrieval** - Generate effective retrieval queries
- Purpose: Query reformulation and context injection
- Code: src/rag/retriever/document_retriever.py:12

### Evaluation Prompts (`evaluation/`)

**Quality** - Score response quality (LLM-as-a-Judge)
- Purpose: Rate relevance, accuracy, completeness, citations
- Code: evaluation/llm_judge.py

---

## Documentation Index

### Core Concepts
- [Structure](./structure.md) - Directory layout and file format
- [Versioning](./versioning.md) - Version management strategy
- [Langfuse Integration](./langfuse-integration.md) - Centralized prompt management
- [Configuration](./configuration.md) - Settings and environment variables

### Development
- [Workflow](./workflow.md) - Creating, testing, and deploying prompts
- [API Reference](./api-reference.md) - PromptUploader class documentation

---

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

---

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

---

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
