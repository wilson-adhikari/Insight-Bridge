# ui/tabs/visualization_tab.py
from __future__ import annotations

from typing import List

import math
import seaborn as sns
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QScrollArea,
)
from PySide6.QtCore import Qt

from core.controller import Controller
from ui.widgets.plot_canvas import PlotCanvas
from visualization.exporters import save_figure


class VisualizationTab(QWidget):
    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        layout = QVBoxLayout(self)

        controls = QHBoxLayout()
        self.chart_type = QComboBox()
        self.chart_type.addItems([
            "histogram", "scatter", "bar_counts", "line", "boxplot", "violin", "kde",
            "corr_heatmap", "pairplot", "multi_hist_subplots", "multi_line_overlay"
        ])

        self.x_combo = QComboBox()
        self.y_combo = QComboBox()

        self.btn_plot = QPushButton("Plot")
        self.btn_export = QPushButton("Export plot")

        controls.addWidget(QLabel("Chart"))
        controls.addWidget(self.chart_type)
        controls.addWidget(QLabel("X"))
        controls.addWidget(self.x_combo)
        controls.addWidget(QLabel("Y"))
        controls.addWidget(self.y_combo)
        controls.addWidget(self.btn_plot)
        controls.addWidget(self.btn_export)

        self.multi_col_list = QListWidget()
        self.multi_col_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.canvas = PlotCanvas()

        # Scroll area with functional scrolling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)  # Critical: canvas keeps large size → enables real scrolling
        self.scroll_area.setWidget(self.canvas)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Large minimum size → scroll bars always active/useful
        # self.canvas.setMinimumSize(1600, 1200)

        layout.addLayout(controls)
        layout.addWidget(QLabel("Columns for multi charts"))
        layout.addWidget(self.multi_col_list)
        layout.addWidget(self.scroll_area)

        self.setLayout(layout)

        self.btn_plot.clicked.connect(self.make_plot)
        self.btn_export.clicked.connect(self.export_plot)

    def refresh_from_state(self):
        df = self.controller.state.active_df()
        self.x_combo.clear()
        self.y_combo.clear()
        self.multi_col_list.clear()
        if df is not None:
            cols = df.columns.tolist()
            self.x_combo.addItems(cols)
            self.y_combo.addItems(cols)
            for c in cols:
                QListWidgetItem(c, self.multi_col_list)

    def make_plot(self):
        df = self.controller.state.active_df()
        if df is None:
            QMessageBox.warning(self, "No data", "Load a dataset first.")
            return

        # Safely clear previous plot
        empty_fig = Figure(figsize=(1, 1))
        self.canvas.draw_figure(empty_fig)
        self.canvas.setFixedSize(400, 300)  # Small default

        chart = self.chart_type.currentText()
        x = self.x_combo.currentText()
        y = self.y_combo.currentText()

        if "multi" in chart:
            selected_cols = [item.text() for item in self.multi_col_list.selectedItems()]
            if not selected_cols:
                QMessageBox.warning(self, "No columns", "Select columns for multi chart.")
                return
            if chart == "multi_hist_subplots":
                fig = self._make_multi_hist_subplots(df, selected_cols)
            else:
                fig = self._make_multi_line_overlay(df, selected_cols)
        else:
            if chart not in ("corr_heatmap", "pairplot") and not x:
                QMessageBox.warning(self, "Missing X", "Select an X column.")
                return

            if chart == "histogram":
                fig = self._make_histogram(df, x)
            elif chart == "scatter":
                if not y:
                    QMessageBox.warning(self, "Missing Y", "Select Y for scatter.")
                    return
                fig = self._make_scatter(df, x, y)
            elif chart == "line":
                if not y:
                    QMessageBox.warning(self, "Missing Y", "Select Y for line.")
                    return
                fig = self._make_line(df, x, y)
            elif chart == "bar_counts":
                fig = self._make_bar_counts(df, x)
            elif chart == "boxplot":
                fig = self._make_boxplot(df, x, y if y else None)
            elif chart == "violin":
                fig = self._make_violin(df, x, y if y else None)
            elif chart == "kde":
                fig = self._make_kde(df, x)
            elif chart == "corr_heatmap":
                fig = self._make_corr_heatmap(df)
            elif chart == "pairplot":
                fig = self._make_pairplot(df)
            else:
                return

        # Very large figure → guarantees scrolling works perfectly
        fig.set_size_inches(12, 8)  # Extremely large → you can scroll to see whole graph

        # Draw the large figure
        self.canvas.draw_figure(fig)

        # Resize canvas to exact pixel size of figure → true scrolling of entire graph
        dpi = fig.dpi
        width, height = fig.get_size_inches() * dpi
        self.canvas.setFixedSize(int(width), int(height))

    # ---------- Plot implementations ----------
    def _make_histogram(self, df, col) -> Figure:
        fig = Figure()
        ax = fig.add_subplot(111)
        sns.histplot(df[col].dropna(), bins=30, kde=True, ax=ax)
        ax.set_title(f"Histogram of {col}")
        return fig

    def _make_scatter(self, df, x, y) -> Figure:
        fig = Figure()
        ax = fig.add_subplot(111)
        sns.scatterplot(data=df, x=x, y=y, ax=ax)
        ax.set_title(f"{x} vs {y}")
        return fig

    def _make_line(self, df, x, y) -> Figure:
        fig = Figure()
        ax = fig.add_subplot(111)
        sns.lineplot(data=df, x=x, y=y, ax=ax)
        ax.set_title(f"{y} over {x}")
        return fig

    def _make_bar_counts(self, df, col) -> Figure:
        fig = Figure()
        ax = fig.add_subplot(111)
        df[col].value_counts().head(30).plot(kind="bar", ax=ax)
        ax.set_title(f"Top 30 counts of {col}")
        return fig

    def _make_boxplot(self, df, x, group=None) -> Figure:
        fig = Figure()
        ax = fig.add_subplot(111)
        if group:
            sns.boxplot(data=df, x=x, y=group, ax=ax)
        else:
            sns.boxplot(y=df[x], ax=ax)
        ax.set_title("Boxplot")
        return fig

    def _make_violin(self, df, x, group=None) -> Figure:
        fig = Figure()
        ax = fig.add_subplot(111)
        if group:
            sns.violinplot(data=df, x=x, y=group, ax=ax)
        else:
            sns.violinplot(y=df[x], ax=ax)
        ax.set_title("Violin plot")
        return fig

    def _make_kde(self, df, col) -> Figure:
        fig = Figure()
        ax = fig.add_subplot(111)
        sns.kdeplot(df[col].dropna(), ax=ax, fill=True)
        ax.set_title(f"KDE of {col}")
        return fig

    def _make_corr_heatmap(self, df) -> Figure:
        fig = Figure(figsize=(12, 10))
        ax = fig.add_subplot(111)
        corr = df.corr(numeric_only=True)
        sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax, fmt=".2f")
        ax.set_title("Correlation Heatmap")
        return fig

    def _make_pairplot(self, df) -> Figure:
        sample_df = df.sample(min(1000, len(df)))
        g = sns.pairplot(sample_df)
        return g.fig

    def _make_multi_hist_subplots(self, df, cols: List[str]) -> Figure:
        n = len(cols)
        n_cols_plot = 3  # More columns for wider layout
        n_rows = math.ceil(n / n_cols_plot)
        fig = Figure(figsize=(8 * n_cols_plot, 5 * n_rows))
        for idx, col in enumerate(cols, start=1):
            ax = fig.add_subplot(n_rows, n_cols_plot, idx)
            try:
                sns.histplot(df[col].dropna(), bins=30, kde=True, ax=ax)
                ax.set_title(col)
            except Exception as e:
                ax.text(0.5, 0.5, f"Error: {e}", ha="center", va="center")
        fig.tight_layout()
        return fig

    def _make_multi_line_overlay(self, df, cols: List[str]) -> Figure:
        fig = Figure(figsize=(16, 10))
        ax = fig.add_subplot(111)
        for col in cols:
            ax.plot(df.index, df[col], label=col)
        ax.set_xlabel("Index")
        ax.set_ylabel("Value")
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        fig.tight_layout()
        return fig

    def export_plot(self):
        if self.canvas.figure is None:
            QMessageBox.warning(self, "No plot", "Create a plot first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export plot", "", "PNG (*.png);;JPEG (*.jpg);;PDF (*.pdf)"
        )
        if path:

            save_figure(self.canvas.figure, path)
