import pandas as pd

from sentiment import (
    add_sentiment_columns,
    get_sentiment,
    get_vader_compound,
    label_agreement,
    label_from_polarity,
    label_from_vader_compound,
)


def test_get_sentiment_positive_text() -> None:
    assert get_sentiment('I love this amazing day') > 0


def test_get_sentiment_negative_text() -> None:
    assert get_sentiment('I hate this terrible day') < 0


def test_get_sentiment_neutral_text() -> None:
    assert get_sentiment('The office opens at nine') == 0


def test_get_vader_compound_positive_text() -> None:
    assert get_vader_compound('I love this AMAZING day!!!') > 0.5


def test_get_vader_compound_negative_text() -> None:
    assert get_vader_compound('I hate this terrible day') < -0.5


def test_get_vader_compound_neutral_text() -> None:
    compound = get_vader_compound('The office opens at nine')

    assert -0.05 < compound < 0.05


def test_label_from_polarity_boundaries() -> None:
    assert label_from_polarity(0.75) == 'positive'
    assert label_from_polarity(0.01) == 'positive'
    assert label_from_polarity(-0.75) == 'negative'
    assert label_from_polarity(-0.01) == 'negative'
    assert label_from_polarity(0.0) == 'neutral'


def test_label_from_vader_compound_thresholds() -> None:
    assert label_from_vader_compound(0.06) == 'positive'
    assert label_from_vader_compound(0.05) == 'positive'
    assert label_from_vader_compound(0.04) == 'neutral'
    assert label_from_vader_compound(-0.06) == 'negative'
    assert label_from_vader_compound(-0.05) == 'negative'
    assert label_from_vader_compound(0.0) == 'neutral'


def test_label_agreement_computes_overall_and_per_label() -> None:
    labels_a = pd.Series(['positive', 'positive', 'negative'])
    labels_b = pd.Series(['positive', 'negative', 'negative'])

    agreement = label_agreement(labels_a, labels_b)

    assert agreement['overall'] == 2 / 3
    by_label = agreement['by_label']
    assert isinstance(by_label, dict)
    assert by_label['positive'] == 0.5
    assert by_label['negative'] == 1.0


def test_label_agreement_raises_for_length_mismatch() -> None:
    try:
        label_agreement(pd.Series(['positive']), pd.Series(['positive', 'negative']))
        raise AssertionError('deveria ter lançado ValueError')
    except ValueError as error:
        assert 'mesmo tamanho' in str(error)


def test_add_sentiment_columns_adds_all_columns(sample_texts: pd.Series) -> None:
    df = pd.DataFrame({'tweet_text': sample_texts})

    result = add_sentiment_columns(df)

    assert list(result.columns) == [
        'tweet_text',
        'sentiment',
        'sentiment_label',
        'vader_compound',
        'vader_label',
    ]
    assert set(result['sentiment_label']) == {'positive', 'negative', 'neutral'}
    assert set(result['vader_label']) == {'positive', 'negative', 'neutral'}


def test_add_sentiment_columns_labels_match_scores() -> None:
    df = pd.DataFrame(
        {'tweet_text': ['I love this', 'I hate this', 'The office opens at nine']}
    )

    result = add_sentiment_columns(df)

    assert result.loc[0, 'sentiment_label'] == 'positive'
    assert result.loc[0, 'vader_label'] == 'positive'
    assert result.loc[1, 'sentiment_label'] == 'negative'
    assert result.loc[1, 'vader_label'] == 'negative'
    assert result.loc[2, 'vader_label'] == 'neutral'


def test_add_sentiment_columns_raises_for_missing_column() -> None:
    df = pd.DataFrame({'other': ['text']})

    try:
        add_sentiment_columns(df)
        raise AssertionError('deveria ter lançado ValueError')
    except ValueError as error:
        assert 'tweet_text' in str(error)
