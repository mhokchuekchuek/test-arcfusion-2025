from pathlib import Path

from dynaconf import Dynaconf

from .validator import ConfigValidator


class Settings:
    """Application settings manager using Dynaconf.

    This class wraps Dynaconf and provides a clean interface for
    configuration management with validation support.

    Attributes:
        _dynaconf: Internal Dynaconf instance
        _validator: Configuration validator
    """

    def __init__(self):
        """Initialize settings from YAML, .env, and environment variables."""
        # Find project root
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent

        # Auto-discover all YAML config files (recursive)
        configs_dir = project_root / "configs"
        config_files = sorted(configs_dir.glob("**/*.yaml"))
        settings_files = [str(f) for f in config_files]

        # Initialize Dynaconf
        self._dynaconf = Dynaconf(
            # Settings files (auto-discovered, loaded in sorted order)
            settings_files=settings_files,
            # Environment variables (no prefix required - simpler!)
            envvar_prefix=False,  # Can use LLM__PROVIDER directly
            environments=False,  # Set to True for multi-env support (dev, prod, etc)
            # .env file support
            load_dotenv=True,
            dotenv_path=str(project_root / ".env"),
            # Nested separator for env vars (LLM__PROVIDER maps to llm.provider)
            nested_separator="__",
            # Merge nested dicts instead of replacing
            merge_enabled=True,
        )

        # Initialize validator
        self._validator = ConfigValidator(self._dynaconf)

    def __getattr__(self, name: str):
        """Delegate attribute access to Dynaconf instance.

        This allows: settings.llm.provider instead of settings._dynaconf.llm.provider

        Args:
            name: Attribute name

        Returns:
            Value from Dynaconf settings
        """
        return getattr(self._dynaconf, name)

    def validate(self) -> None:
        """Validate all configuration settings.

        Raises:
            ValueError: If any validation fails
        """
        self._validator.validate_all()

    def reload(self) -> None:
        """Reload settings from all sources.

        Useful when environment variables change at runtime.
        """
        self._dynaconf.reload()
