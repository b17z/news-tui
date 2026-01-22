"""Source registry and management for news-tui.

This module handles loading and managing news source configurations.

Security notes:
- ALWAYS use yaml.safe_load(), NEVER yaml.load()
- Validate all URLs before use
"""

from pathlib import Path

import yaml

from news_tui.core.errors import ConfigError, Result, err, ok
from news_tui.core.types import Source, SourceId

# Default sources for first-time users
DEFAULT_SOURCES: list[dict[str, str | float | bool]] = [
    {
        "id": "hn",
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "source_type": "rss",
        "bias_rating": 0.0,
        "reliability_score": 0.7,
    },
    {
        "id": "lobsters",
        "name": "Lobste.rs",
        "url": "https://lobste.rs/rss",
        "source_type": "rss",
        "bias_rating": 0.0,
        "reliability_score": 0.75,
    },
    {
        "id": "aeon",
        "name": "Aeon",
        "url": "https://aeon.co/feed.rss",
        "source_type": "rss",
        "bias_rating": -0.1,
        "reliability_score": 0.85,
    },
]


def load_sources(sources_path: Path) -> Result[list[Source], ConfigError]:
    """Load source configurations from file.

    If the file doesn't exist, creates it with default sources.

    Args:
        sources_path: Path to sources.yaml file.

    Returns:
        Result containing list of Source on success, ConfigError on failure.

    Security:
        - Uses yaml.safe_load() to prevent code execution
    """
    if not sources_path.exists():
        # Create default sources file
        create_result = _create_default_sources(sources_path)
        if isinstance(create_result, err):
            return create_result

    try:
        with open(sources_path) as f:
            # SECURITY: Always use safe_load, never load()
            data = yaml.safe_load(f)

        if data is None:
            return ok([])

        if not isinstance(data, dict) or "sources" not in data:
            return err(ConfigError("sources", "Invalid sources file format"))

        sources_data = data["sources"]
        if not isinstance(sources_data, list):
            return err(ConfigError("sources", "sources must be a list"))

        sources: list[Source] = []
        for i, source_dict in enumerate(sources_data):
            try:
                # Ensure ID is a SourceId
                if "id" in source_dict:
                    source_dict["id"] = SourceId(source_dict["id"])
                source = Source(**source_dict)
                sources.append(source)
            except (ValueError, TypeError) as e:
                return err(ConfigError(f"sources[{i}]", str(e)))

        return ok(sources)

    except yaml.YAMLError as e:
        return err(ConfigError("sources", f"Invalid YAML: {e}"))
    except OSError as e:
        return err(ConfigError("sources", f"Cannot read sources file: {e}"))


def _create_default_sources(sources_path: Path) -> Result[None, ConfigError]:
    """Create the default sources file.

    Args:
        sources_path: Path to create the file at.

    Returns:
        Result indicating success or failure.
    """
    try:
        sources_path.parent.mkdir(parents=True, exist_ok=True)

        with open(sources_path, "w") as f:
            yaml.safe_dump({"sources": DEFAULT_SOURCES}, f, default_flow_style=False)

        # Set restrictive permissions
        sources_path.chmod(0o600)

        return ok(None)
    except OSError as e:
        return err(ConfigError("sources", f"Cannot create sources file: {e}"))


def save_sources(sources: list[Source], sources_path: Path) -> Result[None, ConfigError]:
    """Save source configurations to file.

    Args:
        sources: List of sources to save.
        sources_path: Path to save to.

    Returns:
        Result indicating success or failure.
    """
    try:
        sources_data = [source.model_dump() for source in sources]

        with open(sources_path, "w") as f:
            yaml.safe_dump({"sources": sources_data}, f, default_flow_style=False)

        sources_path.chmod(0o600)
        return ok(None)
    except OSError as e:
        return err(ConfigError("sources", f"Cannot save sources file: {e}"))


def add_source(
    sources: list[Source],
    name: str,
    url: str,
    source_type: str = "rss",
) -> Result[list[Source], ConfigError]:
    """Add a new source to the list.

    Args:
        sources: Current list of sources.
        name: Name for the new source.
        url: Feed URL.
        source_type: Type of source (rss, atom, etc.).

    Returns:
        Result containing updated list of sources.
    """
    # Generate ID from name (lowercase, replace spaces with hyphens)
    source_id = SourceId(name.lower().replace(" ", "-")[:20])

    # Check for duplicate ID
    if any(s.id == source_id for s in sources):
        return err(ConfigError("source", f"Source with ID '{source_id}' already exists"))

    try:
        new_source = Source(
            id=source_id,
            name=name,
            url=url,  # type: ignore[arg-type]  # Pydantic validates
            source_type=source_type,  # type: ignore[arg-type]
        )
        return ok([*sources, new_source])
    except ValueError as e:
        return err(ConfigError("source", str(e)))


def remove_source(sources: list[Source], source_id: str) -> Result[list[Source], ConfigError]:
    """Remove a source by ID.

    Args:
        sources: Current list of sources.
        source_id: ID of source to remove.

    Returns:
        Result containing updated list of sources.
    """
    new_sources = [s for s in sources if s.id != source_id]

    if len(new_sources) == len(sources):
        return err(ConfigError("source", f"Source '{source_id}' not found"))

    return ok(new_sources)
