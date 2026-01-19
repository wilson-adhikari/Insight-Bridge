# ui/widgets/plot_canvas.py
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PlotCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._figure = Figure()
        self._canvas = FigureCanvas(self._figure)
        layout = QVBoxLayout(self)
        layout.addWidget(self._canvas)
        self.setLayout(layout)

    @property
    def figure(self) -> Figure:
        return self._figure

    def draw_figure(self, fig: Figure):
        self._figure = fig
        self._canvas.figure = fig
        self._canvas.draw()
