"""
Train a YOLO detector for RIA prompts from training_data_ria_detector.

The dataset is kept in place. This script writes only:
- training_data_ria_detector/yolo_dataset/train.txt
- training_data_ria_detector/yolo_dataset/val.txt
- training_data_ria_detector/yolo_dataset/data.yaml
- training_runs/ria_detector/*
"""
import argparse
import os
import random
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_ROOT = SCRIPT_DIR / "training_data_ria_detector"
IMAGE_DIR = DATA_ROOT / "images"
LABEL_DIR = DATA_ROOT / "labels_yolo"
ULTRALYTICS_LABEL_DIR = DATA_ROOT / "labels"
SPLIT_DIR = DATA_ROOT / "yolo_dataset"
RUN_DIR = SCRIPT_DIR / "training_runs"


def collect_labeled_images():
    images = sorted(
        p for p in IMAGE_DIR.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    pairs = []
    missing_labels = []
    empty_labels = []
    bad_labels = []

    for image_path in images:
        label_path = LABEL_DIR / f"{image_path.stem}.txt"
        if not label_path.exists():
            missing_labels.append(image_path.name)
            continue
        lines = [line.strip() for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            empty_labels.append(label_path.name)
            continue
        ok = True
        for line in lines:
            parts = line.split()
            if len(parts) != 5:
                ok = False
                break
            try:
                cls = int(float(parts[0]))
                values = [float(v) for v in parts[1:]]
            except ValueError:
                ok = False
                break
            if cls != 0 or any(v < 0.0 or v > 1.0 for v in values):
                ok = False
                break
        if not ok:
            bad_labels.append(label_path.name)
            continue
        pairs.append((image_path, label_path))

    return pairs, missing_labels, empty_labels, bad_labels


def write_split_files(pairs, val_fraction=0.2, seed=245):
    rng = random.Random(seed)
    shuffled = list(pairs)
    rng.shuffle(shuffled)
    val_count = max(1, round(len(shuffled) * val_fraction)) if len(shuffled) > 1 else 0
    val_pairs = shuffled[:val_count]
    train_pairs = shuffled[val_count:]

    SPLIT_DIR.mkdir(parents=True, exist_ok=True)
    train_txt = SPLIT_DIR / "train.txt"
    val_txt = SPLIT_DIR / "val.txt"
    data_yaml = SPLIT_DIR / "data.yaml"
    data_root_posix = str(DATA_ROOT.resolve()).replace("\\", "/")
    train_txt_posix = str(train_txt.resolve()).replace("\\", "/")
    val_txt_posix = str(val_txt.resolve()).replace("\\", "/")

    train_txt.write_text(
        "\n".join(str(image_path.resolve()).replace("\\", "/") for image_path, _ in train_pairs) + "\n",
        encoding="utf-8",
    )
    val_txt.write_text(
        "\n".join(str(image_path.resolve()).replace("\\", "/") for image_path, _ in val_pairs) + "\n",
        encoding="utf-8",
    )
    data_yaml.write_text(
        "\n".join([
            f"path: {data_root_posix}",
            f"train: {train_txt_posix}",
            f"val: {val_txt_posix}",
            "names:",
            "  0: ria",
            "",
        ]),
        encoding="utf-8",
    )
    return train_pairs, val_pairs, data_yaml


def sync_ultralytics_labels(pairs):
    ULTRALYTICS_LABEL_DIR.mkdir(parents=True, exist_ok=True)
    valid_label_names = {label_path.name for _, label_path in pairs}
    for old_label in ULTRALYTICS_LABEL_DIR.glob("*.txt"):
        if old_label.name not in valid_label_names:
            old_label.unlink()
    for _, label_path in pairs:
        target = ULTRALYTICS_LABEL_DIR / label_path.name
        text = label_path.read_text(encoding="utf-8")
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            target.write_text(text, encoding="utf-8")

    for cache_path in DATA_ROOT.glob("labels*.cache"):
        cache_path.unlink()


def train_yolo(data_yaml, model, epochs, imgsz, batch, device, workers, patience):
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "ultralytics is not installed. Install it first with:\n"
            "python -m pip install ultralytics"
        ) from exc

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
        name="ria_detector",
        exist_ok=True,
        single_cls=True,
        plots=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="yolo11n.pt", help="Ultralytics model or local .pt path.")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=float, default=-1, help="-1 lets Ultralytics choose a GPU batch size.")
    parser.add_argument("--device", default=0, help="0 for CUDA GPU, cpu for CPU.")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=245)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()

    pairs, missing_labels, empty_labels, bad_labels = collect_labeled_images()
    print(f"Images with valid labels: {len(pairs)}")
    if missing_labels:
        print(f"Missing labels skipped: {len(missing_labels)}")
    if empty_labels:
        print(f"Empty labels skipped: {len(empty_labels)}")
    if bad_labels:
        print(f"Bad labels skipped: {len(bad_labels)}")
    if len(pairs) < 10:
        raise RuntimeError("Too few labeled images for training.")

    sync_ultralytics_labels(pairs)
    train_pairs, val_pairs, data_yaml = write_split_files(
        pairs,
        val_fraction=args.val_fraction,
        seed=args.seed,
    )
    print(f"Train images: {len(train_pairs)}")
    print(f"Val images: {len(val_pairs)}")
    print(f"Dataset YAML: {data_yaml}")

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
