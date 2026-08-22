from pathlib import Path

import pandas as pd
import pytest

from preprocessing import ensure_nltk_data
from sentiment import ensure_vader_lexicon


@pytest.fixture(scope='session', autouse=True)
def _nltk_data() -> None:
    ensure_nltk_data()
    ensure_vader_lexicon()


POSITIVE_TEXTS = [
    'I love this amazing day',
    'What a wonderful surprise, absolutely great',
    'Best news ever, so happy and grateful',
    'Fantastic work, truly impressive result',
    'Delightful experience, I am very satisfied',
]

NEGATIVE_TEXTS = [
    'I hate this terrible day',
    'What an awful surprise, absolutely horrible',
    'Worst news ever, so sad and angry',
    'Terrible work, truly disappointing result',
    'Dreadful experience, I am very upset',
]

NEUTRAL_TEXTS = [
    'The meeting is scheduled for Tuesday',
    'Prices were updated last night',
    'The report contains five chapters',
    'Data is stored in the cloud',
    'The office opens at nine',
]


@pytest.fixture
def sample_texts() -> pd.Series:
    return pd.Series(POSITIVE_TEXTS + NEGATIVE_TEXTS + NEUTRAL_TEXTS)


@pytest.fixture
def tiny_csv(tmp_path: Path) -> Path:
    rows = pd.DataFrame(
        {'text': POSITIVE_TEXTS * 6 + NEGATIVE_TEXTS * 6 + NEUTRAL_TEXTS * 6}
    )
    path = tmp_path / 'tweets.csv'
    rows.to_csv(path, index=False)
    return path
