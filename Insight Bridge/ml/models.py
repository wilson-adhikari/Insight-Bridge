# ml/models.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Any

from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.cluster import KMeans, DBSCAN


RegressionName = Literal["linear", "rf"]
ClassificationName = Literal["logistic", "rf"]
ClusteringName = Literal["kmeans", "dbscan"]


@dataclass
class ModelSpec:
    kind: Literal["regression", "classification", "clustering"]
    name: str
    params: dict[str, Any]


class ModelFactory:
    """Small factory that builds core sklearn estimators by name."""

    @staticmethod
    def create_regression(name: RegressionName, **kwargs) -> Any:
        if name == "linear":
            return LinearRegression(**kwargs)
        if name == "rf":
            return RandomForestRegressor(**kwargs)
        raise ValueError(f"Unknown regression model: {name}")

    @staticmethod
    def create_classification(name: ClassificationName, **kwargs) -> Any:
        if name == "logistic":
            return LogisticRegression(max_iter=1000, **kwargs)
        if name == "rf":
            return RandomForestClassifier(**kwargs)
        raise ValueError(f"Unknown classification model: {name}")

    @staticmethod
    def create_clustering(name: ClusteringName, **kwargs) -> Any:
        if name == "kmeans":
            return KMeans(**kwargs)
        if name == "dbscan":
            return DBSCAN(**kwargs)
        raise ValueError(f"Unknown clustering model: {name}")
