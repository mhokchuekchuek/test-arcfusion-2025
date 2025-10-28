"""Configuration loader for evaluation pipeline.

Loads configuration from configs/ directory using Dynaconf.
Independent from src/ to keep evaluation as a separate module.
"""

from pathlib import Path

from dynaconf import Dynaconf


def load_evaluation_config() -> Dynaconf:
    """Load evaluation configuration from configs directory.

    Loads agent configs to get agent names for workflow validation.

    Returns:
        Dynaconf settings object with merged configuration

    Example:
        >>> config = load_evaluation_config()
        >>> print(config.orchestrator.name)
        'orchestrator'
        >>> print(config.research.name)
        'research'
    """
    # Find project root (parent of evaluation/)
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
