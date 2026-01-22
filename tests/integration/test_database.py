"""Integration tests for database operations.

Tests the SQLite database layer including schema, CRUD operations,
and read history tracking.
"""

import pytest
from sqlite_utils import Database

from news_tui.core.errors import Ok, Err
from news_tui.track.db import (
    init_db,
    store_article,
    get_article,
    get_recent_articles,
    record_read,
    get_read_history,
)


class TestDatabaseInit:
    """Tests for database initialization."""

    def test_init_creates_tables(self, test_db: Database):
        """Test that init_db creates required tables."""
        # init_db is called by fixture, just verify tables exist
        tables = set(test_db.table_names())

        assert "articles" in tables
        assert "read_history" in tables
        assert "sources" in tables
        assert "schema_version" in tables

    def test_init_is_idempotent(self, test_db: Database):
        """Test that init_db can be called multiple times."""
        # Should not raise
        result1 = init_db(test_db)
        result2 = init_db(test_db)

        assert isinstance(result1, Ok)
        assert isinstance(result2, Ok)


class TestArticleStorage:
    """Tests for article storage operations."""

    def test_store_and_retrieve_article(self, test_db: Database):
        """Test storing and retrieving an article."""
        article_data = {
            "id": "test-123",
            "source_id": "test-source",
            "title": "Test Article",
            "url": "https://example.com/article",
            "content": "Article content here.",
            "fetched_at": "2024-01-15T10:00:00",
            "sentiment": 0.5,
            "topics": '["ai", "tech"]',
        }

        # Store
        store_result = store_article(test_db, article_data)
        assert isinstance(store_result, Ok)

        # Retrieve
        get_result = get_article(test_db, "test-123")
        assert isinstance(get_result, Ok)
        assert get_result.value is not None
        assert get_result.value["title"] == "Test Article"

    def test_store_updates_existing(self, test_db: Database):
        """Test that storing with same ID updates the article."""
        article_v1 = {
            "id": "update-test",
            "source_id": "test",
            "title": "Original Title",
            "url": "https://example.com/update",
            "fetched_at": "2024-01-15T10:00:00",
        }
        article_v2 = {
            "id": "update-test",
            "source_id": "test",
            "title": "Updated Title",
            "url": "https://example.com/update",
            "fetched_at": "2024-01-15T11:00:00",
        }

        store_article(test_db, article_v1)
        store_article(test_db, article_v2)

        result = get_article(test_db, "update-test")
        assert isinstance(result, Ok)
        assert result.value["title"] == "Updated Title"

    def test_get_nonexistent_article(self, test_db: Database):
        """Test retrieving non-existent article returns None."""
        result = get_article(test_db, "does-not-exist")

        assert isinstance(result, Ok)
        assert result.value is None

    def test_get_recent_articles(self, test_db: Database):
        """Test retrieving recent articles."""
        # Store some articles
        for i in range(5):
            store_article(test_db, {
                "id": f"recent-{i}",
                "source_id": "test",
                "title": f"Article {i}",
                "url": f"https://example.com/{i}",
                "fetched_at": f"2024-01-{15+i:02d}T10:00:00",
            })

        result = get_recent_articles(test_db, limit=3)

        assert isinstance(result, Ok)
        assert len(result.value) == 3

    def test_get_recent_articles_by_source(self, test_db: Database):
        """Test filtering recent articles by source."""
        store_article(test_db, {
            "id": "source-a-1",
            "source_id": "source-a",
            "title": "From A",
            "url": "https://a.com/1",
            "fetched_at": "2024-01-15T10:00:00",
        })
        store_article(test_db, {
            "id": "source-b-1",
            "source_id": "source-b",
            "title": "From B",
            "url": "https://b.com/1",
            "fetched_at": "2024-01-15T10:00:00",
        })

        result = get_recent_articles(test_db, source_id="source-a")

        assert isinstance(result, Ok)
        assert len(result.value) == 1
        assert result.value[0]["source_id"] == "source-a"


class TestReadHistory:
    """Tests for read history tracking."""

    def test_record_and_retrieve_read(self, test_db: Database):
        """Test recording and retrieving read history."""
        record_result = record_read(
            test_db,
            article_id="read-test",
            read_at="2024-01-15T10:00:00",
            topics=["ai", "tech"],
            duration_seconds=300,
        )

        assert isinstance(record_result, Ok)

        history_result = get_read_history(test_db, limit=10)
        assert isinstance(history_result, Ok)
        assert len(history_result.value) >= 1

    def test_read_history_order(self, test_db: Database):
        """Test that history is returned in reverse chronological order."""
        record_read(test_db, "article-1", "2024-01-15T10:00:00", [])
        record_read(test_db, "article-2", "2024-01-16T10:00:00", [])
        record_read(test_db, "article-3", "2024-01-14T10:00:00", [])

        result = get_read_history(test_db)
        assert isinstance(result, Ok)

        # Most recent first
        dates = [h["read_at"] for h in result.value]
        assert dates == sorted(dates, reverse=True)
