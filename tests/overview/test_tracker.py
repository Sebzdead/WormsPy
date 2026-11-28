"""WormTraffic overview tracker: Hungarian assignment, BG subtraction, MultiTracker."""

import itertools

import cv2
import numpy as np
import pytest

from wormspy.config import OverviewConfig
from wormspy.overview.tracker import (
    MultiTracker,
    OverviewProcessor,
    RunningAverageBG,
    connected_components,
    linear_sum_assignment,
    threshold_and_clean,
)


def _brute_force_min_cost(cost: np.ndarray) -> float:
    n_rows, n_cols = cost.shape
    if n_rows <= n_cols:
        return min(
            sum(cost[r, c] for r, c in enumerate(cols))
            for cols in itertools.permutations(range(n_cols), n_rows)
        )
    return min(
        sum(cost[r, c] for c, r in enumerate(rows))
        for rows in itertools.permutations(range(n_rows), n_cols)
    )


def test_linear_sum_assignment_matches_brute_force_on_rectangular_matrices():
    rng = np.random.default_rng(7)
    for shape in ((0, 0), (0, 3), (3, 0), (3, 3), (3, 5), (5, 3), (4, 4)):
        cost = rng.uniform(0.0, 100.0, size=shape)
        r_ind, c_ind = linear_sum_assignment(cost)
        assert len(r_ind) == len(c_ind) == min(shape)
        if min(shape) > 0:
            assert len(set(r_ind)) == len(r_ind)
            assert len(set(c_ind)) == len(c_ind)
            assert float(cost[r_ind, c_ind].sum()) == pytest.approx(_brute_force_min_cost(cost))


def test_multi_tracker_follows_moving_worms_prunes_lost_and_snaps_to_closest():
    bg = RunningAverageBG(alpha=0.02)
    tracker = MultiTracker(max_missed=2, max_dist=30.0)
    blank = np.full((120, 120), 200, np.uint8)
    bg.apply(blank)

    for step in range(5):
        img = blank.copy()
        cv2.circle(img, (20 + step * 5, 30), 5, 40, -1)
        cv2.circle(img, (90, 80 - step * 4), 5, 40, -1)
        fg, _ = bg.apply(img)
        mask = threshold_and_clean(fg, thresh=25)
        objs = connected_components(mask, min_area=20)
        tracker.step([o.centroid for o in objs])

    snaps = tracker.snapshots()
    assert len(snaps) == 2
    hit = tracker.find_closest(41.0, 31.0, max_dist_px=15.0)
    assert hit is not None and hit[1] == pytest.approx((40.0, 30.0), abs=2.0)
    assert tracker.find_closest(0.0, 0.0, max_dist_px=10.0) is None

    for _ in range(3):
        tracker.step([])
    assert tracker.snapshots() == ()


def test_overview_processor_handles_uint16_and_computes_fps():
    proc = OverviewProcessor(OverviewConfig(min_area_px=20, threshold=20))
    frame0 = np.full((100, 100), 1000, dtype=np.uint16)
    out0 = proc.process(frame0, ts=1.0)
    assert out0.image_u8.dtype == np.uint8
    frame1 = frame0.copy()
    cv2.circle(frame1, (50, 50), 6, 40000, -1)
    out1 = proc.process(frame1, ts=2.0)
    assert out1.fps == pytest.approx(1.0)
    assert len(out1.tracks) == 1
