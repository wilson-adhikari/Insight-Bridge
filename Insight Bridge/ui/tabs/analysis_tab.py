# ui/tabs/analysis_tab.py

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QMessageBox,
    QLabel,
    QComboBox,
)

from core.controller import Controller


class AnalysisTab(QWidget):
    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        layout = QVBoxLayout(self)

        # Top row: categorical analysis controls
        top_row = QHBoxLayout()
        self.cat_col_combo = QComboBox()
        self.btn_cat = QPushButton("Categorical analysis")
        top_row.addWidget(QLabel("Categorical column"))
        top_row.addWidget(self.cat_col_combo)
        top_row.addWidget(self.btn_cat)

        # Buttons for numeric + relationships
        self.btn_numeric = QPushButton("Numeric analysis")
        self.btn_relationships = QPushButton("Relationship hints")

        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        layout.addLayout(top_row)
        layout.addWidget(self.btn_numeric)
        layout.addWidget(self.btn_relationships)
        layout.addWidget(self.output)
        self.setLayout(layout)

        self.btn_numeric.clicked.connect(self.show_numeric)
        self.btn_relationships.clicked.connect(self.show_relationships)
        self.btn_cat.clicked.connect(self.show_categorical)

    # Call this from MainWindow when active table changes
    def refresh_from_state(self):
        df = self.controller.state.active_df()
        schema = self.controller.state.active_schema()
        self.cat_col_combo.clear()
        if df is None or schema is None:
            return
        cat_cols = [c.name for c in schema.columns.values() if c.logical_type == "categorical"]
        self.cat_col_combo.addItems(cat_cols)

    def show_numeric(self):
        result = self.controller.numeric_analysis()
        if result is None:
            QMessageBox.warning(self, "No data", "Load and clean a dataset first.")
            return
        lines = []
        for col, summary in result.summaries.items():
            lines.append(
                f"{col}: mean={summary.mean}, median={summary.median}, std={summary.std}, "
                f"skew={summary.skew}, kurt={summary.kurt}"
            )
        self.output.setPlainText("\n".join(lines))

    def show_categorical(self):
        col = self.cat_col_combo.currentText()
        if not col:
            QMessageBox.warning(self, "No column", "Select a categorical column.")
            return
        freq = self.controller.categorical_analysis(col)
        if freq is None:
            QMessageBox.warning(self, "No data", "Load and clean a dataset first.")
            return
        # Show top 30 categories as text
        self.output.setPlainText(str(freq.head(30)))

    def show_relationships(self):
        rels = self.controller.relationship_hints()
        if not rels:
            self.output.setPlainText("No relationships or data.")
            return
        lines = [
            f"{r.numeric_col} vs {r.categorical_col}: p-value={r.p_value:.4g}"
            for r in rels
        ]
        self.output.setPlainText("\n".join(lines))
