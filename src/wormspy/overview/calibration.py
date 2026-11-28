"""Global-view (WormTraffic) camera-to-stage homography calibration.

Maps overview image pixels `(u, v)` to Zaber stage XY coordinates `(x_um, y_um)` in µm, and
projects the high-magnification field of view back onto the overview image.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class OverviewCalibration:
    homography_px_to_um: np.ndarray
    pixel_points: tuple[tuple[float, float], ...] = ()
    stage_points_um: tuple[tuple[float, float], ...] = ()
    residual_um: float = 0.0

    def __post_init__(self) -> None:
        h = np.asarray(self.homography_px_to_um, dtype=np.float64)
        if h.shape != (3, 3):
            raise ValueError(f"expected (3, 3) homography, got {h.shape}")
        object.__setattr__(self, "homography_px_to_um", h)

    @classmethod
    def fit(cls, pixel_points, stage_points_um) -> "OverviewCalibration":
        px = np.asarray(pixel_points, dtype=np.float64)
        um = np.asarray(stage_points_um, dtype=np.float64)
        if px.ndim != 2 or px.shape[1] != 2 or um.shape != px.shape or len(px) < 4:
            raise ValueError("need at least 4 matching (u, v) and (x_um, y_um) point pairs")
        if _is_degenerate(px) or _is_degenerate(um):
            raise ValueError("calibration points are collinear or degenerate")
        if len(px) == 4:
            homography = cv2.getPerspectiveTransform(px.astype(np.float32), um.astype(np.float32))
        else:
            homography, _ = cv2.findHomography(px, um, method=0)
        if homography is None or abs(float(np.linalg.det(homography))) < 1e-12:
            raise ValueError("calibration points are degenerate; cannot fit homography")
        homography = np.asarray(homography, dtype=np.float64)
        residual = _rms_residual_um(homography, px, um)
        return cls(
            homography_px_to_um=homography,
            pixel_points=tuple((float(u), float(v)) for u, v in px),
            stage_points_um=tuple((float(x), float(y)) for x, y in um),
            residual_um=residual,
        )

    def pixel_to_stage_um(self, u: float, v: float) -> tuple[float, float]:
        w = self.homography_px_to_um @ np.array([u, v, 1.0], dtype=np.float64)
        if abs(float(w[2])) < 1e-12:
            raise ValueError("homography mapping produced w[2] near zero")
        return float(w[0] / w[2]), float(w[1] / w[2])

    def stage_um_to_pixel(self, x_um: float, y_um: float) -> tuple[float, float]:
        inv = np.linalg.inv(self.homography_px_to_um)
        w = inv @ np.array([x_um, y_um, 1.0], dtype=np.float64)
        if abs(float(w[2])) < 1e-12:
            raise ValueError("inverse homography mapping produced w[2] near zero")
        return float(w[0] / w[2]), float(w[1] / w[2])

    def fov_polygon_px(self, stage_xy_um: tuple[float, float],
                       fov_um: tuple[float, float] = (1440.0, 900.0)) -> np.ndarray:
        """Closed 5-point pixel polygon of the high-magnification FOV on the overview image."""
        cx, cy = stage_xy_um
        hw, hh = fov_um[0] / 2.0, fov_um[1] / 2.0
        corners = (
            (cx - hw, cy - hh),
            (cx + hw, cy - hh),
            (cx + hw, cy + hh),
            (cx - hw, cy + hh),
            (cx - hw, cy - hh),
        )
        return np.array([self.stage_um_to_pixel(x, y) for x, y in corners], dtype=np.float64)

    def to_json(self) -> dict:
        return {
            "homography_px_to_um": self.homography_px_to_um.tolist(),
            "pixel_points": [list(pt) for pt in self.pixel_points],
            "stage_points_um": [list(pt) for pt in self.stage_points_um],
            "residual_um": self.residual_um,
        }

    @classmethod
    def from_json(cls, data: dict) -> "OverviewCalibration":
        return cls(
            homography_px_to_um=np.array(data["homography_px_to_um"], dtype=np.float64),
            pixel_points=tuple((float(p[0]), float(p[1])) for p in data.get("pixel_points", ())),
            stage_points_um=tuple(
                (float(p[0]), float(p[1])) for p in data.get("stage_points_um", ())),
            residual_um=float(data.get("residual_um", 0.0)),
        )

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.to_json(), indent=2))
        tmp.replace(path)

    @classmethod
    def load(cls, path: Path) -> "OverviewCalibration":
        return cls.from_json(json.loads(Path(path).read_text()))

    @classmethod
    def from_legacy_yaml(cls, path: Path) -> "OverviewCalibration":
        """Import WormTraffic's `camera_stage_calibration.yaml` (which stores H in mm)."""
        data = _load_yaml_mapping(Path(path).read_text())
        if "H_pix2world" not in data:
            raise ValueError(f"{path} does not contain H_pix2world")
        h_mm = np.asarray(data["H_pix2world"], dtype=np.float64)
        if h_mm.shape != (3, 3):
            raise ValueError(f"expected (3, 3) H_pix2world in {path}, got {h_mm.shape}")
        h_um = np.diag([1000.0, 1000.0, 1.0]) @ h_mm

        px_pts: tuple[tuple[float, float], ...] = ()
        um_pts: tuple[tuple[float, float], ...] = ()
        residual = 0.0
        raw_px = data.get("pixel_points")
        order = data.get("pixel_points_order")
        raw_mm = data.get("world_points_mm")
        if (isinstance(raw_px, dict) and isinstance(order, list) and isinstance(raw_mm, list)
                and len(order) == len(raw_mm) and all(name in raw_px for name in order)):
            px_arr = np.array([raw_px[name] for name in order], dtype=np.float64)
            um_arr = np.array(raw_mm, dtype=np.float64) * 1000.0
            px_pts = tuple((float(u), float(v)) for u, v in px_arr)
            um_pts = tuple((float(x), float(y)) for x, y in um_arr)
            residual = _rms_residual_um(h_um, px_arr, um_arr)
        return cls(homography_px_to_um=h_um, pixel_points=px_pts, stage_points_um=um_pts,
                   residual_um=residual)


