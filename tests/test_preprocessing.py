import pandas as pd

from preprocessing import (
    clean_tweet,
    ensure_nltk_data,
    load_stopwords,
    preprocess_dataframe,
    preprocess_text,
)


def test_clean_tweet_removes_urls() -> None:
    assert clean_tweet('check this https://t.co/QZvYbrOgb0 now') == 'check this now'


def test_clean_tweet_removes_mentions() -> None:
    assert clean_tweet('hey @yankees @mlb great game') == 'hey great game'


def test_clean_tweet_removes_retweet_prefix() -> None:
    assert clean_tweet('RT @user: stay safe people') == ': stay safe people'


def test_clean_tweet_unwraps_hashtags() -> None:
    assert clean_tweet('the #COVID19 news #StayHome') == 'the COVID19 news StayHome'


def test_clean_tweet_collapses_whitespace() -> None:
    assert clean_tweet('too   many \n spaces') == 'too many spaces'


def test_preprocess_text_lowercases_and_removes_stopwords() -> None:
    result = preprocess_text('The Quick Brown Fox jumps over the lazy dog')

    assert result == 'quick brown fox jumps lazy dog'


def test_preprocess_text_strips_urls_and_mentions() -> None:
    result = preprocess_text('Check https://t.co/abc @user the vaccine news')

    assert result == 'check vaccine news'


def test_preprocess_text_removes_all_stopwords_to_empty() -> None:
    assert preprocess_text('The a an of') == ''


def test_preprocess_text_handles_non_string_input() -> None:
    assert preprocess_text(12345) == '12345'


def test_load_stopwords_contains_common_english_words() -> None:
    stopwords = load_stopwords()

    assert 'the' in stopwords
    assert 'fox' not in stopwords


def test_ensure_nltk_data_is_idempotent() -> None:
    ensure_nltk_data()

    assert load_stopwords()


def test_preprocess_dataframe_adds_tweet_and_clean_columns() -> None:
    df = pd.DataFrame({'text': ['The vaccine is great', 'I hate the virus']})

    result = preprocess_dataframe(df, 'text')

    assert list(result.columns) == ['text', 'tweet_text', 'clean_text']
    assert result.loc[0, 'tweet_text'] == 'The vaccine is great'
    assert result.loc[0, 'clean_text'] == 'vaccine great'
    assert result.loc[1, 'clean_text'] == 'hate virus'


def test_preprocess_dataframe_does_not_mutate_original() -> None:
    df = pd.DataFrame({'text': ['The vaccine is great']})

    preprocess_dataframe(df, 'text')

    assert 'clean_text' not in df.columns


def test_preprocess_dataframe_raises_for_missing_column() -> None:
    df = pd.DataFrame({'other': ['text']})

    try:
        preprocess_dataframe(df, 'text')
        raise AssertionError('deveria ter lançado ValueError')
    except ValueError as error:
        assert 'text' in str(error)
