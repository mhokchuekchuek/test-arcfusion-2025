"""Agent state management for LangGraph workflow.

This module defines the state schema that flows through the entire
multi-agent graph execution, accumulating context and decisions from each agent.
"""

from operator import add
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """State passed between agents in the graph.

    This state flows through the entire graph execution, accumulating
    context and decisions from each agent.

    Attributes:
        messages: Full chat history with annotations for proper message merging
        session_id: Unique identifier for conversation session
        next_agent: Next agent to execute ("clarification" | "research" | "synthesis" | "END")
        iteration: Current graph iteration counter (prevent infinite loops)
        context: Research state populated by ReAct agent containing observations and results
        clarification_needed: Flag indicating if query needs clarification
        missing_context: List of information that is vague or missing from query
        final_answer: Final synthesized answer to user query
        confidence_score: Confidence score (0-1) in the answer quality
    """

    # Core conversation
    messages: Annotated[Sequence[BaseMessage], add]
    session_id: str

    # Routing state
    next_agent: str
    last_agent: Optional[str]  # Track which agent executed last (for clarification follow-up detection)
    iteration: int

    # Research state (populated by ReAct agent)
    context: Dict[str, Any]
    # Context structure:
    # {
    #   "observations": List[str],         # Tool execution results
    #   "pdf_results": List[Document],     # Raw PDF documents
    #   "web_results": List[Dict],         # Raw web search results
    #   "plan": str,                       # Research plan (optional)
    #   "tool_history": List[str],         # Tools used in sequence
    #   "final_output": str,               # Final output from research agent
    # }

    # Clarification state
    clarification_needed: bool
    missing_context: List[str]
    clarification_count: int  # Track consecutive clarification turns

    # Output
    final_answer: Optional[str]
    confidence_score: Optional[float]


def create_initial_state(
    messages: Sequence[BaseMessage],
    session_id: str,
) -> AgentState:
    """Create initial agent state for new graph execution.

    Args:
        messages: Initial messages (typically user query)
        session_id: Unique session identifier

    Returns:
        Initialized AgentState ready for graph execution
    """
    return AgentState(
        messages=messages,
        session_id=session_id,
        next_agent="orchestrator",
        last_agent=None,
        iteration=0,
        context={
            "observations": [],
            "pdf_results": [],
            "web_results": [],
            "tool_history": [],
        },
        clarification_needed=False,
        missing_context=[],
        clarification_count=0,
        final_answer=None,
        confidence_score=None,
    )