def _is_degenerate(pts: np.ndarray) -> bool:
    if np.linalg.matrix_rank(pts - pts[0]) < 2:
        return True
    if len(pts) == 4:
        for i in range(4):
            tri = np.delete(pts, i, axis=0)
            area2 = abs((tri[1, 0] - tri[0, 0]) * (tri[2, 1] - tri[0, 1])
                        - (tri[2, 0] - tri[0, 0]) * (tri[1, 1] - tri[0, 1]))
            if area2 < 1e-6:
                return True
    return False


def _rms_residual_um(homography: np.ndarray, px: np.ndarray, um: np.ndarray) -> float:
    ones = np.ones((len(px), 1), dtype=np.float64)
    proj = (homography @ np.hstack([px, ones]).T).T
    if np.any(np.abs(proj[:, 2]) < 1e-12):
        raise ValueError("calibration points project to infinity")
    pred = proj[:, :2] / proj[:, 2:3]
    return float(np.sqrt(np.mean(np.sum((pred - um) ** 2, axis=1))))


def _load_yaml_mapping(text: str) -> dict:
    try:
        import yaml  # type: ignore[import-not-found]
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise TypeError("expected YAML mapping")
        return loaded
    except ImportError:
        return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> dict:
    """Minimal stdlib YAML parser covering Tracker's camera_stage_calibration.yaml structure."""
    lines = []
    for raw in text.splitlines():
        stripped = raw.split("#", 1)[0].rstrip()
        if stripped.strip():
            indent = len(raw) - len(raw.lstrip(" "))
            lines.append((indent, stripped.strip()))

    def parse_scalar(val: str):
        low = val.lower()
        if low in ("true", "false"):
            return low == "true"
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            return val.strip("'\"")

    def parse_block(idx: int, min_indent: int):
        if idx >= len(lines):
            return None, idx
        base_indent, first = lines[idx]
        if first.startswith("- "):
            items = []
            while idx < len(lines) and lines[idx][0] == base_indent and lines[idx][1].startswith("- "):
                rest = lines[idx][1][2:].strip()
                if rest.startswith("- "):
                    nested = [parse_scalar(rest[2:].strip())]
                    idx += 1
                    while idx < len(lines) and lines[idx][0] > base_indent and lines[idx][1].startswith("- "):
                        nested.append(parse_scalar(lines[idx][1][2:].strip()))
                        idx += 1
                    items.append(nested)
                elif rest:
                    items.append(parse_scalar(rest))
                    idx += 1
                else:
                    val, idx = parse_block(idx + 1, base_indent + 1)
                    items.append(val)
            return items, idx

        mapping = {}
        while idx < len(lines) and lines[idx][0] == base_indent:
            content = lines[idx][1]
            if ":" not in content or content.startswith("- "):
                break
            key, rest = content.split(":", 1)
            key = key.strip()
            rest = rest.strip()
            if rest:
                mapping[key] = parse_scalar(rest)
                idx += 1
            elif idx + 1 < len(lines) and (
                lines[idx + 1][0] > base_indent
                or (lines[idx + 1][0] == base_indent and lines[idx + 1][1].startswith("- "))
            ):
                val, idx = parse_block(idx + 1, base_indent + 1)
                mapping[key] = val
            else:
                mapping[key] = None
                idx += 1
        return mapping, idx

    result, _ = parse_block(0, 0)
    if not isinstance(result, dict):
        raise TypeError("expected YAML mapping")
    return result
