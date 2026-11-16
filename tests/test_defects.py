"""Regression tests for docs/audit/TECHNICAL_DEBT.md defects D1-D11, D13, D26.

Run from the repo root:  python -m pytest tests -q
Qt tests run headless (QT_QPA_PLATFORM=offscreen is set in conftest.py).
"""
import json
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def _frame(n=60):
    rng = np.random.default_rng(0)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    return pd.DataFrame(
        {
            "x1": x1,
            "x2": x2,
            "y": 2 * x1 + x2 + rng.normal(scale=0.1, size=n),
            "grp": ["a", "b"] * (n // 2),
            "city": ["ny", "LA", "ny"] * (n // 3),
        }
    )


def _controller(df=None):
    from core.controller import Controller

    ctrl = Controller()
    ctrl._post_load_processing("t", _frame() if df is None else df)
    return ctrl


def _wait(qapp, cond, timeout=20.0):
    end = time.time() + timeout
    while time.time() < end and not cond():
        qapp.processEvents()
        time.sleep(0.01)
    return cond()


def _stop_threads(tab):
    from PySide6.QtCore import QThread

    for t in tab.findChildren(QThread):
        t.quit()
        t.wait(2000)


@pytest.fixture
def stub_metrics(monkeypatch):
    """Isolate D4 tests from D2/D3 by stubbing the metric functions."""
    import ml.ml_manager as mm
    from ml.evaluation import ClassificationMetrics, ClusteringMetrics, RegressionMetrics

    monkeypatch.setattr(mm, "regression_metrics", lambda *a, **k: RegressionMetrics(0.0, 0.0, 0.0))
    monkeypatch.setattr(
        mm,
        "classification_metrics",
        lambda *a, **k: ClassificationMetrics(1.0, 1.0, 1.0, 1.0, np.eye(2)),
    )
    monkeypatch.setattr(mm, "clustering_metrics", lambda *a, **k: ClusteringMetrics(None, {}))


# ---------------------------------------------------------------- D1
def test_d1_ml_worker_is_kept_alive_and_runs(qapp, msgs):
    from ui.tabs.ml_tab import MLTab

    ctrl = _controller()
    ctrl.train_regression_with_columns = lambda *a: "result"
    tab = MLTab(ctrl)
    tab.refresh_from_state()
    tab.column_panel.num_list.selectAll()
    tab.target_combo.setCurrentText("y")
    got = []
    tab._on_trained = lambda info: got.append(info)
    try:
        tab._train_model()
        assert _wait(qapp, lambda: got == ["result"]), "worker never ran (garbage-collected)"
        assert _wait(qapp, lambda: tab.btn_train.isEnabled() and tab._ml_thread is None)
    finally:
        _stop_threads(tab)


# ---------------------------------------------------------------- D2 / D3
def test_d3_regression_metrics_work_on_current_sklearn():
    from ml.evaluation import regression_metrics

    m = regression_metrics([1.0, 2.0, 3.0], [1.0, 2.0, 5.0])
    assert m.rmse == pytest.approx(np.sqrt(4 / 3))
    assert m.mae == pytest.approx(2 / 3)


def test_d2_classification_and_clustering_metrics_have_no_citation_markers():
    from ml.evaluation import classification_metrics, clustering_metrics

    c = classification_metrics(np.array([0, 1, 1, 0]), np.array([0, 1, 0, 0]))
    assert c.accuracy == pytest.approx(0.75)
    k = clustering_metrics(np.array([[0.0], [0.1], [5.0], [5.1]]), np.array([0, 0, 1, 1]))
    assert k.cluster_sizes == {0: 2, 1: 2}


# ---------------------------------------------------------------- D4
def test_d4_regression_plots_and_prediction_column(qapp, msgs, stub_metrics):
    from ui.tabs.ml_tab import MLTab

    ctrl = _controller()
    tab = MLTab(ctrl)
    info = ctrl.train_regression_with_columns("rf", "y", ["x1", "x2"], [])
    tab._on_trained(info)
    assert len(tab.canvas.figure.axes) == 2  # feature importance + predicted vs actual
    tab._apply_predictions()
    out = ctrl.state.active_df()
    assert out["prediction"].notna().all() and len(out) == 60


def test_d4_classification_adds_prediction_column(qapp, msgs, stub_metrics):
    from ui.tabs.ml_tab import MLTab

    ctrl = _controller()
    tab = MLTab(ctrl)
    info = ctrl.train_classification_with_columns("logistic", "grp", ["x1", "x2"], [])
    tab._on_trained(info)
    tab._apply_predictions()
    assert set(ctrl.state.active_df()["prediction"]) <= {"a", "b"}


def test_d4_clustering_tuple_is_unpacked_and_labels_applied(qapp, msgs, stub_metrics):
    from ui.tabs.ml_tab import MLTab

    ctrl = _controller()
    tab = MLTab(ctrl)
    result = ctrl.train_clustering_with_columns("kmeans", ["x1", "x2"], [])
    tab._on_trained(result)
    assert tab._last_info is result[0]
    tab._apply_predictions()
    assert ctrl.state.active_df()["cluster_label"].nunique() == 3


# ---------------------------------------------------------------- D5
def test_d5_export_csv_writes_active_dataframe():
    ctrl = _controller()
    ctrl.export_active_to_csv("out.csv")
    assert pd.read_csv("out.csv").shape == (60, 5)


# ---------------------------------------------------------------- D6
def test_d6_save_session_serialises_models():
    from ml.evaluation import ClassificationMetrics
    from ml.ml_manager import TrainedModelInfo

    ctrl = _controller()
    ctrl.ml_manager.models["clf_rf_grp"] = TrainedModelInfo(
        key="clf_rf_grp",
        kind="classification",
        model_name="rf",
        target_col="grp",
        metrics=ClassificationMetrics(1.0, 1.0, 1.0, 1.0, np.eye(2)),  # numpy array inside
    )
    ctrl.save_session("s")
    session_file = Path(ctrl.config.sessions_dir) / "s.session.json"
    data = json.loads(session_file.read_text(encoding="utf-8"))
    assert data["active_dataset_name"] == "t"
    assert "clf_rf_grp" in data["models"]


# ---------------------------------------------------------------- D7
@pytest.mark.parametrize(
    "strategy, expected",
    [("ffill", [-1.0, 2.0, 2.0, 4.0]), ("bfill", [2.0, 2.0, 4.0, 4.0])],
)
def test_d7_ffill_bfill_work_on_current_pandas(strategy, expected):
    from cleaning.missing_value_handler import MissingStrategyConfig, MissingValueHandler

    df = pd.DataFrame({"a": [np.nan, 2.0, np.nan, 4.0]})
    out = MissingValueHandler().apply(df, {"a": "numeric"}, {"a": MissingStrategyConfig(strategy=strategy)})
    assert out["a"].fillna(-1.0).tolist() == expected


# ---------------------------------------------------------------- D8
def test_d8_feature_builder_config_reaches_the_cleaner():
    from cleaning.feature_engineering import ArithmeticFeatureDef, FeatureEngineeringConfig
    from cleaning.preprocessor import CleaningConfig

    ctrl = _controller()
    cfg = CleaningConfig()
    cfg.feature_config = FeatureEngineeringConfig(
        arithmetic_features=[ArithmeticFeatureDef("x_sum", "x1", "x2", "add")]
    )
    cleaned, _ = ctrl.clean_active(cfg)
    assert "x_sum" in cleaned.columns
    assert cleaned["x_sum"].equals(ctrl.state.active_df()["x_sum"])


# ---------------------------------------------------------------- D9
def test_d9_rules_editor_sources_populated_so_rules_can_be_added(qapp, msgs):
    from ui.tabs.ml_tab import MLTab

    tab = MLTab(_controller())
    tab.refresh_from_state()
    sources = [tab.rules_editor.source_combo.itemText(i) for i in range(tab.rules_editor.source_combo.count())]
    assert {"x1", "prediction", "cluster_label"} <= set(sources)
    tab.rules_editor.source_combo.setCurrentText("prediction")
    tab.rules_editor.threshold_edit.setText("0.5")
    tab.rules_editor.target_col_edit.setText("alert")
    tab.rules_editor._on_add_clicked()
    assert len(tab.rules_editor.rules()) == 1 and not msgs["warning"]


def test_d9_rule_sources_have_no_duplicates_after_apply(qapp, msgs, stub_metrics):
    from ui.tabs.ml_tab import MLTab

    ctrl = _controller()
    tab = MLTab(ctrl)
    tab._on_trained(ctrl.train_regression_with_columns("linear", "y", ["x1", "x2"], []))
    tab._apply_predictions()
    combo = tab.rules_editor.source_combo
    items = [combo.itemText(i) for i in range(combo.count())]
    assert items.count("prediction") == 1


# ---------------------------------------------------------------- D10
def test_d10_categorical_case_is_preserved_by_default():
    from cleaning.categorical_cleaning import CategoricalCleaner

    out = CategoricalCleaner().clean(pd.DataFrame({"c": ["ny", "LA"]}), {"c": "categorical"})
    assert out["c"].tolist() == ["ny", "LA"]


def test_d10_case_normalisation_is_opt_in_via_checkbox(qapp, msgs):
    from ui.tabs.cleaning_tab import CleaningTab

    ctrl = _controller()
    tab = CleaningTab(ctrl)
    tab.refresh_from_state()
    tab.run_cleaning()
    assert set(ctrl.state.active_df()["city"]) == {"ny", "LA"}

    tab.chk_normalize_case.setChecked(True)
    tab.run_cleaning()
    assert set(ctrl.state.active_df()["city"]) == {"Ny", "La"}


# ---------------------------------------------------------------- D11
def test_d11_constant_strategy_fills_numeric_and_text_columns():
    from cleaning.missing_value_handler import MissingStrategyConfig, MissingValueHandler

    df = pd.DataFrame({"n": [1.0, np.nan], "s": ["a", None]})
    out = MissingValueHandler().apply(
        df,
        {"n": "numeric", "s": "categorical"},
        {"n": MissingStrategyConfig("constant", "0"), "s": MissingStrategyConfig("constant", "z")},
    )
    assert out["n"].tolist() == [1.0, 0.0] and out["n"].dtype.kind == "f"
    assert out["s"].tolist() == ["a", "z"]


def test_d11_constant_strategy_without_value_is_not_silent():
    from cleaning.missing_value_handler import MissingStrategyConfig, MissingValueHandler

    df = pd.DataFrame({"n": [1.0, np.nan]})
    with pytest.raises(ValueError):
        MissingValueHandler().apply(df, {"n": "numeric"}, {"n": MissingStrategyConfig("constant")})


def test_d11_cleaning_tab_has_a_value_field_for_constant(qapp, msgs):
    from PySide6.QtCore import Qt
    from ui.tabs.cleaning_tab import CleaningTab

    df = _frame()
    df.loc[::5, "x1"] = np.nan
    ctrl = _controller(df)
    tab = CleaningTab(ctrl)
    tab.refresh_from_state()
    tab.col_list.findItems("x1", Qt.MatchExactly)[0].setSelected(True)
    tab.strategy_combo.setCurrentText("constant")

    tab._apply_to_selected()  # no value typed yet -> rejected, nothing recorded
    assert msgs["warning"] and not tab._column_strategies

    tab.constant_edit.setText("0")
    tab._apply_to_selected()
    tab.run_cleaning()
    out = ctrl.state.active_df()["x1"]
    assert out.notna().all() and (out == 0).sum() == 12


# ---------------------------------------------------------------- D13
def test_d13_requirements_pin_the_versions_the_tests_ran_on():
    req = Path(__file__).resolve().parents[1] / "Insight Bridge" / "requirements.txt"
    lines = [ln.strip() for ln in req.read_text(encoding="utf-8").splitlines()]
    pins = dict(ln.split("==") for ln in lines if "==" in ln and not ln.startswith("#"))
    assert {"pandas", "numpy", "scikit-learn", "matplotlib", "PySide6"} <= set(pins)
    for name, pinned in pins.items():
        assert version(name) == pinned, name


# ---------------------------------------------------------------- D26
def test_d26_window_title_says_insightbridge(qapp):
    from ui.main_window import MainWindow

    assert MainWindow().windowTitle() == "InsightBridge"
