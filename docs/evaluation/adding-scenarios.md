# Adding New Scenarios

Guide to creating custom evaluation scenarios.

---

## Quick Reference

**What you define:**
- `query`: The test question
- `agents_should_include`: Which agents MUST run (fails if missing)
- `agents_should_exclude`: Which agents MUST NOT run (fails if called)
- `tools_should_include`: Which tools MUST be used (fails if missing)
- `tools_should_exclude`: Which tools MUST NOT be used (fails if called)
- `expected_answer_criteria`: What makes a good answer (used by LLM judge)

**What gets evaluated:**
1. **Workflow**: Did correct agents/tools run? (binary pass/fail)
2. **Quality**: How good is the answer? (scored 0-1 on 3 metrics)

---

## Step 1: Create Scenario File

Create `evaluation/scenarios/my_scenario.py`:

```python
from dataclasses import dataclass
from typing import List

@dataclass
class WorkflowExpectation:
    agents_should_include: List[str]   # Agents that MUST be called
    agents_should_exclude: List[str]   # Agents that MUST NOT be called
    tools_should_include: List[str]    # Tools that MUST be used
    tools_should_exclude: List[str]    # Tools that MUST NOT be used
    clarification_expected: bool = False

@dataclass
class Scenario:
    id: str                           # Unique identifier
    name: str                         # Display name
    query: str                        # Test query
    expected_workflow: WorkflowExpectation
    description: str                  # What this tests
    expected_answer_criteria: str     # Quality criteria

# Your scenario
MY_SCENARIO = Scenario(
    id="custom-test",
    name="My Test Scenario",
    query="Your test query here",
    expected_workflow=WorkflowExpectation(
        agents_should_include=["research"],
        agents_should_exclude=["clarification"],
        tools_should_include=["pdf_retrieval"],
        tools_should_exclude=["web_search"],
    ),
    description="Tests PDF-only retrieval",
    expected_answer_criteria="""
    Expected answer should:
    1. Extract information from PDFs only
    2. Cite specific papers
    3. NOT include web search results
    4. Be factually accurate
    """
)

SCENARIOS = [MY_SCENARIO]
```

---

## Step 2: Parameter Guide

### Basic Parameters

| Parameter | Type | Purpose | Example |
|-----------|------|---------|---------|
| **id** | str | Unique identifier | `"2-pdf-only"` |
| **name** | str | Display name | `"PDF Only Query"` |
| **query** | str | Test question | `"What is in Section 3.2?"` |
| **description** | str | What scenario tests | `"Tests PDF retrieval"` |

### Workflow Expectations

| Parameter | Type | Validation | When to Use |
|-----------|------|------------|-------------|
| **agents_should_include** | List[str] | **Fails** if missing | Agents that MUST run |
| **agents_should_exclude** | List[str] | **Fails** if called | Agents that should NOT run |
| **tools_should_include** | List[str] | **Fails** if missing | Tools that MUST be used |
| **tools_should_exclude** | List[str] | **Fails** if called | Tools that should NOT be used |

**Common Values:**
- **Agents**: `orchestrator`, `research`, `synthesis`, `clarification`
- **Tools**: `pdf_retrieval`, `web_search`

### Quality Criteria

**`expected_answer_criteria`** (str)

Multi-line description of what makes a **good answer**. Used by LLM-as-a-Judge.

**Format:**
```python
expected_answer_criteria="""
Expected answer should:
1. First requirement
2. Second requirement
3. Third requirement
...
"""
```

**Tips:**
- Be specific and measurable
- List 3-5 concrete criteria
- Focus on content, not style
- Include what to avoid (e.g., "NOT include web results")

---

## Step 3: Example Scenarios

### Example 1: PDF-Only Query

**Goal:** Ensure system doesn't waste time on web search when PDF is enough

```python
PDF_ONLY = Scenario(
    id="2-pdf-only",
    name="PDF Only",
    query="What is in Section 3.2 of Zhang et al. 2024?",
    expected_workflow=WorkflowExpectation(
        agents_should_include=["research"],      # Must call research
        agents_should_exclude=["clarification"], # Query is clear
        tools_should_include=["pdf_retrieval"],  # Must search PDFs
        tools_should_exclude=["web_search"],     # Don't waste time on web
    ),
    description="Tests PDF retrieval without unnecessary web search",
    expected_answer_criteria="""
    Expected answer should:
    1. Extract content from Section 3.2 specifically
    2. Cite Zhang et al. 2024 paper
    3. NOT include web search results
    4. Be factually accurate to the paper
    """
)
```

**What gets validated:**
- ✅ Workflow: `research` called, `pdf_retrieval` used, `web_search` NOT used
- ✅ Quality: Answer meets all 4 criteria (scored by LLM judge)

---

### Example 2: Multi-Tool Query

**Goal:** Ensure system autonomously uses multiple tools when needed

