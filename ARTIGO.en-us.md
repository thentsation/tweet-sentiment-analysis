[🇧🇷 Português](ARTIGO.md) | 🇺🇸 English

# From notebook to production: productizing a tweet sentiment analysis pipeline

How an exploratory NLP notebook became a deterministic, tested, fully-typed pipeline with CI/CD — and, along the way, gained a second annotator, a model benchmark, temporal trends, and automatic topic selection.

## The starting point

The project started like most data science projects: a Jupyter notebook (`notebooks/tweetML.ipynb`) that loaded 179k COVID-19 tweets, ran TextBlob for sentiment, LDA for topics, and trained a Naive Bayes. It worked. And that was it.

The problem is that a notebook isn't an engineering artifact. It was missing everything that separates exploratory analysis from a pipeline you'd put your name on:

- All the logic lived in cells — re-running the analysis meant executing the entire notebook from scratch, with global state depending on execution order
- Zero automated tests — changing preprocessing meant praying the numbers wouldn't move
- `requirements.txt` with no version pinning (listing libraries that weren't even used)
- No CI, no lint, no type checking — nothing
- Results trapped in cell outputs: the classifier accuracy only existed inside the notebook

This article is the path from there to here.

## First stop: the foundation (extract, test, automate)

The rule I followed: **no new feature before the existing logic is covered by tests.** But before testing, there had to be something to test.

### Extracting the notebook into modules

Each cell became a module with one responsibility — and one test boundary:

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

The same analysis that lived in cells tied together by global variables became a pure `run_pipeline(config)` function: a frozen, validated `PipelineConfig` goes in, a `PipelineResult` + `reports/metrics.json` comes out. Today's CLI (`python src/main.py --sample 2000`) runs exactly what the notebook ran.

### Tests with synthetic fixtures

The dataset is 66 MB — tests can't depend on it (or on downloading anything). The fixtures build synthetic tweets that are clearly positive, negative, and neutral ("I love this amazing day", "I hate this terrible day", "The office opens at nine") and validate signs and boundaries: polarity-sign classification, confusion matrix shape, determinism under fixed seeds.

### CI that runs on every commit

Lint, format check, mypy (with `disallow_untyped_defs`), pytest with a coverage threshold across a Python 3.11/3.12 matrix, dependency auditing with pip-audit — and a **pipeline smoke** job that runs the real pipeline on a 500-tweet sample and asserts the reports exist. Unit tests won't catch "the CSV has no `date` column"; smoke will.

### Docker without surprises

Multi-stage image on `python:3.14-slim`, installs from the lockfile, non-root user, stopwords and the VADER lexicon pre-downloaded at build time — and the dataset bundled in. The whole pipeline runs anywhere Docker does: `docker run tweet-sentiment --sample 5000`. In CI, the image is scanned with Trivy and pushed to GHCR.

## The features: better tweets, better analyses

With the foundation in place, the attack on the quality problems the notebook hid.

### Tweet-specific cleaning

The notebook only did lowercase + stopwords. But tweets have truncated URLs (`https://t.co/...`), @mentions, "RT" prefixes, and hashtags — all of it became LDA and classifier features. The cleaning now strips URLs, mentions, and RT, and unwraps `#COVID19` into `COVID19` (the hashtag text is content; the `#` is punctuation).

### Two annotators instead of one

The training labels came only from TextBlob — which wasn't built for social media. I added **VADER** as a second annotator (it understands ALL-CAPS, "!!!", and emojis) and an agreement analysis in `metrics.json`. The result is the project's most interesting finding: **the two agree on only ~53% of tweets**. Each annotator thinks the other is wrong on nearly half the corpus. That's the clearest evidence that lexical labels are noisy proxies — and the central argument for the roadmap (human annotation or a pre-trained model).

### TF-IDF with bigrams + model benchmark

A unigram `CountVectorizer` loses "not good". Switching to `TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)` captures negations and compound expressions. And instead of trusting Naive Bayes on faith, a 4-model benchmark on the same split:

| model | accuracy | macro-F1 |
| --- | --- | --- |
| LinearSVC | **0.820** | **0.784** |
| LogisticRegression | 0.803 | 0.752 |
| ComplementNB | 0.729 | 0.701 |
| MultinomialNB | 0.731 | 0.651 |

LinearSVC wins by a clear margin. And ComplementNB — designed for imbalanced classes — beats MultinomialNB on macro-F1 precisely because `negative` is the minority class (micro-average hides it; macro exposes it).

### The temporal dimension the notebook ignored

The dataset has a `date` column and it was used for nothing. Now `metrics.json` summarizes the covered period, the most negative and most positive days, and `figures/sentiment_timeline.png` plots daily average polarity — TextBlob and VADER side by side. When the curves diverge on a given day, that's a signal the content there is captured by only one of the lexicons.

### Topics without guessing k

Picking `num_topics=5` was arbitrary. With `--tune-topics`, the pipeline trains LDA for k ∈ {3, 5, 7, 10} and picks the highest coherence (simplified UMass, computed over the document-term matrix itself — no extra dependencies). On the 20k-tweet sample, k=3 won. The `metrics.json` keeps every candidate's score for auditing.

## Lessons the tutorial doesn't tell you

1. **Determinism first.** Fixed seeds on sampling, split, and LDA mean two runs produce the same `metrics.json` — and diffing the metrics is the data scientist's code review.
2. **Vulnerabilities can come from where you least expect.** Trivy found CVEs in `msgpack` and `setuptools` *vendored inside pip* (duplicated in the ensurepip wheel). Fix: remove ensurepip from the image and point the skip-dirs at the right path. None of it was my dependency.
3. **Annotator agreement is a free quality metric.** Before training any model, measuring how much two heuristics agree tells you a lot about the ceiling of what you can learn.
4. **The notebook doesn't die.** It stays in the repository as a record of the original exploration. The pipeline is what the notebook *wanted to be* when it grew up — and the source of truth is the tested code, not the cell output.

## Final state

- 64 tests, 97% coverage, a 95% threshold blocking CI
- ruff (lint + format) and mypy clean, running on every push
- Python matrix CI, pipeline smoke on real data, Docker image scanned with Trivy and published to GHCR
- Pipeline with dual sentiment annotation, a 4-model benchmark, temporal trends, and coherence-based topic selection
- A reproducible `metrics.json` — the final analysis artifact, versioned alongside the code
