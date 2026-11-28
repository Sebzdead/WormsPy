"""ReviewWindow: play back a finished recording, every source frame-synced.

- The channels side by side (behaviour left, fluorescence right), each a `LiveView` as in the
  live window: fixed levels, LUT, exposure histogram, and the tracked point as it was tracked.
- The worm's path on the plate (µm): the whole path faint, the part travelled so far bright,
  the current position, and the event markers labelled where they happened.
- A scrub bar over the whole recording: tracking status and dropped frames as bands, event
  markers as labelled lines, and a playhead. Click or drag anywhere on it to scrub.

Every source follows one **position** (row of frames.csv), so frame *i* of each video, the plot
and the scrub bar always show the same exposure pair. Playback runs in real time by the
recorded capture times and skips frames the display cannot keep up with.
"""

import time
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from wormspy.core.frames import Frame, FrameHub
from wormspy.reader import Recording, open_recording
from wormspy.review import PlaybackClock, ReviewData, compute_calcium_stats
from wormspy.ui import theme
from wormspy.ui.calcium_stats import CalciumStatsWidget
from wormspy.ui.live_view import LiveView
from wormspy.ui.session_browser import SessionBrowser

MARGIN = 14
GAP = 12
SPEEDS = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
PLAYBACK_TICK_MS = 15
STATUS_COLOURS = {"tracking": theme.ACCENT_DIM, "lost": theme.AMBER, "override": theme.MUTED,
                  "limit": theme.RED}
LABELS = {"gcamp": "GCaMP", "dsred": "DsRed", "rfp": "RFP", "gfp": "GFP"}


def channel_label(channel: str) -> str:
    return LABELS.get(channel.lower(), channel.replace("_", " ").title())


def recordings_near(path: Path) -> tuple[list[Path], Path]:
    """The recordings to offer for `path` (a rec-NNN folder or a session folder), and the one
    to open first."""
    path = Path(path)
    if (path / "frames.csv").exists():
        siblings = sorted(p for p in path.parent.glob("rec-*") if (p / "frames.csv").exists())
        return (siblings if path in siblings else [path]), path
    recordings = sorted(p for p in path.glob("rec-*") if (p / "frames.csv").exists())
    if not recordings:
        raise FileNotFoundError(f"{path} holds no WormsPy recordings (no rec-*/frames.csv)")
    return recordings, recordings[0]


class _Sized:
    """Asks for a target size but may be squeezed below it, so it never pins the window
    (the same approach as `live_view.FeedCanvas`)."""

    _target = QSize(320, 320)

    def set_target(self, width: int, height: int) -> None:
        self._target = QSize(width, height)
        self.setMaximumSize(self._target)
        self.updateGeometry()

    def sizeHint(self) -> QSize:
        return self._target

    def minimumSizeHint(self) -> QSize:
        return QSize(0, 0)


