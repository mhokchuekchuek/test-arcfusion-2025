"""LiteLLM proxy client using OpenAI SDK.

The LiteLLM proxy exposes OpenAI-compatible endpoints.
We use the OpenAI SDK pointing to the proxy URL.

Reference: https://docs.litellm.ai/docs/proxy/quick_start
"""

from typing import Optional

from openai import OpenAI

from tools.llm.client.base import BaseLLM
from tools.logger.logger import get_logger

logger = get_logger(__name__)


class LLMClient(BaseLLM):
    """LiteLLM proxy client using OpenAI SDK.

    The proxy exposes OpenAI-compatible /chat/completions and /embeddings endpoints.
    We use the OpenAI SDK with base_url pointing to the proxy.

    The proxy provides:
    - Automatic caching via Redis
    - Multi-provider support (Claude, GPT-4, etc.)
    - Load balancing and fallbacks

    Reference: https://docs.litellm.ai/docs/proxy/quick_start
    """

    def __init__(
        self,
        proxy_url: str = "http://litellm-proxy:4000",
        completion_model: Optional[str] = None,
        embedding_model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        api_key: str = "dummy",  # Proxy doesn't need real key if auth disabled
    ):
        """Initialize LiteLLM proxy client.

        Args:
            proxy_url: LiteLLM proxy server URL
            completion_model: Model name from proxy config (e.g., "claude-3-5-sonnet")
            embedding_model: Embedding model name (e.g., "text-embedding-ada-002")
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            api_key: API key for proxy (use "dummy" if auth disabled)

        Note:
            Model names must match those in proxy's config.yaml model_list
        """
        self.completion_model = completion_model
        self.embedding_model = embedding_model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Create OpenAI client pointing to proxy
        self.client = OpenAI(
            base_url=proxy_url,
            api_key=api_key,  # Proxy may not need auth
        )

        logger.info(
            f"LiteLLM proxy client initialized (proxy={proxy_url}, "
            f"completion={completion_model}, embedding={embedding_model})"
        )

    def generate(
        self,
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        prompt_variables: Optional[dict] = None,
        **kwargs
    ) -> str:
        """Generate text completion via proxy.

        Supports two modes:
        1. Dotprompt mode: Use .prompt files with template variables (preferred)
        2. Traditional mode: Direct prompt strings for standard chat completion

        Args:
            prompt: User prompt (used in traditional mode)
            system_prompt: System instructions (used in traditional mode)
            prompt_variables: Variables for .prompt file templating (dotprompt mode)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text

        Raises:
            ValueError: If completion_model is not set or invalid arguments

        Examples:
            Dotprompt mode (uses .prompt file):
                >>> llm.generate(prompt_variables={"question": "What is RAG?", "context": "..."})

            Traditional mode:
                >>> llm.generate(prompt="Hello", system_prompt="You are helpful")
        """
        if not self.completion_model:
            raise ValueError("completion_model not set. Provide it in __init__")

        try:
            # Mode 1: Dotprompt with template variables
            if prompt_variables is not None:
                logger.debug(
                    f"Using dotprompt mode with variables: {list(prompt_variables.keys())}"
                )

                # For dotprompt models, messages content is ignored
                # The .prompt file template is used instead
                # Pass prompt_variables via extra_body per LiteLLM docs
                response = self.client.chat.completions.create(
                    model=self.completion_model,
                    messages=[{"role": "user", "content": "ignored"}],
                    extra_body={"prompt_variables": prompt_variables},
                    temperature=kwargs.get("temperature", self.temperature),
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    **kwargs,
                )

            # Mode 2: Traditional chat completion
            else:
                if prompt is None:
                    raise ValueError(
                        "Either 'prompt' or 'prompt_variables' must be provided"
                    )

                logger.debug("Using traditional chat completion mode")

                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = self.client.chat.completions.create(
                    model=self.completion_model,
                    messages=messages,
                    temperature=kwargs.get("temperature", self.temperature),
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    **kwargs,
                )

            content = response.choices[0].message.content

            # Check cache hit from response headers if available
            cache_hit = hasattr(response, '_cache_hit') and response._cache_hit

            logger.info(f"Generated (cache_hit={cache_hit}, length={len(content)})")
            return content

        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            raise

    def embed(self, texts: list[str], **kwargs) -> list[list[float]]:
        """Generate embeddings via proxy.

        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If embedding_model is not set
        """
        if not self.embedding_model:
            raise ValueError("embedding_model not set. Provide it in __init__")

        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
                **kwargs,
            )

            embeddings = [item.embedding for item in response.data]

            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Embedding failed: {e}", exc_info=True)
            raise
