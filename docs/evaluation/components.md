# Evaluation Components

The three main components that power the evaluation system.

---

## 1. Evaluator

**Location**: `evaluation/evaluator.py`

Main orchestrator that runs scenarios and coordinates validation.

### Usage

```python
from evaluation.evaluator import Evaluator

evaluator = Evaluator()

# Run all scenarios
results = evaluator.run_all_scenarios()

# Run single scenario
from evaluation.scenarios import autonomous
result = evaluator.run_scenario(autonomous.MULTI_STEP_QUERY)
```

### What It Does

1. **Loads Configuration**: From `configs/evaluation/evaluation.yaml`
2. **Runs Scenarios**: Sends queries to your API
3. **Validates Workflow**: Checks agents/tools via WorkflowValidator
4. **Evaluates Quality**: Scores answers via LLMJudge
5. **Logs to Langfuse**: Tracks scores over time

### Key Methods

#### `run_all_scenarios()`

Runs all evaluation scenarios.

```python
results = evaluator.run_all_scenarios()
# Returns: List of evaluation results

for result in results:
    print(f"{result['scenario']}: {result['success']}")
    print(f"  Workflow: {result['workflow']['pass']}")
    print(f"  Quality: {result['quality']}")
```

**Returns:**
```python
[
    {
        'scenario': 'Autonomous Multi-Step',
        'scenario_id': '3-autonomous-multistep',
        'category': 'autonomous',
        'success': True,
        'workflow': {...},      # Workflow validation result
        'quality': {...},       # Quality scores
        'session_id': 'eval-...'
    },
    ...
]
```

#### `run_scenario(scenario)`

Runs single scenario.

```python
from evaluation.scenarios.autonomous import MULTI_STEP_QUERY

result = evaluator.run_scenario(MULTI_STEP_QUERY)
```

**Returns:** API response with session_id

---

## 2. LLMJudge

**Location**: `evaluation/llm_judge.py`

LLM-as-a-Judge evaluator for response quality.

### Usage

```python
from evaluation.llm_judge import LLMJudge

judge = LLMJudge(
    llm_client=llm_client,
    langfuse_client=langfuse_client
)

scores = judge.evaluate_quality(
    query="What is RAG?",
    expected_criteria="Should explain retrieval and generation",
    answer="RAG is Retrieval-Augmented Generation...",
    sources=[...]
)
```

### Key Methods

#### `evaluate_quality()`

Evaluates answer quality against criteria.

```python
scores = judge.evaluate_quality(
    query="What is RAG?",
    expected_criteria="""
    Expected answer should:
    1. Define RAG clearly
    2. Explain retrieval step
    3. Explain generation step
    4. Provide examples
    """,
    answer="RAG is Retrieval-Augmented Generation...",
    sources=[{"text": "...", "source": "paper.pdf"}],
    session_id="eval-123"  # Optional, for Langfuse logging
)
```

**Returns:**
```python
{
    'answer_quality': 0.90,        # Clarity, structure (0-1)
    'factual_correctness': 0.95,   # Accuracy, no hallucinations (0-1)
    'completeness': 0.85,          # Meets all criteria (0-1)
    'reasoning': "Answer clearly defines RAG and explains both steps..."
}
```

#### `load_evaluation_prompt(category)`

Loads evaluation prompt from Langfuse.

```python
template = judge.load_evaluation_prompt("quality")
# Returns: Prompt template with {{variable}} placeholders
```

**Available categories:**
- `quality`: General quality evaluation
- `autonomous`: Multi-step execution
- `clarification`: Clarification quality
- `pdf_only`: PDF retrieval quality

### How It Works

1. **Load Prompt**: Fetches prompt from Langfuse (`evaluation_quality`)
2. **Fill Variables**: Replaces `{{query}}`, `{{expected_criteria}}`, etc.
3. **Call LLM**: Sends to judge model (GPT-4)
4. **Parse JSON**: Extracts scores from response
5. **Log to Langfuse**: Records scores for tracking

### Prompt Used

`prompts/evaluation/quality/v1.prompt`:

```yaml
---
model: gpt-4
temperature: 0.0
---

You are an expert evaluator assessing AI system responses.

## Context
**Original Query:** {{query}}
**Expected Criteria:** {{expected_criteria}}
**Actual Response:** {{answer}}
**Sources:** {{sources}}

## Evaluation
Score on three dimensions (0-1):
1. answer_quality: Clarity and structure
2. factual_correctness: Accuracy, no hallucinations
3. completeness: Meets expected criteria

Return JSON:
{
  "answer_quality": 0.0-1.0,
  "factual_correctness": 0.0-1.0,
  "completeness": 0.0-1.0,
  "reasoning": "Brief explanation"
}
```

