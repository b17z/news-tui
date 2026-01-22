"""Unit tests for topic extraction.

Tests the keyword-based topic extraction functions.
"""

import pytest

from news_tui.analyze.topics import extract_topics, topic_overlap
from news_tui.core.types import TopicTag


class TestExtractTopics:
    """Tests for extract_topics function."""

    def test_extracts_ai_topics(self):
        """Test extraction of AI-related topics."""
        text = """
        Artificial intelligence and machine learning continue to advance.
        New deep learning models show promising results. GPT and LLM
        technologies are transforming the industry.
        """
        topics = extract_topics(text)

        assert TopicTag("ai") in topics

    def test_extracts_tech_topics(self):
        """Test extraction of tech-related topics."""
        text = """
        Google and Apple announced new software products.
        Startup founders in Silicon Valley are excited about the
        programming tools for developers.
        """
        topics = extract_topics(text)

        assert TopicTag("tech") in topics

    def test_extracts_finance_topics(self):
        """Test extraction of finance-related topics."""
        text = """
        The stock market saw significant gains today. Wall Street
        analysts predict continued investment growth. The Fed's
        interest rate decision impacts the economy.
        """
        topics = extract_topics(text)

        assert TopicTag("finance") in topics

    def test_extracts_multiple_topics(self):
        """Test extraction of multiple topics from mixed content."""
        text = """
        Tech companies are investing in AI research. Google's machine
        learning division is exploring applications in finance and
        stock market prediction.
        """
        topics = extract_topics(text)

        assert len(topics) >= 2

    def test_empty_text_returns_empty(self):
        """Test that empty text returns no topics."""
        topics = extract_topics("")
        assert topics == ()

    def test_respects_max_topics(self):
        """Test that max_topics limit is respected."""
        text = """
        AI tech crypto finance politics science culture philosophy.
        Machine learning software bitcoin stock election research art ideas.
        """
        topics = extract_topics(text, max_topics=3)

        assert len(topics) <= 3

    def test_returns_tuple(self):
        """Test that result is an immutable tuple."""
        topics = extract_topics("AI and machine learning are advancing.")
        assert isinstance(topics, tuple)


class TestTopicOverlap:
    """Tests for topic_overlap function."""

    def test_identical_topics(self):
        """Test overlap of identical topic sets."""
        topics = (TopicTag("ai"), TopicTag("tech"))
        overlap = topic_overlap(topics, topics)

        assert overlap == 1.0

    def test_no_overlap(self):
        """Test completely different topic sets."""
        topics1 = (TopicTag("ai"), TopicTag("tech"))
        topics2 = (TopicTag("finance"), TopicTag("politics"))
        overlap = topic_overlap(topics1, topics2)

        assert overlap == 0.0

    def test_partial_overlap(self):
        """Test partial overlap between topic sets."""
        topics1 = (TopicTag("ai"), TopicTag("tech"), TopicTag("science"))
        topics2 = (TopicTag("ai"), TopicTag("finance"))
        overlap = topic_overlap(topics1, topics2)

        # Jaccard: |{ai}| / |{ai, tech, science, finance}| = 1/4 = 0.25
        assert overlap == 0.25

    def test_empty_topics(self):
        """Test overlap with empty topic sets."""
        topics = (TopicTag("ai"),)

        # Both empty = same
        assert topic_overlap((), ()) == 1.0

        # One empty = no overlap
        assert topic_overlap(topics, ()) == 0.0
        assert topic_overlap((), topics) == 0.0
