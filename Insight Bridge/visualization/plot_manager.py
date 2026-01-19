# visualization/plot_manager.py
from __future__ import annotations

from typing import List, Sequence, Optional

import pandas as pd

from visualization.numeric_plots import (
    plot_histogram,
    plot_kde,
    plot_scatter,
    plot_line,
    plot_multi_hist_subplots,
    plot_multi_line_overlay,
    plot_corr_heatmap,
    plot_pairplot,
)
from visualization.categorical_plots import (
    plot_bar_counts,
    plot_boxplot,
    plot_violin,
    plot_cat_swarm,
)
from visualization.ml_plots import (
    feature_importance_plot,
    prediction_vs_actual,
    residual_plot,
    confusion_matrix_plot,
    roc_curve_plot,
)


class PlotManager:
    """
    Thin wrapper around all plotting functions.
    UI tabs call methods here instead of importing plotting modules directly.
    """

    # -------- Basic numeric plots --------
    def histogram(self, df: pd.DataFrame, column: str):
        return plot_histogram(df, column)

    def kde(self, df: pd.DataFrame, column: str):
        return plot_kde(df, column)

    def scatter(self, df: pd.DataFrame, x: str, y: str, hue: Optional[str] = None):
        return plot_scatter(df, x, y, hue=hue)

    def line_plot(self, df: pd.DataFrame, x: str, y: str, hue: Optional[str] = None):
        return plot_line(df, x, y, hue=hue)

    def multi_hist_subplots(self, df: pd.DataFrame, columns: List[str]):
        return plot_multi_hist_subplots(df, columns)

    def multi_line_overlay(self, df: pd.DataFrame, columns: List[str]):
        return plot_multi_line_overlay(df, columns)

    def corr_heatmap(self, df: pd.DataFrame):
        return plot_corr_heatmap(df)

    def pairplot(self, df: pd.DataFrame):
        return plot_pairplot(df)

    # -------- Categorical plots --------
    def bar_counts(self, df: pd.DataFrame, column: str):
        return plot_bar_counts(df, column)

    def boxplot(self, df: pd.DataFrame, x: str, y: str, hue: Optional[str] = None):
        return plot_boxplot(df, x, y, hue=hue)

    def violin(self, df: pd.DataFrame, x: str, y: str, hue: Optional[str] = None):
        return plot_violin(df, x, y, hue=hue)

    def swarm(self, df: pd.DataFrame, x: str, y: str, hue: Optional[str] = None):
        return plot_cat_swarm(df, x, y, hue=hue)

    # -------- ML-specific plots --------
    def ml_feature_importance(
        self,
        feature_names: List[str],
        importances: Sequence[float],
        title: str = "Feature importance",
        top_n: Optional[int] = None,
    ):
        return feature_importance_plot(
            feature_names=feature_names,
            importances=importances,
            title=title,
            top_n=top_n,
        )

    def ml_prediction_vs_actual(
        self,
        y_true,
        y_pred,
        title: str = "Prediction vs actual",
    ):
        return prediction_vs_actual(y_true, y_pred, title=title)

    def ml_residual_plot(
        self,
        y_true,
        y_pred,
        title: str = "Residual plot",
    ):
        return residual_plot(y_true, y_pred, title=title)

    def ml_confusion_matrix(
        self,
        y_true,
        y_pred,
        class_labels: Optional[List[str]] = None,
        title: str = "Confusion matrix",
        normalize: bool = False,
    ):
        return confusion_matrix_plot(
            y_true=y_true,
            y_pred=y_pred,
            class_labels=class_labels,
            title=title,
            normalize=normalize,
        )

    def ml_roc_curve(
        self,
        fpr,
        tpr,
        auc_value: float,
        title: str = "ROC curve",
    ):
        return roc_curve_plot(fpr, tpr, auc_value=auc_value, title=title)
