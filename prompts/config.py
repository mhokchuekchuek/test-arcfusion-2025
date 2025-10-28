"""Configuration loader for prompt uploader.

Loads configuration from configs/ directory using Dynaconf.
Independent from src/ to keep prompt management as a separate process.
"""

from pathlib import Path
from dynaconf import Dynaconf


def load_prompts_config() -> Dynaconf:
    """Load configuration for prompt uploader.

    Returns:
        Dynaconf settings object with merged configuration

    Example:
        >>> config = load_prompts_config()
        >>> print(config.observability.langfuse.host)
        'http://langfuse:3000'
        >>> print(config.observability.langfuse.public_key)
        'pk-...'
    """
    # Find project root (parent of prompts/)
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
