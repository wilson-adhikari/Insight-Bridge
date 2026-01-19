# reporting/export_plots.py
from __future__ import annotations
from pathlib import Path
from typing import List
from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import PdfPages


def export_single_plot(fig: Figure, path: str | Path) -> None:
    fig.savefig(path, bbox_inches="tight")  # PNG/JPEG/PDF[web:196][web:192]


def export_plots_to_pdf(figures: List[Figure], path: str | Path) -> None:
    path = Path(path)
    with PdfPages(path) as pdf:
        for fig in figures:
            pdf.savefig(fig, bbox_inches="tight")
