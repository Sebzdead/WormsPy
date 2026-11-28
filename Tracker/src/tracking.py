from __future__ import annotations
import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import Dict, Tuple, List

class Track:
    def __init__(self, tid: int, centroid: Tuple[float,float], t: float):
        self.id = tid
        self.centroid = centroid
        self.trace = [(t, centroid[0], centroid[1])]
        self.missed = 0

    def update(self, centroid, t):
        self.centroid = centroid
        self.trace.append((t, centroid[0], centroid[1]))
        self.missed = 0

class MultiTracker:
    """最近邻 + 匈牙利匹配的简易多目标跟踪。"""
    def __init__(self, max_missed=3, max_dist=60.0):
        self.max_missed = int(max_missed)
        self.max_dist = float(max_dist)
        self.tracks: Dict[int, Track] = {}
        self._next_id = 1

    def step(self, detections: List[Tuple[float,float]], t: float):
        if len(self.tracks) == 0:
            for c in detections:
                self._spawn(c, t)
            return

        track_ids = list(self.tracks.keys())
        track_cs = np.array([self.tracks[tid].centroid for tid in track_ids], dtype=np.float32)
        det_cs   = np.array(detections, dtype=np.float32) if len(detections) else np.zeros((0,2), np.float32)

        if len(det_cs) == 0:
            for tid in track_ids:
                self.tracks[tid].missed += 1
            self._prune()
            return

        dists = np.linalg.norm(track_cs[:,None,:] - det_cs[None,:,:], axis=2)
        r, c = linear_sum_assignment(dists)

        assigned_tracks, assigned_dets = set(), set()
        for ri, ci in zip(r, c):
            if dists[ri, ci] <= self.max_dist:
                tid = track_ids[ri]
                self.tracks[tid].update(tuple(det_cs[ci]), t)
                assigned_tracks.add(ri)
                assigned_dets.add(ci)

        for ri, tid in enumerate(track_ids):
            if ri not in assigned_tracks:
                self.tracks[tid].missed += 1

        for ci, det in enumerate(det_cs):
            if ci not in assigned_dets:
                self._spawn(tuple(det), t)

        self._prune()

    def _spawn(self, centroid, t):
        tid = self._next_id
        self._next_id += 1
        self.tracks[tid] = Track(tid, centroid, t)

    def _prune(self):
        for tid in [tid for tid, tr in self.tracks.items() if tr.missed > self.max_missed]:
            del self.tracks[tid]

    def export_csv_rows(self):
        rows = []
        for tid, tr in sorted(self.tracks.items()):
            for (t, x, y) in tr.trace:
                rows.append((t, tid, x, y))
        return rows