---

## 3. WorkflowValidator

**Location**: `evaluation/workflow_validator.py`

Validates that correct agents and tools were used.

### Usage

```python
from evaluation.workflow_validator import WorkflowValidator

validator = WorkflowValidator(langfuse_client=langfuse_client)

validation = validator.validate(
    scenario=scenario,
    session_id="eval-123"
)
```

### Key Method

#### `validate(scenario, session_id)`

Validates workflow execution against scenario expectations.

```python
from evaluation.scenarios.autonomous import MULTI_STEP_QUERY

validation = validator.validate(
    scenario=MULTI_STEP_QUERY,
    session_id="eval-auto-abc123"
)
```

**Returns:**
```python
{
    'pass': True,  # Overall pass/fail
    'agents': {
        'pass': True,
        'included': ['orchestrator', 'research'],  # Expected & called ✓
        'excluded': ['clarification'],            # Expected NOT called ✓
        'missing': [],                            # Expected but NOT called ✗
        'unexpected': []                          # NOT expected but called ✗
    },
    'tools': {
        'pass': True,
        'included': ['pdf_retrieval', 'web_search'],
        'excluded': [],
        'missing': [],
        'unexpected': []
    }
}
```

### How It Works

1. **Fetch Trace**: Gets execution trace from Langfuse by session_id
2. **Extract Agents**: Finds which agents were called
3. **Extract Tools**: Finds which tools were used
4. **Compare**: Matches against scenario expectations
5. **Validate**: Checks included/excluded/missing/unexpected

### Validation Logic

**Agents Pass:**
- All `agents_should_include` were called
- None of `agents_should_exclude` were called

**Tools Pass:**
- All `tools_should_include` were used
- None of `tools_should_exclude` were used

**Overall Pass:**
- `agents.pass == True AND tools.pass == True`

---

## Component Flow

```
Evaluator
    │
    ├─→ Run Scenario
    │   └─→ POST /chat with query
    │
    ├─→ WorkflowValidator
    │   ├─→ Fetch trace from Langfuse
    │   ├─→ Extract agents/tools
    │   └─→ Validate against expectations
    │
    └─→ LLMJudge
        ├─→ Load evaluation prompt
        ├─→ Fill with query/answer/criteria
        ├─→ Call judge LLM (GPT-4)
        ├─→ Parse scores
        └─→ Log to Langfuse
```

---

## Testing

### Mock Evaluator

```python
def test_evaluator():
    evaluator = Evaluator()
    results = evaluator.run_all_scenarios()

    assert len(results) > 0
    assert all(r['success'] for r in results)
```

### Mock LLMJudge

```python
def test_llm_judge():
    mock_llm = Mock(spec=BaseLLM)
    mock_llm.generate.return_value = '{"answer_quality": 0.9, ...}'

    judge = LLMJudge(llm_client=mock_llm)
    scores = judge.evaluate_quality(
        query="Test",
        expected_criteria="Should work",
        answer="It works",
        sources=[]
    )

    assert 0 <= scores['answer_quality'] <= 1
```

### Mock WorkflowValidator

```python
def test_workflow_validator():
    validator = WorkflowValidator(langfuse_client=mock_langfuse)

    validation = validator.validate(
        scenario=test_scenario,
        session_id="test-123"
    )

    assert 'pass' in validation
    assert 'agents' in validation
    assert 'tools' in validation
```

---

## Configuration

All components use `configs/evaluation/evaluation.yaml`:

```yaml
evaluation:
  api_url: http://localhost:8000  # API to test

  llm:
    provider: litellm
    model: gpt-4o                 # Judge model
    temperature: 0
    proxy_url: http://localhost:4000
    api_key: dummy

  observability:
    langfuse:
      provider: langfuse
      public_key: ${LANGFUSE_PUBLIC_KEY}
      secret_key: ${LANGFUSE_SECRET_KEY}
      host: https://cloud.langfuse.com
```

---

## See Also

- [Metrics](./metrics.md) - What gets measured
- [Adding Scenarios](./adding-scenarios.md) - Create custom tests
- [Evaluation Module](./README.md) - Back to evaluation overview
