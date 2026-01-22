"""Command-line interface for news-tui.

This module provides the Click CLI entry point with subcommands
for managing feeds, viewing stats, and launching the TUI.
"""

import click

from news_tui import __version__
from news_tui.core.config import load_config, ensure_config_dir, get_sources_path
from news_tui.core.errors import Err


@click.group(invoke_without_command=True)
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option("--version", is_flag=True, help="Show version and exit")
@click.option("--refresh", is_flag=True, help="Refresh feeds before launching")
@click.pass_context
def main(ctx: click.Context, debug: bool, version: bool, refresh: bool) -> None:
    """News-TUI: Mindful terminal news reader.

    Launch without arguments to start the TUI.
    Use subcommands for management tasks.
    """
    if version:
        click.echo(f"news-tui {__version__}")
        return

    # Store config in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug

    # Load configuration
    config_result = load_config()
    if isinstance(config_result, Err):
        click.echo(f"Error loading config: {config_result.error.message}", err=True)
        ctx.exit(1)

    config = config_result.value
    ctx.obj["config"] = config

    # Ensure config directory exists
    ensure_result = ensure_config_dir(config)
    if isinstance(ensure_result, Err):
        click.echo(f"Error: {ensure_result.error.message}", err=True)
        ctx.exit(1)

    # If no subcommand, launch TUI
    if ctx.invoked_subcommand is None:
        if refresh:
            click.echo("Refreshing feeds...")
            # TODO: Implement refresh

        from news_tui.app import run_app
        run_app(debug=debug)


@main.group()
def feeds() -> None:
    """Manage news sources and feeds."""
    pass


@feeds.command("list")
@click.pass_context
def feeds_list(ctx: click.Context) -> None:
    """List configured news sources."""
    from news_tui.ingest.sources import load_sources

    config = ctx.obj["config"]
    sources_path = get_sources_path(config)

    result = load_sources(sources_path)
    if isinstance(result, Err):
        click.echo(f"Error: {result.error.message}", err=True)
        ctx.exit(1)

    sources = result.value

    if not sources:
        click.echo("No sources configured. Use 'news-tui feeds add <url>' to add one.")
        return

    click.echo(f"Configured sources ({len(sources)}):\n")
    for source in sources:
        status = "[enabled]" if source.enabled else "[disabled]"
        click.echo(f"  {source.id}: {source.name} {status}")
        click.echo(f"    URL: {source.url}")
        click.echo(f"    Type: {source.source_type}")
        click.echo()


@feeds.command("add")
@click.argument("url")
@click.option("--name", "-n", help="Display name for the source")
@click.pass_context
def feeds_add(ctx: click.Context, url: str, name: str | None) -> None:
    """Add a new RSS feed source."""
    from news_tui.ingest.sources import load_sources, add_source, save_sources

    config = ctx.obj["config"]
    sources_path = get_sources_path(config)

    # Load existing sources
    result = load_sources(sources_path)
    if isinstance(result, Err):
        click.echo(f"Error: {result.error.message}", err=True)
        ctx.exit(1)

    sources = result.value

    # Generate name from URL if not provided
    if name is None:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        name = parsed.netloc or "Unknown"

    # Add the source
    add_result = add_source(sources, name=name, url=url)
    if isinstance(add_result, Err):
        click.echo(f"Error: {add_result.error.message}", err=True)
        ctx.exit(1)

    new_sources = add_result.value

    # Save back
    save_result = save_sources(new_sources, sources_path)
    if isinstance(save_result, Err):
        click.echo(f"Error: {save_result.error.message}", err=True)
        ctx.exit(1)

    click.echo(f"Added source: {name} ({url})")


@feeds.command("remove")
@click.argument("source_id")
@click.pass_context
def feeds_remove(ctx: click.Context, source_id: str) -> None:
    """Remove a news source by ID."""
    from news_tui.ingest.sources import load_sources, remove_source, save_sources

    config = ctx.obj["config"]
    sources_path = get_sources_path(config)

    # Load existing sources
    result = load_sources(sources_path)
    if isinstance(result, Err):
        click.echo(f"Error: {result.error.message}", err=True)
        ctx.exit(1)

    sources = result.value

    # Remove the source
    remove_result = remove_source(sources, source_id)
    if isinstance(remove_result, Err):
        click.echo(f"Error: {remove_result.error.message}", err=True)
        ctx.exit(1)

    new_sources = remove_result.value

    # Save back
    save_result = save_sources(new_sources, sources_path)
    if isinstance(save_result, Err):
        click.echo(f"Error: {save_result.error.message}", err=True)
        ctx.exit(1)

    click.echo(f"Removed source: {source_id}")


@main.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Show reading statistics."""
    from news_tui.core.config import get_db_path
    from news_tui.track.db import get_connection, init_db
    from news_tui.track.history import get_reading_stats

    config = ctx.obj["config"]
    db_path = get_db_path(config)

    # Get database connection
    conn_result = get_connection(db_path)
    if isinstance(conn_result, Err):
        click.echo(f"Error: {conn_result.error.message}", err=True)
        ctx.exit(1)

    db = conn_result.value
    init_db(db)

    # Get stats
    stats_result = get_reading_stats(db, days=7)
    if isinstance(stats_result, Err):
        click.echo(f"Error: {stats_result.error.message}", err=True)
        ctx.exit(1)

    stats_data = stats_result.value

    click.echo("\nReading Statistics (Last 7 Days)")
    click.echo("=" * 40)
    click.echo(f"Articles read: {stats_data['total_articles']}")
    click.echo(f"Time spent: {stats_data['total_time_minutes']} minutes")
    click.echo(f"Average per day: {stats_data['articles_per_day']:.1f} articles")

    if stats_data["top_topics"]:
        click.echo("\nTop Topics:")
        for topic, count in stats_data["top_topics"][:5]:
            click.echo(f"  #{topic}: {count} articles")


@main.command()
@click.argument("url")
@click.pass_context
def analyze(ctx: click.Context, url: str) -> None:
    """Analyze a single article by URL."""
    click.echo(f"Analyzing: {url}")
    click.echo("(Analysis feature coming soon)")
    # TODO: Implement single article analysis


if __name__ == "__main__":
    main()
