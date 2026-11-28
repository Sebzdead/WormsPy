"""ControlPanel: the row of control cards below the feeds (ADR 0004/0010).

Buttons only dispatch Commands. `render(state)` is the single place that sets every enabled
state and label, so the panel always shows what the state machine says, never a local guess.
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from wormspy.control import AppState, Mode, TrackingStatus
from wormspy.control import commands as C
from wormspy.ui import theme
from wormspy.ui.bridge import StateBridge
from wormspy.ui.camera_card import CameraCard

ESTIMATORS = (("dark_object", "Brightfield silhouette", "behaviour"),
              ("bright_marker", "Fluorescent marker", "fluorescence"))
SOURCES = (("behaviour", "Brightfield camera", "behaviour"),
           ("fluorescence", "Fluorescence camera", "fluorescence"))
POLARITIES = (("dark", "Dark on bright"), ("bright", "Bright on dark"))
TRACKING_TEXT = {
    TrackingStatus.OFF: ("Off", theme.MUTED),
    TrackingStatus.TRACKING: ("Tracking", theme.ACCENT),
    TrackingStatus.LOST: ("Target lost", theme.RED),
    TrackingStatus.OVERRIDE: ("Joystick override", theme.AMBER),
    TrackingStatus.LIMIT: ("At stage limit", theme.AMBER),
}


def format_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class ControlPanel(QWidget):
    def __init__(self, bridge: StateBridge,
                 camera_labels: tuple[str, str] = ("Clock cam", "Follower"),
                 channel_sources: tuple[tuple[str, str, str], ...] | None = None) -> None:
        super().__init__()
        self._bridge = bridge
        self._state = bridge.state
        self._sources = SOURCES if channel_sources is None else channel_sources
        self._elapsed_s: float | None = None
        layout = QHBoxLayout(self)          # one row of cards below the feeds
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # session (and the live switch: nothing happens before the camera runs)
        session = QGroupBox("SESSION")
        self.session_box = session
        grid = QGridLayout(session)
        self._session_grid = grid
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        self.live_button = QPushButton("Start live")
        self.live_button.setProperty("role", "primary")
        self.live_button.clicked.connect(self._toggle_live)
        self.condition, self.animal_id, self.operator = QLineEdit(), QLineEdit(), QLineEdit()
        self.animal_id.setPlaceholderText("e.g. N2 #3")
        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(30)
        self.notes.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.notes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for field in (self.condition, self.animal_id, self.operator, self.notes):
            field.setMinimumWidth(48)
        self.new_session_button = QPushButton("New session")
        self.new_session_button.clicked.connect(self._new_session)
        self.session_label = QLabel()
        self.session_label.setObjectName("muted")
        grid.addWidget(self.live_button, 0, 0, 1, 4)
        for row, col, text, field in ((1, 0, "Condition", self.condition),
                                      (1, 2, "Animal", self.animal_id),
                                      (2, 0, "Operator", self.operator),
                                      (2, 2, "Notes", self.notes)):
            label = QLabel(text)
            label.setObjectName("muted")
            grid.addWidget(label, row, col)
            grid.addWidget(field, row, col + 1)
        grid.addWidget(self.new_session_button, 3, 0, 1, 2)
        grid.addWidget(self.session_label, 3, 2, 1, 2)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        QWidget.setTabOrder(self.condition, self.animal_id)
        QWidget.setTabOrder(self.animal_id, self.operator)
        QWidget.setTabOrder(self.operator, self.notes)
        QWidget.setTabOrder(self.notes, self.new_session_button)
        layout.addWidget(session, 3)

        # recording
        recording = QGroupBox("RECORDING")
        rec_layout = QVBoxLayout(recording)
        rec_layout.setSpacing(6)
        self.record_button = QPushButton()
        self.record_button.clicked.connect(lambda: bridge.dispatch(C.ToggleRecording()))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 86400)
        self.duration_spin.setSingleStep(10)
        self.duration_spin.setSpecialValueText("∞")
        self.duration_spin.setSuffix(" s")
        self.duration_spin.setKeyboardTracking(False)
        self.duration_spin.setMinimumWidth(68)
        self.duration_spin.setToolTip("Auto-stop after N seconds (0 = manual stop)")
        self.duration_spin.valueChanged.connect(self._duration_changed)
        rec_top = QHBoxLayout()
        rec_top.setSpacing(6)
        rec_top.addWidget(self.record_button, 1)
        rec_top.addWidget(self._muted("Limit"))
        rec_top.addWidget(self.duration_spin)
        self.recording_label = QLabel()
        self.recording_label.setObjectName("muted")
        self.recording_label.setFont(theme.mono_font())
        self.event_label = QLineEdit()
        self.event_label.setPlaceholderText("event label")
        self.event_label.setMinimumWidth(64)
        self.mark_button = QPushButton("Mark event")
        self.mark_button.clicked.connect(
            lambda: bridge.dispatch(C.MarkEvent(label=self.event_label.text() or "marker")))
        marker_row = QHBoxLayout()
        marker_row.setSpacing(8)
        marker_row.addWidget(self.event_label, 1)
        marker_row.addWidget(self.mark_button)
        rec_layout.addLayout(rec_top)
        rec_layout.addWidget(self.recording_label)
        rec_layout.addLayout(marker_row)
        rec_layout.addStretch(1)
        layout.addWidget(recording, 2)

        # tracking
        tracking = QGroupBox("TRACKING")
        self.tracking_box = tracking
        tracking.setMaximumWidth(250)
        trk = QFormLayout(tracking)
        trk.setHorizontalSpacing(8)
        trk.setVerticalSpacing(6)
        trk.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.estimator_box = QComboBox()
        for key, label, _source in ESTIMATORS:
            self.estimator_box.addItem(label, key)
        self.source_box = QComboBox()
        for key, label, _role in self._sources:
            self.source_box.addItem(label, key)
        self.polarity_box = QComboBox()
        for key, label in POLARITIES:
            self.polarity_box.addItem(label, key)
        for box in (self.estimator_box, self.source_box, self.polarity_box):
            box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            box.setMinimumContentsLength(8)
        self.estimator_box.currentIndexChanged.connect(self._estimator_chosen)
        self.source_box.currentIndexChanged.connect(self._source_chosen)
        self.polarity_box.currentIndexChanged.connect(self._polarity_chosen)
        self.track_button = QPushButton()
        self.track_button.setProperty("role", "primary")
        self.track_button.clicked.connect(lambda: bridge.dispatch(C.ToggleTracking()))
        self.tracking_label = QLabel()
        trk.addRow(self._muted("Target"), self.estimator_box)
        trk.addRow(self._muted("Camera"), self.source_box)
        trk.addRow(self._muted("Polarity"), self.polarity_box)
        trk.addRow(self.track_button)
        trk.addRow(self._muted("Status"), self.tracking_label)
        layout.addWidget(tracking, 2)

        self.cameras = CameraCard(bridge, camera_labels)
        layout.addWidget(self.cameras, 3)

        # focus and calibration: visually separated Focus, Calibration, and Gamepad sections
        stage = QGroupBox("FOCUS && CALIBRATION")
        self.stage_box = stage
        stg = QVBoxLayout(stage)
        stg.setSpacing(6)
        focus_row = QHBoxLayout()
        focus_row.setSpacing(6)
        self.set_focus_button = QPushButton("Set focus")
        self.set_focus_button.clicked.connect(lambda: bridge.dispatch(C.SetFocus()))
        self.return_focus_button = QPushButton("Return to focus")
        self.return_focus_button.clicked.connect(lambda: bridge.dispatch(C.ReturnToFocus()))
        focus_row.addWidget(self.set_focus_button, 1)
        focus_row.addWidget(self.return_focus_button, 1)
        self.focus_label = QLabel()
        self.focus_label.setObjectName("muted")
        stg.addLayout(focus_row)
        stg.addWidget(self.focus_label)
        stg.addWidget(self._divider())

        calibration_row = QHBoxLayout()
        calibration_row.setSpacing(8)
        self.calibrate_button = QPushButton("Calibrate stage")
        self.calibrate_button.setToolTip("Needs a bead or grid slide in focus under the objective")
        self.calibrate_button.clicked.connect(lambda: bridge.dispatch(C.Calibrate()))
        self.calibration_label = QLabel()
        self.calibration_label.setObjectName("muted")
        self.calibration_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        calibration_row.addWidget(self.calibrate_button)
        calibration_row.addWidget(self.calibration_label, 1)
        stg.addLayout(calibration_row)
        stg.addWidget(self._divider())

        self.reset_gamepad_button = QPushButton("Reset gamepad")
        self.reset_gamepad_button.setToolTip("Reinitialize the gamepad controller without restarting")
        self.reset_gamepad_button.clicked.connect(lambda: bridge.dispatch(C.ResetGamepad()))
        stg.addWidget(self.reset_gamepad_button)
        stg.addStretch(1)
        layout.addWidget(stage, 2)

        # status text wraps rather than widening the window
        for label in (self.session_label, self.focus_label, self.calibration_label):
            label.setWordWrap(True)

        bridge.state_changed.connect(self.render)
        self.render(bridge.state)

    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setObjectName("sectionDivider")
        line.setFixedHeight(1)
        return line

    @staticmethod
    def _muted(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("muted")
        return label

    # --- commands ------------------------------------------------------------------------

    def _toggle_live(self) -> None:
        self._bridge.dispatch(C.StartLive() if self._state.mode is Mode.IDLE else C.StopLive())

    def _new_session(self) -> None:
        self._bridge.dispatch(C.NewSession(metadata={
            "animal_id": self.animal_id.text().strip(),
            "operator": self.operator.text().strip(),
            "condition": self.condition.text().strip(),
            "notes": self.notes.toPlainText().strip()}))

    def _duration_changed(self, value: int) -> None:
        self._bridge.dispatch(C.SetRecordingDuration(duration_s=None if value == 0 else float(value)))

    def _estimator_chosen(self, _index: int) -> None:
        name = self.estimator_box.currentData()
        preferred_role = next(src for key, _label, src in ESTIMATORS if key == name)
        default_source = next(
            (key for key, _label, role in self._sources if role == preferred_role),
            self.source_box.currentData())
        self._bridge.dispatch(C.SelectEstimator(name=name, source_channel=default_source,
                                                polarity=self.polarity_box.currentData()))

    def _source_chosen(self, _index: int) -> None:
        self._bridge.dispatch(C.SelectEstimator(name=self.estimator_box.currentData(),
                                                source_channel=self.source_box.currentData(),
                                                polarity=self.polarity_box.currentData()))

    def _polarity_chosen(self, _index: int) -> None:
        self._bridge.dispatch(C.SelectEstimator(name=self.estimator_box.currentData(),
                                                source_channel=self.source_box.currentData(),
                                                polarity=self.polarity_box.currentData()))

    def set_recording_elapsed(self, elapsed_s: float | None) -> None:
        self._elapsed_s = elapsed_s
        if self._state.mode is Mode.RECORDING:
            self._update_recording_label()

    def _update_recording_label(self) -> None:
        s = self._state
        if s.mode is not Mode.RECORDING:
            limit = (f" (limit {format_duration(s.recording_duration_s)})"
                     if s.recording_duration_s is not None else "")
            self.recording_label.setText(f"Not recording{limit}")
            return
        elapsed = format_duration(0.0 if self._elapsed_s is None else self._elapsed_s)
        if s.recording_duration_s is not None:
            elapsed = f"{elapsed} / {format_duration(s.recording_duration_s)}"
        self.recording_label.setText(
            f"{s.recording_name} · {elapsed} · {s.recording_drops} dropped")

    # --- the single source of truth for the panel's appearance ------------------------------

    def render(self, s: AppState) -> None:
        self._state = s
        self.cameras.render(s)
        live, recording = s.mode is not Mode.IDLE, s.mode is Mode.RECORDING
        busy = s.calibrating
        tracking_on = s.tracking is not TrackingStatus.OFF
        if not recording:
            self._elapsed_s = None

        self.live_button.setText("Start live" if s.mode is Mode.IDLE else "Stop live")
        self.live_button.setEnabled(not recording and not busy)

        self.new_session_button.setEnabled(not recording)
        self.session_label.setText(Path(s.session_dir).name if s.session_dir else "No session")

        self.record_button.setText("■ Stop recording" if recording else "● Record")
        self.record_button.setProperty("role", "danger" if recording else "primary")
        theme.repolish(self.record_button)
        self.record_button.setEnabled(recording or (s.mode is Mode.LIVE and s.session_dir is not None
                                                    and not busy))
        self.duration_spin.blockSignals(True)
        self.duration_spin.setValue(0 if s.recording_duration_s is None
                                    else round(s.recording_duration_s))
        self.duration_spin.blockSignals(False)
        self.duration_spin.setEnabled(not recording)
        self._update_recording_label()
        self.mark_button.setEnabled(recording)
        self.event_label.setEnabled(recording)

        self.track_button.setText("Stop tracking" if tracking_on else "Start tracking")
        self.track_button.setEnabled(tracking_on or (live and s.calibrated and not busy))
        text, colour = TRACKING_TEXT[s.tracking]
        self.tracking_label.setText(text)
        self.tracking_label.setStyleSheet(f"color: {colour}; font-weight: 600;")
        source_index = self.source_box.findData(s.source_channel)
        if source_index < 0:
            role_match = next((i for i, (_k, _l, role) in enumerate(self._sources)
                               if role == s.source_channel), 0)
            source_index = role_match
        self.estimator_box.blockSignals(True)
        self.estimator_box.setCurrentIndex(max(0, self.estimator_box.findData(s.estimator)))
        self.estimator_box.blockSignals(False)
        self.estimator_box.setEnabled(not tracking_on)
        self.source_box.blockSignals(True)
        self.source_box.setCurrentIndex(max(0, source_index))
        self.source_box.blockSignals(False)
        self.source_box.setEnabled(not tracking_on)
        self.polarity_box.blockSignals(True)
        self.polarity_box.setCurrentIndex(max(0, self.polarity_box.findData(s.polarity)))
        self.polarity_box.blockSignals(False)
        self.polarity_box.setEnabled(not tracking_on and s.estimator == "dark_object")

        self.set_focus_button.setEnabled(not busy)
        self.return_focus_button.setEnabled(s.focus_z_um is not None and not busy)
        self.reset_gamepad_button.setEnabled(not busy)
        self.focus_label.setText(f"Focus z = {s.focus_z_um:.0f} µm" if s.focus_z_um is not None
                                 else "No focus stored")

        self.calibrate_button.setEnabled(s.mode is Mode.LIVE and not tracking_on and not busy)
        self.calibration_label.setText("Calibrating…" if busy else
                                       "Calibrated" if s.calibrated else "Not calibrated")
        cal_colour = theme.AMBER if busy else theme.ACCENT if s.calibrated else theme.MUTED
        self.calibration_label.setStyleSheet(f"color: {cal_colour};")
