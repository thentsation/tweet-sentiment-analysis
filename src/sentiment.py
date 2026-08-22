from typing import Literal

import pandas as pd
from nltk.downloader import download
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob

SentimentLabel = Literal['positive', 'negative', 'neutral']

VADER_THRESHOLD = 0.05

_VADER_ANALYZER: SentimentIntensityAnalyzer | None = None


def ensure_vader_lexicon() -> None:
    try:
        SentimentIntensityAnalyzer()
    except LookupError:
        download('vader_lexicon', quiet=True)


def get_vader_analyzer() -> SentimentIntensityAnalyzer:
    global _VADER_ANALYZER
    if _VADER_ANALYZER is None:
        ensure_vader_lexicon()
        _VADER_ANALYZER = SentimentIntensityAnalyzer()
    return _VADER_ANALYZER


def get_sentiment(text: str) -> float:
    return TextBlob(str(text)).sentiment.polarity


def get_vader_compound(text: str) -> float:
    return float(get_vader_analyzer().polarity_scores(str(text))['compound'])


def label_from_polarity(polarity: float) -> SentimentLabel:
    if polarity > 0:
        return 'positive'
    if polarity < 0:
        return 'negative'
    return 'neutral'


def label_from_vader_compound(
    compound: float, threshold: float = VADER_THRESHOLD
) -> SentimentLabel:
    if compound >= threshold:
        return 'positive'
    if compound <= -threshold:
        return 'negative'
    return 'neutral'


def label_agreement(
    labels_a: pd.Series, labels_b: pd.Series
) -> dict[str, float | dict[str, float]]:
    if len(labels_a) != len(labels_b):
        raise ValueError('séries de rótulos devem ter o mesmo tamanho')
    overall = float((labels_a == labels_b).mean())
    by_label = {
        str(label): float(
            (labels_a[labels_a == label] == labels_b[labels_a == label]).mean()
        )
        for label in sorted(labels_a.unique())
    }
    return {'overall': overall, 'by_label': by_label}


def add_sentiment_columns(
    df: pd.DataFrame, source_column: str = 'tweet_text'
) -> pd.DataFrame:
    if source_column not in df.columns:
        raise ValueError(f'coluna "{source_column}" não encontrada no dataframe')
    result = df.copy()
    result['sentiment'] = result[source_column].apply(get_sentiment)
    result['sentiment_label'] = result['sentiment'].apply(label_from_polarity)
    result['vader_compound'] = result[source_column].apply(get_vader_compound)
    result['vader_label'] = result['vader_compound'].apply(label_from_vader_compound)
    return result
