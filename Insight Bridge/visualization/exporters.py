# visualization/exporters.py
from __future__ import annotations
from pathlib import Path
from typing import List
from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import PdfPages  # multipage PDF[web:185][web:189][web:193][web:197]


def save_figure(fig: Figure, path: str | Path) -> None:
    fig.savefig(path, bbox_inches="tight")  # PNG/JPEG/PDF based on extension[web:196][web:192][web:188]


def save_figures_to_pdf(figures: List[Figure], path: str | Path) -> None:
    path = Path(path)
    with PdfPages(path) as pdf:
        for fig in figures:
            pdf.savefig(fig, bbox_inches="tight")
