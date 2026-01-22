"""RSS/Atom feed parser for news-tui.

This module handles fetching and parsing RSS/Atom feeds into RawArticle objects.

Security notes:
- All parsed content is validated through Pydantic models
- URLs are validated before fetching
- Content is sanitized to prevent XSS (though we're a TUI, be defensive)
- HTML is stripped from content to get clean text
"""

import hashlib
import html
import re
from datetime import datetime
from typing import Sequence

import feedparser
import httpx
from bs4 import BeautifulSoup

from news_tui.core.errors import FetchError, Ok, ParseError, Result, err, ok
from news_tui.core.types import ArticleId, RawArticle, Source, SourceId


def strip_html(content: str) -> str:
    """Strip HTML tags and decode entities from content.

    Args:
        content: Raw HTML content from RSS feed.

    Returns:
        Clean text with HTML removed and entities decoded.
    """
    if not content:
        return ""

    # Use BeautifulSoup to extract text from HTML
    soup = BeautifulSoup(content, "html.parser")

    # Remove script and style elements
    for element in soup(["script", "style", "head", "meta", "link"]):
        element.decompose()

    # Get text content
    text = soup.get_text(separator=" ", strip=True)

    # Decode any remaining HTML entities
    text = html.unescape(text)

    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Remove common RSS attribution patterns
    # "- by Author Read on Source" or "by Author Watch on Source"
    text = re.sub(r"\s*-?\s*by\s+[\w\s()]+\s+(Read|Watch|Listen)\s+on\s+\w+\s*$", "", text, flags=re.IGNORECASE)

    return text


def fetch_rss(source: Source, timeout_seconds: float = 30.0) -> Result[list[RawArticle], FetchError]:
    """Fetch and parse an RSS/Atom feed.

    Args:
        source: The source configuration.
        timeout_seconds: Request timeout.

    Returns:
        Result containing list of RawArticle on success, FetchError on failure.
    """
    try:
        # Fetch the feed
        response = httpx.get(
            str(source.url),
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "news-tui/0.1.0 (https://github.com/be-nvy/news-tui)"},
        )
        response.raise_for_status()

    except httpx.TimeoutException:
        return err(FetchError(source.id, "Request timed out"))
    except httpx.HTTPStatusError as e:
        return err(FetchError(source.id, f"HTTP error: {e}", e.response.status_code))
    except httpx.RequestError as e:
        return err(FetchError(source.id, f"Request failed: {e}"))

    # Parse the feed
    return parse_feed(response.text, source.id)


def parse_feed(content: str, source_id: SourceId) -> Result[list[RawArticle], ParseError]:
    """Parse RSS/Atom feed content into RawArticle objects.

    Args:
        content: The raw feed XML content.
        source_id: The source this feed came from.

    Returns:
        Result containing list of RawArticle on success, ParseError on failure.
    """
    feed = feedparser.parse(content)

    if feed.bozo and feed.bozo_exception:
        # feedparser found issues but may have parsed some content
        # Only fail if we got nothing useful
        if not feed.entries:
            return err(ParseError(source_id, f"Invalid feed: {feed.bozo_exception}"))

    articles: list[RawArticle] = []

    for entry in feed.entries:
        article_result = _parse_entry(entry, source_id)
        if isinstance(article_result, Ok):
            articles.append(article_result.value)
        # Skip invalid entries rather than failing entire feed

    return ok(articles)


def _parse_entry(entry: feedparser.FeedParserDict, source_id: SourceId) -> Result[RawArticle, ParseError]:
    """Parse a single feed entry into a RawArticle.

    Args:
        entry: A feedparser entry dict.
        source_id: The source this came from.

    Returns:
        Result containing RawArticle on success, ParseError on failure.
    """
    # Required: title and link
    raw_title = entry.get("title", "").strip()
    link = entry.get("link", "").strip()

    if not raw_title:
        return err(ParseError(source_id, "Entry missing title"))
    if not link:
        return err(ParseError(source_id, "Entry missing link"))

    # Clean title (some feeds have HTML entities in titles)
    title = html.unescape(raw_title)

    # Generate stable ID from URL
    article_id = _generate_article_id(link)

    # Content: prefer content, fall back to summary
    # Strip HTML to get clean text for analysis
    raw_content = ""
    if "content" in entry and entry.content:
        raw_content = entry.content[0].get("value", "")
    elif "summary" in entry:
        raw_content = entry.get("summary", "")

    content = strip_html(raw_content)

    # Parse published date
    published_at = None
    if "published_parsed" in entry and entry.published_parsed:
        try:
            published_at = datetime(*entry.published_parsed[:6])
        except (TypeError, ValueError):
            pass

    # Author
    author = entry.get("author")

    try:
        article = RawArticle(
            id=article_id,
            source_id=source_id,
            title=title,
            url=link,  # type: ignore[arg-type]  # Pydantic validates
            content=content,
            published_at=published_at,
            author=author,
        )
        return ok(article)
    except ValueError as e:
        return err(ParseError(source_id, f"Invalid entry data: {e}"))


def _generate_article_id(url: str) -> ArticleId:
    """Generate a stable article ID from URL.

    Uses SHA-256 hash of URL to create a unique, stable ID.

    Args:
        url: The article URL.

    Returns:
        A unique ArticleId.
    """
    hash_bytes = hashlib.sha256(url.encode()).hexdigest()[:16]
    return ArticleId(hash_bytes)
