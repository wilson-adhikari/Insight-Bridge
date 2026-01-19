# ml/pipelines.py
from __future__ import annotations
from typing import List, Dict

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.cluster import KMeans, DBSCAN


def make_preprocessor(numeric_cols: List[str], categorical_cols: List[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_cols),
            ("cat", categorical_pipeline, categorical_cols),
        ]
    )  # handles mixed types in one object[web:65][web:38]


def regression_pipeline(model: str, numeric_cols: List[str], categorical_cols: List[str]) -> Pipeline:
    pre = make_preprocessor(numeric_cols, categorical_cols)
    if model == "linear":
        estimator = LinearRegression()
    elif model == "rf":
        estimator = RandomForestRegressor(n_estimators=200, random_state=42)
    else:
        raise ValueError(f"Unknown regression model: {model}")
    return Pipeline(steps=[("preprocess", pre), ("model", estimator)])


def classification_pipeline(model: str, numeric_cols: List[str], categorical_cols: List[str]) -> Pipeline:
    pre = make_preprocessor(numeric_cols, categorical_cols)
    if model == "logistic":
        estimator = LogisticRegression(max_iter=1000)
    elif model == "rf":
        estimator = RandomForestClassifier(n_estimators=200, random_state=42)
    else:
        raise ValueError(f"Unknown classification model: {model}")
    return Pipeline(steps=[("preprocess", pre), ("model", estimator)])


def clustering_pipeline(model: str, numeric_cols: List[str]) -> Pipeline:
    # clustering only on numeric space here
    pre = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    if model == "kmeans":
        estimator = KMeans(n_clusters=3, random_state=42)
    elif model == "dbscan":
        estimator = DBSCAN(eps=0.5, min_samples=5)
    else:
        raise ValueError(f"Unknown clustering model: {model}")
    return Pipeline(steps=[("preprocess", pre), ("model", estimator)])
