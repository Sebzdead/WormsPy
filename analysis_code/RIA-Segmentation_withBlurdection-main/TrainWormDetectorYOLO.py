"""
Train a YOLO detector for whole-worm SAM2 prompts.

This builds training data from existing outputs:
- results/<RUN_ID>/02_tiff_jpg/<stack>/<frame>.jpg
- results/<RUN_ID>/03_worm_segmentation/<stack>/masks/<frame>_worm_mask.png

The detector is used only to propose a box prompt for 3SegmentWorm.py, so bbox
labels generated from existing masks are enough.
"""
import argparse
import csv
import os
import random
import shutil
from pathlib import Path

import cv2


SCRIPT_DIR = Path(__file__).resolve().parent
RUN_ID = "20260529"
RESULTS_ROOT = SCRIPT_DIR / "results" / RUN_ID
JPG_ROOT = RESULTS_ROOT / "02_tiff_jpg"
WORM_SEG_ROOT = RESULTS_ROOT / "03_worm_segmentation"
DATA_ROOT = SCRIPT_DIR / "training_data_worm_detector"
IMAGE_DIR = DATA_ROOT / "images"
LABEL_DIR = DATA_ROOT / "labels"
SPLIT_DIR = DATA_ROOT / "yolo_dataset"
RUN_DIR = SCRIPT_DIR / "training_runs"
os.environ.setdefault("YOLO_CONFIG_DIR", str(SCRIPT_DIR / "Ultralytics"))


def parse_batch(value):
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip()
    try:
        number = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid batch value: {value}") from exc
    if number.is_integer():
        return int(number)
    return number


def bbox_from_mask(mask_path, min_area):
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return None
    ys, xs = (mask > 0).nonzero()
    area = int(len(xs))
    if area < min_area:
        return None
    h, w = mask.shape[:2]
    x1 = int(xs.min())
    x2 = int(xs.max()) + 1
    y1 = int(ys.min())
    y2 = int(ys.max()) + 1
    if x2 <= x1 or y2 <= y1:
        return None
    cx = ((x1 + x2) / 2.0) / w
    cy = ((y1 + y2) / 2.0) / h
    bw = (x2 - x1) / w
    bh = (y2 - y1) / h
    return x1, y1, x2, y2, area, f"0 {cx:.8f} {cy:.8f} {bw:.8f} {bh:.8f}\n"


def collect_mask_pairs(frame_interval, min_area):
    pairs = []
    for stack_dir in sorted(WORM_SEG_ROOT.iterdir()):
        if not stack_dir.is_dir():
            continue
        stack_name = stack_dir.name
        jpg_dir = JPG_ROOT / stack_name
        mask_dir = stack_dir / "masks"
        if not jpg_dir.is_dir() or not mask_dir.is_dir():
            continue
        for mask_path in sorted(mask_dir.glob("*_worm_mask.png")):
            stem = mask_path.name.split("_worm_mask.png")[0]
            if not stem.isdigit():
                continue
            frame_idx = int(stem)
            if frame_interval > 1 and frame_idx % frame_interval != 0:
                continue
            image_path = jpg_dir / f"{frame_idx:06d}.jpg"
            if not image_path.exists():
                continue
            bbox = bbox_from_mask(mask_path, min_area)
            if bbox is None:
                continue
            pairs.append({
                "stack": stack_name,
                "frame": frame_idx,
                "image": image_path,
                "mask": mask_path,
                "bbox": bbox,
            })
    return pairs


def safe_sample(pairs, max_images, seed):
    if max_images <= 0 or len(pairs) <= max_images:
        return pairs
    rng = random.Random(seed)
    return sorted(rng.sample(pairs, max_images), key=lambda row: (row["stack"], row["frame"]))


def link_or_copy(src, dst):
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def write_dataset(pairs, val_fraction, seed):
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    SPLIT_DIR.mkdir(parents=True, exist_ok=True)

    dataset_rows = []
    for row in pairs:
        sample_name = f"{row['stack']}_{row['frame']:06d}"
        image_dst = IMAGE_DIR / f"{sample_name}.jpg"
        label_dst = LABEL_DIR / f"{sample_name}.txt"
        link_or_copy(row["image"], image_dst)
        label_dst.write_text(row["bbox"][-1], encoding="utf-8")
        dataset_rows.append({
            "sample": sample_name,
            "stack": row["stack"],
            "frame": row["frame"],
            "source_image": str(row["image"]),
            "source_mask": str(row["mask"]),
            "image": str(image_dst),
            "label": str(label_dst),
            "area": row["bbox"][4],
        })

    rng = random.Random(seed)
    shuffled = list(dataset_rows)
    rng.shuffle(shuffled)
    val_count = max(1, round(len(shuffled) * val_fraction)) if len(shuffled) > 1 else 0
    val_rows = shuffled[:val_count]
    train_rows = shuffled[val_count:]

    train_txt = SPLIT_DIR / "train.txt"
    val_txt = SPLIT_DIR / "val.txt"
    data_yaml = SPLIT_DIR / "data.yaml"
    summary_csv = DATA_ROOT / "dataset_summary.csv"

    train_txt.write_text(
        "\n".join(Path(row["image"]).resolve().as_posix() for row in train_rows) + "\n",
        encoding="utf-8",
    )
    val_txt.write_text(
        "\n".join(Path(row["image"]).resolve().as_posix() for row in val_rows) + "\n",
        encoding="utf-8",
    )
    data_yaml.write_text(
        "\n".join([
            f"path: {DATA_ROOT.resolve().as_posix()}",
            f"train: {train_txt.resolve().as_posix()}",
            f"val: {val_txt.resolve().as_posix()}",
            "names:",
            "  0: worm",
            "",
        ]),
        encoding="utf-8",
    )

    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        fields = ["sample", "stack", "frame", "source_image", "source_mask", "image", "label", "area"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(dataset_rows)

    for cache_path in DATA_ROOT.glob("labels*.cache"):
        cache_path.unlink()
    return train_rows, val_rows, data_yaml, summary_csv


def train_yolo(data_yaml, model, epochs, imgsz, batch, device, workers, patience):
    from ultralytics import YOLO

    yolo = YOLO(model)
    return yolo.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        workers=workers,
        patience=patience,
        project=str(RUN_DIR),
        name="worm_detector",
        exist_ok=True,
        single_cls=True,
        plots=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=parse_batch, default=-1)
    parser.add_argument("--device", default=0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--frame-interval", type=int, default=10)
    parser.add_argument("--max-images", type=int, default=6000)
    parser.add_argument("--min-area", type=int, default=500)
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=245)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()

    pairs = collect_mask_pairs(args.frame_interval, args.min_area)
    pairs = safe_sample(pairs, args.max_images, args.seed)
    if len(pairs) < 10:
        raise RuntimeError("Too few worm masks for training.")

    train_rows, val_rows, data_yaml, summary_csv = write_dataset(pairs, args.val_fraction, args.seed)
    print(f"Dataset images: {len(pairs)}")
    print(f"Train images: {len(train_rows)}")
    print(f"Val images: {len(val_rows)}")
    print(f"Dataset YAML: {data_yaml}")
    print(f"Summary CSV: {summary_csv}")

    if args.prepare_only:
        return

    train_yolo(
        data_yaml=data_yaml,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        patience=args.patience,
    )


if __name__ == "__main__":
    main()
