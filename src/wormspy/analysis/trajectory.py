"""World-coordinate worm trajectory reconstruction and Tierpsy export (ADR 0007/0009).

Combines stage telemetry (`frames.csv`) + session calibration (`session.json`) with whole-worm
segmentation (from WormsPy's `DarkObject` estimator or external masks such as Step 3 of
`RIA-Segmentation`) to reconstruct world-coordinate centroids, speeds, and skeletons, and
exports them in Tierpsy-compatible formats.
"""

import argparse
import json
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from wormspy.reader import Recording, open_recording, open_session
from wormspy.tracking.estimators import DarkObject


def _zhang_suen_thin(binary: np.ndarray, max_iters: int = 120) -> np.ndarray:
    """Vectorized Zhang-Suen morphological thinning returning a boolean 1-px skeleton."""
    skel = np.pad((binary > 0).astype(np.uint8), 1, mode="constant")
    for _ in range(max_iters):
        changed = False
        for step in (0, 1):
            p2 = skel[:-2, 1:-1]
            p3 = skel[:-2, 2:]
            p4 = skel[1:-1, 2:]
            p5 = skel[2:, 2:]
            p6 = skel[2:, 1:-1]
            p7 = skel[2:, :-2]
            p8 = skel[1:-1, :-2]
            p9 = skel[:-2, :-2]
            center = skel[1:-1, 1:-1]

            neighbors = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            transitions = (
                ((p2 == 0) & (p3 == 1)).astype(np.uint8)
                + ((p3 == 0) & (p4 == 1)).astype(np.uint8)
                + ((p4 == 0) & (p5 == 1)).astype(np.uint8)
                + ((p5 == 0) & (p6 == 1)).astype(np.uint8)
                + ((p6 == 0) & (p7 == 1)).astype(np.uint8)
                + ((p7 == 0) & (p8 == 1)).astype(np.uint8)
                + ((p8 == 0) & (p9 == 1)).astype(np.uint8)
                + ((p9 == 0) & (p2 == 1)).astype(np.uint8)
            )
            cond_a = (center == 1) & (neighbors >= 2) & (neighbors <= 6) & (transitions == 1)
            if step == 0:
                cond_b = (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
            else:
                cond_b = (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
            remove = cond_a & cond_b
            if np.any(remove):
                center[remove] = 0
                changed = True
        if not changed:
            break
    return skel[1:-1, 1:-1].astype(bool)


def _longest_skeleton_path(skel: np.ndarray) -> np.ndarray | None:
    """Two-pass BFS diameter path over an 8-connected boolean skeleton."""
    coords = np.argwhere(skel)
    if len(coords) < 2:
        return None
    h, w = skel.shape
    index_map = np.full((h, w), -1, dtype=np.int32)
    index_map[coords[:, 0], coords[:, 1]] = np.arange(len(coords), dtype=np.int32)

    offsets = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))

    def bfs(start: int) -> tuple[int, np.ndarray]:
        parent = np.full(len(coords), -1, dtype=np.int32)
        dist = np.full(len(coords), -1, dtype=np.int32)
        dist[start] = 0
        q: deque[int] = deque([start])
        farthest = start
        while q:
            cur = q.popleft()
            r, c = int(coords[cur, 0]), int(coords[cur, 1])
            d_next = int(dist[cur]) + 1
            for dr, dc in offsets:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    nxt = int(index_map[nr, nc])
                    if nxt >= 0 and dist[nxt] < 0:
                        dist[nxt] = d_next
                        parent[nxt] = cur
                        q.append(nxt)
                        farthest = nxt
        return farthest, parent

    u, _ = bfs(0)
    v, parent = bfs(u)
    path_idx: list[int] = []
    cur = v
    while cur >= 0:
        path_idx.append(cur)
        cur = int(parent[cur])
    path_idx.reverse()
    if len(path_idx) < 2:
        return None
    rc = coords[np.array(path_idx, dtype=np.int32)]
    # return (x=col, y=row)
    return np.column_stack([rc[:, 1], rc[:, 0]]).astype(np.float64)


def _resample_polyline(pts: np.ndarray, n_points: int) -> np.ndarray:
    deltas = np.diff(pts, axis=0)
    seg_len = np.hypot(deltas[:, 0], deltas[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(seg_len)])
    total = float(cum[-1])
    if total <= 0.0:
        return np.repeat(pts[:1], n_points, axis=0)
    target = np.linspace(0.0, total, n_points)
    return np.column_stack([np.interp(target, cum, pts[:, 0]), np.interp(target, cum, pts[:, 1])])


