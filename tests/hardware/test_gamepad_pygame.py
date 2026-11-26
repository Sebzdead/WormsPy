"""PygameGamepad against a fake pygame module (no SDL/hardware needed)."""

import os
import sys
from types import SimpleNamespace

from wormspy.hardware.gamepad_pygame import PygameGamepad


def _fake_pygame(monkeypatch, axes=(0.25, -0.5, 0.0, 0.75, 0.9), buttons=(False, True, False, False)):
    calls = []

    class FakeJoystick:
        def __init__(self, index):
            self._index = index

        def init(self):
            calls.append(("joystick_obj_init", self._index))

        def get_numaxes(self):
            return len(axes)

        def get_axis(self, i):
            return axes[i]

        def get_numbuttons(self):
            return len(buttons)

        def get_button(self, i):
            return buttons[i]

    fake = SimpleNamespace(
        display=SimpleNamespace(
            init=lambda: calls.append(("display_init", None)),
            quit=lambda: calls.append(("display_quit", None)),
        ),
        joystick=SimpleNamespace(
            init=lambda: calls.append(("joystick_init", None)),
            quit=lambda: calls.append(("joystick_quit", None)),
            get_count=lambda: 1,
            Joystick=FakeJoystick,
        ),
        event=SimpleNamespace(pump=lambda: calls.append(("pump", None))),
    )
    monkeypatch.setitem(sys.modules, "pygame", fake)
    return fake, calls


def test_init_sets_background_events_and_defers_sdl_init_to_poll(monkeypatch):
    monkeypatch.delenv("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", raising=False)
    _, calls = _fake_pygame(monkeypatch)
    pad = PygameGamepad()
    assert os.environ.get("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS") == "1"
    assert calls == []
    state = pad.poll()
    assert state is not None
    assert calls[:3] == [("display_init", None), ("joystick_init", None), ("pump", None)]
    pad.close()
    assert ("joystick_quit", None) in calls and ("display_quit", None) in calls


def test_poll_uses_custom_axis_and_button_indices(monkeypatch):
    _fake_pygame(monkeypatch, axes=(0.0, 0.1, 0.2, 0.3, -0.8), buttons=(False, False, False, True))
    pad = PygameGamepad(
        axes={"left_x": 0, "left_y": 1, "right_y": 4},
        buttons={"X": 3, "B": 1},
    )
    state = pad.poll()
    assert state.axes == {"left_x": 0.0, "left_y": 0.1, "right_y": -0.8}
    assert state.buttons == frozenset({"X"})
    pad.close()
