# visualization/ml_plots.py
from __future__ import annotations

from typing import List, Sequence, Optional

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix as sk_confusion_matrix


def feature_importance_plot(
    feature_names: List[str],
    importances: Sequence[float],
    title: str = "Feature importance",
    top_n: Optional[int] = None,
):
    importances = np.array(importances)
    order = np.argsort(importances)  # ascending
    if top_n is not None and top_n < len(order):
        order = order[-top_n:]
    names_sorted = [feature_names[i] for i in order]
    imps_sorted = importances[order]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(names_sorted, imps_sorted)
    ax.set_xlabel("Importance")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def prediction_vs_actual(y_true, y_pred, title: str = "Prediction vs actual"):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(y_true, y_pred, alpha=0.6)
    lo = min(y_true.min(), y_pred.min())
    hi = max(y_true.max(), y_pred.max())
    ax.plot([lo, hi], [lo, hi], "r--")
    ax.set_xlabel("Actual")
    ax.set_ylabel("Predicted")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def residual_plot(y_true, y_pred, title: str = "Residual plot"):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    residuals = y_true - y_pred
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(y_pred, residuals, alpha=0.6)
    ax.axhline(0, color="red", linestyle="--")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Residual (true - pred)")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def confusion_matrix_plot(
    y_true,
    y_pred,
    class_labels: Optional[List[str]] = None,
    title: str = "Confusion matrix",
    normalize: bool = False,
):
    if class_labels is None:
        class_labels = sorted(list(set(list(y_true) + list(y_pred))))
    cm = sk_confusion_matrix(y_true, y_pred, labels=class_labels)

    if normalize:
        cm = cm.astype("float") / cm.sum(axis=1, keepdims=True)

    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(
        cm,
        annot=True,
        fmt=".2f" if normalize else "d",
        cmap="Blues",
        xticklabels=class_labels,
        yticklabels=class_labels,
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title + (" (normalized)" if normalize else ""))
    fig.tight_layout()
    return fig


def roc_curve_plot(fpr, tpr, auc_value: float, title: str = "ROC curve"):
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(fpr, tpr, label=f"AUC = {auc_value:.3f}")
    ax.plot([0, 1], [0, 1], "k--")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(title)
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig
