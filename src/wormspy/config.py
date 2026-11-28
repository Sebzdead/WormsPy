"""Rig configuration from `rig.toml` (ADR 0005 amendment).

Everything has a default, so a missing section is fine. Anything unsafe or contradictory, like
an inverted safe range, an unknown axis, or a button mapped to a command that doesn't exist, is
rejected at startup with a message naming the offending key.
"""

import dataclasses
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from wormspy.control import commands as C
from wormspy.control.gamepad import DEFAULT_BUTTONS, StickConfig
from wormspy.presets import CameraSettings, exposure_budget_us
from wormspy.tracking.controller import ServoConfig
from wormspy.tracking.estimators import POLARITIES, BrightMarker, DarkObject

AXES = ("x", "y", "z")
# Travel of the reference rig: 2× Zaber TSB60E (50.4 mm) and VSR20A (20 mm). Narrow Z in
# rig.toml to a range that is safe for your objective and sample holder.
DEFAULT_SAFE_RANGE_UM = {"x": (0.0, 50_400.0), "y": (0.0, 50_400.0), "z": (0.0, 20_000.0)}


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class StageConfig:
    xy_port: str = "COM6"
    z_port: str = "COM3"
    max_speed_um_s: float = 2000.0
    safe_range_um: dict[str, tuple[float, float]] = field(
        default_factory=lambda: dict(DEFAULT_SAFE_RANGE_UM))


ROLES = ("fluorescence", "behaviour")
PIXEL_FORMATS = ("Mono8", "Mono16")


@dataclass(frozen=True)
class CameraConfig:
    name: str                  # channel name: file stem and CSV column prefix
    role: str                  # "fluorescence" (raw 16-bit TIFF) or "behaviour" (FFV1 video)
    pixel_format: str
    exposure_us: float
    gain_db: float = 0.0
    serial: str = ""           # FLIR serial number (printed on the camera / SpinView)


@dataclass(frozen=True)
class CamerasConfig:
    """The two FLIR cameras (ADR 0006): the clock camera free-runs at `fps` and drives the
    follower's trigger input through a GPIO cable."""
    fps: float = 10.0
    clock: CameraConfig = field(default_factory=lambda: CameraConfig(
        name="gcamp", role="fluorescence", pixel_format="Mono16", exposure_us=14_000.0))
    follower: CameraConfig = field(default_factory=lambda: CameraConfig(
        name="brightfield", role="behaviour", pixel_format="Mono8", exposure_us=5_000.0))
    clock_output_line: str = "Line2"        # carries the clock camera's ExposureActive
    follower_trigger_line: str = "Line3"    # the follower's trigger input

    @property
    def settings(self) -> CameraSettings:
        """rig.toml's frame rate, exposures and gains: the Default preset."""
        return CameraSettings(fps=self.fps, clock_exposure_us=self.clock.exposure_us,
                              clock_gain_db=self.clock.gain_db,
                              follower_exposure_us=self.follower.exposure_us,
                              follower_gain_db=self.follower.gain_db)


DEFAULT_AXIS_INDICES = {"left_x": 0, "left_y": 1, "right_y": 3}
DEFAULT_BUTTON_INDICES = {"A": 0, "B": 1, "X": 2, "Y": 3}


@dataclass(frozen=True)
class GamepadConfig:
    sticks: StickConfig = field(default_factory=StickConfig)
    buttons: dict[str, type] = field(default_factory=lambda: dict(DEFAULT_BUTTONS))
    axes: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_AXIS_INDICES))
    button_indices: dict[str, int] = field(
        default_factory=lambda: dict(DEFAULT_BUTTON_INDICES))


@dataclass(frozen=True)
class OverviewConfig:
    """Optional third global-view camera + WormTraffic multi-worm tracker."""
    serial: str = ""
    fps: float = 1.0
    exposure_us: float = 3000.0
    gain_db: float = 0.0
    pixel_format: str = "Mono8"
    alpha: float = 0.02
    threshold: int = 20
    min_area_px: int = 50
    max_missed: int = 3
    max_dist_px: float = 60.0
    snap_dist_px: float = 50.0


@dataclass(frozen=True)
class PathsConfig:
    data_root: Path
    calibration: Path
    presets: Path
    overview_calibration: Path


@dataclass(frozen=True)
class TrackingConfig:
    """Servo gains and estimator thresholds (ADR 0008), tuned per rig and per experiment."""
    servo: ServoConfig = field(default_factory=ServoConfig)
    dark_object: DarkObject = field(default_factory=DarkObject)
    bright_marker: BrightMarker = field(default_factory=BrightMarker)


