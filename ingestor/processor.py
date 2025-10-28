"""PDF Ingestion Processor for RAG pipeline.

Automatically discovers and processes PDF files from a directory.
Pipeline: PDF → Parse → Chunk → Embed → Store
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from ingestor.config import load_ingestion_config
from tools.database.vector.selector import VectorStoreSelector
from tools.llm.chunking.selector import TextChunkerSelector
from tools.llm.client.selector import LLMClientSelector
from tools.llm.parser.selector import ParserSelector
from tools.logger import get_logger

logger = get_logger(__name__)


class IngestionProcessor:
    """PDF ingestion processor that auto-discovers files in a directory."""

    def __init__(self):
        """Initialize ingestion processor from config.

        All settings are loaded from configs/ingestor/ingestion.yaml
        (separate config for local ingestion use case)
        Override settings via environment variables if needed (e.g., INGESTION__DIRECTORY=/path)

        Example:
            >>> # Everything from config - super simple!
            >>> processor = IngestionProcessor()
            >>> results = processor.process()
        """
        # Load config
        config = load_ingestion_config()
        self.config = config.ingestion

        logger.info("Initializing IngestionProcessor from config")

        # Create LLM client from config
        logger.debug(f"Creating LLM client: provider={self.config.llm.provider}")
        self.llm_client = LLMClientSelector.create(
            provider=self.config.llm.provider,
            proxy_url=self.config.llm.proxy_url,
            api_key=self.config.llm.api_key,
            embedding_model=self.config.llm.embedding_model,
        )

        # Create vector store from config
        logger.debug(f"Creating vector store: provider={self.config.vectordb.provider}")
        self.vector_store = VectorStoreSelector.create(
            provider=self.config.vectordb.provider,
            host=self.config.vectordb.host,
            port=self.config.vectordb.port,
            collection_name=self.config.vectordb.collection_name,
            vector_size=self.config.vectordb.vector_size,
            create_collection=self.config.vectordb.create_collection,
        )

        # Set processing parameters from config
        self.directory = Path(self.config.directory)
        self.file_type = self.config.file_type.lower().replace(".", "")
        self.chunk_size = self.config.chunk_size
        self.chunk_overlap = self.config.chunk_overlap
        self.batch_size = self.config.batch_size

        logger.info(
            f"IngestionProcessor ready: directory={self.directory}, "
            f"file_type=.{self.file_type}, chunk_size={self.chunk_size}, overlap={self.chunk_overlap}"
        )

    def process(self, metadata: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Discover and process all files in the configured directory.

        Automatically finds all files ending with the configured file_type
        and processes them through the ingestion pipeline.

        Args:
            metadata: Optional metadata to attach to all chunks from all files

        Returns:
            List of ingestion results for each file

        Example:
            >>> results = processor.process()
            >>> for result in results:
            ...     if result['success']:
            ...         print(f"Success: {result['filename']}: {result['num_chunks']} chunks")
            ...     else:
            ...         print(f"Failed: {result['filename']}: {result['error']}")
        """
        if not self.directory.exists():
            logger.error(f"Directory not found: {self.directory}")
            raise FileNotFoundError(f"Directory not found: {self.directory}")

        if not self.directory.is_dir():
            logger.error(f"Path is not a directory: {self.directory}")
            raise ValueError(f"Path is not a directory: {self.directory}")

        # Find all files with the specified extension
        pattern = f"*.{self.file_type}"
        files = list(self.directory.glob(pattern))

        if not files:
            logger.warning(f"No .{self.file_type} files found in {self.directory}")
            return []

        logger.info(f"Found {len(files)} .{self.file_type} files to process in {self.directory}")

        # Process each file
        results = []
        for idx, file_path in enumerate(files, 1):
            logger.info(f"Processing file {idx}/{len(files)}: {file_path.name}")

            result = self._process_file(file_path, metadata=metadata)
            results.append(result)

        # Summary
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful

        logger.info(
            f"Ingestion complete: {successful} succeeded, {failed} failed "
            f"(total: {len(results)} files)"
        )

        return results

    def _process_file(
        self,
        file_path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Process a single file through the ingestion pipeline.

        Args:
            file_path: Path to file
            metadata: Optional metadata to attach to all chunks

        Returns:
            Dictionary with ingestion statistics
        """
        try:
            # Step 1: Parse PDF
            logger.debug(f"[1/4] Parsing {file_path.name}")

            pdf_parser = ParserSelector.create(
                provider=self.config.parser.provider,
            )

            parsed_data = pdf_parser.parse(str(file_path))
            full_text = parsed_data["text"]
            pdf_metadata = parsed_data["metadata"]
            num_pages = pdf_metadata.get("num_pages", 0)

            logger.debug(f"Parsed {num_pages} pages")

            # Step 2: Chunk text
            logger.debug(f"[2/4] Chunking text")

            text_chunker = TextChunkerSelector.create(
                provider=self.config.chunker.provider,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )

            # Prepare metadata for chunks
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "source": file_path.name,
                "filepath": str(file_path.absolute()),
                "num_pages": num_pages,
                "ingested_at": datetime.utcnow().isoformat(),
            })

            chunks = text_chunker.split(full_text, metadata=chunk_metadata)
            num_chunks = len(chunks)

            logger.debug(f"Created {num_chunks} chunks")

            # Step 3: Generate embeddings
            logger.debug(f"[3/4] Generating embeddings")

            chunk_texts = [chunk["text"] for chunk in chunks]
            all_embeddings = []

            for i in range(0, len(chunk_texts), self.batch_size):
                batch = chunk_texts[i:i + self.batch_size]
                batch_embeddings = self.llm_client.embed(batch)
                
                all_embeddings.extend(batch_embeddings)

            logger.debug(f"Generated {len(all_embeddings)} embeddings")

            # Step 4: Store in vector database
            logger.debug(f"[4/4] Storing vectors")

            # Prepare metadata with text content for storage
            vector_metadata = []
            for chunk in chunks:
                meta = chunk["metadata"].copy()
                meta["text"] = chunk["text"]  # Include text for retrieval
                vector_metadata.append(meta)

            self.vector_store.add(
                embeddings=all_embeddings,
                metadata=vector_metadata,
            )

            logger.info(
                f"Successfully ingested {file_path.name}: "
                f"{num_pages} pages -> {num_chunks} chunks -> {len(all_embeddings)} vectors"
            )

            return {
                "filename": file_path.name,
                "filepath": str(file_path.absolute()),
                "num_pages": num_pages,
                "num_chunks": num_chunks,
                "num_embeddings": len(all_embeddings),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Failed to ingest {file_path.name}: {str(e)}")
            return {
                "filename": file_path.name,
                "filepath": str(file_path.absolute()),
                "success": False,
                "error": str(e),
            }
