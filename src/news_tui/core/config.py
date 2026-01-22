"""Configuration management for news-tui.

This module handles loading and validating configuration from files and
environment variables.

Security notes:
- ALWAYS use yaml.safe_load(), NEVER yaml.load()
- Config files should have restricted permissions (0o600)
- API keys should come from environment variables, not config files
- Validate all paths to prevent directory traversal
"""

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from news_tui.core.errors import ConfigError, Result, err, ok

# Default config directory
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "news-tui"

# Environment variable prefix
ENV_PREFIX = "NEWS_TUI_"


class AppConfig(BaseModel):
    """Application configuration.

    Attributes:
        config_dir: Directory for config files and database.
        debug: Enable debug logging.
        refresh_interval_minutes: How often to refresh feeds (0 = manual only).
        max_articles_per_source: Maximum articles to keep per source.
        default_tldr_length: Default length for generated TL;DRs.
    """

    model_config = ConfigDict(frozen=True)

    config_dir: Path = DEFAULT_CONFIG_DIR
    debug: bool = False
    refresh_interval_minutes: int = Field(default=0, ge=0, le=1440)
    max_articles_per_source: int = Field(default=100, ge=10, le=1000)
    default_tldr_length: int = Field(default=50, ge=20, le=200)


class AnalysisConfig(BaseModel):
    """Configuration for the analysis layer.

    Attributes:
        sentiment_threshold_positive: Score above which sentiment is "positive".
        sentiment_threshold_negative: Score below which sentiment is "negative".
        sensationalism_warning_threshold: Score above which to warn about clickbait.
        min_signal_score: Minimum signal score to display article prominently.
    """

    model_config = ConfigDict(frozen=True)

    sentiment_threshold_positive: float = Field(default=0.3, ge=0.0, le=1.0)
    sentiment_threshold_negative: float = Field(default=-0.3, ge=-1.0, le=0.0)
    sensationalism_warning_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    min_signal_score: float = Field(default=0.3, ge=0.0, le=1.0)


class NudgeConfig(BaseModel):
    """Configuration for consumption nudges.

    Attributes:
        topic_drift_threshold: Percentage of same-topic articles to trigger nudge.
        topic_drift_window: Number of recent articles to check for drift.
        enable_diversify_nudges: Show "diversify your reading" nudges.
        enable_sensationalism_warnings: Warn about high-sensationalism sources.
    """

    model_config = ConfigDict(frozen=True)

    topic_drift_threshold: float = Field(default=0.75, ge=0.5, le=1.0)
    topic_drift_window: int = Field(default=10, ge=5, le=50)
    enable_diversify_nudges: bool = True
    enable_sensationalism_warnings: bool = True


class Config(BaseModel):
    """Root configuration object.

    Combines all config sections into a single immutable object.
    """

    model_config = ConfigDict(frozen=True)

    app: AppConfig = Field(default_factory=AppConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    nudges: NudgeConfig = Field(default_factory=NudgeConfig)


def _sanitize_path_component(name: str) -> str:
    """Sanitize a path component to prevent directory traversal.

    Only allows alphanumeric characters, hyphens, underscores, and dots.

    Args:
        name: The path component to sanitize.

    Returns:
        Sanitized path component.
    """
    # Remove any path separators and dangerous characters
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "", name)
    # Prevent hidden files or directory traversal
    sanitized = sanitized.lstrip(".")
    return sanitized or "unnamed"


def _is_safe_path(base: Path, target: Path) -> bool:
    """Check if target path is safely within base directory.

    Args:
        base: The allowed base directory.
        target: The path to check.

    Returns:
        True if target is within base, False otherwise.
    """
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def load_config(config_path: Path | None = None) -> Result[Config, ConfigError]:
    """Load configuration from file.

    Configuration is loaded from:
    1. Default values
    2. Config file (if exists)
    3. Environment variables (override file values)

    Args:
        config_path: Path to config.yaml file. If None, uses default location.

    Returns:
        Result containing Config on success, ConfigError on failure.

    Security:
        - Uses yaml.safe_load() to prevent code execution
        - Validates all paths before use
    """
    config_dir = DEFAULT_CONFIG_DIR
    if config_path is None:
        config_path = config_dir / "config.yaml"

    # Start with defaults
    config_dict: dict[str, Any] = {}

    # Load from file if exists
    if config_path.exists():
        try:
            with open(config_path) as f:
                # SECURITY: Always use safe_load, never load()
                loaded = yaml.safe_load(f)
                if loaded is not None:
                    if not isinstance(loaded, dict):
                        return err(ConfigError("root", "Config file must be a YAML mapping"))
                    config_dict = loaded
        except yaml.YAMLError as e:
            return err(ConfigError("file", f"Invalid YAML: {e}"))
        except OSError as e:
            return err(ConfigError("file", f"Cannot read config file: {e}"))

    # Override with environment variables
    env_overrides = _load_env_overrides()
    _deep_merge(config_dict, env_overrides)

    # Validate and create config
    try:
        config = Config(**config_dict)
        return ok(config)
    except ValueError as e:
        return err(ConfigError("validation", str(e)))


def _load_env_overrides() -> dict[str, Any]:
    """Load configuration overrides from environment variables.

    Environment variables follow the pattern:
    NEWS_TUI_SECTION_KEY=value

    For example:
    NEWS_TUI_APP_DEBUG=true
    NEWS_TUI_ANALYSIS_MIN_SIGNAL_SCORE=0.5

    Returns:
        Dictionary of overrides to merge into config.
    """
    overrides: dict[str, Any] = {}

    for key, value in os.environ.items():
        if not key.startswith(ENV_PREFIX):
            continue

        # Parse key: NEWS_TUI_SECTION_FIELD -> section.field
        parts = key[len(ENV_PREFIX) :].lower().split("_", 1)
        if len(parts) != 2:
            continue

        section, field = parts

        # Convert value to appropriate type
        parsed_value = _parse_env_value(value)

        # Build nested dict
        if section not in overrides:
            overrides[section] = {}
        overrides[section][field] = parsed_value

    return overrides


def _parse_env_value(value: str) -> str | int | float | bool:
    """Parse an environment variable value to the appropriate type.

    Args:
        value: The string value from environment.

    Returns:
        Parsed value (bool, int, float, or str).
    """
    # Boolean
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    # String
    return value


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    """Deep merge override dict into base dict (mutates base).

    Args:
        base: The base dictionary to merge into.
        override: The dictionary with override values.
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def ensure_config_dir(config: Config) -> Result[Path, ConfigError]:
    """Ensure the config directory exists with proper permissions.

    Args:
        config: The application config.

    Returns:
        Result containing the config directory path on success.
    """
    config_dir = config.app.config_dir

    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        # Set restrictive permissions (owner only)
        config_dir.chmod(0o700)
        return ok(config_dir)
    except OSError as e:
        return err(ConfigError("config_dir", f"Cannot create config directory: {e}"))


def get_db_path(config: Config) -> Path:
    """Get the path to the SQLite database.

    Args:
        config: The application config.

    Returns:
        Path to the database file.
    """
    return config.app.config_dir / "news-tui.db"


def get_sources_path(config: Config) -> Path:
    """Get the path to the sources configuration file.

    Args:
        config: The application config.

    Returns:
        Path to the sources.yaml file.
    """
    return config.app.config_dir / "sources.yaml"
