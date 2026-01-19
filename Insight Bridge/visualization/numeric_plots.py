# visualization/numeric_plots.py
from __future__ import annotations

from typing import List, Optional

import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure


def plot_histogram(df: pd.DataFrame, column: str, bins: int = 30) -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    sns.histplot(df[column].dropna(), bins=bins, kde=False, ax=ax)
    ax.set_title(f"Histogram of {column}")
    fig.tight_layout()
    return fig


def plot_kde(df: pd.DataFrame, column: str) -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    sns.kdeplot(data=df, x=column, ax=ax)
    ax.set_title(f"KDE of {column}")
    fig.tight_layout()
    return fig


def plot_scatter(df: pd.DataFrame, x: str, y: str, hue: Optional[str] = None) -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    sns.scatterplot(data=df, x=x, y=y, hue=hue, ax=ax)
    ax.set_title(f"Scatter: {y} vs {x}")
    fig.tight_layout()
    return fig


def plot_line(df: pd.DataFrame, x: str, y: str, hue: Optional[str] = None) -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    sns.lineplot(data=df, x=x, y=y, hue=hue, ax=ax)
    ax.set_title(f"Line: {y} vs {x}")
    fig.tight_layout()
    return fig


def plot_multi_line_overlay(df: pd.DataFrame, columns: List[str]) -> Figure:
    fig = Figure(figsize=(8, 4))
    ax = fig.add_subplot(111)
    x_vals = df.index
    for col in columns:
        ax.plot(x_vals, df[col], label=col)
    ax.set_xlabel("Index")
    ax.set_ylabel("Value")
    ax.legend(loc="best")
    ax.set_title("Multi-line overlay")
    fig.tight_layout()
    return fig


def plot_multi_hist_subplots(df: pd.DataFrame, columns: List[str], bins: int = 30) -> Figure:
    import math

    n = len(columns)
    n_cols = 2
    n_rows = math.ceil(n / n_cols)
    fig = Figure(figsize=(6 * n_cols, 3 * n_rows))

    for idx, col in enumerate(columns, start=1):
        ax = fig.add_subplot(n_rows, n_cols, idx)
        sns.histplot(df[col].dropna(), bins=bins, kde=False, ax=ax)
        ax.set_title(col)

    fig.tight_layout()
    return fig


def plot_corr_heatmap(df: pd.DataFrame) -> Figure:
    numeric_df = df.select_dtypes(include="number")
    corr = numeric_df.corr()
    fig = Figure(figsize=(6, 5))
    ax = fig.add_subplot(111)
    sns.heatmap(corr, annot=False, cmap="coolwarm", ax=ax)
    ax.set_title("Correlation heatmap")
    fig.tight_layout()
    return fig


def plot_pairplot(df: pd.DataFrame) -> Figure:
    numeric_df = df.select_dtypes(include="number")
    g = sns.pairplot(numeric_df)
    return g.figure
