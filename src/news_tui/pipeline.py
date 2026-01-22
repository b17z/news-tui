"""Article processing pipeline for news-tui.

This module orchestrates the full flow:
    fetch RSS → analyze → generate TL;DR → store

All functions are pure where possible, with I/O at the boundaries.
"""

import json
from datetime import datetime

from sqlite_utils import Database

from news_tui.analyze.quality import compute_signal_score, reading_time_minutes
from news_tui.analyze.sentiment import analyze_sentiment
from news_tui.analyze.topics import extract_topics
from news_tui.core.errors import Err, Ok, Result, err, ok
from news_tui.core.types import (
    AnalysisScores,
    Article,
    RawArticle,
    Source,
    TopicTag,
)
from news_tui.generate.markov import generate_tldr
from news_tui.ingest.rss import fetch_rss
from news_tui.track.db import get_recent_articles, store_article


def analyze_article(raw: RawArticle) -> Article:
    """Analyze a raw article and produce a fully processed Article.

    Runs sentiment, topic, and quality analysis, then generates TL;DR.

    Args:
        raw: The raw article to analyze.

    Returns:
        Fully processed Article with scores and TL;DR.
    """
    # Combine title and content for analysis
    full_text = f"{raw.title}. {raw.content}"

    # Sentiment analysis
    sentiment_result = analyze_sentiment(full_text, raw.id)
    sentiment = sentiment_result.value if isinstance(sentiment_result, Ok) else 0.0

    # Topic extraction
    topics = extract_topics(full_text)

    # Quality/signal score
    signal_result = compute_signal_score(raw.content, raw.id)
    signal = signal_result.value if isinstance(signal_result, Ok) else 0.5

    # Reading time
    read_time = reading_time_minutes(raw.content)

    # Generate TL;DR using Markov chains
    tldr = generate_tldr(raw.content, max_words=50)
    if not tldr:
        # Fallback to truncated content
        words = raw.content.split()[:40]
        tldr = " ".join(words) + "..." if words else ""

    scores = AnalysisScores(
        sentiment=sentiment,
        sensationalism=0.0,  # TODO: Phase 4
        bias=0.0,  # TODO: Phase 4
        signal=signal,
        topics=topics,
    )

    return Article(
        raw=raw,
        scores=scores,
        tldr=tldr,
        read_time_minutes=read_time,
        analyzed_at=datetime.now(),
    )


def article_to_db_dict(article: Article) -> dict:
    """Convert an Article to a dictionary for database storage.

    Args:
        article: The article to convert.

    Returns:
        Dictionary suitable for store_article().
    """
    return {
        "id": article.id,
        "source_id": article.source_id,
        "title": article.title,
        "url": str(article.url),
        "content": article.raw.content,
        "published_at": article.raw.published_at.isoformat() if article.raw.published_at else None,
        "author": article.raw.author,
        "fetched_at": article.raw.fetched_at.isoformat(),
        "sentiment": article.scores.sentiment,
        "sensationalism": article.scores.sensationalism,
        "bias": article.scores.bias,
        "signal": article.scores.signal,
        "topics": json.dumps(list(article.scores.topics)),
        "tldr": article.tldr,
        "read_time_minutes": article.read_time_minutes,
        "analyzed_at": article.analyzed_at.isoformat(),
    }


def db_dict_to_article(row: dict) -> Article:
    """Convert a database row back to an Article.

    Args:
        row: Database row dictionary.

    Returns:
        Reconstructed Article object.
    """
    from news_tui.core.types import ArticleId, SourceId

    # Parse topics from JSON
    topics_json = row.get("topics", "[]")
    if isinstance(topics_json, str):
        topics = tuple(TopicTag(t) for t in json.loads(topics_json))
    else:
        topics = ()

    # Parse dates
    published_at = None
    if row.get("published_at"):
        published_at = datetime.fromisoformat(row["published_at"])

    fetched_at = datetime.fromisoformat(row["fetched_at"])
    analyzed_at = datetime.fromisoformat(row["analyzed_at"]) if row.get("analyzed_at") else datetime.now()

    raw = RawArticle(
        id=ArticleId(row["id"]),
        source_id=SourceId(row["source_id"]),
        title=row["title"],
        url=row["url"],
        content=row.get("content", ""),
        published_at=published_at,
        author=row.get("author"),
        fetched_at=fetched_at,
    )

    scores = AnalysisScores(
        sentiment=row.get("sentiment", 0.0),
        sensationalism=row.get("sensationalism", 0.0),
        bias=row.get("bias", 0.0),
        signal=row.get("signal", 0.5),
        topics=topics,
    )

    return Article(
        raw=raw,
        scores=scores,
        tldr=row.get("tldr", ""),
        read_time_minutes=row.get("read_time_minutes", 5),
        analyzed_at=analyzed_at,
    )


def fetch_and_process_source(source: Source) -> Result[list[Article], str]:
    """Fetch and analyze all articles from a source.

    Args:
        source: The source to fetch from.

    Returns:
        Result containing list of processed Articles.
    """
    # Fetch RSS
    fetch_result = fetch_rss(source)
    if isinstance(fetch_result, Err):
        return err(f"Fetch failed: {fetch_result.error.message}")

    raw_articles = fetch_result.value

    # Analyze each article
    articles = [analyze_article(raw) for raw in raw_articles]

    return ok(articles)


def refresh_source(db: Database, source: Source) -> Result[int, str]:
    """Fetch, analyze, and store articles from a source.

    Args:
        db: Database connection.
        source: The source to refresh.

    Returns:
        Result containing count of articles processed.
    """
    result = fetch_and_process_source(source)
    if isinstance(result, Err):
        return result

    articles = result.value
    stored = 0

    for article in articles:
        db_dict = article_to_db_dict(article)
        store_result = store_article(db, db_dict)
        if isinstance(store_result, Ok):
            stored += 1

    return ok(stored)


def get_articles_for_display(db: Database, limit: int = 50) -> list[Article]:
    """Get recent articles from database for TUI display.

    Args:
        db: Database connection.
        limit: Maximum articles to return.

    Returns:
        List of Article objects ready for display.
    """
    result = get_recent_articles(db, limit=limit)
    if isinstance(result, Err):
        return []

    rows = result.value
    return [db_dict_to_article(row) for row in rows if row.get("analyzed_at")]
