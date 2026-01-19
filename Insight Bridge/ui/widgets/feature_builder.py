# ui/widgets/feature_builder.py
from __future__ import annotations
from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QMessageBox
)
from cleaning.feature_engineering import ArithmeticFeatureDef, FeatureEngineeringConfig


class FeatureBuilder(QWidget):
    """Simple UI to define arithmetic features like col_new = col_a / col_b."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._available_columns: List[str] = []
        self._features: List[ArithmeticFeatureDef] = []

        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.left_combo = QComboBox()
        self.op_combo = QComboBox()
        self.op_combo.addItems(["add", "sub", "mul", "div"])
        self.right_combo = QComboBox()
        btn_add = QPushButton("Add feature")

        row.addWidget(QLabel("New name"))
        row.addWidget(self.name_edit)
        row.addWidget(QLabel(" = "))
        row.addWidget(self.left_combo)
        row.addWidget(self.op_combo)
        row.addWidget(self.right_combo)
        row.addWidget(btn_add)

        layout.addLayout(row)
        self.setLayout(layout)

        btn_add.clicked.connect(self._on_add_clicked)

    def set_columns(self, cols: List[str]):
        self._available_columns = cols
        self.left_combo.clear()
        self.right_combo.clear()
        self.left_combo.addItems(cols)
        self.right_combo.addItems(cols)

    def _on_add_clicked(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid name", "Please enter a feature name.")
            return
        left = self.left_combo.currentText()
        right = self.right_combo.currentText()
        op = self.op_combo.currentText()
        feat = ArithmeticFeatureDef(name=name, left_col=left, right_col=right, op=op)  # type: ignore[arg-type]
        self._features.append(feat)
        self.name_edit.clear()

    def to_config(self) -> FeatureEngineeringConfig:
        cfg = FeatureEngineeringConfig()
        cfg.arithmetic_features = list(self._features)
        return cfg
