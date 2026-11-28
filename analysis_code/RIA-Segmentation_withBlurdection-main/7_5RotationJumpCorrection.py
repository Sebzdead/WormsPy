"""
Post-correct sudden rotation jumps after 7AlignRIA_ECC.py.

This step does not rerun ECC. It reads:
- 07_ria_aligned/<stack>_aligned.tif
- 07_ria_aligned/<stack>_alignment.csv

It writes:
- 07_5_ria_rotation_fixed/<stack>_aligned.tif
- 07_5_ria_rotation_fixed/<stack>_alignment_rotation_fixed.csv
- 07_5_ria_rotation_fixed/previews/<stack>_preview.jpg

The correction is based on sudden jumps in rotation_raw_deg. Frames at the jump
and a small configurable lookback are rotated back toward the last stable angle.
"""
import argparse
import csv
import os
from collections import Counter

import cv2
import numpy as np
import tifffile
from tqdm import tqdm


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260603"
SOURCE_SUBDIR = "07_ria_aligned"
OUTPUT_SUBDIR = "07_5_ria_rotation_fixed"
PREVIEW_TILE_COUNT = 25


def parse_args():
    parser = argparse.ArgumentParser(description="Fix sudden rotation jumps after ECC alignment.")
    parser.add_argument("--run-id", default=RUN_ID)
    parser.add_argument("--threshold", type=float, default=20.0, help="Raw rotation jump threshold in degrees.")
    parser.add_argument("--lookback", type=int, default=1, help="Also correct this many frames before a jump.")
    parser.add_argument("--only-stack", default="", help="Process one stack name without _aligned.tif.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite 07_ria_aligned outputs instead of writing step 7.5 folder.")
    return parser.parse_args()


