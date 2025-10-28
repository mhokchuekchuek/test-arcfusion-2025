# Evaluation Module

LLM-as-a-Judge evaluation framework for testing agent workflow quality.

## Quick Start

```bash
# Run all evaluation scenarios
python scripts/run_llm_evaluation.py
```

Output:
```
==============================================================
LLM-as-a-Judge Evaluation Runner
==============================================================

Scenario 1: Autonomous Multi-Step Research
  Workflow: ✓ PASS
  Quality: answer_quality=0.90, factual_correctness=0.95, completeness=0.85

Scenario 2: Clarification Loop
  Workflow: ✓ PASS
  Quality: answer_quality=0.90, factual_correctness=0.95

==============================================================
SUMMARY: 4/4 passed
✓ Scores logged to Langfuse
==============================================================
```

---

## What It Does

The evaluation module:
- **Runs test scenarios** through your API
- **Validates workflow** (correct agents/tools used)
- **Evaluates quality** with LLM-as-a-Judge
- **Logs scores** to Langfuse for tracking

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

## Test Scenarios

### 1. Autonomous Multi-Step

```python
# evaluation/scenarios/autonomous.py
QUERY = "Compare BERT vs GPT accuracy and tell me which is better"
EXPECTED_AGENTS = ["orchestrator", "research", "synthesis"]
EXPECTED_TOOLS = ["pdf_retrieval", "web_search"]
```

**Tests:**
- Orchestrator routes to research
- Research uses BOTH tools autonomously
- Synthesis formats answer

---

### 2. Clarification Loop

```python
# evaluation/scenarios/clarification.py
QUERY = "Tell me about the accuracy"
EXPECTED_AGENTS = ["orchestrator", "clarification"]
EXCLUDED_AGENTS = ["research", "synthesis"]
```

**Tests:**
- Orchestrator detects vagueness
- Routes to clarification
- Does NOT proceed to research

---

### 3. PDF-Only Query

```python
# evaluation/scenarios/pdf_only.py
QUERY = "What is in Section 3.2 of Zhang et al. 2024?"
EXPECTED_TOOLS = ["pdf_retrieval"]
EXCLUDED_TOOLS = ["web_search"]
```

**Tests:**
- Research uses PDF tool only
- Skips web search (not needed)

---

### 4. Web Search Fallback

```python
# evaluation/scenarios/out_of_scope.py
QUERY = "What's the latest model from OpenAI?"
EXPECTED_TOOLS = ["web_search"]
```

**Tests:**
- Research recognizes out-of-scope query
- Falls back to web search

---

## Programmatic Usage

### Run All Scenarios

```python
from evaluation.evaluator import Evaluator

evaluator = Evaluator()
results = evaluator.run_all_scenarios()

for result in results:
    print(f"{result['scenario']}: {result['success']}")
```

---

### Run Single Scenario

```python
from evaluation.scenarios import autonomous

result = evaluator.run_scenario(
    name=autonomous.SCENARIO_NAME,
    query=autonomous.QUERY,
    expected_agents=autonomous.EXPECTED_AGENTS,
    expected_tools=autonomous.EXPECTED_TOOLS
)

# Check results
if result['success']:
    print(f"Workflow: {'PASS' if result['workflow']['pass'] else 'FAIL'}")
    print(f"Quality scores: {result['quality']}")
```

---

### Custom Evaluation

```python
evaluator = Evaluator()

result = evaluator.run_scenario(
    name="My Test",
    query="What is RAG?",
    expected_agents=["orchestrator", "research", "synthesis"],
    expected_tools=["pdf_retrieval"]
)

# Access results
workflow_pass = result['workflow']['pass']
quality_scores = result['quality']
reasoning = result['quality']['reasoning']
```

---

## Metrics

### Workflow Validation

Validates correct agent routing and tool usage:

```python
result['workflow'] = {
    'pass': True,
    'agents': {
        'pass': True,
        'included': ['orchestrator', 'research'],  # Expected & called
        'excluded': ['clarification'],            # Expected NOT called
        'missing': [],                            # Expected but NOT called
        'unexpected': []                          # NOT expected but called
    },
    'tools': {
        'pass': True,
        'included': ['pdf_retrieval'],
        'excluded': ['web_search'],
        'missing': [],
        'unexpected': []
    }
}
```

---

### Quality Scores (LLM-as-a-Judge)

```python
result['quality'] = {
    'answer_quality': 0.90,        # Clarity, structure, helpfulness (0-1)
    'factual_correctness': 0.95,   # Accuracy, no hallucinations (0-1)
    'completeness': 0.85,          # Meets expected criteria (0-1)
    'reasoning': "Answer is well-structured and factually accurate..."
}
```

**Metrics:**
- **answer_quality**: Clear, well-structured, helpful response
- **factual_correctness**: Accurate information supported by sources, no hallucinations
- **completeness**: Meets expected answer criteria, addresses all query aspects

---

## Components

### Evaluator (`evaluation/evaluator.py`)

Main orchestrator:
```python
evaluator = Evaluator()

# Run scenarios
results = evaluator.run_all_scenarios()

# Check specific scenario
result = evaluator.run_scenario(
    name="Test",
    query="...",
    expected_agents=[...],
    expected_tools=[...]
)
```

