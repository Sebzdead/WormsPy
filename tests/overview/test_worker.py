"""OverviewWorker against a fake camera and SimOverviewCamera."""

import time

import cv2
import numpy as np
import pytest

from wormspy.config import OverviewConfig
from wormspy.core.cameras import Camera
from wormspy.core.frames import Frame
from wormspy.overview.worker import OverviewWorker
from wormspy.sim.render import ImageGeometry
from wormspy.sim.rig import ChannelSpec, SimRig
from wormspy.sim.stage import SimStage
from wormspy.sim.worm import SyntheticWorm


class _ScriptedOverviewCamera(Camera):
    def __init__(self):
        self._open = True
        self._idx = 0
        self.begun = False
        self.ended = False

    def begin(self):
        self.begun = True

    def end(self):
        self.ended = True

    def read(self):
        if not self._open or self._idx >= 4:
            return None
        img = np.full((120, 120), 200, np.uint8)
        if self._idx > 0:
            cv2.circle(img, (40 + self._idx * 4, 60), 6, 40, -1)
        fid = self._idx
        self._idx += 1
        return Frame(image=img, device_frame_id=fid, capture_ts=10.0 + fid)

    def is_open(self):
        return self._open

    def release(self):
        self._open = False


def test_worker_processes_frames_and_stops_cleanly():
    cam = _ScriptedOverviewCamera()
    worker = OverviewWorker(cam, OverviewConfig(min_area_px=20, threshold=20))
    worker.start()
    deadline = time.monotonic() + 3.0
    while (worker.latest() is None or not worker.latest().tracks) and time.monotonic() < deadline:
        time.sleep(0.01)
    frame = worker.latest()
    assert frame is not None and len(frame.tracks) == 1
    assert worker.find_closest(*frame.tracks[0].centroid) is not None
    worker.reset_background()
    worker.stop()
    assert cam.begun and cam.ended and not worker.is_running


def test_sim_overview_camera_renders_plate_and_exposes_calibration():
    from wormspy.sim.overview import SimOverviewCamera

    geom = ImageGeometry(48, 32, 30.0)
    safe = {"x": (0.0, 50_400.0), "y": (0.0, 50_400.0), "z": (0.0, 20_000.0)}
    stage = SimStage(safe, 2000.0, {"x": 25_200.0, "y": 25_200.0, "z": 5000.0})
    rig = SimRig(SyntheticWorm(seed=0, start_um=(25_200.0, 25_200.0)), stage,
                 ChannelSpec(geom, "fluorescence"), ChannelSpec(geom, "behaviour"), fps=10.0)
    cam = SimOverviewCamera(rig, safe, fps=20.0)
    cam.begin()
    frame = cam.read()
    assert frame is not None and frame.image.shape == (600, 600)
    calib = cam.sim_calibration()
    assert calib.pixel_to_stage_um(300.0, 300.0)[0] == pytest.approx(25_200.0, abs=1.0)
    cam.end()
    cam.release()
