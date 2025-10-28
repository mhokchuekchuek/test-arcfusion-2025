"""Scenario 1: Ambiguous Questions → Clarification Agent

Tests that vague or ambiguous queries trigger the clarification agent
instead of attempting to answer directly.
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


# Scenario 1a: Vague Quantifier
AMBIGUOUS_QUANTIFIER = Scenario(
    id="1a-ambiguous-quantifier",
    name="Ambiguous Quantifier",
    query="How many examples are enough for good accuracy?",
    expected_workflow=WorkflowExpectation(
        agents_should_include=["clarification"],
        agents_should_exclude=["research"],
        tools_should_include=[],
        tools_should_exclude=["pdf_retrieval", "web_search"],
        clarification_expected=True,
    ),
    description="Vague quantifiers ('enough', 'good') should trigger clarification",
    expected_answer_criteria="""
Expected response should:
1. Ask specific clarifying questions about the vague terms ('enough', 'good')
2. Ask what task/domain this is for (e.g., "What task are you training for?")
3. Ask what 'good accuracy' means (e.g., "What accuracy threshold do you consider good?")
4. NOT attempt to answer without clarification
5. NOT make assumptions about the context
"""
)

# Scenario 1b: Undefined Pronoun
UNDEFINED_PRONOUN = Scenario(
    id="1b-undefined-pronoun",
    name="Undefined Pronoun",
    query="Tell me more about it",
    expected_workflow=WorkflowExpectation(
        agents_should_include=["clarification"],
        agents_should_exclude=["research"],
        tools_should_include=[],
        tools_should_exclude=["pdf_retrieval", "web_search"],
        clarification_expected=True,
    ),
    description="Undefined pronoun ('it') without context should trigger clarification",
    expected_answer_criteria="""
Expected response should:
1. Ask what 'it' refers to (e.g., "What would you like to know more about?")
2. Ask for context or clarification about the topic
3. NOT attempt to guess what 'it' means
4. NOT make assumptions about the subject
5. Be polite and helpful in asking for clarification
"""
)

# All clarification scenarios
SCENARIOS = [
    AMBIGUOUS_QUANTIFIER,
    UNDEFINED_PRONOUN,
]
