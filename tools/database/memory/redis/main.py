"""Redis-backed memory client for session storage."""

import json
from datetime import datetime
from typing import Any

import redis

from tools.database.memory.base import BaseMemory
from tools.logger import get_logger

logger = get_logger(__name__)


class MemoryClient(BaseMemory):
    """Redis client for storing conversation history.

    Stores session-based messages in Redis with automatic TTL expiration.
    Each session is a Redis list containing JSON-encoded messages.

    Example:
        >>> client = MemoryClient(host="localhost", port=6379)
        >>> client.add(session_id="s1", role="user", content="Hello")
        >>> history = client.get(session_id="s1")
        >>> client.clear(session_id="s1")
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str | None = None,
        db: int = 0,
        session_ttl: int = 3600,
        key_prefix: str = "session:",
    ):
        """Initialize Redis memory client.

        Args:
            host: Redis server host
            port: Redis server port
            password: Redis password (optional)
            db: Redis database number
            session_ttl: Session TTL in seconds (default: 1 hour)
            key_prefix: Prefix for Redis keys

        Raises:
            redis.ConnectionError: If cannot connect to Redis
        """
        self.host = host
        self.port = port
        self.session_ttl = session_ttl
        self.key_prefix = key_prefix

        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db,
                decode_responses=True,
            )
            self.client.ping()
            logger.info(
                f"Redis MemoryClient initialized (host={host}:{port}, "
                f"db={db}, ttl={session_ttl}s)"
            )
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
            raise

    def _key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"{self.key_prefix}{session_id}"

    def add(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        **kwargs
    ) -> None:
        """Add a message to session history.

        Args:
            session_id: Session identifier
            role: Message role ("user" or "assistant")
            content: Message content
            metadata: Additional metadata (optional)
            **kwargs: Extra parameters (ignored)

        Raises:
            ValueError: If role is invalid
            redis.RedisError: If Redis operation fails
        """
        if role not in ["user", "assistant"]:
            raise ValueError(f"Invalid role: {role}")

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if metadata:
            message["metadata"] = metadata

        key = self._key(session_id)
        try:
            self.client.rpush(key, json.dumps(message))
            self.client.expire(key, self.session_ttl)
            logger.debug(f"Added message to session '{session_id}' (role={role})")
        except redis.RedisError as e:
            logger.error(f"Failed to add message: {e}", exc_info=True)
            raise

    def get(
        self,
        session_id: str,
        limit: int | None = None,
        **kwargs
    ) -> list[dict[str, Any]]:
        """Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Max messages to return (most recent)
            **kwargs: Extra parameters (ignored)

        Returns:
            List of messages in chronological order

        Raises:
            redis.RedisError: If Redis operation fails
        """
        key = self._key(session_id)
        try:
            messages_raw = self.client.lrange(key, 0, -1)
            messages = [json.loads(msg) for msg in messages_raw]

            if limit is not None and limit > 0:
                messages = messages[-limit:]

            logger.debug(f"Retrieved {len(messages)} messages from '{session_id}'")
            return messages

        except redis.RedisError as e:
            logger.error(f"Failed to get history: {e}", exc_info=True)
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse messages: {e}", exc_info=True)
            return []

    def clear(self, session_id: str, **kwargs) -> None:
        """Clear all messages in a session.

        Args:
            session_id: Session identifier
            **kwargs: Extra parameters (ignored)

        Raises:
            redis.RedisError: If Redis operation fails
        """
        key = self._key(session_id)
        try:
            deleted = self.client.delete(key)
            if deleted:
                logger.info(f"Cleared session '{session_id}'")
            else:
                logger.warning(f"Session '{session_id}' not found")
        except redis.RedisError as e:
            logger.error(f"Failed to clear session: {e}", exc_info=True)
            raise

    def exists(self, session_id: str, **kwargs) -> bool:
        """Check if a session exists.

        Args:
            session_id: Session identifier
            **kwargs: Extra parameters (ignored)

        Returns:
            True if session exists

        Raises:
            redis.RedisError: If Redis operation fails
        """
        key = self._key(session_id)
        try:
            return self.client.exists(key) > 0
        except redis.RedisError as e:
            logger.error(f"Failed to check existence: {e}", exc_info=True)
            raise

    def count(self, session_id: str) -> int:
        """Get number of messages in a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of messages (0 if session doesn't exist)

        Raises:
            redis.RedisError: If operation fails
        """
        key = self._key(session_id)
        try:
            return self.client.llen(key)
        except redis.RedisError as e:
            logger.error(f"Failed to get count: {e}", exc_info=True)
            raise
