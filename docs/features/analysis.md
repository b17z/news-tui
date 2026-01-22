# Analysis Layer: How news-tui Scores Articles

news-tui analyzes every article before displaying it, giving you visibility into the nature of content before you commit to reading. This document explains how each score works.

## Overview

Each article shows these scores:

```
SEN ██████████ +0.78   (Sentiment: positive)
SIG █████░░░░░ +0.52   (Signal: medium info density)
#ai #tech #science     (Topics detected)
```

---

## Sentiment Analysis (SEN)

**What it measures:** The emotional tone of the article.

**Range:** -1.0 (very negative) to +1.0 (very positive)

**How it works:**

We use [VADER (Valence Aware Dictionary and sEntiment Reasoner)](https://github.com/cjhutto/vaderSentiment), a lexicon-based sentiment analyzer specifically tuned for social media and news content.

VADER scores text by:
1. Looking up words in a sentiment lexicon (e.g., "excellent" = +3, "terrible" = -3)
2. Applying grammatical rules (negation, intensifiers, punctuation)
3. Combining scores into a compound sentiment

**Example:**
```
"Great progress on AI safety" → +0.6 (positive)
"Market crashes amid fears" → -0.7 (negative)
"Scientists publish findings" → +0.1 (neutral)
```

**Why it matters:**
- Helps identify emotionally-charged content
- Alerts you to doom-scrolling patterns
- Neutral articles often have higher signal

---

## Signal Score (SIG)

**What it measures:** Information density — how much unique, substantive content per word.

**Range:** 0.0 (fluff/filler) to 1.0 (dense information)

**How it works:**

Signal scoring combines multiple factors:

### 1. Vocabulary Richness (25%)
```
unique_ratio = unique_words / total_content_words
```
Higher ratio = more diverse vocabulary = higher signal.

### 2. Word Length (15%)
```
avg_length_score = (avg_word_length - 3) / 5
```
Longer words tend to be more specific (e.g., "implementation" vs "thing").

### 3. High-Signal Words (20%)
Bonus for technical/precise language:
- "algorithm", "methodology", "hypothesis"
- "specifically", "consequently", "therefore"

### 4. Low-Signal Penalty (15%)
Penalty for filler/clickbait language:
- "amazing", "incredible", "shocking"
- "basically", "literally", "stuff"

### 5. Sentence Complexity (15%)
Ideal: 15-25 words per sentence.
- Too short: fragmented, lacking context
- Too long: hard to follow, potentially bloated

### 6. Content Ratio (10%)
```
content_ratio = content_words / total_words
```
Higher ratio = less fluff (articles vs conjunctions).

**Example scores:**
```
Technical blog post with code examples: 0.75
Thoughtful long-form essay: 0.70
Standard news article: 0.50
Listicle with clickbait: 0.30
```

**Why it matters:**
- Prioritize articles that respect your time
- Identify content-dense deep dives
- Filter out fluff and filler

---

## Topic Extraction (TOP)

**What it measures:** Subject matter categories.

**How it works:**

Keyword-based extraction scans for domain-specific terms:

| Topic | Trigger Words |
|-------|---------------|
| **ai** | artificial intelligence, machine learning, neural network, LLM, GPT |
| **tech** | software, programming, startup, silicon valley, open source |
| **crypto** | bitcoin, ethereum, blockchain, defi, cryptocurrency |
| **finance** | market, stock, investment, economy, inflation |
| **science** | research, study, scientist, experiment, hypothesis |
| **culture** | art, music, film, society, cultural |

**Why it matters:**
- Track what topics you're consuming
- Detect topic drift (echo chambers)
- Diversify your reading diet

---

## Topic Drift Detection

**What it measures:** When your reading becomes too narrow.

**How it works:**

The system analyzes your last 10 articles:
1. Counts topic frequency across recent reads
2. If any topic exceeds 60%, triggers a nudge
3. Suggests alternative topics to explore

**Example nudge:**
```
⚠️ DIVERSIFY: 70% of recent reads are #ai, #tech
   Consider exploring: philosophy, culture, science
```

**Why it matters:**
- Prevents echo chambers
- Encourages intellectual diversity
- Promotes mindful consumption

---

## TL;DR Generation

**What it measures:** A quick summary of the article.

**How it works:**

For short texts (< 100 words):
- **Extractive summarization**: Pulls the most important sentences
- Uses TextRank-inspired scoring based on keyword frequency

For longer texts:
- **Markov chains**: Generates impressionistic summaries
- Captures the "voice" of the content

**Why it matters:**
- Quick assessment before committing to read
- Helps with article triage
- Reduces time wasted on irrelevant content

---

## Future Enhancements (Phase 4+)

### Bias Detection (BIA)
- Political lean detection (-1.0 left → +1.0 right)
- Source reliability ratings
- Cross-reference with known bias databases

### Sensationalism Score (SNS)
- Headline vs body sentiment gap
- Clickbait pattern detection
- "Promise vs deliver" analysis

### Narrative Tracking
- Topic + sentiment time series
- Detect inflection points in coverage
- Help formulate contrarian theses
