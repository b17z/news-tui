"""Integration tests for the article processing pipeline.

Tests the full flow: fetch → analyze → store → retrieve.
"""

import pytest
from sqlite_utils import Database

from news_tui.core.errors import Ok
from news_tui.core.types import RawArticle, ArticleId, SourceId
from news_tui.pipeline import (
    analyze_article,
    article_to_db_dict,
    db_dict_to_article,
    get_articles_for_display,
)
from news_tui.track.db import store_article


class TestAnalyzeArticle:
    """Tests for article analysis."""

    def test_analyze_produces_scores(self, sample_raw_article: RawArticle):
        """Test that analysis produces valid scores."""
        article = analyze_article(sample_raw_article)

        assert article.id == sample_raw_article.id
        assert article.title == sample_raw_article.title
        assert -1.0 <= article.scores.sentiment <= 1.0
        assert 0.0 <= article.scores.signal <= 1.0
        assert article.read_time_minutes >= 1

    def test_analyze_extracts_topics(self, sample_raw_article: RawArticle):
        """Test that topics are extracted from content."""
        article = analyze_article(sample_raw_article)

        # The sample article mentions AI/ML
        assert len(article.scores.topics) > 0

    def test_analyze_generates_tldr(self, sample_raw_article: RawArticle):
        """Test that TL;DR is generated."""
        article = analyze_article(sample_raw_article)

        assert article.tldr
        assert len(article.tldr) > 0


class TestDatabaseRoundtrip:
    """Tests for article database serialization."""

    def test_article_survives_roundtrip(self, sample_raw_article: RawArticle, test_db: Database):
        """Test that article data survives database storage and retrieval."""
        # Analyze
        article = analyze_article(sample_raw_article)

        # Store
        db_dict = article_to_db_dict(article)
        result = store_article(test_db, db_dict)
        assert isinstance(result, Ok)

        # Retrieve and reconstruct
        from news_tui.track.db import get_article
        get_result = get_article(test_db, article.id)
        assert isinstance(get_result, Ok)
        assert get_result.value is not None

        # Reconstruct
        restored = db_dict_to_article(get_result.value)

        # Verify key fields
        assert restored.id == article.id
        assert restored.title == article.title
        assert restored.scores.sentiment == article.scores.sentiment
        assert restored.scores.signal == article.scores.signal
        assert restored.tldr == article.tldr


class TestGetArticlesForDisplay:
    """Tests for retrieving articles for TUI display."""

    def test_returns_analyzed_articles(self, sample_raw_article: RawArticle, test_db: Database):
        """Test that get_articles_for_display returns articles."""
        # Store an analyzed article
        article = analyze_article(sample_raw_article)
        db_dict = article_to_db_dict(article)
        store_article(test_db, db_dict)

        # Retrieve
        articles = get_articles_for_display(test_db, limit=10)

        assert len(articles) == 1
        assert articles[0].id == article.id

    def test_respects_limit(self, test_db: Database):
        """Test that limit is respected."""
        from datetime import datetime

        # Store multiple articles
        for i in range(5):
            raw = RawArticle(
                id=ArticleId(f"test-{i}"),
                source_id=SourceId("test"),
                title=f"Article {i}",
                url=f"https://example.com/{i}",
                content="Some content here for testing purposes.",
                fetched_at=datetime.now(),
            )
            article = analyze_article(raw)
            store_article(test_db, article_to_db_dict(article))

        # Retrieve with limit
        articles = get_articles_for_display(test_db, limit=3)

        assert len(articles) == 3
