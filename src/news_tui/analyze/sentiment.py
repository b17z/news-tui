"""Sentiment analysis for news-tui.

This module provides sentiment analysis using VADER (Valence Aware Dictionary
and sEntiment Reasoner), which is fast and doesn't require ML model loading.

VADER is specifically tuned for social media and news text.
"""

from news_tui.core.errors import AnalysisError, Err, Result, err, ok

# Lazy load nltk to avoid startup cost
_vader_analyzer = None


def _get_vader():
    """Lazy-load the VADER sentiment analyzer."""
    global _vader_analyzer
    if _vader_analyzer is None:
        import nltk
        from nltk.sentiment.vader import SentimentIntensityAnalyzer

        # Download VADER lexicon if needed (first run only)
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon", quiet=True)

        _vader_analyzer = SentimentIntensityAnalyzer()
    return _vader_analyzer


def analyze_sentiment(text: str, article_id: str = "") -> Result[float, AnalysisError]:
    """Analyze the sentiment of text using VADER.

    Args:
        text: The text to analyze (title + content combined works best).
        article_id: Article ID for error reporting.

    Returns:
        Result containing sentiment score (-1.0 to 1.0) on success.
        - Negative values: negative sentiment
        - Zero: neutral
        - Positive values: positive sentiment
    """
    if not text.strip():
        # Empty text is neutral
        return ok(0.0)

    try:
        vader = _get_vader()
        scores = vader.polarity_scores(text)

        # compound score is normalized to -1 to 1
        return ok(scores["compound"])

    except Exception as e:
        return err(AnalysisError(article_id, "sentiment", f"VADER analysis failed: {e}"))


def analyze_headline_vs_body(headline: str, body: str, article_id: str = "") -> Result[float, AnalysisError]:
    """Compare sentiment between headline and body.

    Large differences may indicate sensationalism (emotional headline,
    neutral content).

    Args:
        headline: Article headline.
        body: Article body text.
        article_id: Article ID for error reporting.

    Returns:
        Result containing sentiment difference (headline - body).
        Positive values mean headline is more positive than body.
    """
    headline_result = analyze_sentiment(headline, article_id)
    body_result = analyze_sentiment(body, article_id)

    if isinstance(headline_result, Err):
        return headline_result
    if isinstance(body_result, Err):
        return body_result

    diff = headline_result.value - body_result.value
    return ok(diff)


def sentiment_label(score: float) -> str:
    """Convert sentiment score to human-readable label.

    Args:
        score: Sentiment score (-1.0 to 1.0).

    Returns:
        Human-readable label.
    """
    if score >= 0.5:
        return "Very positive"
    elif score >= 0.2:
        return "Slightly positive"
    elif score >= -0.2:
        return "Neutral"
    elif score >= -0.5:
        return "Slightly negative"
    else:
        return "Very negative"
