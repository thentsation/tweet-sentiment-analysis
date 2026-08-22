from typing import Literal

import pandas as pd
from textblob import TextBlob

SentimentLabel = Literal['positive', 'negative', 'neutral']


def get_sentiment(text: str) -> float:
    return TextBlob(str(text)).sentiment.polarity


def label_from_polarity(polarity: float) -> SentimentLabel:
    if polarity > 0:
        return 'positive'
    if polarity < 0:
        return 'negative'
    return 'neutral'


def add_sentiment_columns(
    df: pd.DataFrame, source_column: str = 'clean_text'
) -> pd.DataFrame:
    if source_column not in df.columns:
        raise ValueError(f'coluna "{source_column}" não encontrada no dataframe')
    result = df.copy()
    result['sentiment'] = result[source_column].apply(get_sentiment)
    result['sentiment_label'] = result['sentiment'].apply(label_from_polarity)
    return result
