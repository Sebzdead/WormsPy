"""
Test the trained RIA blur/quality classifier.

Default:
- model: training_runs/ria_blur_classifier/weights/best.pt
- source: training_data_ria_blur_classifier/yolo_cls_dataset/val
- output: training_runs/ria_blur_classifier_test
"""
import argparse
import csv
import os
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_ROOT = SCRIPT_DIR / "training_data_ria_blur_classifier"
DEFAULT_MODEL = SCRIPT_DIR / "training_runs" / "ria_blur_classifier" / "weights" / "best.pt"
DEFAULT_SOURCE = DATA_ROOT / "yolo_cls_dataset" / "val"
DEFAULT_OUTPUT = SCRIPT_DIR / "training_runs" / "ria_blur_classifier_test"
os.environ.setdefault("YOLO_CONFIG_DIR", str(SCRIPT_DIR / "Ultralytics"))


def collect_images(source):
    source = Path(source)
    if source.is_file():
        return [source]
    if not source.is_dir():
        raise FileNotFoundError(source)
    return sorted(
        p for p in source.rglob("*")
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )


def true_label_from_path(path):
    parent = Path(path).parent.name.lower()
    if parent in {"good", "bad"}:
        return parent
    return ""


def laplacian_score(image):
    if image is None or image.size == 0:
        return 0.0
    return float(cv2.Laplacian(image, cv2.CV_64F).var())


def save_preview(image_path, output_path, true_label, pred_label, conf, lap):
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return
    display = cv2.applyColorMap(image, cv2.COLORMAP_INFERNO)
    scale = 5
    display = cv2.resize(display, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    panel = np.zeros((72, display.shape[1], 3), dtype=np.uint8)
    color = (80, 255, 120) if true_label == pred_label else (80, 80, 255)
    cv2.putText(panel, f"true={true_label or '?'} pred={pred_label} conf={conf:.3f}", (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    cv2.putText(panel, f"laplacian={lap:.3f}", (6, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    out = np.vstack([panel, display])
    cv2.imwrite(str(output_path), out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--imgsz", type=int, default=64)
    parser.add_argument("--preview-limit", type=int, default=200)
    args = parser.parse_args()

    from ultralytics import YOLO

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(model_path)
    images = collect_images(args.source)
    if not images:
        raise RuntimeError(f"No images found: {args.source}")

    output_dir = Path(args.output)
    preview_dir = output_dir / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(model_path))
    results = model.predict(
        source=[str(p) for p in images],
        imgsz=args.imgsz,
        device=args.device,
        verbose=False,
        stream=False,
    )

    rows = []
    correct = 0
    labeled = 0
    confusion = {}
    for idx, (image_path, result) in enumerate(zip(images, results)):
        true_label = true_label_from_path(image_path)
        names = result.names
        probs = result.probs
        top_idx = int(probs.top1)
        pred_label = names[top_idx] if isinstance(names, dict) else str(top_idx)
        conf = float(probs.top1conf)
        prob_by_label = {}
        for cls_idx, cls_name in names.items():
            prob_by_label[str(cls_name)] = float(probs.data[int(cls_idx)])
        prob_bad = prob_by_label.get("bad", np.nan)
        prob_good = prob_by_label.get("good", np.nan)
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        lap = laplacian_score(image)
        if true_label:
            labeled += 1
            correct += int(true_label == pred_label)
            confusion[(true_label, pred_label)] = confusion.get((true_label, pred_label), 0) + 1
        preview_path = ""
        if idx < args.preview_limit:
            preview_path = preview_dir / f"{idx:05d}_{true_label or 'unknown'}_pred_{pred_label}_{image_path.name}"
            save_preview(image_path, preview_path, true_label, pred_label, conf, lap)
        rows.append({
            "image": str(image_path),
            "true_label": true_label,
            "pred_label": pred_label,
            "confidence": f"{conf:.6f}",
            "prob_bad": f"{prob_bad:.6f}" if np.isfinite(prob_bad) else "",
            "prob_good": f"{prob_good:.6f}" if np.isfinite(prob_good) else "",
            "laplacian_score": f"{lap:.6f}",
            "correct": int(true_label == pred_label) if true_label else "",
            "preview": str(preview_path),
        })

    csv_path = output_dir / "predictions.csv"
    fields = ["image", "true_label", "pred_label", "confidence", "prob_bad", "prob_good", "laplacian_score", "correct", "preview"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    sweep_rows = []
    labeled_rows = [row for row in rows if row["true_label"] in {"good", "bad"} and row["prob_bad"]]
    for threshold in np.linspace(0.05, 0.95, 19):
        tp = fp = tn = fn = 0
        for row in labeled_rows:
            true_bad = row["true_label"] == "bad"
            pred_bad = float(row["prob_bad"]) >= threshold
            if true_bad and pred_bad:
                tp += 1
            elif true_bad and not pred_bad:
                fn += 1
            elif not true_bad and pred_bad:
                fp += 1
            else:
                tn += 1
        bad_recall = tp / (tp + fn) if (tp + fn) else np.nan
        good_keep = tn / (tn + fp) if (tn + fp) else np.nan
        accuracy_thr = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) else np.nan
        sweep_rows.append({
            "bad_threshold": f"{threshold:.3f}",
            "bad_recall": f"{bad_recall:.6f}",
            "good_keep_rate": f"{good_keep:.6f}",
            "accuracy": f"{accuracy_thr:.6f}",
            "tp_bad": tp,
            "fn_bad": fn,
            "fp_good_as_bad": fp,
            "tn_good": tn,
        })
    sweep_path = output_dir / "threshold_sweep.csv"
    with sweep_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["bad_threshold", "bad_recall", "good_keep_rate", "accuracy", "tp_bad", "fn_bad", "fp_good_as_bad", "tn_good"])
        writer.writeheader()
        writer.writerows(sweep_rows)

    if sweep_rows:
        x = np.array([float(row["bad_threshold"]) for row in sweep_rows])
        bad_recall = np.array([float(row["bad_recall"]) for row in sweep_rows])
        good_keep = np.array([float(row["good_keep_rate"]) for row in sweep_rows])
        acc = np.array([float(row["accuracy"]) for row in sweep_rows])
        plt.figure(figsize=(8, 5))
        plt.plot(x, bad_recall, marker="o", label="bad recall")
        plt.plot(x, good_keep, marker="o", label="good keep")
        plt.plot(x, acc, marker="o", label="accuracy")
        plt.xlabel("P(bad) threshold")
        plt.ylabel("Rate")
        plt.ylim(0, 1.02)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "threshold_sweep.png", dpi=180)
        plt.close()

    print(f"Images: {len(images)}")
    if labeled:
        print(f"Accuracy: {correct}/{labeled} = {correct / labeled:.3f}")
        print("Confusion:")
        for key, value in sorted(confusion.items()):
            print(f"  true={key[0]} pred={key[1]}: {value}")
    print(f"CSV: {csv_path}")
    print(f"Threshold sweep: {sweep_path}")
    print(f"Previews: {preview_dir}")


if __name__ == "__main__":
    main()
