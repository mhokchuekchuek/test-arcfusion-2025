#!/usr/bin/env python3
"""PDF Ingestion Script

Automatically ingests PDF files from configured directory into Qdrant.
Skips ingestion if data already exists (smart checking).

Usage:
    python scripts/ingest.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestor.processor import IngestionProcessor
from tools.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run PDF ingestion with smart checking."""
    try:
        logger.info("Starting PDF ingestion process")

        # Initialize processor (auto-loads config, creates clients)
        processor = IngestionProcessor()

        # Check if collection already has data
        try:
            count = processor.vector_store.count()
            logger.info(f"Vector store currently has {count} vectors")

            if count > 0:
                logger.info("Collection already has data, skipping ingestion")
                print(f"Vector store already has {count} vectors. Skipping ingestion.")
                return 0

        except Exception as e:
            logger.warning(f"Could not check vector count: {e}. Proceeding with ingestion...")

        # Run ingestion
        logger.info(f"Starting ingestion from: {processor.directory}")
        results = processor.process()

        # Report results
        if not results:
            logger.warning("No files found to ingest")
            print("No PDF files found in configured directory")
            return 0

        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        total_chunks = sum(r.get("num_chunks", 0) for r in results if r["success"])
        total_vectors = sum(r.get("num_embeddings", 0) for r in results if r["success"])

        logger.info(
            f"Ingestion complete: {successful} succeeded, {failed} failed, "
            f"{total_chunks} chunks, {total_vectors} vectors"
        )

        print(f"\nIngestion Summary:")
        print(f"  Files processed: {len(results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total chunks: {total_chunks}")
        print(f"  Total vectors: {total_vectors}")

        # Print individual results
        if failed > 0:
            print(f"\nFailed files:")
            for result in results:
                if not result["success"]:
                    print(f"  - {result['filename']}: {result.get('error', 'Unknown error')}")

        return 0 if failed == 0 else 1

    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
