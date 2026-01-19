# ui/tabs/join_tab.py
from __future__ import annotations

from typing import List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)

from core.controller import Controller
from ingestion.data_manager import JoinPreviewConfig


class JoinTab(QWidget):
    """Preview joins (inner/left/right/outer) between any two loaded tables."""

    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        layout = QVBoxLayout(self)

        # Controls row
        controls = QHBoxLayout()
        self.left_table_combo = QComboBox()
        self.right_table_combo = QComboBox()
        self.join_col_combo = QComboBox()
        self.join_type_combo = QComboBox()
        self.join_type_combo.addItems(["inner", "left", "right", "outer"])

        self.btn_preview = QPushButton("Preview join")

        controls.addWidget(QLabel("Left table"))
        controls.addWidget(self.left_table_combo)
        controls.addWidget(QLabel("Right table"))
        controls.addWidget(self.right_table_combo)
        controls.addWidget(QLabel("Join column"))
        controls.addWidget(self.join_col_combo)
        controls.addWidget(QLabel("Join type"))
        controls.addWidget(self.join_type_combo)
        controls.addWidget(self.btn_preview)

        self.preview_table = QTableWidget()

        layout.addLayout(controls)
        layout.addWidget(self.preview_table)
        self.setLayout(layout)

        self.btn_preview.clicked.connect(self._preview_join)
        self.left_table_combo.currentTextChanged.connect(self._update_join_columns)
        self.right_table_combo.currentTextChanged.connect(self._update_join_columns)

    # Call this from MainWindow when tables change
    def refresh_from_state(self):
        self.left_table_combo.clear()
        self.right_table_combo.clear()
        table_names = list(self.controller.state.tables.keys())
        self.left_table_combo.addItems(table_names)
        self.right_table_combo.addItems(table_names)
        self._update_join_columns()

    def _update_join_columns(self):
        """Update join column combo to intersection of column names in both tables."""
        self.join_col_combo.clear()
        left_name = self.left_table_combo.currentText()
        right_name = self.right_table_combo.currentText()

        if not left_name or not right_name:
            return
        if left_name not in self.controller.state.tables or right_name not in self.controller.state.tables:
            return

        left_df = self.controller.state.tables[left_name]
        right_df = self.controller.state.tables[right_name]
        common_cols = [c for c in left_df.columns if c in right_df.columns]
        self.join_col_combo.addItems(common_cols)

    def _preview_join(self):
        left_name = self.left_table_combo.currentText()
        right_name = self.right_table_combo.currentText()
        join_col = self.join_col_combo.currentText()
        join_type = self.join_type_combo.currentText()

        if not left_name or not right_name or not join_col:
            QMessageBox.warning(self, "Missing selection", "Select both tables and a join column.")
            return

        left_df = self.controller.state.tables.get(left_name)
        right_df = self.controller.state.tables.get(right_name)
        if left_df is None or right_df is None:
            QMessageBox.warning(self, "Error", "Selected tables are not loaded.")
            return

        cfg = JoinPreviewConfig(on=join_col, how=join_type, limit=100)
        try:
            merged = self.controller.data_manager.preview_join(left_df, right_df, cfg)
        except Exception as e:
            QMessageBox.critical(self, "Join error", str(e))
            return

        # Show in table
        self._show_preview(merged)

    def _show_preview(self, df):
        self.preview_table.clear()
        if df is None or df.empty:
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            return

        n_rows = len(df)
        n_cols = len(df.columns)
        self.preview_table.setRowCount(n_rows)
        self.preview_table.setColumnCount(n_cols)
        self.preview_table.setHorizontalHeaderLabels(df.columns.tolist())

        for i in range(n_rows):
            for j, col in enumerate(df.columns):
                self.preview_table.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))
