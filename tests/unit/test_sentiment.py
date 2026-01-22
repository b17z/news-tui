"""Unit tests for sentiment analysis.

Tests the VADER-based sentiment analysis functions.
"""

import pytest

from news_tui.analyze.sentiment import (
    analyze_sentiment,
    sentiment_label,
    analyze_headline_vs_body,
)
from news_tui.core.errors import Ok, Err


class TestAnalyzeSentiment:
    """Tests for analyze_sentiment function."""

    def test_positive_sentiment(self):
        """Test that positive text returns positive score."""
        text = "This is absolutely wonderful, amazing, and fantastic!"
        result = analyze_sentiment(text)

        assert isinstance(result, Ok)
        assert result.value > 0.5

    def test_negative_sentiment(self):
        """Test that negative text returns negative score."""
        text = "This is terrible, awful, and horrible. I hate it."
        result = analyze_sentiment(text)

        assert isinstance(result, Ok)
        assert result.value < -0.5

    def test_neutral_sentiment(self):
        """Test that neutral text returns near-zero score."""
        text = "The meeting is scheduled for 3pm on Tuesday."
        result = analyze_sentiment(text)

        assert isinstance(result, Ok)
        assert -0.3 < result.value < 0.3

    def test_empty_text_returns_neutral(self):
        """Test that empty text returns neutral score."""
        result = analyze_sentiment("")

        assert isinstance(result, Ok)
        assert result.value == 0.0

    def test_whitespace_text_returns_neutral(self):
        """Test that whitespace-only text returns neutral."""
        result = analyze_sentiment("   \n\t  ")

        assert isinstance(result, Ok)
        assert result.value == 0.0

    def test_score_range(self):
        """Test that score is within valid range."""
        texts = [
            "BEST EVER!!!",
            "worst thing in the world",
            "The weather is cloudy today.",
        ]

        for text in texts:
            result = analyze_sentiment(text)
            assert isinstance(result, Ok)
            assert -1.0 <= result.value <= 1.0


class TestSentimentLabel:
    """Tests for sentiment_label function."""

    def test_very_positive(self):
        """Test very positive label."""
        assert sentiment_label(0.7) == "Very positive"

    def test_slightly_positive(self):
        """Test slightly positive label."""
        assert sentiment_label(0.3) == "Slightly positive"

    def test_neutral(self):
        """Test neutral label."""
        assert sentiment_label(0.0) == "Neutral"

    def test_slightly_negative(self):
        """Test slightly negative label."""
        assert sentiment_label(-0.3) == "Slightly negative"

    def test_very_negative(self):
        """Test very negative label."""
        assert sentiment_label(-0.7) == "Very negative"


class TestHeadlineVsBody:
    """Tests for headline vs body sentiment comparison."""

    def test_similar_sentiment(self):
        """Test when headline and body have similar sentiment."""
        headline = "Great news about the economy"
        body = "The economy is doing well with positive growth indicators."

        result = analyze_headline_vs_body(headline, body)

        assert isinstance(result, Ok)
        # Difference should be small
        assert abs(result.value) < 0.5

    def test_sensational_headline(self):
        """Test when headline is more extreme than body."""
        headline = "SHOCKING: Everything is TERRIBLE!!!"
        body = "There was a minor issue reported today. Officials are investigating."

        result = analyze_headline_vs_body(headline, body)

        assert isinstance(result, Ok)
        # Headline more negative than body = negative difference
        assert result.value < 0
