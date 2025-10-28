"""Configuration package using Dynaconf.

Provides Viper-like configuration management for the application.

Usage:
    ```python
    from src.configs import Settings

    settings = Settings()

    # Access configuration (Viper-like attribute access)
    print(settings.llm.provider)
    print(settings.api.port)
    print(settings.websearch.max_results)

    # Validate configuration
    settings.validate()

    # Reload settings dynamically
    settings.reload()
    ```
"""

from .settings import Settings

__all__ = ["Settings"]
