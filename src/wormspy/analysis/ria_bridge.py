"""Bridge between WormsPy v2 recordings and `analysis_code/RIA-Segmentation_withBlurdection-main`.

- `export_for_ria_pipeline`: exposes a WormsPy recording as the `01_tiff_stack/<stack>.tif` and
  `02_tiff_jpg/<stack>/*.jpg` inputs expected by the YOLO + SAM2 RIA segmentation pipeline, plus
  a `<stack>_frame_index_map.csv` mapping 0-based pipeline frame numbers back to `frame_index`.
- `join_ria_results`: merges `head_angles.csv` and/or `*_roi_intensity.csv` back onto WormsPy's
  `frames.csv` spine, adding `time_s`, `valid`, `z_moved`, `event`, and world plate positions
  (`head_x_um`, `anchor_x_um`, ...) via `Recording.plate_um_batch()`.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import tifffile

from wormspy.analysis.segmentation import default_channel
from wormspy.reader import Recording, open_recording, open_session


def _normalize_to_u8(image: np.ndarray, method: str) -> np.ndarray:
    if image.dtype == np.uint8:
        return image
    arr = image.astype(np.float32)
    if method == "percentile":
        lo, hi = np.percentile(arr, (1.0, 99.0))
    elif method == "minmax":
        lo, hi = float(arr.min()), float(arr.max())
    else:
        raise ValueError(f"unknown normalization {method!r}; use 'minmax' or 'percentile'")
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return np.zeros(image.shape[:2], dtype=np.uint8)
    return np.clip((arr - lo) * (255.0 / (hi - lo)), 0.0, 255.0).astype(np.uint8)


def export_for_ria_pipeline(
    rec: Recording,
    output_root: Path,
    run_id: str,
    channel: str | None = None,
    stack_name: str | None = None,
    normalization: str = "minmax",
    quality: int = 95,
    copy_tiff: bool = False,
) -> dict[str, Path]:
    """Export a WormsPy v2 recording into the RIA-Segmentation folder layout."""
    channel = channel or default_channel(rec)
    source = rec[channel]
    stack_name = stack_name or f"{rec.path.parent.name}_{rec.path.name}"
    run_dir = Path(output_root) / run_id
    stack_dir = run_dir / "01_tiff_stack"
    jpg_dir = run_dir / "02_tiff_jpg" / stack_name
    stack_dir.mkdir(parents=True, exist_ok=True)
    jpg_dir.mkdir(parents=True, exist_ok=True)

    stack_path = stack_dir / f"{stack_name}.tif"
    if stack_path.is_symlink() or stack_path.exists():
        stack_path.unlink()
    if source.role == "fluorescence":
        if copy_tiff:
            shutil.copy2(source.path, stack_path)
        else:
            try:
                os.symlink(source.path.resolve(), stack_path)
            except OSError:
                shutil.copy2(source.path, stack_path)
    else:
        with tifffile.TiffWriter(stack_path, bigtiff=True) as writer:
            for image in source:
                writer.write(image, contiguous=True, photometric="minisblack")

    valid = rec.valid
    n_frames = len(source)
    shape = None
    dtype = None
    for pos, (frame_index, image) in enumerate(zip(rec.index, source, strict=True)):
        if shape is None:
            shape, dtype = image.shape, image.dtype
        out_u8 = (
            _normalize_to_u8(image, normalization)
            if valid.loc[frame_index]
            else np.zeros(image.shape[:2], dtype=np.uint8)
        )
        jpg_path = jpg_dir / f"{pos:06d}.jpg"
        if not cv2.imwrite(str(jpg_path), out_u8, [cv2.IMWRITE_JPEG_QUALITY, int(quality)]):
            raise OSError(f"could not write {jpg_path}")

    info_path = jpg_dir / "conversion_info.txt"
    info_path.write_text(
        f"Original file: {source.path}\n"
        f"Original shape: {(n_frames, *(shape or ()))}\n"
        f"Original dtype: {dtype}\n"
        f"Normalization method: {normalization}\n"
        f"JPG quality: {quality}\n"
        f"Number of frames: {n_frames}\n"
    )

    map_table = pd.DataFrame({
        "frame": np.arange(n_frames, dtype=np.int64),
        "frame_index": rec.index.to_numpy(dtype=np.int64),
        "time_s": rec.time_s.to_numpy(),
        "valid": valid.astype(int).to_numpy(),
    })
    for col in ("z_moved", "x_um", "y_um", "event"):
        if col in rec.frames:
            map_table[col] = rec.frames[col].to_numpy()
    map_path = run_dir / f"{stack_name}_frame_index_map.csv"
    map_table.to_csv(map_path, index=False)

    return {"stack": stack_path, "jpg_dir": jpg_dir, "frame_map": map_path}


def _load_pipeline_csv(csv_path: Path, index: pd.Index) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if "frame" not in df.columns:
        raise ValueError(f"{csv_path} has no 'frame' column")
    first_index = int(index[0]) if len(index) else 0
    df["frame_index"] = first_index + df["frame"].astype(int)
    df = df[df["frame_index"].isin(index)].drop_duplicates("frame_index", keep="last")
    return df.drop(columns=["frame"]).set_index("frame_index")


def join_ria_results(
    rec: Recording,
    head_angles_csv: Path | None = None,
    roi_intensity_csv: Path | None = None,
    channel: str | None = None,
) -> pd.DataFrame:
    """Join RIA-Segmentation pipeline CSVs onto WormsPy's recording timeline and coordinates."""
    table = pd.DataFrame({
        "frame": np.arange(len(rec.index), dtype=np.int64),
        "time_s": rec.time_s.to_numpy(),
        "valid": rec.valid.to_numpy(),
    }, index=rec.index)
    for col in ("z_moved", "x_um", "y_um", "event"):
        if col in rec.frames:
            table[col] = rec.frames[col].to_numpy()

    if head_angles_csv is not None:
        angles = _load_pipeline_csv(Path(head_angles_csv), rec.index)
        table = table.join(angles, how="left")
        target_ch = channel or default_channel(rec)
        try:
            rec._calibrated_camera(target_ch)
            can_project = True
        except ValueError:
            can_project = False
        if can_project:
            for landmark in ("head", "anchor", "body_ref", "tail"):
                cx, cy = f"{landmark}_x", f"{landmark}_y"
                if cx in table.columns and cy in table.columns:
                    pts = table[[cx, cy]].to_numpy(dtype=np.float64)
                    world = rec.plate_um_batch(target_ch, pts)
                    table[f"{landmark}_x_um"] = world[:, 0]
                    table[f"{landmark}_y_um"] = world[:, 1]

    if roi_intensity_csv is not None:
        rois = _load_pipeline_csv(Path(roi_intensity_csv), rec.index)
        extra_cols = [c for c in rois.columns if c not in table.columns]
        table = table.join(rois[extra_cols], how="left")

    return table


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m wormspy.analysis.ria_bridge",
        description="Bridge WormsPy v2 recordings and the RIA-Segmentation pipeline.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    exp = sub.add_parser("export", help="Export a recording or session for RIA-Segmentation")
    exp.add_argument("path", type=Path, help="rec-NNN folder or session folder")
    exp.add_argument("--out", type=Path, required=True, help="RIA results root directory")
    exp.add_argument("--run-id", required=True, help="RUN_ID subfolder name")
    exp.add_argument("--channel", default=None)
    exp.add_argument("--normalization", choices=("minmax", "percentile"), default="minmax")
    exp.add_argument("--copy", action="store_true", help="copy TIFF instead of symlinking")

    jn = sub.add_parser("join", help="Join RIA pipeline CSVs back onto a WormsPy recording")
    jn.add_argument("path", type=Path, help="rec-NNN recording folder")
    jn.add_argument("--head-angles", type=Path, default=None)
    jn.add_argument("--roi-intensity", type=Path, default=None)
    jn.add_argument("--channel", default=None)
    jn.add_argument("--out", type=Path, default=None, help="Output CSV path")

    args = parser.parse_args(argv)
    if args.cmd == "export":
        folders = ([args.path] if (args.path / "frames.csv").exists()
                   else open_session(args.path).recordings)
        for folder in folders:
            with open_recording(folder) as rec:
                out = export_for_ria_pipeline(
                    rec, args.out, args.run_id, channel=args.channel,
                    normalization=args.normalization, copy_tiff=args.copy)
                print(f"{folder.name}: exported -> {out['stack']} & {out['jpg_dir']}",
                      file=sys.stderr)
        return 0

    with open_recording(args.path) as rec:
        joined = join_ria_results(rec, head_angles_csv=args.head_angles,
                                  roi_intensity_csv=args.roi_intensity, channel=args.channel)
        out_path = args.out or (args.path / "analysis" / "ria_joined.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        joined.to_csv(out_path)
        print(f"{args.path.name}: wrote {len(joined)} rows -> {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
