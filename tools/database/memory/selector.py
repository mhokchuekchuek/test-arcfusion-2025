"""Memory client selector for choosing provider implementation."""

from tools.base.selector import BaseToolSelector


class MemoryClientSelector(BaseToolSelector):
    """Selector for memory client providers.

    Available providers:
        - redis: Redis memory store

    Example:
        >>> from tools.database.memory.selector import MemoryClientSelector
        >>> memory = MemoryClientSelector.create(
        ...     provider="redis",
        ...     host="redis",
        ...     port=6379,
        ...     db=0
        ... )
    """

    _PROVIDERS = {
        "redis": "tools.database.memory.redis.main.MemoryClient",
    }
