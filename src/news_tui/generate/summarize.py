"""Extractive summarization for news-tui.

This module implements TextRank-inspired extractive summarization
for generating TL;DRs from article content. Better for short texts
than Markov chains.
"""

import re
from collections import Counter


def extractive_summary(text: str, max_sentences: int = 2) -> str:
    """Generate a summary by extracting the most important sentences.

    Uses a simplified TextRank approach:
    1. Split into sentences
    2. Score sentences by keyword overlap with other sentences
    3. Pick top-scoring sentences

    Args:
        text: Source text to summarize.
        max_sentences: Maximum sentences to extract.

    Returns:
        Extracted summary string.
    """
    if not text.strip():
        return ""

    # Split into sentences
    sentences = _split_sentences(text)

    if len(sentences) <= max_sentences:
        return text.strip()

    # Score each sentence
    scores = _score_sentences(sentences)

    # Get top sentences (preserving original order)
    sorted_sentences = sorted(
        enumerate(sentences),
        key=lambda x: scores[x[0]],
        reverse=True
    )

    top_indices = sorted([idx for idx, _ in sorted_sentences[:max_sentences]])
    summary_sentences = [sentences[i] for i in top_indices]

    return " ".join(summary_sentences)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences.

    Args:
        text: Text to split.

    Returns:
        List of sentences.
    """
    # Simple sentence splitting on . ! ?
    # Handles common abbreviations
    text = re.sub(r'([.!?])\s+', r'\1|||', text)
    sentences = text.split('|||')

    # Clean up and filter
    sentences = [s.strip() for s in sentences if s.strip()]

    # Filter out very short "sentences" (likely fragments)
    sentences = [s for s in sentences if len(s.split()) >= 3]

    return sentences


def _score_sentences(sentences: list[str]) -> list[float]:
    """Score sentences by importance using keyword overlap.

    Args:
        sentences: List of sentences.

    Returns:
        List of scores (same order as input).
    """
    # Get keywords (non-stop words) for each sentence
    sentence_keywords = [_get_keywords(s) for s in sentences]

    # Build global keyword frequency
    all_keywords: list[str] = []
    for kws in sentence_keywords:
        all_keywords.extend(kws)

    keyword_freq = Counter(all_keywords)

    # Score each sentence
    scores: list[float] = []

    for i, keywords in enumerate(sentence_keywords):
        if not keywords:
            scores.append(0.0)
            continue

        # Score based on:
        # 1. Keyword importance (frequency across document)
        # 2. Position bonus (first sentences often important)
        # 3. Length penalty (too short = less info)

        keyword_score = sum(keyword_freq[kw] for kw in keywords) / len(keywords)

        # Position bonus: first 20% of sentences get boost
        position = i / len(sentences)
        position_bonus = 1.5 if position < 0.2 else 1.0

        # Length factor: prefer medium-length sentences
        word_count = len(sentences[i].split())
        length_factor = min(word_count / 15, 1.0) if word_count < 15 else max(0.5, 1.0 - (word_count - 30) / 50)

        score = keyword_score * position_bonus * length_factor
        scores.append(score)

    return scores


def _get_keywords(text: str) -> list[str]:
    """Extract keywords (non-stop words) from text.

    Args:
        text: Text to extract keywords from.

    Returns:
        List of keywords (lowercased).
    """
    # Simple stop words list
    stop_words = frozenset([
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "to", "of", "in", "for", "on", "with",
        "at", "by", "from", "as", "into", "through", "during", "before", "after",
        "this", "that", "these", "those", "it", "its", "and", "but", "or", "so",
        "if", "then", "than", "too", "very", "just", "also", "about", "such",
        "there", "here", "when", "where", "what", "which", "who", "whom", "how",
        "all", "each", "every", "both", "few", "more", "most", "other", "some",
        "no", "nor", "not", "only", "own", "same", "you", "your", "they", "their",
        "we", "our", "he", "she", "him", "her", "his", "i", "me", "my",
    ])

    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    return [w for w in words if w not in stop_words and len(w) > 2]


def smart_tldr(text: str, max_words: int = 50) -> str:
    """Generate a smart TL;DR using the best method for the text.

    For short texts (< 100 words): Use extractive summary
    For longer texts: Use Markov chains for impressionistic summary

    Args:
        text: Source text to summarize.
        max_words: Maximum words in output.

    Returns:
        Generated TL;DR.
    """
    if not text.strip():
        return ""

    word_count = len(text.split())

    if word_count < 100:
        # Short text: extractive is better
        summary = extractive_summary(text, max_sentences=2)
        # Truncate if needed
        words = summary.split()
        if len(words) > max_words:
            return " ".join(words[:max_words]) + "..."
        return summary
    else:
        # Longer text: Markov can work
        from news_tui.generate.markov import generate_tldr
        result = generate_tldr(text, max_words=max_words)
        if result:
            return result
        # Fallback to extractive
        return extractive_summary(text, max_sentences=2)
