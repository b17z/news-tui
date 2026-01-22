"""Information quality/signal analysis for news-tui.

This module computes a "signal" score measuring information density:
- How much unique information per word?
- Is this content-dense or fluff?
- TF-IDF based analysis for better differentiation
"""

import math
import re
from collections import Counter
from functools import lru_cache

from news_tui.core.errors import AnalysisError, Result, ok

# Common stop words to filter out
STOP_WORDS = frozenset([
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "to", "of", "in", "for", "on", "with",
    "at", "by", "from", "as", "into", "through", "during", "before", "after",
    "above", "below", "between", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "just", "and", "but", "if",
    "or", "because", "until", "while", "this", "that", "these", "those",
    "what", "which", "who", "whom", "i", "you", "he", "she", "it", "we", "they",
    "about", "also", "like", "just", "even", "well", "back", "much", "way",
    "say", "said", "says", "one", "two", "first", "new", "now", "time", "year",
])

# High-signal indicator words (technical, specific, informative)
HIGH_SIGNAL_WORDS = frozenset([
    # Technical depth indicators
    "algorithm", "implementation", "architecture", "protocol", "framework",
    "analysis", "methodology", "hypothesis", "theorem", "proof", "evidence",
    "research", "study", "experiment", "data", "statistics", "correlation",
    # Domain specificity
    "cryptographic", "authentication", "latency", "throughput", "scalability",
    "regression", "inference", "optimization", "heuristic", "deterministic",
    # Precision language
    "specifically", "precisely", "approximately", "consequently", "therefore",
    "furthermore", "moreover", "nevertheless", "alternatively", "accordingly",
])

# Low-signal filler words (vague, sensational, clickbait)
LOW_SIGNAL_WORDS = frozenset([
    "amazing", "incredible", "shocking", "unbelievable", "mindblowing",
    "revolutionary", "groundbreaking", "game-changing", "disruptive",
    "literally", "basically", "actually", "really", "totally", "absolutely",
    "stuff", "things", "something", "whatever", "somehow", "everything",
    "everyone", "nobody", "always", "never", "forever",
])


def compute_signal_score(text: str, article_id: str = "") -> Result[float, AnalysisError]:
    """Compute information density score for text.

    Uses a combination of:
    - Vocabulary richness (unique words ratio)
    - Average word length (longer words = more specific)
    - High-signal word presence (technical/precise language)
    - Low-signal word penalty (filler/clickbait language)
    - Sentence complexity (avg words per sentence)

    Args:
        text: The text to analyze.
        article_id: Article ID for error reporting.

    Returns:
        Result containing signal score (0.0 to 1.0).
        Higher = more information-dense.
    """
    if not text.strip():
        return ok(0.5)  # Empty text is neutral

    # Tokenize
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

    if len(words) < 10:
        return ok(0.5)  # Too short to analyze meaningfully

    # Filter stop words for content analysis
    content_words = [w for w in words if w not in STOP_WORDS]

    if not content_words:
        return ok(0.2)  # All stop words = low signal

    total_words = len(words)
    content_count = len(content_words)

    # 1. Vocabulary richness (unique words / total content words)
    unique_ratio = len(set(content_words)) / content_count
    vocab_score = min(unique_ratio * 1.2, 1.0)  # Boost slightly

    # 2. Average word length (normalized to 0-1 scale)
    avg_length = sum(len(w) for w in content_words) / content_count
    length_score = min((avg_length - 3) / 5.0, 1.0)  # 3-8 char range
    length_score = max(0.0, length_score)

    # 3. High-signal word bonus
    high_signal_count = sum(1 for w in content_words if w in HIGH_SIGNAL_WORDS)
    high_signal_ratio = min(high_signal_count / max(content_count / 20, 1), 1.0)

    # 4. Low-signal word penalty
    low_signal_count = sum(1 for w in content_words if w in LOW_SIGNAL_WORDS)
    low_signal_ratio = min(low_signal_count / max(content_count / 10, 1), 1.0)

    # 5. Sentence complexity (words per sentence)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if sentences:
        avg_sentence_len = total_words / len(sentences)
        # Ideal: 15-25 words per sentence
        if 15 <= avg_sentence_len <= 25:
            complexity_score = 1.0
        elif avg_sentence_len < 15:
            complexity_score = avg_sentence_len / 15
        else:
            complexity_score = max(0.5, 1.0 - (avg_sentence_len - 25) / 25)
    else:
        complexity_score = 0.5

    # 6. Content ratio (content words vs total words)
    content_ratio = content_count / total_words

    # Combine scores (weighted)
    signal = (
        vocab_score * 0.25 +
        length_score * 0.15 +
        high_signal_ratio * 0.20 +
        (1.0 - low_signal_ratio) * 0.15 +
        complexity_score * 0.15 +
        content_ratio * 0.10
    )

    # Normalize to 0-1 range with more spread
    signal = max(0.0, min(1.0, signal))

    return ok(signal)


def word_frequency(text: str) -> dict[str, int]:
    """Get word frequency distribution.

    Useful for debugging and understanding content.

    Args:
        text: The text to analyze.

    Returns:
        Dictionary of word -> count.
    """
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    content_words = [w for w in words if w not in STOP_WORDS]
    return dict(Counter(content_words).most_common(50))


def reading_time_minutes(text: str, wpm: int = 200) -> int:
    """Estimate reading time in minutes.

    Args:
        text: The text to analyze.
        wpm: Words per minute (default 200 for average reader).

    Returns:
        Estimated reading time in minutes (minimum 1).
    """
    words = len(text.split())
    minutes = max(1, round(words / wpm))
    return minutes
