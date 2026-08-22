import pandas as pd

from sentiment import add_sentiment_columns, get_sentiment, label_from_polarity


def test_get_sentiment_positive_text() -> None:
    assert get_sentiment('I love this amazing day') > 0


def test_get_sentiment_negative_text() -> None:
    assert get_sentiment('I hate this terrible day') < 0


def test_get_sentiment_neutral_text() -> None:
    assert get_sentiment('The office opens at nine') == 0


def test_label_from_polarity_boundaries() -> None:
    assert label_from_polarity(0.75) == 'positive'
    assert label_from_polarity(0.01) == 'positive'
    assert label_from_polarity(-0.75) == 'negative'
    assert label_from_polarity(-0.01) == 'negative'
    assert label_from_polarity(0.0) == 'neutral'


def test_add_sentiment_columns_adds_both_columns(sample_texts: pd.Series) -> None:
    df = pd.DataFrame({'clean_text': sample_texts})

    result = add_sentiment_columns(df)

    assert list(result.columns) == ['clean_text', 'sentiment', 'sentiment_label']
    assert set(result['sentiment_label']) == {'positive', 'negative', 'neutral'}


def test_add_sentiment_columns_labels_match_polarity_sign() -> None:
    df = pd.DataFrame(
        {'clean_text': ['I love this', 'I hate this', 'The office opens at nine']}
    )

    result = add_sentiment_columns(df)

    assert result.loc[0, 'sentiment'] > 0
    assert result.loc[0, 'sentiment_label'] == 'positive'
    assert result.loc[1, 'sentiment'] < 0
    assert result.loc[1, 'sentiment_label'] == 'negative'
    assert result.loc[2, 'sentiment_label'] == 'neutral'


def test_add_sentiment_columns_raises_for_missing_column() -> None:
    df = pd.DataFrame({'other': ['text']})

    try:
        add_sentiment_columns(df)
        raise AssertionError('deveria ter lançado ValueError')
    except ValueError as error:
        assert 'clean_text' in str(error)