@dataclass(frozen=True)
class RigConfig:
    cameras: CamerasConfig
    stage: StageConfig
    gamepad: GamepadConfig
    paths: PathsConfig
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    overview: OverviewConfig = field(default_factory=OverviewConfig)


def _button_commands() -> dict[str, type]:
    """Commands a button can issue: those that need no arguments."""
    out = {}
    for name in dir(C):
        cls = getattr(C, name)
        if dataclasses.is_dataclass(cls) and isinstance(cls, type) and all(
                f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING
                for f in dataclasses.fields(cls)):
            out[name] = cls
    return out


def load_config(path: Path) -> RigConfig:
    path = Path(path)
    if not path.exists():
        # no rig.toml yet: every default
        stage = _stage({})
        cameras = _cameras({})
        return RigConfig(cameras=cameras, stage=stage, gamepad=_gamepad({}),
                         paths=_paths({}, path), tracking=_tracking({}, stage),
                         overview=_overview({}, cameras))
    try:
        raw = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path.name}: {exc}") from exc
    stage = _stage(raw.get("stage", {}))
    cameras = _cameras(raw.get("cameras", {}))
    return RigConfig(cameras=cameras, stage=stage,
                     gamepad=_gamepad(raw.get("gamepad", {})),
                     paths=_paths(raw.get("paths", {}), path),
                     tracking=_tracking(raw.get("tracking", {}), stage),
                     overview=_overview(raw.get("overview", {}), cameras))


def _camera(raw: dict, default: CameraConfig, key: str, fps: float) -> CameraConfig:
    unknown = set(raw) - {f.name for f in dataclasses.fields(CameraConfig)}
    if unknown:
        raise ConfigError(f"{key}: unknown key(s) {sorted(unknown)}")
    camera = dataclasses.replace(default, **raw)
    camera = dataclasses.replace(camera, exposure_us=float(camera.exposure_us),
                                 gain_db=float(camera.gain_db), serial=str(camera.serial))
    if camera.role not in ROLES:
        raise ConfigError(f"{key}.role must be one of {list(ROLES)}, not {camera.role!r}")
    if camera.pixel_format not in PIXEL_FORMATS:
        raise ConfigError(f"{key}.pixel_format must be one of {list(PIXEL_FORMATS)}")
    if camera.role == "fluorescence" and camera.pixel_format != "Mono16":
        raise ConfigError(f"{key}: fluorescence is recorded raw 16-bit; use Mono16 (ADR 0007)")
    budget = exposure_budget_us(fps)
    if not 0 < camera.exposure_us <= budget:
        raise ConfigError(f"{key}.exposure_us must be in (0, {budget:.0f}] at {fps:g} fps")
    return camera


def _cameras(raw: dict) -> CamerasConfig:
    defaults = CamerasConfig()
    unknown = set(raw) - {f.name for f in dataclasses.fields(CamerasConfig)}
    if unknown:
        raise ConfigError(f"cameras: unknown key(s) {sorted(unknown)}")
    fps = float(raw.get("fps", defaults.fps))
    if fps <= 0:
        raise ConfigError("cameras.fps must be positive")
    clock = _camera(raw.get("clock", {}), defaults.clock, "cameras.clock", fps)
    follower = _camera(raw.get("follower", {}), defaults.follower, "cameras.follower", fps)
    if clock.name == follower.name:
        raise ConfigError("cameras: clock and follower need different names")
    if clock.serial and clock.serial == follower.serial:
        raise ConfigError("cameras: clock and follower have the same serial number")
    cameras = CamerasConfig(
        fps=fps, clock=clock, follower=follower,
        clock_output_line=str(raw.get("clock_output_line", defaults.clock_output_line)),
        follower_trigger_line=str(raw.get("follower_trigger_line",
                                          defaults.follower_trigger_line)))
    problem = cameras.settings.problem()
    if problem:
        raise ConfigError(f"cameras: {problem}")
    return cameras


