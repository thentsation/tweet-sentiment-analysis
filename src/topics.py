import numpy as np
import pandas as pd
from scipy.sparse import spmatrix
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer


def train_lda(
    texts: pd.Series,
    *,
    num_topics: int = 5,
    max_features: int = 3000,
    random_state: int = 42,
) -> tuple[LatentDirichletAllocation, CountVectorizer]:
    vectorizer = CountVectorizer(
        max_df=0.85, max_features=max_features, stop_words='english'
    )
    matrix = vectorizer.fit_transform(texts)
    lda = LatentDirichletAllocation(
        n_components=num_topics, random_state=random_state, n_jobs=-1
    )
    lda.fit(matrix)
    return lda, vectorizer


def top_words_per_topic(
    lda: LatentDirichletAllocation,
    vectorizer: CountVectorizer,
    *,
    num_words: int = 10,
) -> list[list[str]]:
    feature_names = vectorizer.get_feature_names_out()
    return [
        [str(feature_names[index]) for index in topic.argsort()[: -num_words - 1 : -1]]
        for topic in lda.components_
    ]


def coherence_score(
    lda: LatentDirichletAllocation,
    matrix: spmatrix,
    *,
    num_words: int = 10,
) -> float:
    """Coerência UMass simplificada: média de log((D(wi,wj) + 1) / D(wi))."""
    binary = matrix.tocsc()
    doc_freq = np.asarray((binary > 0).sum(axis=0)).ravel()
    total_sum = 0.0
    pairs = 0

    for topic in lda.components_:
        top_idx = topic.argsort()[: -num_words - 1 : -1]
        for position, word_i in enumerate(top_idx):
            docs_i = doc_freq[word_i]
            if docs_i == 0:
                continue
            co_occurrence = binary[:, top_idx[position + 1 :]].multiply(
                binary[:, [word_i]]
            )
            docs_ij = np.asarray((co_occurrence > 0).sum(axis=0)).ravel()
            total_sum += float(np.log((docs_ij + 1.0) / (docs_i + 1.0)).sum())
            pairs += len(docs_ij)

    return total_sum / pairs if pairs else 0.0


def tune_num_topics(
    texts: pd.Series,
    *,
    candidates: tuple[int, ...] = (3, 5, 7, 10),
    max_features: int = 3000,
    random_state: int = 42,
    num_words: int = 10,
) -> dict[str, float | int | dict[str, float]]:
    vectorizer = CountVectorizer(
        max_df=0.85, max_features=max_features, stop_words='english'
    )
    matrix = vectorizer.fit_transform(texts)

    best_num_topics = 0
    best_score = float('-inf')
    scores: dict[str, float] = {}

    for num_topics in candidates:
        if num_topics >= matrix.shape[0]:
            continue
        lda = LatentDirichletAllocation(
            n_components=num_topics, random_state=random_state, n_jobs=-1
        )
        lda.fit(matrix)
        score = coherence_score(lda, matrix, num_words=num_words)
        scores[str(num_topics)] = score
        if score > best_score:
            best_score = score
            best_num_topics = num_topics

    return {
        'best_num_topics': best_num_topics,
        'best_coherence': best_score,
        'scores': scores,
    }
