"""Pytest configuration and fixtures for news-tui tests.

This module provides shared fixtures used across unit and integration tests.
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlite_utils import Database

from news_tui.core.config import Config, AppConfig
from news_tui.core.types import ArticleId, RawArticle, Source, SourceId
from news_tui.track.db import init_db


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_dir: Path) -> Config:
    """Create a test configuration with temporary paths."""
    return Config(
        app=AppConfig(config_dir=temp_dir, debug=True),
    )


@pytest.fixture
def test_db(temp_dir: Path) -> Generator[Database, None, None]:
    """Create an in-memory test database."""
    db_path = temp_dir / "test.db"
    db = Database(db_path)
    init_db(db)
    yield db
    db.close()


@pytest.fixture
def sample_source() -> Source:
    """Create a sample source for testing."""
    return Source(
        id=SourceId("test-source"),
        name="Test Source",
        url="https://example.com/feed.rss",  # type: ignore
        source_type="rss",
        bias_rating=0.0,
        reliability_score=0.7,
    )


@pytest.fixture
def sample_raw_article() -> RawArticle:
    """Create a sample raw article for testing."""
    from datetime import datetime

    return RawArticle(
        id=ArticleId("test-article-123"),
        source_id=SourceId("test-source"),
        title="Test Article: AI Makes Progress in Research",
        url="https://example.com/article/123",  # type: ignore
        content="""
        Artificial intelligence continues to make significant progress in various
        research areas. Scientists at leading institutions have developed new
        machine learning techniques that show promising results.

        The new approach combines deep learning with traditional algorithms to
        achieve better performance on complex tasks. Researchers are optimistic
        about the potential applications in healthcare and climate science.

        However, some experts caution that more work is needed before these
        systems can be deployed in real-world scenarios.
        """,
        published_at=datetime(2024, 1, 15, 10, 30, 0),
        author="Jane Researcher",
    )


@pytest.fixture
def sample_text() -> str:
    """Sample text for NLP testing."""
    return """
    The quick brown fox jumps over the lazy dog.
    This is a classic pangram used for testing.
    The fox was very quick and the dog was quite lazy.
    In the end, they became friends despite their differences.
    """


@pytest.fixture
def sample_rss_feed() -> str:
    """Sample RSS feed XML for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <link>https://example.com</link>
            <description>A test RSS feed</description>
            <item>
                <title>First Article</title>
                <link>https://example.com/article/1</link>
                <description>This is the first test article.</description>
                <pubDate>Mon, 15 Jan 2024 10:00:00 GMT</pubDate>
                <author>test@example.com</author>
            </item>
            <item>
                <title>Second Article</title>
                <link>https://example.com/article/2</link>
                <description>This is the second test article.</description>
                <pubDate>Tue, 16 Jan 2024 11:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>
    """
