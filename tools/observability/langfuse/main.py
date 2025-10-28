"""Langfuse client for LLM observability and prompt management."""

import os
from typing import Optional, Dict, Any
from langfuse import Langfuse, get_client
from tools.logger import get_logger
from tools.observability.base import BaseObservability

logger = get_logger(__name__)


class LangfuseClient(BaseObservability):
    """Client for Langfuse observability and prompt management."""

    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
    ):
        """Initialize Langfuse client.

        Args:
            public_key: Langfuse public key (default: from LANGFUSE_PUBLIC_KEY env)
            secret_key: Langfuse secret key (default: from LANGFUSE_SECRET_KEY env)
            host: Langfuse host URL (default: from LANGFUSE_HOST env)
        """
        self.public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self.host = host or os.getenv("LANGFUSE_HOST", "http://localhost:3000")

        if not self.public_key or not self.secret_key:
            raise ValueError(
                "Langfuse API keys not provided. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY"
            )

        # Initialize Langfuse client for prompt management
        self.client = Langfuse(
            public_key=self.public_key,
            secret_key=self.secret_key,
            host=self.host,
        )

        # Set environment variables for get_client() to use
        os.environ["LANGFUSE_PUBLIC_KEY"] = self.public_key
        os.environ["LANGFUSE_SECRET_KEY"] = self.secret_key
        os.environ["LANGFUSE_HOST"] = self.host

        logger.info(f"Langfuse client initialized with host: {self.host}")

    def get_prompt(
        self, name: str, version: Optional[int] = None, label: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a prompt from Langfuse.

        Args:
            name: Prompt name
            version: Specific version (optional)
            label: Label like "production" or "latest" (optional)

        Returns:
            Prompt object with compiled template and metadata
        """
        try:
            if version is not None:
                prompt = self.client.get_prompt(name, version=version)
            elif label:
                prompt = self.client.get_prompt(name, label=label)
            else:
                prompt = self.client.get_prompt(name)

            logger.debug(f"Retrieved prompt '{name}' from Langfuse")
            return prompt

        except Exception as e:
            logger.error(f"Failed to get prompt '{name}' from Langfuse: {e}")
            raise

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
            session_id: Session ID for grouping traces (also used as trace_id)
        """
        try:
            # Get the global langfuse client
            langfuse = get_client()

            # Create deterministic trace_id from session_id (32-char hex)
            trace_id = Langfuse.create_trace_id(seed=session_id) if session_id else None
            trace_context = {"trace_id": trace_id} if trace_id else None

            # Use context manager for generation tracing
            with langfuse.start_as_current_generation(
                name=name,
                model=model,
                input=input_data,
                metadata=metadata or {},
                trace_context=trace_context,
            ) as generation:
                # Set trace-level attributes (session_id for grouping)
                if session_id:
                    generation.update_trace(session_id=session_id)

                # Update with output
                generation.update(output=output)

            # Flush to send immediately
            langfuse.flush()

            logger.debug(f"Traced generation '{name}' to Langfuse (trace_id={trace_id}, session={session_id})")

        except Exception as e:
            logger.error(f"Failed to trace generation to Langfuse: {e}", exc_info=True)

    def flush(self):
        """Flush pending traces to Langfuse."""
        try:
            self.client.flush()
            logger.debug("Flushed traces to Langfuse")
        except Exception as e:
            logger.warning(f"Failed to flush traces to Langfuse: {e}")
