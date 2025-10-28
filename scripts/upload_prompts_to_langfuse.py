#!/usr/bin/env python3
"""Upload local .prompt files to Langfuse.

Automatically uploads all .prompt files from prompts/ directory to Langfuse
for centralized prompt management and versioning.

Usage:
    python scripts/upload_prompts_to_langfuse.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prompts.uploader import PromptUploader
from tools.logger import get_logger

logger = get_logger(__name__)


def main():
    """Upload all .prompt files to Langfuse."""
    try:
        logger.info("Starting prompt upload process")

        # Initialize uploader (auto-loads config, creates Langfuse client)
        uploader = PromptUploader()

        # Upload all prompts
        results = uploader.upload_all()

        # Report results
        if not results:
            logger.warning("No .prompt files found")
            print("No .prompt files found in prompts/ directory")
            return 0

        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful

        logger.info(
            f"Upload complete: {successful} succeeded, {failed} failed"
        )

        print(f"\nUpload Summary:")
        print(f"  Files processed: {len(results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Version: {uploader.VERSION}")
        print(f"  Label: {uploader.LABEL}")

        # Print individual results
        if successful > 0:
            print(f"\nUploaded prompts:")
            for result in results:
                if result["success"]:
                    print(f"  ✓ {result['prompt_name']}")

        if failed > 0:
            print(f"\nFailed uploads:")
            for result in results:
                if not result["success"]:
                    print(f"  ✗ {result['filename']}")

        return 0 if failed == 0 else 1

    except Exception as e:
        logger.error(f"Prompt upload failed: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
