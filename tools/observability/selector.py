"""Observability tool selector for choosing provider implementation."""

from tools.base.selector import BaseToolSelector


class ObservabilitySelector(BaseToolSelector):
    """Selector for observability tool providers.

    Available providers:
        - langfuse: Langfuse client for LLM tracing and prompt management

    Example:
        >>> from tools.observability.selector import ObservabilitySelector
        >>>
        >>> # Create Langfuse client
        >>> client = ObservabilitySelector.create(
        ...     provider="langfuse",
        ...     public_key="pk-...",
        ...     secret_key="sk-...",
        ...     host="http://localhost:3000"
        ... )
        >>> prompt = client.get_prompt("orchestrator_intent")
    """

    _PROVIDERS = {
        "langfuse": "tools.observability.langfuse.main.LangfuseClient",
    }
