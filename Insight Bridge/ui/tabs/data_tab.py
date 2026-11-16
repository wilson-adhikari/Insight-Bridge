# ui/tabs/data_tab.py
from __future__ import annotations

from pathlib import Path
import traceback  # for detailed error capture

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QLabel,
    QHBoxLayout,
    QComboBox,
    QTextEdit,
    QInputDialog,
    QMessageBox,
    QScrollArea,
    QLineEdit,
)
from PySide6.QtCore import Qt

from core.controller import Controller
from ui.workers.task import run_in_thread


class DataTab(QWidget):
    def __init__(self, controller: Controller, main_window=None):
        super().__init__()
        self.controller = controller
        self.main_window = main_window

        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self.btn_load_csv = QPushButton("Load CSV")
        self.btn_load_csv_multi = QPushButton("Load multiple CSVs")
        self.btn_load_excel = QPushButton("Load Excel")
        self.btn_load_excel_multi = QPushButton("Load multiple Excels")
        self.btn_load_xml = QPushButton("Load XML")
        self.btn_load_xml.clicked.connect(self.load_xml)
        btn_row.addWidget(self.btn_load_xml)
        self.btn_load_sql = QPushButton("Load SQL table")
        self.btn_load_sql_multi = QPushButton("Load multiple SQL tables")

        self.btn_load_csv.clicked.connect(self.load_csv)
        self.btn_load_csv_multi.clicked.connect(self.load_csv_multi)
        self.btn_load_excel.clicked.connect(self.load_excel)
        self.btn_load_excel_multi.clicked.connect(self.load_excel_multi)
        self.btn_load_sql.clicked.connect(self.load_sql)
        self.btn_load_sql_multi.clicked.connect(self.load_sql_multi)

        btn_row.addWidget(self.btn_load_csv)
        btn_row.addWidget(self.btn_load_csv_multi)
        btn_row.addWidget(self.btn_load_excel)
        btn_row.addWidget(self.btn_load_excel_multi)
        btn_row.addWidget(self.btn_load_sql)
        btn_row.addWidget(self.btn_load_sql_multi)

        self.table_selector = QComboBox()
        self.table_selector.currentTextChanged.connect(self.on_table_changed)

        self.info_label = QLabel("No dataset loaded.")

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFontFamily("Courier")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.preview_text)

        layout.addLayout(btn_row)
        layout.addWidget(self.table_selector)
        layout.addWidget(self.info_label)
        layout.addWidget(scroll)
        self.setLayout(layout)

    # ---------- Loading: read on a worker thread (D24), store on the GUI thread ----------
    def _start_load(self, read, sources):
        """read(source) -> DataFrame; sources is [(dataset name, source)]. Never overwrites a loaded dataset (D23)."""
        taken = set(self.controller.state.tables)
        jobs = []
        for base, src in sources:
            name, i = base, 2
            while name in taken:
                name = f"{base}_{i}"
                i += 1
            taken.add(name)
            jobs.append((name, src))
        self._set_busy(True)
        run_in_thread(self, self._read_all, read, jobs, on_done=self._on_loaded, on_error=self._on_load_error)

    def _read_all(self, read, jobs):
        """Runs on the worker thread: no widgets, no shared state. One bad file does not stop the others."""
        done, failed, skipped = [], [], 0
        for name, src in jobs:
            self.controller.last_skipped_rows = 0  # only read_csv sets it
            try:
                df = read(src)
                skipped += self.controller.last_skipped_rows
                done.append((name, *self.controller.prepare_loaded(df)))
            except Exception as e:
                traceback.print_exc()  # details go to the terminal only
                failed.append(f"{Path(str(src)).name}:\n\n{e}")
        return len(jobs), done, failed, skipped

    def _on_loaded(self, result):
        total, done, failed, skipped = result
        for name, df, schema in done:
            self.controller.store_loaded(name, df, schema)
        self._set_busy(False)
        for msg in failed:
            QMessageBox.critical(self, "Load Failed", f"Could not load {msg}")
        note = f"\n{skipped} malformed rows were skipped." if skipped else ""
        if total > 1:
            QMessageBox.information(self, "Done", f"Processed {total} files.{note}")
        elif done:
            QMessageBox.information(self, "Success", f"Loaded {done[0][0]} successfully!{note}")
        if done:
            self.refresh_tables()
            self._notify_main_window()

    def _on_load_error(self, msg: str):
        self._set_busy(False)
        QMessageBox.critical(self, "Load Failed", msg)

    def _set_busy(self, busy: bool):
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(not busy)
        if busy:
            self.info_label.setText("Loading…")

    def _load_files(self, read, multi: bool, title: str, pattern: str):
        if multi:
            paths = QFileDialog.getOpenFileNames(self, title, "", pattern)[0]
        else:
            path = QFileDialog.getOpenFileName(self, title, "", pattern)[0]
            paths = [path] if path else []
        if paths:
            self._start_load(read, [(Path(p).stem, p) for p in paths])

    def load_csv(self):
        self._load_files(self.controller.read_csv, False, "Select CSV file", "CSV Files (*.csv)")

    def load_csv_multi(self):
        self._load_files(self.controller.read_csv, True, "Select CSV files", "CSV Files (*.csv)")

    def load_excel(self):
        self._load_files(self.controller.read_excel, False, "Select Excel file", "Excel Files (*.xlsx)")

    def load_excel_multi(self):
        self._load_files(self.controller.read_excel, True, "Select Excel files", "Excel Files (*.xlsx)")

    def load_xml(self):
        self._load_files(self.controller.read_xml, False, "Select XML file", "XML Files (*.xml)")

    def _load_sql(self, prompt: str):
        conn_str, ok1 = QInputDialog.getText(self, "SQL connection", "Enter SQLAlchemy connection string:", QLineEdit.Password)
        if not ok1 or not conn_str.strip():
            return
        text, ok2 = QInputDialog.getText(self, "SQL tables", prompt)
        tables = [t.strip() for t in text.split(",") if t.strip()] if ok2 else []
        if tables:
            conn_str = conn_str.strip()
            self._start_load(lambda table: self.controller.read_sql_table(conn_str, table), [(t, t) for t in tables])

    def load_sql(self):
        self._load_sql("Enter table name:")

    def load_sql_multi(self):
        self._load_sql("Enter table names (comma-separated):")

    # ---------- Common ----------
    def refresh_tables(self):
        self.table_selector.blockSignals(True)  # Prevent signal during populate
        current_active = self.controller.state.active_table_name
        self.table_selector.clear()
        for name in self.controller.state.tables.keys():
            self.table_selector.addItem(name)
        if current_active and current_active in self.controller.state.tables:
            self.table_selector.setCurrentText(current_active)
        self.table_selector.blockSignals(False)
        self.update_preview()  # Safe preview update

    def on_table_changed(self, name: str):
        if not name:
            return
        # Only update state if actually changed
        if name != self.controller.state.active_table_name:
            self.controller.state.active_table_name = name
        self.update_preview()

    def update_preview(self):
        try:
            df = self.controller.state.active_df()
            if df is None:
                self.info_label.setText("No dataset loaded.")
                self.preview_text.clear()
                return

            preview_str = f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns\n\n"
            preview_str += "Columns and types:\n"
            preview_str += df.dtypes.to_string()
            self.info_label.setText(f"Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
            self.preview_text.setPlainText(preview_str)
        except Exception as e:
            traceback.print_exc()
            self.info_label.setText("Data loaded but preview failed")
            self.preview_text.setPlainText(f"Error: {e}")

    def _notify_main_window(self):
        if self.main_window and hasattr(self.main_window, "refresh_tabs"):
            self.main_window.refresh_tabs()