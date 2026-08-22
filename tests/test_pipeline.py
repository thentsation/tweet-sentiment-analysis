import json
from pathlib import Path

import pandas as pd
import pytest

from config import PipelineConfig
from pipeline import build_timeline, load_data, run_pipeline, timeline_summary


@pytest.fixture
def config(tiny_csv: Path, tmp_path: Path) -> PipelineConfig:
    return PipelineConfig(
        input_path=tiny_csv,
        output_dir=tmp_path / 'reports',
        num_topics=2,
        num_words=3,
        max_features=100,
    )


def test_load_data_reads_and_keeps_text_column(config: PipelineConfig) -> None:
    df = load_data(config)

    assert 'text' in df.columns
    assert len(df) == 90
    assert df['text'].notna().all()


def test_load_data_samples_deterministically(tiny_csv: Path) -> None:
    config = PipelineConfig(input_path=tiny_csv, sample_size=10, random_state=42)

    first = load_data(config)
    second = load_data(config)

    assert len(first) == 10
    assert list(first['text']) == list(second['text'])


def test_load_data_raises_for_missing_column(tiny_csv: Path) -> None:
    config = PipelineConfig(input_path=tiny_csv, text_column='missing')

    with pytest.raises(ValueError, match='missing'):
        load_data(config)


def test_run_pipeline_produces_reports(config: PipelineConfig) -> None:
    result = run_pipeline(config)

    assert result.tweets_analyzed == 90
    assert len(result.topics) == 2
    assert all(len(words) == 3 for words in result.topics)
    assert 0.0 <= result.evaluation.accuracy <= 1.0

    metrics_path = config.output_dir / 'metrics.json'
    assert metrics_path.exists()
    metrics = json.loads(metrics_path.read_text())
    assert metrics['tweets_analyzed'] == 90
    assert metrics['num_topics'] == 2
    assert len(metrics['topics']) == 2
    assert metrics['accuracy'] == result.evaluation.accuracy

    agreement = metrics['label_agreement']
    assert 0.0 <= agreement['overall'] <= 1.0
    assert set(agreement['by_label']) == {'positive', 'negative', 'neutral'}
    assert all(0.0 <= score <= 1.0 for score in agreement['by_label'].values())

    benchmark = metrics['model_benchmark']
    assert len(benchmark) == 4
    assert {'model', 'accuracy', 'macro_f1'} == set(benchmark[0].keys())
    f1_scores = [entry['macro_f1'] for entry in benchmark]
    assert f1_scores == sorted(f1_scores, reverse=True)

    assert (config.output_dir / 'figures' / 'sentiment_distribution.png').exists()
    assert (config.output_dir / 'figures' / 'sentiment_timeline.png').exists()
    assert (
        config.output_dir / 'figures' / 'wordclouds' / 'wordcloud_topic_1.png'
    ).exists()
    assert (
        config.output_dir / 'figures' / 'wordclouds' / 'wordcloud_topic_2.png'
    ).exists()

    timeline = metrics['sentiment_timeline']
    assert timeline is not None
    assert timeline['start'] == '2020-07-25'
    assert timeline['days'] == 5


def test_build_timeline_groups_by_day(config: PipelineConfig) -> None:
    from preprocessing import preprocess_dataframe
    from sentiment import add_sentiment_columns

    raw = load_data(config)
    processed = add_sentiment_columns(preprocess_dataframe(raw, 'text'))

    timeline = build_timeline(processed, 'date')

    assert timeline is not None
    assert list(timeline.columns) == ['date', 'textblob', 'vader']
    assert len(timeline) == 5
    assert timeline['date'].is_monotonic_increasing
    assert timeline['textblob'].between(-1, 1).all()


def test_build_timeline_returns_none_without_date_column() -> None:
    from preprocessing import preprocess_dataframe
    from sentiment import add_sentiment_columns

    df = pd.DataFrame({'text': ['great day', 'bad day'] * 3})
    processed = add_sentiment_columns(preprocess_dataframe(df, 'text'))

    assert build_timeline(processed, 'date') is None


def test_timeline_summary_reports_period() -> None:
    timeline = pd.DataFrame(
        {
            'date': pd.to_datetime(['2020-07-25', '2020-07-26', '2020-07-27']),
            'textblob': [0.2, -0.3, 0.1],
            'vader': [0.1, 0.0, 0.4],
        }
    )

    summary = timeline_summary(timeline)

    assert summary['start'] == '2020-07-25'
    assert summary['end'] == '2020-07-27'
    assert summary['days'] == 3
    assert summary['most_negative_day'] == '2020-07-26'
    assert summary['most_positive_day'] == '2020-07-27'


def test_run_pipeline_is_deterministic(config: PipelineConfig) -> None:
    first = run_pipeline(config)
    second = run_pipeline(config)

    assert first.evaluation.accuracy == second.evaluation.accuracy
    assert first.topics == second.topics


def test_run_pipeline_on_real_data_sample() -> None:
    pytest.skip('executado apenas localmente com o dataset completo')
    df = pd.read_csv('data/covid19_tweets.csv')
    assert len(df) > 0
