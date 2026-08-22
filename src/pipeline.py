import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from classifier import (
    ClassifierEvaluation,
    ModelScore,
    TrainResult,
    benchmark_models,
    train_and_evaluate,
)
from config import PipelineConfig
from preprocessing import preprocess_dataframe
from sentiment import add_sentiment_columns, label_agreement
from topics import top_words_per_topic, train_lda
from visualization import (
    plot_sentiment_distribution,
    plot_sentiment_timeline,
    plot_wordclouds,
)


@dataclass(frozen=True)
class PipelineResult:
    tweets_analyzed: int
    topics: list[list[str]]
    evaluation: ClassifierEvaluation
    benchmark: list[ModelScore]
    output_dir: Path


def load_data(config: PipelineConfig) -> pd.DataFrame:
    df = pd.read_csv(config.input_path)
    if config.text_column not in df.columns:
        raise ValueError(
            f'coluna "{config.text_column}" não encontrada em {config.input_path}'
        )
    df = df.dropna(subset=[config.text_column])
    if config.sample_size is not None and config.sample_size < len(df):
        df = df.sample(n=config.sample_size, random_state=config.random_state)
    return df.reset_index(drop=True)


def build_timeline(df: pd.DataFrame, date_column: str) -> pd.DataFrame | None:
    if date_column not in df.columns:
        return None
    dates = pd.to_datetime(df[date_column], errors='coerce')
    if dates.isna().all():
        return None
    timeline = pd.DataFrame(
        {
            'date': dates.dt.normalize(),
            'textblob': df['sentiment'],
            'vader': df['vader_compound'],
        }
    ).dropna(subset=['date'])
    if timeline.empty:
        return None
    return timeline.groupby('date', as_index=False).mean(numeric_only=True)


def timeline_summary(timeline: pd.DataFrame) -> dict[str, str | int]:
    textblob_row = timeline.loc[timeline['textblob'].idxmin()]
    vader_row = timeline.loc[timeline['vader'].idxmax()]
    return {
        'start': str(timeline['date'].min().date()),
        'end': str(timeline['date'].max().date()),
        'days': int(timeline['date'].nunique()),
        'most_negative_day': str(textblob_row['date'].date()),
        'most_positive_day': str(vader_row['date'].date()),
    }


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    df = load_data(config)
    df = preprocess_dataframe(df, config.text_column)
    df = df[df['clean_text'].str.strip().str.len() > 0].reset_index(drop=True)
    df = add_sentiment_columns(df)

    lda, lda_vectorizer = train_lda(
        df['clean_text'],
        num_topics=config.num_topics,
        max_features=config.max_features,
        random_state=config.random_state,
    )
    topics = top_words_per_topic(lda, lda_vectorizer, num_words=config.num_words)

    train_result: TrainResult = train_and_evaluate(
        df['clean_text'],
        df['sentiment_label'],
        max_features=config.max_features,
        test_size=config.test_size,
        random_state=config.random_state,
    )
    agreement = label_agreement(df['sentiment_label'], df['vader_label'])
    benchmark = benchmark_models(
        df['clean_text'],
        df['sentiment_label'],
        max_features=config.max_features,
        test_size=config.test_size,
        random_state=config.random_state,
    )

    figures_dir = config.output_dir / 'figures'
    plot_sentiment_distribution(
        df['sentiment'], figures_dir / 'sentiment_distribution.png'
    )
    timeline = build_timeline(df, config.date_column)
    if timeline is not None:
        plot_sentiment_timeline(timeline, figures_dir / 'sentiment_timeline.png')
    plot_wordclouds(lda, lda_vectorizer, figures_dir / 'wordclouds')

    write_metrics(
        config,
        train_result.evaluation,
        topics,
        len(df),
        agreement,
        benchmark,
        timeline_summary(timeline) if timeline is not None else None,
    )
    return PipelineResult(
        tweets_analyzed=len(df),
        topics=topics,
        evaluation=train_result.evaluation,
        benchmark=benchmark,
        output_dir=config.output_dir,
    )


def write_metrics(
    config: PipelineConfig,
    evaluation: ClassifierEvaluation,
    topics: list[list[str]],
    tweets_analyzed: int,
    agreement: dict[str, float | dict[str, float]],
    benchmark: list[ModelScore],
    timeline: dict[str, str | int] | None,
) -> None:
    metrics = {
        'tweets_analyzed': tweets_analyzed,
        'num_topics': config.num_topics,
        'sample_size': config.sample_size,
        'random_state': config.random_state,
        'accuracy': evaluation.accuracy,
        'confusion_matrix': evaluation.confusion_matrix,
        'labels': evaluation.labels,
        'classification_report': evaluation.classification_report,
        'label_agreement': agreement,
        'sentiment_timeline': timeline,
        'model_benchmark': [
            {
                'model': score.name,
                'accuracy': score.accuracy,
                'macro_f1': score.macro_f1,
            }
            for score in benchmark
        ],
        'topics': [
            {'topic': index + 1, 'top_words': words}
            for index, words in enumerate(topics)
        ],
    }
    config.output_dir.mkdir(parents=True, exist_ok=True)
    (config.output_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2))
