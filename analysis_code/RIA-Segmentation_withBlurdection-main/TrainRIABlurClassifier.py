"""
Train a YOLO image classifier for RIA crop quality.

Input:
- training_data_ria_blur_classifier/good/*.jpg
- training_data_ria_blur_classifier/bad/*.jpg

The unsure class is ignored.

Outputs:
- training_data_ria_blur_classifier/yolo_cls_dataset/
- training_runs/ria_blur_classifier/
"""
import argparse
import os
import random
import shutil
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_ROOT = SCRIPT_DIR / "training_data_ria_blur_classifier"
RUN_DIR = SCRIPT_DIR / "training_runs"
DATASET_DIR = DATA_ROOT / "yolo_cls_dataset"
CLASSES = ("bad", "good")
os.environ.setdefault("YOLO_CONFIG_DIR", str(SCRIPT_DIR / "Ultralytics"))


def collect_images():
    items = []
    for label in CLASSES:
        folder = DATA_ROOT / label
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                items.append((path, label))
    return items


def rebuild_dataset(items, val_fraction, seed):
    if DATASET_DIR.exists():
        shutil.rmtree(DATASET_DIR)
    rng = random.Random(seed)
    by_label = {label: [] for label in CLASSES}
    for path, label in items:
        by_label[label].append(path)

    train_count = 0
    val_count = 0
    for label, paths in by_label.items():
        rng.shuffle(paths)
        n_val = max(1, round(len(paths) * val_fraction)) if len(paths) > 1 else 0
        splits = {
            "val": paths[:n_val],
            "train": paths[n_val:],
        }
        for split, split_paths in splits.items():
            out_dir = DATASET_DIR / split / label
            out_dir.mkdir(parents=True, exist_ok=True)
            for src in split_paths:
                dst = out_dir / src.name
                shutil.copy2(src, dst)
            if split == "train":
                train_count += len(split_paths)
            else:
                val_count += len(split_paths)
    return train_count, val_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="yolo11n-cls.pt")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--imgsz", type=int, default=64)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--device", default="0")
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=245)
    parser.add_argument("--patience", type=int, default=12)
    args = parser.parse_args()

    items = collect_images()
    counts = {label: sum(1 for _, item_label in items if item_label == label) for label in CLASSES}
    print(f"Label counts: {counts}")
    if counts["good"] < 10 or counts["bad"] < 10:
        raise RuntimeError("Need at least 10 good and 10 bad images.")

    train_count, val_count = rebuild_dataset(items, args.val_fraction, args.seed)
    print(f"Dataset: {DATASET_DIR}")
    print(f"Train images: {train_count}, val images: {val_count}")

    from ultralytics import YOLO

    model = YOLO(args.model)
    model.train(
        data=str(DATASET_DIR),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=str(RUN_DIR),
        name="ria_blur_classifier",
        patience=args.patience,
        exist_ok=True,
    )


if __name__ == "__main__":
    main()
