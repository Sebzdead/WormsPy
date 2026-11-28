"""What the review window shows for a finished recording, frame by frame, without Qt.

`ReviewData` turns a `wormspy.reader.Recording` into per-frame arrays, all indexed by
**position** (0 … N−1, row *i* of frames.csv; `frame_index − first_frame_index`):

- `time_s`: seconds since the first frame, from the capture times (gaps interpolated);
- `stage_um`: the stage position at each frame;
- `worm_um`: the worm's plate position from accepted tracker estimates (NaN where the tracker
  found nothing, was rejected, or skipped the frame);
- `path_um`: the worm where it is known, else the stage, which the tracker keeps on the worm;
- `status`, `dropped`, `events`: tracking state, zero-filled frames and event markers;
- `overlays(position)`: the tracked point in each channel's pixels, as in the live view.

`PlaybackClock` plays back in real time by the recorded capture times: a display that can't
keep up skips frames instead of falling behind.
"""

from contextlib import suppress
from dataclasses import dataclass

import numpy as np
import pandas as pd

from wormspy.reader import Recording

DEFAULT_FPS = 10.0


@dataclass(frozen=True)
class Event:
    position: int
    frame_index: int
    label: str
    time_s: float
    xy_um: tuple[float, float]


@dataclass(frozen=True)
class Overlay:
    point_px: tuple[float, float]
    mapped: bool                    # True: another camera's target, mapped by registration


class ReviewData:
    def __init__(self, recording: Recording) -> None:
        self.recording = recording
        frames = recording.frames
        self.frame_index = frames.index.to_numpy(dtype=int)
        n = len(self.frame_index)
        self.time_s = _times(frames["host_time"].to_numpy(dtype=float) if n else np.empty(0),
                             recording.fps)
        self.fps = float(recording.fps or _fps(self.time_s))
        self.stage_um = np.column_stack([_column(frames, "x_um"), _column(frames, "y_um")])
        accepted = _column(frames, "track_accepted") == 1
        worm = np.column_stack([_column(frames, "track_worm_x_um"),
                                _column(frames, "track_worm_y_um")])
        worm[~accepted] = np.nan
        traj_csv = recording.path / "analysis" / "tierpsy" / "trajectory.csv"
        if traj_csv.exists():
            with suppress(OSError, ValueError, KeyError):
                traj = pd.read_csv(traj_csv).set_index("frame_index")
                if {"worm_x_um", "worm_y_um"} <= set(traj.columns):
                    aligned = traj.reindex(recording.index)
                    recon = np.column_stack([
                        aligned["worm_x_um"].to_numpy(dtype=float),
                        aligned["worm_y_um"].to_numpy(dtype=float),
                    ])
                    missing = ~np.isfinite(worm).all(axis=1) & np.isfinite(recon).all(axis=1)
                    worm[missing] = recon[missing]
        self.worm_um = worm
        known = np.isfinite(worm).all(axis=1)
        self.path_um = np.where(known[:, None], worm, self.stage_um)
        self.status = (frames["track_status"].fillna("").astype(str).to_numpy()
                       if "track_status" in frames else np.full(n, "", dtype=object))
        self.dropped = (~recording.valid).to_numpy(dtype=bool)
        self.channels = list(recording.channels)
        self._calibration = recording.calibration
        self.events = [self._event(frame_index, label)
                       for frame_index, label in recording.events
                       if n and self.frame_index[0] <= frame_index <= self.frame_index[-1]]

    def __len__(self) -> int:
        return len(self.frame_index)

    @property
    def duration_s(self) -> float:
        return float(self.time_s[-1]) if len(self) else 0.0

    @property
    def first_valid(self) -> int:
        """The first position with a real image in every channel (0 if there is none)."""
        valid = np.flatnonzero(~self.dropped)
        return int(valid[0]) if len(valid) else 0

    def clamp(self, position: int) -> int:
        return int(min(max(int(position), 0), max(len(self) - 1, 0)))

    def position_of(self, frame_index: int) -> int:
        return self.clamp(int(frame_index) - int(self.frame_index[0]))

    def position_at(self, time_s: float) -> int:
        """The frame shown at `time_s`: the last one captured at or before it (to within a
        microsecond, so float rounding in the capture times never shows the previous frame)."""
        return self.clamp(int(np.searchsorted(self.time_s, time_s + 1e-6, side="right")) - 1)

    def next_event(self, position: int) -> Event | None:
        return next((e for e in self.events if e.position > position), None)

    def previous_event(self, position: int) -> Event | None:
        return next((e for e in reversed(self.events) if e.position < position), None)

    def events_at(self, position: int) -> list[str]:
        return [e.label for e in self.events if e.position == position]

    def overlays(self, position: int) -> dict[str, Overlay]:
        """The tracked point in each channel at this frame: measured in the tracker's source
        channel, and mapped into the others once the cameras are registered."""
        row = self.recording.frames.iloc[position]
        source = row.get("track_source_channel")
        x, y = row.get("track_target_px_x", np.nan), row.get("track_target_px_y", np.nan)
        if not isinstance(source, str) or not np.isfinite([x, y]).all():
            return {}
        overlays = {source: Overlay((float(x), float(y)), mapped=False)}
        if self._calibration is not None:
            for channel in self.channels:
                if channel == source:
                    continue
                mapped = self._calibration.map_px(source, channel, (x, y))
                if mapped is not None:
                    overlays[channel] = Overlay(mapped, mapped=True)
        return overlays

    def _event(self, frame_index: int, label: str) -> Event:
        position = self.position_of(frame_index)
        x, y = self.path_um[position]
        return Event(position, int(frame_index), label, float(self.time_s[position]),
                     (float(x), float(y)))


