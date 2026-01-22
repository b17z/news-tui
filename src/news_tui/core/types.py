"""Core data types for news-tui.

This module defines the immutable data structures used throughout the application.
All types are frozen (immutable) to enforce functional programming principles.

Security note: All external data must be validated through these Pydantic models
before being trusted internally. Never bypass validation for user/network data.
"""

from datetime import datetime
from typing import Literal, NewType

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

# Branded types for type safety (prevent mixing up IDs)
ArticleId = NewType("ArticleId", str)
SourceId = NewType("SourceId", str)
TopicTag = NewType("TopicTag", str)


class Source(BaseModel):
    """A news source configuration.

    Attributes:
        id: Unique identifier for the source.
        name: Human-readable name.
        url: Feed URL (RSS/Atom/API endpoint).
        source_type: Type of source for parsing.
        enabled: Whether to fetch from this source.
        bias_rating: Pre-configured bias rating (-1.0 left to 1.0 right).
        reliability_score: Source reliability (0.0 to 1.0).
    """

    model_config = ConfigDict(frozen=True)

    id: SourceId
    name: str = Field(min_length=1, max_length=100)
    url: HttpUrl
    source_type: Literal["rss", "atom", "hn_api", "lobsters"] = "rss"
    enabled: bool = True
    bias_rating: float = Field(default=0.0, ge=-1.0, le=1.0)
    reliability_score: float = Field(default=0.5, ge=0.0, le=1.0)


class RawArticle(BaseModel):
    """An article as fetched from a source, before analysis.

    This represents the raw data from RSS/API before any processing.
    Used as input to the analysis pipeline.

    Attributes:
        id: Unique identifier (typically URL hash or source-provided ID).
        source_id: Which source this came from.
        title: Article headline.
        url: Link to full article.
        content: Article body text (may be summary or full text).
        published_at: Publication timestamp.
        author: Author name if available.
        fetched_at: When we fetched this article.
    """

    model_config = ConfigDict(frozen=True)

    id: ArticleId
    source_id: SourceId
    title: str = Field(min_length=1, max_length=500)
    url: HttpUrl
    content: str = ""
    published_at: datetime | None = None
    author: str | None = None
    fetched_at: datetime = Field(default_factory=datetime.now)


class AnalysisScores(BaseModel):
    """Analysis scores computed for an article.

    All scores are normalized to consistent ranges for display.

    Attributes:
        sentiment: Emotional valence (-1.0 negative to 1.0 positive).
        sensationalism: Headline hype vs content (0.0 substance to 1.0 clickbait).
        bias: Political lean (-1.0 left to 1.0 right).
        signal: Information density (0.0 fluff to 1.0 dense).
        topics: Extracted topic tags.
    """

    model_config = ConfigDict(frozen=True)

    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)
    sensationalism: float = Field(default=0.0, ge=0.0, le=1.0)
    bias: float = Field(default=0.0, ge=-1.0, le=1.0)
    signal: float = Field(default=0.5, ge=0.0, le=1.0)
    topics: tuple[TopicTag, ...] = ()


class Article(BaseModel):
    """A fully processed article ready for display.

    Combines raw article data with analysis scores and generated content.

    Attributes:
        raw: The original article data.
        scores: Computed analysis scores.
        tldr: Generated TL;DR summary.
        read_time_minutes: Estimated reading time.
        analyzed_at: When analysis was performed.
    """

    model_config = ConfigDict(frozen=True)

    raw: RawArticle
    scores: AnalysisScores
    tldr: str = ""
    read_time_minutes: int = Field(default=5, ge=1)
    analyzed_at: datetime = Field(default_factory=datetime.now)

    @property
    def id(self) -> ArticleId:
        """Article ID (delegated to raw)."""
        return self.raw.id

    @property
    def title(self) -> str:
        """Article title (delegated to raw)."""
        return self.raw.title

    @property
    def url(self) -> HttpUrl:
        """Article URL (delegated to raw)."""
        return self.raw.url

    @property
    def source_id(self) -> SourceId:
        """Source ID (delegated to raw)."""
        return self.raw.source_id


class ReadHistoryEntry(BaseModel):
    """A record of an article being read.

    Attributes:
        article_id: Which article was read.
        read_at: When it was read.
        read_duration_seconds: How long user spent (if tracked).
        topics: Topics at time of reading (for drift analysis).
    """

    model_config = ConfigDict(frozen=True)

    article_id: ArticleId
    read_at: datetime = Field(default_factory=datetime.now)
    read_duration_seconds: int | None = None
    topics: tuple[TopicTag, ...] = ()
