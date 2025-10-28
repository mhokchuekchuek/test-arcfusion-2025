"""Text chunker selector for choosing provider implementation."""

from tools.base.selector import BaseToolSelector


class TextChunkerSelector(BaseToolSelector):
    """Selector for text chunker providers.

    Available providers:
        - recursive: Recursive character text splitter

    Example:
        >>> from tools.llm.chunking.selector import TextChunkerSelector
        >>> chunker = TextChunkerSelector.create(
        ...     provider="recursive",
        ...     chunk_size=1000,
        ...     chunk_overlap=200
        ... )
    """

    _PROVIDERS = {
        "recursive": "tools.llm.chunking.recursive.main.TextChunker",
    }
