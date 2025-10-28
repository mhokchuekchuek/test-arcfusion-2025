"""Configuration loader for ingestion pipeline.

Loads configuration from configs/ directory using Dynaconf.
Independent from src/ to keep ingestion as a separate preprocessing step.
"""

from pathlib import Path

from dynaconf import Dynaconf


def load_ingestion_config() -> Dynaconf:
    """Load ingestion configuration from configs directory.

    Loads both system.yaml and ingestion.yaml to get all necessary configs
    for LLM client, vector store, and ingestion settings.

    Returns:
        Dynaconf settings object with merged configuration

    Example:
        >>> config = load_ingestion_config()
        >>> print(config.ingestion.directory)
        './papers'
        >>> print(config.llm.proxy_url)
        'http://litellm-proxy:4000'
        >>> print(config.vectordb.qdrant.host)
        'qdrant'
    """
    # Find project root (parent of ingestor/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Load all config files (recursive search in configs/ subdirectories)
    configs_dir = project_root / "configs"
    config_files = sorted(configs_dir.glob("**/*.yaml"))
    # Exclude litellm proxy config (not for application settings)
    settings_files = [str(f) for f in config_files if "litellm" not in str(f)]

    # Load merged config
    settings = Dynaconf(
        settings_files=settings_files,
        envvar_prefix=False,
        environments=False,
        load_dotenv=True,
        dotenv_path=str(project_root / ".env"),
        nested_separator="__",
        merge_enabled=True,
    )

    return settings
