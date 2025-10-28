"""Scenario 2: PDF-Only Queries → PDF Retrieval

Tests that queries about content in PDFs use only PDF retrieval,
without unnecessary web search.
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


# Scenario 2a: Zhang et al. paper query
ZHANG_PAPER_QUERY = Scenario(
    id="2a-pdf-zhang",
    name="PDF Query - Zhang et al.",
    query="Which prompt template gave the highest zero-shot accuracy on Spider in Zhang et al. (2024)?",
    expected_workflow=WorkflowExpectation(
        agents_should_include=["research"],
        agents_should_exclude=["clarification"],
        tools_should_include=["pdf_retrieval"],
        tools_should_exclude=["web_search"],
        clarification_expected=False,
    ),
    description="Specific paper query should use PDF retrieval only",
    expected_answer_criteria="""
Expected answer should:
1. Name the specific prompt template (e.g., "Create Table + Select 3", "DIN-SQL prompt", etc.)
2. Cite the exact accuracy percentage mentioned in the paper
3. Confirm it's from Zhang et al. (2024) paper
4. Reference the Spider benchmark/dataset
5. Be based ONLY on PDF content, not web search or made-up information
"""
)

# Scenario 2b: davinci-codex technical query
DAVINCI_CODEX_QUERY = Scenario(
    id="2b-pdf-davinci",
    name="PDF Query - davinci-codex",
    query="What execution accuracy does davinci-codex reach on Spider with the Create Table + Select 3 prompt?",
    expected_workflow=WorkflowExpectation(
        agents_should_include=["research"],
        agents_should_exclude=["clarification"],
        tools_should_include=["pdf_retrieval"],
        tools_should_exclude=["web_search"],
        clarification_expected=False,
    ),
    description="Technical query from papers should use PDF retrieval only",
    expected_answer_criteria="""
Expected answer should:
1. State the specific execution accuracy percentage for davinci-codex
2. Confirm it's for the Spider dataset
3. Confirm it's using "Create Table + Select 3" prompt
4. Cite the source paper where this information appears
5. Be factually accurate based on PDF content only
"""
)

# All PDF-only scenarios
SCENARIOS = [
    ZHANG_PAPER_QUERY,
    DAVINCI_CODEX_QUERY,
]
