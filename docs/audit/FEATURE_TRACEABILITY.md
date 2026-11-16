# InsightBridge — Feature Traceability

Audit of commit `2bf82df`. Paths are relative to `Insight Bridge/`.
Evidence column: **E** = executed (backend_smoke / gui_smoke / ml_after_clean, Python 3.11, pandas 3.1.1, scikit-learn 1.9.1, PySide6 6.12.0); **I** = code inspection only.

Status values: Fully implemented · Partially implemented · Not implemented · Broken · Experimental · Unverified.

## README-declared features

| # | Declared feature | Status | Evidence | Location |
|---|---|---|---|---|
| F1 | Fully offline desktop application | Fully implemented | E: launches (PySide6); I: no network code except user-directed SQL | `main.py`, `ui/main_window.py:122-128` |
| F2 | CSV import | Fully implemented (with caveat) | E: single and multi load OK. Malformed rows silently skipped; encodings tried in order | `core/controller.py:48-73` |
| F3 | Excel import | Partially implemented | E: `.xlsx` OK. I: first sheet only; `.xls` offered in dialog but `openpyxl` cannot read it | `controller.py:75-80`, `ui/tabs/data_tab.py:107,113` |
| F4 | XML import | Not implemented | I: no XML code in repo | — |
| F5 | SQL database import | Fully implemented | E: SQLite single and multi-table load OK | `controller.py:82-92`, `data_tab.py:123-154` |
| F6 | No-code cleaning: missing values | Partially implemented | E: drop/mean/median/mode/auto OK; **ffill/bfill Broken** (`TypeError`, removed pandas API); **constant** silent no-op (no value input) | `cleaning/missing_value_handler.py:32-60` |
| F7 | No-code cleaning: inconsistent entries / formatting | Partially implemented | E: categorical strip + title-case runs unconditionally (alters "NY"→"Ny"); fuzzy merge is a stub flag | `cleaning/categorical_cleaning.py:26-48` |
| F8 | Outlier handling | Not implemented (no-op) | I: computes bounds but `clip_extremes=False` by default and no UI toggle, so nothing changes; only a warning count is reported | `cleaning/numeric_cleaning.py:28-40`, `cleaning/validators.py:66-79` |
| F9 | Automated visualization suggestions | Not implemented | I: no recommendation code in source; only orphan `visualization/__pycache__/chart_selector.cpython-313.pyc` | — |
| F10 | Data visualization (charts) | Fully implemented | E: all 11 chart types plotted without error; PNG export OK | `ui/tabs/visualization_tab.py:97-268` |
| F11 | Summaries and insights | Fully implemented (basic) | E: numeric stats, categorical frequency, ANOVA p-value hints | `ui/tabs/analysis_tab.py`, `analysis/*.py` |
| F12 | Local ML training (regression / classification / clustering) | Broken | E: UI worker never runs (`ui/tabs/ml_tab.py:186-189`); backend fails in every model: `TypeError 'squared'` (`ml/evaluation.py:45`), `NameError 'web'` (`ml/evaluation.py:48,67,77`) | `ml/ml_manager.py`, `ml/evaluation.py` |
| F13 | ML outputs: predictions added to data, plots | Broken | I: reads non-existent `TrainedModelInfo` attributes `importance`, `predicted`, `actual`, `cluster_labels`; clustering returns a tuple the UI does not unpack | `ml_tab.py:202,217,227,263-266`, `core/controller.py:229-239` |
| F14 | Report export — PDF | Partially implemented | E: PDF created (text only: shape, dtypes, numeric stats). No charts, no ML results, no insights | `controller.py:259-279`, `reporting/report_builder.py` |
| F15 | Report export — Excel | Partially implemented | E: active dataset written to `.xlsx`; no insights/charts; sheet name = dataset name (>31 chars would fail, I) | `controller.py:250-256`, `reporting/export_data.py:12-19` |
| F16 | Privacy-first, local processing | Fully implemented | I: no telemetry or uploads in code; `streamlit` installed but never imported | — |

## Features present in the UI but not in the README

| # | Feature | Status | Evidence | Location |
|---|---|---|---|---|
| U1 | Row filtering (conditions, preview, apply) | Partially implemented | E: works; no remove/clear condition; "Columns" list unused; other tabs not refreshed | `ui/tabs/filter_tab.py` |
| U2 | Join preview | Partially implemented | E: 100-row preview works; result cannot be kept as a dataset | `ui/tabs/join_tab.py`, `ingestion/data_manager.py:54-65` |
| U3 | Feature engineering (arithmetic columns) | Broken | E: "Add feature" accepted, column never created (config not propagated) | `ui/widgets/feature_builder.py`, `cleaning/preprocessor.py:40-42`, `controller.py:130` |
| U4 | Decision rules on predictions | Broken (UI) | E: rule cannot be added (source combo empty). Backend `RulesEngine` works in isolation | `ui/widgets/rules_editor.py:48-61`, `ml/rules_engine.py` |
| U5 | Export active data to CSV | Broken | E: `AttributeError: 'dict' object has no attribute 'to_csv'` | `controller.py:245-248` → `reporting/export_data.py:8` |
| U6 | Save session | Broken | E: `AttributeError: 'AppState' object has no attribute 'models'` | `controller.py:282-289` |
| U7 | Load session | Not implemented (no UI); backend stub only sets active name | I | `controller.py:291-297` |
| U8 | Data quality warnings (imbalance/outliers) | Partially implemented | E: counts shown in cleaning dialog; `WarningsPanel` widget never used | `cleaning/validators.py`, `ui/widgets/warnings_panel.py` |

## Backend capabilities with no UI path (dead code)

| Capability | Status | Location |
|---|---|---|
| Model save/load/list (joblib + JSON) | Unverified (unreachable) | `ml/persistence.py`, `ml/ml_manager.py:281-330` |
| Permutation importance | Unverified (unreachable) | `ml/explainability.py`, `ml_manager.py:255-270` |
| Duplicate removal | Unverified (unreachable) | `cleaning/duplicates.py` |
| Categorical encoding (one-hot / ordinal / frequency) | Unverified (unreachable) | `cleaning/encoding.py` |
| Outlier detection/marking | Unverified (unreachable) | `cleaning/outliers.py` |
| Incremental SQL loading | Unverified (unreachable; contains SQL injection) | `ingestion/data_manager.py:68-95` |
| SQL foreign-key relationship detection | Unverified (unreachable) | `ingestion/relationship_detector.py` |
| Plot library (`PlotManager`, ML plots, confusion matrix, ROC) | Unverified (unreachable) | `visualization/*.py` |
| Background workers for loading/cleaning/analysis/report | Unverified (unreachable; same GC defect as ML worker) | `ui/workers/*.py` |
| `CSVLoader.load` | Broken (`AttributeError`, E) | `ingestion/csv_loader.py:10` |

## Backend smoke results (executed)

108 checks, 98 OK, 10 FAIL:
`clean ffill` TypeError · `clean bfill` TypeError · `train regression linear/rf` (NaN target on raw data; after cleaning: TypeError `squared`) · `train classification logistic/rf` NameError `web` · `train clustering kmeans` (NaN; after cleaning: NameError `web`) · `export_active_to_csv` AttributeError · `save_session` AttributeError · `CSVLoader.load` AttributeError.
