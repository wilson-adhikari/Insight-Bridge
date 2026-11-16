# InsightBridge — Repository Audit

**Audit date:** 2026-11-05 · **Commit audited:** `2bf82df` (branch default, 12 commits, all 2026-01-19, mostly "Add files via upload")
**Auditor:** Claude Code (automated code-level audit, not a README review)
**Scope:** every `.py` file (79 files, 4,804 lines), `requirements.txt`, README, LICENSE, git history, committed `.pyc` files.

## 1. Verdict

- **Launches:** yes. `python main.py` opens an 8-tab PySide6 window (offscreen run, killed by timeout after 8 s with no error).
- **Works end to end:** no. Loading, cleaning (most strategies), filtering, analysis, joins, plotting, plot export, Excel export and the text-only PDF report work. **All ML training is broken**, CSV export and session save crash, and several buttons do nothing useful (see section 5).
- **Automated tests / CI / packaging:** none exist.
- **Customer-ready:** no. See section 8.

## 2. What the repository contains

| Item | Finding |
|---|---|
| Layout | All code is under `Insight Bridge/` (path contains a space). Packages: `core`, `ingestion`, `cleaning`, `analysis`, `visualization`, `ml`, `reporting`, `ui` (`tabs`, `widgets`, `workers`), `utils`. |
| Entry point | `Insight Bridge/main.py` → `ui.main_window.run_app()`. Must be run with `Insight Bridge/` as the working directory or on `PYTHONPATH` (absolute imports like `from core.controller import ...`). |
| Stray files | `Insight Bridge/main` (2-byte empty file). 72 committed `__pycache__/*.cpython-313.pyc` files; no `.gitignore`. |
| Orphan bytecode | `.pyc` files exist for modules that have **no source**: `visualization/chart_selector`, `visualization/plot_factory`, `ingestion/schema_detector`, `cleaning/missing_values`, `ui/multi_select_combo`, `ui/worker`, `ui/worler`. Strings inside `chart_selector.pyc` ("Recommend charts based on data characteristics") show the chart-suggestion feature existed in an earlier local copy but was **not uploaded**. The `.pyc` files also embed the developer's local folder names (OneDrive/Desktop/"Universal Data Analyzer exe"). |
| Product identity | Window title is "Universal Data Analyzer" (`ui/main_window.py:37`), not InsightBridge. This code base appears to be the same lineage as the company's "Universal Data Analyzer Desktop" product; the founder should decide whether these are one product or two. |
| Dependencies | `requirements.txt`: 20 packages, lower bounds only, no lock file. `streamlit`, `weasyprint`, `reportlab`, `jinja2`, `pydantic`, `python-dotenv` are **never imported**. `numpy>=2.1` requires Python ≥ 3.10, so README's "Python 3.9+" is wrong. |
| Tests | None. `pytest` → "no tests ran". |
| CI | None (no `.github/`). |
| Packaging | None (no `pyproject.toml`, PyInstaller spec, or installer) despite being described as a desktop application. |
| Licence | `LICENSE` = MIT (2026, wilson adhikari). README says "Licensing terms can be adapted as needed" — contradicts the MIT file. |

## 3. Architecture (as implemented)

`MainWindow` creates one `Controller` and eight tabs. The controller holds `AppState` (dict of DataFrames + schemas + active table name) and wraps `DataManager`, `TypeInference`, `TypeCaster`, `Preprocessor`, `MLManager`, `SessionManager`. Everything runs on the GUI thread except ML training, which uses a `QThread` worker (broken, see TECHNICAL_DEBT D1). Other tabs are refreshed only after a data load (`DataTab._notify_main_window`), not after cleaning, filtering or ML apply.

Roughly 40% of backend code is **unreferenced**: `visualization/plot_manager.py` + `numeric_plots.py` + `categorical_plots.py` + `ml_plots.py` (the Visualization tab has its own plot code), `cleaning/duplicates.py`, `encoding.py`, `outliers.py`, `analysis/grouped_analysis.py`, `summary_stats.py`, `ml/models.py`, `ml/persistence.py` (instantiated but never used for save/load), `ingestion/csv_loader.py`, `excel_loader.py`, `relationship_detector.py`, `incremental_tracker.py`, four of the five `ui/workers/*`, `ui/widgets/warnings_panel.py`, all of `utils/`.

## 4. What was executed

