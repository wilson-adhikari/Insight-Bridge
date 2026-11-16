InsightBridge
=============

**Offline-First Desktop Data Intelligence Platform**

InsightBridge is a no-code, offline **desktop application** (Python + PySide6) for loading, cleaning, analysing, visualising and modelling tabular data on your own machine, without any cloud dependency.

Features
--------

Each item below is a tab in the application.

*   **Data** – import CSV, Excel (`.xlsx`), XML (flat, row-oriented files) and SQL tables (SQLAlchemy connection string; the database driver must be installed separately). Malformed CSV rows are skipped and counted in the load message. Every loaded dataset keeps an untouched copy named `<name>_raw`.
*   **Cleaning** – per-column missing-value strategies (drop, mean, median, mode, ffill, bfill, constant, auto), optional title-casing of categorical values, optional capping of numeric outliers (1.5 x IQR), and simple arithmetic features (add / sub / mul / div of two columns).
*   **Filter** – build conditions (`>`, `==`, `contains`, `in`, `between`, ...), preview the result and apply it to the active dataset.
*   **Analysis** – numeric summaries, categorical frequency tables and numeric-vs-categorical relationship hints.
*   **Visualization** – charts you choose yourself (histogram, scatter, line, bar, box, violin, KDE, correlation heatmap and others) with plot export.
*   **ML** – local training of regression (linear, random forest), classification (logistic, random forest) and k-means clustering; predictions or cluster labels can be added to the data, with optional decision rules.
*   **Joins** – preview a join between two loaded datasets.
*   **Reporting** – basic PDF report, export of the active dataset to CSV or Excel, and saving a session file.

All processing is local. No data leaves the machine.

Known limitations
-----------------

*   Apart from ML training, work runs on the UI thread, so the window can freeze on large files or plots.
*   A saved session records dataset and model names only; there is no "Load session" in the UI yet.
*   Old `.xls` workbooks are not supported; save them as `.xlsx` first.
*   Charts are picked manually; the app does not propose chart types.
*   Join results can be previewed but not saved as a new dataset.

Requirements
------------

*   Python 3.11 (the version the tests run on)
*   Desktop OS (Windows / Linux / macOS), 4 GB RAM
*   Python packages: see `Insight Bridge/requirements.txt` (tested versions are pinned)

Install and run
---------------

```
cd "Insight Bridge"
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Trained-model and session files are written to `~/.insightbridge/`.

Tests
-----

From the repository root, in the same environment:

```
python -m pytest tests -q
```

The Qt tests run headless (`QT_QPA_PLATFORM=offscreen` is set by `tests/conftest.py`).

Project status
--------------

Working MVP. Open defects and their status are tracked in `docs/audit/TECHNICAL_DEBT.md`.

License
-------

See `LICENSE`.
