import json
from pathlib import Path

import pandas as pd
import pytest

from config import PipelineConfig
from pipeline import load_data, run_pipeline


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

    assert (config.output_dir / 'figures' / 'sentiment_distribution.png').exists()
    assert (
        config.output_dir / 'figures' / 'wordclouds' / 'wordcloud_topic_1.png'
    ).exists()
    assert (
        config.output_dir / 'figures' / 'wordclouds' / 'wordcloud_topic_2.png'
    ).exists()


def test_run_pipeline_is_deterministic(config: PipelineConfig) -> None:
    first = run_pipeline(config)
    second = run_pipeline(config)

    assert first.evaluation.accuracy == second.evaluation.accuracy
    assert first.topics == second.topics


def test_run_pipeline_on_real_data_sample() -> None:
    pytest.skip('executado apenas localmente com o dataset completo')
    df = pd.read_csv('data/covid19_tweets.csv')
    assert len(df) > 0
