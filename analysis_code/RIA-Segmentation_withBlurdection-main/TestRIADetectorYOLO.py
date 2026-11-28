"""
Quick visual test for the trained RIA YOLO detector.

Default behavior:
- loads training_runs/ria_detector/weights/best.pt
- samples JPG frames from results/<RUN_ID>/02_tiff_jpg
- saves prediction overlays and a CSV summary to training_runs/ria_detector_test
"""
import argparse
import csv
import os
import random
from pathlib import Path

import cv2


SCRIPT_DIR = Path(__file__).resolve().parent
RUN_ID = "20260529"
DEFAULT_MODEL = SCRIPT_DIR / "training_runs" / "ria_detector" / "weights" / "best.pt"
DEFAULT_SOURCE = SCRIPT_DIR / "results" / RUN_ID / "02_tiff_jpg"
DEFAULT_OUTPUT = SCRIPT_DIR / "training_runs" / "ria_detector_test"
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


def sample_images(images, n, seed):
    if n <= 0 or n >= len(images):
        return images
    rng = random.Random(seed)
    return sorted(rng.sample(images, n))


def draw_predictions(image, result, conf_threshold):
    rows = []
    names = result.names
    boxes = result.boxes
    if boxes is None:
        return image, rows

    for det_idx, box in enumerate(boxes):
        conf = float(box.conf[0])
        if conf < conf_threshold:
            continue
        cls = int(box.cls[0])
        x1, y1, x2, y2 = [int(round(v)) for v in box.xyxy[0].tolist()]
        label = names.get(cls, str(cls)) if isinstance(names, dict) else str(cls)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        text = f"{label} {conf:.3f}"
        cv2.putText(image, text, (x1, max(18, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
        rows.append({
            "det_idx": det_idx,
            "class": cls,
            "label": label,
            "conf": f"{conf:.6f}",
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "width": x2 - x1,
            "height": y2 - y1,
        })
    return image, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--seed", type=int, default=245)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="cpu", help="Use cpu while training is running, or 0 for CUDA.")
    args = parser.parse_args()

    from ultralytics import YOLO

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(model_path)

    output_dir = Path(args.output)
    overlay_dir = output_dir / "overlays"
    overlay_dir.mkdir(parents=True, exist_ok=True)

    images = collect_images(args.source)
    selected = sample_images(images, args.n, args.seed)
    if not selected:
        raise RuntimeError(f"No images found in {args.source}")

    print(f"Model: {model_path}")
    print(f"Source images: {len(images)}")
    print(f"Testing images: {len(selected)}")
    print(f"Output: {output_dir}")

    model = YOLO(str(model_path))
    results = model.predict(
        source=[str(p) for p in selected],
        imgsz=args.imgsz,
        conf=args.conf,
        device=args.device,
        verbose=False,
        stream=False,
    )

    csv_rows = []
    for image_path, result in zip(selected, results):
        image = cv2.imread(str(image_path))
        if image is None:
            continue
        overlay, detections = draw_predictions(image, result, args.conf)
        relative_name = "_".join(image_path.parts[-2:]) if image_path.parent != Path(args.source) else image_path.name
        overlay_path = overlay_dir / relative_name
        cv2.imwrite(str(overlay_path), overlay)
        if not detections:
            csv_rows.append({
                "image": str(image_path),
                "overlay": str(overlay_path),
                "det_idx": "",
                "class": "",
                "label": "",
                "conf": "",
                "x1": "",
                "y1": "",
                "x2": "",
                "y2": "",
                "width": "",
                "height": "",
            })
        else:
            for det in detections:
                row = {"image": str(image_path), "overlay": str(overlay_path)}
                row.update(det)
                csv_rows.append(row)

    csv_path = output_dir / "predictions.csv"
    fields = ["image", "overlay", "det_idx", "class", "label", "conf", "x1", "y1", "x2", "y2", "width", "height"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(csv_rows)

    detected_images = len({row["image"] for row in csv_rows if row["conf"]})
    print(f"Images with detections: {detected_images}/{len(selected)}")
    print(f"CSV: {csv_path}")
    print(f"Overlays: {overlay_dir}")


if __name__ == "__main__":
    main()
