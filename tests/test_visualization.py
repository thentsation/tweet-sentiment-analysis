from pathlib import Path

import pandas as pd

from topics import train_lda
from visualization import plot_sentiment_distribution, plot_wordclouds

DOCS = pd.Series(
    [
        'covid vaccine health cases deaths virus spread',
        'mask lockdown stay home safe quarantine',
        'covid cases deaths hospital patients reports',
        'vaccine immune trial study development phase',
    ]
    * 3
)


def test_plot_sentiment_distribution_creates_file(tmp_path: Path) -> None:
    sentiments = pd.Series([0.5, -0.25, 0.0, 0.8, -0.7, 0.1, 0.3, -0.4] * 3)
    output_path = tmp_path / 'figures' / 'sentiment_distribution.png'

    plot_sentiment_distribution(sentiments, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_wordclouds_creates_one_file_per_topic(tmp_path: Path) -> None:
    lda, vectorizer = train_lda(DOCS, num_topics=2, max_features=100)

    paths = plot_wordclouds(lda, vectorizer, tmp_path / 'wordclouds')

    assert len(paths) == 2
    assert all(path.exists() and path.stat().st_size > 0 for path in paths)
    assert paths[0].name == 'wordcloud_topic_1.png'
    assert paths[1].name == 'wordcloud_topic_2.png'
