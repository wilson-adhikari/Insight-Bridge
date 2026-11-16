# InsightBridge — Rebuild Plan

Principle: keep the existing structure (Controller + AppState + 8 PySide6 tabs + backend packages). No rewrite. Each milestone is small, reviewable, and ends with tests passing. Defect IDs refer to TECHNICAL_DEBT.md.

Founder decisions needed before Milestone 3: (a) is InsightBridge the same product as "Universal Data Analyzer Desktop"? (b) keep the public MIT licence, or develop commercial features in a separate private repo? (c) free vs paid feature split.

## Milestone 1 — Runnable, reproducible, tested baseline

Objective: anyone can install and run it the same way, and regressions are caught automatically.

1. Add `.gitignore`; remove committed `__pycache__/` and the empty `Insight Bridge/main` file (D27).
2. Pin the dependency set that was verified in this audit (Python 3.11, pandas 3.1.1, numpy 2.4.6, scikit-learn 1.9.1, PySide6 6.12.0, matplotlib 3.11.2, seaborn 0.13.2, SQLAlchemy 2.1.8, openpyxl 3.1.5, scipy 1.17.1, joblib); move pytest/flake8/black to `requirements-dev.txt`; drop unused streamlit, weasyprint, reportlab, jinja2, pydantic, python-dotenv (D13, D31).
3. Add README "Install and run" section (`cd "Insight Bridge"` then `python main.py`) and correct the Python version.
4. Add `tests/` with pytest:
   - backend tests for load (CSV/XLSX/SQLite), each cleaning strategy, analysis, ML (one per task), exports, report, session — the scratch `backend_smoke.py` from this audit is a ready starting point;
   - an offscreen GUI test (`QT_QPA_PLATFORM=offscreen`) that builds `MainWindow` and clicks every button with dialogs stubbed (from `gui_smoke.py`).
   These tests will initially fail on D1–D7; mark them `xfail` with the defect ID, then remove the marker as each is fixed.
5. Add GitHub Actions CI: Windows runner, install pinned deps, `flake8 --select=E9,F63,F7,F82`, pytest.

Verification: CI green (with documented xfails); `flake8` F821 count visible.

## Milestone 2 — Fix defects and every non-functional button

Objective: every visible control does what its label says, or is removed.

| Order | Fix | Defects | Verification |
|---|---|---|---|
| 1 | ML: remove `[web:…]`, replace `squared=False`, keep worker/thread references, return predictions/labels, unpack clustering tuple, use `feature_importance` | D1–D4 | ML tests pass for linear, rf, logistic, kmeans; GUI test shows "Training successful" and adds `prediction`/`cluster_label` |
| 2 | Export CSV passes DataFrame; Save session uses `ml_manager.models` (or remove button until Load exists) | D5, D6 | Export/session tests pass |
| 3 | `ffill()`/`bfill()`; constant value field or remove option | D7, D11 | Cleaning strategy tests pass |
| 4 | Build a fresh `Preprocessor(cfg)` per run; show list of added features with remove | D8, D25 | Feature column appears after cleaning |
| 5 | Populate rules editor sources | D9 | Rule added and applied in GUI test |
| 6 | Refresh all tabs after cleaning/filter/ML apply; re-infer schema after cleaning | D14 | GUI test: new column visible in Analysis/Visualization/ML |
| 7 | Categorical normalisation off by default with checkbox; keep raw copy / one-step undo | D10, D15 | Values unchanged by default; undo restores row count |
| 8 | Error handling + success messages on Reporting tab; no "Report generated" without data; hide tracebacks behind "Details"; mask connection string input | D18, D20 | Manual check + GUI test asserts messages |
| 9 | Remove `.xls` from dialog (or add `xlrd`); report count of skipped CSV rows; warn before overwriting same-name dataset | D16, D17, D23 | Tests for each |
| 10 | Window title "InsightBridge" (after founder decision) | D26 | — |

Verification: all xfails removed; full button-click GUI test has zero unhandled exceptions; manual on-screen walkthrough of all 8 tabs recorded in `docs/`.

## Milestone 3 — Close README gaps and harden

Objective: README claims match the product; safe to hand to beta users.

1. Recover `chart_selector.py` from the author's local copy (orphan `.pyc` proves it existed) and wire an "Suggest charts" control into the Visualization tab — or implement a small rule-based recommender from column logical types (D12).
2. XML import via `pandas.read_xml` in the Data tab (D12), with tests.
3. Report: include current figures and last ML metrics in the PDF; add a summary sheet to Excel export (F14, F15).
4. Move `models/`/`sessions/` to a per-user data directory (D21); parameterise the incremental SQL query and restrict `joblib.load` to app-created files before exposing either (D22).
5. Move loading/cleaning/report work to the existing worker classes (with the D1 fix applied) so large files do not freeze the UI (D24); delete the duplicate worker modules or merge into one (D28).
6. Delete or wire the remaining dead modules, decided case by case (D28); replace `print` with `utils/logging_config.py` (D32).

## Milestone 4 — Release readiness (company release gates)

1. Windows installer (e.g. PyInstaller) with `THIRD_PARTY_NOTICES` including the PySide6 LGPLv3 text; clean-machine install test.
2. Versioning (`__version__`, changelog, tags).
3. If sold: integrate company licensing/entitlement checks (server-side verification per company policy) in a way that never deletes user data on expiry.
4. Security review, dependency/licence scan, and founder release approval.

## Out of scope

Rewriting the UI framework, switching to a web stack, or restructuring packages. These are not justified by the audit findings.
