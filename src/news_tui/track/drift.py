"""Topic drift detection for news-tui.

This module detects when reading patterns become too focused
on a narrow set of topics, triggering diversification nudges.
"""

import json
from collections import Counter
from typing import Any

from sqlite_utils import Database

from news_tui.core.errors import StorageError, Result, ok
from news_tui.core.types import TopicTag
from news_tui.track.db import get_read_history


def detect_topic_drift(
    db: Database,
    window_size: int = 10,
    threshold: float = 0.75,
) -> Result[dict[str, Any] | None, StorageError]:
    """Detect if reading has drifted to a narrow topic focus.

    Args:
        db: Database connection.
        window_size: Number of recent articles to analyze.
        threshold: Percentage threshold for drift warning (0.0-1.0).

    Returns:
        Result containing drift info dict if drift detected, None otherwise.
        Drift info includes: dominant_topics, percentage, suggested_topics.
    """
    history_result = get_read_history(db, limit=window_size)
    if isinstance(history_result, err):
        return history_result

    history = history_result.value

    if len(history) < window_size // 2:
        # Not enough history to detect drift
        return ok(None)

    # Collect all topics from recent reads
    all_topics: list[str] = []
    for entry in history[:window_size]:
        topics_json = entry.get("topics", "[]")
        try:
            topics = json.loads(topics_json) if isinstance(topics_json, str) else topics_json
            all_topics.extend(topics)
        except json.JSONDecodeError:
            pass

    if not all_topics:
        return ok(None)

    # Count topic frequencies
    topic_counts = Counter(all_topics)
    total_topics = len(all_topics)

    # Find dominant topic(s)
    most_common = topic_counts.most_common(3)
    dominant_count = most_common[0][1] if most_common else 0
    dominant_percentage = dominant_count / total_topics if total_topics > 0 else 0

    if dominant_percentage >= threshold:
        # Drift detected!
        dominant_topics = [topic for topic, count in most_common if count >= dominant_count * 0.5]

        # Suggest alternative topics
        suggested = _suggest_alternatives(dominant_topics)

        return ok({
            "dominant_topics": dominant_topics,
            "percentage": dominant_percentage,
            "article_count": len(history[:window_size]),
            "suggested_topics": suggested,
        })

    return ok(None)


def _suggest_alternatives(dominant_topics: list[str]) -> list[str]:
    """Suggest alternative topics to diversify reading.

    Args:
        dominant_topics: Topics user is currently focused on.

    Returns:
        List of suggested alternative topics.
    """
    # Topic "opposites" or complementary topics
    ALTERNATIVES: dict[str, list[str]] = {
        "ai": ["philosophy", "culture", "science"],
        "tech": ["culture", "science", "finance"],
        "crypto": ["finance", "science", "culture"],
        "finance": ["science", "culture", "tech"],
        "politics": ["science", "culture", "philosophy"],
        "science": ["culture", "philosophy", "tech"],
        "culture": ["science", "tech", "philosophy"],
    }

    suggestions: set[str] = set()
    for topic in dominant_topics:
        if topic in ALTERNATIVES:
            suggestions.update(ALTERNATIVES[topic])

    # Remove dominant topics from suggestions
    suggestions -= set(dominant_topics)

    return list(suggestions)[:3]
