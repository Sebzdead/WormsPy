"""Simulated global-view overview camera for `--sim` and tests."""

import time

import cv2
import numpy as np

from wormspy.core.cameras import Camera
from wormspy.core.frames import Frame
from wormspy.overview.calibration import OverviewCalibration
from wormspy.sim.render import ImageGeometry
from wormspy.sim.rig import SimRig
from wormspy.sim.worm import SyntheticWorm


class SimOverviewCamera(Camera):
    """Renders the full 50.4 × 50.4 mm plate with multiple crawling worms."""

    def __init__(self, rig: SimRig, safe_range_um: dict[str, tuple[float, float]],
                 fps: float = 2.0, width_px: int = 600, height_px: int = 600,
                 um_per_px: float = 90.0) -> None:
        self._rig = rig
        self._fps = fps
        self._period_s = 1.0 / fps
        self._geometry = ImageGeometry(width_px=width_px, height_px=height_px,
                                       um_per_px=um_per_px)
        x_lo, x_hi = safe_range_um["x"]
        y_lo, y_hi = safe_range_um["y"]
        self._centre_um = ((x_lo + x_hi) / 2.0, (y_lo + y_hi) / 2.0)
        self._extra_worms = (
            SyntheticWorm(seed=11, start_um=(x_lo + 0.28 * (x_hi - x_lo),
                                             y_lo + 0.30 * (y_hi - y_lo)),
                          speed_um_s=220.0, length_um=1400.0),
            SyntheticWorm(seed=22, start_um=(x_lo + 0.72 * (x_hi - x_lo),
                                             y_lo + 0.35 * (y_hi - y_lo)),
                          speed_um_s=240.0, length_um=1400.0),
            SyntheticWorm(seed=33, start_um=(x_lo + 0.65 * (x_hi - x_lo),
                                             y_lo + 0.75 * (y_hi - y_lo)),
                          speed_um_s=200.0, length_um=1400.0),
        )
        self._open = True
        self._streaming = False
        self._frame_id = 0
        self._last_read = 0.0

    def begin(self) -> None:
        self._streaming = True
        self._last_read = 0.0

    def end(self) -> None:
        self._streaming = False

    def is_open(self) -> bool:
        return self._open

    def release(self) -> None:
        self._streaming = False
        self._open = False

    def sim_calibration(self) -> OverviewCalibration:
        h, w = self._geometry.height_px, self._geometry.width_px
        px = np.array([[50.0, 50.0], [w - 50.0, 50.0],
                       [w - 50.0, h - 50.0], [50.0, h - 50.0]], dtype=np.float64)
        um = self._geometry.px_to_world(px, self._centre_um)
        return OverviewCalibration.fit(px, um)

    def read(self) -> Frame | None:
        if not self._open or not self._streaming:
            return None
        now = time.monotonic()
        if self._last_read > 0.0 and (now - self._last_read) < self._period_s:
            return None
        dt = self._period_s if self._last_read == 0.0 else (now - self._last_read)
        self._last_read = now
        for worm in self._extra_worms:
            worm.step(dt)
        image = self._render()
        fid = self._frame_id
        self._frame_id += 1
        return Frame(image=image, device_frame_id=fid, capture_ts=now)

    def _render(self) -> np.ndarray:
        geom = self._geometry
        img = np.full((geom.height_px, geom.width_px), 210, dtype=np.uint8)
        for worm in (self._rig.worm, *self._extra_worms):
            px = geom.world_to_px(worm.points, self._centre_um)
            pts = np.rint(px * 16).astype(np.int32).reshape(-1, 1, 2)
            cv2.polylines(img, [pts], isClosed=False, color=40, thickness=4,
                          lineType=cv2.LINE_AA, shift=4)
        # subtle objective illumination spot at current stage XY for calibration practice
        sx, sy = self._rig.stage.position_um("x"), self._rig.stage.position_um("y")
        spot_px = geom.world_to_px(np.array([[sx, sy]], dtype=np.float64), self._centre_um)[0]
        cv2.circle(img, (round(spot_px[0]), round(spot_px[1])), 5, 245, -1)
        return img
