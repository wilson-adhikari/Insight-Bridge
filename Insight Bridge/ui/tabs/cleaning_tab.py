# ui/tabs/cleaning_tab.py
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QHBoxLayout,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QTextEdit,
)

from core.controller import Controller
from cleaning.preprocessor import CleaningConfig
from cleaning.missing_value_handler import MissingStrategyConfig
from ui.widgets.feature_builder import FeatureBuilder


# ui/tabs/cleaning_tab.py
# ... (keep all imports)

class CleaningTab(QWidget):
    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        layout = QVBoxLayout(self)

        self.status_label = QLabel("Status: Configure strategies and run cleaning")

        # Add instructions for multi-select
        instructions = QLabel("Hold Ctrl (or Shift) to select multiple columns")
        instructions.setStyleSheet("color: blue; font-style: italic;")

        self.col_list = QListWidget()
        self.col_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Add "Select All" button for convenience
        select_row = QHBoxLayout()
        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self.col_list.selectAll)
        select_row.addWidget(self.btn_select_all)
        select_row.addStretch()

        strategy_row = QHBoxLayout()
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "drop", "mean", "median", "mode",
            "ffill", "bfill", "constant", "auto"
        ])
        self.btn_apply = QPushButton("Apply strategy to selected columns")
        strategy_row.addWidget(QLabel("Strategy"))
        strategy_row.addWidget(self.strategy_combo)
        strategy_row.addWidget(self.btn_apply)

        self.current_strategies_text = QTextEdit()
        self.current_strategies_text.setReadOnly(True)
        self.current_strategies_text.setMaximumHeight(120)

        self.feature_builder = FeatureBuilder()

        self.btn_run = QPushButton("Run Cleaning (apply all)")

        layout.addWidget(self.status_label)
        layout.addWidget(instructions)
        layout.addWidget(QLabel("Columns (multi-select enabled)"))
        layout.addWidget(self.col_list)
        layout.addLayout(select_row)
        layout.addLayout(strategy_row)
        layout.addWidget(QLabel("Current per-column strategies"))
        layout.addWidget(self.current_strategies_text)
        layout.addWidget(QLabel("Feature Engineering"))
        layout.addWidget(self.feature_builder)
        layout.addWidget(self.btn_run)

        # (rest unchanged)
        self._column_strategies: dict[str, str] = {}

        self.btn_apply.clicked.connect(self._apply_to_selected)
        self.btn_run.clicked.connect(self.run_cleaning)

    def refresh_from_state(self):
        df = self.controller.state.active_df()
        self.col_list.clear()
        self._column_strategies.clear()
        self._update_strategies_display()
        if df is not None:
            for col in df.columns:
                QListWidgetItem(col, self.col_list)
            self.feature_builder.set_columns(list(df.columns))

    def _apply_to_selected(self):
        items = self.col_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "No selection", "Select one or more columns first.")
            return
        strat = self.strategy_combo.currentText()
        for item in items:
            col = item.text()
            self._column_strategies[col] = strat
        self._update_strategies_display()
        self.status_label.setText(f"Status: Applied '{strat}' to {len(items)} columns")

    def _update_strategies_display(self):
        if not self._column_strategies:
            self.current_strategies_text.setPlainText("No per-column strategies set yet (auto/default will be used)")
            return
        lines = [f"{col}: {strat}" for col, strat in sorted(self._column_strategies.items())]
        self.current_strategies_text.setPlainText("\n".join(lines))

    def run_cleaning(self):
        df = self.controller.state.active_df()
        if df is None:
            QMessageBox.warning(self, "No data", "Load data first.")
            return

        cfg = CleaningConfig()
        for col, strat in self._column_strategies.items():
            cfg.missing_strategies[col] = MissingStrategyConfig(strategy=strat)

        cfg.feature_config = self.feature_builder.to_config()

        cleaned, report = self.controller.clean_active(cfg)
        if cleaned is None or report is None:
            QMessageBox.warning(self, "Failed", "Cleaning failed.")
            self.status_label.setText("Status: Cleaning failed")
            return

        msg = f"Cleaning complete!\n\nRows: {report.initial_shape[0]} → {report.final_shape[0]}\nColumns: {report.initial_shape[1]} → {report.final_shape[1]}"

        if report.validation_report:
            imb = len(report.validation_report.imbalance_warnings or [])
            out = len(report.validation_report.outlier_warnings or [])  # Fixed: it's a list, not dict
            msg += f"\n\nWarnings:\nImbalance: {imb} columns\nOutliers detected in: {out} columns"

        QMessageBox.information(self, "Success", msg)
        self.status_label.setText("Status: Cleaning successful")
        self._update_strategies_display()