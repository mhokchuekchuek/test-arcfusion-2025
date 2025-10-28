# Test Scenarios

Predefined test scenarios for evaluating agent workflow behavior.

---

## 1. Autonomous Multi-Step

**Tests:** System can autonomously use multiple tools for complex queries

```python
# evaluation/scenarios/autonomous.py
QUERY = "What is the state-of-the-art text-to-sql approach? And search on the web to tell me more about the authors"

EXPECTED_AGENTS = ["orchestrator", "research", "synthesis"]
EXPECTED_TOOLS = ["pdf_retrieval", "web_search"]  # BOTH required
```

**Expected Behavior:**
1. Orchestrator routes to research agent
2. Research uses PDF retrieval autonomously
3. Research uses web search autonomously
4. Synthesis formats final answer

**What Gets Validated:**
- ✅ Research agent called
- ✅ Both `pdf_retrieval` AND `web_search` used
- ✅ Answer synthesizes info from both sources

---

## 2. Clarification Loop

**Tests:** System asks clarifying questions for ambiguous queries

```python
# evaluation/scenarios/clarification.py
QUERY = "How many examples are enough for good accuracy?"

EXPECTED_AGENTS = ["orchestrator", "clarification"]
EXCLUDED_AGENTS = ["research", "synthesis"]
EXCLUDED_TOOLS = ["pdf_retrieval", "web_search"]
```

**Expected Behavior:**
1. Orchestrator detects vague query ("enough", "good")
2. Routes to clarification agent
3. Asks clarifying questions
4. Does NOT proceed to research

**What Gets Validated:**
- ✅ Clarification agent called
- ✅ Research agent NOT called
- ✅ No tools used (shouldn't search yet)

**Examples of Ambiguous Queries:**
- "How many examples are enough for good accuracy?" (vague quantifiers)
- "Tell me more about it" (undefined pronoun)
- "What's the accuracy?" (missing context)

---

## 3. PDF-Only Query

**Tests:** System uses PDF retrieval only when appropriate

```python
# evaluation/scenarios/pdf_only.py
QUERY = "What is in Section 3.2 of Zhang et al. 2024?"

EXPECTED_TOOLS = ["pdf_retrieval"]
EXCLUDED_TOOLS = ["web_search"]
```

**Expected Behavior:**
1. Research agent called
2. Uses PDF retrieval to find specific section
3. Does NOT use web search (not needed)

**What Gets Validated:**
- ✅ PDF retrieval used
- ✅ Web search NOT used (efficient tool selection)

---

## 4. Web Search Fallback

**Tests:** System falls back to web search for out-of-scope queries

```python
# evaluation/scenarios/out_of_scope.py
QUERY = "What's the latest model from OpenAI?"

EXPECTED_TOOLS = ["web_search"]
```

**Expected Behavior:**
1. Research recognizes query is outside PDF scope
2. Falls back to web search
3. Returns current information

**What Gets Validated:**
- ✅ Web search used
- ✅ Answer contains up-to-date information

---

## Scenario Categories

| Category | Scenarios | What It Tests |
|----------|-----------|---------------|
| **Autonomous** | 1 scenario | Multi-step tool usage |
| **Clarification** | 2 scenarios | Ambiguity detection |
| **PDF-Only** | Multiple | Efficient tool selection |
| **Out-of-Scope** | Multiple | Graceful fallback |

---

## Running Specific Scenarios

```python
from evaluation.evaluator import Evaluator
from evaluation.scenarios import autonomous

evaluator = Evaluator()

# Run single scenario
result = evaluator.run_scenario(autonomous.MULTI_STEP_QUERY)

# Check results
print(f"Workflow: {'PASS' if result['workflow']['pass'] else 'FAIL'}")
print(f"Quality: {result['quality']}")
```

---

## See Also

- [Adding New Scenarios](./adding-scenarios.md) - Create custom tests
- [Metrics](./metrics.md) - How scenarios are evaluated
- [Evaluation Module](./README.md) - Back to main evaluation docs
