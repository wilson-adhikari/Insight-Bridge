# reporting/report_builder.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt


@dataclass
class SectionText:
    title: str
    body: str


@dataclass
class ReportContent:
    title: str
    sections: List[SectionText]
    figures: List[Figure]
    metadata: Optional[Dict[str, Any]] = None


def build_pdf_report(content: ReportContent, path: str | Path) -> None:
    path = Path(path)

    with PdfPages(path) as pdf:
        # Text/title pages
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis("off")

        y = 0.95
        ax.text(0.5, y, content.title, ha="center", va="top", fontsize=16, fontweight="bold")
        y -= 0.08

        for sec in content.sections:
            ax.text(0.05, y, sec.title, ha="left", va="top", fontsize=12, fontweight="bold")
            y -= 0.04
            ax.text(0.05, y, sec.body, ha="left", va="top", fontsize=10, wrap=True)
            y -= 0.08
            if y < 0.1:
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)
                fig, ax = plt.subplots(figsize=(8.27, 11.69))
                ax.axis("off")
                y = 0.95

        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # Figures pages
        for fig in content.figures:
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
