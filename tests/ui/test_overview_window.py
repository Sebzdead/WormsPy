"""OverviewWindow: start/stop, click-to-move snapping, and 4-point calibration."""

import time

import cv2
import numpy as np
import pytest

from wormspy.config import OverviewConfig
from wormspy.control import AppState, Mode, StateStore
from wormspy.control import effects as X
from wormspy.core.cameras import Camera
from wormspy.core.frames import Frame
from wormspy.overview.calibration import OverviewCalibration
from wormspy.overview.worker import OverviewWorker
from wormspy.ui.bridge import StateBridge
from wormspy.ui.overview_window import OverviewWindow


class _DummyCam(Camera):
    def __init__(self):
        self._idx = 0

    def begin(self):
        pass

    def end(self):
        pass

    def read(self):
        img = np.full((200, 200), 200, np.uint8)
        if self._idx > 0:
            cv2.circle(img, (80, 90), 6, 40, -1)
        fid = self._idx
        self._idx += 1
        time.sleep(0.01)
        return Frame(image=img, device_frame_id=fid, capture_ts=time.monotonic())

    def is_open(self):
        return True

    def release(self):
        pass


def _calib():
    return OverviewCalibration.fit(
        [(0, 0), (200, 0), (200, 200), (0, 200)],
        [(0, 0), (20_000, 0), (20_000, 20_000), (0, 20_000)],
    )


def test_clicking_near_a_track_snaps_and_dispatches_move_stage_xy(qtbot):
    store = StateStore(AppState(mode=Mode.LIVE))
    effects = []
    store.on_effect(effects.append)
    worker = OverviewWorker(_DummyCam(), OverviewConfig(min_area_px=20, threshold=20, snap_dist_px=30))
    win = OverviewWindow(StateBridge(store), worker, stage_position=lambda: (5000.0, 5000.0),
                         initial_calibration=_calib())
    qtbot.addWidget(win)
    win.start_overview()
    qtbot.waitUntil(lambda: worker.latest() is not None and len(worker.latest().tracks) == 1,
                    timeout=3000)
    win.tick()
    win.click_at_pixel(88.0, 96.0)
    assert win.selected_track_id is not None
    assert effects[-1] == pytest.approx(X.MoveXYTo(x_um=8000.0, y_um=9000.0), abs=300.0)
    win.close()


def test_four_point_calibration_fits_and_saves_file(qtbot, tmp_path):
    store = StateStore(AppState())
    effects = []
    store.on_effect(effects.append)
    worker = OverviewWorker(_DummyCam(), OverviewConfig())
    stage_pos = [(0.0, 0.0)]
    cal_path = tmp_path / "overview_calibration.json"
    win = OverviewWindow(StateBridge(store), worker, stage_position=lambda: stage_pos[0],
                         calibration_path=cal_path)
    qtbot.addWidget(win)

    # Uncalibrated click does not move stage
    win.click_at_pixel(50.0, 50.0)
    assert effects == []

    win.calibrate_button.setChecked(True)
    for (u, v), (sx, sy) in (
        ((0.0, 0.0), (0.0, 0.0)),
        ((200.0, 0.0), (20_000.0, 0.0)),
        ((200.0, 200.0), (20_000.0, 20_000.0)),
        ((0.0, 200.0), (0.0, 20_000.0)),
    ):
        stage_pos[0] = (sx, sy)
        win.click_at_pixel(u, v)

    assert not win.calibrate_button.isChecked()
    assert win.calibration is not None and cal_path.exists()
    assert win.calibration.pixel_to_stage_um(100.0, 100.0) == pytest.approx((10_000.0, 10_000.0))
    win.close()