def normalize_uint8(image):
    image = np.asarray(image)
    if image.dtype == np.uint8:
        return image
    finite = image[np.isfinite(image)]
    if finite.size == 0:
        return np.zeros(image.shape, dtype=np.uint8)
    lo = float(finite.min())
    hi = float(finite.max())
    if hi <= lo:
        return np.zeros(image.shape, dtype=np.uint8)
    return np.clip((image.astype(np.float32) - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)


def parse_float(value):
    try:
        if value == "":
            return np.nan
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def nearest_equivalent_angle(angle_deg, reference_deg):
    candidates = [angle_deg - 360.0, angle_deg, angle_deg + 360.0]
    return min(candidates, key=lambda value: abs(value - reference_deg))


def rotate_frame_center(frame, angle_deg):
    if not np.isfinite(angle_deg) or abs(float(angle_deg)) < 1e-6:
        return frame
    h, w = frame.shape[:2]
    center = ((w - 1) / 2.0, (h - 1) / 2.0)
    matrix = cv2.getRotationMatrix2D(center, float(angle_deg), 1.0)
    return cv2.warpAffine(
        frame,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )


def make_preview(frames, out_path, max_tiles=PREVIEW_TILE_COUNT):
    if not frames:
        return
    sample = [normalize_uint8(frame) for frame in frames[:max_tiles]]
    h, w = sample[0].shape[:2]
    cols = 5
    rows = int(np.ceil(len(sample) / cols))
    canvas = np.zeros((rows * h, cols * w), dtype=np.uint8)
    for idx, frame in enumerate(sample):
        if frame.ndim == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        y = (idx // cols) * h
        x = (idx % cols) * w
        canvas[y:y + h, x:x + w] = frame
    cv2.imwrite(out_path, canvas)


def read_csv_rows(csv_path):
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    return rows, fieldnames


def write_csv_rows(csv_path, rows, fieldnames):
    extra_fields = sorted({key for row in rows for key in row.keys()} - set(fieldnames))
    fieldnames = list(fieldnames) + extra_fields
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_rotation_jump_corrections(rows, threshold_deg, lookback_frames):
    corrections = [0.0 for _ in rows]
    unwrapped_angles = [np.nan for _ in rows]
    jump_flags = [0 for _ in rows]
    stable_angle = None

    for idx, row in enumerate(rows):
        raw_angle = parse_float(row.get("rotation_raw_deg", ""))
        if row.get("status") != "ok" or not np.isfinite(raw_angle):
            continue

        if stable_angle is None:
            stable_angle = raw_angle
            unwrapped_angles[idx] = raw_angle
            continue

        current_angle = nearest_equivalent_angle(raw_angle, stable_angle)
        delta = current_angle - stable_angle
        unwrapped_angles[idx] = current_angle

        if abs(delta) > threshold_deg:
            correction = stable_angle - current_angle
            corrections[idx] = correction
            jump_flags[idx] = 1
            for lookback in range(1, max(0, lookback_frames) + 1):
                prev_idx = idx - lookback
                if prev_idx < 0:
                    break
                if rows[prev_idx].get("status") == "ok" and abs(corrections[prev_idx]) < 1e-6:
                    corrections[prev_idx] = correction
                    jump_flags[prev_idx] = 1
            continue

        stable_angle = current_angle

    return corrections, unwrapped_angles, jump_flags


def process_stack(stack_name, source_tif, source_csv, out_tif, out_csv, preview_path, threshold_deg, lookback_frames):
    rows, fieldnames = read_csv_rows(source_csv)
    corrections, unwrapped_angles, jump_flags = build_rotation_jump_corrections(rows, threshold_deg, lookback_frames)

    for row, correction, unwrapped, jump_flag in zip(rows, corrections, unwrapped_angles, jump_flags):
        row["rotation_unwrapped_deg"] = f"{unwrapped:.6f}" if np.isfinite(unwrapped) else ""
        row["rotation_jump_detected"] = jump_flag
        row["rotation_post_correction_deg"] = f"{correction:.6f}" if abs(correction) > 1e-6 else ""
        row["rotation_jump_threshold_deg"] = f"{threshold_deg:.6f}"
        row["rotation_jump_lookback_frames"] = lookback_frames

    os.makedirs(os.path.dirname(out_tif), exist_ok=True)
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    preview_frames = []
    corrected_count = 0

    tmp_tif = out_tif + ".tmp"
    with tifffile.TiffFile(source_tif) as tif, tifffile.TiffWriter(tmp_tif, bigtiff=False) as out:
        for idx, page in enumerate(tqdm(tif.pages, total=len(tif.pages), desc=f"Rotation fix {stack_name}", leave=False)):
            frame = page.asarray()
            correction = corrections[idx] if idx < len(corrections) else 0.0
            if abs(correction) > 1e-6:
                corrected_count += 1
            fixed = rotate_frame_center(frame, correction)
            out.write(fixed, contiguous=True)
            if len(preview_frames) < PREVIEW_TILE_COUNT:
                preview_frames.append(fixed)
    os.replace(tmp_tif, out_tif)
    make_preview(preview_frames, preview_path)
    write_csv_rows(out_csv, rows, fieldnames)

    counts = Counter(row.get("rotation_jump_detected", 0) for row in rows)
    print(
        f"[7.5] {stack_name}: corrected={corrected_count}/{len(rows)}, "
        f"jump_marked={counts.get(1, 0)}, threshold={threshold_deg:.1f}, lookback={lookback_frames}"
    )


def main():
    args = parse_args()
    source_dir = os.path.join(RESULTS_ROOT, args.run_id, SOURCE_SUBDIR)
    out_dir = source_dir if args.overwrite else os.path.join(RESULTS_ROOT, args.run_id, OUTPUT_SUBDIR)
    preview_dir = os.path.join(out_dir, "previews")

    if not os.path.isdir(source_dir):
        print(f"No source folder found: {source_dir}")
        return

    names = sorted(name for name in os.listdir(source_dir) if name.endswith("_aligned.tif"))
    if args.only_stack:
        target = f"{args.only_stack}_aligned.tif"
        names = [name for name in names if name == target]

    if not names:
        print(f"No aligned TIFF files found in {source_dir}")
        return

    print(f"Found {len(names)} aligned stack(s). Output: {out_dir}")
    for idx, name in enumerate(names, 1):
        stack_name = name[:-len("_aligned.tif")]
        source_tif = os.path.join(source_dir, name)
        source_csv = os.path.join(source_dir, f"{stack_name}_alignment.csv")
        if not os.path.exists(source_csv):
            print(f"[{idx}/{len(names)}] skip {stack_name}: missing {source_csv}")
            continue
        out_tif = os.path.join(out_dir, name)
        out_csv_name = f"{stack_name}_alignment.csv" if args.overwrite else f"{stack_name}_alignment_rotation_fixed.csv"
        out_csv = os.path.join(out_dir, out_csv_name)
        preview_path = os.path.join(preview_dir, f"{stack_name}_preview.jpg")
        print(f"\n[{idx}/{len(names)}] Processing {stack_name}")
        process_stack(
            stack_name,
            source_tif,
            source_csv,
            out_tif,
            out_csv,
            preview_path,
            args.threshold,
            args.lookback,
        )


if __name__ == "__main__":
    main()
