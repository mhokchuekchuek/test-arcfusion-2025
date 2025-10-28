from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from tools.llm.chunking.base import BaseChunker
from tools.logger import get_logger

logger = get_logger(__name__)


class TextChunker(BaseChunker):
    """Text chunker using LangChain's RecursiveCharacterTextSplitter.

    Uses LangChain's implementation which recursively splits text using
    a hierarchy of separators to preserve semantic boundaries while
    maintaining desired chunk sizes.

    Splits on: paragraphs → lines → sentences → words → characters
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: list[str] | None = None,
        **kwargs
    ):
        """Initialize recursive text chunker.

        Args:
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: Number of characters to overlap between chunks
            separators: Custom list of separators (default: LangChain defaults)
            **kwargs: Additional configuration for RecursiveCharacterTextSplitter
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        # Initialize LangChain's splitter
        splitter_kwargs = {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }

        if separators is not None:
            splitter_kwargs["separators"] = separators

        splitter_kwargs.update(kwargs)

        self.splitter = RecursiveCharacterTextSplitter(**splitter_kwargs)

        logger.info(
            f"Initialized TextChunker with LangChain "
            f"(size={chunk_size}, overlap={chunk_overlap})"
        )

    def split(
        self,
        text: str,
        metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Split text into chunks using LangChain's splitter.

        Args:
            text: Text to split
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of dicts, each containing:
            {
                "text": str,
                "metadata": dict (includes chunk_index and chunk_size)
            }

        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        metadata = metadata or {}

        try:
            # Use LangChain's splitter
            chunks = self.splitter.split_text(text)

            # Build result with metadata
            result = []
            for idx, chunk_text in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = idx
                chunk_metadata["chunk_size"] = len(chunk_text)

                result.append({
                    "text": chunk_text.strip(),
                    "metadata": chunk_metadata,
                })

            logger.debug(f"Split text into {len(result)} chunks")

            return result

        except Exception as e:
            logger.error(f"Error splitting text: {str(e)}")
            raise
