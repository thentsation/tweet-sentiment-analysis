[🇧🇷 Português](ARTIGO.md) | 🇺🇸 English

# What a notebook of covid tweets taught me about sentiment labeling

I started out just wanting to tidy up a messy notebook. I ended up finding out that the two sentiment labelers I was using only agree on a little over half of the tweets — and that changed what I think "sentiment analysis" actually measures.

## Where this came from

The starting point was `notebooks/tweetML.ipynb`: 179k COVID-19 tweets, TextBlob computing sentiment, LDA pulling out topics, a Naive Bayes trained on top of it. It ran cell by cell, produced a result, and for a while that was enough — it was an NLP exercise, not a system.

The problem showed up when I tried to reproduce an analysis two days later: redoing anything meant running the whole notebook from the top, in the right order, hoping the global state hadn't quietly changed meaning along the way. There wasn't a single test — changing preprocessing meant praying the numbers wouldn't shift without me noticing. `requirements.txt` listed libraries I wasn't even using anymore. No CI, no lint, no type checking. And the most important output of the notebook, the classifier's accuracy, only existed inside the cell that printed it — close Jupyter and the number was gone with it.

## Getting the analysis out of the cells

The rule I set for myself: no new feature before the existing logic is covered by a test. But to test anything, I first needed something testable — so I broke the notebook into modules, each with one responsibility and one test boundary:

```
src/
├── preprocessing.py   # text cleaning + stopwords
├── sentiment.py       # TextBlob and labels
├── topics.py          # LDA
├── classifier.py      # Naive Bayes + evaluation
├── visualization.py   # histogram + wordclouds
├── pipeline.py        # orchestration
└── main.py            # CLI
```

The same analysis that used to live tied together by global variables between cells became a pure `run_pipeline(config)` function: a frozen, validated `PipelineConfig` goes in, a `PipelineResult` plus `reports/metrics.json` comes out. Today, `python src/main.py --sample 2000` runs exactly what the notebook ran, just reproducibly.

The dataset is 66 MB, so tests couldn't depend on it or on downloading anything. The fixtures build synthetic tweets that are clearly positive, negative, and neutral — "I love this amazing day", "I hate this terrible day", "The office opens at nine" — and validate signs and boundaries: polarity-sign classification, confusion matrix shape, determinism under fixed seeds. CI runs on every commit: lint, format check, mypy (`disallow_untyped_defs`), pytest with a coverage threshold across a Python 3.11/3.12 matrix, dependency auditing with pip-audit, and a **pipeline smoke** job that runs the real thing on a 500-tweet sample and checks the reports come out the other side — a unit test won't catch "the CSV has no `date` column"; smoke will.

The Docker image became a multi-stage build on `python:3.14-slim`, installing from the lockfile, non-root user, stopwords and the VADER lexicon pre-downloaded at build time, dataset bundled in — the whole pipeline runs anywhere Docker does: `docker run tweet-sentiment --sample 5000`. In CI, the image gets scanned with Trivy before it goes to GHCR.

## Cleaning actual tweets, not generic text

The original notebook only did lowercasing and stopword removal — fine for book text, not for a tweet. Truncated URLs (`https://t.co/...`), @mentions, "RT" prefixes, and hashtags were becoming features for the LDA and the classifier without me ever deciding that on purpose. The cleaning now strips URLs, mentions, and RT explicitly, and unwraps `#COVID19` into `COVID19` — the hashtag's text carries meaning, the `#` is just punctuation getting in the vectorizer's way.

## The finding that changed the project: two labelers, ~53% agreement

The training labels came only from TextBlob, which wasn't built for social media. I added VADER as a second labeler — it understands ALL-CAPS, "!!!", and emojis, things TextBlob ignores — and an agreement analysis between the two in `metrics.json`.

The result was the most interesting part of the entire project: **the two agree on only ~53% of tweets**. On nearly half the corpus, each labeler thinks the other got it wrong. That's not implementation noise — it's evidence that "lexical sentiment" is a noisy proxy for what we actually want to measure, and it became the central argument for the project's natural next step: human annotation or a pre-trained model, instead of blindly trusting lexicon heuristics.

## TF-IDF with bigrams and a 4-model benchmark

A unigram `CountVectorizer` loses negation — "not good" becomes "good" as far as the classifier is concerned. I switched to `TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)`, which captures negations and compound expressions. And instead of keeping Naive Bayes just because it was already there, I ran a 4-model benchmark on the same split:

| model | accuracy | macro-F1 |
| --- | --- | --- |
| LinearSVC | **0.820** | **0.784** |
| LogisticRegression | 0.803 | 0.752 |
| ComplementNB | 0.729 | 0.701 |
| MultinomialNB | 0.731 | 0.651 |

LinearSVC won by a clear margin. The part I didn't expect: ComplementNB — designed specifically for imbalanced classes — beats MultinomialNB on macro-F1, because `negative` is the minority class in this dataset. The micro-average hides that imbalance; the macro exposes it.

## The column the original notebook ignored

The dataset always had a `date` column, and it was never used for anything. Now `metrics.json` summarizes the covered period, points out the most negative and most positive day, and `figures/sentiment_timeline.png` plots daily average polarity with TextBlob and VADER side by side. When the two curves diverge on a given day, that's a signal there's content that day only one of the two lexicons is picking up correctly.

## Topics without guessing k

`num_topics=5` in the original notebook was a number picked in the dark. With `--tune-topics`, the pipeline trains LDA for k ∈ {3, 5, 7, 10} and picks the one with the highest coherence — simplified UMass, computed over the document-term matrix itself, no extra dependency. On the 20k-tweet sample, k=3 won. `metrics.json` keeps every candidate's score, not just the winner, so I can audit the decision later.

## What I learned doing this

Determinism comes before everything else: fixed seeds on sampling, split, and LDA mean two runs produce the same `metrics.json`, and diffing that file became my version of a data scientist's code review. Vulnerabilities can come from where you least expect — Trivy found CVEs in `msgpack` and `setuptools` vendored *inside pip itself*, duplicated in the ensurepip wheel; the fix was removing ensurepip from the image and pointing the skip-dirs at the right path, and none of it was actually my dependency. Agreement between labelers is a nearly free quality metric: before training any model, measuring how much two heuristics agree with each other already tells you a lot about the ceiling of what can be learned from the data. And the notebook didn't die — it's still in the repository as a record of the original exploration; the pipeline is what it wanted to be when it grew up, and the source of truth is now tested code, not cell output.

## Where the pipeline stands now

64 tests, 97% coverage, a 95% threshold gating CI. `ruff` (lint + format) and `mypy` clean on every push, CI across a Python matrix, pipeline smoke on real data, Docker image scanned with Trivy and published to GHCR. The pipeline today has dual sentiment annotation, a 4-model benchmark, temporal trends, and coherence-based topic selection — and `metrics.json` is reproducible, the final artifact of the analysis, versioned right alongside the code.
