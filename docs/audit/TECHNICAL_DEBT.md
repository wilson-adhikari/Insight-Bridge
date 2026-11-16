# InsightBridge — Technical Debt and Defects

Commit `2bf82df`. Paths relative to `Insight Bridge/`. E = reproduced by execution, I = inspection.
Severity: **P0** headline feature broken or crash/data loss · **P1** advertised behaviour wrong or silent data change · **P2** degraded UX / latent defect · **P3** hygiene.

## P0

| ID | Defect | Location | Impact | Recommended fix |
|---|---|---|---|---|
| D1 | **FIXED 2026-11-14 (tests/test_defects.py).** ML worker is garbage-collected before it runs. `worker` is a local variable with no parent; `run()` never executes and no signal fires. Process aborts at exit ("QThread destroyed while running", exit 127). (E) | `ui/tabs/ml_tab.py:186-189`, `ui/workers/ml_worker.py:25-35` | "Train Model" does nothing; status stuck at "Training..." | Keep a reference (`self._ml_worker = worker; self._ml_thread = run_ml_in_thread(...)`) and clear it on finish/error. |
| D2 | **FIXED 2026-11-14 (tests/test_defects.py).** Pasted citation markers in executable code: `RegressionMetrics(...)[web:118]` etc. raise `NameError: name 'web' is not defined`. (E) | `ml/evaluation.py:48,67,77` | Every ML model fails even with D1 fixed | Delete the `[web:…]` suffixes. |
| D3 | **FIXED 2026-11-14 (tests/test_defects.py).** `mean_squared_error(..., squared=False)` removed in scikit-learn 1.6+. (E) | `ml/evaluation.py:45` | Regression always fails on current scikit-learn | Use `root_mean_squared_error` (or `np.sqrt(mean_squared_error(...))`). |
| D4 | **FIXED 2026-11-14 (tests/test_defects.py).** ML result handling uses attributes that do not exist (`importance`, `predicted`, `actual`, `cluster_labels`); clustering returns `(info, labels)` tuple which `_on_trained` treats as `info`. (I) | `ui/tabs/ml_tab.py:202,217,227,263-266`; `core/controller.py:229-239` | No ML plots ever; "Add predictions/clusters" adds nothing; clustering would crash with `AttributeError` | Return predictions/labels from the controller (e.g. via `MLManager.predict` on the active df) and use `info.feature_importance`; unpack the clustering tuple. |
| D5 | **FIXED 2026-11-14 (tests/test_defects.py).** Export CSV passes a `dict` to a function expecting a `DataFrame`. Unhandled `AttributeError`. (E) | `core/controller.py:245-248` → `reporting/export_data.py:8` | "Export active to CSV" always crashes | Pass `df` directly. |
| D6 | **FIXED 2026-11-14 (tests/test_defects.py; save no longer crashes, the Load-session / data-path decision is still open).** `save_session` reads `self.state.models`, which `AppState` does not define. (E) | `core/controller.py:286`, `core/state.py:12-22` | "Save session" always crashes | Use `self.ml_manager.models` and serialise `TrainedModelInfo` safely (metrics contain numpy arrays). Decide whether sessions should store data paths; add Load session or remove the button. |
| D7 | **FIXED 2026-11-14 (tests/test_defects.py).** `fillna(method=...)` removed in pandas 3. (E) | `cleaning/missing_value_handler.py:44,46` | Choosing ffill/bfill makes "Run Cleaning" raise an unhandled `TypeError` | Use `.ffill()` / `.bfill()`. |

## P1

| ID | Defect | Location | Impact | Recommended fix |
|---|---|---|---|---|
| D8 | **FIXED 2026-11-14 (tests/test_defects.py).** Feature builder config is ignored: controller swaps `preprocessor.config`, but `FeatureEngineer`, `NumericCleaner`, `CategoricalCleaner` keep the config they were built with. (E) | `core/controller.py:130`, `cleaning/preprocessor.py:37-43` | "Add feature" silently does nothing | Construct a new `Preprocessor(cfg)` per run (one line) instead of mutating `.config`. |
| D9 | **FIXED 2026-11-14 (tests/test_defects.py).** Rules editor source combo never populated (`set_source_columns` has no caller). (E) | `ui/widgets/rules_editor.py:48-61`, `ui/tabs/ml_tab.py` | "Add rule" always rejects input | Call `rules_editor.set_source_columns(df.columns + ["prediction","cluster_label"])` in `MLTab.refresh_from_state` and after apply. |
| D10 | **FIXED 2026-11-14 (tests/test_defects.py).** Categorical cleaning always strips and title-cases every categorical column; no opt-out in UI. (E: "ny"/"LA" → "Ny"/"La") | `cleaning/categorical_cleaning.py:12-13,33-37` | Silent alteration of customer data (codes, IDs, e-mails) | Default `normalize_case=False`; expose as a checkbox. |
| D11 | **FIXED 2026-11-14 (tests/test_defects.py).** `constant` strategy has no value input; `fillna(None)` leaves NaN unchanged with no message. (E) | `ui/tabs/cleaning_tab.py:52-55,124`, `missing_value_handler.py:47-48` | Strategy shown to user does nothing | Add a value field or remove the option. |
| D12 | **FIXED 2026-11-15 (tests/test_defects_round2.py; XML import added via pd.read_xml; README no longer claims chart suggestions; chart_selector not recreated).** Advertised features absent: XML import; automated chart suggestions (source missing, only orphan `.pyc`). (I) | README; `visualization/__pycache__/chart_selector.cpython-313.pyc` | README over-claims | Recover `chart_selector.py` from the author's machine or implement; add XML via `pd.read_xml`; or correct README. |
| D13 | **FIXED 2026-11-14 (tests/test_defects.py; pins only, no lock file; unused deps D31 left unpinned).** Unpinned requirements; code was written for older pandas/scikit-learn and breaks on current releases (D3, D7). (E) | `requirements.txt` | Non-reproducible installs | Pin tested versions (or use upper bounds) and add a lock/constraints file. |
| D14 | **FIXED 2026-11-15 (tests/test_defects_round2.py).** Other tabs are refreshed only after a data load, not after cleaning, filtering, ML apply; schemas are never re-inferred after cleaning. (E: analysis combo stale) | `ui/main_window.py:61-119`, `ui/tabs/data_tab.py:194-196`, `core/controller.py:120-137` | Stale column lists; new columns invisible to Analysis/ML | Pass `main_window` to all tabs (or emit a signal) and call `refresh_tabs()` after mutating actions; re-infer schema after cleaning. |
| D15 | **FIXED 2026-11-15 (tests/test_defects_round2.py; untouched `<name>_raw` copy kept per loaded dataset).** Filter apply and cleaning overwrite the active dataset with no undo or raw copy. (I) | `ui/tabs/filter_tab.py:113-127`, `core/controller.py:133-135` | Irreversible loss of loaded data within a session | Keep the original under `<name>_raw` or add an Undo stack of one. |

