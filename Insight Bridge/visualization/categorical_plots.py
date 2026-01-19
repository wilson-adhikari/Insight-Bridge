# visualization/categorical_plots.py
from __future__ import annotations

from typing import Optional

import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure


def plot_bar_counts(df: pd.DataFrame, column: str) -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    sns.countplot(data=df, x=column, ax=ax)
    ax.set_title(f"Count plot of {column}")
    fig.tight_layout()
    return fig


def plot_boxplot(df: pd.DataFrame, x: str, y: str, hue: Optional[str] = None) -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    sns.boxplot(data=df, x=x, y=y, hue=hue, ax=ax)
    ax.set_title(f"Boxplot of {y} by {x}")
    fig.tight_layout()
    return fig


def plot_violin(df: pd.DataFrame, x: str, y: str, hue: Optional[str] = None) -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    sns.violinplot(data=df, x=x, y=y, hue=hue, ax=ax)
    ax.set_title(f"Violin plot of {y} by {x}")
    fig.tight_layout()
    return fig


def plot_cat_swarm(df: pd.DataFrame, x: str, y: str, hue: Optional[str] = None) -> Figure:
    """Optional: swarm plot to show all points by category."""
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    sns.swarmplot(data=df, x=x, y=y, hue=hue, ax=ax)
    ax.set_title(f"Swarm plot of {y} by {x}")
    fig.tight_layout()
    return fig
