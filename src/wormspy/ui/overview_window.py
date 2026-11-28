"""OverviewWindow: non-modal third window for the WormTraffic global-view camera.

Shows the whole-plate overview feed, real-time multi-worm tracks, and the high-magnification
objective FOV box. Clicking a worm (or any point on the plate) moves the Zaber XY stage to
image that worm at high magnification. Includes an interactive 4-point calibration wizard and
legacy YAML import.
"""

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from wormspy.control import commands as C
from wormspy.overview.calibration import OverviewCalibration
from wormspy.overview.tracker import OverviewFrame
from wormspy.overview.worker import OverviewWorker
from wormspy.ui import theme
from wormspy.ui.bridge import StateBridge


class OverviewWindow(QMainWindow):
    def __init__(
        self,
        bridge: StateBridge,
        worker: OverviewWorker,
        stage_position: Callable[[], tuple[float, float] | None],
        calibration_path: Path | None = None,
        initial_calibration: OverviewCalibration | None = None,
        fov_um: tuple[float, float] = (1440.0, 900.0),
        refresh_hz: float = 10.0,
    ) -> None:
        super().__init__()
        self.setWindowTitle("WormsPy — Global view (WormTraffic)")
        self._bridge = bridge
        self._worker = worker
        self._stage_position = stage_position
        self._calibration_path = None if calibration_path is None else Path(calibration_path)
        self.calibration: OverviewCalibration | None = initial_calibration
        self._fov_um = fov_um
        self.selected_track_id: int | None = None
        self._calibrating = False
        self._calib_points: list[tuple[tuple[float, float], tuple[float, float]]] = []
        self._image_shape: tuple[int, int] | None = None
        self._last_ts: float | None = None

        self.start_button = QPushButton("Start overview")
        self.start_button.setProperty("role", "primary")
        self.start_button.clicked.connect(self.toggle_worker)
        self.reset_bg_button = QPushButton("Reset BG")
        self.reset_bg_button.clicked.connect(self._worker.reset_background)
        self.calibrate_button = QPushButton("Calibrate (4 pts)")
        self.calibrate_button.setCheckable(True)
        self.calibrate_button.toggled.connect(self._toggle_calibration)
        self.undo_calib_button = QPushButton("Undo point")
        self.undo_calib_button.clicked.connect(self._undo_calibration_point)
        self.undo_calib_button.setVisible(False)
        self.import_yaml_button = QPushButton("Import YAML…")
        self.import_yaml_button.clicked.connect(self._import_yaml)
        self.status_label = QLabel()
        self.status_label.setObjectName("muted")

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        for btn in (self.start_button, self.reset_bg_button, self.calibrate_button,
                    self.undo_calib_button, self.import_yaml_button):
            toolbar.addWidget(btn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.status_label)

        self.canvas = pg.GraphicsLayoutWidget()
        self.canvas.setBackground(theme.FEED_BACKGROUND)
        self.canvas.ci.setContentsMargins(0, 0, 0, 0)
        self._viewbox = self.canvas.addViewBox(lockAspect=True, invertY=True)
        self._viewbox.setMenuEnabled(False)
        self._viewbox.setDefaultPadding(0)
        self._viewbox.setMouseEnabled(x=False, y=False)
        self.image_item = pg.ImageItem()
        self._trails_item = pg.PlotDataItem(
            pen=pg.mkPen(theme.rgba(theme.ACCENT, 140), width=1.5), connect="finite")
        self._tracks_item = pg.ScatterPlotItem(
            size=10, symbol="o", pen=pg.mkPen("#0a0a0a", width=1),
            brush=pg.mkBrush(theme.ACCENT))
        self._selected_item = pg.ScatterPlotItem(
            size=18, symbol="o", pen=pg.mkPen(theme.AMBER, width=2),
            brush=pg.mkBrush(None))
        self._fov_item = pg.PlotDataItem(
            pen=pg.mkPen(theme.AMBER, width=1.5, style=Qt.PenStyle.DashLine))
        self._calib_item = pg.ScatterPlotItem(
            size=12, symbol="+", pen=pg.mkPen(theme.RED, width=2))
        for item in (self.image_item, self._trails_item, self._fov_item,
                     self._tracks_item, self._selected_item, self._calib_item):
            self._viewbox.addItem(item)
        self.canvas.scene().sigMouseClicked.connect(self._on_click)

        central = QWidget()
        central.setObjectName("central")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)
        layout.addLayout(toolbar)
        layout.addWidget(self.canvas, 1)
        self.setCentralWidget(central)
        self.resize(820, 860)

        bridge.rejected.connect(lambda reason: self.statusBar().showMessage(reason, 6000))
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.tick)
        self._timer.start(int(1000 / refresh_hz))
        self._sync_controls()

    # --- worker lifecycle ---------------------------------------------------------------

    def start_overview(self) -> None:
        self._worker.start()
        self._sync_controls()

    def stop_overview(self) -> None:
        self._worker.stop()
        self._sync_controls()

    def toggle_worker(self) -> None:
        if self._worker.is_running:
            self.stop_overview()
        else:
            self.start_overview()

    def _sync_controls(self) -> None:
        running = self._worker.is_running
        self.start_button.setText("Stop overview" if running else "Start overview")
        self.reset_bg_button.setEnabled(running)
        self._update_status(self._worker.latest())

    # --- calibration --------------------------------------------------------------------

    def _toggle_calibration(self, active: bool) -> None:
        self._calibrating = bool(active)
        self._calib_points.clear()
        self.undo_calib_button.setVisible(self._calibrating)
        self._calib_item.setData([])
        self._update_status(self._worker.latest())

    def _undo_calibration_point(self) -> None:
        if self._calib_points:
            self._calib_points.pop()
            self._draw_calib_points()
            self._update_status(self._worker.latest())

    def _draw_calib_points(self) -> None:
        pts = [{"pos": px} for px, _um in self._calib_points]
        self._calib_item.setData(pts)

    def _import_yaml(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Import WormTraffic YAML calibration", "", "YAML files (*.yaml *.yml)")
        if not path_str:
            return
        try:
            calib = OverviewCalibration.from_legacy_yaml(Path(path_str))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Import failed", str(exc))
            return
        self.calibration = calib
        if self._calibration_path is not None:
            calib.save(self._calibration_path)
        self._update_status(self._worker.latest())

    # --- interaction --------------------------------------------------------------------

    def _on_click(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._image_shape is None:
            return
        pt = self.image_item.mapFromScene(event.scenePos())
        h, w = self._image_shape
        if 0 <= pt.x() < w and 0 <= pt.y() < h:
            self.click_at_pixel(float(pt.x()), float(pt.y()))

    def click_at_pixel(self, u: float, v: float) -> None:
        """Handle a click at overview pixel `(u, v)`: add calibration point or slew stage."""
        if self._calibrating:
            stage_xy = self._stage_position()
            if stage_xy is None:
                self.statusBar().showMessage("Stage position unavailable for calibration.", 4000)
                return
            self._calib_points.append(((u, v), (float(stage_xy[0]), float(stage_xy[1]))))
            self._draw_calib_points()
            if len(self._calib_points) >= 4:
                px_pts = [p for p, _ in self._calib_points]
                um_pts = [s for _, s in self._calib_points]
                try:
                    calib = OverviewCalibration.fit(px_pts, um_pts)
                except ValueError as exc:
                    self.statusBar().showMessage(f"Calibration failed: {exc}", 6000)
                    self._calib_points.clear()
                    self._draw_calib_points()
                else:
                    self.calibration = calib
                    if self._calibration_path is not None:
                        calib.save(self._calibration_path)
                    self.calibrate_button.setChecked(False)
                    self.statusBar().showMessage(
                        f"Overview calibrated (RMS {calib.residual_um:.1f} µm).", 5000)
            self._update_status(self._worker.latest())
            return

        hit = self._worker.find_closest(u, v)
        if hit is not None:
            tid, (px, py) = hit
            self.selected_track_id = tid
        else:
            px, py = u, v
            self.selected_track_id = None

        if self.calibration is None:
            self.statusBar().showMessage(
                "Uncalibrated — click Calibrate (4 pts) or Import YAML first.", 5000)
            return
        x_um, y_um = self.calibration.pixel_to_stage_um(px, py)
        self._bridge.dispatch(C.MoveStageXY(x_um=x_um, y_um=y_um))
        self.statusBar().showMessage(f"Moving stage to ({x_um:.0f}, {y_um:.0f}) µm", 4000)

    # --- refresh ------------------------------------------------------------------------

    def tick(self) -> None:
        frame = self._worker.latest()
        if frame is not None and frame.timestamp != self._last_ts:
            self._last_ts = frame.timestamp
            first = self._image_shape != frame.image_u8.shape
            self._image_shape = frame.image_u8.shape
            self.image_item.setImage(frame.image_u8, autoLevels=False, levels=(0, 255))
            if first:
                h, w = self._image_shape
                self._viewbox.setRange(xRange=(0, w), yRange=(0, h), padding=0)
            self._draw_tracks(frame)
        self._draw_fov()
        self._update_status(frame)

    def _draw_tracks(self, frame: OverviewFrame) -> None:
        tracks = frame.tracks
        self._tracks_item.setData([{"pos": tr.centroid} for tr in tracks])
        selected = [tr for tr in tracks if tr.id == self.selected_track_id]
        self._selected_item.setData([{"pos": selected[0].centroid}] if selected else [])

        xs: list[float] = []
        ys: list[float] = []
        for tr in tracks:
            if len(tr.trace) >= 2:
                for px, py in tr.trace:
                    xs.append(px)
                    ys.append(py)
                xs.append(np.nan)
                ys.append(np.nan)
        if xs:
            self._trails_item.setData(np.array(xs, dtype=np.float64), np.array(ys, dtype=np.float64))
        else:
            self._trails_item.setData(np.empty(0), np.empty(0))

    def _draw_fov(self) -> None:
        stage_xy = self._stage_position()
        if self.calibration is None or stage_xy is None:
            self._fov_item.setData(np.empty(0), np.empty(0))
            return
        poly = self.calibration.fov_polygon_px(stage_xy, self._fov_um)
        self._fov_item.setData(poly[:, 0], poly[:, 1])

    def _update_status(self, frame: OverviewFrame | None) -> None:
        if self._calibrating:
            self.status_label.setText(
                f"Calibrating: move stage & click spot ({len(self._calib_points)}/4)")
            return
        cal_text = (f"Calibrated ({self.calibration.residual_um:.1f} µm)"
                    if self.calibration is not None else "Uncalibrated")
        if frame is None:
            self.status_label.setText(cal_text)
        else:
            self.status_label.setText(
                f"{cal_text} · {len(frame.tracks)} track(s) · {frame.fps:.1f} fps")

    def closeEvent(self, event) -> None:
        self._timer.stop()
        self._worker.stop()
        super().closeEvent(event)
