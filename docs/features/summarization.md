# Summarization: How TL;DRs are Generated

news-tui generates TL;DRs for every article using a hybrid approach that adapts to content length.

## The Challenge

RSS feeds typically provide only snippets (50-200 words), not full articles. Traditional summarization techniques need more text to work with. Our solution adapts:

- **Short texts**: Extractive summarization (pick best sentences)
- **Long texts**: Markov chains (generate impressionistic summary)

---

## Extractive Summarization (for short texts)

For articles under 100 words, we extract the most important sentences.

### How it works

1. **Split into sentences**
   ```
   "First sentence. Second sentence." → ["First sentence", "Second sentence"]
   ```

2. **Score each sentence** by:
   - **Keyword importance**: Words that appear frequently across the document
   - **Position bonus**: First sentences often contain key information (1.5x boost)
   - **Length factor**: Prefer medium-length sentences (15-25 words ideal)

3. **Select top sentences** preserving original order

### Example

```
Input: "Scientists discovered a new exoplanet orbiting a distant star. 
        The planet is roughly Earth-sized. Initial observations suggest 
        it may have an atmosphere. Further study is needed."

Scores:
- Sentence 1: 4.2 (high - keywords: scientists, discovered, exoplanet)
- Sentence 2: 2.1 (low - generic statement)
- Sentence 3: 3.8 (good - keywords: observations, atmosphere)
- Sentence 4: 1.5 (low - filler)

TL;DR: "Scientists discovered a new exoplanet orbiting a distant star. 
        Initial observations suggest it may have an atmosphere."
```

---

## Markov Chain Generation (for long texts)

For texts over 100 words, we use Markov chains to generate an "impressionistic" summary.

### What is a Markov Chain?

A Markov chain predicts the next word based on the previous N words (n-grams).

```
Text: "the cat sat on the mat"

Bigram chain:
  ("the", "cat") → ["sat"]
  ("cat", "sat") → ["on"]
  ("sat", "on")  → ["the"]
  ("on", "the")  → ["mat"]
  ("the", "mat") → []
```

### How generation works

1. **Build chain** from source text
2. **Pick random seed** (starting n-gram)
3. **Walk the chain**: For each state, randomly pick a next word
4. **Stop** when reaching max words or a dead end

### Why Markov chains?

The goal isn't perfect semantic accuracy — it's capturing the "voice" and key themes:

```
Source: Technical blog about React performance optimization
Markov output: "component rendering lifecycle optimization hooks..."
```

The output is impressionistic but captures core themes.

### Limitations

- Needs sufficient text to build a useful chain
- Can produce grammatically awkward sentences
- Falls back to extractive if chain is too sparse

---

## HTML Cleaning

Before any summarization, we clean the raw RSS content:

1. **Strip HTML tags**: `<p>Text</p>` → `Text`
2. **Decode entities**: `&amp;` → `&`
3. **Remove scripts/styles**: No code contamination
4. **Remove attribution**: "by Author Read on Source" patterns

This ensures TL;DRs contain actual content, not HTML artifacts.

---

## Configuration

Current settings:
- **Max TL;DR length**: 50 words
- **Extractive threshold**: < 100 words
- **N-gram size**: 2 (bigrams)
- **Extractive sentences**: 2

These are tuned for RSS feed snippets and can be adjusted in `pipeline.py`.
