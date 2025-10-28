"""Document retriever for RAG pipeline."""

from typing import Any

from tools.database.vector.base import BaseVectorStore
from tools.llm.client.base import BaseLLM
from tools.logger import get_logger

logger = get_logger(__name__)


class DocumentRetriever:
    """Retrieve relevant documents from vector store for RAG.

    Generates query embeddings and searches vector database for
    semantically similar document chunks.

    Example:
        >>> retriever = DocumentRetriever(llm_client, vector_store)
        >>> results = retriever.retrieve("What is RAG?", top_k=5)
        >>> for doc in results:
        ...     print(f"{doc['source']} (score: {doc['score']})")
    """

    def __init__(
        self,
        llm_client: BaseLLM,
        vector_store: BaseVectorStore,
    ):
        """Initialize document retriever.

        Args:
            llm_client: LLM client for generating embeddings
            vector_store: Vector database for similarity search
        """
        self.llm_client = llm_client
        self.vector_store = vector_store
        logger.info("DocumentRetriever initialized")

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant documents for a query.

        Args:
            query: User query string
            top_k: Number of documents to retrieve
            filter: Optional metadata filter (e.g., {"source": "doc.pdf"})

        Returns:
            List of documents with metadata:
            [
                {
                    "text": str,
                    "source": str,
                    "page": int,
                    "score": float,
                    "metadata": dict
                }
            ]

        Raises:
            ValueError: If query is empty
            Exception: If retrieval fails

        Example:
            >>> results = retriever.retrieve("What is RAG?", top_k=3)
            >>> print(f"Found {len(results)} documents")

        Note:
            TODO: Add query preprocessing for long inputs (>512 tokens)
            This will be handled by agents in future tasks (Task 2.2+)
        """
        # Validate input
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        logger.info(f"Retrieving documents for query: '{query[:50]}...' (top_k={top_k})")

        try:
            # Step 1: Generate query embedding
            logger.debug("Generating query embedding")
            query_embeddings = self.llm_client.embed([query])
            query_embedding = query_embeddings[0]

            logger.debug(f"Query embedding generated (dim={len(query_embedding)})")

            # Step 2: Search vector store
            logger.debug(f"Searching vector store (top_k={top_k}, filter={filter})")
            search_results = self.vector_store.search(
                query_embedding=query_embedding,
                k=top_k,
                filter=filter,
            )

            # Step 3: Format results
            documents = []
            for result in search_results:
                doc = {
                    "text": result.get("text", ""),
                    "source": result.get("metadata", {}).get("source", "unknown"),
                    "page": result.get("metadata", {}).get("page", 0),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {}),
                }
                documents.append(doc)

            logger.info(
                f"Retrieved {len(documents)} documents "
                f"(scores: {[f'{d['score']:.3f}' for d in documents[:3]]}...)"
            )

            return documents

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise

        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}", exc_info=True)
            raise