def _tuned(cls, raw: dict, key: str, auto: tuple[str, ...] = (),
           choices: dict[str, tuple[str, ...]] | None = None):
    """A frozen dataclass with rig.toml's values for its fields. Every value must be a positive
    number; fields in `auto` may also be "auto" (stored as None: computed per frame); fields in
    `choices` must be one of the listed strings."""
    types = {f.name: f.type for f in dataclasses.fields(cls)}
    names = set(types)
    unknown = set(raw) - names
    if unknown:
        raise ConfigError(f"{key}: unknown key(s) {sorted(unknown)}; choose from {sorted(names)}")
    choices = choices or {}
    values = {}
    for name, value in raw.items():
        if name in choices:
            if not isinstance(value, str) or value not in choices[name]:
                raise ConfigError(f"{key}.{name} must be one of {list(choices[name])}, "
                                  f"not {value!r}")
            values[name] = value
            continue
        if name in auto and value == "auto":
            values[name] = None
            continue
        if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
            hint = ' or "auto"' if name in auto else ""
            raise ConfigError(f"{key}.{name} must be a positive number{hint}, not {value!r}")
        if types[name] is int and not isinstance(value, int):
            raise ConfigError(f"{key}.{name} must be a whole number, not {value!r}")
        values[name] = value
    return cls(**values)


def _tracking(raw: dict, stage: StageConfig) -> TrackingConfig:
    unknown = set(raw) - {"servo", "dark_object", "bright_marker"}
    if unknown:
        raise ConfigError(f"tracking: unknown section(s) {sorted(unknown)}")
    servo = _tuned(ServoConfig, raw.get("servo", {}), "tracking.servo")
    if servo.max_speed_um_s > stage.max_speed_um_s:
        raise ConfigError(f"tracking.servo.max_speed_um_s ({servo.max_speed_um_s:g}) is above "
                          f"stage.max_speed_um_s ({stage.max_speed_um_s:g})")
    if servo.feed_forward > 1.5 or servo.velocity_smoothing > 1:
        raise ConfigError("tracking.servo: feed_forward must be ≤ 1.5 and "
                          "velocity_smoothing ≤ 1")
    dark = _tuned(DarkObject, raw.get("dark_object", {}), "tracking.dark_object",
                  auto=("threshold",), choices={"polarity": POLARITIES})
    marker = _tuned(BrightMarker, raw.get("bright_marker", {}), "tracking.bright_marker")
    return TrackingConfig(servo=servo, dark_object=dark, bright_marker=marker)


def _stage(raw: dict) -> StageConfig:
    safe = dict(DEFAULT_SAFE_RANGE_UM)
    for axis, value in raw.get("safe_range_um", {}).items():
        if axis not in AXES:
            raise ConfigError(f"stage.safe_range_um: unknown axis {axis!r} (use x, y, z)")
        lo, hi = (float(v) for v in value)
        if not lo < hi:
            raise ConfigError(f"stage.safe_range_um.{axis}: min {lo} must be below max {hi}")
        safe[axis] = (lo, hi)
    speed = float(raw.get("max_speed_um_s", StageConfig.max_speed_um_s))
    if speed <= 0:
        raise ConfigError("stage.max_speed_um_s must be positive")
    return StageConfig(xy_port=str(raw.get("xy_port", StageConfig.xy_port)),
                       z_port=str(raw.get("z_port", StageConfig.z_port)),
                       max_speed_um_s=speed, safe_range_um=safe)


def _gamepad(raw: dict) -> GamepadConfig:
    unknown_sections = set(raw) - {"sticks", "buttons", "axes", "button_indices"}
    if unknown_sections:
        raise ConfigError(f"gamepad: unknown section(s) {sorted(unknown_sections)}")
    sticks_raw = raw.get("sticks", {})
    unknown = set(sticks_raw) - {f.name for f in dataclasses.fields(StickConfig)}
    if unknown:
        raise ConfigError(f"gamepad.sticks: unknown key(s) {sorted(unknown)}")
    sticks = StickConfig(**sticks_raw)
    if not 0 <= sticks.deadzone < 1:
        raise ConfigError("gamepad.sticks.deadzone must be in [0, 1)")
    if sticks.expo <= 0 or sticks.xy_max_um_s <= 0 or sticks.z_max_um_s <= 0:
        raise ConfigError("gamepad.sticks: expo and max speeds must be positive")
    buttons = dict(DEFAULT_BUTTONS)
    if "buttons" in raw:
        allowed = _button_commands()
        buttons = {}
        for button, command in raw["buttons"].items():
            if command not in allowed:
                raise ConfigError(f"gamepad.buttons.{button}: unknown command {command!r}; "
                                  f"choose from {sorted(allowed)}")
            buttons[button] = allowed[command]
    axes = _index_map(raw.get("axes"), DEFAULT_AXIS_INDICES, "gamepad.axes", restrict_keys=True)
    button_indices = _index_map(raw.get("button_indices"), DEFAULT_BUTTON_INDICES,
                                "gamepad.button_indices", restrict_keys=False)
    return GamepadConfig(sticks=sticks, buttons=buttons, axes=axes,
                         button_indices=button_indices)


