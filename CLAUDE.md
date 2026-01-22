# News-TUI

Mindful terminal news reader with analysis-first consumption. News is analyzed before being presented — sentiment, bias, quality scoring — to prevent doomscrolling and promote epistemic hygiene.

**Current phase:** Phase 3 (Tracking & Nudges) ✅
**Test count:** 84 tests (target: 80%+ coverage)

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run the app
news-tui                     # Launch TUI
news-tui --refresh           # Refresh feeds first, then launch

# Keyboard shortcuts (in TUI)
j/k     Navigate up/down
Enter/v View article in terminal
o       Open in browser
r       Refresh feeds
s       Show stats
q       Quit
?       Help
```

## CLI Reference

```bash
# Feed management
news-tui feeds list          # Show configured sources
news-tui feeds add <url>     # Add RSS feed
news-tui feeds remove <id>   # Remove a source

# Analysis & stats
news-tui stats               # Reading statistics (last 7 days)
news-tui analyze <url>       # Analyze single article (coming soon)
```

## Architecture

```
~/.config/news-tui/          # User config
├── config.yaml              # API keys, preferences
├── sources.yaml             # News source configuration
└── news-tui.db              # SQLite (history, analysis cache)

<project>/
├── CLAUDE.md                # This file
├── docs/
│   ├── SPEC.md              # Full specification (reference)
│   ├── architecture.md      # System design
│   └── features/            # Feature documentation
└── src/news_tui/            # Source code
```

## Analysis Score Display (UI)

Each article shows colored score indicators at a glance:

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📰 Why AI Doom Narratives Miss the Point                           │
│ The Marginalian • 12 min read • 2h ago                             │
│                                                                     │
│ SEN [████████░░] 0.78   Slightly positive                          │
│ SNS [██░░░░░░░░] 0.21   Low sensationalism ✓                       │
│ BIA [█████░░░░░] 0.52   Moderate left                              │
│ SIG [███████░░░] 0.71   High signal                                │
│ TOP  #ai #philosophy #technology                                   │
│                                                                     │
│ TL;DR: "The discourse around artificial intelligence tends to..."  │
└─────────────────────────────────────────────────────────────────────┘
```

**Score legend:**

| Code | Metric | Color Scale |
|------|--------|-------------|
| **SEN** | Sentiment | 🔴 negative → 🟡 neutral → 🟢 positive |
| **SNS** | Sensationalism | 🟢 low (good) → 🟡 medium → 🔴 high (clickbait) |
| **BIA** | Bias | 🔵 left ← ⚪ center → 🔴 right |
| **SIG** | Signal (info density) | 🔴 low → 🟡 medium → 🟢 high |
| **TOP** | Topics | Colored tags by category |

**Color implementation (Textual CSS):**

```css
/* Score bars */
.score-low { color: $error; }      /* Red */
.score-mid { color: $warning; }    /* Yellow */
.score-high { color: $success; }   /* Green */

/* Bias uses different scale */
.bias-left { color: $primary; }    /* Blue */
.bias-center { color: $surface; }  /* Gray */
.bias-right { color: $error; }     /* Red */

/* Topic tags */
.topic-tech { background: #3b82f6; }
.topic-ai { background: #8b5cf6; }
.topic-finance { background: #10b981; }
.topic-politics { background: #ef4444; }
.topic-science { background: #06b6d4; }
```

**Nudge banners (when triggered):**

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚠️  DIVERSIFY: 6 of your last 8 articles were #ai #doom            │
│     Consider: science, economics, culture                     [x]  │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Modules

| File | Purpose |
|------|---------|
| `cli.py` | Click entry point |
| `app.py` | Textual TUI application |
| `ingest/rss.py` | RSS feed parsing |
| `ingest/hn.py` | Hacker News API |
| `analyze/sentiment.py` | VADER / transformer sentiment |
| `analyze/topics.py` | LDA / BERTopic clustering |
| `analyze/quality.py` | Information density scoring |
| `generate/markov.py` | Markov chain TL;DR generation |
| `track/db.py` | SQLite schema & queries |
| `track/drift.py` | Topic drift detection |

## Documentation Hierarchy

| Doc | When to Load | Size |
|-----|--------------|------|
| `CLAUDE.md` | **Always** — quick reference | ~4KB |
| `docs/SPEC.md` | Implementation details, full context | ~15KB |
| `docs/features/*.md` | Deep dive on specific features | Varies |

**Default:** This file + `docs/SPEC.md` for implementation work.

## Development Phases

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Foundation (scaffolding, Markov, RSS, basic TUI) | ✅ Complete |
| 2 | Analysis layer (sentiment, topics, quality) | ✅ Complete |
| 3 | Tracking & nudges (history, drift, diversify) | ✅ Complete |
| 4 | Advanced analysis (BERTopic, bias, sensationalism) | 🔄 Current |
| 5 | Prediction & polish (narrative prediction, viz) | ⏳ |

## Core Principles

1. **Functional over OOP** — Pure functions, immutable data, composition
2. **Tests are mandatory** — Every feature needs unit + integration tests
3. **Analysis before consumption** — Never show raw feed, always analyzed
4. **"2am debugging" test** — Will I understand this when it's broken?
5. **Security paranoia** — No pickle, no eval, validate at boundaries

