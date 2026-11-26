"""AcquisitionLoop: the single reader of both cameras (ADR 0006).

Each step reads one frame from each camera, publishes it to the FrameHub under its channel name
(display and tracking read the latest frame there, never slowing acquisition), and feeds the
FramePairer. Every completed pair goes to `on_pair` (the recorder, when recording). Camera
reads may block (real hardware, with a timeout) or return None at once (simulated cameras). A
camera error ends the thread and is reported through `on_failure`.
"""

import threading
import time
from collections.abc import Callable

from wormspy.acquisition.pairing import FramePair, FramePairer
from wormspy.core.cameras import Camera
from wormspy.core.frames import Frame, FrameHub

IDLE_SLEEP_S = 0.001


class AcquisitionLoop:
    def __init__(self, clock: Camera, follower: Camera, clock_name: str, follower_name: str,
                 hub: FrameHub, on_pair: Callable[[FramePair], None],
                 on_failure: Callable[[str], None] | None = None,
                 pairer: FramePairer | None = None) -> None:
        self._clock, self._follower = clock, follower
        self._clock_name, self._follower_name = clock_name, follower_name
        self._hub = hub
        self._on_pair = on_pair
        self._on_failure = on_failure
        self._pairer = FramePairer() if pairer is None else pairer
        self._lock = threading.Lock()
        self._failed = False
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    def step(self) -> int:
        """Read at most one frame per camera; returns how many frames were read."""
        read = 0
        if self._read_one(self._clock, self._clock_name, self._pairer.add_clock):
            read += 1
        if self._read_one(self._follower, self._follower_name, self._pairer.add_follower):
            read += 1
        return read

    def _read_one(self, camera: Camera, name: str,
                  add_fn: Callable[[Frame], list[FramePair]]) -> bool:
        frame = camera.read()
        if frame is None:
            return False
        self._hub.publish(name, frame)
        with self._lock:
            self._emit(add_fn(frame))
        return True

    def index_of(self, device_frame_id: int) -> int | None:
        with self._lock:
            return self._pairer.index_of(device_frame_id)

    def flush(self) -> None:
        """Resolve everything seen so far; frames still missing count as dropped."""
        with self._lock:
            self._emit(self._pairer.flush())

    def start(self) -> None:
        self._stop.clear()
        self._failed = False
        self._threads = [
            threading.Thread(target=self._run_camera,
                             args=(self._clock, self._clock_name, self._pairer.add_clock),
                             name="acquisition-clock", daemon=True),
            threading.Thread(target=self._run_camera,
                             args=(self._follower, self._follower_name,
                                   self._pairer.add_follower),
                             name="acquisition-follower", daemon=True),
        ]
        for thread in self._threads:
            thread.start()

    def stop(self) -> None:
        self._stop.set()
        me = threading.current_thread()
        for thread in self._threads:
            if thread is not me:
                thread.join()
        self._threads.clear()
        self.flush()

    def _run_camera(self, camera: Camera, name: str,
                    add_fn: Callable[[Frame], list[FramePair]]) -> None:
        while not self._stop.is_set():
            try:
                if not self._read_one(camera, name, add_fn):
                    time.sleep(IDLE_SLEEP_S)
            except Exception as exc:      # noqa: BLE001 - any camera error ends acquisition
                self._stop.set()
                with self._lock:
                    already_failed = self._failed
                    self._failed = True
                if not already_failed and self._on_failure is not None:
                    self._on_failure(f"{type(exc).__name__}: {exc}")
                return

    def _emit(self, pairs: list[FramePair]) -> None:
        for pair in pairs:
            self._on_pair(pair)
