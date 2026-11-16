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

    # ---------- Loading with max safety ----------
    def _load_local_sync(self, load_fn, name: str, path: str, quiet: bool = False) -> int:
        """Load one file; returns the number of malformed rows that were skipped."""
        base, i = name, 2
        while name in self.controller.state.tables:  # never overwrite a loaded dataset
            name = f"{base}_{i}"
            i += 1
        self.controller.last_skipped_rows = 0
        try:
            load_fn(name, path)
            self.controller.state.active_table_name = name
        except Exception as e:
            QMessageBox.critical(self, "Load Failed", f"Could not load {Path(path).name}:\n\n{e}")
            traceback.print_exc()  # details go to the terminal only
            return 0
        skipped = self.controller.last_skipped_rows
        if not quiet:
            note = f"\n{skipped} malformed rows were skipped." if skipped else ""
            QMessageBox.information(self, "Success", f"Loaded {name} successfully!{note}")
            self.refresh_tables()
            self._notify_main_window()
        return skipped

    def _load_many(self, load_fn, paths):
        skipped = sum(self._load_local_sync(load_fn, Path(p).stem, p, quiet=True) for p in paths)
        self.refresh_tables()
        self._notify_main_window()
        note = f"\n{skipped} malformed rows were skipped." if skipped else ""
        QMessageBox.information(self, "Done", f"Processed {len(paths)} files.{note}")

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV file", "", "CSV Files (*.csv)")
        if not path: return
        name = Path(path).stem
        self._load_local_sync(self.controller.load_csv, name, path)

    def load_csv_multi(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select CSV files", "", "CSV Files (*.csv)")
        if not paths: return
        self._load_many(self.controller.load_csv, paths)

    def load_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel file", "", "Excel Files (*.xlsx)")
        if not path: return
        name = Path(path).stem
        self._load_local_sync(self.controller.load_excel, name, path)

    def load_excel_multi(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Excel files", "", "Excel Files (*.xlsx)")
        if not paths: return
        self._load_many(self.controller.load_excel, paths)

    def load_xml(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select XML file", "", "XML Files (*.xml)")
        if not path: return
        self._load_local_sync(self.controller.load_xml, Path(path).stem, path)

    def load_sql(self):
        conn_str, ok1 = QInputDialog.getText(self, "SQL connection", "Enter SQLAlchemy connection string:", QLineEdit.Password)
        if not ok1 or not conn_str.strip(): return
        table_name, ok2 = QInputDialog.getText(self, "Table name", "Enter table name:")
        if not ok2 or not table_name.strip(): return
        name = table_name.strip()
        try:
            self.controller.load_sql_table(name, conn_str.strip(), table_name.strip())
            self.controller.state.active_table_name = name
            QMessageBox.information(self, "Success", f"Loaded SQL table {name}")
            self.refresh_tables()
            self._notify_main_window()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "SQL Error", f"Failed:\n{e}")

    def load_sql_multi(self):
        conn_str, ok1 = QInputDialog.getText(self, "SQL connection", "Enter SQLAlchemy connection string:", QLineEdit.Password)
        if not ok1 or not conn_str.strip(): return
        tables_text, ok2 = QInputDialog.getText(self, "SQL tables", "Enter table names (comma-separated):")
        if not ok2 or not tables_text.strip(): return
        table_names = [t.strip() for t in tables_text.split(",") if t.strip()]
        if not table_names: return
        try:
            self.controller.load_sql_tables(conn_str.strip(), table_names)
            self.controller.state.active_table_name = table_names[-1]
            QMessageBox.information(self, "Success", "Loaded multiple SQL tables")
            self.refresh_tables()
            self._notify_main_window()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "SQL Error", f"Failed:\n{e}")

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