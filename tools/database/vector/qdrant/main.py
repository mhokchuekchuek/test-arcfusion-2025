"""Qdrant vector database client.

Implements vector storage and retrieval using Qdrant.

Reference: https://qdrant.tech/documentation/quick-start/
"""

import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from tools.database.vector.base import BaseVectorStore
from tools.logger.logger import get_logger

logger = get_logger(__name__)


class VectorStoreClient(BaseVectorStore):
    """Qdrant vector database client.

    Provides vector storage with metadata support. Qdrant is a high-performance
    vector similarity search engine with built-in filtering capabilities.

    Features:
    - Persistent storage with Docker volumes
    - Metadata filtering (session_id, source, page)
    - Distance metrics (cosine, euclidean, dot product)
    - Collection management

    Reference: https://qdrant.tech/documentation/
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "pdf_documents",
        vector_size: int = 1536,  # Default for OpenAI embeddings
        distance: str = "Cosine",
        create_collection: bool = True,
    ):
        """Initialize Qdrant client.

        Args:
            host: Qdrant server host (default: "localhost")
            port: Qdrant server port (default: 6333)
            collection_name: Name of the collection to use
            vector_size: Dimension of embedding vectors
            distance: Distance metric ("Cosine", "Euclid", "Dot")
            create_collection: Create collection if it doesn't exist

        Note:
            For Docker Compose, use host="qdrant" to connect to the service
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance

        # Initialize client
        self.client = QdrantClient(host=host, port=port)

        # Create collection if needed
        if create_collection:
            self._ensure_collection()

        logger.info(
            f"Qdrant client initialized (host={host}:{port}, "
            f"collection={collection_name}, vector_size={vector_size})"
        )

    def _ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                # Map distance string to Distance enum
                distance_map = {
                    "Cosine": Distance.COSINE,
                    "Euclid": Distance.EUCLID,
                    "Dot": Distance.DOT,
                }
                distance_metric = distance_map.get(self.distance, Distance.COSINE)

                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=distance_metric,
                    ),
                )
                logger.info(f"Created collection '{self.collection_name}'")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")

        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}", exc_info=True)
            raise

    def add(
        self,
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        """Add embeddings to Qdrant.

        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dicts (must match embeddings length if provided)
            ids: Optional list of IDs (auto-generated if not provided)

        Raises:
            ValueError: If embeddings and metadata lengths don't match
            Exception: If addition fails

        Example metadata:
            {
                "text": "The content of the chunk...",
                "source": "document.pdf",
                "page": 1,
                "session_id": "abc123",
            }
        """
        # Use empty dicts if no metadata provided
        if metadata is None:
            metadata = [{} for _ in range(len(embeddings))]

        if len(embeddings) != len(metadata):
            raise ValueError(
                f"Embeddings ({len(embeddings)}) and metadata ({len(metadata)}) "
                "lengths must match"
            )

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(embeddings))]

        if len(ids) != len(embeddings):
            raise ValueError(
                f"IDs ({len(ids)}) and embeddings ({len(embeddings)}) "
                "lengths must match"
            )

        try:
            # Create points
            points = [
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=meta,
                )
                for point_id, embedding, meta in zip(ids, embeddings, metadata)
            ]

            # Upload to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

            logger.info(f"Added {len(points)} points to collection '{self.collection_name}'")

        except Exception as e:
            logger.error(f"Failed to add embeddings: {e}", exc_info=True)
            raise

    def search(
        self,
        query_embedding: list[float],
        k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar embeddings in Qdrant.

        Args:
            query_embedding: Query vector
            k: Number of results to return
            filter: Optional metadata filter (e.g., {"session_id": "abc123", "page": 1})

        Returns:
            List of results, each containing:
            {
                "id": str,
                "score": float,
                "metadata": dict,
                "text": str (if available in metadata)
            }

        Raises:
            Exception: If search fails

        Example filter:
            {"session_id": "abc123", "source": "document.pdf"}
        """
        try:
            # Build Qdrant filter if provided
            qdrant_filter = None
            if filter:
                conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                    for key, value in filter.items()
                ]
                qdrant_filter = Filter(must=conditions)

            # Search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=k,
                query_filter=qdrant_filter,
            )

            # Format results
            results = []
            for hit in search_result:
                result = {
                    "id": str(hit.id),
                    "score": hit.score,
                    "metadata": hit.payload,
                }
                # Include text if available
                if "text" in hit.payload:
                    result["text"] = hit.payload["text"]

                results.append(result)

            logger.info(
                f"Search returned {len(results)} results "
                f"(k={k}, filter={filter is not None})"
            )
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            raise

    def delete(
        self,
        ids: list[str] | None = None,
        filter: dict[str, Any] | None = None,
    ) -> None:
        """Delete embeddings by ID or filter.

        Args:
            ids: List of embedding IDs to delete
            filter: Metadata filter for deletion (e.g., {"session_id": "abc123"})

        Raises:
            ValueError: If both ids and filter are provided, or neither is provided
            Exception: If deletion fails

        Examples:
            # Delete by IDs
            store.delete(ids=["id1", "id2", "id3"])

            # Delete by filter
            store.delete(filter={"session_id": "abc123"})
        """
        # Validate input
        if ids is not None and filter is not None:
            raise ValueError("Cannot provide both 'ids' and 'filter'. Choose one.")
        if ids is None and filter is None:
            raise ValueError("Must provide either 'ids' or 'filter'.")

        try:
            if ids is not None:
                # Delete by IDs
                if not ids:
                    logger.warning("Empty IDs list provided for deletion")
                    return

                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=ids,
                )
                logger.info(f"Deleted {len(ids)} points by IDs")

            else:
                # Delete by filter
                conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                    for key, value in filter.items()
                ]
                qdrant_filter = Filter(must=conditions)

                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=qdrant_filter,
                )
                logger.info(f"Deleted points matching filter: {filter}")

        except Exception as e:
            logger.error(f"Deletion failed: {e}", exc_info=True)
            raise

    def count(self, filter: dict[str, Any] | None = None) -> int:
        """Count points in collection.

        This is a Qdrant-specific convenience method not in BaseVectorStore.

        Args:
            filter: Optional metadata filter

        Returns:
            Number of points

        Raises:
            Exception: If count fails
        """
        try:
            # Build Qdrant filter if provided
            qdrant_filter = None
            if filter:
                conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                    for key, value in filter.items()
                ]
                qdrant_filter = Filter(must=conditions)

            # Count
            result = self.client.count(
                collection_name=self.collection_name,
                count_filter=qdrant_filter,
                exact=True,
            )

            return result.count

        except Exception as e:
            logger.error(f"Count failed: {e}", exc_info=True)
            raise
