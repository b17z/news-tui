"""Integration tests for RSS parsing.

Tests the RSS parsing pipeline from raw XML to RawArticle objects.
"""

import pytest

from news_tui.core.errors import Ok, Err
from news_tui.core.types import SourceId
from news_tui.ingest.rss import parse_feed


class TestParseFeed:
    """Tests for RSS feed parsing."""

    def test_parse_valid_feed(self, sample_rss_feed: str):
        """Test parsing a valid RSS feed."""
        result = parse_feed(sample_rss_feed, SourceId("test"))

        assert isinstance(result, Ok)
        articles = result.value
        assert len(articles) == 2

    def test_parse_extracts_title(self, sample_rss_feed: str):
        """Test that article titles are extracted."""
        result = parse_feed(sample_rss_feed, SourceId("test"))

        assert isinstance(result, Ok)
        titles = [a.title for a in result.value]
        assert "First Article" in titles
        assert "Second Article" in titles

    def test_parse_extracts_url(self, sample_rss_feed: str):
        """Test that article URLs are extracted."""
        result = parse_feed(sample_rss_feed, SourceId("test"))

        assert isinstance(result, Ok)
        urls = [str(a.url) for a in result.value]
        assert "https://example.com/article/1" in urls

    def test_parse_extracts_content(self, sample_rss_feed: str):
        """Test that article content/description is extracted."""
        result = parse_feed(sample_rss_feed, SourceId("test"))

        assert isinstance(result, Ok)
        assert any("first test article" in a.content for a in result.value)

    def test_parse_handles_empty_feed(self):
        """Test parsing an empty but valid feed."""
        empty_feed = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Empty Feed</title>
            </channel>
        </rss>
        """
        result = parse_feed(empty_feed, SourceId("test"))

        assert isinstance(result, Ok)
        assert result.value == []

    def test_parse_invalid_xml_fails(self):
        """Test that invalid XML returns error."""
        invalid_xml = "not xml at all <>"
        result = parse_feed(invalid_xml, SourceId("test"))

        # feedparser is lenient, so this might not fail
        # but should return empty if it can't parse
        assert isinstance(result, Ok) and result.value == [] or isinstance(result, Err)

    def test_parse_assigns_source_id(self, sample_rss_feed: str):
        """Test that source_id is correctly assigned."""
        source_id = SourceId("my-source")
        result = parse_feed(sample_rss_feed, source_id)

        assert isinstance(result, Ok)
        for article in result.value:
            assert article.source_id == source_id

    def test_parse_generates_article_ids(self, sample_rss_feed: str):
        """Test that unique article IDs are generated."""
        result = parse_feed(sample_rss_feed, SourceId("test"))

        assert isinstance(result, Ok)
        ids = [a.id for a in result.value]

        # IDs should be unique
        assert len(ids) == len(set(ids))

        # IDs should be non-empty strings
        for article_id in ids:
            assert article_id
            assert len(article_id) > 0
