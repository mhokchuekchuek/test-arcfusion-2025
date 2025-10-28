from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs,
    ) -> str:
        """Generate text completion.

        Args:
            prompt: User prompt
            system_prompt: System instructions (optional)
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def embed(self, texts: list[str], **kwargs) -> list[list[float]]:
        """Generate embeddings.

        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If embedding model is not configured
        """
        pass
