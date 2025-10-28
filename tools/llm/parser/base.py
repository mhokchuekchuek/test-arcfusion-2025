from abc import ABC, abstractmethod
from typing import Any


class BasePDFParser(ABC):
    """Abstract base class for PDF parsers."""

    @abstractmethod
    def parse(self, pdf_path: str, **kwargs) -> dict[str, Any]:
        """Parse PDF file and extract content with metadata.

        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parser-specific parameters

        Returns:
            Dictionary containing:
                - text: Extracted text content
                - metadata: Dictionary with file metadata (e.g., pages, title, author)
                - pages: Optional list of page-wise content

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is invalid or corrupted
        """
        pass

    @abstractmethod
    def parse_pages(self, pdf_path: str, **kwargs) -> list[dict[str, Any]]:
        """Parse PDF and return content organized by pages.

        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parser-specific parameters

        Returns:
            List of dictionaries, one per page, each containing:
                - page_number: Page index (0-based)
                - text: Text content of the page
                - metadata: Page-specific metadata

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is invalid or corrupted
        """
        pass
