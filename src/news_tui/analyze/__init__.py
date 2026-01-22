"""Analysis layer for news-tui.

This module handles computing analysis scores for articles:
- Sentiment analysis
- Topic extraction
- Information quality/signal
- Bias detection
- Sensationalism scoring

All analysis functions are pure functions that take RawArticle
and return AnalysisScores.
"""

from news_tui.analyze.sentiment import analyze_sentiment
from news_tui.analyze.topics import extract_topics
from news_tui.analyze.quality import compute_signal_score

__all__ = [
    "analyze_sentiment",
    "extract_topics",
    "compute_signal_score",
]
