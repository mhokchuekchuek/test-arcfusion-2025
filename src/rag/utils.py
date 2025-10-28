"""Utility functions for RAG pipeline."""

from typing import Any


def format_documents(documents: list[dict[str, Any]]) -> str:
    """Format retrieved documents for prompt context.

    Args:
        documents: List of retrieved documents with text, source, page, score

    Returns:
        Formatted context string with numbered sources

    Example:
        >>> docs = [
        ...     {"text": "RAG is...", "source": "paper.pdf", "page": 3, "score": 0.89},
        ...     {"text": "It combines...", "source": "guide.pdf", "page": 1, "score": 0.85}
        ... ]
        >>> context = format_documents(docs)
        >>> print(context)
        [1] paper.pdf (page 3, score: 0.89)
        RAG is...

        [2] guide.pdf (page 1, score: 0.85)
        It combines...
    """
    if not documents:
        return ""

    formatted = []
    for i, doc in enumerate(documents, 1):
        source = doc.get("source", "unknown")
        page = doc.get("page", 0)
        text = doc.get("text", "")
        score = doc.get("score", 0.0)

        # Format: [1] source.pdf (page 3, score: 0.89)
        # Text content...
        formatted.append(
            f"[{i}] {source} (page {page}, score: {score:.2f})\n{text}"
        )

    return "\n\n".join(formatted)


def format_history(messages: list[dict[str, Any]]) -> str:
    """Format conversation history for prompt.

    Args:
        messages: List of messages with role and content

    Returns:
        Formatted history string with role prefixes

    Example:
        >>> messages = [
        ...     {"role": "user", "content": "What is RAG?"},
        ...     {"role": "assistant", "content": "RAG is..."}
        ... ]
        >>> history = format_history(messages)
        >>> print(history)
        User: What is RAG?

        Assistant: RAG is...
    """
    if not messages:
        return ""

    formatted = []
    for msg in messages:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")

    return "\n\n".join(formatted)
