from __future__ import annotations
import cv2
import os
from typing import Optional


class Camera:
    """
    Fake camera that reads frames from a video file and exposes a Webcam-like API.

    Usage:
        cam = Camera(video_path="demo.mp4", width=640, height=480, loop=True, sample_every_n=1)
        frame = cam.read()  # returns a BGR uint8 frame (resized if width/height provided)
        cam.release()
    """

    def __init__(
        self,
        device: int = 0,                       # kept for drop-in compatibility; ignored
        width: Optional[int] = None,
        height: Optional[int] = None,
        *,
        video_path: Optional[str] = None,
        loop: bool = True,
        sample_every_n: int = 1,               # read every Nth frame (>=1)
    ):
        """
        Parameters
        ----------
        device : int
            Ignored, kept only for compatibility with real Camera signature.
        width, height : Optional[int]
            If provided, output frames are resized to (width, height).
        video_path : str
            Path to the input video file.
        loop : bool
            When reaching EOF, restart from the beginning if True; else raise RuntimeError.
        sample_every_n : int
            Read one frame every N frames in the file; useful to thin high-FPS sources.
        """
        if video_path is None:
            raise ValueError("capture_fake.Camera requires `video_path`.")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        self.width = int(width) if width else None
        self.height = int(height) if height else None
        self.loop = bool(loop)
        self.sample_every_n = max(1, int(sample_every_n))
        self._skip_counter = 0
        self._video_path = video_path

    def _restart(self):
        """Restart the video to the first frame."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def read(self):
        """Read one frame. On EOF: loop or raise."""
        # Skip frames if thinning
        if self.sample_every_n > 1 and self._skip_counter > 0:
            # fast-forward by grabbing frames without decoding (if available)
            for _ in range(self._skip_counter):
                ok = self.cap.grab()
                if not ok:
                    # EOF during skip path
                    if self.loop:
                        self._restart()
                        continue
                    raise RuntimeError("End of video (during skip).")
            self._skip_counter = 0

        ok, frame = self.cap.read()

        if not ok:
            # EOF
            if self.loop:
                self._restart()
                ok, frame = self.cap.read()
                if not ok:
                    raise RuntimeError("Failed to read frame after restart.")
            else:
                raise RuntimeError("End of video.")

        # Optional resize to requested output size
        if self.width is not None and self.height is not None:
            frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)

        # Prepare skip counter for next call
        self._skip_counter = self.sample_every_n - 1

        # Ensure BGR uint8 (VideoCapture typically returns that already)
        if frame.dtype != 'uint8':
            frame = cv2.convertScaleAbs(frame)

        return frame

    def release(self):
        try:
            self.cap.release()
        except Exception:
            pass
