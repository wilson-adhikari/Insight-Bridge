# ui/widgets/column_panel.py
from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
)


class ColumnPanel(QWidget):
    """Shows numeric and categorical columns with multi-selection support."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.num_label = QLabel("Numeric columns")
        self.num_list = QListWidget()
        self.num_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.cat_label = QLabel("Categorical columns")
        self.cat_list = QListWidget()
        self.cat_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        layout.addWidget(self.num_label)
        layout.addWidget(self.num_list)
        layout.addWidget(self.cat_label)
        layout.addWidget(self.cat_list)

        self.setLayout(layout)

    def set_columns(self, numeric_cols: List[str], categorical_cols: List[str]) -> None:
        """Populate the lists with available columns."""
        self.num_list.clear()
        self.cat_list.clear()

        for c in numeric_cols:
            QListWidgetItem(c, self.num_list)
        for c in categorical_cols:
            QListWidgetItem(c, self.cat_list)

    def selected_numeric(self) -> List[str]:
        """Return selected numeric column names."""
        return [i.text() for i in self.num_list.selectedItems()]

    def selected_categorical(self) -> List[str]:
        """Return selected categorical column names."""
        return [i.text() for i in self.cat_list.selectedItems()]
