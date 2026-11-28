"""pygame gamepad adapter. pygame is imported lazily (optional `gamepad` extra).

Index maps default to the v1 layout on the rig's controller: axes 0/1 = left stick, axis 3 =
right stick vertical (Z); buttons A=0, B=1, X=2, Y=3. Override them in rig.toml if a different
controller reports other indices. Verified manually on the rig, not in CI.
"""

import os
import threading

from wormspy.control.gamepad import Gamepad, GamepadState

DEFAULT_AXES = {"left_x": 0, "left_y": 1, "right_y": 3}
DEFAULT_BUTTONS = {"A": 0, "B": 1, "X": 2, "Y": 3}


class PygameGamepad(Gamepad):
    def __init__(self, index: int = 0, axes: dict[str, int] | None = None,
                 buttons: dict[str, int] | None = None) -> None:
        # On Windows, SDL drops joystick events when PySide6 owns the foreground window unless
        # background events are enabled before pygame/SDL initialises.
        os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
        import pygame
        self._pygame = pygame
        self._index = index
        self._axes = DEFAULT_AXES if axes is None else axes
        self._buttons = DEFAULT_BUTTONS if buttons is None else buttons
        self._initialized = False
        self._joystick = None
        self._reset_requested = threading.Event()

    def reset(self) -> None:
        self._reset_requested.set()

    def _ensure_init(self) -> None:
        if not self._initialized:
            self._pygame.display.init()
            self._pygame.joystick.init()
            self._initialized = True

    def poll(self) -> GamepadState | None:
        if self._reset_requested.is_set():
            self._reset_requested.clear()
            if self._initialized:
                self._pygame.joystick.quit()
                self._pygame.joystick.init()
            self._joystick = None
        self._ensure_init()
        pg = self._pygame
        pg.event.pump()
        get_events = getattr(pg.event, "get", None)
        added = getattr(pg, "JOYDEVICEADDED", None)
        removed = getattr(pg, "JOYDEVICEREMOVED", None)
        if (callable(get_events) and added is not None and removed is not None
                and get_events([added, removed])):
            self._joystick = None
        if self._joystick is not None:
            get_init = getattr(self._joystick, "get_init", None)
            if callable(get_init) and not get_init():
                self._joystick = None
        if pg.joystick.get_count() <= self._index:
            self._joystick = None
            return None
        if self._joystick is None:
            self._joystick = pg.joystick.Joystick(self._index)
            self._joystick.init()
        js = self._joystick
        axes = {name: js.get_axis(i) for name, i in self._axes.items() if i < js.get_numaxes()}
        pressed = frozenset(name for name, i in self._buttons.items()
                            if i < js.get_numbuttons() and js.get_button(i))
        return GamepadState(axes=axes, buttons=pressed)

    def close(self) -> None:
        if self._initialized:
            self._pygame.joystick.quit()
            self._pygame.display.quit()
            self._initialized = False
            self._joystick = None
