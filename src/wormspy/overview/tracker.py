"""WormTraffic multi-worm detector and tracker (ported from Tracker/src/).

Background subtraction via running average, morphological cleanup, connected-component
centroids, and Hungarian (Kuhn-Munkres) track association in pure NumPy.
"""

from collections import deque
from dataclasses import dataclass

import cv2
import numpy as np

from wormspy.config import OverviewConfig


def ensure_gray_u8(image: np.ndarray) -> np.ndarray:
    """Convert BGR/mono or uint16/float overview frames into a contiguous 2D uint8 array."""
    arr = np.asarray(image)
    if arr.ndim == 3 and arr.shape[2] >= 3:
        arr = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_BGR2GRAY)
    elif arr.ndim == 3:
        arr = arr[:, :, 0]
    if arr.dtype == np.uint8:
        return arr
    if arr.dtype == np.uint16:
        lo, hi = np.percentile(arr, (1, 99))
        if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
            return np.zeros(arr.shape, dtype=np.uint8)
        return np.clip((arr - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)
    lo = float(np.nanmin(arr))
    hi = float(np.nanmax(arr))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return np.zeros(arr.shape, dtype=np.uint8)
    return np.clip((arr - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)


class RunningAverageBG:
    """Running-average background model for slow-moving overview scenes."""

    def __init__(self, alpha: float = 0.02) -> None:
        self.alpha = float(alpha)
        self.bg: np.ndarray | None = None

    def reset(self) -> None:
        self.bg = None

    def apply(self, frame_gray: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        gray = ensure_gray_u8(frame_gray).astype(np.float32)
        if self.bg is None or self.bg.shape != gray.shape:
            self.bg = gray.copy()
        self.bg = (1.0 - self.alpha) * self.bg + self.alpha * gray
        fg = cv2.absdiff(gray, self.bg).astype(np.float32)
        return fg, self.bg


def threshold_and_clean(fg: np.ndarray, thresh: int = 20, ksize: int = 3,
                        iters: int = 1) -> np.ndarray:
    fg8 = cv2.convertScaleAbs(fg)
    _, mask = cv2.threshold(fg8, thresh, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=iters)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=iters)
    return mask


@dataclass(frozen=True)
class DetectedObject:
    bbox: tuple[int, int, int, int]
    area: int
    centroid: tuple[float, float]


def connected_components(mask: np.ndarray, min_area: int = 50) -> list[DetectedObject]:
    num_labels, _labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    objects: list[DetectedObject] = []
    for idx in range(1, num_labels):
        x, y, w, h, area = stats[idx]
        if int(area) >= min_area:
            cx, cy = centroids[idx]
            objects.append(DetectedObject(
                bbox=(int(x), int(y), int(w), int(h)),
                area=int(area),
                centroid=(float(cx), float(cy)),
            ))
    return objects


def linear_sum_assignment(cost_matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Exact minimum-weight bipartite assignment (Jonker-Volgenant / Hungarian, pure NumPy)."""
    cost = np.asarray(cost_matrix, dtype=np.float64)
    if cost.ndim != 2:
        raise ValueError(f"expected 2D cost matrix, got {cost.ndim}D")
    n_rows, n_cols = cost.shape
    if n_rows == 0 or n_cols == 0:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)

    transposed = False
    if n_rows > n_cols:
        cost = cost.T
        n_rows, n_cols = cost.shape
        transposed = True

    u = np.zeros(n_rows + 1, dtype=np.float64)
    v = np.zeros(n_cols + 1, dtype=np.float64)
    p = np.zeros(n_cols + 1, dtype=np.int64)
    way = np.zeros(n_cols + 1, dtype=np.int64)

    for i in range(1, n_rows + 1):
        p[0] = i
        j0 = 0
        minv = np.full(n_cols + 1, np.inf, dtype=np.float64)
        used = np.zeros(n_cols + 1, dtype=bool)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = np.inf
            j1 = 0
            row_cost = cost[i0 - 1]
            for j in range(1, n_cols + 1):
                if not used[j]:
                    cur = row_cost[j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(n_cols + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    row_ind = np.empty(n_rows, dtype=np.int64)
    col_ind = np.empty(n_rows, dtype=np.int64)
    k = 0
    for j in range(1, n_cols + 1):
        if p[j] > 0:
            row_ind[k] = p[j] - 1
            col_ind[k] = j - 1
            k += 1

    if transposed:
        row_ind, col_ind = col_ind, row_ind
    order = np.argsort(row_ind)
    return row_ind[order], col_ind[order]


@dataclass(frozen=True)
class TrackSnapshot:
    id: int
    centroid: tuple[float, float]
    trace: tuple[tuple[float, float], ...]


class _Track:
    def __init__(self, tid: int, centroid: tuple[float, float], max_trace: int) -> None:
        self.id = tid
        self.centroid = centroid
        self.trace: deque[tuple[float, float]] = deque([centroid], maxlen=max_trace)
        self.missed = 0

    def update(self, centroid: tuple[float, float]) -> None:
        self.centroid = centroid
        self.trace.append(centroid)
        self.missed = 0


class MultiTracker:
    """Nearest-neighbor Hungarian multi-object tracker."""

    def __init__(self, max_missed: int = 3, max_dist: float = 60.0,
                 max_trace: int = 300) -> None:
        self.max_missed = int(max_missed)
        self.max_dist = float(max_dist)
        self._max_trace = int(max_trace)
        self._tracks: dict[int, _Track] = {}
        self._next_id = 1

    def reset(self) -> None:
        self._tracks.clear()
        self._next_id = 1

    def step(self, detections: list[tuple[float, float]]) -> None:
        if not self._tracks:
            for det in detections:
                self._spawn(det)
            return

        track_ids = list(self._tracks)
        if not detections:
            for tid in track_ids:
                self._tracks[tid].missed += 1
            self._prune()
            return

        track_cs = np.array([self._tracks[tid].centroid for tid in track_ids], dtype=np.float64)
        det_cs = np.array(detections, dtype=np.float64)
        dists = np.linalg.norm(track_cs[:, None, :] - det_cs[None, :, :], axis=2)
        rows, cols = linear_sum_assignment(dists)

        assigned_tracks: set[int] = set()
        assigned_dets: set[int] = set()
        for r, c in zip(rows, cols, strict=True):
            if dists[r, c] <= self.max_dist:
                tid = track_ids[r]
                self._tracks[tid].update((float(det_cs[c, 0]), float(det_cs[c, 1])))
                assigned_tracks.add(int(r))
                assigned_dets.add(int(c))

        for r, tid in enumerate(track_ids):
            if r not in assigned_tracks:
                self._tracks[tid].missed += 1
        for c, det in enumerate(detections):
            if c not in assigned_dets:
                self._spawn(det)
        self._prune()

    def snapshots(self) -> tuple[TrackSnapshot, ...]:
        return tuple(
            TrackSnapshot(id=tr.id, centroid=tr.centroid, trace=tuple(tr.trace))
            for tr in self._tracks.values()
        )

    def find_closest(self, x: float, y: float,
                     max_dist_px: float = 50.0) -> tuple[int, tuple[float, float]] | None:
        best: tuple[int, tuple[float, float]] | None = None
        best_d2 = max_dist_px * max_dist_px
        for tid, tr in self._tracks.items():
            tx, ty = tr.centroid
            d2 = (tx - x) ** 2 + (ty - y) ** 2
            if d2 <= best_d2:
                best_d2 = d2
                best = (tid, (tx, ty))
        return best

    def _spawn(self, centroid: tuple[float, float]) -> None:
        tid = self._next_id
        self._next_id += 1
        self._tracks[tid] = _Track(tid, (float(centroid[0]), float(centroid[1])), self._max_trace)

    def _prune(self) -> None:
        for tid in [tid for tid, tr in self._tracks.items() if tr.missed > self.max_missed]:
            del self._tracks[tid]


@dataclass(frozen=True)
class OverviewFrame:
    image_u8: np.ndarray
    objects: tuple[DetectedObject, ...]
    tracks: tuple[TrackSnapshot, ...]
    timestamp: float
    fps: float


class OverviewProcessor:
    """Runs background subtraction + connected components + MultiTracker on one overview frame."""

    def __init__(self, config: OverviewConfig) -> None:
        self._config = config
        self._bg = RunningAverageBG(alpha=config.alpha)
        self._tracker = MultiTracker(max_missed=config.max_missed, max_dist=config.max_dist_px)
        self._last_ts: float | None = None
        self._fps = 0.0

    def reset(self) -> None:
        self._bg.reset()
        self._tracker.reset()

    def process(self, image: np.ndarray, ts: float) -> OverviewFrame:
        gray = ensure_gray_u8(image)
        fg, _ = self._bg.apply(gray)
        mask = threshold_and_clean(fg, thresh=self._config.threshold)
        objects = connected_components(mask, min_area=self._config.min_area_px)
        self._tracker.step([obj.centroid for obj in objects])
        if self._last_ts is not None and ts > self._last_ts:
            inst = 1.0 / (ts - self._last_ts)
            self._fps = inst if self._fps == 0.0 else 0.7 * self._fps + 0.3 * inst
        self._last_ts = ts
        return OverviewFrame(
            image_u8=gray,
            objects=tuple(objects),
            tracks=self._tracker.snapshots(),
            timestamp=ts,
            fps=self._fps,
        )

    def find_closest(self, x: float, y: float) -> tuple[int, tuple[float, float]] | None:
        return self._tracker.find_closest(x, y, max_dist_px=self._config.snap_dist_px)
