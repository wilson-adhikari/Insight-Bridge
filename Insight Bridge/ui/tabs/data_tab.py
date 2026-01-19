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
    def _load_local_sync(self, load_fn, name: str, path: str):
        try:
            load_fn(name, path)
            self.controller.state.active_table_name = name
            QMessageBox.information(self, "Success", f"Loaded {name} successfully!")
            self.refresh_tables()
            self._notify_main_window()
        except Exception as e:
            error_details = traceback.format_exc()  # full details
            QMessageBox.critical(self, "Load Failed", f"Could not load {Path(path).name}:\n\n{str(e)}\n\nDetails:\n{error_details}")
            print(error_details)  # also prints to terminal

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV file", "", "CSV Files (*.csv)")
        if not path: return
        name = Path(path).stem
        self._load_local_sync(self.controller.load_csv, name, path)
        self.refresh_tables()  # Updates combo and preview
        self._notify_main_window()  # Refreshes other tabs once

    def load_csv_multi(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select CSV files", "", "CSV Files (*.csv)")
        if not paths: return
        last_name = None
        for path in paths:
            name = Path(path).stem
            self._load_local_sync(self.controller.load_csv, name, path)
            last_name = name
        if last_name:
            self.controller.state.active_table_name = last_name

    def load_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel file", "", "Excel Files (*.xlsx *.xls)")
        if not path: return
        name = Path(path).stem
        self._load_local_sync(self.controller.load_excel, name, path)

    def load_excel_multi(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Excel files", "", "Excel Files (*.xlsx *.xls)")
        if not paths: return
        last_name = None
        for path in paths:
            name = Path(path).stem
            self._load_local_sync(self.controller.load_excel, name, path)
            last_name = name
        if last_name:
            self.controller.state.active_table_name = last_name

    def load_sql(self):
        conn_str, ok1 = QInputDialog.getText(self, "SQL connection", "Enter SQLAlchemy connection string:")
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
            error_details = traceback.format_exc()
            QMessageBox.critical(self, "SQL Error", f"Failed:\n{str(e)}\n\n{error_details}")

    def load_sql_multi(self):
        conn_str, ok1 = QInputDialog.getText(self, "SQL connection", "Enter SQLAlchemy connection string:")
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
            error_details = traceback.format_exc()
            QMessageBox.critical(self, "SQL Error", f"Failed:\n{str(e)}\n\n{error_details}")

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
            error_details = traceback.format_exc()
            self.info_label.setText("Data loaded but preview failed")
            self.preview_text.setPlainText(f"Error: {str(e)}\n\n{error_details}")

    def _notify_main_window(self):
        if self.main_window and hasattr(self.main_window, "refresh_tabs"):
            self.main_window.refresh_tabs()