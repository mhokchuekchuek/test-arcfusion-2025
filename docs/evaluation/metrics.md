# Evaluation Metrics

How scenarios are evaluated: workflow validation + quality scoring.

---

## 1. Workflow Validation

**Question:** Did the system use the correct agents and tools?

**Result:** Binary PASS/FAIL

### Structure

```python
result['workflow'] = {
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
        'included': ['pdf_retrieval'],
        'excluded': ['web_search'],
        'missing': [],
        'unexpected': []
    }
}
```

### Validation Logic

| Field | Meaning | Pass Condition |
|-------|---------|----------------|
| **included** | Expected agents/tools that WERE called | All must be present |
| **excluded** | Agents/tools that should NOT be called | None should be present |
| **missing** | Expected but NOT called | Must be empty |
| **unexpected** | Called but NOT expected | Must be empty |

**Overall pass:** `agents.pass == True AND tools.pass == True`

### Example: PASS

```python
# Scenario expectation
agents_should_include = ["research"]
agents_should_exclude = ["clarification"]
tools_should_include = ["pdf_retrieval"]
tools_should_exclude = ["web_search"]

# Actual execution
agents_called = ["orchestrator", "research"]
tools_used = ["pdf_retrieval"]

# Result: ✓ PASS
workflow = {
    'pass': True,
    'agents': {
        'pass': True,
        'included': ['research'],      # ✓ research was called
        'excluded': ['clarification'], # ✓ clarification was NOT called
        'missing': [],                 # ✓ no missing agents
        'unexpected': []               # ✓ orchestrator is always expected
    },
    'tools': {
        'pass': True,
        'included': ['pdf_retrieval'], # ✓ pdf_retrieval was used
        'excluded': ['web_search'],    # ✓ web_search was NOT used
        'missing': [],
        'unexpected': []
    }
}
```

### Example: FAIL

```python
# Scenario expectation
tools_should_include = ["pdf_retrieval", "web_search"]  # Both required

# Actual execution
tools_used = ["pdf_retrieval"]  # Only one used

# Result: ✗ FAIL
workflow = {
    'pass': False,  # ✗
    'tools': {
        'pass': False,             # ✗
        'included': ['pdf_retrieval'],
        'missing': ['web_search'], # ✗ web_search was required but not used
    }
}
```

---

## 2. Quality Scores (LLM-as-a-Judge)

**Question:** Is the answer good?

**Result:** Three metrics scored 0-1

### Metrics

```python
result['quality'] = {
    'answer_quality': 0.90,        # 0-1 scale
    'factual_correctness': 0.95,   # 0-1 scale
    'completeness': 0.85,          # 0-1 scale
    'reasoning': "Answer is well-structured and factually accurate..."
}
```

### 1. Answer Quality (0-1)

**Question:** Is the response clear, well-structured, and helpful?

| Score | Quality | Description |
|-------|---------|-------------|
| **1.0** | Excellent | Clear, professional, well-organized |
| **0.8** | Good | Clear and helpful, minor issues |
| **0.6** | Adequate | Understandable but could be clearer |
| **0.4** | Poor | Unclear, poorly structured |
| **0.2** | Very poor | Confusing, disorganized |
| **0.0** | Unacceptable | Incomprehensible |

### 2. Factual Correctness (0-1)

**Question:** Is the information accurate based on sources, without hallucinations?

| Score | Accuracy | Description |
|-------|----------|-------------|
| **1.0** | Perfect | All information supported by sources |
| **0.8** | Mostly correct | Minor unsupported claims |
| **0.6** | Some issues | Few statements not in sources |
| **0.4** | Significant issues | Multiple factual errors |
| **0.2** | Major issues | Substantial misinformation |
| **0.0** | Completely wrong | Fabricated information |

**Critical:** Hallucinations are penalized heavily!

### 3. Completeness (0-1)

**Question:** Does the response meet the expected criteria?

| Score | Coverage | Description |
|-------|----------|-------------|
| **1.0** | Complete | Meets all expected criteria |
| **0.8** | Mostly complete | Minor omissions |
| **0.6** | Partially complete | Missing some elements |
| **0.4** | Incomplete | Significant gaps |
| **0.2** | Minimal | Only addresses small part |
| **0.0** | Does not answer | Failed to meet criteria |

**Compared against:** `expected_answer_criteria` from scenario

### Example Evaluation

**Scenario:**
```python
expected_answer_criteria = """
Expected answer should:
1. Identify a specific text-to-SQL approach
2. Mention accuracy metrics or benchmarks
3. Provide author information
4. Synthesize PDF and web sources
5. Be coherent and well-structured
"""
```

**Actual Answer:**
```
DIN-SQL is the current state-of-the-art text-to-SQL model, achieving
85.3% execution accuracy on the Spider benchmark (Liu et al., 2023).
The approach was developed by researchers at Stanford University...
```

**LLM Judge Scores:**
```python
{
    'answer_quality': 0.95,      # Well-structured, professional
    'factual_correctness': 1.0,  # All info supported by sources
    'completeness': 0.90,        # Meets 4/5 criteria (missing web synthesis)
    'reasoning': "Answer clearly identifies DIN-SQL, cites metrics, and
                  provides author info. Minor: could synthesize more web sources."
}
```

---

## How Scores Are Used

### 1. Logged to Langfuse

Each metric logged as separate score:
```python
langfuse.create_score(
    name="quality_answer_quality",
    value=0.90,
    trace_id=session_id
)
```

**View in Langfuse:**
- Filter by score type
- Track trends over time
- Compare scenarios

### 2. Overall Pass/Fail

```python
# Workflow: binary
workflow_pass = result['workflow']['pass']

# Quality: no strict threshold (subjective)
# Up to you to decide acceptable scores
average_quality = (
    result['quality']['answer_quality'] +
    result['quality']['factual_correctness'] +
    result['quality']['completeness']
) / 3
```

---

## Prompt Used

Quality evaluation uses: `prompts/evaluation/quality/v1.prompt`

Key sections:
- Expected criteria (from scenario)
- Actual response
- Sources used
- Scoring rubric (shown above)

---

## See Also

- [Evaluation Module](./README.md) - Back to evaluation overview
- [Scenarios](./scenarios.md) - What gets tested
- [Adding Scenarios](./adding-scenarios.md) - Define expected_answer_criteria
- [Components](./components.md) - LLMJudge implementation
