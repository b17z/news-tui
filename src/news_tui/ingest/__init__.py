"""Data ingestion layer for news-tui.

This module handles fetching content from various sources:
- RSS/Atom feeds
- Hacker News API
- Lobste.rs

All fetched data is validated through Pydantic models before being
passed to the analysis layer.
"""

from news_tui.ingest.rss import fetch_rss
from news_tui.ingest.sources import load_sources

__all__ = [
    "fetch_rss",
    "load_sources",
]
