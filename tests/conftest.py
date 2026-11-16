import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Insight Bridge"))


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    # Controller/MLManager create models/ and sessions/ in the cwd (D21); keep them out of the repo.
    monkeypatch.chdir(tmp_path)
    # The per-user data dir (~/.insightbridge) must not touch the real home during tests.
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "home"))


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


@pytest.fixture
def msgs(monkeypatch):
    """Replace modal QMessageBox calls with recorders so tests never block."""
    from PySide6.QtWidgets import QMessageBox

    calls = {"information": [], "warning": [], "critical": []}
    for kind in calls:
        monkeypatch.setattr(
            QMessageBox, kind, staticmethod(lambda *a, _k=kind, **kw: calls[_k].append(a[1:]))
        )
    monkeypatch.setattr(QMessageBox, "question", staticmethod(lambda *a, **kw: QMessageBox.Yes))
    return calls
