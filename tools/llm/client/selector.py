"""LLM client selector for choosing provider implementation."""

from tools.base.selector import BaseToolSelector


class LLMClientSelector(BaseToolSelector):
    """Selector for LLM client providers.

    Available providers:
        - litellm: LiteLLM proxy client (OpenAI SDK-based)
        - langchain: LangChain ChatOpenAI wrapper for LiteLLM proxy

    Example:
        >>> from tools.llm.client.selector import LLMClientSelector
        >>>
        >>> # LiteLLM (for direct API use, RAG)
        >>> client = LLMClientSelector.create(
        ...     provider="litellm",
        ...     proxy_url="http://litellm-proxy:4000",
        ...     completion_model="gpt-4"
        ... )
        >>> response = client.generate("Hello")
        >>>
        >>> # LangChain (for agents, chains)
        >>> client = LLMClientSelector.create(
        ...     provider="langchain",
        ...     proxy_url="http://litellm-proxy:4000"
        ... )
        >>> chat = client.get_client(model="gpt-4")
    """

    _PROVIDERS = {
        "litellm": "tools.llm.client.litellm.main.LLMClient",
        "langchain": "tools.llm.client.langchain.main.LLMClient",
    }
