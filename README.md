# News-TUI

Mindful terminal news reader with analysis-first consumption.

News is analyzed **before** being presented — sentiment, bias, quality scoring — to prevent doomscrolling and promote epistemic hygiene.

## Philosophy

Instead of feeds optimized for engagement (dopamine hits), this tool optimizes for *informed* engagement. Think Hacker News signal-to-noise ratio meets information diet management.

## Features

- **Analysis Layer**: Every article is scored for sentiment, sensationalism, bias, and signal density before you see it
- **Topic Tracking**: Detects when you're drifting into echo chambers
- **Diversification Nudges**: Gentle reminders to expand your reading horizons
- **Markov TL;DRs**: Impressionistic summaries that capture source "voice"
- **Narrative Tracking**: Follow how stories evolve over time

## Installation

```bash
# From source
git clone https://github.com/be-nvy/news-tui.git
cd news-tui
pip install -e ".[dev]"
```

## Usage

```bash
# Launch the TUI
news-tui

# With feed refresh
news-tui --refresh

# Manage sources
news-tui feeds list
news-tui feeds add https://example.com/feed.rss
news-tui feeds remove <source-id>

# View stats
news-tui stats

# Analyze a single article
news-tui analyze https://example.com/article
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=news_tui --cov-report=term-missing

# Lint
ruff check src/

# Type check
mypy src/
```

## Project Structure

```
src/news_tui/
├── cli.py           # CLI entry point
├── app.py           # Textual TUI
├── core/            # Types, config, errors
├── ingest/          # RSS, HN, Lobsters fetchers
├── analyze/         # Sentiment, topics, quality
├── generate/        # Markov chains, summaries
├── track/           # Database, history, drift
└── ui/              # Screens and widgets
```

## Security

This project takes security seriously:

- **No pickle**: We never use `pickle.load()` with untrusted data
- **Safe YAML**: Always `yaml.safe_load()`, never `yaml.load()`
- **No eval**: No `eval()` or `exec()` with any user input
- **Validation**: All external data is validated via Pydantic models
- **Permissions**: Sensitive files are `chmod 0o600`

See `~/engineering_principles/` and `~/sage/` for security guidelines.

## License

MIT
