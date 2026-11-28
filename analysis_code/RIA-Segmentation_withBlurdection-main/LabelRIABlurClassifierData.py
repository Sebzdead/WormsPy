"""
Manually label RIA crop frames for a good/bad frame classifier.

Input:
- results/<RUN_ID>/06_crop_jpg/*_crop_jpg/*.jpg

Output:
- training_data_ria_blur_classifier/good/*.jpg
- training_data_ria_blur_classifier/bad/*.jpg
- training_data_ria_blur_classifier/unsure/*.jpg
- training_data_ria_blur_classifier/labels.csv

Keys:
- g: good / usable
- b: bad / blurry / ghost / missing / unstable
- u: unsure
- s: skip without saving
- q or Esc: quit
"""
import argparse
import csv
import os
import random
import shutil

import cv2
import numpy as np


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260529"
JPG_CROP_SUBDIR = "06_crop_jpg"
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "training_data_ria_blur_classifier")


def collect_images(source_dir):
    images = []
    if not os.path.isdir(source_dir):
        return images
    for root, _, files in os.walk(source_dir):
        for name in files:
            if name.lower().endswith((".jpg", ".jpeg", ".png")):
                images.append(os.path.join(root, name))
    return sorted(images)


def existing_labeled_sources(labels_path):
    labeled = set()
    if not os.path.exists(labels_path):
        return labeled
    with open(labels_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            src = row.get("source_path")
            if src:
                labeled.add(os.path.normcase(os.path.abspath(src)))
    return labeled


def normalize_display(image, scale):
    if image is None:
        return None
    if image.ndim == 2:
        display = cv2.applyColorMap(image, cv2.COLORMAP_INFERNO)
    else:
        display = image.copy()
    if scale != 1.0:
        display = cv2.resize(display, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    return display


def put_panel(image, text_lines):
    out = image.copy()
    panel_h = 92
    panel = np.zeros((panel_h, out.shape[1], 3), dtype=np.uint8)
    y = 22
    for line in text_lines:
        cv2.putText(panel, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)
        y += 22
    return np.vstack([panel, out])


def laplacian_score(image):
    if image is None or image.size == 0:
        return 0.0
    return float(cv2.Laplacian(image, cv2.CV_64F).var())


def safe_name(path):
    rel = os.path.relpath(path, os.path.join(RESULTS_ROOT, RUN_ID, JPG_CROP_SUBDIR))
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in rel)


def append_label(labels_path, row):
    exists = os.path.exists(labels_path)
    fields = ["source_path", "label", "laplacian_score", "saved_path"]
    with open(labels_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def save_labeled_image(source_path, label, output_dir):
    label_dir = os.path.join(output_dir, label)
    os.makedirs(label_dir, exist_ok=True)
    dst = os.path.join(label_dir, safe_name(source_path))
    if not os.path.exists(dst):
        shutil.copy2(source_path, dst)
    return dst


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=RUN_ID)
    parser.add_argument("--source-dir", default="")
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--shuffle", dest="shuffle", action="store_true", default=True)
    parser.add_argument("--no-shuffle", dest="shuffle", action="store_false")
    parser.add_argument("--seed", type=int, default=245)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--scale", type=float, default=5.0)
    parser.add_argument("--include-labeled", action="store_true")
    args = parser.parse_args()

    source_dir = args.source_dir or os.path.join(RESULTS_ROOT, args.run_id, JPG_CROP_SUBDIR)
    labels_path = os.path.join(args.output_dir, "labels.csv")
    os.makedirs(args.output_dir, exist_ok=True)
    for label in ("good", "bad", "unsure"):
        os.makedirs(os.path.join(args.output_dir, label), exist_ok=True)

    images = collect_images(source_dir)
    if not args.include_labeled:
        labeled = existing_labeled_sources(labels_path)
        images = [p for p in images if os.path.normcase(os.path.abspath(p)) not in labeled]
    if args.shuffle:
        rng = random.Random(args.seed)
        rng.shuffle(images)
    if args.limit > 0:
        images = images[:args.limit]
    if not images:
        print(f"No images to label in {source_dir}")
        return

    window_name = "RIA blur classifier labeling"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    counts = {"good": 0, "bad": 0, "unsure": 0, "skip": 0}

    for idx, path in enumerate(images, 1):
        image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            continue
        blur_score = laplacian_score(image)
        display = normalize_display(image, args.scale)
        text = [
            f"{idx}/{len(images)}  {os.path.basename(path)}",
            f"Laplacian score: {blur_score:.3f}  display: thermal LUT",
            "g=good   b=bad/blurry/ghost/missing   u=unsure   s=skip   q=quit",
            f"counts good={counts['good']} bad={counts['bad']} unsure={counts['unsure']} skip={counts['skip']}",
        ]
        shown = put_panel(display, text)
        cv2.imshow(window_name, shown)
        key = cv2.waitKey(0) & 0xFF

        if key in (ord("q"), 27):
            break
        if key == ord("g"):
            label = "good"
        elif key == ord("b"):
            label = "bad"
        elif key == ord("u"):
            label = "unsure"
        elif key == ord("s"):
            counts["skip"] += 1
            continue
        else:
            counts["skip"] += 1
            continue

        saved_path = save_labeled_image(path, label, args.output_dir)
        append_label(labels_path, {
            "source_path": os.path.abspath(path),
            "label": label,
            "laplacian_score": f"{blur_score:.6f}",
            "saved_path": os.path.abspath(saved_path),
        })
        counts[label] += 1

    cv2.destroyAllWindows()
    print(f"Labels saved to: {labels_path}")
    print(f"Counts: {counts}")


if __name__ == "__main__":
    main()