def extract_skeleton(mask: np.ndarray, n_points: int = 49,
                     max_dim: int = 160) -> np.ndarray | None:
    """Extract an `n_points` centerline `(x, y)` in full-res pixels from a binary worm mask."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    h, w = mask.shape[:2]
    x0, x1 = max(0, int(xs.min()) - 2), min(w, int(xs.max()) + 3)
    y0, y1 = max(0, int(ys.min()) - 2), min(h, int(ys.max()) + 3)
    crop = (mask[y0:y1, x0:x1] > 0).astype(np.uint8)
    ch, cw = crop.shape
    scale = min(1.0, float(max_dim) / max(ch, cw))
    if scale < 1.0:
        sw, sh = max(2, round(cw * scale)), max(2, round(ch * scale))
        work = cv2.resize(crop, (sw, sh), interpolation=cv2.INTER_NEAREST)
        sx, sy = cw / sw, ch / sh
    else:
        work = crop
        sx, sy = 1.0, 1.0

    skel = _zhang_suen_thin(work)
    path = _longest_skeleton_path(skel)
    if path is None:
        return None
    sampled = _resample_polyline(path, n_points)
    sampled[:, 0] = x0 + sampled[:, 0] * sx
    sampled[:, 1] = y0 + sampled[:, 1] * sy
    return sampled


@dataclass
class TrajectoryResult:
    table: pd.DataFrame
    skeletons_px: np.ndarray | None
    skeletons_um: np.ndarray | None
    stage_px: np.ndarray | None
    microns_per_pixel: float | None
    fps: float
    channel: str


def default_behaviour_channel(rec: Recording) -> str:
    for name, ch in rec.channels.items():
        if ch.role == "behaviour":
            return name
    if rec.calibration and rec.calibration.reference in rec.channels:
        return rec.calibration.reference
    return next(iter(rec.channels))


def _largest_mask_and_centroid(mask_raw: np.ndarray) -> tuple[np.ndarray | None, tuple[float, float] | None, float]:
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        (mask_raw > 0).astype(np.uint8), connectivity=8)
    if num_labels <= 1:
        return None, None, 0.0
    best = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    area = float(stats[best, cv2.CC_STAT_AREA])
    cx, cy = float(centroids[best, 0]), float(centroids[best, 1])
    return (labels == best), (cx, cy), area


def reconstruct_trajectory(
    rec: Recording,
    channel: str | None = None,
    estimator=None,
    mask_dir: Path | None = None,
    extract_skeletons: bool = True,
    skeleton_points: int = 49,
) -> TrajectoryResult:
    """Reconstruct per-frame worm centroids, speeds, and optional skeletons in world µm."""
    channel = channel or default_behaviour_channel(rec)
    source = rec[channel]
    est = DarkObject() if estimator is None else estimator
    valid = rec.valid
    n = len(rec.index)

    centroids_px = np.full((n, 2), np.nan, dtype=np.float64)
    areas_px = np.full(n, np.nan, dtype=np.float64)
    skeletons_px = (
        np.full((n, skeleton_points, 2), np.nan, dtype=np.float64)
        if extract_skeletons else None
    )
    prev_skel: np.ndarray | None = None

    for pos, (frame_index, image) in enumerate(zip(rec.index, source, strict=True)):
        if not valid.loc[frame_index]:
            continue
        if mask_dir is not None:
            mask_path = Path(mask_dir) / f"{pos:06d}_worm_mask.png"
            raw = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE) if mask_path.exists() else None
            if raw is None:
                continue
            mask, centroid, area = _largest_mask_and_centroid(raw)
        else:
            out = est(image)
            mask, centroid, area = out.mask, out.point_px, out.area_px

        if centroid is not None:
            centroids_px[pos] = centroid
            areas_px[pos] = area
        if skeletons_px is not None and mask is not None:
            skel = extract_skeleton(mask, n_points=skeleton_points)
            if skel is not None:
                if prev_skel is not None:
                    d_fwd = float(np.linalg.norm(skel[0] - prev_skel[0])
                                  + np.linalg.norm(skel[-1] - prev_skel[-1]))
                    d_rev = float(np.linalg.norm(skel[-1] - prev_skel[0])
                                  + np.linalg.norm(skel[0] - prev_skel[-1]))
                    if d_rev < d_fwd:
                        skel = skel[::-1].copy()
                skeletons_px[pos] = skel
                prev_skel = skel

    table = pd.DataFrame({
        "centroid_x_px": centroids_px[:, 0],
        "centroid_y_px": centroids_px[:, 1],
        "area_px": areas_px,
        "time_s": rec.time_s.to_numpy(),
        "valid": valid.to_numpy(),
    }, index=rec.index)
    for col in ("z_moved", "x_um", "y_um", "event"):
        if col in rec.frames:
            table[col] = rec.frames[col].to_numpy()

    skeletons_um: np.ndarray | None = None
    stage_px: np.ndarray | None = None
    um_per_px: float | None = None
    try:
        cam = rec._calibrated_camera(channel)
        um_per_px = rec.microns_per_pixel(channel)
        world_xy = rec.plate_um_batch(channel, centroids_px)
        table["worm_x_um"] = world_xy[:, 0]
        table["worm_y_um"] = world_xy[:, 1]
        if skeletons_px is not None:
            skeletons_um = rec.plate_um_batch(channel, skeletons_px)
        if {"x_um", "y_um"} <= set(rec.frames.columns):
            stage_um = rec.frames[["x_um", "y_um"]].to_numpy(dtype=np.float64)
            stage_px = stage_um @ cam.matrix.T

        dt = np.diff(table["time_s"].to_numpy(dtype=np.float64))
        dx = np.diff(world_xy[:, 0])
        dy = np.diff(world_xy[:, 1])
        ok = np.isfinite(dx) & np.isfinite(dy) & (dt > 0.0)
        step_dist = np.full(n, np.nan, dtype=np.float64)
        speed = np.full(n, np.nan, dtype=np.float64)
        heading = np.full(n, np.nan, dtype=np.float64)
        step_dist[1:][ok] = np.hypot(dx[ok], dy[ok])
        speed[1:][ok] = step_dist[1:][ok] / dt[ok]
        heading[1:][ok] = np.degrees(np.arctan2(dy[ok], dx[ok]))
        table["speed_um_s"] = speed
        table["heading_deg"] = heading
        cum = np.zeros(n, dtype=np.float64)
        np.cumsum(np.where(np.isfinite(step_dist), step_dist, 0.0), out=cum)
        table["distance_um"] = cum
    except ValueError:
        pass

    return TrajectoryResult(
        table=table,
        skeletons_px=skeletons_px,
        skeletons_um=skeletons_um,
        stage_px=stage_px,
        microns_per_pixel=um_per_px,
        fps=float(rec.fps or 10.0),
        channel=channel,
    )


def write_tierpsy_hdf5(result: TrajectoryResult, path: Path) -> Path:
    """Write a Tierpsy-compatible `_skeletons.hdf5` file (requires `h5py`)."""
    try:
        import h5py
    except ImportError as exc:
        raise ImportError(
            "Tierpsy HDF5 export needs h5py: install the `tierpsy` extra "
            "(uv sync --extra tierpsy, or pip install h5py)."
        ) from exc

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = len(result.table)
    use_world = result.skeletons_um is not None
    skel = result.skeletons_um if use_world else result.skeletons_px
    um_per_px = 1.0 if use_world else float(result.microns_per_pixel or 1.0)

    coord_x = (result.table["worm_x_um"] if "worm_x_um" in result.table
               else result.table["centroid_x_px"]).to_numpy(dtype=np.float32)
    coord_y = (result.table["worm_y_um"] if "worm_y_um" in result.table
               else result.table["centroid_y_px"]).to_numpy(dtype=np.float32)
    area = result.table["area_px"].to_numpy(dtype=np.float32)
    detected = np.isfinite(coord_x) & np.isfinite(coord_y)

    traj_dtype = np.dtype([
        ("frame_number", np.int32),
        ("worm_index_joined", np.int32),
        ("coord_x", np.float32),
        ("coord_y", np.float32),
        ("area", np.float32),
        ("threshold", np.float32),
    ])
    traj = np.empty(n, dtype=traj_dtype)
    traj["frame_number"] = np.arange(n, dtype=np.int32)
    traj["worm_index_joined"] = np.where(detected, 1, -1).astype(np.int32)
    traj["coord_x"] = coord_x
    traj["coord_y"] = coord_y
    traj["area"] = area
    traj["threshold"] = 0.0

    with h5py.File(path, "w") as h5:
        h5.attrs["fps"] = result.fps
        h5.attrs["expected_fps"] = result.fps
        h5.attrs["microns_per_pixel"] = um_per_px
        if skel is not None:
            ds = h5.create_dataset("skeleton", data=skel.astype(np.float32))
            ds.attrs["fps"] = result.fps
            ds.attrs["microns_per_pixel"] = um_per_px
            ds.attrs["units"] = "microns" if use_world else "pixels"
        if result.stage_px is not None:
            h5.create_dataset("stage_position_pix", data=result.stage_px.astype(np.float64))
        ts_grp = h5.create_group("timestamp")
        ts_grp.create_dataset("raw", data=np.arange(n, dtype=np.int64))
        ts_grp.create_dataset("time", data=result.table["time_s"].to_numpy(dtype=np.float64))
        h5.create_dataset("trajectories_data", data=traj)
    return path


def export_tierpsy(rec: Recording, result: TrajectoryResult, out_dir: Path,
                   write_hdf5: bool = False) -> dict[str, Path]:
    """Export world-coordinate trajectory tables, stage positions, and optional Tierpsy HDF5."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}

    traj_csv = out_dir / "trajectory.csv"
    result.table.to_csv(traj_csv)
    outputs["trajectory_csv"] = traj_csv

    stage_df = pd.DataFrame({
        "frame_index": rec.index.to_numpy(dtype=np.int64),
        "time_s": result.table["time_s"].to_numpy(),
        "stage_x_um": (result.table["x_um"].to_numpy() if "x_um" in result.table
                       else np.full(len(result.table), np.nan)),
        "stage_y_um": (result.table["y_um"].to_numpy() if "y_um" in result.table
                       else np.full(len(result.table), np.nan)),
        "stage_x_px": (result.stage_px[:, 0] if result.stage_px is not None
                       else np.full(len(result.table), np.nan)),
        "stage_y_px": (result.stage_px[:, 1] if result.stage_px is not None
                       else np.full(len(result.table), np.nan)),
    })
    stage_csv = out_dir / "stage_position.csv"
    stage_df.to_csv(stage_csv, index=False)
    outputs["stage_csv"] = stage_csv

    meta_path = out_dir / "tierpsy_metadata.json"
    meta = {
        "fps": result.fps,
        "microns_per_pixel": result.microns_per_pixel,
        "channel": result.channel,
        "first_frame_index": int(rec.index[0]) if len(rec.index) else 0,
        "n_frames": len(result.table),
        "skeleton_points": (0 if result.skeletons_px is None
                            else int(result.skeletons_px.shape[1])),
        "coordinate_units": "microns" if result.skeletons_um is not None else "pixels",
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    outputs["metadata"] = meta_path

    if result.skeletons_px is not None:
        npz_path = out_dir / "skeletons_world.npz"
        payload = {
            "frame_index": rec.index.to_numpy(dtype=np.int64),
            "skeleton_px": result.skeletons_px,
            "fps": np.array(result.fps),
        }
        if result.skeletons_um is not None:
            payload["skeleton_um"] = result.skeletons_um
        if {"worm_x_um", "worm_y_um"} <= set(result.table.columns):
            payload["centroid_um"] = result.table[["worm_x_um", "worm_y_um"]].to_numpy()
        if result.stage_px is not None:
            payload["stage_px"] = result.stage_px
        np.savez(npz_path, **payload)
        outputs["skeletons_npz"] = npz_path

    if write_hdf5:
        outputs["hdf5"] = write_tierpsy_hdf5(result, out_dir / f"{rec.path.name}_skeletons.hdf5")

    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m wormspy.analysis.trajectory",
        description="Reconstruct world-coordinate worm trajectories and export Tierpsy files.",
    )
    parser.add_argument("path", type=Path, help="rec-NNN folder or session folder")
    parser.add_argument("--channel", default=None)
    parser.add_argument("--masks", type=Path, default=None,
                        help="Optional folder of 000000_worm_mask.png masks")
    parser.add_argument("--no-skeleton", action="store_true")
    parser.add_argument("--hdf5", action="store_true",
                        help="Also write Tierpsy _skeletons.hdf5 (requires h5py)")
    parser.add_argument("--out", type=Path, default=None,
                        help="Output folder (default: <rec>/analysis/tierpsy)")
    args = parser.parse_args(argv)

    folders = ([args.path] if (args.path / "frames.csv").exists()
               else open_session(args.path).recordings)
    for folder in folders:
        with open_recording(folder) as rec:
            res = reconstruct_trajectory(
                rec, channel=args.channel, mask_dir=args.masks,
                extract_skeletons=not args.no_skeleton)
            out_dir = args.out or (folder / "analysis" / "tierpsy")
            outputs = export_tierpsy(rec, res, out_dir, write_hdf5=args.hdf5)
            print(f"{folder.name}: wrote {outputs['trajectory_csv']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
