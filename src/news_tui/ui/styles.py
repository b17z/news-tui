"""CSS styles and theme configuration for news-tui.

This module defines the visual theming using Textual's CSS system.
"""

# Topic tag colors
TOPIC_COLORS: dict[str, str] = {
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

# Main application CSS
APP_CSS = """
Screen {
    background: $surface;
}

/* Article list */
.article-list {
    height: 100%;
    border: solid $primary;
}

.article-item {
    padding: 1;
    border-bottom: solid $surface-darken-1;
}

.article-item:hover {
    background: $surface-lighten-1;
}

.article-item:focus {
    background: $primary-darken-2;
}

/* Article card */
.article-card {
    padding: 1 2;
    margin: 1;
    border: round $primary;
    background: $surface;
}

.article-title {
    text-style: bold;
    color: $text;
}

.article-meta {
    color: $text-muted;
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
    background: $surface-darken-1;
    border: round $surface-lighten-1;
    color: $text-muted;
}

/* Nudge banners */
.nudge-banner {
    padding: 1 2;
    margin: 1;
    border: round $warning;
    background: $warning-darken-3;
}

.nudge-banner.warning {
    border: round $warning;
    background: $warning-darken-3;
}

.nudge-banner.info {
    border: round $primary;
    background: $primary-darken-3;
}

.nudge-banner.alert {
    border: round $error;
    background: $error-darken-3;
}

/* Header */
Header {
    background: $primary;
    color: $text;
}

/* Footer */
Footer {
    background: $surface-darken-1;
}

/* Stats view */
.stats-container {
    padding: 2;
}

.stat-value {
    text-style: bold;
    color: $primary;
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
