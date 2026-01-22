"""Generation layer for news-tui.

This module handles generating content:
- Markov chain TL;DR summaries
- Narrative predictions
- Diversification suggestions
"""

from news_tui.generate.markov import build_chain, generate

__all__ = [
    "build_chain",
    "generate",
]
