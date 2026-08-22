import pandas as pd

from classifier import (
    benchmark_models,
    build_vectorizer,
    predict,
    train_and_evaluate,
)
from preprocessing import preprocess_dataframe
from sentiment import add_sentiment_columns


def test_build_vectorizer_extracts_unigrams_and_bigrams() -> None:
    vectorizer = build_vectorizer(max_features=100)
    matrix = vectorizer.fit_transform(
        ['not good at all', 'stay home today', 'not bad result']
    )

    features = set(vectorizer.get_feature_names_out())

    assert 'not good' in features
    assert 'good' in features
    assert matrix.shape[0] == 3


def build_training_data() -> tuple[pd.Series, pd.Series]:
    texts = pd.Series(
        [
            'I love this amazing day',
            'I hate this terrible day',
            'The office opens at nine',
        ]
        * 20
    )
    df = add_sentiment_columns(preprocess_dataframe(pd.DataFrame({'text': texts})))
    return df['clean_text'], df['sentiment_label']


def test_train_and_evaluate_learns_separable_classes() -> None:
    texts, labels = build_training_data()

    result = train_and_evaluate(texts, labels, max_features=100, test_size=0.2)

    assert result.evaluation.accuracy >= 0.8


def test_train_and_evaluate_is_deterministic() -> None:
    texts, labels = build_training_data()

    first = train_and_evaluate(texts, labels, max_features=100, random_state=42)
    second = train_and_evaluate(texts, labels, max_features=100, random_state=42)

    assert first.evaluation.accuracy == second.evaluation.accuracy
    assert first.evaluation.confusion_matrix == second.evaluation.confusion_matrix


def test_train_and_evaluate_evaluation_fields(sample_texts: pd.Series) -> None:
    df = add_sentiment_columns(
        preprocess_dataframe(pd.DataFrame({'text': sample_texts * 4}))
    )

    result = train_and_evaluate(
        df['clean_text'], df['sentiment_label'], max_features=100
    )

    evaluation = result.evaluation
    assert 0.0 <= evaluation.accuracy <= 1.0
    assert set(evaluation.labels) == {'positive', 'negative', 'neutral'}
    assert len(evaluation.confusion_matrix) == len(evaluation.labels)
    assert all(
        len(row) == len(evaluation.labels) for row in evaluation.confusion_matrix
    )
    assert 'precision' in evaluation.classification_report
    assert 'recall' in evaluation.classification_report


def test_predict_returns_labels_for_new_texts() -> None:
    texts, labels = build_training_data()

    result = train_and_evaluate(texts, labels, max_features=100)

    predictions = predict(
        result.classifier, result.vectorizer, ['amazing love day', 'hate terrible day']
    )
    assert all(label in {'positive', 'negative', 'neutral'} for label in predictions)


def test_benchmark_models_covers_all_models() -> None:
    texts, labels = build_training_data()

    scores = benchmark_models(texts, labels, max_features=100)

    assert sorted(score.name for score in scores) == [
        'ComplementNB',
        'LinearSVC',
        'LogisticRegression',
        'MultinomialNB',
    ]
    assert all(0.0 <= score.accuracy <= 1.0 for score in scores)
    assert all(0.0 <= score.macro_f1 <= 1.0 for score in scores)


def test_benchmark_models_learns_separable_classes() -> None:
    texts, labels = build_training_data()

    scores = benchmark_models(texts, labels, max_features=100)

    best = scores[0]
    assert best.macro_f1 >= 0.8
    assert best.name in {
        'MultinomialNB',
        'ComplementNB',
        'LogisticRegression',
        'LinearSVC',
    }


def test_benchmark_models_is_deterministic() -> None:
    texts, labels = build_training_data()

    first = benchmark_models(texts, labels, max_features=100)
    second = benchmark_models(texts, labels, max_features=100)

    assert [(s.name, s.accuracy) for s in first] == [
        (s.name, s.accuracy) for s in second
    ]
