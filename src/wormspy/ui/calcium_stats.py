"""CalciumStatsWidget: bottom-right calcium distribution & temporal trace panel."""

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from wormspy.review import CalciumStats
from wormspy.ui import theme


class CalciumStatsWidget(QWidget):
    """Displays calcium pixel-intensity distribution and temporal p99.9 / background traces."""

    def __init__(self) -> None:
        super().__init__()
        self._target = QSize(420, 220)
        self._stats: CalciumStats | None = None

        title = QLabel("CALCIUM STATS")
        title.setObjectName("feedTitle")
        self.dist_button = QPushButton("Distribution")
        self.trace_button = QPushButton("Over time")
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)
        for idx, btn in enumerate((self.dist_button, self.trace_button)):
            btn.setCheckable(True)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self._mode_group.addButton(btn, idx)
        self.dist_button.setChecked(True)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.dist_button)
        header.addWidget(self.trace_button)

        self.summary_label = QLabel("No fluorescence channel")
        self.summary_label.setObjectName("muted")
        self.summary_label.setFont(theme.mono_font(10))

        self.hist_plot = self._make_plot("intensity", "log10(count + 1)")
        self.hist_curve = self.hist_plot.plot(
            pen=pg.mkPen(theme.rgba(theme.ACCENT, 200), width=1.5),
            brush=theme.rgba(theme.ACCENT, 65),
            fillLevel=0,
            stepMode="center",
        )

        self.trace_plot = self._make_plot("time", "intensity", x_units="s")
        self.p999_curve = self.trace_plot.plot(
            pen=pg.mkPen(theme.ACCENT, width=2), name="p99.9")
        self.median_curve = self.trace_plot.plot(
            pen=pg.mkPen(theme.MUTED, width=1.2), name="median")
        self.playhead = pg.InfiniteLine(
            angle=90, movable=False, pen=pg.mkPen(theme.AMBER, width=1.5))
        self.trace_plot.addItem(self.playhead)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.hist_plot)
        self.stack.addWidget(self.trace_plot)
        self._mode_group.idClicked.connect(self.stack.setCurrentIndex)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addLayout(header)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.stack, 1)

    @staticmethod
    def _make_plot(x_label: str, y_label: str, x_units: str | None = None) -> pg.PlotWidget:
        plot = pg.PlotWidget()
        plot.setBackground(theme.FEED_BACKGROUND)
        item = plot.getPlotItem()
        item.setMenuEnabled(False)
        item.hideButtons()
        item.showGrid(x=True, y=True, alpha=0.12)
        for name in ("left", "bottom"):
            axis = item.getAxis(name)
            axis.setPen(theme.BORDER_STRONG)
            axis.setTextPen(theme.MUTED)
            axis.setStyle(tickFont=theme.mono_font(9))
            axis.enableAutoSIPrefix(False)
        item.setLabel("bottom", x_label, units=x_units)
        item.setLabel("left", y_label)
        return plot

    def set_target(self, width: int, height: int) -> None:
        self._target = QSize(width, height)
        self.setMaximumSize(self._target)
        self.updateGeometry()

    def sizeHint(self) -> QSize:
        return self._target

    def minimumSizeHint(self) -> QSize:
        return QSize(0, 0)

    def set_mode(self, mode: str) -> None:
        if mode == "trace":
            self.trace_button.setChecked(True)
            self.stack.setCurrentIndex(1)
        else:
            self.dist_button.setChecked(True)
            self.stack.setCurrentIndex(0)

    def show_time(self, time_s: float) -> None:
        self.playhead.setPos(time_s)

    def set_stats(self, stats: CalciumStats | None) -> None:
        self._stats = stats
        if stats is None:
            self.summary_label.setText("No fluorescence channel")
            self.hist_curve.setData(np.empty(0), np.empty(0))
            self.p999_curve.setData(np.empty(0), np.empty(0))
            self.median_curve.setData(np.empty(0), np.empty(0))
            return

        self.summary_label.setText(
            f"{stats.channel}: med {stats.median:.0f} · p99.9 {stats.p999:.0f} · "
            f"max {stats.max_val:.0f} · SNR {stats.snr_proxy:.1f} · "
            f"sat {stats.saturated_pct:.2f}% · z {stats.z_moved_pct:.1f}%"
        )
        self.hist_curve.setData(stats.hist_edges, stats.hist_log_counts)
        self.hist_plot.getPlotItem().enableAutoRange()
        self.hist_plot.getPlotItem().autoRange()

        self.p999_curve.setData(stats.sample_times_s, stats.sample_p999)
        self.median_curve.setData(stats.sample_times_s, stats.sample_median)
        self.trace_plot.getPlotItem().enableAutoRange()
        self.trace_plot.getPlotItem().autoRange()
