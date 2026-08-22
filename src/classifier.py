from dataclasses import dataclass

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB


@dataclass(frozen=True)
class ClassifierEvaluation:
    accuracy: float
    labels: list[str]
    confusion_matrix: list[list[int]]
    classification_report: str


@dataclass(frozen=True)
class TrainResult:
    classifier: MultinomialNB
    vectorizer: CountVectorizer
    evaluation: ClassifierEvaluation


def train_and_evaluate(
    texts: pd.Series,
    labels: pd.Series,
    *,
    max_features: int = 3000,
    test_size: float = 0.2,
    random_state: int = 42,
) -> TrainResult:
    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=test_size,
        random_state=random_state,
    )
    vectorizer = CountVectorizer(max_df=0.85, max_features=max_features)
    train_matrix = vectorizer.fit_transform(X_train)
    classifier = MultinomialNB()
    classifier.fit(train_matrix, y_train)

    test_matrix = vectorizer.transform(X_test)
    predictions = classifier.predict(test_matrix)
    sorted_labels = sorted(set(y_test) | set(predictions))

    evaluation = ClassifierEvaluation(
        accuracy=float(accuracy_score(y_test, predictions)),
        labels=sorted_labels,
        confusion_matrix=confusion_matrix(
            y_test, predictions, labels=sorted_labels
        ).tolist(),
        classification_report=classification_report(
            y_test,
            predictions,
            labels=sorted_labels,
            zero_division=0,
        ),
    )
    return TrainResult(
        classifier=classifier, vectorizer=vectorizer, evaluation=evaluation
    )


def predict(
    classifier: MultinomialNB, vectorizer: CountVectorizer, texts: list[str]
) -> list[str]:
    matrix = vectorizer.transform(texts)
    return [str(label) for label in classifier.predict(matrix)]
