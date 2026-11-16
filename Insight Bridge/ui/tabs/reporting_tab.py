# ui/tabs/reporting_tab.py
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QLabel,
    QHBoxLayout,
)

from core.controller import Controller


class ReportingTab(QWidget):
    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        layout = QVBoxLayout(self)

        # Report title + build button
        row1 = QHBoxLayout()
        self.report_title = QLineEdit("Analysis Report")
        btn_build = QPushButton("Build PDF report")
        row1.addWidget(QLabel("Title"))
        row1.addWidget(self.report_title)
        row1.addWidget(btn_build)

        # Export + session buttons
        btn_export_csv = QPushButton("Export active to CSV")
        btn_export_excel = QPushButton("Export active to Excel")
        btn_save_session = QPushButton("Save session")

        layout.addLayout(row1)
        layout.addWidget(btn_export_csv)
        layout.addWidget(btn_export_excel)
        layout.addWidget(btn_save_session)
        self.setLayout(layout)

        btn_build.clicked.connect(self._build_report)
        btn_export_csv.clicked.connect(self._export_csv)
        btn_export_excel.clicked.connect(self._export_excel)
        btn_save_session.clicked.connect(self._save_session)

    def _build_report(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF report",
            "",
            "PDF (*.pdf)",
        )
        if not path:
            return
        self._run("Report generated.", self.controller.build_basic_report, path, self.report_title.text() or "Analysis Report")

    def _run(self, done: str, fn, *args):
        try:
            fn(*args)
        except Exception as e:
            QMessageBox.critical(self, "Failed", str(e))
            return
        QMessageBox.information(self, "Done", done)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            "",
            "CSV (*.csv)",
        )
        if not path:
            return
        self._run("CSV exported.", self.controller.export_active_to_csv, path)

    def _export_excel(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Excel",
            "",
            "Excel (*.xlsx)",
        )
        if not path:
            return
        self._run("Excel file exported.", self.controller.export_active_to_excel, path)

    def _save_session(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save session",
            "",
            "Session (*.session.json)",
        )
        if not path:
            return

        session_name = Path(path).stem
        self._run("Session saved.", self.controller.save_session, session_name)