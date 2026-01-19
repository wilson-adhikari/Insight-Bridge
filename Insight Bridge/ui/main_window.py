# ui/main_window.py
from __future__ import annotations

import sys
import traceback

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox

from core.controller import Controller
from ui.tabs.data_tab import DataTab
from ui.tabs.cleaning_tab import CleaningTab
from ui.tabs.analysis_tab import AnalysisTab
from ui.tabs.visualization_tab import VisualizationTab
from ui.tabs.ml_tab import MLTab
from ui.tabs.reporting_tab import ReportingTab
from ui.tabs.join_tab import JoinTab
from ui.tabs.filter_tab import FilterTab


def global_exception_hook(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    print("=== UNHANDLED EXCEPTION (app would normally close silently) ===")
    print(error_msg)
    QMessageBox.critical(
        None,
        "Critical Error",
        f"An unexpected error occurred:\n\n{error_msg}\n\n"
        "The app will continue running if possible, but check console for details.",
    )
    # Do NOT sys.exit() - we want to see where it happens


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = Controller()
        self.setWindowTitle("Universal Data Analyzer")
        self.resize(1400, 900)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.data_tab = DataTab(self.controller, main_window=self)
        self.cleaning_tab = CleaningTab(self.controller)
        self.filter_tab = FilterTab(self.controller)
        self.analysis_tab = AnalysisTab(self.controller)
        self.visualization_tab = VisualizationTab(self.controller)
        self.ml_tab = MLTab(self.controller)
        self.join_tab = JoinTab(self.controller)
        self.reporting_tab = ReportingTab(self.controller)

        self.tabs.addTab(self.data_tab, "Data")
        self.tabs.addTab(self.cleaning_tab, "Cleaning")
        self.tabs.addTab(self.filter_tab, "Filter")
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.tabs.addTab(self.visualization_tab, "Visualization")
        self.tabs.addTab(self.ml_tab, "ML")
        self.tabs.addTab(self.join_tab, "Joins")
        self.tabs.addTab(self.reporting_tab, "Reporting")

    def refresh_tabs(self):
        print("\n=== Starting refresh_tabs() ===")
        try:
            print("Refreshing Data tab...")
            self.data_tab.refresh_tables()
            print("Data tab refreshed OK")
        except Exception as e:
            print(f"ERROR in Data tab refresh: {e}")
            traceback.print_exc()

        try:
            print("Refreshing Cleaning tab...")
            self.cleaning_tab.refresh_from_state()
            print("Cleaning tab refreshed OK")
        except Exception as e:
            print(f"ERROR in Cleaning tab refresh: {e}")
            traceback.print_exc()

        try:
            print("Refreshing Filter tab...")
            self.filter_tab.refresh_from_state()
            print("Filter tab refreshed OK")
        except Exception as e:
            print(f"ERROR in Filter tab refresh: {e}")
            traceback.print_exc()

        try:
            print("Refreshing Analysis tab...")
            self.analysis_tab.refresh_from_state()
            print("Analysis tab refreshed OK")
        except Exception as e:
            print(f"ERROR in Analysis tab refresh: {e}")
            traceback.print_exc()

        try:
            print("Refreshing Visualization tab...")
            self.visualization_tab.refresh_from_state()
            print("Visualization tab refreshed OK")
        except Exception as e:
            print(f"ERROR in Visualization tab refresh: {e}")
            traceback.print_exc()

        try:
            print("Refreshing ML tab...")
            self.ml_tab.refresh_from_state()
            print("ML tab refreshed OK")
        except Exception as e:
            print(f"ERROR in ML tab refresh: {e}")
            traceback.print_exc()

        try:
            print("Refreshing Joins tab...")
            self.join_tab.refresh_from_state()
            print("Joins tab refreshed OK")
        except Exception as e:
            print(f"ERROR in Joins tab refresh: {e}")
            traceback.print_exc()

        print("=== refresh_tabs() completed ===\n")


def run_app():
    sys.excepthook = global_exception_hook

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())