class PlaybackClock:
    """Which position to show at a given wall-clock time, playing at `speed` × real time."""

    def __init__(self, data: ReviewData, speed: float = 1.0) -> None:
        self._data = data
        self.speed = speed
        self._start_time = 0.0
        self._start_wall = 0.0

    def start(self, position: int, now: float) -> None:
        self._start_time = float(self._data.time_s[position])
        self._start_wall = now

    def position(self, now: float) -> int:
        return self._data.position_at(self._start_time + (now - self._start_wall) * self.speed)


def _column(frames, name: str) -> np.ndarray:
    if name not in frames:
        return np.full(len(frames), np.nan)
    return frames[name].to_numpy(dtype=float)


def _times(host_time: np.ndarray, fps: float | None) -> np.ndarray:
    """Seconds since the first frame. Rows whose capture time is missing (both cameras dropped)
    are interpolated; without any capture times, the nominal frame rate is used."""
    n = len(host_time)
    known = np.flatnonzero(np.isfinite(host_time))
    if len(known) < 2:
        return np.arange(n) / (fps or DEFAULT_FPS)
    filled = np.interp(np.arange(n), known, host_time[known])
    # extrapolate past the first/last known capture time at the measured rate
    period = (host_time[known[-1]] - host_time[known[0]]) / (known[-1] - known[0])
    filled[: known[0]] = host_time[known[0]] - (known[0] - np.arange(known[0])) * period
    after = np.arange(known[-1] + 1, n)
    filled[after] = host_time[known[-1]] + (after - known[-1]) * period
    return filled - filled[0]


def _fps(time_s: np.ndarray) -> float:
    if len(time_s) < 2 or time_s[-1] <= 0:
        return DEFAULT_FPS
    return (len(time_s) - 1) / time_s[-1]


@dataclass(frozen=True)
class CalciumStats:
    channel: str
    hist_edges: np.ndarray
    hist_log_counts: np.ndarray
    sample_times_s: np.ndarray
    sample_median: np.ndarray
    sample_p999: np.ndarray
    median: float
    p999: float
    max_val: float
    snr_proxy: float
    saturated_pct: float
    z_moved_pct: float
    dropped_pct: float
    dtype_max: float
    sampled_frames: int


