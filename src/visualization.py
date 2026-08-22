from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from wordcloud import WordCloud


def plot_sentiment_distribution(sentiments: pd.Series, output_path: Path) -> None:
    plt.figure(figsize=(8, 5))
    sns.histplot(sentiments, bins=30, kde=True, color='blue')
    plt.title('Sentiment Distribution in Tweets')
    plt.xlabel('Sentiment Polarity')
    plt.ylabel('Frequency')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_wordclouds(
    lda: LatentDirichletAllocation,
    vectorizer: CountVectorizer,
    output_dir: Path,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    feature_names = vectorizer.get_feature_names_out()
    paths: list[Path] = []
    for topic_index, topic in enumerate(lda.components_, start=1):
        frequencies = {
            str(feature_names[i]): float(topic[i]) for i in range(len(topic))
        }
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
        ).generate_from_frequencies(frequencies)
        output_path = output_dir / f'wordcloud_topic_{topic_index}.png'
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'Word Cloud for Topic #{topic_index}')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        paths.append(output_path)
    return paths
