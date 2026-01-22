"""Core types, configuration, and utilities for news-tui.

This module contains shared types, configuration management, and error
handling used throughout the application.
"""

from news_tui.core.errors import Err, NewsTuiError, Ok, Result
from news_tui.core.types import AnalysisScores, Article, RawArticle, Source

__all__ = [
    # Types
    "Article",
    "RawArticle",
    "Source",
    "AnalysisScores",
    # Errors
    "Result",
    "Ok",
    "Err",
    "NewsTuiError",
]
