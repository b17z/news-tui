"""Read history tracking for news-tui.

This module provides higher-level functions for tracking
and analyzing reading history.
"""

from datetime import datetime, timedelta
from typing import Any

from sqlite_utils import Database

from news_tui.core.errors import Err, StorageError, Result, ok
from news_tui.track.db import get_read_history, record_read


def mark_as_read(
    db: Database,
    article_id: str,
    topics: list[str],
    duration_seconds: int | None = None,
) -> Result[None, StorageError]:
    """Mark an article as read.

    Args:
        db: Database connection.
        article_id: Article that was read.
        topics: Topics of the article.
        duration_seconds: Optional reading duration.

    Returns:
        Result indicating success or failure.
    """
    return record_read(
        db,
        article_id=article_id,
        read_at=datetime.now().isoformat(),
        topics=topics,
        duration_seconds=duration_seconds,
    )


def get_reading_stats(db: Database, days: int = 7) -> Result[dict[str, Any], StorageError]:
    """Get reading statistics for the past N days.

    Args:
        db: Database connection.
        days: Number of days to analyze.

    Returns:
        Result containing stats dictionary.
    """
    history_result = get_read_history(db, limit=1000)
    if isinstance(history_result, Err):
        return history_result

    history = history_result.value
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    # Filter to recent entries
    recent = [h for h in history if h.get("read_at", "") >= cutoff]

    # Calculate stats
    total_articles = len(recent)
    total_time = sum(
        h.get("read_duration_seconds") or 0
        for h in recent
    )

    # Topic distribution
    import json
    topic_counts: dict[str, int] = {}
    for entry in recent:
        topics_json = entry.get("topics", "[]")
        try:
            topics = json.loads(topics_json) if isinstance(topics_json, str) else topics_json
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        except json.JSONDecodeError:
            pass

    return ok({
        "period_days": days,
        "total_articles": total_articles,
        "total_time_minutes": total_time // 60,
        "articles_per_day": total_articles / days if days > 0 else 0,
        "top_topics": sorted(topic_counts.items(), key=lambda x: -x[1])[:10],
    })
