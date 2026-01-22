"""CSS styles and theme configuration for news-tui.

This module defines the visual theming using Textual's CSS system.
Cyberpunk aesthetic: lavender/purple accents on dark gunmetal.
"""

# Cyberpunk color palette
COLORS = {
    # Background tones (gunmetal/dark)
    "bg_dark": "#0d0d14",       # Near-black with blue tint
    "bg_main": "#13131f",       # Gunmetal dark
    "bg_surface": "#1a1a2e",    # Elevated surface
    "bg_highlight": "#242438",  # Highlighted surface

    # Accent colors (lavender/purple)
    "lavender": "#c4b5fd",      # Light lavender (primary)
    "purple": "#a78bfa",        # Medium purple
    "violet": "#8b5cf6",        # Vivid violet
    "pink_accent": "#f0abfc",   # Pink for highlights

    # Text
    "text_primary": "#e4e4f0",  # Off-white
    "text_muted": "#7c7c9a",    # Muted lavender-gray
}

# Topic tag colors (cyberpunk palette)
TOPIC_COLORS: dict[str, str] = {
    "ai": "#c084fc",        # Purple
    "tech": "#60a5fa",      # Blue
    "crypto": "#fbbf24",    # Amber
    "finance": "#34d399",   # Emerald
    "politics": "#f87171",  # Red
    "science": "#22d3ee",   # Cyan
    "culture": "#f472b6",   # Pink
    "philosophy": "#a78bfa", # Lavender
    "default": "#7c7c9a",   # Muted gray
}

# Main application CSS - Cyberpunk theme
APP_CSS = """
Screen {
    background: #13131f;
}

/* Article list */
.article-list {
    height: 100%;
    border: solid #8b5cf6;
    background: #13131f;
}

ListItem {
    padding: 1;
    background: #13131f;
}

ListItem:hover {
    background: #1a1a2e;
}

ListItem:focus {
    background: #242438;
}

ListItem > Label {
    color: #e4e4f0;
}

/* Article card */
.article-card {
    padding: 1 2;
    margin: 1;
    border: round #8b5cf6;
    background: #1a1a2e;
}

.article-title {
    text-style: bold;
    color: #c4b5fd;
}

.article-meta {
    color: #7c7c9a;
    margin-bottom: 1;
}

/* Score bars */
.score-row {
    height: 1;
}

.score-label {
    width: 4;
    text-style: bold;
}

.score-bar {
    width: 12;
}

.score-value {
    width: 6;
    text-align: right;
}

.score-description {
    color: $text-muted;
    padding-left: 1;
}

/* Score colors */
.score-low {
    color: $error;
}

.score-mid {
    color: $warning;
}

.score-high {
    color: $success;
}

/* Bias scale (different from standard) */
.bias-left {
    color: $primary;
}

.bias-center {
    color: $text-muted;
}

.bias-right {
    color: $error;
}

/* Topic tags */
.topic-tags {
    margin-top: 1;
}

.topic-tag {
    padding: 0 1;
    margin-right: 1;
    border: round $surface-lighten-2;
}

/* TL;DR section */
.tldr {
    margin-top: 1;
    padding: 1;
    background: #0d0d14;
    border: round #242438;
    color: #7c7c9a;
}

/* Nudge banners */
.nudge-banner {
    padding: 1 2;
    margin: 1;
    border: round #fbbf24;
    background: #1a1a2e;
}

.nudge-banner.warning {
    border: round #fbbf24;
    background: #1a1a2e;
}

.nudge-banner.info {
    border: round #a78bfa;
    background: #1a1a2e;
}

.nudge-banner.alert {
    border: round #f87171;
    background: #1a1a2e;
}

/* Header - Cyberpunk purple gradient feel */
Header {
    background: #8b5cf6;
    color: #0d0d14;
}

/* Footer */
Footer {
    background: #0d0d14;
    color: #7c7c9a;
}

FooterKey > .footer-key--key {
    background: #8b5cf6;
    color: #0d0d14;
}

FooterKey > .footer-key--description {
    color: #c4b5fd;
}

/* Stats view */
.stats-container {
    padding: 2;
    background: #13131f;
}

.stat-value {
    text-style: bold;
    color: #c4b5fd;
}

/* Main container */
#main-container {
    background: #13131f;
}
"""


def get_score_class(score: float, inverted: bool = False) -> str:
    """Get CSS class for a score value.

    Args:
        score: Score value (0.0 to 1.0 or -1.0 to 1.0).
        inverted: If True, low scores are good (green).

    Returns:
        CSS class name.
    """
    # Normalize to 0-1 if needed
    if score < 0:
        score = (score + 1) / 2

    if inverted:
        score = 1 - score

    if score < 0.33:
        return "score-low"
    elif score < 0.66:
        return "score-mid"
    else:
        return "score-high"


def get_bias_class(bias: float) -> str:
    """Get CSS class for bias score.

    Args:
        bias: Bias value (-1.0 left to 1.0 right).

    Returns:
        CSS class name.
    """
    if bias < -0.3:
        return "bias-left"
    elif bias > 0.3:
        return "bias-right"
    else:
        return "bias-center"


def get_topic_color(topic: str) -> str:
    """Get color for a topic tag.

    Args:
        topic: Topic name.

    Returns:
        Hex color code.
    """
    return TOPIC_COLORS.get(topic.lower(), TOPIC_COLORS["default"])
