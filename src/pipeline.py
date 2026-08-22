import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from classifier import ClassifierEvaluation, TrainResult, train_and_evaluate
from config import PipelineConfig
from preprocessing import preprocess_dataframe
from sentiment import add_sentiment_columns
from topics import top_words_per_topic, train_lda
from visualization import plot_sentiment_distribution, plot_wordclouds


@dataclass(frozen=True)
class PipelineResult:
    tweets_analyzed: int
    topics: list[list[str]]
    evaluation: ClassifierEvaluation
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

    figures_dir = config.output_dir / 'figures'
    plot_sentiment_distribution(
        df['sentiment'], figures_dir / 'sentiment_distribution.png'
    )
    plot_wordclouds(lda, lda_vectorizer, figures_dir / 'wordclouds')

    write_metrics(config, train_result.evaluation, topics, len(df))
    return PipelineResult(
        tweets_analyzed=len(df),
        topics=topics,
        evaluation=train_result.evaluation,
        output_dir=config.output_dir,
    )


def write_metrics(
    config: PipelineConfig,
    evaluation: ClassifierEvaluation,
    topics: list[list[str]],
    tweets_analyzed: int,
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
        'topics': [
            {'topic': index + 1, 'top_words': words}
            for index, words in enumerate(topics)
        ],
    }
    config.output_dir.mkdir(parents=True, exist_ok=True)
    (config.output_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2))
