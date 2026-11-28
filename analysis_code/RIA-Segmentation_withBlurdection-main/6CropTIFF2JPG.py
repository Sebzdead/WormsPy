"""
Convert RIA crop TIFF stacks to normalized JPG frame folders.

Inputs:
- results/<RUN_ID>/04_ria_crop/<stack>_crop.tif

Outputs:
- results/<RUN_ID>/06_crop_jpg/<stack>_crop_jpg/000000.jpg

These JPGs are normalized visualization/registration images. Step 5 ECC uses
them to estimate motion, while aligned TIFF output still uses the original crop
TIFF data.
"""
import os
import sys
import time

import cv2
import numpy as np
import tifffile


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260529"

CROP_SUBDIR = "04_ria_crop"
JPG_CROP_SUBDIR = "06_crop_jpg"

NORMALIZATION = "minmax"
JPG_QUALITY = 100
OVERWRITE_EXISTING = False
PROGRESS_UPDATE_INTERVAL_SEC = 0.5

input_dir = os.path.join(RESULTS_ROOT, RUN_ID, CROP_SUBDIR)
output_root = os.path.join(RESULTS_ROOT, RUN_ID, JPG_CROP_SUBDIR)


def normalize_to_8bit(image, method=NORMALIZATION, global_min=None, global_max=None):
    if image.dtype == np.uint8:
        return image
    image = image.astype(np.float32)
    if method == "global":
        lo, hi = float(global_min), float(global_max)
    elif method == "percentile":
        lo, hi = np.percentile(image, (1, 99))
    else:
        lo, hi = float(image.min()), float(image.max())
    if hi <= lo:
        return np.zeros(image.shape, dtype=np.uint8)
    return np.clip((image - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)


class SingleLineProgress:
    def __init__(self, label, total):
        self.label = label
        self.total = max(int(total), 1)
        self.count = 0
        self.last_update = 0.0
        self.last_len = 0

    def update(self, frame_idx=None, force=False):
        self.count += 1
        now = time.time()
        if not force and now - self.last_update < PROGRESS_UPDATE_INTERVAL_SEC and self.count < self.total:
            return
        self.last_update = now
        percent = min(100.0, 100.0 * self.count / self.total)
        text = f"\r{self.label}: {self.count}/{self.total} ({percent:5.1f}%)"
        if frame_idx is not None:
            text += f" | frame={frame_idx}"
        pad = " " * max(0, self.last_len - len(text))
        sys.stdout.write(text + pad)
        sys.stdout.flush()
        self.last_len = len(text)

    def close(self):
        if self.last_len:
            sys.stdout.write("\r" + " " * self.last_len + "\r")
            sys.stdout.flush()
            self.last_len = 0


def crop_stack_name(crop_file_name):
    if crop_file_name.endswith("_crop.tif"):
        return crop_file_name[:-len("_crop.tif")]
    if crop_file_name.endswith("_crop.tiff"):
        return crop_file_name[:-len("_crop.tiff")]
    return os.path.splitext(crop_file_name)[0]


def output_dir_for_crop(crop_file_name):
    return os.path.join(output_root, f"{crop_stack_name(crop_file_name)}_crop_jpg")


def crop_tiff_files():
    if not os.path.isdir(input_dir):
        return []
    return sorted(
        name for name in os.listdir(input_dir)
        if name.lower().endswith((".tif", ".tiff"))
    )


def output_complete(out_dir, expected_frames):
    info_path = os.path.join(out_dir, "conversion_info.txt")
    if not os.path.exists(info_path):
        return False
    jpg_count = sum(1 for name in os.listdir(out_dir) if name.lower().endswith(".jpg"))
    return jpg_count >= expected_frames


def tiff_shape(path):
    with tifffile.TiffFile(path) as tif:
        series_shape = tif.series[0].shape
        if len(series_shape) == 2:
            return 1, series_shape
        return int(series_shape[0]), tuple(series_shape[1:3])


def global_range(path):
    lo = None
    hi = None
    for _, frame in iter_tiff_frames(path):
        frame_min = float(np.min(frame))
        frame_max = float(np.max(frame))
        lo = frame_min if lo is None else min(lo, frame_min)
        hi = frame_max if hi is None else max(hi, frame_max)
    return lo, hi


def iter_tiff_frames(path):
    with tifffile.TiffFile(path) as tif:
        series_shape = tif.series[0].shape
        if len(series_shape) == 2:
            yield 0, tif.asarray()
            return
        n_frames = int(series_shape[0])
        if len(tif.pages) == n_frames:
            for idx, page in enumerate(tif.pages):
                yield idx, page.asarray()
        else:
            stack = tif.asarray()
            for idx, frame in enumerate(stack):
                yield idx, frame


def convert_crop_tiff(crop_path, out_dir):
    n_frames, shape = tiff_shape(crop_path)
    if not OVERWRITE_EXISTING and os.path.isdir(out_dir) and output_complete(out_dir, n_frames):
        print(f"[skip] {os.path.basename(crop_path)} already converted")
        return True

    os.makedirs(out_dir, exist_ok=True)
    g_min = g_max = None
    if NORMALIZATION == "global":
        g_min, g_max = global_range(crop_path)

    label = f"Crop JPG {os.path.basename(crop_path)}"
    progress = SingleLineProgress(label, n_frames)
    ok = True
    for frame_idx, frame in iter_tiff_frames(crop_path):
        if frame.ndim == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_u8 = normalize_to_8bit(frame, NORMALIZATION, g_min, g_max)
        out_path = os.path.join(out_dir, f"{frame_idx:06d}.jpg")
        if not cv2.imwrite(out_path, frame_u8, [cv2.IMWRITE_JPEG_QUALITY, JPG_QUALITY]):
            ok = False
            print(f"\n[warn] failed to write: {out_path}")
        progress.update(frame_idx=frame_idx)
    progress.close()

    info_path = os.path.join(out_dir, "conversion_info.txt")
    with open(info_path, "w", encoding="utf-8") as f:
        f.write(f"Original file: {crop_path}\n")
        f.write(f"Frame count: {n_frames}\n")
        f.write(f"Frame shape: {shape}\n")
        f.write(f"Normalization: {NORMALIZATION}\n")
        f.write(f"JPG quality: {JPG_QUALITY}\n")
    print(f"[done] {os.path.basename(crop_path)} -> {out_dir}")
    return ok


def main():
    files = crop_tiff_files()
    if not files:
        print(f"No crop TIFF files found in {input_dir}")
        return

    os.makedirs(output_root, exist_ok=True)
    print(f"Input : {input_dir}")
    print(f"Output: {output_root}")
    print(f"Found {len(files)} crop TIFF file(s).")

    successful = 0
    failed = 0
    for idx, file_name in enumerate(files, 1):
        crop_path = os.path.join(input_dir, file_name)
        out_dir = output_dir_for_crop(file_name)
        print(f"\n[{idx}/{len(files)}] {file_name}")
        if convert_crop_tiff(crop_path, out_dir):
            successful += 1
        else:
            failed += 1

    print(f"\nCrop TIFF to JPG complete. successful={successful}, failed={failed}")


if __name__ == "__main__":
    main()
