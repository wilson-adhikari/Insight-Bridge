"""Regression tests for docs/audit/TECHNICAL_DEBT.md defects D12, D14-D23, D25 (D24 is not fixed)."""
from pathlib import Path

import pytest

from test_defects import _controller, _frame


def _feature_cfg():
    from cleaning.feature_engineering import ArithmeticFeatureDef, FeatureEngineeringConfig
    from cleaning.preprocessor import CleaningConfig

    cfg = CleaningConfig()
    cfg.feature_config = FeatureEngineeringConfig(
        arithmetic_features=[ArithmeticFeatureDef("x_sum", "x1", "x2", "add")]
    )
    return cfg


# ---------------------------------------------------------------- D12
def test_d12_xml_import():
    from core.controller import Controller

    Path("d.xml").write_text(
        "<rows><row><a>1</a><b>x</b></row><row><a>2</a><b>y</b></row></rows>", encoding="utf-8"
    )
    ctrl = Controller()
    ctrl.load_xml("d", "d.xml")
    assert ctrl.state.active_df().shape == (2, 2)


def test_d12_readme_does_not_claim_chart_suggestions():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8").lower()
    assert "suggestion" not in readme and "recommends" not in readme


# ---------------------------------------------------------------- D14
def test_d14_schema_is_reinferred_and_ui_notified_after_cleaning():
    ctrl = _controller()
    calls = []
    ctrl.on_data_changed = lambda: calls.append(1)
    ctrl.clean_active(_feature_cfg())
    assert "x_sum" in ctrl.state.active_schema().columns
    assert calls


def test_d14_all_tabs_refresh_after_filter_apply(qapp, msgs):
    from ui.main_window import MainWindow

    w = MainWindow()
    w.controller._post_load_processing("t", _frame())
    w.refresh_tabs()
    w.filter_tab._conditions = [{"col": "x1", "op": ">", "value": "0"}]
    w.filter_tab._apply_filters()
    rows = len(w.controller.state.active_df())
    assert 0 < rows < 60
    assert f"{rows:,} rows" in w.data_tab.info_label.text()


# ---------------------------------------------------------------- D15
def test_d15_raw_copy_survives_cleaning_and_filtering(qapp, msgs):
    from ui.tabs.filter_tab import FilterTab

    ctrl = _controller()
    tab = FilterTab(ctrl)
    tab._conditions = [{"col": "x1", "op": ">", "value": "0"}]
    tab._apply_filters()
    ctrl.clean_active(_feature_cfg())
    assert len(ctrl.state.active_df()) < 60
    raw = ctrl.state.tables["t_raw"]
    assert len(raw) == 60 and "x_sum" not in raw.columns


# ---------------------------------------------------------------- D16
def test_d16_xls_is_not_offered(qapp, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    from ui.tabs.data_tab import DataTab

    filters = []
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (filters.append(a[3]), ("", ""))[1])
    )
    monkeypatch.setattr(
        QFileDialog, "getOpenFileNames", staticmethod(lambda *a, **k: (filters.append(a[3]), ([], ""))[1])
    )
    tab = DataTab(_controller())
    tab.load_excel()
    tab.load_excel_multi()
    assert len(filters) == 2
    assert all("*.xls" not in f.replace("*.xlsx", "") for f in filters)


# ---------------------------------------------------------------- D17
def test_d17_skipped_csv_rows_are_counted():
    from core.controller import Controller

    Path("bad.csv").write_text("a,b\n1,2\n3,4,5\n6,7\n", encoding="utf-8")
    ctrl = Controller()
    ctrl.load_csv("bad", "bad.csv")
    assert len(ctrl.state.active_df()) == 2
    assert ctrl.last_skipped_rows == 1


# ---------------------------------------------------------------- D18
def test_d18_report_and_exports_fail_loudly_without_data(qapp, msgs, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    from core.controller import Controller
    from ui.tabs.reporting_tab import ReportingTab

    ctrl = Controller()
    for fn in (ctrl.build_basic_report, ctrl.export_active_to_csv, ctrl.export_active_to_excel):
        with pytest.raises(ValueError):
            fn("out.bin")

    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: ("r.pdf", "")))
    ReportingTab(ctrl)._build_report()
    assert msgs["critical"] and not msgs["information"]


