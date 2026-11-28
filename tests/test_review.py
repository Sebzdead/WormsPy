"""wormspy.review: per-frame review data and real-time playback, from real recordings."""

import numpy as np
import pytest

from tests.test_reader import _record
from wormspy.reader import open_recording
from wormspy.review import PlaybackClock, ReviewData, compute_calcium_stats


@pytest.fixture
def data(tmp_path):
    rec = open_recording(_record(tmp_path, first=50, count=12, events={52: "glycerol", 58: "wash"},
                                 tracked={51, 52, 53}, drop_clock={56}))
    yield ReviewData(rec)
    rec.close()


def test_every_array_has_one_row_per_frame_by_position(data):
    assert len(data) == 12 and list(data.frame_index) == list(range(50, 62))
    assert data.fps == 10.0 and data.duration_s == pytest.approx(1.1)
    assert data.time_s == pytest.approx(np.arange(12) / 10)
    assert data.stage_um.shape == data.worm_um.shape == data.path_um.shape == (12, 2)
    assert data.position_of(55) == 5 and data.position_of(10) == 0 and data.position_of(99) == 11


def test_the_path_is_the_tracked_worm_where_known_else_the_stage(data):
    assert np.isfinite(data.worm_um[1:4]).all() and np.isnan(data.worm_um[4:]).all()
    assert tuple(data.path_um[2]) == (1052.0, 2000.0)          # tracker's worm position
    assert tuple(data.path_um[7]) == (1057.0, 2000.0)          # stage: no estimate there
    assert list(data.status[:5]) == ["", "tracking", "tracking", "tracking", ""]


def test_events_carry_their_position_time_and_place(data):
    labels = [(e.label, e.frame_index, e.position) for e in data.events]
    assert [label for label, *_ in labels] == ["glycerol", "wash"]
    first = data.events[0]
    assert first.time_s == pytest.approx(data.time_s[first.position])
    assert first.xy_um == tuple(data.path_um[first.position])
    assert data.next_event(0) is first and data.next_event(first.position) is data.events[1]
    assert data.previous_event(first.position) is None
    assert data.events_at(first.position) == ["glycerol"]


def test_dropped_frames_are_flagged_and_skipped_for_the_first_valid_frame(tmp_path):
    rec = open_recording(_record(tmp_path, drop_clock={50, 51}, drop_follower={50}))
    data = ReviewData(rec)
    assert list(np.flatnonzero(data.dropped)) == [0, 1] and data.first_valid == 2
    # frame 50 lost both cameras, so it has no capture time: it is extrapolated
    assert data.time_s == pytest.approx(np.arange(12) / 10)
    rec.close()


def test_overlays_are_measured_in_the_source_and_mapped_into_the_other_channel(data):
    overlays = data.overlays(2)
    assert overlays["brightfield"].point_px == (15.0, 10.0)
    assert not overlays["brightfield"].mapped
    expected = data.recording.calibration.map_px("brightfield", "gcamp", (15.0, 10.0))
    assert overlays["gcamp"].mapped and overlays["gcamp"].point_px == pytest.approx(expected)
    assert data.overlays(8) == {}                                 # not tracked then


def test_playback_follows_the_capture_times_and_skips_what_it_cannot_show(data):
    clock = PlaybackClock(data)
    clock.start(2, now=100.0)
    assert clock.position(100.0) == 2
    assert clock.position(100.35) == 5                  # 0.35 s later: frame 3.5 → the 5th
    clock.speed = 4.0
    clock.start(2, now=200.0)
    assert clock.position(200.1) == 6
    assert clock.position(260.0) == 11                  # clamped to the last frame


def test_compute_calcium_stats_returns_distribution_and_temporal_traces(data):
    stats = compute_calcium_stats(data.recording, data)
    assert stats is not None
    assert stats.channel == "gcamp"
    assert stats.sampled_frames == 11                   # 12 frames, 1 dropped
    assert stats.dropped_pct == pytest.approx(100.0 / 12.0)
    assert stats.median == pytest.approx(1055.0, abs=10.0)
    assert stats.p999 >= stats.median
    assert len(stats.sample_times_s) == 11
    assert len(stats.hist_log_counts) == 128


def test_compute_calcium_stats_handles_all_dropped_frames_without_warning(tmp_path):
    rec = open_recording(_record(tmp_path, first=0, count=3, drop_clock={0, 1, 2}))
    rd = ReviewData(rec)
    stats = compute_calcium_stats(rec, rd)
    assert stats is not None and stats.sampled_frames == 0
    assert stats.dropped_pct == 100.0
    rec.close()
