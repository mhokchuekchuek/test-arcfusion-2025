"""Scenario 4: Out-of-Scope Queries → Web Search

Tests that time-sensitive or out-of-scope queries (not in PDFs)
correctly route to web search instead of PDF retrieval.
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


# Scenario 4: Out-of-scope/current events query
CURRENT_EVENTS_QUERY = Scenario(
    id="4-out-of-scope",
    name="Out-of-Scope Query",
    query="What did OpenAI release this month?",
    expected_workflow=WorkflowExpectation(
        agents_should_include=["research"],
        agents_should_exclude=["clarification"],
        tools_should_include=["web_search"],
        tools_should_exclude=["pdf_retrieval"],
        clarification_expected=False,
    ),
    description="Time-sensitive query should use web search only",
    expected_answer_criteria="""
Expected answer should:
1. Provide current/recent information about OpenAI releases
2. Be time-appropriate (mention recent dates/months)
3. Include specific product/model names or updates
4. Cite web sources (not PDF papers)
5. Acknowledge if information is too recent to have comprehensive details
"""
)

# All out-of-scope scenarios
SCENARIOS = [
    CURRENT_EVENTS_QUERY,
]
