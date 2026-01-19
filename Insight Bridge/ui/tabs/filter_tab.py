# ui/tabs/filter_tab.py
from __future__ import annotations

from typing import List

import pandas as pd
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QLineEdit,
    QTextEdit,
    QMessageBox,
)

from core.controller import Controller


class FilterTab(QWidget):
    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        layout = QVBoxLayout(self)

        self.col_list = QListWidget()
        self.col_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        cond_row = QHBoxLayout()
        self.col_cond_combo = QComboBox()
        self.op_combo = QComboBox()
        self.op_combo.addItems([">", ">=", "<", "<=", "==", "!=", "contains", "in", "not in", "between"])
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Value(s), comma-separated for in/between")
        self.btn_add_cond = QPushButton("Add condition")

        cond_row.addWidget(QLabel("Column"))
        cond_row.addWidget(self.col_cond_combo)
        cond_row.addWidget(QLabel("Op"))
        cond_row.addWidget(self.op_combo)
        cond_row.addWidget(self.value_edit)
        cond_row.addWidget(self.btn_add_cond)

        self.conditions_view = QTextEdit()
        self.conditions_view.setReadOnly(True)

        self.btn_preview = QPushButton("Preview filtered")
        self.btn_apply = QPushButton("Apply filters → replace active data")

        layout.addWidget(QLabel("Columns"))
        layout.addWidget(self.col_list)
        layout.addLayout(cond_row)
        layout.addWidget(QLabel("Active conditions"))
        layout.addWidget(self.conditions_view)
        layout.addWidget(self.btn_preview)
        layout.addWidget(self.btn_apply)

        self.setLayout(layout)

        self._conditions: List[dict] = []

        self.btn_add_cond.clicked.connect(self._add_condition)
        self.btn_preview.clicked.connect(self._preview_filters)
        self.btn_apply.clicked.connect(self._apply_filters)

    def refresh_from_state(self):
        df = self.controller.state.active_df()
        self.col_list.clear()
        self.col_cond_combo.clear()
        if df is not None:
            cols = df.columns.tolist()
            for c in cols:
                QListWidgetItem(c, self.col_list)
            self.col_cond_combo.addItems(cols)

    def _add_condition(self):
        col = self.col_cond_combo.currentText()
        op = self.op_combo.currentText()
        val_text = self.value_edit.text().strip()
        if not col or not op or not val_text:
            QMessageBox.warning(self, "Invalid", "Fill column, operator, and value.")
            return
        self._conditions.append({"col": col, "op": op, "value": val_text})
        self._update_conditions_view()
        self.value_edit.clear()

    def _update_conditions_view(self):
        lines = [f"{c['col']} {c['op']} {c['value']}" for c in self._conditions]
        self.conditions_view.setPlainText("\n".join(lines))

    def _preview_filters(self):
        df = self.controller.state.active_df()
        if df is None or not self._conditions:
            QMessageBox.information(self, "Nothing", "Load data and add conditions.")
            return
        try:
            filtered = self._filter_dataframe(df, self._conditions)
            preview_rows = min(20, len(filtered))
            QMessageBox.information(
                self,
                "Preview",
                f"Rows after filter: {len(filtered)}\n\nFirst {preview_rows} rows:\n{filtered.head(preview_rows).to_string(index=False)}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _apply_filters(self):
        if not self._conditions:
            QMessageBox.information(self, "No conditions", "Add conditions first.")
            return
        if QMessageBox.question(self, "Confirm", "Replace active data with filtered version? (irreversible)") != QMessageBox.Yes:
            return

        df = self.controller.state.active_df()
        try:
            filtered = self._filter_dataframe(df, self._conditions)
            name = self.controller.state.active_table_name
            self.controller.state.tables[name] = filtered
            QMessageBox.information(self, "Applied", f"Active data now has {len(filtered)} rows.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _filter_dataframe(self, df: pd.DataFrame, conds: List[dict]) -> pd.DataFrame:
        mask = pd.Series(True, index=df.index)
        for c in conds:
            col, op, val_text = c["col"], c["op"], c["value"]
            if col not in df.columns:
                continue
            series = df[col]

            if op in ("in", "not in"):
                values = [v.strip() for v in val_text.split(",")]
            elif op == "between":
                parts = [v.strip() for v in val_text.split(",")]
                if len(parts) != 2:
                    raise ValueError("between needs low,high")
                low, high = parts
                try:
                    low, high = float(low), float(high)
                except ValueError:
                    pass
                cond_mask = (series >= low) & (series <= high)
                mask &= cond_mask
                continue
            else:
                try:
                    value = float(val_text)
                except ValueError:
                    value = val_text

            if op == ">":
                cond_mask = series > value
            elif op == ">=":
                cond_mask = series >= value
            elif op == "<":
                cond_mask = series < value
            elif op == "<=":
                cond_mask = series <= value
            elif op == "==":
                cond_mask = series == value
            elif op == "!=":
                cond_mask = series != value
            elif op == "contains":
                cond_mask = series.astype(str).str.contains(str(value), na=False)
            elif op == "in":
                cond_mask = series.isin(values)
            elif op == "not in":
                cond_mask = ~series.isin(values)
            else:
                continue

            mask &= cond_mask

        return df[mask]