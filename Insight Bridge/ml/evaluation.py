# ml/evaluation.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

import numpy as np
from sklearn.metrics import (
    r2_score,
    mean_squared_error,
    mean_absolute_error,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.metrics import silhouette_score


@dataclass
class RegressionMetrics:
    r2: float
    rmse: float
    mae: float


@dataclass
class ClassificationMetrics:
    accuracy: float
    f1: float
    precision: float
    recall: float
    confusion: np.ndarray
    roc_auc: float | None = None


@dataclass
class ClusteringMetrics:
    silhouette: float | None
    cluster_sizes: Dict[int, int]


def regression_metrics(y_true, y_pred) -> RegressionMetrics:
    rmse = mean_squared_error(y_true, y_pred, squared=False)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return RegressionMetrics(r2=r2, rmse=rmse, mae=mae)[web:118]


def classification_metrics(y_true, y_pred, y_proba=None) -> ClassificationMetrics:
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="weighted")
    prec = precision_score(y_true, y_pred, average="weighted")
    rec = recall_score(y_true, y_pred, average="weighted")
    cm = confusion_matrix(y_true, y_pred)
    roc_auc = None
    if y_proba is not None and y_proba.shape[1] == 2:
        roc_auc = roc_auc_score(y_true, y_proba[:, 1])
    return ClassificationMetrics(
        accuracy=acc,
        f1=f1,
        precision=prec,
        recall=rec,
        confusion=cm,
        roc_auc=roc_auc,
    )[web:109][web:115][web:112]


def clustering_metrics(X, labels) -> ClusteringMetrics:
    unique_labels = np.unique(labels)
    sizes = {int(lbl): int((labels == lbl).sum()) for lbl in unique_labels}
    sil = None
    # silhouette requires at least 2 clusters and no noise-only labels
    if len(unique_labels) > 1 and -1 not in unique_labels:
        sil = float(silhouette_score(X, labels))
    return ClusteringMetrics(silhouette=sil, cluster_sizes=sizes)[web:118]
