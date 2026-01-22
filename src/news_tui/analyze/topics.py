"""Topic extraction for news-tui.

This module extracts topics from article content using keyword-based
extraction (Phase 1) with plans for LDA/BERTopic in later phases.
"""

import re
from collections import Counter

from news_tui.core.types import TopicTag

# Topic keywords mapped to canonical tags
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "ai": [
        "artificial intelligence", "machine learning", "deep learning",
        "neural network", "gpt", "llm", "chatgpt", "openai", "anthropic",
        "transformer", "diffusion", "generative ai",
    ],
    "tech": [
        "software", "programming", "developer", "startup", "silicon valley",
        "google", "apple", "microsoft", "amazon", "meta", "facebook",
    ],
    "crypto": [
        "cryptocurrency", "bitcoin", "ethereum", "blockchain", "defi",
        "nft", "web3", "stablecoin", "usdc", "usdt",
    ],
    "finance": [
        "stock", "market", "investment", "hedge fund", "wall street",
        "fed", "interest rate", "inflation", "economy", "gdp",
    ],
    "politics": [
        "election", "congress", "senate", "president", "democrat",
        "republican", "policy", "legislation", "government",
    ],
    "science": [
        "research", "study", "scientist", "physics", "biology",
        "chemistry", "climate", "space", "nasa", "cern",
    ],
    "culture": [
        "art", "music", "film", "book", "literature", "philosophy",
        "society", "social", "trend",
    ],
}


def extract_topics(text: str, max_topics: int = 5) -> tuple[TopicTag, ...]:
    """Extract topic tags from text using keyword matching.

    This is a simple keyword-based approach for Phase 1.
    Later phases will use LDA or BERTopic for better clustering.

    Args:
        text: The text to analyze.
        max_topics: Maximum number of topics to return.

    Returns:
        Tuple of TopicTag strings.
    """
    if not text.strip():
        return ()

    text_lower = text.lower()
    topic_scores: Counter[str] = Counter()

    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            # Count occurrences of each keyword
            count = len(re.findall(r"\b" + re.escape(keyword) + r"\b", text_lower))
            if count > 0:
                topic_scores[topic] += count

    # Return top topics
    top_topics = topic_scores.most_common(max_topics)
    return tuple(TopicTag(topic) for topic, _ in top_topics if topic)


def topic_overlap(topics1: tuple[TopicTag, ...], topics2: tuple[TopicTag, ...]) -> float:
    """Calculate overlap between two topic sets.

    Used for topic drift detection.

    Args:
        topics1: First set of topics.
        topics2: Second set of topics.

    Returns:
        Jaccard similarity (0.0 to 1.0).
    """
    if not topics1 and not topics2:
        return 1.0  # Both empty = same
    if not topics1 or not topics2:
        return 0.0  # One empty = no overlap

    set1 = set(topics1)
    set2 = set(topics2)

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0
