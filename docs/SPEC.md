# News-TUI: Mindful Terminal News Reader

## Project Overview

Build a terminal-based news reader (TUI) that enforces **analysis-first consumption** — news is analyzed before being presented, preventing doomscrolling and promoting epistemic hygiene.

**The philosophy:** Instead of feeds optimized for engagement (dopamine hits), this tool optimizes for *informed* engagement. Think Hacker News signal-to-noise ratio meets information diet management.

**Inspiration:** [spotify-tui](https://github.com/Rigellute/spotify-tui) (Rust TUI for Spotify) — we want that aesthetic but for news consumption.

---

## Core Features

### 1. Analysis Layer (Gatekeeper)
Before any article is shown, compute:

| Analysis | Purpose | Approach |
|----------|---------|----------|
| **Sentiment** | Is this emotionally charged? | VADER (fast) or fine-tuned DistilBERT |
| **Sensationalism score** | How clickbaity is headline vs content? | Headline embedding vs body embedding distance |
| **Bias detection** | Political lean, source reliability | Pre-built source ratings + language markers |
| **Information density** | Signal-to-noise ratio | Unique entities / word count, fact density heuristics |
| **Topic clustering** | "You've read 5 crypto doom articles today" | LDA or BERTopic |

### 2. TL;DR Generation (Markov Chains)
- Implement n-gram Markov chains from scratch (learning project)
- Train per-source to capture voice/style
- Output is "impressionistic mood" not semantic fidelity — that's intentional
- Consider extractive summarization (TextRank) as a secondary option for faithful summaries

### 3. Consumption Tracking & Nudges
- SQLite database for read history
- Topic drift detection: "You're 80% AI doom content this week"
- Diversification nudges: "Hey, maybe diversify a bit more"
- Contrarian signals: Flag articles with minority sentiment on hot topics ("what people AREN'T seeing")

### 4. Narrative Tracking
- Model how narratives evolve over time
- Topic + sentiment time series
- Detect inflection points in coverage
- Help formulate theses on trends

### 5. Predictive Element
- Markov-based prediction: "What kind of news you'll see next"
- Based on current trends and historical patterns

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NEWS-TUI ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐ │
│  │   INGEST     │     │   ANALYZE    │     │      PRESENT         │ │
│  │              │     │              │     │                      │ │
│  │ • RSS Feeds  │────▶│ • Sentiment  │────▶│ • TUI (Textual)      │ │
│  │ • HN API     │     │ • Topics     │     │ • Article list       │ │
│  │ • Lobste.rs  │     │ • Quality    │     │ • Analysis overlay   │ │
│  │ • NewsAPI    │     │ • Bias       │     │ • Trend charts       │ │
│  └──────────────┘     └──────────────┘     └──────────────────────┘ │
│         │                    │                       ▲              │
│         │                    ▼                       │              │
│         │           ┌──────────────┐                 │              │
│         │           │    TRACK     │                 │              │
│         │           │              │                 │              │
│         └──────────▶│ • SQLite DB  │─────────────────┘              │
│                     │ • Read history                                │
│                     │ • Topic drift │                               │
│                     │ • Narratives  │                               │
│                     └──────────────┘                                │
│                            │                                        │
│                            ▼                                        │
│                    ┌──────────────┐                                 │
│                    │   GENERATE   │                                 │
│                    │              │                                 │
│                    │ • Markov TL;DR                                 │
│                    │ • Diversify nudges                             │
│                    │ • Narrative predictions                        │
│                    └──────────────┘                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## UI Design: Analysis Score Display

The core UX innovation: **scores are visible before you commit to reading**.

### Article Card Layout

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

### Score Metrics

| Code | Metric | Range | Interpretation |
|------|--------|-------|----------------|
| **SEN** | Sentiment | -1.0 to 1.0 | Emotional valence of content |
| **SNS** | Sensationalism | 0.0 to 1.0 | Headline hype vs content substance |
| **BIA** | Bias | -1.0 to 1.0 | Political lean (-1 left, +1 right) |
| **SIG** | Signal | 0.0 to 1.0 | Information density (facts per word) |
| **TOP** | Topics | Tags | Extracted topic clusters |

### Color Scales

**Sentiment (SEN):**
```
-1.0          0.0          +1.0
 🔴 ─────────── 🟡 ─────────── 🟢
 Negative      Neutral       Positive
```

**Sensationalism (SNS) — inverted (low is good):**
```
 0.0          0.5          1.0
 🟢 ─────────── 🟡 ─────────── 🔴
 Substance     Mixed        Clickbait
```

**Bias (BIA):**
```
-1.0          0.0          +1.0
 🔵 ─────────── ⚪ ─────────── 🔴
 Left          Center        Right
```

**Signal (SIG):**
```
 0.0          0.5          1.0
 🔴 ─────────── 🟡 ─────────── 🟢
 Fluff         Mixed        Dense
```

### Progress Bar Implementation

```python
def render_score_bar(score: float, width: int = 10, inverted: bool = False) -> str:
    """Render a score as a colored progress bar.

    Args:
        score: Value between 0.0 and 1.0
        width: Character width of bar
        inverted: If True, low scores are good (green)

    Returns:
        Rich-formatted progress bar string
    """
    filled = int(score * width)
    empty = width - filled

    # Determine color based on score (and inversion)
    if inverted:
        score = 1.0 - score

    if score < 0.33:
        color = "red"
    elif score < 0.66:
        color = "yellow"
    else:
        color = "green"

    bar = f"[{color}]{'█' * filled}[/]{'░' * empty}"
    return f"[{bar}] {score:.2f}"
```

### Topic Tag Colors

```python
TOPIC_COLORS = {
    "ai": "#8b5cf6",        # Purple
    "tech": "#3b82f6",      # Blue
    "crypto": "#f59e0b",    # Amber
    "finance": "#10b981",   # Emerald
    "politics": "#ef4444",  # Red
    "science": "#06b6d4",   # Cyan
    "culture": "#ec4899",   # Pink
    "philosophy": "#6366f1", # Indigo
    "default": "#6b7280",   # Gray
}
```

### Nudge Banners

When consumption patterns trigger alerts:

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚠️  ECHO CHAMBER: 6 of last 8 articles were #ai #doom              │
│     Suggested topics: science, economics, culture             [x]  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 🔴 HIGH SENSATIONALISM: This source averages 0.73 SNS              │
│     Consider cross-referencing with higher-signal sources     [x]  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 📊 NARRATIVE SHIFT: "AI regulation" sentiment flipped negative     │
│     3 days ago: 0.45 → today: -0.32                           [→]  │
└─────────────────────────────────────────────────────────────────────┘
```

### Compact List View (Alternative)

For quick scanning without full cards:

```
┌─────────────────────────────────────────────────────────────────────┐
│ ARTICLES                                              ↑↓ navigate  │
├─────────────────────────────────────────────────────────────────────┤
│ ▸ Why AI Doom Narratives Miss...   SEN🟢 SNS🟢 BIA⚪ SIG🟢  12m  │
│   The Hidden Cost of Stablecoins   SEN🟡 SNS🟡 BIA🔴 SIG🟢   8m  │
│   React 19: What You Need to Know  SEN🟢 SNS🔴 BIA⚪ SIG🟡   5m  │
│   The Fall of SVB: One Year Later  SEN🔴 SNS🟡 BIA🔵 SIG🟢  15m  │
│   New Research on Sleep and Memory SEN🟢 SNS🟢 BIA⚪ SIG🟢   6m  │
└─────────────────────────────────────────────────────────────────────┘
```

### Textual Widget Structure

```python
class ArticleCard(Static):
    """A card displaying article with analysis scores."""

    def compose(self) -> ComposeResult:
        yield Label(self.article.title, classes="title")
        yield Label(self.article.source_line, classes="meta")
        yield ScoreBar("SEN", self.article.sentiment)
        yield ScoreBar("SNS", self.article.sensationalism, inverted=True)
        yield ScoreBar("BIA", self.article.bias, scale="political")
        yield ScoreBar("SIG", self.article.signal)
        yield TopicTags(self.article.topics)
        yield Label(self.article.tldr, classes="tldr")


class ScoreBar(Static):
    """A single score metric with colored bar."""

    def __init__(self, label: str, score: float, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.score = score
        # ... rendering logic
```

---

## News Sources

### High-Signal Long-Form
- [Aeon](https://aeon.co/) - Essays and ideas
- [The Marginalian](https://www.themarginalian.org/) - Maria Popova's curation
- [Pudding](https://pudding.cool/) - Visual essays
- [Quanta Magazine](https://www.quantamagazine.org/) - Science
- [Works in Progress](https://worksinprogress.co/) - Progress studies

### Tech/Dev
- Hacker News API
- Lobste.rs RSS
- Ars Technica

### Domain-Specific
- AI news (various RSS feeds)
- Stablecoin/crypto news
- Fintech news

---

## Tech Stack

**Language:** Python 3.11+

**Rationale:** ML/NLP ecosystem is native (scikit, transformers, etc.), Textual is excellent for TUIs, rapid iteration > raw performance for a news reader.

**Core Dependencies:**
```toml
[project]
dependencies = [
    # TUI
    "textual>=0.50.0",

    # NLP/ML
    "nltk>=3.8.0",           # VADER sentiment
    "scikit-learn>=1.4.0",   # TF-IDF, topic modeling
    "sentence-transformers>=2.2.0",  # Embeddings

    # Data
    "feedparser>=6.0.0",     # RSS parsing
    "httpx>=0.27.0",         # Async HTTP
    "beautifulsoup4>=4.12.0", # HTML parsing

    # Storage
    "sqlite-utils>=3.35.0",  # SQLite wrapper

    # Utils
    "rich>=13.0.0",          # Terminal formatting
    "pydantic>=2.5.0",       # Data validation
    "click>=8.1.0",          # CLI framework
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
]
```

---

## Project Structure

```
news-tui/
├── CLAUDE.md                 # Session context for Claude Code
├── README.md                 # Project documentation
├── pyproject.toml
├── src/
│   └── news_tui/
│       ├── __init__.py
│       ├── cli.py            # Click entry point
│       ├── app.py            # Textual app definition
│       │
│       ├── ingest/           # Data fetching
│       │   ├── __init__.py
│       │   ├── rss.py        # RSS feed parser
│       │   ├── hn.py         # Hacker News API
│       │   ├── lobsters.py   # Lobste.rs scraper
│       │   └── sources.py    # Source registry
│       │
│       ├── analyze/          # Analysis layer
│       │   ├── __init__.py
│       │   ├── sentiment.py  # VADER / transformer sentiment
│       │   ├── topics.py     # LDA / BERTopic clustering
│       │   ├── quality.py    # Information density scoring
│       │   ├── bias.py       # Source bias detection
│       │   └── sensationalism.py  # Headline vs body analysis
│       │
│       ├── generate/         # Generation layer
│       │   ├── __init__.py
│       │   ├── markov.py     # Markov chain implementation
│       │   ├── summarize.py  # TL;DR generation
│       │   └── predict.py    # Narrative prediction
│       │
│       ├── track/            # Persistence layer
│       │   ├── __init__.py
│       │   ├── db.py         # SQLite schema & queries
│       │   ├── history.py    # Read history tracking
│       │   ├── drift.py      # Topic drift detection
│       │   └── narratives.py # Narrative time series
│       │
│       ├── ui/               # TUI components
│       │   ├── __init__.py
│       │   ├── screens/      # Textual screens
│       │   ├── widgets/      # Custom widgets
│       │   └── styles.py     # CSS theming
│       │
│       └── core/             # Shared types & utils
│           ├── __init__.py
│           ├── types.py      # Pydantic models
│           ├── config.py     # Configuration management
│           └── errors.py     # Custom exceptions
│
├── tests/
│   ├── conftest.py           # Pytest fixtures
│   ├── unit/                 # Unit tests (mirror src structure)
│   │   ├── test_markov.py
│   │   ├── test_sentiment.py
│   │   └── ...
│   └── integration/          # Integration tests
│       ├── test_ingest_analyze.py
│       ├── test_full_pipeline.py
│       └── ...
│
├── docs/
│   ├── architecture.md       # System design docs
│   ├── features/             # Feature documentation
│   │   ├── markov-chains.md
│   │   ├── sentiment-analysis.md
│   │   └── ...
│   └── decisions/            # ADRs (Architecture Decision Records)
│       └── 001-python-over-rust.md
│
└── data/
    ├── sources.yaml          # News source configuration
    └── bias_ratings.json     # Source bias ratings
```

---

## Development Process Requirements

### 1. Use Sage Throughout

**Before starting any significant work:**
```bash
sage checkpoint "Starting [feature] implementation"
```

**After completing features or making discoveries:**
```bash
sage knowledge add "Learned: [insight]"
```

**Track these specifically:**
- Architecture decisions and why
- Tricky implementation details
- Bugs encountered and how they were solved
- Performance findings
- Security considerations

**Goal:** Build a comprehensive knowledge base that documents the entire build process. This will be used to show others how to build with AI.

### 2. Engineering Principles

Reference `~/engineering_principles/` directory throughout development:

- **`ENGINEERING_PRINCIPLES.md`** — Core philosophy, FP-first approach
- **`SENIOR_ENGINEER_CHECKLIST.md`** — 14+ senior engineer personas for code review
- **`PROMPT_ENGINEERING.md`** — Best practices for prompts

**Key principles to enforce:**
- Functional programming paradigm preferred over OOP (composition over inheritance)
- Pure functions where possible
- Immutability by default
- "Will I understand this at 2am when it's broken?" test
- Single source of truth
- Validate at boundaries, trust internally

### 3. Security Mindset

Reference `~/sage/` directory for security learnings:

**Deserialization vigilance:**
- NO `pickle.load()` on untrusted data
- NO `yaml.load()` — always `yaml.safe_load()`
- NO `torch.load()` without `weights_only=True`
- NO `np.load()` without `allow_pickle=False`
- NO `eval()` / `exec()` with any user input

**General security:**
- Input validation at boundaries
- Secrets never in logs or version control
- Rate limiting on external APIs
- Graceful degradation on failures

### 4. Testing Requirements

**Unit tests on everything:**
- Every function in `analyze/` must have tests
- Every function in `generate/` must have tests
- Markov chain implementation needs comprehensive tests
- Mock external APIs in tests

**Integration tests:**
- Full pipeline: ingest → analyze → present
- Database operations
- TUI interactions (Textual has testing support)

**Test coverage target:** 80%+

**Test naming convention:**
```python
def test_<function_name>_<scenario>_<expected_behavior>():
    """Test that <function> does <thing> when <condition>."""
```

### 5. Documentation Requirements

**Every module needs:**
- Module-level docstring explaining purpose
- All public functions have docstrings with:
  - Description
  - Args with types
  - Returns with types
  - Raises (if applicable)
  - Example usage (for complex functions)

**Critical features need standalone docs in `docs/features/`:**
- How the Markov chain implementation works
- How sentiment analysis pipeline works
- How topic clustering works
- How narrative tracking works

**Architecture decisions need ADRs in `docs/decisions/`:**
- Format: `NNN-title.md`
- Include: context, decision, consequences

---

## Implementation Phases

### Phase 1: Foundation (MVP)
1. Project scaffolding with proper structure
2. Basic RSS ingestion (one source)
3. Markov chain implementation from scratch
4. SQLite storage setup
5. Minimal TUI showing article list

**Checkpoint:** Can fetch articles, generate (chaotic) TL;DRs, display in terminal

### Phase 2: Analysis Layer
1. VADER sentiment analysis
2. TF-IDF for information density
3. Topic extraction (start with keyword-based)
4. Analysis overlay in TUI

**Checkpoint:** Articles show sentiment scores and topics

### Phase 3: Tracking & Nudges
1. Read history persistence
2. Topic drift detection
3. "Diversify" nudge logic
4. Reading stats view

**Checkpoint:** "You've read 5 AI doom articles" works

### Phase 4: Advanced Analysis
1. BERTopic for better clustering
2. Sensationalism detection (headline vs body)
3. Source bias integration
4. Narrative time series

**Checkpoint:** Full analysis suite operational

### Phase 5: Prediction & Polish
1. Markov narrative prediction
2. Trend visualization (sparklines in TUI)
3. Keyboard shortcuts optimization
4. Performance profiling

**Checkpoint:** Feature complete, ready for daily use

---

## Code Style Examples

### Good: Functional, Pure, Documented

```python
"""Markov chain implementation for text generation.

This module implements n-gram Markov chains for generating
impressionistic summaries of article content. The goal is
to capture the "voice" of a source rather than semantic accuracy.
"""

from collections import defaultdict
from typing import Sequence
import random


def build_chain(
    text: str,
    n: int = 2,
) -> dict[tuple[str, ...], list[str]]:
    """Build an n-gram Markov chain from input text.

    Args:
        text: Input text to build chain from.
        n: Size of n-gram (default 2 for bigrams).

    Returns:
        Dictionary mapping n-gram tuples to list of possible
        next words.

    Example:
        >>> chain = build_chain("the cat sat on the mat", n=2)
        >>> chain[("the", "cat")]
        ["sat"]
    """
    words = text.split()
    chain: dict[tuple[str, ...], list[str]] = defaultdict(list)

    for i in range(len(words) - n):
        key = tuple(words[i:i + n])
        next_word = words[i + n]
        chain[key].append(next_word)

    return dict(chain)


def generate(
    chain: dict[tuple[str, ...], list[str]],
    seed: tuple[str, ...] | None = None,
    max_words: int = 50,
    rng: random.Random | None = None,
) -> str:
    """Generate text from a Markov chain.

    Args:
        chain: Markov chain dictionary.
        seed: Starting n-gram (random if None).
        max_words: Maximum words to generate.
        rng: Random number generator (for reproducibility).

    Returns:
        Generated text string.

    Raises:
        ValueError: If chain is empty.
    """
    if not chain:
        raise ValueError("Cannot generate from empty chain")

    rng = rng or random.Random()

    if seed is None:
        seed = rng.choice(list(chain.keys()))

    words = list(seed)
    n = len(seed)

    for _ in range(max_words - n):
        key = tuple(words[-n:])
        if key not in chain:
            break
        next_word = rng.choice(chain[key])
        words.append(next_word)

    return " ".join(words)
```

### Bad: OOP-heavy, Impure, Undocumented

```python
# Don't do this
class MarkovChainGenerator:
    def __init__(self):
        self.chain = {}
        self.last_generated = None  # Stateful!

    def train(self, text):  # No types, no docs
        # Mutates self.chain
        ...

    def generate(self):  # Depends on hidden state
        self.last_generated = ...
        return self.last_generated
```

---

## Questions to Resolve During Development

1. **Embedding model choice:** MiniLM-L6-v2 (fast, small) vs mxbai-embed-large (better quality)?
2. **Async vs sync:** Full async for ingestion or keep simple?
3. **Caching strategy:** How aggressively to cache analysis results?
4. **Refresh frequency:** Background polling or manual refresh?
5. **Multiple instances:** Should support multiple users or single-user local?

---

## Success Criteria

1. **Daily driver:** You actually use this instead of browsing HN directly
2. **Mindful consumption:** The analysis overlay changes how you select articles
3. **Insight generation:** Narrative tracking helps form contrarian theses
4. **Documented journey:** Sage knowledge base captures the full build process
5. **Shareable:** Someone else could learn from the checkpoints and knowledge items

---

## Resources

- [Textual Documentation](https://textual.textualize.io/)
- [Markov Chains Explained](https://setosa.io/ev/markov-chains/)
- [VADER Sentiment](https://github.com/cjhutto/vaderSentiment)
- [BERTopic](https://maartengr.github.io/BERTopic/)
- [spotify-tui](https://github.com/Rigellute/spotify-tui) — UX reference
