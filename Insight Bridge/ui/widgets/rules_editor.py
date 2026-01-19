# ui/widgets/rules_editor.py
from __future__ import annotations
from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QMessageBox
)
from ml.rules_engine import Rule


class RulesEditor(QWidget):
    """UI to define rules like: if prediction > threshold -> alert."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._available_sources: List[str] = []
        self._rules: List[Rule] = []

        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        self.source_combo = QComboBox()
        self.op_combo = QComboBox()
        self.op_combo.addItems([">", ">=", "<", "<=", "==", "!="])
        self.threshold_edit = QLineEdit()
        self.target_col_edit = QLineEdit()
        self.target_val_edit = QLineEdit()
        btn_add = QPushButton("Add rule")

        row.addWidget(QLabel("If"))
        row.addWidget(self.source_combo)
        row.addWidget(self.op_combo)
        row.addWidget(self.threshold_edit)
        row.addWidget(QLabel("then set"))
        row.addWidget(self.target_col_edit)
        row.addWidget(QLabel("to"))
        row.addWidget(self.target_val_edit)
        row.addWidget(btn_add)

        self.list = QListWidget()

        layout.addLayout(row)
        layout.addWidget(self.list)
        self.setLayout(layout)

        btn_add.clicked.connect(self._on_add_clicked)

    def set_source_columns(self, cols: List[str]):
        self._available_sources = cols
        self.source_combo.clear()
        self.source_combo.addItems(cols)

    def _on_add_clicked(self):
        src = self.source_combo.currentText()
        op = self.op_combo.currentText()
        thr_text = self.threshold_edit.text().strip()
        tgt_col = self.target_col_edit.text().strip()
        tgt_val = self.target_val_edit.text().strip()
        if not (src and thr_text and tgt_col):
            QMessageBox.warning(self, "Invalid rule", "Please fill all fields except value (optional).")
            return
        # try numeric threshold, fallback to string
        try:
            thr = float(thr_text)
        except ValueError:
            thr = thr_text
        val: str | bool | float = tgt_val or True
        rule = Rule(source_col=src, op=op, threshold=thr, target_col=tgt_col, target_value=val)  # type: ignore[arg-type]
        self._rules.append(rule)
        QListWidgetItem(f"{src} {op} {thr_text} -> {tgt_col} = {val}", self.list)
        self.threshold_edit.clear()
        self.target_col_edit.clear()
        self.target_val_edit.clear()

    def rules(self) -> List[Rule]:
        return list(self._rules)
