"""Background thread running the decoupled global-view (WormTraffic) camera."""

import threading
import time
from collections.abc import Callable

from wormspy.config import OverviewConfig
from wormspy.overview.tracker import OverviewFrame, OverviewProcessor

IDLE_SLEEP_S = 0.02


class OverviewWorker:
    def __init__(self, camera, config: OverviewConfig,
                 on_error: Callable[[str], None] | None = None,
                 on_recover: Callable[[], None] | None = None) -> None:
        self._camera = camera
        self._config = config
        self._processor = OverviewProcessor(config)
        self._on_error = on_error
        self._on_recover = on_recover
        self._lock = threading.Lock()
        self._latest: OverviewFrame | None = None
        self._reset_bg = False
        self._failing = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return
        self._stop.clear()
        self._failing = False
        begin = getattr(self._camera, "begin", None)
        if callable(begin):
            begin()
        self._thread = threading.Thread(target=self._run, name="overview", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        end = getattr(self._camera, "end", None)
        if callable(end):
            end()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        self._thread = None

    def reset_background(self) -> None:
        with self._lock:
            self._reset_bg = True

    def latest(self) -> OverviewFrame | None:
        with self._lock:
            return self._latest

    def find_closest(self, x: float, y: float) -> tuple[int, tuple[float, float]] | None:
        with self._lock:
            return self._processor.find_closest(x, y)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                frame = self._camera.read()
                if self._failing:
                    self._failing = False
                    if self._on_recover is not None:
                        self._on_recover()
            except Exception as exc:  # noqa: BLE001 - surface error, keep worker alive
                if not self._failing:
                    self._failing = True
                    if self._on_error is not None:
                        self._on_error(f"{type(exc).__name__}: {exc}")
                self._stop.wait(0.1)
                continue

            if frame is None:
                self._stop.wait(IDLE_SLEEP_S)
                continue

            with self._lock:
                if self._reset_bg:
                    self._processor.reset()
                    self._reset_bg = False
                ts = frame.capture_ts if frame.capture_ts > 0 else time.monotonic()
                self._latest = self._processor.process(frame.image, ts)
