# ui/widgets/warnings_panel.py
from __future__ import annotations
from typing import List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem


class WarningsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.label = QLabel("Data warnings")
        self.list = QListWidget()
        layout.addWidget(self.label)
        layout.addWidget(self.list)
        self.setLayout(layout)

    def set_warnings(self, messages: List[str]):
        self.list.clear()
        for m in messages:
            QListWidgetItem(m, self.list)
