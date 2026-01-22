"""Main Textual TUI application for news-tui.

This module defines the main application class and screen navigation.
"""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from news_tui.core.config import Config, get_db_path, get_sources_path, load_config
from news_tui.core.errors import Err, Ok
from news_tui.core.types import Article
from news_tui.ui.styles import APP_CSS, get_score_class


def format_score_indicator(label: str, score: float, inverted: bool = False) -> str:
    """Format a score as a colored indicator.

    Args:
        label: Score label (SEN, SNS, etc.)
        score: Score value (-1 to 1 or 0 to 1)
        inverted: If True, low is good (green)

    Returns:
        Rich-formatted score string.
    """
    # Normalize to 0-1 for display
    display_score = (score + 1) / 2 if score < 0 else score

    # Get color class
    css_class = get_score_class(display_score, inverted)
    color = {"score-low": "red", "score-mid": "yellow", "score-high": "green"}[css_class]

    # Build bar
    filled = int(display_score * 5)
    bar = "█" * filled + "░" * (5 - filled)

    return f"[{color}]{label}[/{color}] [{color}]{bar}[/{color}]"


def format_article_scores(article: Article) -> str:
    """Format all article scores for display.

    Args:
        article: The article to format scores for.

    Returns:
        Formatted score summary string.
    """
    sen = format_score_indicator("SEN", article.scores.sentiment)
    sig = format_score_indicator("SIG", article.scores.signal)

    topics = " ".join(f"[dim]#{t}[/dim]" for t in article.scores.topics[:3])

    return f"{sen} {sig} {topics}"


class ArticleListItem(ListItem):
    """A single article in the list view."""

    def __init__(self, article: Article, **kwargs) -> None:
        super().__init__(**kwargs)
        self.article = article

    def compose(self) -> ComposeResult:
        title = self.article.title[:60] + "..." if len(self.article.title) > 60 else self.article.title
        yield Label(f"[bold]{title}[/bold]")

        source = self.article.source_id
        time = f"{self.article.read_time_minutes}m"
        scores = format_article_scores(self.article)

        yield Label(f"[dim]{source}[/dim] • {time} | {scores}", classes="article-meta")


class PlaceholderItem(ListItem):
    """Placeholder when no articles are loaded."""

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.message = message

    def compose(self) -> ComposeResult:
        yield Label(f"[dim]{self.message}[/dim]")


class ArticleList(ListView):
    """List of articles with keyboard navigation."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.add_class("article-list")


class MainScreen(Static):
    """Main screen showing article list."""

    def compose(self) -> ComposeResult:
        yield Container(
            ArticleList(id="article-list"),
            id="main-container",
        )


class NewsTuiApp(App):
    """The main news-tui application."""

    CSS = APP_CSS
    TITLE = "News-TUI"
    SUB_TITLE = "Mindful News Reader"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "stats", "Stats"),
        Binding("?", "help", "Help"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "select", "Open", show=False),
    ]

    def __init__(self, config: Config | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config
        self._db = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield MainScreen()
        yield Footer()

    def _get_db(self):
        """Get or create database connection."""
        if self._db is None:
            from news_tui.track.db import get_connection, init_db

            if self.config is None:
                return None

            db_path = get_db_path(self.config)
            result = get_connection(db_path)
            if isinstance(result, Ok):
                self._db = result.value
                init_db(self._db)

        return self._db

    def action_refresh(self) -> None:
        """Refresh feeds."""
        self.notify("Refreshing feeds...")
        self._refresh_feeds()

    def _refresh_feeds(self) -> None:
        """Fetch and analyze articles from all sources."""
        if self.config is None:
            self.notify("No configuration loaded", severity="error")
            return

        db = self._get_db()
        if db is None:
            self.notify("Cannot connect to database", severity="error")
            return

        from news_tui.ingest.sources import load_sources
        from news_tui.pipeline import refresh_source

        sources_path = get_sources_path(self.config)
        sources_result = load_sources(sources_path)

        if isinstance(sources_result, Err):
            self.notify(f"Cannot load sources: {sources_result.error.message}", severity="error")
            return

        sources = sources_result.value
        total = 0

        for source in sources:
            if not source.enabled:
                continue

            result = refresh_source(db, source)
            if isinstance(result, Ok):
                total += result.value
                self.notify(f"Fetched {result.value} from {source.name}")
            else:
                self.notify(f"Error fetching {source.name}: {result.error}", severity="warning")

        self.notify(f"Refreshed {total} articles total")
        self._load_articles()

    def action_stats(self) -> None:
        """Show reading statistics."""
        self.notify("Stats view coming in Phase 3...")

    def action_help(self) -> None:
        """Show help."""
        self.notify(
            "Keys: j/k=navigate, r=refresh, s=stats, q=quit",
            timeout=5,
        )

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self._load_articles()

    def _load_articles(self) -> None:
        """Load articles from database into the list."""
        article_list = self.query_one("#article-list", ArticleList)
        article_list.clear()

        db = self._get_db()
        if db is None:
            article_list.append(
                PlaceholderItem("No database connection. Check config.")
            )
            return

        from news_tui.pipeline import get_articles_for_display

        articles = get_articles_for_display(db, limit=50)

        if not articles:
            article_list.append(
                PlaceholderItem("No articles yet. Press 'r' to refresh feeds.")
            )
            return

        for article in articles:
            article_list.append(ArticleListItem(article))


def run_app(config: Config | None = None, debug: bool = False) -> None:
    """Run the TUI application.

    Args:
        config: Application configuration.
        debug: Enable debug mode with verbose logging.
    """
    if config is None:
        result = load_config()
        if isinstance(result, Ok):
            config = result.value

    app = NewsTuiApp(config=config)
    app.run()
