# Evaluation Module

LLM-as-a-Judge framework for testing agent workflow quality.

## Quick Start

```bash
# Run all evaluation scenarios
python scripts/run_llm_evaluation.py
```

**Output:**
```
Scenario 1: Autonomous Multi-Step Research
  Workflow: ✓ PASS
  Quality: answer_quality=0.90, factual_correctness=0.95, completeness=0.85

SUMMARY: 4/4 passed
✓ Scores logged to Langfuse
```

---

## What It Does

The evaluation module:
- **Runs test scenarios** through your API
- **Validates workflow** (correct agents/tools used)
- **Evaluates quality** with LLM-as-a-Judge
- **Logs scores** to Langfuse for tracking

---

## Two-Stage Evaluation

### 1. Workflow Validation

**Checks:** Did the system use the correct agents and tools?

```python
result['workflow'] = {
    'pass': True,  # ✓ or ✗
    'agents': {
        'included': ['orchestrator', 'research'],  # Expected & called
        'missing': [],                             # Expected but NOT called
    },
    'tools': {
        'included': ['pdf_retrieval'],
        'missing': []
    }
}
```

### 2. Quality Evaluation (LLM-as-a-Judge)

**Checks:** Is the answer good?

```python
result['quality'] = {
    'answer_quality': 0.90,        # Clear, well-structured
    'factual_correctness': 0.95,   # Accurate, no hallucinations
    'completeness': 0.85,          # Meets expected criteria
    'reasoning': "..."
}
```

---

## Configuration

`configs/evaluation/evaluation.yaml`:

```yaml
evaluation:
  api_url: http://localhost:8000  # API to test

  llm:
    provider: litellm
    model: gpt-4o                 # Judge model
    temperature: 0

  observability:
    langfuse:
      provider: langfuse
      host: https://cloud.langfuse.com
```

---

## Documentation

| Topic | Link |
|-------|------|
| **Test Scenarios** | [scenarios.md](./scenarios.md) |
| **Metrics Explained** | [metrics.md](./metrics.md) |
| **Adding Scenarios** | [adding-scenarios.md](./adding-scenarios.md) |
| **Components** | [components.md](./components.md) |

---

## Programmatic Usage

```python
from evaluation.evaluator import Evaluator

evaluator = Evaluator()
results = evaluator.run_all_scenarios()

for result in results:
    print(f"{result['scenario']}: {result['success']}")
```

---

## Requirements

- **API running**: `http://localhost:8000`
- **Langfuse setup**: For workflow validation
- **LLM access**: For quality evaluation (costs apply)

---

## Files

```
evaluation/
├── evaluator.py              # Main orchestrator
├── llm_judge.py              # Quality assessment
├── workflow_validator.py     # Agent/tool validation
└── scenarios/
    ├── autonomous.py         # Multi-step test
    ├── clarification.py      # Clarification test
    ├── pdf_only.py           # PDF-only test
    └── out_of_scope.py       # Web fallback test

scripts/
└── run_llm_evaluation.py     # CLI runner

configs/evaluation/
└── evaluation.yaml           # Configuration
```

---

## See Also

- [Agent Documentation](../agents/README.md)
- [System Overview](../architecture/system-overview.md)
- [Multi-Agent Orchestration](../architecture/multi-agent-orchestration.md)