def test_d18_export_reports_success(qapp, msgs, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    from ui.tabs.reporting_tab import ReportingTab

    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: ("out.csv", "")))
    ReportingTab(_controller())._export_csv()
    assert Path("out.csv").exists() and msgs["information"] and not msgs["critical"]


# ---------------------------------------------------------------- D19
def test_d19_outlier_capping_is_configurable(qapp, msgs):
    from ui.tabs.cleaning_tab import CleaningTab

    df = _frame()
    df.loc[0, "x1"] = 1000.0
    ctrl = _controller(df)
    tab = CleaningTab(ctrl)
    tab.refresh_from_state()
    tab.run_cleaning()
    assert ctrl.state.active_df()["x1"].max() == 1000.0  # off by default: data untouched

    tab.chk_cap_outliers.setChecked(True)
    tab.run_cleaning()
    assert ctrl.state.active_df()["x1"].max() < 1000.0


# ---------------------------------------------------------------- D20
def test_d20_no_traceback_in_dialogs_and_masked_connection_string(qapp, msgs, monkeypatch):
    from PySide6.QtWidgets import QInputDialog, QLineEdit
    from ui.main_window import global_exception_hook
    from ui.tabs.data_tab import DataTab

    def boom(name, path):
        raise ValueError("bad file")

    tab = DataTab(_controller())
    tab._load_local_sync(boom, "n", "p.csv")
    try:
        raise ValueError("oops")
    except ValueError as e:
        global_exception_hook(type(e), e, e.__traceback__)
    assert len(msgs["critical"]) == 2
    for call in msgs["critical"]:
        assert "Traceback" not in " ".join(map(str, call))

    seen = []
    monkeypatch.setattr(QInputDialog, "getText", staticmethod(lambda *a, **k: (seen.append(a), ("", False))[1]))
    tab.load_sql()
    tab.load_sql_multi()
    assert len(seen) == 2 and all(QLineEdit.Password in a for a in seen)


# ---------------------------------------------------------------- D21
def test_d21_data_dirs_live_in_the_user_dir_not_the_cwd():
    from core.controller import Controller

    Controller()
    assert not Path("models").exists() and not Path("sessions").exists()
    assert (Path.home() / ".insightbridge" / "sessions").is_dir()
    assert (Path.home() / ".insightbridge" / "models").is_dir()


# ---------------------------------------------------------------- D22
def test_d22_unsafe_unreachable_code_is_gone():
    from ingestion.data_manager import DataManager
    from ml.persistence import ModelPersistence

    assert not hasattr(DataManager, "load_sql_incremental")  # string-built SQL
    assert not hasattr(ModelPersistence, "load")  # joblib.load (pickle) of files on disk


# ---------------------------------------------------------------- D23
def test_d23_same_stem_does_not_overwrite_and_multi_load_reports_once(qapp, msgs, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    from core.controller import Controller
    from ui.tabs.data_tab import DataTab

    Path("one").mkdir()
    Path("two").mkdir()
    Path("one/sales.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    Path("two/sales.csv").write_text("a,b\n3,4\n5,6\n", encoding="utf-8")
    ctrl = Controller()
    tab = DataTab(ctrl)
    monkeypatch.setattr(
        QFileDialog, "getOpenFileNames", staticmethod(lambda *a, **k: (["one/sales.csv", "two/sales.csv"], ""))
    )
    tab.load_csv_multi()
    assert len(ctrl.state.tables["sales"]) == 1 and len(ctrl.state.tables["sales_2"]) == 2
    assert len(msgs["information"]) == 1


# ---------------------------------------------------------------- D25
def test_d25_feature_builder_lists_and_removes_features(qapp, msgs):
    from ui.widgets.feature_builder import FeatureBuilder

    fb = FeatureBuilder()
    fb.set_columns(["a", "b"])
    fb.name_edit.setText("s")
    fb._on_add_clicked()
    assert fb.feature_list.count() == 1 and len(fb.to_config().arithmetic_features) == 1
    fb.feature_list.setCurrentRow(0)
    fb._remove_selected()
    assert fb.feature_list.count() == 0 and fb.to_config().arithmetic_features == []
