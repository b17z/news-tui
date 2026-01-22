"""Main Textual TUI application for news-tui.

This module defines the main application class and screen navigation.
"""

import webbrowser
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, Markdown, Static

from news_tui.core.config import Config, get_db_path, get_sources_path, load_config
from news_tui.core.errors import Err, Ok
from news_tui.core.types import Article
from news_tui.ui.styles import APP_CSS, get_score_class


def format_score_indicator(label: str, score: float, inverted: bool = False) -> str:
    """Format a score as a colored indicator with numeric value.

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

    # Build bar (10 segments for better granularity)
    filled = int(display_score * 10)
    bar = "█" * filled + "░" * (10 - filled)

    # Show numeric value for precision
    return f"[#c4b5fd]{label}[/#c4b5fd] [{color}]{bar}[/{color}] [dim]{score:+.2f}[/dim]"


def format_article_scores(article: Article) -> str:
    """Format all article scores for display.

    Args:
        article: The article to format scores for.

    Returns:
        Formatted score summary string.
    """
    sen = format_score_indicator("SEN", article.scores.sentiment)
    sig = format_score_indicator("SIG", article.scores.signal)

    # Topic tags with cyberpunk colors
    topic_colors = {"ai": "#c084fc", "tech": "#60a5fa", "crypto": "#fbbf24",
                    "finance": "#34d399", "science": "#22d3ee", "culture": "#f472b6"}
    topics_formatted = []
    for t in article.scores.topics[:3]:
        color = topic_colors.get(t.lower(), "#7c7c9a")
        topics_formatted.append(f"[{color}]#{t}[/{color}]")
    topics = " ".join(topics_formatted)

    return f"{sen} {sig} {topics}"


class ArticleListItem(ListItem):
    """A single article in the list view with TL;DR."""

    def __init__(self, article: Article, **kwargs) -> None:
        super().__init__(**kwargs)
        self.article = article

    def compose(self) -> ComposeResult:
        title = self.article.title[:70] + "..." if len(self.article.title) > 70 else self.article.title
        yield Label(f"[bold #c4b5fd]{title}[/bold #c4b5fd]")

        source = self.article.source_id
        time = f"{self.article.read_time_minutes}m"

        yield Label(f"[#7c7c9a]{source}[/#7c7c9a] [#8b5cf6]•[/#8b5cf6] [#a78bfa]{time}[/#a78bfa]", classes="article-meta")

        # Scores on separate line for better readability
        scores = format_article_scores(self.article)
        yield Label(scores, classes="article-meta")

        # TL;DR preview
        if self.article.tldr:
            tldr_preview = self.article.tldr[:100] + "..." if len(self.article.tldr) > 100 else self.article.tldr
            yield Label(f"[#7c7c9a italic]\"{tldr_preview}\"[/#7c7c9a italic]", classes="article-tldr")


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


ARTICLE_DETAIL_CSS = """
ArticleDetailScreen {
    background: #13131f;
}

#article-detail-container {
    background: #13131f;
    padding: 1 2;
}

#article-detail-container > Label {
    margin-bottom: 1;
}

.detail-title {
    text-style: bold;
    color: #c4b5fd;
    margin-bottom: 1;
}

.detail-meta {
    color: #7c7c9a;
    margin-bottom: 1;
}

.detail-scores {
    margin-bottom: 1;
}

.detail-tldr {
    background: #1a1a2e;
    padding: 1;
    margin: 1 0;
    border: round #8b5cf6;
}

.detail-content {
    color: #e4e4f0;
    padding: 1 0;
}
"""


class ArticleDetailScreen(Screen):
    """Screen showing full article details."""

    CSS = ARTICLE_DETAIL_CSS

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
        Binding("o", "open_browser", "Browser"),
        Binding("j", "scroll_down", "Down", show=False),
        Binding("k", "scroll_up", "Up", show=False),
    ]

    def __init__(self, article: Article, **kwargs) -> None:
        super().__init__(**kwargs)
        self.article = article

    def compose(self) -> ComposeResult:
        yield Header()

        with ScrollableContainer(id="article-detail-container"):
            # Title
            yield Label(f"[bold #c4b5fd]{self.article.title}[/bold #c4b5fd]", classes="detail-title")

            # Meta info
            source = self.article.source_id
            time = f"{self.article.read_time_minutes} min read"
            yield Label(f"[#7c7c9a]{source} • {time}[/#7c7c9a]", classes="detail-meta")

            # Scores
            scores = format_article_scores(self.article)
            yield Label(scores, classes="detail-scores")

            # TL;DR section
            if self.article.tldr:
                yield Label("[bold #a78bfa]TL;DR[/bold #a78bfa]")
                yield Label(f"[#e4e4f0 italic]{self.article.tldr}[/#e4e4f0 italic]", classes="detail-tldr")

            # Content
            yield Label("[bold #a78bfa]Content[/bold #a78bfa]")
            content = self.article.raw.content or "No content available."
            yield Label(f"[#e4e4f0]{content}[/#e4e4f0]", classes="detail-content")

            # URL
            yield Label(f"\n[dim]URL: {self.article.url}[/dim]")

        yield Footer()

    def action_go_back(self) -> None:
        """Go back to the article list."""
        self.app.pop_screen()

    def action_open_browser(self) -> None:
        """Open article in browser."""
        webbrowser.open(str(self.article.url))
        self.notify(f"Opening in browser...")

    def action_scroll_down(self) -> None:
        """Scroll down."""
        container = self.query_one("#article-detail-container")
        container.scroll_down()

    def action_scroll_up(self) -> None:
        """Scroll up."""
        container = self.query_one("#article-detail-container")
        container.scroll_up()


class NewsTuiApp(App):
    """The main news-tui application."""

    CSS = APP_CSS
    TITLE = "News-TUI"
    SUB_TITLE = "Mindful News Reader"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "stats", "Stats"),
        Binding("v", "view_article", "View"),
        Binding("o", "open_browser", "Browser"),
        Binding("?", "help", "Help"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "view_article", "View", show=False),
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

    def _get_selected_article(self) -> Article | None:
        """Get the currently selected article."""
        article_list = self.query_one("#article-list", ArticleList)
        if article_list.highlighted_child is None:
            return None

        selected = article_list.highlighted_child
        if isinstance(selected, ArticleListItem):
            return selected.article
        return None

    def action_view_article(self) -> None:
        """View the selected article in the terminal."""
        article = self._get_selected_article()
        if article is None:
            self.notify("No article selected", severity="warning")
            return

        # Show article detail screen
        self.push_screen(ArticleDetailScreen(article))
        self._mark_as_read(article)

    def action_open_browser(self) -> None:
        """Open the selected article in the browser."""
        article = self._get_selected_article()
        if article is None:
            self.notify("No article selected", severity="warning")
            return

        url = str(article.url)
        webbrowser.open(url)
        self.notify(f"Opening in browser: {article.title[:40]}...")
        self._mark_as_read(article)

    def _mark_as_read(self, article: Article) -> None:
        """Mark an article as read in the database."""
        db = self._get_db()
        if db is None:
            return

        from news_tui.track.history import mark_as_read

        mark_as_read(
            db,
            article_id=article.id,
            topics=list(article.scores.topics),
            duration_seconds=None,  # We don't track time yet
        )

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
