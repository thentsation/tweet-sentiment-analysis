import sys
from pathlib import Path

from config import PipelineConfig
from main import build_config, main, parse_args


def test_parse_args_defaults(monkeypatch) -> None:
    monkeypatch.setattr(sys, 'argv', ['main.py'])

    args = parse_args()

    assert args.input == 'data/covid19_tweets.csv'
    assert args.output == 'reports'
    assert args.text_column == 'text'
    assert args.sample is None
    assert args.num_topics == 5
    assert args.num_words == 10
    assert args.seed == 42


def test_parse_args_custom_values(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        'argv',
        ['main.py', '--input', 'outro.csv', '--sample', '100', '--num-topics', '3'],
    )

    args = parse_args()

    assert args.input == 'outro.csv'
    assert args.sample == 100
    assert args.num_topics == 3


def test_build_config_maps_args(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        'argv',
        ['main.py', '--input', 'tweets.csv', '--output', 'out', '--sample', '50'],
    )

    config = build_config(parse_args())

    assert config == PipelineConfig(
        input_path=Path('tweets.csv'),
        output_dir=Path('out'),
        sample_size=50,
    )


def test_main_runs_pipeline_end_to_end(
    monkeypatch, tiny_csv: Path, tmp_path: Path
) -> None:
    output_dir = tmp_path / 'reports'
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'main.py',
            '--input',
            str(tiny_csv),
            '--output',
            str(output_dir),
            '--num-topics',
            '2',
            '--num-words',
            '3',
        ],
    )

    main()

    assert (output_dir / 'metrics.json').exists()
    assert (output_dir / 'figures' / 'sentiment_distribution.png').exists()
    assert (output_dir / 'figures' / 'wordclouds' / 'wordcloud_topic_1.png').exists()