## Code Style

- Python 3.11+ (match statements, type parameter syntax)
- Frozen dataclasses / Pydantic models for data
- 100 char line length
- Functional: pure functions, avoid mutable state
- Docstrings on all public functions

**Good:**
```python
def build_chain(text: str, n: int = 2) -> dict[tuple[str, ...], list[str]]:
    """Build n-gram Markov chain from text.

    Args:
        text: Input text to process.
        n: N-gram size (default bigram).

    Returns:
        Dictionary mapping n-gram tuples to possible next words.
    """
    words = text.split()
    chain: dict[tuple[str, ...], list[str]] = defaultdict(list)
    # ... pure implementation
    return dict(chain)
```

**Bad:**
```python
class MarkovGenerator:
    def __init__(self):
        self.chain = {}  # Mutable state
        self.last_output = None  # Hidden state

    def train(self, text):  # No types, no docs, mutates
        ...
```

## Testing Patterns

**Every feature implementation MUST include:**

```python
# Unit test — isolated function
def test_build_chain_creates_valid_transitions():
    """Test that build_chain produces correct n-gram mappings."""
    text = "the cat sat on the mat"
    chain = build_chain(text, n=2)
    assert ("the", "cat") in chain
    assert chain[("the", "cat")] == ["sat"]

# Integration test — full workflow
def test_ingest_analyze_pipeline():
    """Test RSS → analysis → storage flow."""
    articles = fetch_rss(TEST_FEED_URL)
    analyzed = [analyze_article(a) for a in articles]
    store_articles(db, analyzed)
    assert db.count_articles() == len(articles)

# Edge case — boundaries and errors
def test_build_chain_handles_empty_text():
    """Test graceful handling of empty input."""
    chain = build_chain("")
    assert chain == {}
```

## Security Checklist

**NEVER do these:**
- `pickle.load()` on any data
- `yaml.load()` — always `yaml.safe_load()`
- `eval()` / `exec()` with any input
- Store API keys in code or logs

**ALWAYS do these:**
- Validate input at boundaries
- Use Pydantic for external data
- Rate limit external API calls
- Graceful degradation on failures

## Sage Integration (REQUIRED)

**Before starting any feature:**
```bash
sage checkpoint "Starting [feature]: [brief description]"
```

**After completing features:**
```bash
sage checkpoint "Completed [feature]: [what works now]"
```

**When you learn something interesting:**
```bash
sage knowledge add "Learned: [insight]" --keywords "[relevant,keywords]"
```

**Track these specifically:**
- Architecture decisions and why
- Tricky implementation gotchas
- Bugs encountered and solutions
- Performance findings
- Security considerations

**Goal:** Build knowledge base documenting the entire build process.

## Development Commands

```bash
# Setup
pip install -e ".[dev]"      # Install dev mode

# Quality
ruff check src/ --fix        # Lint
black src/                   # Format
mypy src/                    # Type check

# Testing
pytest                       # Run all tests
pytest tests/unit/ -v        # Unit tests only
pytest tests/integration/ -v # Integration tests
pytest --cov=news_tui        # Coverage report
pytest --cov=news_tui --cov-report=term-missing

# Manual testing
news-tui --debug             # Verbose logging
```

## Phase 1 Checklist ✅

- [x] Project scaffolding (pyproject.toml, structure)
- [x] Markov chain module with tests
- [x] RSS ingestion (single feed) with tests
- [x] SQLite storage setup with tests
- [x] Minimal Textual TUI (article list)
- [x] Integration test: fetch → generate TL;DR → display

**Checkpoint criteria:** Can fetch articles, generate Markov TL;DRs, display in terminal. ✅

## Phase 2 Checklist ✅

- [x] VADER sentiment analysis
- [x] TF-IDF inspired signal scoring (information density)
- [x] Topic extraction (keyword-based)
- [x] Analysis overlay in TUI (score bars with values)
- [x] Cyberpunk theme (lavender/purple, gunmetal)
- [x] Article detail view (terminal reading)
- [x] Open article in browser
- [x] Track reads in history

**Checkpoint criteria:** Articles show sentiment scores, signal, topics. Can view in terminal or browser. ✅

## Phase 3 Checklist ✅

- [x] HTML stripping from RSS content
- [x] Extractive summarization for better TL;DRs
- [x] Read history persistence (mark as read)
- [x] Topic drift detection
- [x] Diversification nudge banner
- [x] Reading stats view (press 's')
- [x] Topic bar charts in stats

**Checkpoint criteria:** "You've read 5 AI articles" nudge works. Stats show 7-day summary with topic breakdown. ✅

## External References

- **Engineering principles:** `~/engineering_principles/`
- **Sage security learnings:** `~/sage/` (deserialization, etc.)
- **Textual docs:** https://textual.textualize.io/
- **spotify-tui (UX reference):** https://github.com/Rigellute/spotify-tui

## Don't Forget

- [ ] Run tests before AND after changes
- [ ] New features need tests (unit + integration)
- [ ] Update test count in this file when adding tests
- [ ] Checkpoint with Sage at phase boundaries
- [ ] Document "why" in ADRs for architectural decisions
- [ ] No pickle, no eval, no yaml.load()
