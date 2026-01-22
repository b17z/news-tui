"""Persistence layer for news-tui.

This module handles all data storage:
- SQLite database operations
- Read history tracking
- Topic drift detection
- Narrative time series
"""

from news_tui.track.db import init_db, get_connection

__all__ = [
    "init_db",
    "get_connection",
]
