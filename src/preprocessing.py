import re

import pandas as pd
from nltk.corpus import stopwords
from nltk.downloader import download

URL_PATTERN = re.compile(r'https?://\S+|www\.\S+')
MENTION_PATTERN = re.compile(r'@\w+')
RETWEET_PATTERN = re.compile(r'^\s*rt\b[: ]?', re.IGNORECASE)
HASHTAG_PATTERN = re.compile(r'#(\w+)')
WHITESPACE_PATTERN = re.compile(r'\s+')

_STOPWORDS_CACHE: set[str] | None = None


def ensure_nltk_data() -> None:
    try:
        stopwords.words('english')
    except LookupError:
        download('stopwords', quiet=True)


def load_stopwords() -> set[str]:
    global _STOPWORDS_CACHE
    if _STOPWORDS_CACHE is None:
        ensure_nltk_data()
        _STOPWORDS_CACHE = set(stopwords.words('english'))
    return _STOPWORDS_CACHE


def clean_tweet(text: str) -> str:
    text = URL_PATTERN.sub(' ', str(text))
    text = MENTION_PATTERN.sub(' ', text)
    text = RETWEET_PATTERN.sub(' ', text)
    text = HASHTAG_PATTERN.sub(r'\1', text)
    return WHITESPACE_PATTERN.sub(' ', text).strip()


def preprocess_text(text: str) -> str:
    stop_words = load_stopwords()
    tokens = clean_tweet(text).lower().split()
    return ' '.join(word for word in tokens if word not in stop_words)


def preprocess_dataframe(df: pd.DataFrame, text_column: str = 'text') -> pd.DataFrame:
    if text_column not in df.columns:
        raise ValueError(f'coluna "{text_column}" não encontrada no dataframe')
    result = df.copy()
    result['tweet_text'] = result[text_column].apply(clean_tweet)
    result['clean_text'] = result['tweet_text'].apply(preprocess_text)
    return result