class PositionPlot(_Sized, pg.PlotWidget):
    """The worm's path on the plate, in stage µm. Clicking an event marker jumps to it."""

    event_clicked = Signal(int)          # position

    def __init__(self) -> None:
        super().__init__()
        self.setBackground(theme.FEED_BACKGROUND)
        item = self.getPlotItem()
        item.setAspectLocked(True)
        item.showGrid(x=True, y=True, alpha=0.12)
        item.setMenuEnabled(False)
        for name in ("left", "bottom"):
            axis = item.getAxis(name)
            axis.setPen(theme.BORDER_STRONG)
            axis.setTextPen(theme.MUTED)
            axis.setStyle(tickFont=theme.mono_font(9))
            axis.enableAutoSIPrefix(False)        # stage µm, never "kµm"
        item.setLabel("bottom", "x", units="µm")
        item.setLabel("left", "y", units="µm")
        self.stage_line = self.plot(pen=pg.mkPen(theme.rgba(theme.MUTED, 70), width=1))
        self.path_line = self.plot(pen=pg.mkPen(theme.rgba(theme.ACCENT, 60), width=1.5),
                                   connect="finite")
        self.trail_line = self.plot(pen=pg.mkPen(theme.rgba(theme.ACCENT, 230), width=2),
                                    connect="finite")
        self.start_marker = pg.ScatterPlotItem(size=9, symbol="o", brush=pg.mkBrush(None),
                                               pen=pg.mkPen(theme.TEXT, width=1.5))
        self.event_markers = pg.ScatterPlotItem(size=11, symbol="d",
                                                brush=pg.mkBrush(theme.AMBER),
                                                pen=pg.mkPen(theme.FEED_BACKGROUND, width=1),
                                                hoverable=True, hoverSize=14)
        self.event_markers.sigClicked.connect(self._marker_clicked)
        self.current_marker = pg.ScatterPlotItem(size=13, symbol="o",
                                                 brush=pg.mkBrush(theme.ACCENT),
                                                 pen=pg.mkPen(theme.FEED_BACKGROUND, width=1.5))
        for marker in (self.start_marker, self.event_markers, self.current_marker):
            self.addItem(marker)
        self._labels: list[pg.TextItem] = []
        self._path = np.empty((0, 2))

    def set_data(self, data: ReviewData) -> None:
        self._path = data.path_um
        self.stage_line.setData(data.stage_um[:, 0], data.stage_um[:, 1], connect="finite")
        self.path_line.setData(data.worm_um[:, 0], data.worm_um[:, 1], connect="finite")
        known = np.flatnonzero(np.isfinite(self._path).all(axis=1))
        self.start_marker.setData([] if not len(known) else [{"pos": self._path[known[0]]}])
        for label in self._labels:
            self.removeItem(label)
        self._labels = []
        spots = []
        for event in data.events:
            if not np.isfinite(event.xy_um).all():
                continue
            spots.append({"pos": event.xy_um, "data": event.position})
            label = pg.TextItem(event.label, color=theme.AMBER, anchor=(0, 1.1))
            label.setFont(theme.mono_font(9))
            label.setPos(*event.xy_um)
            self.addItem(label)
            self._labels.append(label)
        self.event_markers.setData(spots)
        self.getPlotItem().enableAutoRange()
        self.getPlotItem().autoRange()

    @property
    def labels(self) -> list[str]:
        return [label.toPlainText() for label in self._labels]

    def show_position(self, position: int) -> None:
        trail = self._path[: position + 1]
        self.trail_line.setData(trail[:, 0], trail[:, 1], connect="finite")
        here = self._path[position]
        self.current_marker.setData([] if not np.isfinite(here).all() else [{"pos": here}])

    def _marker_clicked(self, _item, points, *_) -> None:
        if len(points):
            self.event_clicked.emit(int(points[0].data()))


class _ScrubBox(pg.ViewBox):
    """A ViewBox that turns clicks and drags into positions along x instead of panning."""

    scrubbed = Signal(float)

    def mouseClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept()
            self.scrubbed.emit(self.mapSceneToView(event.scenePos()).x())

    def mouseDragEvent(self, event, axis=None) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept()
            self.scrubbed.emit(self.mapSceneToView(event.scenePos()).x())

    def wheelEvent(self, event, axis=None) -> None:
        event.ignore()


class ScrubBar(pg.PlotWidget):
    """The whole recording along time: status bands, event lines and the playhead."""

    scrubbed = Signal(float)             # seconds since the first frame

    BAND_TOP = 0.34                      # status and dropped bands take the bottom third

    def __init__(self) -> None:
        self._box = _ScrubBox()
        super().__init__(viewBox=self._box)
        self._box.scrubbed.connect(self.scrubbed)
        self.setBackground(theme.PANEL)
        self.setFixedHeight(96)
        item = self.getPlotItem()
        item.setMenuEnabled(False)
        item.hideButtons()
        item.hideAxis("left")
        axis = item.getAxis("bottom")
        axis.setPen(theme.BORDER_STRONG)
        axis.setTextPen(theme.MUTED)
        axis.setStyle(tickFont=theme.mono_font(9))
        item.setLabel("bottom", units="s")
        self._box.setMouseEnabled(x=False, y=False)
        self._box.setYRange(0, 1, padding=0)
        self.setToolTip("Click or drag to scrub.\nBottom band: tracking (green), target lost "
                        "(amber), joystick (grey), stage limit (red).\nThin band above it: "
                        "dropped frames (red). Amber lines: event markers.")
        self._bands = pg.ImageItem()
        self.addItem(self._bands)
        self.playhead = pg.InfiniteLine(angle=90, movable=False,
                                        pen=pg.mkPen(theme.ACCENT, width=2))
        self.playhead.setZValue(10)
        self.addItem(self.playhead)
        self.event_lines: list[pg.InfiniteLine] = []

    def set_data(self, data: ReviewData) -> None:
        n = len(data)
        end = max(data.duration_s + 1 / data.fps, 1e-3)
        bands = np.zeros((2, max(n, 1), 4), np.uint8)
        for status, colour in STATUS_COLOURS.items():
            bands[0, data.status == status] = theme.rgba(colour, 220)
        bands[1, data.dropped] = theme.rgba(theme.RED, 255)
        self._bands.setImage(bands, autoLevels=False)
        # rows are y (row 0 at the bottom), columns are frames spread over the recording
        self._bands.setRect(QRectF(0, 0, end, self.BAND_TOP))
        for line in self.event_lines:
            self.removeItem(line)
        self.event_lines = []
        for event in data.events:
            line = pg.InfiniteLine(
                pos=event.time_s, angle=90, movable=False,
                pen=pg.mkPen(theme.rgba(theme.AMBER, 190), width=1),
                label=event.label,
                labelOpts={"position": 0.86, "color": theme.AMBER, "anchors": [(0, 0.5), (0, 0.5)],
                           "fill": theme.rgba(theme.PANEL, 200)})
            line.label.setFont(theme.mono_font(9))
            self.addItem(line)
            self.event_lines.append(line)
        self._box.setLimits(xMin=0, xMax=end)
        self._box.setXRange(0, end, padding=0)
        self._box.setYRange(0, 1, padding=0)

    def show_time(self, time_s: float) -> None:
        self.playhead.setPos(time_s)


class ReviewWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WormsPy Review")
        self.data: ReviewData | None = None
        self.recording: Recording | None = None
        self.recordings: list[Path] = []
        self.position = 0
        self.views: list[LiveView] = []
        self._hub = FrameHub()
        self._serial = 0                  # makes every published frame new to its LiveView
        self._luts: dict[str, str] = {}
        self._pending: int | None = None
        self._clock: PlaybackClock | None = None
        self._speed = 1.0

        self.wordmark = QLabel("WormsPy")
        self.wordmark.setStyleSheet(f"color: {theme.ACCENT}; font-size: 24px; font-weight: 800;"
                                    "letter-spacing: -0.5px;")
        subtitle = QLabel("review")
        subtitle.setObjectName("muted")
        self.sessions_button = QPushButton("Sessions")
        self.sessions_button.setCheckable(True)
        self.sessions_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.recording_box = QComboBox()
        self.recording_box.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.recording_box.activated.connect(
            lambda index: self.open(self.recordings[index]))
        self.info_label = QLabel("")
        self.info_label.setObjectName("muted")
        self.warning_chip = QLabel("")
        self.warning_chip.setObjectName("chip")
        self.warning_chip.setProperty("tone", "warn")
        self.warning_chip.hide()
        open_button = QPushButton("Open…")
        open_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        open_button.clicked.connect(self.ask_open)
        header = QHBoxLayout()
        header.setSpacing(10)
        header.addWidget(self.wordmark)
        header.addWidget(subtitle, 0, Qt.AlignmentFlag.AlignBottom)
        header.addSpacing(14)
        header.addWidget(self.sessions_button)
        header.addWidget(self.recording_box)
        header.addWidget(self.info_label)
        header.addWidget(self.warning_chip)
        header.addStretch(1)
        header.addWidget(open_button)

        self.feeds = QHBoxLayout()
        self.feeds.setSpacing(GAP)
        self.plot = PositionPlot()
        self.plot.event_clicked.connect(self.seek)
        self.plot_title = QLabel("WORLD TRAJECTORY")
        self.plot_title.setObjectName("feedTitle")
        plot_column = QVBoxLayout()
        plot_column.setSpacing(4)
        plot_column.addWidget(self.plot_title)
        plot_column.addWidget(self.plot)
        self.calcium_stats = CalciumStatsWidget()
        self._bottom_row = QHBoxLayout()
        self._bottom_row.setSpacing(GAP)
        self._bottom_row.addStretch(1)
        self._bottom_row.addLayout(plot_column)
        self._bottom_row.addWidget(self.calcium_stats)
        self._bottom_row.addStretch(1)

        self.play_button = QPushButton("▶  Play")
        self.play_button.setProperty("role", "primary")
        self.play_button.setMinimumWidth(96)
        self.play_button.clicked.connect(self.toggle_play)
        buttons = [self.play_button]
        for text, tip, slot in (
                ("⏮", "Previous event  (Page Up)", self.previous_event),
                ("◀︎", "Back one frame  (←)", lambda: self.step(-1)),
                ("▶︎", "Forward one frame  (→)", lambda: self.step(1)),
                ("⏭", "Next event  (Page Down)", self.next_event)):
            button = QPushButton(text)
            button.setToolTip(tip)
            button.clicked.connect(slot)
            buttons.append(button)
        self.speed_box = QComboBox()
        for speed in SPEEDS:
            self.speed_box.addItem(f"{speed:g}×", speed)
        self.speed_box.setCurrentIndex(SPEEDS.index(1.0))
        self.speed_box.currentIndexChanged.connect(
            lambda i: self.set_speed(self.speed_box.itemData(i)))
        self.readout = QLabel("")
        self.readout.setObjectName("readout")
        self.readout.setFont(theme.mono_font(11))
        self.readout.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.event_chip = QLabel("")
        self.event_chip.setObjectName("chip")
        self.event_chip.setProperty("tone", "warn")
        self.event_chip.hide()
        self.dropped_chip = QLabel("DROPPED")
        self.dropped_chip.setObjectName("chip")
        self.dropped_chip.setProperty("tone", "rec")
        self.dropped_chip.setToolTip("A camera dropped this frame: its image is a zero-filled "
                                     "placeholder.")
        self.dropped_chip.hide()
        transport = QHBoxLayout()
        transport.setSpacing(8)
        for widget in (*buttons, self.speed_box):
            widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            transport.addWidget(widget)
        transport.addSpacing(10)
        transport.addWidget(self.readout)
        transport.addWidget(self.dropped_chip)
        transport.addWidget(self.event_chip)
        transport.addStretch(1)
        self.transport = QFrame()
        self.transport.setObjectName("readouts")
        self.transport.setLayout(transport)
        transport.setContentsMargins(10, 8, 10, 8)

        self.scrub_bar = ScrubBar()
        self.scrub_bar.scrubbed.connect(self.scrub_to_time)

        self._viewer = QWidget()
        self._column = QVBoxLayout(self._viewer)
        self._column.setContentsMargins(MARGIN, 8, MARGIN, MARGIN)
        self._column.setSpacing(8)
        self._column.addLayout(header)
        self._column.addLayout(self.feeds)
        self._column.addLayout(self._bottom_row)
        self._column.addWidget(self.transport)
        self._column.addWidget(self.scrub_bar)
        self._column.addStretch(1)

        self.browser = SessionBrowser()
        self.browser.setMinimumWidth(340)
        self.browser.hide()
        self.browser.recording_selected.connect(self.open_path)
        self.browser.root_change_requested.connect(self.ask_root)
        self.browser.pipeline_finished.connect(self._on_pipeline_finished)
        self.sessions_button.toggled.connect(self._toggle_browser)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("central")
        self.splitter.addWidget(self.browser)
        self.splitter.addWidget(self._viewer)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.setCentralWidget(self.splitter)
        self._fitted_for = None
        self._actions()

        self._play_timer = QTimer(self)
        self._play_timer.setInterval(PLAYBACK_TICK_MS)
        self._play_timer.timeout.connect(self._play_tick)
        self._scrub_timer = QTimer(self)             # coalesces a drag's many scrub events
        self._scrub_timer.setSingleShot(True)
        self._scrub_timer.setInterval(0)
        self._scrub_timer.timeout.connect(self._flush_scrub)

    def _actions(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        open_action = QAction("Open recording…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.ask_open)
        file_menu.addAction(open_action)
        menu = self.menuBar().addMenu("Playback")
        for text, keys, slot in (
                ("Play / pause", "Space", self.toggle_play),
                ("Forward one frame", "Right", lambda: self.step(1)),
                ("Back one frame", "Left", lambda: self.step(-1)),
                ("Forward one second", "Shift+Right", lambda: self.step_seconds(1)),
                ("Back one second", "Shift+Left", lambda: self.step_seconds(-1)),
                ("Next event", "PgDown", self.next_event),
                ("Previous event", "PgUp", self.previous_event),
                ("First frame", "Home", lambda: self.seek(0)),
                ("Last frame", "End", lambda: self.seek(len(self.data or ()) - 1))):
            action = QAction(text, self)
            action.setShortcut(QKeySequence(keys))
            action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
            action.triggered.connect(slot)
            menu.addAction(action)

    # --- opening ----------------------------------------------------------------------------

    def _toggle_browser(self, visible: bool) -> None:
        self.browser.setVisible(bool(visible))
        self._fitted_for = None
        self._fit(force=True)

    def ask_root(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose sessions root folder", "")
        if folder:
            self.open_root(Path(folder))

    def open_root(self, root: Path) -> None:
        """Scan `root` into the session browser, show it, and open the first recording."""
        self.browser.set_root(root)
        self.sessions_button.setChecked(True)
        visible = self.browser.visible_entries()
        if visible:
            self.open_path(visible[0].path)

    def _on_pipeline_finished(self, rec_dir: Path) -> None:
        if self.recording is not None and self.recording.path.resolve() == rec_dir.resolve():
            pos = self.position
            self.open(self.recording.path)
            self.seek(pos)

    def ask_open(self) -> None:
        start = str(self.recording.path.parent) if self.recording else ""
        folder = QFileDialog.getExistingDirectory(
            self, "Open a recording (rec-NNN) or session folder", start)
        if folder:
            try:
                self.open_path(Path(folder))
            except (OSError, ValueError, KeyError) as exc:
                QMessageBox.warning(self, "Cannot open", str(exc))

    def open_path(self, path: Path) -> None:
        """A rec-NNN folder, or a session folder (its first recording opens)."""
        recordings, first = recordings_near(path)
        self.recordings = recordings
        self.recording_box.clear()
        self.recording_box.addItems([p.name for p in recordings])
        self.open(first)

    def open(self, path: Path) -> None:
        self.pause()
        recording = open_recording(path)
        if self.recording is not None:
            self.recording.close()
        self.recording = recording
        self.data = ReviewData(recording)
        if path in self.recordings:
            self.recording_box.setCurrentIndex(self.recordings.index(path))
        self._describe(recording)
        self._build_views()
        self.plot.set_data(self.data)
        self.calcium_stats.set_stats(compute_calcium_stats(recording, self.data))
        self.browser.select_recording(path)
        self.scrub_bar.set_data(self.data)
        self._fitted_for = None
        self._fit()
        # the feeds level themselves on the first frame they show, so show a real one first
        self.seek(self.data.first_valid)
        if self.data.first_valid:
            self.seek(0)

    def _describe(self, recording: Recording) -> None:
        metadata = (recording.session or {}).get("metadata", {})
        details = [metadata.get(key) for key in ("animal_id", "condition", "operator")]
        data = self.data
        details += [f"{len(data)} frames", f"{data.fps:g} fps", _mmss(data.duration_s)]
        drops = int(data.dropped.sum())
        if drops:
            details.append(f"{drops} dropped")
        self.info_label.setText("  ·  ".join(str(d) for d in details if d))
        self.setWindowTitle(f"WormsPy Review — {recording.path.parent.name}/{recording.path.name}")
        self.warning_chip.setVisible(bool(recording.warnings))
        self.warning_chip.setText("CUT SHORT" if not recording.complete else "CHECK")
        self.warning_chip.setToolTip("\n".join(recording.warnings))
        theme.repolish(self.warning_chip)

    def _build_views(self) -> None:
        for view in self.views:
            self._luts[view.channel] = view.lut_name
            self.feeds.removeWidget(view)
            view.deleteLater()
        roles = {name: ch.role for name, ch in self.recording.channels.items()}
        names = sorted(roles, key=lambda name: roles[name] != "behaviour")   # behaviour left
        self.views = []
        for name in names:
            view = LiveView(self._hub, channel=name, title=channel_label(name))
            view.mask_checkbox.hide()                # no threshold masks in a recording
            view.set_lut(self._luts.get(name, "grey"))
            for control in view.findChildren(QWidget):   # keys belong to playback
                control.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.feeds.addWidget(view)
            self.views.append(view)

    # --- navigation -------------------------------------------------------------------------

    def seek(self, position: int) -> None:
        """Show one frame in every view, the plot and the scrub bar."""
        if self.data is None or not len(self.data):
            return
        self.position = position = self.data.clamp(position)
        frame_index = int(self.data.frame_index[position])
        time_s = float(self.data.time_s[position])
        self._serial += 1
        for view in self.views:
            image = self.recording[view.channel][frame_index]
            self._hub.publish(view.channel, Frame(image, device_frame_id=self._serial,
                                                  capture_ts=time_s))
            view.refresh()
        overlays = self.data.overlays(position)
        for view in self.views:
            overlay = overlays.get(view.channel)
            view.set_tracked_point(None if overlay is None else overlay.point_px,
                                   mapped=overlay is not None and overlay.mapped)
        self.plot.show_position(position)
        self.calcium_stats.show_time(time_s)
        self.scrub_bar.show_time(time_s)
        self._show_readout(position)

    def scrub_to_time(self, time_s: float) -> None:
        if self.data is None:
            return
        self._pending = self.data.position_at(time_s)
        if self._play_timer.isActive():
            self._clock.start(self._pending, time.monotonic())
        self._scrub_timer.start()

    def _flush_scrub(self) -> None:
        if self._pending is not None:
            position, self._pending = self._pending, None
            self.seek(position)

    def step(self, frames: int) -> None:
        self.pause()
        self.seek(self.position + frames)

    def step_seconds(self, seconds: float) -> None:
        if self.data is not None:
            self.pause()
            self.seek(self.data.position_at(self.data.time_s[self.position] + seconds))

    def next_event(self) -> None:
        event = self.data and self.data.next_event(self.position)
        if event:
            self.seek(event.position)

    def previous_event(self) -> None:
        event = self.data and self.data.previous_event(self.position)
        if event:
            self.seek(event.position)

    # --- playback ---------------------------------------------------------------------------

    @property
    def playing(self) -> bool:
        return self._play_timer.isActive()

    def toggle_play(self) -> None:
        self.pause() if self.playing else self.play()

    def play(self) -> None:
        if self.data is None or len(self.data) < 2:
            return
        if self.position >= len(self.data) - 1:
            self.seek(0)                        # play again from the start
        self._clock = PlaybackClock(self.data, self._speed)
        self._clock.start(self.position, time.monotonic())
        self._play_timer.start()
        self.play_button.setText("❚❚  Pause")

    def pause(self) -> None:
        self._play_timer.stop()
        self._clock = None
        self.play_button.setText("▶  Play")

    def set_speed(self, speed: float) -> None:
        self._speed = float(speed)
        if self.playing:
            self._clock = PlaybackClock(self.data, self._speed)
            self._clock.start(self.position, time.monotonic())

    def _play_tick(self) -> None:
        position = self._clock.position(time.monotonic())
        if position != self.position:
            self.seek(position)
        if position >= len(self.data) - 1:
            self.pause()

    # --- readouts and layout ----------------------------------------------------------------

    def _show_readout(self, position: int) -> None:
        data = self.data
        x, y = data.path_um[position]
        where = "" if not np.isfinite([x, y]).all() else f"   X {x:9.1f}  Y {y:9.1f} µm"
        status = data.status[position] or "—"
        self.readout.setText(
            f"frame {data.frame_index[position]:>6}   "
            f"{_mmss(data.time_s[position])} / {_mmss(data.duration_s)}   "
            f"{status:<8}{where}")
        self.dropped_chip.setVisible(bool(data.dropped[position]))
        labels = data.events_at(position)
        self.event_chip.setVisible(bool(labels))
        self.event_chip.setText("  ·  ".join(labels).upper())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._fit(force=True)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._fit(force=True)

    def _fit(self, force: bool = False) -> None:
        """Top row: Brightfield & Calcium feeds at camera aspect. Bottom row: World trajectory &
        Calcium stats side by side."""
        if not self.views:
            return
        viewer_w = self._viewer.width()
        viewer_h = self._viewer.height()
        aspects = [view.aspect for view in self.views]
        key = (viewer_w, viewer_h, tuple(aspects), self.browser.isVisible())
        if key == self._fitted_for and not force:
            return
        self._fitted_for = key
        chrome = max(view.chrome_height() for view in self.views)
        avail_w = max(320, viewer_w - 2 * MARGIN)
        feeds_w = avail_w - GAP * max(len(self.views) - 1, 0)
        spacing = self._column.spacing()
        others = (self.wordmark.sizeHint().height() + self.transport.sizeHint().height()
                  + self.scrub_bar.height() + chrome + self.plot_title.sizeHint().height()
                  + 8 + MARGIN + 5 * spacing)
        avail_h = max(180, viewer_h - others)
        top_h = max(60, min(feeds_w / sum(aspects), avail_h * 0.58))
        bottom_h = max(120, avail_h - top_h)
        for view, aspect in zip(self.views, aspects, strict=True):
            view.canvas.set_target(int(top_h * aspect), int(top_h))
        plot_w = min(int(bottom_h), int((avail_w - GAP) * 0.45))
        stats_w = max(200, avail_w - GAP - plot_w)
        self.plot.set_target(plot_w, int(bottom_h))
        self.calcium_stats.set_target(stats_w, int(bottom_h))

    def closeEvent(self, event) -> None:
        self.pause()
        self.browser.stop_runner()
        if self.recording is not None:
            self.recording.close()
        super().closeEvent(event)


def _mmss(seconds: float) -> str:
    """mm:ss.s"""
    minutes, rest = divmod(max(float(seconds), 0.0), 60)
    return f"{int(minutes):02d}:{rest:04.1f}"
