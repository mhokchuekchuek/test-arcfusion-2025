"""Configuration validators.

Validators check conditional configuration requirements that dynaconf
cannot handle (e.g., API key required based on provider selection).
"""


class ConfigValidator:
    """Validates configuration settings based on conditional rules."""

    def __init__(self, settings):
        """Initialize validator with settings object.

        Args:
            settings: Dynaconf settings instance
        """
        self.settings = settings

    def validate_websearch_api_key(self) -> None:
        """Validate web search API key based on selected provider.

        Raises:
            ValueError: If required API key is missing
        """
        if self.settings.websearch.provider == "tavily":
            if not self.settings.get("api_keys.tavily_api_key"):
                raise ValueError(
                    "TAVILY_API_KEY is required when websearch.provider=tavily. "
                    "Set via environment variable API_KEYS__TAVILY_API_KEY "
                    "or in .env file"   
                )
        elif self.settings.websearch.provider == "serp_api":
            if not self.settings.get("api_keys.serp_api_key"):
                raise ValueError(
                    "SERP_API_KEY is required when websearch.provider=serp_api. "
                    "Set via environment variable API_KEYS__SERP_API_KEY "
                    "or in .env file"
                )

    def validate_ingestion_config(self) -> None:
        """Validate ingestion configuration.

        Raises:
            ValueError: If chunk_overlap >= chunk_size
        """
        if self.settings.ingestion.chunk_overlap >= self.settings.ingestion.chunk_size:
            raise ValueError(
                f"ingestion.chunk_overlap ({self.settings.ingestion.chunk_overlap}) "
                f"must be less than ingestion.chunk_size ({self.settings.ingestion.chunk_size})"
            )

    def validate_all(self) -> None:
        """Run all validation checks.

        Raises:
            ValueError: If any validation fails
        """
        self.validate_websearch_api_key()
        self.validate_ingestion_config()
