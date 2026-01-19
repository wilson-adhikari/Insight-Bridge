# ui/tabs/ml_tab.py
from __future__ import annotations

from typing import List
import json  # For pretty-printing metrics if dict

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTextEdit,
    QMessageBox,
    QScrollArea,
)
from PySide6.QtCore import Qt

from matplotlib.figure import Figure

from core.controller import Controller
from ui.widgets.column_panel import ColumnPanel
from ui.widgets.rules_editor import RulesEditor
from ui.widgets.plot_canvas import PlotCanvas
from ui.workers.ml_worker import MLWorker, run_ml_in_thread


class MLTab(QWidget):
    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        layout = QVBoxLayout(self)

        self.column_panel = ColumnPanel()

        top_row = QHBoxLayout()
        self.task_combo = QComboBox()
        self.task_combo.addItems(["regression", "classification", "clustering"])

        self.model_combo = QComboBox()
        self.target_combo = QComboBox()
        self.btn_train = QPushButton("Train Model")
        self.btn_apply = QPushButton("Add predictions/clusters to data")

        top_row.addWidget(QLabel("Task"))
        top_row.addWidget(self.task_combo)
        top_row.addWidget(QLabel("Model"))
        top_row.addWidget(self.model_combo)
        top_row.addWidget(QLabel("Target"))
        top_row.addWidget(self.target_combo)
        top_row.addWidget(self.btn_train)
        top_row.addWidget(self.btn_apply)

        self.status_label = QLabel("Status: Ready")
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)

        self.rules_editor = RulesEditor()
        self.canvas = PlotCanvas()

        # Scroll area for functional scrolling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setWidget(self.canvas)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.canvas.setMinimumSize(1600, 1200)

        layout.addWidget(self.column_panel)
        layout.addLayout(top_row)
        layout.addWidget(self.status_label)
        layout.addWidget(QLabel("Metrics & Info"))
        layout.addWidget(self.metrics_text)
        layout.addWidget(QLabel("Decision Rules (applied on add)"))
        layout.addWidget(self.rules_editor)
        layout.addWidget(self.scroll_area)

        self.task_combo.currentTextChanged.connect(self._on_task_changed)
        self.btn_train.clicked.connect(self._train_model)
        self.btn_apply.clicked.connect(self._apply_predictions)

        self._last_info = None

        # Populate model combo on startup
        self._on_task_changed(self.task_combo.currentText())

    def refresh_from_state(self):
        df = self.controller.state.active_df()
        schema = self.controller.state.active_schema()
        self.column_panel.set_columns([], [])
        self.target_combo.clear()

        if df is None or schema is None:
            self.status_label.setText("Status: No data loaded")
            return

        numeric_cols = [c.name for c in schema.columns.values() if c.logical_type == "numeric"]
        cat_cols = [c.name for c in schema.columns.values() if c.logical_type in ("categorical", "boolean")]

        self.column_panel.set_columns(numeric_cols, cat_cols)

        # Populate target combo with all columns initially
        self.target_combo.addItems(df.columns.tolist())

        task = self.task_combo.currentText()
        valid_targets = []
        if task == "regression":
            valid_targets = numeric_cols
        elif task == "classification":
            # Low-cardinality categorical + binary numeric
            valid_targets = cat_cols + [c for c in numeric_cols if df[c].nunique() <= 20]
        else:  # clustering
            valid_targets = []

        # Filter target combo
        self.target_combo.clear()
        if valid_targets:
            self.target_combo.addItems(valid_targets)
            self.target_combo.setEnabled(True)
        else:
            self.target_combo.setEnabled(False)

        self.status_label.setText(f"Status: Ready - {len(numeric_cols)} numeric, {len(cat_cols)} categorical columns")

    def _on_task_changed(self, task: str):
        self.model_combo.clear()
        self.target_combo.setEnabled(True)

        if task == "regression":
            self.model_combo.addItems(["linear", "rf"])
        elif task == "classification":
            self.model_combo.addItems(["logistic", "rf"])
        elif task == "clustering":
            self.model_combo.addItems(["kmeans"])
            self.target_combo.setEnabled(False)

        # Refresh target filtering when task changes
        self.refresh_from_state()

    def _train_model(self):
        # Clear plot safely
        empty_fig = Figure()
        self.canvas.draw_figure(empty_fig)

        self.status_label.setText("Status: Training...")
        self.metrics_text.clear()

        task = self.task_combo.currentText()
        model_name = self.model_combo.currentText()

        if not model_name:
            QMessageBox.warning(self, "Invalid", "Select a model (change task if combo empty).")
            self.status_label.setText("Status: Failed - no model")
            return

        target = self.target_combo.currentText() if task != "clustering" else None

        if task != "clustering" and not target:
            QMessageBox.warning(self, "Invalid", "Select a target column.")
            self.status_label.setText("Status: Failed - no target")
            return

        num_cols = self.column_panel.selected_numeric()
        cat_cols = self.column_panel.selected_categorical()

        # Remove target from features
        if target:
            if target in num_cols:
                num_cols.remove(target)
            if target in cat_cols:
                cat_cols.remove(target)

        if not num_cols and not cat_cols:
            QMessageBox.warning(self, "Invalid", "Select at least one feature column.")
            self.status_label.setText("Status: Failed - no features")
            return

        worker_func = {
            "regression": self.controller.train_regression_with_columns,
            "classification": self.controller.train_classification_with_columns,
            "clustering": self.controller.train_clustering_with_columns,
        }[task]

        worker = MLWorker(worker_func, model_name, target, num_cols, cat_cols)
        worker.finished.connect(self._on_trained)
        worker.error.connect(self._on_train_error)
        run_ml_in_thread(self, worker)

    def _on_trained(self, info):
        if info is None:
            self.status_label.setText("Status: Training failed")
            QMessageBox.warning(self, "Failed", "Training returned no result. Check selection/data.")
            return

        self._last_info = info
        self.status_label.setText("Status: Training successful")
        QMessageBox.information(self, "Success", "Model trained successfully!")

        # Pretty-print metrics
        if isinstance(info.metrics, dict):
            metrics_str = json.dumps(info.metrics, indent=2)
        else:
            metrics_str = str(info.metrics)
        self.metrics_text.setPlainText(f"Metrics:\n{metrics_str}")

        # Clear previous plot safely
        empty_fig = Figure(figsize=(1, 1))
        self.canvas.draw_figure(empty_fig)
        self.canvas.setFixedSize(400, 300)  # Small default

        # Create large figure for full scrolling
        fig = Figure(figsize=(40, 30))  # Extremely large → scroll to see whole graph
        has_plot = False

        if hasattr(info, "importance") and info.importance:
            ax1 = fig.add_subplot(121)
            importances = sorted(info.importance.items(), key=lambda x: abs(x[1]), reverse=True)[:20]
            if importances:
                cols, vals = zip(*importances)
                ax1.barh(cols, vals)
                ax1.set_title("Top 20 Feature Importance")
                ax1.invert_yaxis()
                has_plot = True

        if hasattr(info, "predicted") and hasattr(info, "actual"):
            ax2 = fig.add_subplot(122)
            ax2.scatter(info.actual, info.predicted, alpha=0.6)
            min_v = min(info.actual.min(), info.predicted.min())
            max_v = max(info.actual.max(), info.predicted.max())
            ax2.plot([min_v, max_v], [min_v, max_v], "r--", label="Perfect prediction")
            ax2.set_xlabel("Actual")
            ax2.set_ylabel("Predicted")
            ax2.set_title("Predicted vs Actual")
            ax2.legend()
            has_plot = True

        if has_plot:
            fig.suptitle("Model Results", fontsize=20)
            fig.tight_layout(rect=[0, 0.03, 1, 0.95])

            # Draw the large figure
            self.canvas.draw_figure(fig)

            # Resize canvas to exact pixel size → true scrolling of entire large plot
            dpi = fig.dpi
            width_px = int(fig.get_size_inches()[0] * dpi)
            height_px = int(fig.get_size_inches()[1] * dpi)
            self.canvas.setFixedSize(width_px, height_px)

    def _on_train_error(self, msg: str):
        self.status_label.setText("Status: Training error")
        QMessageBox.critical(self, "Training Error", f"Failed:\n{msg}")

    def _apply_predictions(self):
        if self._last_info is None:
            QMessageBox.warning(self, "No Model", "Train a model first.")
            return

        df = self.controller.state.active_df().copy()

        if hasattr(self._last_info, "predicted"):
            df["prediction"] = self._last_info.predicted
        if hasattr(self._last_info, "cluster_labels"):
            df["cluster_label"] = self._last_info.cluster_labels.astype(int)

        rules = self.rules_editor.rules()
        if rules:
            from ml.rules_engine import RulesEngine
            engine = RulesEngine()
            df = engine.apply_rules(df, rules)

        name = self.controller.state.active_table_name or "active"
        self.controller.state.tables[name] = df
        QMessageBox.information(self, "Applied", "Predictions/clusters (and rules) added to active data!")
        self.status_label.setText("Status: Predictions applied")