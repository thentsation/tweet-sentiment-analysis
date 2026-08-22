import pandas as pd

from topics import coherence_score, top_words_per_topic, train_lda, tune_num_topics

DOCS = pd.Series(
    [
        'covid vaccine health cases deaths virus spread',
        'mask lockdown stay home safe quarantine',
        'covid cases deaths hospital patients reports',
        'vaccine immune trial study development phase',
        'mask protection wear face covering safety',
        'cases total daily report august increase',
        'vaccine doses administered population campaign',
        'lockdown rules economy reopening stores',
    ]
    * 3
)


def test_train_lda_returns_requested_number_of_topics() -> None:
    lda, vectorizer = train_lda(DOCS, num_topics=3, max_features=100)

    assert lda.n_components == 3
    assert len(vectorizer.get_feature_names_out()) > 0


def test_train_lda_is_deterministic_with_same_seed() -> None:
    lda_a, _ = train_lda(DOCS, num_topics=2, max_features=100, random_state=42)
    lda_b, _ = train_lda(DOCS, num_topics=2, max_features=100, random_state=42)

    assert (lda_a.components_ == lda_b.components_).all()


def test_top_words_per_topic_returns_expected_shape() -> None:
    lda, vectorizer = train_lda(DOCS, num_topics=3, max_features=100)

    topics = top_words_per_topic(lda, vectorizer, num_words=5)

    assert len(topics) == 3
    assert all(len(words) == 5 for words in topics)
    vocabulary = set(vectorizer.get_feature_names_out())
    assert all(word in vocabulary for words in topics for word in words)


def test_top_words_per_topic_orders_by_relevance() -> None:
    lda, vectorizer = train_lda(DOCS, num_topics=2, max_features=100)

    topics = top_words_per_topic(lda, vectorizer, num_words=5)
    component = lda.components_[0]
    feature_names = vectorizer.get_feature_names_out()
    expected_first = str(feature_names[component.argmax()])

    assert topics[0][0] == expected_first


def test_coherence_score_is_finite_negative() -> None:
    lda, vectorizer = train_lda(DOCS, num_topics=2, max_features=100)
    matrix = vectorizer.transform(DOCS)

    score = coherence_score(lda, matrix, num_words=5)

    assert score < 0
    assert score > float('-inf')


def test_coherence_score_is_deterministic() -> None:
    lda, vectorizer = train_lda(DOCS, num_topics=2, max_features=100)
    matrix = vectorizer.transform(DOCS)

    assert coherence_score(lda, matrix, num_words=5) == coherence_score(
        lda, matrix, num_words=5
    )


def test_tune_num_topics_returns_scores_for_candidates() -> None:
    result = tune_num_topics(DOCS, candidates=(2, 3), max_features=100)

    assert result['best_num_topics'] in (2, 3)
    scores = result['scores']
    assert set(scores.keys()) == {'2', '3'}
    assert result['best_coherence'] == max(scores.values())


def test_tune_num_topics_skips_candidates_above_dataset() -> None:
    result = tune_num_topics(DOCS, candidates=(2, 100), max_features=100)

    assert result['best_num_topics'] == 2
    assert set(result['scores'].keys()) == {'2'}
