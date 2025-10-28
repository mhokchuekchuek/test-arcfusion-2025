"""Base abstraction for observability tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseObservability(ABC):
    """Abstract base class for observability tool implementations."""

    @abstractmethod
    def get_prompt(
        self, name: str, version: Optional[int] = None, label: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a prompt template.

        Args:
            name: Prompt name
            version: Specific version (optional)
            label: Label like "production" or "latest" (optional)

        Returns:
            Prompt object with compiled template and metadata
        """
        pass

    @abstractmethod
    def trace_generation(
        self,
        name: str,
        input_data: Dict[str, Any],
        output: str,
        model: str,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ):
        """Trace an LLM generation.

        Args:
            name: Name of the generation
            input_data: Input data (prompt variables, messages, etc.)
            output: Generated output
            model: Model name
            metadata: Additional metadata
            session_id: Session ID for grouping traces
        """
        pass

    @abstractmethod
    def flush(self):
        """Flush pending traces to observability backend."""
        pass
