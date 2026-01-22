"""Markov chain implementation for text generation.

This module implements n-gram Markov chains for generating
impressionistic summaries of article content. The goal is
to capture the "voice" of a source rather than semantic accuracy.

This is a from-scratch implementation for learning purposes.
"""

import random
import re
from collections import defaultdict

# Type aliases for clarity
MarkovChain = dict[tuple[str, ...], list[str]]


def build_chain(text: str, n: int = 2) -> MarkovChain:
    """Build an n-gram Markov chain from input text.

    Args:
        text: Input text to build chain from.
        n: Size of n-gram (default 2 for bigrams).

    Returns:
        Dictionary mapping n-gram tuples to list of possible
        next words.

    Example:
        >>> chain = build_chain("the cat sat on the mat", n=2)
        >>> chain[("the", "cat")]
        ['sat']
        >>> chain[("on", "the")]
        ['mat']
    """
    if n < 1:
        raise ValueError("n must be at least 1")

    # Tokenize: split on whitespace, preserving punctuation as separate tokens
    words = _tokenize(text)

    if len(words) <= n:
        return {}

    chain: dict[tuple[str, ...], list[str]] = defaultdict(list)

    for i in range(len(words) - n):
        key = tuple(words[i : i + n])
        next_word = words[i + n]
        chain[key].append(next_word)

    return dict(chain)


def generate(
    chain: MarkovChain,
    seed: tuple[str, ...] | None = None,
    max_words: int = 50,
    rng: random.Random | None = None,
) -> str:
    """Generate text from a Markov chain.

    Args:
        chain: Markov chain dictionary from build_chain().
        seed: Starting n-gram (random if None).
        max_words: Maximum words to generate.
        rng: Random number generator (for reproducibility in tests).

    Returns:
        Generated text string.

    Raises:
        ValueError: If chain is empty.

    Example:
        >>> chain = build_chain("the cat sat on the mat on the floor", n=2)
        >>> rng = random.Random(42)
        >>> text = generate(chain, max_words=10, rng=rng)
        >>> print(text)  # Will be reproducible with same seed
    """
    if not chain:
        raise ValueError("Cannot generate from empty chain")

    rng = rng or random.Random()

    # Choose random seed if not provided
    if seed is None:
        seed = rng.choice(list(chain.keys()))

    n = len(seed)
    words = list(seed)

    for _ in range(max_words - n):
        key = tuple(words[-n:])
        if key not in chain:
            break
        next_word = rng.choice(chain[key])
        words.append(next_word)

    return _detokenize(words)


def generate_tldr(text: str, max_words: int = 50, n: int = 2) -> str:
    """Generate a TL;DR summary using Markov chains.

    Convenience function that builds a chain and generates text.

    Args:
        text: Source text to summarize.
        max_words: Maximum words in output.
        n: N-gram size for chain.

    Returns:
        Generated summary text, or empty string if text is too short.
    """
    chain = build_chain(text, n=n)
    if not chain:
        return ""

    return generate(chain, max_words=max_words)


def _tokenize(text: str) -> list[str]:
    """Tokenize text into words and punctuation.

    Preserves sentence boundaries by keeping punctuation as tokens.

    Args:
        text: Text to tokenize.

    Returns:
        List of tokens.
    """
    # Split on whitespace but keep punctuation attached, then separate
    # punctuation into its own tokens
    tokens: list[str] = []

    # Match words (with optional trailing punctuation) and standalone punctuation
    pattern = r"[\w']+|[.,!?;:\"\-\(\)]"
    matches = re.findall(pattern, text)

    for match in matches:
        tokens.append(match.lower())

    return tokens


def _detokenize(tokens: list[str]) -> str:
    """Convert tokens back to readable text.

    Handles punctuation spacing properly.

    Args:
        tokens: List of tokens.

    Returns:
        Readable text string.
    """
    if not tokens:
        return ""

    result: list[str] = []
    no_space_before = {".", ",", "!", "?", ";", ":", ")", '"'}
    no_space_after = {"(", '"'}

    for i, token in enumerate(tokens):
        if i == 0:
            result.append(token.capitalize())
        elif token in no_space_before:
            result.append(token)
        elif i > 0 and tokens[i - 1] in no_space_after:
            result.append(token)
        else:
            result.append(" " + token)

    text = "".join(result)

    # Ensure ends with period if doesn't end with punctuation
    if text and text[-1] not in ".!?":
        text += "..."

    return text


def merge_chains(chains: list[MarkovChain]) -> MarkovChain:
    """Merge multiple Markov chains into one.

    Useful for combining chains from multiple articles of the same source
    to capture overall source "voice".

    Args:
        chains: List of Markov chains to merge.

    Returns:
        Single merged chain.
    """
    merged: dict[tuple[str, ...], list[str]] = defaultdict(list)

    for chain in chains:
        for key, words in chain.items():
            merged[key].extend(words)

    return dict(merged)


def chain_entropy(chain: MarkovChain) -> float:
    """Calculate the average entropy (unpredictability) of a chain.

    Higher entropy = more creative/chaotic output.
    Lower entropy = more repetitive/predictable output.

    Args:
        chain: Markov chain to analyze.

    Returns:
        Average entropy across all states (0.0 if empty).
    """
    if not chain:
        return 0.0

    import math

    total_entropy = 0.0

    for words in chain.values():
        if len(words) <= 1:
            continue  # No entropy with single option

        # Count word frequencies
        total = len(words)
        counts: dict[str, int] = {}
        for w in words:
            counts[w] = counts.get(w, 0) + 1

        # Calculate entropy for this state
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)

        total_entropy += entropy

    return total_entropy / len(chain) if chain else 0.0
