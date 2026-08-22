import pandas as pd
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
