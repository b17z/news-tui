"""SQLite database management for news-tui.

This module handles database initialization, schema management,
and provides connection utilities.

Security notes:
- Always use parameterized queries (sqlite-utils handles this)
- Never interpolate user input into SQL
- Database file permissions are set to 0o600 (owner only)
"""

import sqlite3
from pathlib import Path
from typing import Any

from sqlite_utils import Database

from news_tui.core.errors import StorageError, Result, err, ok

# Current schema version (increment when schema changes)
SCHEMA_VERSION = 1


def get_connection(db_path: Path) -> Result[Database, StorageError]:
    """Get a database connection, creating the database if needed.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        Result containing Database on success, StorageError on failure.
    """
    try:
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create database (or open existing)
        db = Database(db_path)

        # Set restrictive permissions
        db_path.chmod(0o600)

        return ok(db)
    except (sqlite3.Error, OSError) as e:
        return err(StorageError("connect", f"Cannot open database: {e}"))


def init_db(db: Database) -> Result[None, StorageError]:
    """Initialize database schema.

    Creates all tables if they don't exist and runs migrations.

    Args:
        db: Database connection.

    Returns:
        Result indicating success or failure.
    """
    try:
        # Create schema version table
        db.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)

        # Check current version
        current_version = _get_schema_version(db)

        if current_version < SCHEMA_VERSION:
            _run_migrations(db, current_version, SCHEMA_VERSION)

        return ok(None)
    except sqlite3.Error as e:
        return err(StorageError("init", f"Schema initialization failed: {e}"))


def _get_schema_version(db: Database) -> int:
    """Get current schema version from database."""
    try:
        result = db.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        return result[0] if result else 0
    except sqlite3.Error:
        return 0


def _run_migrations(db: Database, from_version: int, to_version: int) -> None:
    """Run schema migrations."""
    for version in range(from_version + 1, to_version + 1):
        if version == 1:
            _migrate_v1(db)

        # Update version
        db.execute("DELETE FROM schema_version")
        db.execute("INSERT INTO schema_version (version) VALUES (?)", [version])


def _migrate_v1(db: Database) -> None:
    """Initial schema creation (v1)."""

    # Articles table
    db.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            content TEXT DEFAULT '',
            published_at TEXT,
            author TEXT,
            fetched_at TEXT NOT NULL,
            -- Analysis scores
            sentiment REAL DEFAULT 0.0,
            sensationalism REAL DEFAULT 0.0,
            bias REAL DEFAULT 0.0,
            signal REAL DEFAULT 0.5,
            topics TEXT DEFAULT '[]',  -- JSON array
            tldr TEXT DEFAULT '',
            read_time_minutes INTEGER DEFAULT 5,
            analyzed_at TEXT
        )
    """)

    # Indexes for common queries
    db.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_articles_fetched ON articles(fetched_at)")

    # Read history table
    db.execute("""
        CREATE TABLE IF NOT EXISTS read_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT NOT NULL,
            read_at TEXT NOT NULL,
            read_duration_seconds INTEGER,
            topics TEXT DEFAULT '[]',  -- JSON array
            FOREIGN KEY (article_id) REFERENCES articles(id)
        )
    """)

    db.execute("CREATE INDEX IF NOT EXISTS idx_history_article ON read_history(article_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_history_read_at ON read_history(read_at)")

    # Sources table (cached from sources.yaml)
    db.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            source_type TEXT DEFAULT 'rss',
            enabled INTEGER DEFAULT 1,
            bias_rating REAL DEFAULT 0.0,
            reliability_score REAL DEFAULT 0.5,
            last_fetched_at TEXT
        )
    """)


def store_article(db: Database, article_data: dict[str, Any]) -> Result[None, StorageError]:
    """Store or update an article in the database.

    Args:
        db: Database connection.
        article_data: Article data as dictionary.

    Returns:
        Result indicating success or failure.
    """
    try:
        db["articles"].upsert(article_data, pk="id")
        return ok(None)
    except sqlite3.Error as e:
        return err(StorageError("write", f"Cannot store article: {e}"))


def get_article(db: Database, article_id: str) -> Result[dict[str, Any] | None, StorageError]:
    """Retrieve an article by ID.

    Args:
        db: Database connection.
        article_id: Article ID to retrieve.

    Returns:
        Result containing article dict or None if not found.
    """
    try:
        row = db["articles"].get(article_id)
        return ok(row)
    except sqlite3.Error as e:
        return err(StorageError("read", f"Cannot retrieve article: {e}"))


def get_recent_articles(
    db: Database,
    limit: int = 50,
    source_id: str | None = None,
) -> Result[list[dict[str, Any]], StorageError]:
    """Get recently fetched articles.

    Args:
        db: Database connection.
        limit: Maximum number of articles to return.
        source_id: Filter by source (optional).

    Returns:
        Result containing list of article dicts.
    """
    try:
        query = db["articles"]

        if source_id:
            query = query.rows_where("source_id = ?", [source_id])
        else:
            query = query.rows

        # Sort by fetched_at descending, limit results
        articles = list(query)
        articles.sort(key=lambda a: a.get("fetched_at", ""), reverse=True)
        return ok(articles[:limit])
    except sqlite3.Error as e:
        return err(StorageError("read", f"Cannot retrieve articles: {e}"))


def record_read(
    db: Database,
    article_id: str,
    read_at: str,
    topics: list[str],
    duration_seconds: int | None = None,
) -> Result[None, StorageError]:
    """Record that an article was read.

    Args:
        db: Database connection.
        article_id: Which article was read.
        read_at: ISO timestamp of when it was read.
        topics: Topics at time of reading.
        duration_seconds: How long user spent reading (optional).

    Returns:
        Result indicating success or failure.
    """
    try:
        import json

        db["read_history"].insert({
            "article_id": article_id,
            "read_at": read_at,
            "read_duration_seconds": duration_seconds,
            "topics": json.dumps(topics),
        })
        return ok(None)
    except sqlite3.Error as e:
        return err(StorageError("write", f"Cannot record read: {e}"))


def get_read_history(
    db: Database,
    limit: int = 100,
) -> Result[list[dict[str, Any]], StorageError]:
    """Get recent read history.

    Args:
        db: Database connection.
        limit: Maximum entries to return.

    Returns:
        Result containing list of read history entries.
    """
    try:
        entries = list(db["read_history"].rows)
        entries.sort(key=lambda e: e.get("read_at", ""), reverse=True)
        return ok(entries[:limit])
    except sqlite3.Error as e:
        return err(StorageError("read", f"Cannot retrieve history: {e}"))
