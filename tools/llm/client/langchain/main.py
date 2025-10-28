"""LangChain ChatOpenAI client wrapper for LiteLLM proxy.

This client provides ChatOpenAI instances configured to use the LiteLLM proxy,
enabling LangChain/LangGraph agents to work with any model via the proxy.
"""

from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI

from tools.logger.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """LangChain ChatOpenAI wrapper for LiteLLM proxy.

    Provides ChatOpenAI instances that work with LangChain agents and LangGraph.
    All requests go through the LiteLLM proxy for unified model access.

    Example:
        >>> from tools.llm.client.selector import LLMClientSelector
        >>> client = LLMClientSelector.create(
        ...     provider="langchain",
        ...     proxy_url="http://litellm-proxy:4000",
        ...     api_key="sk-1234"
        ... )
        >>>
        >>> # Standard mode - for agents
        >>> chat = client.get_client(model="gpt-4", temperature=0.7)
        >>> from langchain.agents import create_agent
        >>> agent = create_agent(model=chat, tools=[...])
        >>>
        >>> # Dotprompt mode - for custom templates
        >>> chat = client.get_client(
        ...     model="rag-dotprompt",
        ...     extra_body={"prompt_variables": {"query": "What is RAG?"}}
        ... )
        >>> response = chat.invoke([])
    """

    def __init__(
        self,
        proxy_url: str = "http://litellm-proxy:4000",
        api_key: str = "sk-1234",
        default_model: str = "gpt-4",
        default_temperature: float = 0.7,
        default_max_tokens: int = 2000,
        **kwargs
    ):
        """Initialize LangChain ChatOpenAI client wrapper.

        Args:
            proxy_url: LiteLLM proxy URL
            api_key: API key for proxy (use dummy if auth disabled)
            default_model: Default model name from proxy config
            default_temperature: Default sampling temperature (0-1)
            default_max_tokens: Default maximum tokens in response
            **kwargs: Additional default parameters for ChatOpenAI
        """
        self.proxy_url = proxy_url
        self.api_key = api_key
        self.default_model = default_model
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        self.default_kwargs = kwargs

        logger.info(
            f"ChatOpenAI client initialized (proxy={proxy_url}, model={default_model})"
        )

    def get_client(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        extra_body: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ChatOpenAI:
        """Get ChatOpenAI instance configured for LiteLLM proxy.

        Supports two modes:
        1. Standard mode: For LangChain agents, chains, direct chat
        2. Dotprompt mode: Pass extra_body={"prompt_variables": {...}} for templates

        Args:
            model: Model name (defaults to default_model)
            temperature: Sampling temperature (defaults to default_temperature)
            max_tokens: Maximum tokens (defaults to default_max_tokens)
            extra_body: Extra body for LiteLLM (e.g., {"prompt_variables": {...}})
            **kwargs: Additional ChatOpenAI parameters

        Returns:
            Configured ChatOpenAI instance

        Examples:
            Standard mode (for agents):
            >>> chat = client.get_client(model="gpt-4", temperature=0.5)
            >>> from langchain.agents import create_agent
            >>> agent = create_agent(model=chat, tools=[...])

            Dotprompt mode (for custom templates):
            >>> chat = client.get_client(
            ...     model="rag-dotprompt",
            ...     extra_body={"prompt_variables": {"query": "What is RAG?"}}
            ... )
            >>> response = chat.invoke([])
        """
        chat_kwargs = {
            "model": model or self.default_model,
            "openai_api_base": self.proxy_url,
            "openai_api_key": self.api_key,
            "temperature": temperature if temperature is not None else self.default_temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.default_max_tokens,
            **self.default_kwargs,
            **kwargs,
        }

        # Add extra_body if provided (for dotprompt mode)
        if extra_body is not None:
            chat_kwargs["extra_body"] = extra_body
            logger.debug(
                f"Creating ChatOpenAI with extra_body "
                f"(model={chat_kwargs['model']}, keys={list(extra_body.keys())})"
            )
        else:
            logger.debug(f"Creating ChatOpenAI (model={chat_kwargs['model']})")

        return ChatOpenAI(**chat_kwargs)