def compute_calcium_stats(
    recording: Recording,
    data: ReviewData,
    channel: str | None = None,
    max_samples: int = 120,
    bins: int = 128,
) -> CalciumStats | None:
    """Compute fast sampled pixel-intensity distribution and temporal stats for fluorescence."""
    if channel is None:
        fluo = [name for name, ch in recording.channels.items() if ch.role == "fluorescence"]
        if not fluo:
            return None
        ref = recording.calibration.reference if recording.calibration else None
        channel = ref if ref in fluo else fluo[0]
    elif channel not in recording.channels:
        return None

    n = len(data)
    dropped_pct = 100.0 * float(data.dropped.mean()) if n else 0.0
    z_moved_pct = (
        100.0 * float(recording.frames["z_moved"].fillna(0).astype(bool).mean())
        if n and "z_moved" in recording.frames else 0.0
    )

    valid_pos = np.flatnonzero(~data.dropped)
    if not len(valid_pos):
        edges = np.linspace(0.0, 65535.0, bins + 1)
        return CalciumStats(
            channel=channel,
            hist_edges=edges,
            hist_log_counts=np.zeros(bins, dtype=np.float64),
            sample_times_s=np.empty(0, dtype=np.float64),
            sample_median=np.empty(0, dtype=np.float64),
            sample_p999=np.empty(0, dtype=np.float64),
            median=0.0, p999=0.0, max_val=0.0, snr_proxy=0.0,
            saturated_pct=0.0, z_moved_pct=z_moved_pct, dropped_pct=dropped_pct,
            dtype_max=65535.0, sampled_frames=0,
        )

    if len(valid_pos) > max_samples:
        idx = np.linspace(0, len(valid_pos) - 1, max_samples, dtype=int)
        chosen = valid_pos[idx]
    else:
        chosen = valid_pos

    src = recording[channel]
    stack = src.array() if src.role == "fluorescence" else None
    sample0 = stack[int(chosen[0])] if stack is not None else src[int(data.frame_index[chosen[0]])]
    dtype = sample0.dtype
    dtype_max = float(np.iinfo(dtype).max) if np.issubdtype(dtype, np.integer) else 1.0
    step_y = 4 if sample0.shape[0] >= 16 else 1
    step_x = 4 if sample0.shape[1] >= 16 else 1

    counts = np.zeros(bins, dtype=np.int64)
    edges = np.linspace(0.0, dtype_max + 1.0, bins + 1)
    sample_times = np.empty(len(chosen), dtype=np.float64)
    sample_med = np.empty(len(chosen), dtype=np.float64)
    sample_p999 = np.empty(len(chosen), dtype=np.float64)
    all_samples: list[np.ndarray] = []
    sat_pixels = 0
    total_pixels = 0
    obs_max = 0.0

    for out_i, pos in enumerate(chosen):
        img = stack[int(pos)] if stack is not None else src[int(data.frame_index[pos])]
        sub = img[::step_y, ::step_x]
        flat = sub.ravel()
        all_samples.append(flat)
        c, _ = np.histogram(flat, bins=edges)
        counts += c
        sample_times[out_i] = float(data.time_s[pos])
        sample_med[out_i] = float(np.median(flat))
        sample_p999[out_i] = float(np.percentile(flat, 99.9))
        obs_max = max(obs_max, float(img.max()))
        if np.issubdtype(dtype, np.integer):
            sat_pixels += int(np.count_nonzero(sub >= dtype_max))
        total_pixels += int(flat.size)

    pooled = np.concatenate(all_samples)
    med = float(np.median(pooled))
    p999 = float(np.percentile(pooled, 99.9))
    mad = float(np.median(np.abs(pooled.astype(np.float64) - med))) * 1.4826
    snr_proxy = (p999 - med) / max(mad, 1.0)
    sat_pct = 100.0 * sat_pixels / total_pixels if total_pixels else 0.0

    return CalciumStats(
        channel=channel,
        hist_edges=edges,
        hist_log_counts=np.log10(1.0 + counts),
        sample_times_s=sample_times,
        sample_median=sample_med,
        sample_p999=sample_p999,
        median=med,
        p999=p999,
        max_val=obs_max,
        snr_proxy=snr_proxy,
        saturated_pct=sat_pct,
        z_moved_pct=z_moved_pct,
        dropped_pct=dropped_pct,
        dtype_max=dtype_max,
        sampled_frames=len(chosen),
    )