Environment: Windows 11, Python 3.11.0. **Deviation:** the requested scratchpad on C: could not hold the venv (C: had 529 MB free; first install failed with `OSError: [Errno 28] No space left on device`). The venv was created at `D:\audit-tmp\insightbridge\venv` instead (outside the repo). Scripts and logs are in the scratchpad `audit-insightbridge\` folder. All runs used `PYTHONDONTWRITEBYTECODE=1` and a scratch working directory, so nothing was written into the repo except these four audit files.

| # | Command | Result |
|---|---|---|
| 1 | `py -3.11 -m venv venv` then `pip install --no-cache-dir -r "Insight Bridge/requirements.txt"` | Success (3 min 19 s). Resolved: pandas 3.1.1, numpy 2.4.6, scikit-learn 1.9.1, PySide6 6.12.0, matplotlib 3.11.2, SQLAlchemy 2.1.8. |
| 2 | `python -m pytest "Insight Bridge" -q` | `no tests ran` |
| 3 | `python -m flake8 --select=E9,F63,F7,F82 .` | 5 × `F821 undefined name 'web'` in `ml/evaluation.py:48,67,77`; 1 × F811 duplicate `active_schema` in `core/state.py:35`. Full flake8: 309 findings (mostly style). |
| 4 | `backend_smoke.py` (imports every module, then drives the controller with a 200-row CSV/XLSX/SQLite sample) | 108 checks: 98 OK, 10 FAIL. All 59 modules import. Failures listed in FEATURE_TRACEABILITY.md. |
| 5 | `ml_after_clean.py` (ML on fully cleaned, NaN-free data) | Regression: `TypeError: unexpected keyword argument 'squared'`; classification and clustering: `NameError: name 'web' is not defined` (`ml/evaluation.py:67,77`). |
| 6 | `gui_smoke.py` with `QT_QPA_PLATFORM=offscreen`: builds `MainWindow`, counts `clicked()` receivers for all 26 buttons, clicks every one with file/message dialogs stubbed | All 26 buttons are connected. 2 unhandled exceptions (Export CSV, Save session). ML Train stays at "Status: Training..." forever with no error. Details in section 5. |
| 7 | `ml_worker_probe.py`: `MLWorker` used exactly like `MLTab._train_model` | Worker `run()` never executes; no `finished`/`error` signal; process exits with code 127 (QThread destroyed while running). |
| 8 | `timeout 8 python "Insight Bridge/main.py"` (offscreen) | Exit 124 = still running when killed → **launches**. Creates `models/` and `sessions/` folders in the current working directory on every start. |
| 9 | `git status --short` after all runs | Clean (no source modified, no temporary fixes applied). |

Not executed: a real on-screen (non-offscreen) session, `.xls` loading, very large files, remote SQL servers, a packaged build, macOS/Linux.

## 5. Buttons and controls (26 buttons, all have a connected handler)

| Tab | Control | Handler | Observed result |
|---|---|---|---|
| Data | Load CSV / Load multiple CSVs | `ui/tabs/data_tab.py:87,95` | Works. Malformed rows are silently skipped (`core/controller.py:58`). Same file stem silently overwrites an existing dataset. |
| Data | Load Excel / Load multiple Excels | `data_tab.py:106,112` | `.xlsx` works (first sheet only). Dialog offers `.xls`, which the `openpyxl` engine cannot read (`controller.py:77`, inspection only). |
| Data | Load SQL table / multiple | `data_tab.py:123,139` | Works (SQLite tested). Connection string typed in clear text. |
| Cleaning | Select All, Apply strategy | `cleaning_tab.py:46,97` | Works. |
| Cleaning | Add feature | `ui/widgets/feature_builder.py:49` | **Non-functional:** feature is stored but never created; Preprocessor sub-components keep their construction-time config (`cleaning/preprocessor.py:40-42`, `core/controller.py:130`). No list of added features is shown. |
| Cleaning | Run Cleaning | `cleaning_tab.py:116` | Works for drop/mean/median/mode/auto. **ffill/bfill crash** (`TypeError`, `cleaning/missing_value_handler.py:44,46`). **constant is a silent no-op** (no value field; `missing_value_handler.py:48`). |
| Filter | Add condition, Preview, Apply | `filter_tab.py:82,97,113` | Work. "Columns" list is populated but used by nothing (`filter_tab.py:32,77-79`). No way to remove/clear conditions. Apply does not refresh other tabs. |
| Analysis | Numeric / Categorical / Relationship hints | `analysis_tab.py:62,75,87` | Work (text output). |
| Visualization | Plot (11 chart types), Export plot | `visualization_tab.py:97,259` | All 11 chart types rendered without error; PNG export works. No chart **suggestion** exists. |
| ML | Train Model | `ui/tabs/ml_tab.py:142-189` | **Broken:** worker is garbage-collected and never runs (`ml_tab.py:186-189`); status stuck at "Training...". Even if it ran, every model fails in `ml/evaluation.py`. |
| ML | Add predictions/clusters to data | `ml_tab.py:256` | **Non-functional:** depends on a successful train; even then it reads attributes (`predicted`, `cluster_labels`) that `TrainedModelInfo` does not have (`ml_tab.py:263-266`), so nothing is added. |
| ML | Add rule | `ui/widgets/rules_editor.py:53` | **Non-functional:** source column combo is never populated (`set_source_columns` is never called), so every click shows "Please fill all fields". |
| Joins | Preview join | `join_tab.py:86` | Works (100-row preview). Result cannot be saved as a dataset. |
| Reporting | Build PDF report | `reporting_tab.py:51` | Produces a text-only PDF (no charts, no ML). Says "Report generated." even when no data is loaded (`controller.py:261-262`). |
| Reporting | Export active to CSV | `reporting_tab.py:66` | **Crashes:** `AttributeError: 'dict' object has no attribute 'to_csv'` (`controller.py:245-248` passes a dict to `reporting/export_data.py:8`). |
| Reporting | Export active to Excel | `reporting_tab.py:77` | Works. No success message. |
| Reporting | Save session | `reporting_tab.py:88` | **Crashes:** `AttributeError: 'AppState' object has no attribute 'models'` (`controller.py:286`). There is no Load session control at all. |

## 6. Security and privacy

| Severity | Finding | Location |
|---|---|---|
| Medium | SQL built by f-string from table/column names (SQL injection if ever wired to UI input). Currently unreachable. | `ingestion/data_manager.py:80-82` |
| Medium | `joblib.load` of model files = arbitrary code execution if a user opens an untrusted model. Currently unreachable from UI. | `ml/persistence.py:73` |
| Low | SQL connection strings (may contain passwords) entered in a plain, non-masked `QInputDialog`. | `ui/tabs/data_tab.py:124,140` |
| Low | Full Python tracebacks shown to end users in dialogs and printed to console (path disclosure, poor UX). | `data_tab.py:84,137`; `ui/main_window.py:20-29` |
| Low | App writes `models/` and `sessions/` into the current working directory at startup; will fail or scatter files when installed under Program Files. | `core/config.py:16-17`, `ml/persistence.py:29`, `reporting/session_manager.py:21` |
| Low | Committed `.pyc` files leak developer's local folder structure. | `*/__pycache__/*.pyc` |
| Info | No network calls in the code itself; "offline" claim holds for the code paths reviewed (SQL is user-directed). `streamlit` is installed but never run. | — |

Data-integrity risks (not security, but customer-impacting): default cleaning title-cases every categorical value ("NY" → "Ny", e-mails, IDs) with no opt-out (`cleaning/categorical_cleaning.py:36-37`); filter and cleaning overwrite the active dataset with no undo; CSV loader drops malformed rows silently.

## 7. Licence and third-party

- Repository is public and MIT-licensed: anyone may already copy, modify and resell this code. Selling it is allowed, but there is no exclusivity. Founder decision needed before positioning it as a paid product.
- PySide6 is LGPLv3: a distributed installer must ship the licence text and allow users to replace the Qt libraries (dynamic linking is fine). No `THIRD_PARTY_NOTICES` exists.
- Other runtime dependencies (pandas, numpy, scipy, scikit-learn, matplotlib, seaborn, SQLAlchemy, openpyxl, joblib) are BSD/MIT/PSF-style. Unused `weasyprint` (BSD) needs native GTK libraries on Windows; remove it rather than ship it.
- Many source comments contain pasted citation markers such as `[web:119]`. In `ml/evaluation.py` these markers are in executable code and cause the ML failure. This suggests code was pasted from AI chat output without being run.

## 8. README accuracy

| README claim | Reality |
|---|---|
| Supports CSV, Excel, **XML**, SQL | No XML code anywhere. `.xls` offered but not readable. |
| Automated visualization suggestions — "Implemented" | Not implemented in source (only an orphan `.pyc`). |
| Local ML — "Implemented", "ML workflows work correctly" | All training fails; UI never even starts training. |
| Report export (PDF / Excel) of insights, visualizations and ML outputs | PDF is text only (shape, dtypes, numeric stats). Excel is a raw data dump. CSV export crashes. |
| "Does not affect system accuracy or data integrity" | Default cleaning alters categorical values; malformed CSV rows are silently dropped. |
| Python 3.9+ | Requirements need Python ≥ 3.10. |
| Licence "can be adapted as needed" | MIT LICENSE file is binding for already-published code. |
| No installation/run instructions | README has none; app must be run from inside `Insight Bridge/`. |

## 9. Customer readiness

Not offerable to customers in its current state: the headline ML feature, CSV export and session save are broken, two advertised features (XML, chart suggestions) do not exist, there are no tests, no installer and no versioning. Milestones 1–2 in REBUILD_PLAN.md (targeted fixes, no rewrite) would make it a credible free/beta tool; a paid offering also needs the company licensing/entitlement integration and a founder decision on the MIT licence.
