"""Scenario 3: Autonomous Multi-Step Execution

Tests that the system can autonomously decompose a multi-part query
and execute multiple tools in sequence (PDF retrieval + web search).
"""

from dataclasses import dataclass
from typing import List


@dataclass
class WorkflowExpectation:
    """Expected workflow behavior."""

    agents_should_include: List[str]
    agents_should_exclude: List[str]
    tools_should_include: List[str]
    tools_should_exclude: List[str]
    clarification_expected: bool = False


@dataclass
class Scenario:
    """Test scenario definition."""

    id: str
    name: str
    query: str
    expected_workflow: WorkflowExpectation
    description: str
    expected_answer_criteria: str = ""  # What a good answer should contain


# Scenario 3: Multi-step autonomous execution
MULTI_STEP_QUERY = Scenario(
    id="3-autonomous-multistep",
    name="Autonomous Multi-Step",
    query="What is the state-of-the-art text-to-sql approach? And search on the web to tell me more about the authors who contributed to the approach",
    expected_workflow=WorkflowExpectation(
        agents_should_include=["research"],
        agents_should_exclude=["clarification"],
        tools_should_include=["pdf_retrieval", "web_search"],  # BOTH required
        tools_should_exclude=[],
        clarification_expected=False,
    ),
    description="Multi-part query requiring both PDF and web search autonomously",
    expected_answer_criteria="""
Expected answer should:
1. Identify a specific text-to-SQL approach/model (e.g., DIN-SQL, RESDSQL, C3, etc.)
2. Mention why it's state-of-the-art (accuracy metrics, benchmarks)
3. Provide information about the authors (names, affiliations, contributions)
4. Synthesize information from both PDF papers and web sources
5. Be coherent and well-structured
"""
)

# All autonomous scenarios
SCENARIOS = [
    MULTI_STEP_QUERY,
]
