"""ReviewWindow: both channels, the position plot and the scrub bar stay frame-synced."""

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt

from tests.test_reader import _record
from wormspy.ui.review_window import ReviewWindow, recordings_near


@pytest.fixture
def recording(tmp_path):
    return _record(tmp_path, first=50, count=12, events={52: "glycerol", 58: "wash"},
                   tracked={51, 52, 53}, drop_follower={57})


@pytest.fixture
def window(qtbot, recording):
    window = ReviewWindow()
    qtbot.addWidget(window)
    window.resize(1400, 800)
    window.open_path(recording.parent)                  # a session folder: opens rec-001
    window.show()
    qtbot.waitExposed(window)
    return window


def _shown(window, channel):
    view = next(v for v in window.views if v.channel == channel)
    return int(view.image[0, 0])


def test_the_channels_open_behaviour_left_fluorescence_right(window):
    assert [v.channel for v in window.views] == ["brightfield", "gcamp"]
    assert window.recording_box.currentText() == "rec-001"
    assert "N2 #3" in window.info_label.text() and "12 frames" in window.info_label.text()
    assert window.position == 0


def test_seeking_shows_the_same_frame_everywhere(window):
    window.seek(5)                                       # frame_index 55
    assert _shown(window, "gcamp") == 1055               # the pixels encode the frame index
    assert _shown(window, "brightfield") == 56
    assert window.scrub_bar.playhead.value() == pytest.approx(0.5)
    marker = window.plot.current_marker.data[0]
    assert (marker["x"], marker["y"]) == (1055.0, 2000.0)
    assert "frame     55" in window.readout.text()


def test_the_tracked_point_is_drawn_where_it_was_tracked(window):
    window.seek(2)
    views = {v.channel: v for v in window.views}
    assert views["brightfield"].tracked_point == (15.0, 10.0)
    assert views["gcamp"].tracked_point is not None       # mapped through registration
    window.seek(8)
    assert views["brightfield"].tracked_point is None


def test_events_are_labelled_on_the_plot_and_the_scrub_bar_and_can_be_jumped_to(window):
    assert window.plot.labels == ["glycerol", "wash"]
    assert [line.label.format for line in window.scrub_bar.event_lines] == ["glycerol", "wash"]
    window.next_event()
    assert window.data.frame_index[window.position] >= 52
    assert window.event_chip.isVisibleTo(window) and window.event_chip.text() == "GLYCEROL"
    window.next_event()
    window.previous_event()
    assert window.event_chip.text() == "GLYCEROL"


def test_a_dropped_frame_is_flagged(window):
    window.seek(7)
    assert window.dropped_chip.isVisibleTo(window)
    assert _shown(window, "brightfield") == 0            # the zero-filled placeholder
    window.step(1)
    assert not window.dropped_chip.isVisibleTo(window)


def test_clicking_the_scrub_bar_moves_every_source(window, qtbot):
    bar = window.scrub_bar
    box = bar.getPlotItem().getViewBox()
    x = bar.mapFromScene(box.mapViewToScene(QPointF(0.85, 0.5)))
    qtbot.mouseClick(bar.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(x.x(), x.y()))
    qtbot.waitUntil(lambda: window.position == 8)
    assert _shown(window, "gcamp") == 1058


def test_playback_runs_in_real_time_and_stops_at_the_end(window, monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("wormspy.ui.review_window.time.monotonic", lambda: now[0])
    window.seek(1)
    window.play()
    assert window.playing
    now[0] += 0.3
    window._play_tick()
    assert window.position == 4
    window.set_speed(4.0)
    now[0] += 10
    window._play_tick()
    assert window.position == 11 and not window.playing
    window.play()                                        # at the end: plays from the start
    assert window.position == 0 and window.playing
    window.pause()


def test_keyboard_steps_frames_and_seconds(window, qtbot):
    qtbot.keyClick(window, Qt.Key.Key_Right)
    assert window.position == 1
    qtbot.keyClick(window, Qt.Key.Key_Right, Qt.KeyboardModifier.ShiftModifier)
    assert window.position == 11                         # 1 s later (clamped at the end)
    qtbot.keyClick(window, Qt.Key.Key_Home)
    assert window.position == 0


def test_recordings_near_a_recording_or_session_folder(recording, tmp_path):
    assert recordings_near(recording) == ([recording], recording)
    assert recordings_near(recording.parent) == ([recording], recording)
    with pytest.raises(FileNotFoundError, match="no WormsPy recordings"):
        recordings_near(tmp_path)