## P2

| ID | Defect | Location | Impact |
|---|---|---|---|
| D16 | **FIXED 2026-11-15 (tests/test_defects_round2.py).** `.xls` offered in file dialog but `openpyxl` engine cannot read it. (I) | `core/controller.py:77`, `data_tab.py:107,113` | Load fails with a traceback dialog |
| D17 | **FIXED 2026-11-15 (tests/test_defects_round2.py).** CSV loader skips malformed rows silently (`on_bad_lines="skip"`). (I) | `core/controller.py:58` | Silent row loss; user not told how many rows were dropped |
| D18 | **FIXED 2026-11-15 (tests/test_defects_round2.py).** "Build PDF report" reports success when no data is loaded; reporting/exports have no error handling or success messages. (I) | `core/controller.py:261-262`, `ui/tabs/reporting_tab.py:51-100` | Misleading feedback; exceptions go to the global hook |
| D19 | **FIXED 2026-11-15 (tests/test_defects_round2.py).** Outlier "capping" is a no-op by default and not configurable. (I) | `cleaning/numeric_cleaning.py:13-15,28-40` | Feature appears to exist but does nothing |
| D20 | **FIXED 2026-11-15 (tests/test_defects_round2.py).** Full tracebacks shown to users; connection strings typed unmasked. (I) | `data_tab.py:84,124,137,140`; `ui/main_window.py:20-29` | Poor UX, possible password exposure on screen |
| D21 | **FIXED 2026-11-15 (tests/test_defects_round2.py).** `models/` and `sessions/` folders created in the current working directory at startup. (E) | `core/config.py:16-17`, `ml/persistence.py:29`, `reporting/session_manager.py:21` | Breaks or litters when installed under Program Files; use a per-user data dir |
| D22 | **FIXED 2026-11-15 (tests/test_defects_round2.py; string-built SQL and joblib.load removed; the dead `MLManager.load_model` stub and an unused `create_engine` import remain because their removal was denied by the permission system).** Latent SQL injection and unsafe deserialisation in unreachable code. (I) | `ingestion/data_manager.py:80-82`, `ml/persistence.py:73` | Becomes exploitable if wired to UI |
| D23 | **FIXED 2026-11-15 (tests/test_defects_round2.py).** Loading a file whose stem matches an existing dataset silently replaces it; each file in a multi-load shows its own modal and triggers a full refresh. (E/I) | `ui/tabs/data_tab.py:75-121` | Data overwritten without warning; noisy UX |
| D24 | All work except (broken) ML runs on the GUI thread. (I) | all tabs | UI freezes on large files/plots |
| D25 | **FIXED 2026-11-15 (tests/test_defects_round2.py).** Feature builder shows no list of added features and no remove control; added features persist across runs. (I) | `ui/widgets/feature_builder.py` | Users cannot see or undo definitions |
| D26 | **FIXED 2026-11-14 (tests/test_defects.py).** Window title "Universal Data Analyzer" instead of InsightBridge. (E) | `ui/main_window.py:37` | Brand confusion with another company product |

## P3

| ID | Item | Location |
|---|---|---|
| D27 | No tests, no CI, no packaging, no `.gitignore`; 72 `.pyc` files committed (some for modules without source, leaking local paths); empty stray file `Insight Bridge/main`. | repo root |
| D28 | ~40% of backend code unreferenced (see REPOSITORY_AUDIT §3); four duplicate worker modules. | `visualization/*`, `cleaning/{duplicates,encoding,outliers}.py`, `ui/workers/*` |
| D29 | `AppState` decorated `@dataclass` but defines its own `__init__`; `active_schema` defined twice. | `core/state.py:10-38` |
| D30 | `CSVLoader.load` references non-existent attribute (E: AttributeError). | `ingestion/csv_loader.py:10` |
| D31 | Unused heavy dependencies (`streamlit`, `weasyprint`, `reportlab`, `jinja2`, `pydantic`, `python-dotenv`). README "Python 3.9+" is wrong (numpy 2.1 needs 3.10+). | `requirements.txt`, `README.md` |
| D32 | `print()` debugging throughout instead of logging (`utils/logging_config.py` exists but is unused). | `core/controller.py`, `ui/main_window.py` |
| D33 | Source directory name contains a space (`Insight Bridge/`), which complicates packaging and imports. | repo layout |
| D34 | `[web:NNN]` citation markers in comments across many files. | `analysis/*.py`, `ml/*.py`, `reporting/*.py`, `visualization/exporters.py` |