---

### LLMJudge (`evaluation/llm_judge.py`)

Quality assessment using LLM:
```python
judge = LLMJudge(llm_client, langfuse_client)

scores = judge.evaluate_quality(
    query="What is RAG?",
    expected_criteria="Should explain retrieval and generation",
    answer="RAG is Retrieval-Augmented Generation...",
    sources=[...]
)
# Returns: {
#   'answer_quality': 0.90,
#   'factual_correctness': 0.95,
#   'completeness': 0.85,
#   'reasoning': '...'
# }
```

---

### WorkflowValidator (`evaluation/workflow_validator.py`)

Validates workflow execution:
```python
validator = WorkflowValidator(langfuse_client)

validation = validator.validate(
    session_id="eval-123",
    expected_agents=["orchestrator", "research"],
    expected_tools=["pdf_retrieval"]
)
# Returns: {'pass': True, 'agents': {...}, 'tools': {...}}
```

---

## Adding New Scenarios

Create `evaluation/scenarios/my_scenario.py`:

```python
SCENARIO_NAME = "My Test Scenario"
CATEGORY = "Custom"

QUERY = "Your test query here"

EXPECTED_AGENTS = ["orchestrator", "research"]
EXCLUDED_AGENTS = ["clarification"]

EXPECTED_TOOLS = ["pdf_retrieval"]
EXCLUDED_TOOLS = ["web_search"]

EXPECTED_ANSWER_CRITERIA = "Should explain the main concept clearly"
```

Import in `evaluation/evaluator.py`:

```python
from evaluation.scenarios import my_scenario

# Add to scenarios list
SCENARIOS = [
    autonomous,
    clarification,
    pdf_only,
    out_of_scope,
    my_scenario  # Your new scenario
]
```

---

## Langfuse Integration

Scores are automatically logged to Langfuse:

```python
# Logged for each evaluation
{
    "name": "eval_autonomous_multi_step",
    "session_id": "eval-auto-123",
    "input": {"query": "..."},
    "output": {"answer": "..."},
    "metadata": {
        "scenario": "Autonomous Multi-Step",
        "workflow_pass": True,
        "quality_scores": {
            "answer_quality": 0.90,
            "factual_correctness": 0.95,
            "completeness": 0.85
        }
    }
}
```

**View in Langfuse:**
1. Go to https://cloud.langfuse.com
2. Filter sessions starting with "eval-"
3. View metrics over time
4. Compare scenarios

---

## Example Output

```
==============================================================
LLM-as-a-Judge Evaluation Runner
==============================================================

Starting evaluation process

Scenario 1: Autonomous Multi-Step Research (Multi-step)
  Session ID: eval-auto-abc123
  Workflow: ✓ PASS
    Agents: ✓
      ✓ orchestrator
      ✓ research
      ✓ synthesis
    Tools: ✓
      ✓ pdf_retrieval
      ✓ web_search
  Quality:
    answer_quality: 0.90
    factual_correctness: 0.95
    completeness: 0.85
    reasoning: Answer addresses both PDF and web sources

Scenario 2: Clarification Loop (Clarification)
  Session ID: eval-clar-def456
  Workflow: ✓ PASS
    Agents: ✓
      ✓ orchestrator
      ✓ clarification
      ✓ research (excluded ✓)
      ✓ synthesis (excluded ✓)
  Quality:
    answer_quality: 0.90
    factual_correctness: 0.95

==============================================================
EVALUATION SUMMARY
==============================================================

Total: 4 scenarios
Workflow Passed: 4/4
Quality Evaluation Successful: 4
Quality Evaluation Failed: 0
==============================================================

✓ All evaluations complete
✓ Scores logged to Langfuse
✓ View results at: https://cloud.langfuse.com
```

---

## Testing

```python
# Test evaluator
def test_evaluator():
    evaluator = Evaluator()
    results = evaluator.run_all_scenarios()
    assert len(results) == 4
    assert all(r['success'] for r in results)

# Test LLM judge
def test_llm_judge():
    judge = LLMJudge(mock_llm, langfuse_client)
    scores = judge.evaluate_quality(
        query="What is AI?",
        expected_criteria="Should define artificial intelligence",
        answer="AI is artificial intelligence",
        sources=[]
    )
    assert 0 <= scores['answer_quality'] <= 1
    assert 0 <= scores['factual_correctness'] <= 1
    assert 0 <= scores['completeness'] <= 1
```

---

## Requirements

- **API running**: `http://localhost:8000`
- **Langfuse setup**: For workflow validation
- **LLM access**: For quality evaluation (costs apply)

---

## Limitations

- Requires API to be running
- LLM-as-a-Judge can be subjective
- Evaluation costs (GPT-4 API calls)
- Workflow validation depends on Langfuse traces

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

- [Agent Documentation](../agents/README.md) - How agents work
- [System Overview](../architecture/system-overview.md) - Full system
- [Multi-Agent Orchestration](../architecture/multi-agent-orchestration.md) - Workflow details
