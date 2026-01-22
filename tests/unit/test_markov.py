"""Unit tests for Markov chain implementation.

Tests the core Markov chain building and generation functions.
"""

import random

import pytest

from news_tui.generate.markov import (
    build_chain,
    generate,
    generate_tldr,
    merge_chains,
    chain_entropy,
    _tokenize,
    _detokenize,
)


class TestBuildChain:
    """Tests for build_chain function."""

    def test_build_chain_creates_valid_transitions(self):
        """Test that build_chain produces correct n-gram mappings."""
        text = "the cat sat on the mat"
        chain = build_chain(text, n=2)

        assert ("the", "cat") in chain
        assert chain[("the", "cat")] == ["sat"]
        assert ("on", "the") in chain
        assert chain[("on", "the")] == ["mat"]

    def test_build_chain_handles_empty_text(self):
        """Test graceful handling of empty input."""
        chain = build_chain("")
        assert chain == {}

    def test_build_chain_handles_short_text(self):
        """Test handling of text shorter than n-gram size."""
        chain = build_chain("hello", n=2)
        assert chain == {}

    def test_build_chain_with_unigrams(self):
        """Test building unigram (n=1) chains."""
        text = "a b a c a b"
        chain = build_chain(text, n=1)

        assert ("a",) in chain
        # "a" is followed by "b", "c", "b"
        assert sorted(chain[("a",)]) == ["b", "b", "c"]

    def test_build_chain_with_trigrams(self):
        """Test building trigram (n=3) chains."""
        text = "one two three four five"
        chain = build_chain(text, n=3)

        assert ("one", "two", "three") in chain
        assert chain[("one", "two", "three")] == ["four"]

    def test_build_chain_preserves_duplicates(self):
        """Test that duplicate transitions are preserved for probability."""
        text = "a b a b a b c"
        chain = build_chain(text, n=1)

        # "a" is followed by "b" twice, so "b" should appear twice
        assert chain[("a",)].count("b") == 3

    def test_build_chain_invalid_n_raises(self):
        """Test that n < 1 raises ValueError."""
        with pytest.raises(ValueError, match="n must be at least 1"):
            build_chain("hello world", n=0)


class TestGenerate:
    """Tests for generate function."""

    def test_generate_produces_text(self):
        """Test that generate produces non-empty text."""
        chain = build_chain("the cat sat on the mat on the floor", n=2)
        text = generate(chain, max_words=10)

        assert text
        assert isinstance(text, str)

    def test_generate_with_seed(self):
        """Test that providing a seed works."""
        chain = build_chain("the cat sat on the mat", n=2)
        text = generate(chain, seed=("the", "cat"), max_words=5)

        # Should start with "the cat"
        assert text.lower().startswith("the cat")

    def test_generate_is_reproducible_with_rng(self):
        """Test that same RNG seed produces same output."""
        chain = build_chain("the cat sat on the mat on the floor on the bed", n=2)

        rng1 = random.Random(42)
        rng2 = random.Random(42)

        text1 = generate(chain, max_words=10, rng=rng1)
        text2 = generate(chain, max_words=10, rng=rng2)

        assert text1 == text2

    def test_generate_respects_max_words(self):
        """Test that output doesn't exceed max_words."""
        chain = build_chain("a b c d e f g h i j k l m n o p", n=1)
        text = generate(chain, max_words=5)

        # Count words (roughly - tokenization may affect this slightly)
        word_count = len(text.split())
        assert word_count <= 6  # Allow small margin for punctuation

    def test_generate_empty_chain_raises(self):
        """Test that empty chain raises ValueError."""
        with pytest.raises(ValueError, match="Cannot generate from empty chain"):
            generate({})

    def test_generate_stops_at_dead_end(self):
        """Test that generation stops gracefully at dead ends."""
        # Chain that leads to dead end
        chain = {("a", "b"): ["c"], ("b", "c"): ["d"]}
        text = generate(chain, seed=("a", "b"), max_words=100)

        # Should stop when no valid next word
        assert text


class TestTokenization:
    """Tests for tokenization functions."""

    def test_tokenize_splits_words(self):
        """Test basic word splitting."""
        tokens = _tokenize("hello world")
        assert tokens == ["hello", "world"]

    def test_tokenize_handles_punctuation(self):
        """Test that punctuation is separated."""
        tokens = _tokenize("hello, world!")
        assert "," in tokens
        assert "!" in tokens

    def test_tokenize_lowercases(self):
        """Test that tokens are lowercased."""
        tokens = _tokenize("Hello WORLD")
        assert "hello" in tokens
        assert "world" in tokens

    def test_detokenize_capitalizes_first(self):
        """Test that first word is capitalized."""
        text = _detokenize(["hello", "world"])
        assert text.startswith("Hello")

    def test_detokenize_handles_punctuation(self):
        """Test punctuation spacing in detokenization."""
        text = _detokenize(["hello", ",", "world", "!"])
        assert ", " in text or ",world" in text.lower()


class TestMergeChains:
    """Tests for chain merging."""

    def test_merge_combines_transitions(self):
        """Test that merging combines transition lists."""
        chain1 = {("a",): ["b", "c"]}
        chain2 = {("a",): ["d", "e"]}

        merged = merge_chains([chain1, chain2])

        assert ("a",) in merged
        assert set(merged[("a",)]) == {"b", "c", "d", "e"}

    def test_merge_preserves_unique_keys(self):
        """Test that unique keys from each chain are preserved."""
        chain1 = {("a",): ["b"]}
        chain2 = {("x",): ["y"]}

        merged = merge_chains([chain1, chain2])

        assert ("a",) in merged
        assert ("x",) in merged


class TestChainEntropy:
    """Tests for entropy calculation."""

    def test_entropy_zero_for_deterministic(self):
        """Test that deterministic chain has zero entropy."""
        # Each state has only one possible next word
        chain = {("a",): ["b"], ("b",): ["c"]}
        entropy = chain_entropy(chain)

        assert entropy == 0.0

    def test_entropy_positive_for_random(self):
        """Test that non-deterministic chain has positive entropy."""
        # Each state has multiple possible next words
        chain = {("a",): ["b", "c", "d"]}
        entropy = chain_entropy(chain)

        assert entropy > 0

    def test_entropy_empty_chain(self):
        """Test entropy of empty chain."""
        assert chain_entropy({}) == 0.0


class TestGenerateTldr:
    """Tests for the convenience TL;DR function."""

    def test_generate_tldr_produces_output(self):
        """Test that generate_tldr works end-to-end."""
        text = "The cat sat on the mat. The dog ran in the park. The cat and dog played."
        tldr = generate_tldr(text, max_words=20)

        assert tldr
        assert isinstance(tldr, str)

    def test_generate_tldr_empty_text(self):
        """Test generate_tldr with empty text."""
        tldr = generate_tldr("", max_words=20)
        assert tldr == ""

    def test_generate_tldr_short_text(self):
        """Test generate_tldr with text too short for chain."""
        tldr = generate_tldr("hello", max_words=20)
        assert tldr == ""