```python
MULTI_TOOL = Scenario(
    id="3-autonomous",
    name="Autonomous Multi-Step",
    query="Compare BERT vs GPT accuracy and find recent papers by the authors",
    expected_workflow=WorkflowExpectation(
        agents_should_include=["research"],
        agents_should_exclude=["clarification"],
        tools_should_include=["pdf_retrieval", "web_search"],  # BOTH required
        tools_should_exclude=[],
    ),
    description="Tests autonomous multi-tool execution",
    expected_answer_criteria="""
    Expected answer should:
    1. Compare BERT vs GPT with specific accuracy numbers
    2. Include author names and recent papers
    3. Synthesize information from both PDFs and web
    4. Be well-structured with clear comparison
    5. Cite sources for all claims
    """
)
```

**What gets validated:**
- ✅ Workflow: BOTH `pdf_retrieval` AND `web_search` used
- ✅ Quality: Answer meets all 5 criteria

---

### Example 3: Clarification Needed

**Goal:** Ensure system asks for clarification instead of guessing

```python
AMBIGUOUS = Scenario(
    id="1-clarification",
    name="Ambiguous Query",
    query="How many examples are enough for good accuracy?",
    expected_workflow=WorkflowExpectation(
        agents_should_include=["clarification"],      # Must ask for clarification
        agents_should_exclude=["research"],           # Should NOT research yet
        tools_should_include=[],
        tools_should_exclude=["pdf_retrieval", "web_search"],  # No tools yet
        clarification_expected=True,
    ),
    description="Tests clarification for vague queries",
    expected_answer_criteria="""
    Expected response should:
    1. Ask what 'enough' means (specific number?)
    2. Ask what 'good accuracy' means (threshold?)
    3. Ask about task/domain (what are you training?)
    4. NOT attempt to answer without clarification
    5. Be polite and helpful in asking questions
    """
)
```

**What gets validated:**
- ✅ Workflow: `clarification` called, `research` NOT called, NO tools used
- ✅ Quality: Response asks all necessary questions

---

## Step 4: Register Scenario

Add to `evaluation/evaluator.py`:

```python
from evaluation.scenarios import (
    autonomous,
    clarification,
    pdf_only,
    out_of_scope,
    my_scenario  # ← Import your scenario
)

# In run_all_scenarios() method (line ~263)
all_scenarios = [
    *[(s, 'autonomous') for s in autonomous.SCENARIOS],
    *[(s, 'clarification') for s in clarification.SCENARIOS],
    *[(s, 'pdf_only') for s in pdf_only.SCENARIOS],
    *[(s, 'out_of_scope') for s in out_of_scope.SCENARIOS],
    *[(s, 'custom') for s in my_scenario.SCENARIOS],  # ← Add here
]
```

---

## Step 5: Run Evaluation

```bash
python scripts/run_llm_evaluation.py
```

**Output:**
```
Scenario: My Test Scenario (custom)
  Session ID: eval-custom-test-20250129-143022
  Workflow: ✓ PASS
    Agents: ✓
      ✓ research
      ✓ clarification (excluded ✓)
    Tools: ✓
      ✓ pdf_retrieval
      ✓ web_search (excluded ✓)
  Quality:
    answer_quality: 0.90
    factual_correctness: 0.95
    completeness: 0.85
    reasoning: Answer meets all criteria...
```

---

## Common Patterns

### Pattern 1: Tool Exclusion Test

Ensure system doesn't use unnecessary tools:

```python
tools_should_exclude=["web_search"]  # Don't search web for PDF queries
```

### Pattern 2: Agent Flow Test

Ensure correct agent routing:

```python
agents_should_include=["research", "synthesis"]
agents_should_exclude=["clarification"]  # Don't clarify clear queries
```

### Pattern 3: Multi-Step Test

Ensure system uses multiple tools autonomously:

```python
tools_should_include=["pdf_retrieval", "web_search"]  # Must use BOTH
```

---

## Validation Logic

### Workflow Validation

| Condition | Result |
|-----------|--------|
| All `agents_should_include` were called | ✅ agents.pass = True |
| Any `agents_should_include` missing | ❌ agents.pass = False |
| Any `agents_should_exclude` were called | ❌ agents.pass = False |
| All `tools_should_include` were used | ✅ tools.pass = True |
| Any `tools_should_include` missing | ❌ tools.pass = False |
| Any `tools_should_exclude` were used | ❌ tools.pass = False |

**Overall:** `workflow.pass = agents.pass AND tools.pass`

### Quality Evaluation

LLM judge compares actual answer against `expected_answer_criteria` and scores:
- **answer_quality**: Clear, well-structured (0-1)
- **factual_correctness**: Accurate, no hallucinations (0-1)
- **completeness**: Meets all criteria (0-1)

---

## Tips

1. **Be Specific**: Clear expectations → better validation
2. **Test Edge Cases**: Ambiguous queries, out-of-scope, multi-tool
3. **Use Exclusions**: Test what should NOT happen
4. **Number Criteria**: Makes evaluation clearer (1, 2, 3...)
5. **Avoid Assumptions**: Don't assume agents know context

---

## See Also

- [Evaluation Module](./README.md) - Back to evaluation overview
- [Scenarios](./scenarios.md) - Existing test scenarios
- [Metrics](./metrics.md) - How validation works
- [Components](./components.md) - LLMJudge and WorkflowValidator
