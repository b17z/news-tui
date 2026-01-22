"""Main Textual TUI application for news-tui.

This module defines the main application class and screen navigation.
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header, Static, Label, ListItem, ListView

from news_tui.ui.styles import APP_CSS


class ArticleListItem(ListItem):
    """A single article in the list view."""

    def __init__(self, title: str, source: str, scores_summary: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.source = source
        self.scores_summary = scores_summary

    def compose(self) -> ComposeResult:
        yield Label(f"[bold]{self.title}[/bold]")
        yield Label(f"{self.source} | {self.scores_summary}", classes="article-meta")


class ArticleList(ListView):
    """List of articles with keyboard navigation."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.add_class("article-list")


class MainScreen(Static):
    """Main screen showing article list."""

    def compose(self) -> ComposeResult:
        yield Container(
            Label("[bold]News-TUI[/bold] - Mindful News Reader", classes="header-title"),
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

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield MainScreen()
        yield Footer()

    def action_refresh(self) -> None:
        """Refresh feeds."""
        self.notify("Refreshing feeds...")
        # TODO: Implement feed refresh

    def action_stats(self) -> None:
        """Show reading statistics."""
        self.notify("Stats view coming soon...")
        # TODO: Implement stats screen

    def action_help(self) -> None:
        """Show help."""
        self.notify(
            "Keys: j/k=navigate, enter=open, r=refresh, s=stats, q=quit",
            timeout=5,
        )

    def on_mount(self) -> None:
        """Called when app is mounted."""
        # Load initial articles
        self._load_articles()

    def _load_articles(self) -> None:
        """Load articles into the list."""
        article_list = self.query_one("#article-list", ArticleList)

        # TODO: Load real articles from database
        # For now, show placeholder
        article_list.append(
            ArticleListItem(
                title="Welcome to News-TUI",
                source="System",
                scores_summary="Add some RSS feeds to get started!",
            )
        )


def run_app(debug: bool = False) -> None:
    """Run the TUI application.

    Args:
        debug: Enable debug mode with verbose logging.
    """
    app = NewsTuiApp()
    app.run()
