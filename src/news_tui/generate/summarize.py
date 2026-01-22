"""Summarization utilities for news-tui.

Wraps Markov chain generation with article-specific logic.
"""

from news_tui.core.types import Article, RawArticle
from news_tui.generate.markov import generate_tldr


def summarize_article(article: RawArticle, max_words: int = 50) -> str:
    """Generate a TL;DR summary for an article.

    Combines title and content for better context.

    Args:
        article: The article to summarize.
        max_words: Maximum words in summary.

    Returns:
        Generated summary text.
    """
    # Combine title and content for more material
    text = f"{article.title}. {article.content}"

    tldr = generate_tldr(text, max_words=max_words)

    # If too short, just use truncated content
    if len(tldr.split()) < 10:
        words = article.content.split()[:max_words]
        if words:
            tldr = " ".join(words) + "..."

    return tldr
