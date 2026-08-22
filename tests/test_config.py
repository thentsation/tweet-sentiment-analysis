from pathlib import Path

import pytest

from config import PipelineConfig


def test_defaults() -> None:
    config = PipelineConfig()

    assert config.input_path == Path('data/covid19_tweets.csv')
    assert config.output_dir == Path('reports')
    assert config.text_column == 'text'
    assert config.num_topics == 5
    assert config.sample_size is None
    assert config.random_state == 42


def test_invalid_test_size_raises() -> None:
    with pytest.raises(ValueError, match='test_size'):
        PipelineConfig(test_size=1.5)


def test_zero_test_size_raises() -> None:
    with pytest.raises(ValueError, match='test_size'):
        PipelineConfig(test_size=0)


def test_invalid_num_topics_raises() -> None:
    with pytest.raises(ValueError, match='num_topics'):
        PipelineConfig(num_topics=1)


def test_invalid_sample_size_raises() -> None:
    with pytest.raises(ValueError, match='sample_size'):
        PipelineConfig(sample_size=0)


def test_invalid_max_features_raises() -> None:
    with pytest.raises(ValueError, match='max_features'):
        PipelineConfig(max_features=5)


def test_config_is_frozen() -> None:
    config = PipelineConfig()

    with pytest.raises(AttributeError):
        config.num_topics = 10  # type: ignore[misc]
