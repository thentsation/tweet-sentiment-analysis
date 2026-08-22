import pandas as pd
from nltk.corpus import stopwords
from nltk.downloader import download

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


def preprocess_text(text: str) -> str:
    stop_words = load_stopwords()
    tokens = str(text).lower().split()
    return ' '.join(word for word in tokens if word not in stop_words)


def preprocess_dataframe(df: pd.DataFrame, text_column: str = 'text') -> pd.DataFrame:
    if text_column not in df.columns:
        raise ValueError(f'coluna "{text_column}" não encontrada no dataframe')
    result = df.copy()
    result['clean_text'] = result[text_column].apply(preprocess_text)
    return result
