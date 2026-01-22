"""Information quality/signal analysis for news-tui.

This module computes a "signal" score measuring information density:
- How much unique information per word?
- Is this content-dense or fluff?
"""

import re
from collections import Counter

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
])


def compute_signal_score(text: str, article_id: str = "") -> Result[float, AnalysisError]:
    """Compute information density score for text.

    Uses a combination of:
    - Unique word ratio (vocabulary richness)
    - Average word length (longer words tend to be more specific)
    - Proper noun density (names, places = specific info)

    Args:
        text: The text to analyze.
        article_id: Article ID for error reporting.

    Returns:
        Result containing signal score (0.0 to 1.0).
        Higher = more information-dense.
    """
    if not text.strip():
        return ok(0.5)  # Empty text is neutral

    # Tokenize (simple word split)
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

    if len(words) < 10:
        return ok(0.5)  # Too short to analyze meaningfully

    # Filter stop words for content analysis
    content_words = [w for w in words if w not in STOP_WORDS]

    if not content_words:
        return ok(0.2)  # All stop words = low signal

    # 1. Vocabulary richness (unique words / total words)
    unique_ratio = len(set(content_words)) / len(content_words)

    # 2. Average word length (normalized to 0-1 scale)
    avg_length = sum(len(w) for w in content_words) / len(content_words)
    length_score = min(avg_length / 10.0, 1.0)  # Cap at 10 chars

    # 3. Capitalized word ratio (potential proper nouns)
    original_words = re.findall(r"\b[A-Za-z]+\b", text)
    cap_words = [w for w in original_words if w[0].isupper() and w.lower() not in STOP_WORDS]
    cap_ratio = len(cap_words) / len(original_words) if original_words else 0

    # Combine scores (weighted average)
    signal = (unique_ratio * 0.4) + (length_score * 0.3) + (cap_ratio * 0.3)

    # Normalize to 0-1 range
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
