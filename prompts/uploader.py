"""Prompt uploader for Langfuse.

Handles parsing and uploading .prompt files to Langfuse for centralized
prompt management and versioning.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List

import yaml

from prompts.config import load_prompts_config
from tools.logger import get_logger
from tools.observability.selector import ObservabilitySelector

logger = get_logger(__name__)


class PromptUploader:
    """Uploads .prompt files to Langfuse."""

    def __init__(self):
        """Initialize prompt uploader from config.

        All settings are loaded from configs/prompts/uploader.yaml and configs/agents/shared.yaml
        (separate config for local prompt upload use case)
        Override settings via environment variables if needed (e.g., PROMPTS__VERSION=v2)

        Example:
            >>> # Everything from config - super simple!
            >>> uploader = PromptUploader()
            >>> results = uploader.upload_all()
        """
        # Load config
        config = load_prompts_config()
        self.config = config

        logger.info("Initializing PromptUploader from config")

        # Create Langfuse client from config
        logger.debug(f"Creating Langfuse client: host={config.observability.langfuse.host}")
        self.langfuse_client = ObservabilitySelector.create(
            provider=config.observability.langfuse.provider,
            public_key=config.observability.langfuse.public_key,
            secret_key=config.observability.langfuse.secret_key,
            host=config.observability.langfuse.host,
        )

        # Set processing parameters from config
        self.prompts_dir = Path(config.prompts.directory)
        self.VERSION = config.prompts.version
        self.LABEL = config.prompts.label

        if not self.prompts_dir.exists():
            raise ValueError(f"Prompts directory does not exist: {self.prompts_dir}")

        logger.info(
            f"PromptUploader ready: directory={self.prompts_dir}, "
            f"version={self.VERSION}, label={self.LABEL}"
        )

    def parse_prompt_file(self, filepath: Path) -> Dict:
        """Parse .prompt file with YAML frontmatter.

        Args:
            filepath: Path to .prompt file

        Returns:
            Dict with 'config' (frontmatter) and 'template' (content)
        """
        with open(filepath, 'r') as f:
            content = f.read()

        # Split frontmatter and template
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                template = parts[2].strip()
                config = yaml.safe_load(frontmatter) if frontmatter else {}
                return {'config': config, 'template': template}

        return {'config': {}, 'template': content.strip()}

    def upload_prompt(self, filepath: Path) -> bool:
        """Upload a single prompt file to Langfuse.

        Generates prompt name from directory structure:
            prompts/agent/orchestrator/v1.prompt → agent_orchestrator
            prompts/rag/document_retrieval/v1.prompt → rag_document_retrieval
            prompts/evaluation/clarification/v1.prompt → evaluation_clarification

        Args:
            filepath: Path to .prompt file

        Returns:
            True if successful, False otherwise
        """
        # Extract category and name from path
        # Example: prompts/agent/orchestrator/v1.prompt
        # → parts = ['agent', 'orchestrator', 'v1.prompt']
        relative_path = filepath.relative_to(self.prompts_dir)
        parts = relative_path.parts

        if len(parts) >= 2:
            category = parts[0]  # e.g., "agent"
            name = parts[1]      # e.g., "orchestrator"
            version = filepath.stem  # e.g., "v1"
            prompt_name = f"{category}_{name}"  # e.g., "agent_orchestrator"
        else:
            # Fallback for flat structure (backward compatibility)
            prompt_name = filepath.stem
            version = self.VERSION

        logger.info(f"Uploading: {prompt_name} ({version})")

        try:
            parsed = self.parse_prompt_file(filepath)
            config = parsed['config']
            template = parsed['template']

            # Add metadata
            timestamp = datetime.now().isoformat()
            metadata = {
                "uploaded_at": timestamp,
                "source_file": str(filepath.name),
                "category": category if len(parts) >= 2 else "unknown",
                "version": version,
                "label": self.LABEL
            }

            # Create prompt in Langfuse
            self.langfuse_client.client.create_prompt(
                name=prompt_name,
                prompt=template,
                config={**config, **metadata},
                labels=[self.LABEL],
                tags=[version, category if len(parts) >= 2 else "legacy"]
            )

            logger.info(f"✓ Uploaded: {prompt_name} (version: {version}, label: {self.LABEL})")
            return True

        except Exception as e:
            logger.error(f"✗ Failed {prompt_name}: {e}")
            return False

    def upload_all(self) -> List[Dict]:
        """Upload all .prompt files in directory (including nested subdirectories).

        Scans the new directory structure:
            prompts/
            ├── agent/           # Agent system prompts
            │   ├── orchestrator/v1.prompt
            │   ├── clarification/v1.prompt
            │   └── ...
            ├── rag/             # RAG prompts
            │   └── document_retrieval/v1.prompt
            └── evaluation/      # Evaluation prompts
                ├── clarification/v1.prompt
                └── ...

        Uploaded with naming: {category}_{name}_{version}
        Example: agent_orchestrator_v1, evaluation_clarification_v1

        Returns:
            List of results with filename, success status
        """
        # Recursively find all .prompt files in nested structure
        prompt_files = list(self.prompts_dir.glob('**/*.prompt'))

        if not prompt_files:
            logger.warning(f"No .prompt files found in {self.prompts_dir}")
            return []

        logger.info(f"Found {len(prompt_files)} prompt files")
        logger.info(f"Version: {self.VERSION}, Label: {self.LABEL}")

        results = []
        for filepath in prompt_files:
            success = self.upload_prompt(filepath)
            results.append({
                'filename': filepath.name,
                'prompt_name': filepath.stem,
                'success': success
            })

        # Flush to ensure all requests complete
        self.langfuse_client.flush()

        return results