def _index_map(raw: dict | None, defaults: dict[str, int], key: str,
               restrict_keys: bool) -> dict[str, int]:
    out = dict(defaults)
    if raw is None:
        return out
    if restrict_keys:
        unknown = set(raw) - set(defaults)
        if unknown:
            raise ConfigError(f"{key}: unknown key(s) {sorted(unknown)}; "
                              f"choose from {sorted(defaults)}")
    for name, idx in raw.items():
        if isinstance(idx, bool) or not isinstance(idx, int) or idx < 0:
            raise ConfigError(f"{key}.{name} must be a non-negative integer, not {idx!r}")
        out[name] = idx
    return out


def _paths(raw: dict, config_path: Path) -> PathsConfig:
    data_root = Path(raw.get("data_root", Path.home() / "WormsPy_data")).expanduser()
    calibration = Path(raw.get("calibration", config_path.parent / "calibration.json"))
    presets = Path(raw.get("presets", config_path.parent / "presets.json"))
    overview_calibration = Path(
        raw.get("overview_calibration", config_path.parent / "overview_calibration.json"))
    return PathsConfig(data_root=data_root, calibration=calibration.expanduser(),
                       presets=presets.expanduser(),
                       overview_calibration=overview_calibration.expanduser())


def _overview(raw: dict, cameras: CamerasConfig) -> OverviewConfig:
    unknown = set(raw) - {f.name for f in dataclasses.fields(OverviewConfig)}
    if unknown:
        raise ConfigError(f"overview: unknown key(s) {sorted(unknown)}")
    defaults = OverviewConfig()
    cfg = OverviewConfig(
        serial=str(raw.get("serial", defaults.serial)),
        fps=float(raw.get("fps", defaults.fps)),
        exposure_us=float(raw.get("exposure_us", defaults.exposure_us)),
        gain_db=float(raw.get("gain_db", defaults.gain_db)),
        pixel_format=str(raw.get("pixel_format", defaults.pixel_format)),
        alpha=float(raw.get("alpha", defaults.alpha)),
        threshold=raw.get("threshold", defaults.threshold),
        min_area_px=raw.get("min_area_px", defaults.min_area_px),
        max_missed=raw.get("max_missed", defaults.max_missed),
        max_dist_px=float(raw.get("max_dist_px", defaults.max_dist_px)),
        snap_dist_px=float(raw.get("snap_dist_px", defaults.snap_dist_px)),
    )
    if cfg.serial and cfg.serial in (cameras.clock.serial, cameras.follower.serial):
        raise ConfigError("overview.serial must differ from cameras.clock and cameras.follower")
    if cfg.fps <= 0:
        raise ConfigError("overview.fps must be positive")
    if cfg.exposure_us <= 0:
        raise ConfigError("overview.exposure_us must be positive")
    if cfg.gain_db < 0:
        raise ConfigError("overview.gain_db must be non-negative")
    if cfg.pixel_format not in PIXEL_FORMATS:
        raise ConfigError(f"overview.pixel_format must be one of {list(PIXEL_FORMATS)}")
    if not 0 < cfg.alpha <= 1:
        raise ConfigError("overview.alpha must be in (0, 1]")
    if isinstance(cfg.threshold, bool) or not isinstance(cfg.threshold, int) or not (0 < cfg.threshold <= 255):
        raise ConfigError("overview.threshold must be an integer in (0, 255]")
    if isinstance(cfg.min_area_px, bool) or not isinstance(cfg.min_area_px, int) or cfg.min_area_px <= 0:
        raise ConfigError("overview.min_area_px must be a positive integer")
    if isinstance(cfg.max_missed, bool) or not isinstance(cfg.max_missed, int) or cfg.max_missed < 0:
        raise ConfigError("overview.max_missed must be a non-negative integer")
    if cfg.max_dist_px <= 0:
        raise ConfigError("overview.max_dist_px must be positive")
    if cfg.snap_dist_px <= 0:
        raise ConfigError("overview.snap_dist_px must be positive")
    return cfg
