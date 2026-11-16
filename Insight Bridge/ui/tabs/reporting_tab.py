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
from ui.workers.task import run_in_thread


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
        # Built here, not on a worker: matplotlib is not thread-safe and the other tabs draw on this thread.
        # shortcut: the report is a few text pages, so this is quick; move it off-thread if it ever renders big plots.
        try:
            self.controller.build_basic_report(path, self.report_title.text() or "Analysis Report")
        except Exception as e:
            QMessageBox.critical(self, "Failed", str(e))
            return
        QMessageBox.information(self, "Done", "Report generated.")

    def _run(self, done: str, fn, *args):
        """Export or save on a worker thread (D24); buttons stay disabled until it finishes."""
        self._done_message = done
        self._set_busy(True)
        run_in_thread(self, fn, *args, on_done=self._on_done, on_error=self._on_failed)

    def _set_busy(self, busy: bool):
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(not busy)

    def _on_done(self, _result):
        self._set_busy(False)
        QMessageBox.information(self, "Done", self._done_message)

    def _on_failed(self, msg: str):
        self._set_busy(False)
        QMessageBox.critical(self, "Failed", msg)

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