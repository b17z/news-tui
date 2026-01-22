"""Unit tests for quality/signal analysis.

Tests the information density scoring functions.
"""

import pytest

from news_tui.analyze.quality import (
    compute_signal_score,
    word_frequency,
    reading_time_minutes,
)
from news_tui.core.errors import Ok


class TestComputeSignalScore:
    """Tests for compute_signal_score function."""

    def test_dense_text_high_score(self):
        """Test that information-dense text gets high score."""
        text = """
        Dr. Sarah Johnson at MIT discovered a novel protein structure
        using cryogenic electron microscopy. The research, published
        in Nature, identifies key binding sites for pharmaceutical
        development targeting Alzheimer's disease pathways.
        """
        result = compute_signal_score(text)

        assert isinstance(result, Ok)
        assert result.value > 0.5

    def test_fluffy_text_low_score(self):
        """Test that low-information text gets lower score."""
        text = """
        Things are really good and nice. We like it a lot.
        It is very good. The thing is that it is nice.
        We think it is good and we like it.
        """
        result = compute_signal_score(text)

        assert isinstance(result, Ok)
        assert result.value < 0.6

    def test_empty_text_neutral(self):
        """Test that empty text returns neutral score."""
        result = compute_signal_score("")

        assert isinstance(result, Ok)
        assert result.value == 0.5

    def test_short_text_neutral(self):
        """Test that very short text returns neutral."""
        result = compute_signal_score("Hello world")

        assert isinstance(result, Ok)
        assert result.value == 0.5

    def test_score_in_valid_range(self):
        """Test that score is always in valid range."""
        texts = [
            "x" * 1000,  # Repetitive
            "The quick brown fox jumps over the lazy dog.",
            "Dr. Smith at Harvard University researched quantum mechanics.",
        ]

        for text in texts:
            result = compute_signal_score(text)
            assert isinstance(result, Ok)
            assert 0.0 <= result.value <= 1.0


class TestWordFrequency:
    """Tests for word_frequency function."""

    def test_counts_content_words(self):
        """Test that content words are counted correctly."""
        text = "apple banana apple cherry apple"
        freq = word_frequency(text)

        assert freq.get("apple", 0) == 3
        assert freq.get("banana", 0) == 1
        assert freq.get("cherry", 0) == 1

    def test_excludes_stop_words(self):
        """Test that stop words are excluded."""
        text = "the quick brown fox and the lazy dog"
        freq = word_frequency(text)

        assert "the" not in freq
        assert "and" not in freq
        assert "quick" in freq

    def test_returns_dict(self):
        """Test that result is a dictionary."""
        freq = word_frequency("hello world hello")
        assert isinstance(freq, dict)


class TestReadingTime:
    """Tests for reading_time_minutes function."""

    def test_short_text(self):
        """Test reading time for short text."""
        text = "Hello world"  # 2 words
        minutes = reading_time_minutes(text)

        assert minutes == 1  # Minimum 1 minute

    def test_medium_text(self):
        """Test reading time for medium text."""
        text = " ".join(["word"] * 400)  # 400 words
        minutes = reading_time_minutes(text)

        assert minutes == 2  # 400/200 = 2

    def test_custom_wpm(self):
        """Test with custom words per minute."""
        text = " ".join(["word"] * 300)  # 300 words
        minutes = reading_time_minutes(text, wpm=100)

        assert minutes == 3  # 300/100 = 3
