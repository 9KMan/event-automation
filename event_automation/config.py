"""Configuration management for event_automation."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Try to load .env file from project root or current directory
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()


class Config:
    """Configuration class that reads from environment variables."""

    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
    SPORTS_API_KEY: str = os.getenv("SPORTS_API_KEY", "")
    SELENIUM_HEADLESS: bool = os.getenv("SELENIUM_HEADLESS", "true").lower() == "true"

    # Derived settings
    LLM_PROVIDER: str = _detect_provider(LLM_MODEL)

    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value by key."""
        return os.getenv(key, default)

    @classmethod
    def reload(cls) -> None:
        """Reload configuration from environment."""
        load_dotenv(override=True)
        cls.LLM_API_KEY = os.getenv("LLM_API_KEY", "")
        cls.LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
        cls.SPORTS_API_KEY = os.getenv("SPORTS_API_KEY", "")
        cls.SELENIUM_HEADLESS = os.getenv("SELENIUM_HEADLESS", "true").lower() == "true"
        cls.LLM_PROVIDER = _detect_provider(cls.LLM_MODEL)


def _detect_provider(model: str) -> str:
    """Detect LLM provider from model name."""
    model_lower = model.lower()
    if "claude" in model_lower:
        return "anthropic"
    elif "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
        return "openai"
    else:
        return "openai"  # default


# Global config instance
config = Config()