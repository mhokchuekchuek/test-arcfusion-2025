"""Base agent classes for the multi-agent system."""

from abc import ABC, abstractmethod
from src.graph.state import AgentState


class BaseAgent(ABC):
    """Abstract base class for all agents in the system.

    Each agent implements execute() which receives state and returns updated state.
    """

    def __init__(self, name: str):
        """Initialize base agent.

        Args:
            name: Human-readable agent name for logging
        """
        self.name = name

    @abstractmethod
    def execute(self, state: AgentState) -> AgentState:
        """Execute agent logic and update state.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        pass
