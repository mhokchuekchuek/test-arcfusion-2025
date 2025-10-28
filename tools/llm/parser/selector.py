"""Parser selector for choosing provider implementation."""

from tools.base.selector import BaseToolSelector


class ParserSelector(BaseToolSelector):
    """Selector for document parser providers.

    Available providers:
        - docling: Docling parser (PDF, Word, etc.)

    Example:
        >>> from tools.llm.parser.selector import ParserSelector
        >>> parser = ParserSelector.create(
        ...     provider="docling"
        ... )
    """

    _PROVIDERS = {
        "docling": "tools.llm.parser.docling.main.PDFParser",
    }
