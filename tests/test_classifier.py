import pandas as pd

from classifier import predict, train_and_evaluate
from preprocessing import preprocess_dataframe
from sentiment import add_sentiment_columns


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
