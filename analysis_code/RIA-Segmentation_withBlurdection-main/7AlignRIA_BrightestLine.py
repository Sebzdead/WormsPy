"""
Align RIA crops using the brightest line inside the RIA mask.

This is an alternative step 7. It does not modify 7AlignRIA_ECC.py.

Inputs:
- 04_ria_crop/<stack>_crop.tif
- 06_crop_jpg/<stack>_crop_jpg/*.jpg, used for normalized direction detection
- 04_ria_mask/<stack>_ria_mask.tif

Outputs:
- 07_ria_aligned_brightest_line/<stack>_aligned.tif
- 07_ria_aligned_brightest_line/<stack>_alignment.csv
- 07_ria_aligned_brightest_line/previews/<stack>_max_projection.jpg
- 07_ria_aligned_brightest_line/debug/<stack>/*.jpg
"""
import argparse
import csv
import os
from collections import Counter

import cv2
import numpy as np
import tifffile


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260603"

CROP_SUBDIR = "04_ria_crop"
JPG_CROP_SUBDIR = "06_crop_jpg"
RIA_MASK_SUBDIR = "04_ria_mask"
ALIGNED_SUBDIR = "07_ria_aligned_brightest_line"

TARGET_ANGLE_DEG = 0.0
TARGET_LINE_SIDE = "above"
MASK_DILATE_ITERATIONS = 1
SOMA_RADIUS = 6
MIN_PIXELS = 8
STRIPE_RADIUS = 1.25
ANGLE_STEP_DEG = 2.0
DEBUG_EVERY_N_FRAMES = 200
DEBUG_FIRST_OK_FRAMES = 20
WRITE_DEBUG = True

USE_RIA_BLUR_CLASSIFIER = True
RIA_BLUR_CLASSIFIER_PATH = os.path.join(SCRIPT_DIR, "training_runs", "ria_blur_classifier", "weights", "best.pt")
RIA_BLUR_CLASSIFIER_DEVICE = "cpu"
RIA_BLUR_CLASSIFIER_IMGSZ = 64
RIA_BLUR_BAD_THRESHOLD = 0.35
USE_CLAHE_FOR_BLUR_CLASSIFIER = False

crop_dir = os.path.join(RESULTS_ROOT, RUN_ID, CROP_SUBDIR)
jpg_crop_dir = os.path.join(RESULTS_ROOT, RUN_ID, JPG_CROP_SUBDIR)
ria_mask_dir = os.path.join(RESULTS_ROOT, RUN_ID, RIA_MASK_SUBDIR)
aligned_dir = os.path.join(RESULTS_ROOT, RUN_ID, ALIGNED_SUBDIR)


def normalize_uint8(image):
    image = np.squeeze(image)
    if image.dtype == np.uint8:
        return image
    image = image.astype(np.float32)
    lo, hi = np.percentile(image, (1, 99))
    if hi <= lo:
        lo, hi = float(image.min()), float(image.max())
    if hi <= lo:
        return np.zeros(image.shape, dtype=np.uint8)
    return (np.clip((image - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)


_ria_blur_classifier = None


def get_ria_blur_classifier():
    global _ria_blur_classifier
    if not USE_RIA_BLUR_CLASSIFIER:
        return None
    if _ria_blur_classifier is not None:
        return _ria_blur_classifier
    if not os.path.exists(RIA_BLUR_CLASSIFIER_PATH):
        print(f"[blur cls] model not found; classifier disabled: {RIA_BLUR_CLASSIFIER_PATH}")
        return None
    os.environ.setdefault("YOLO_CONFIG_DIR", os.path.join(SCRIPT_DIR, "Ultralytics"))
    try:
        from ultralytics import YOLO
        _ria_blur_classifier = YOLO(RIA_BLUR_CLASSIFIER_PATH)
        print(f"[blur cls] loaded: {RIA_BLUR_CLASSIFIER_PATH}")
    except Exception as exc:
        print(f"[blur cls] could not load classifier; disabled. {exc}")
        _ria_blur_classifier = None
    return _ria_blur_classifier


def classify_ria_frame_quality(image):
    model = get_ria_blur_classifier()
    if model is None or image is None:
        return "", np.nan, np.nan
    image = normalize_uint8(image)
    try:
        results = model.predict(
            source=image,
            imgsz=RIA_BLUR_CLASSIFIER_IMGSZ,
            device=RIA_BLUR_CLASSIFIER_DEVICE,
            verbose=False,
            stream=False,
        )
    except Exception as exc:
        print(f"[blur cls] prediction failed: {exc}")
        return "", np.nan, np.nan
    if not results:
        return "", np.nan, np.nan
    result = results[0]
    names = result.names
    probs = result.probs
    if probs is None:
        return "", np.nan, np.nan
    top_idx = int(probs.top1)
    label = names[top_idx] if isinstance(names, dict) else str(top_idx)
    prob_by_label = {}
    if isinstance(names, dict):
        for cls_idx, cls_name in names.items():
            prob_by_label[str(cls_name)] = float(probs.data[int(cls_idx)])
    return str(label), prob_by_label.get("bad", np.nan), prob_by_label.get("good", np.nan)


def stack_name_from_crop(name):
    return name[:-len("_crop.tif")]


def crop_stack_files():
    if not os.path.isdir(crop_dir):
        return []
    return sorted(f for f in os.listdir(crop_dir) if f.endswith("_crop.tif"))


def read_crop_jpg(stack_name, frame_idx, shape):
    folder = os.path.join(jpg_crop_dir, f"{stack_name}_crop_jpg")
    for name in (f"{frame_idx:06d}.jpg", f"{frame_idx}.jpg"):
        path = os.path.join(folder, name)
        if os.path.exists(path):
            image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if image is not None:
                if image.shape[:2] != shape:
                    image = cv2.resize(image, (shape[1], shape[0]), interpolation=cv2.INTER_AREA)
                return image
    return None


def preprocess_for_direction(image):
    image = normalize_uint8(image)
    bg = cv2.GaussianBlur(image, (0, 0), 8)
    flat = cv2.subtract(image, bg)
    flat = normalize_uint8(flat)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    return clahe.apply(flat)


def pca_elongation(points):
    centered = points - points.mean(axis=0)
    cov = centered.T @ centered / max(len(points) - 1, 1)
    eigvals, _ = np.linalg.eigh(cov)
    eigvals = np.sort(eigvals)[::-1]
    return float(eigvals[0] / (eigvals[1] + 1e-6))


def brightest_line_in_mask(proc, residual_mask):
    ys, xs = np.where(residual_mask)
    if len(xs) < MIN_PIXELS:
        return None

    points = np.column_stack([xs.astype(np.float32), ys.astype(np.float32)])
    weights = proc[ys, xs].astype(np.float32) + 1.0
    center = np.average(points, axis=0, weights=weights)

    best = None
    best_score = -1.0
    for angle_deg in np.arange(0.0, 180.0, ANGLE_STEP_DEG):
        theta = np.deg2rad(angle_deg)
        direction = np.array([np.cos(theta), np.sin(theta)], dtype=np.float32)
        normal = np.array([-direction[1], direction[0]], dtype=np.float32)
        signed_dist = (points - center) @ normal
        lo, hi = np.percentile(signed_dist, (5, 95))
        for offset in np.linspace(lo, hi, 31):
            in_stripe = np.abs(signed_dist - offset) <= STRIPE_RADIUS
            count = int(in_stripe.sum())
            if count < MIN_PIXELS:
                continue
            stripe_weights = weights[in_stripe]
            score = float(stripe_weights.mean() * np.sqrt(count))
            if score <= best_score:
                continue
            stripe_points = points[in_stripe]
            proj = (stripe_points - center) @ direction
            p1 = center + direction * float(proj.min())
            p2 = center + direction * float(proj.max())
            best = {
                "center": center + normal * float(offset),
                "direction": direction,
                "p1": p1,
                "p2": p2,
                "points": stripe_points,
                "score": score,
                "count": count,
                "scan_angle_deg": float(angle_deg),
            }
            best_score = score
    return best


def estimate_direction(image_for_detection, mask):
    image_for_detection = normalize_uint8(image_for_detection)
    mask = np.squeeze(mask)
    if mask.ndim != 2:
        return {"status": "bad_mask"}
    if mask.shape[:2] != image_for_detection.shape[:2]:
        mask = cv2.resize(mask.astype(np.uint8), (image_for_detection.shape[1], image_for_detection.shape[0]), interpolation=cv2.INTER_NEAREST)
    mask = (mask > 0).astype(np.uint8)
    if int(mask.sum()) < MIN_PIXELS:
        return {"status": "mask_too_small"}
    if MASK_DILATE_ITERATIONS > 0:
        kernel = np.ones((3, 3), dtype=np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=MASK_DILATE_ITERATIONS)

    proc = preprocess_for_direction(image_for_detection)
    masked_values = proc[mask > 0]
    if masked_values.size < MIN_PIXELS:
        return {"status": "no_signal"}

    high_thr = np.percentile(masked_values, 90)
    high = ((proc >= high_thr) & (mask > 0)).astype(np.uint8)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(high, 8)
    if n_labels <= 1:
        return {"status": "no_soma"}

    soma = None
    best_score = -1.0
    for label_id in range(1, n_labels):
        area = int(stats[label_id, cv2.CC_STAT_AREA])
        if area < 1:
            continue
        cx, cy = centroids[label_id]
        score = float(proc[labels == label_id].mean()) * np.sqrt(area)
        if score > best_score:
            best_score = score
            soma = (float(cx), float(cy))
    if soma is None:
        return {"status": "no_soma"}

    yy, xx = np.indices(image_for_detection.shape[:2])
    soma_disk = (xx - soma[0]) ** 2 + (yy - soma[1]) ** 2 <= SOMA_RADIUS ** 2
    residual_mask = (mask > 0) & (~soma_disk)
    line = brightest_line_in_mask(proc, residual_mask)
    if line is None:
        return {"status": "no_bright_line", "soma_x": soma[0], "soma_y": soma[1]}

    major = line["direction"].copy()
    soma_to_line = line["center"] - np.array(soma, dtype=np.float32)
    if np.dot(major, soma_to_line) < 0:
        major = -major
    if np.linalg.norm(soma_to_line) < 2.0:
        return {"status": "ambiguous_direction", "soma_x": soma[0], "soma_y": soma[1]}

    angle_deg = float(np.degrees(np.arctan2(major[1], major[0])))
    return {
        "status": "ok",
        "soma_x": soma[0],
        "soma_y": soma[1],
        "line_center_x": float(line["center"][0]),
        "line_center_y": float(line["center"][1]),
        "axis_x": float(major[0]),
        "axis_y": float(major[1]),
        "angle_deg": angle_deg,
        "raw_angle_deg": angle_deg,
        "elongation": pca_elongation(line["points"]),
        "line_score": float(line["score"]),
        "line_count": int(line["count"]),
        "line_x1": float(line["p1"][0]),
        "line_y1": float(line["p1"][1]),
        "line_x2": float(line["p2"][0]),
        "line_y2": float(line["p2"][1]),
        "mask_pixels": int(mask.sum()),
        "method": "brightest_line",
        "mask": mask,
    }


def transform_point(matrix, point):
    x, y = float(point[0]), float(point[1])
    return np.array([
        matrix[0, 0] * x + matrix[0, 1] * y + matrix[0, 2],
        matrix[1, 0] * x + matrix[1, 1] * y + matrix[1, 2],
    ], dtype=np.float32)


def normalize_angle(angle_deg):
    return ((float(angle_deg) + 180.0) % 360.0) - 180.0


def rotate_translate_to_center(image, angle_deg, source_center, target_angle_deg, line_center=None, target_line_side=TARGET_LINE_SIDE):
    image = normalize_uint8(image)
    h, w = image.shape[:2]
    target_center = np.array([w / 2.0, h / 2.0], dtype=np.float32)
    source_center = np.array(source_center, dtype=np.float32)
    rotation_deg = float(angle_deg - target_angle_deg)
    rotation_deg = normalize_angle(rotation_deg)
    matrix = cv2.getRotationMatrix2D((float(source_center[0]), float(source_center[1])), rotation_deg, 1.0)
    rotated_source = transform_point(matrix, source_center)
    shift = target_center - rotated_source
    matrix[0, 2] += float(shift[0])
    matrix[1, 2] += float(shift[1])

    side_flip_applied = False
    if line_center is not None and target_line_side in ("above", "below"):
        aligned_line_center = transform_point(matrix, line_center)
        line_is_below = aligned_line_center[1] > target_center[1]
        want_below = target_line_side == "below"
        if line_is_below != want_below:
            flip = cv2.getRotationMatrix2D((float(target_center[0]), float(target_center[1])), 180.0, 1.0)
            matrix_3 = np.vstack([matrix, [0.0, 0.0, 1.0]])
            flip_3 = np.vstack([flip, [0.0, 0.0, 1.0]])
            matrix = (flip_3 @ matrix_3)[:2]
            rotation_deg = normalize_angle(rotation_deg + 180.0)
            side_flip_applied = True

    aligned = cv2.warpAffine(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    return aligned, matrix, rotation_deg, side_flip_applied


def draw_debug(image, aligned, result, out_path, target_angle_deg):
    left = cv2.applyColorMap(normalize_uint8(image), cv2.COLORMAP_INFERNO)
    mask = result.get("mask")
    if mask is not None:
        contours, _ = cv2.findContours((mask > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(left, contours, -1, (0, 255, 255), 1)
    if result.get("status") == "ok":
        sx, sy = int(round(result["soma_x"])), int(round(result["soma_y"]))
        cv2.circle(left, (sx, sy), 4, (0, 0, 255), -1)
        p1 = (int(round(result["line_x1"])), int(round(result["line_y1"])))
        p2 = (int(round(result["line_x2"])), int(round(result["line_y2"])))
        cv2.line(left, p1, p2, (255, 255, 0), 1, cv2.LINE_AA)
        ax, ay = result["axis_x"], result["axis_y"]
        cv2.arrowedLine(left, (sx, sy), (int(round(sx + ax * 18)), int(round(sy + ay * 18))), (0, 255, 0), 1, tipLength=0.25)

    right = cv2.applyColorMap(normalize_uint8(aligned), cv2.COLORMAP_INFERNO)
    h, w = aligned.shape[:2]
    center = (int(round(w / 2.0)), int(round(h / 2.0)))
    cv2.drawMarker(right, center, (0, 0, 255), markerType=cv2.MARKER_CROSS, markerSize=8, thickness=1)
    theta = np.deg2rad(target_angle_deg)
    direction = np.array([np.cos(theta), np.sin(theta)], dtype=np.float32)
    cv2.line(
        right,
        (int(round(center[0] - direction[0] * 18)), int(round(center[1] - direction[1] * 18))),
        (int(round(center[0] + direction[0] * 18)), int(round(center[1] + direction[1] * 18))),
        (255, 255, 0),
        1,
        cv2.LINE_AA,
    )
    matrix = result.get("affine_matrix")
    if result.get("status") == "ok" and matrix is not None:
        soma_aligned = transform_point(matrix, (result["soma_x"], result["soma_y"]))
        line_p1 = transform_point(matrix, (result["line_x1"], result["line_y1"]))
        line_p2 = transform_point(matrix, (result["line_x2"], result["line_y2"]))
        cv2.circle(right, (int(round(soma_aligned[0])), int(round(soma_aligned[1]))), 4, (0, 0, 255), -1)
        cv2.line(
            right,
            (int(round(line_p1[0])), int(round(line_p1[1]))),
            (int(round(line_p2[0])), int(round(line_p2[1]))),
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )
    text = result.get("status", "")
    if result.get("status") == "ok":
        text = f"angle={result['angle_deg']:.1f} rot={result['rotation_deg']:.1f}"
    cv2.putText(left, text, (4, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (255, 255, 255), 1, cv2.LINE_AA)
    canvas = np.concatenate([left, right], axis=1)
    canvas = cv2.resize(canvas, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(out_path, canvas)


def make_preview(aligned_frames, out_path):
    if not aligned_frames:
        return
    max_img = np.max(np.stack(aligned_frames, axis=0), axis=0).astype(np.uint8)
    preview = cv2.applyColorMap(max_img, cv2.COLORMAP_INFERNO)
    preview = cv2.resize(preview, None, fx=5, fy=5, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(out_path, preview)


def process_stack(crop_name, limit=None, target_angle_deg=TARGET_ANGLE_DEG):
    stack_name = stack_name_from_crop(crop_name)
    crop_path = os.path.join(crop_dir, crop_name)
    mask_path = os.path.join(ria_mask_dir, f"{stack_name}_ria_mask.tif")
    if not os.path.exists(mask_path):
        print(f"[skip] {stack_name}: missing RIA mask")
        return

    os.makedirs(aligned_dir, exist_ok=True)
    preview_dir = os.path.join(aligned_dir, "previews")
    debug_dir = os.path.join(aligned_dir, "debug", stack_name)
    os.makedirs(preview_dir, exist_ok=True)
    if WRITE_DEBUG:
        os.makedirs(debug_dir, exist_ok=True)

    rows = []
    aligned_frames = []
    status_counts = Counter()
    previous_angle = None
    ok_debug_saved = 0

    with tifffile.TiffFile(crop_path) as tif, tifffile.TiffFile(mask_path) as mtif:
        n_frames = min(len(tif.pages), len(mtif.pages))
        if limit is not None:
            n_frames = min(n_frames, limit)
        print(f"[align brightest line] {stack_name}: {n_frames} frames")
        for frame_idx in range(n_frames):
            raw_frame = tif.pages[frame_idx].asarray()
            frame_u8 = normalize_uint8(raw_frame)
            detection_frame = read_crop_jpg(stack_name, frame_idx, frame_u8.shape[:2])
            if detection_frame is None:
                detection_frame = frame_u8
            mask = mtif.pages[frame_idx].asarray()
            classifier_frame = preprocess_for_direction(detection_frame) if USE_CLAHE_FOR_BLUR_CLASSIFIER else detection_frame
            blur_label, blur_prob_bad, blur_prob_good = classify_ria_frame_quality(classifier_frame)
            if USE_RIA_BLUR_CLASSIFIER and np.isfinite(blur_prob_bad) and blur_prob_bad >= RIA_BLUR_BAD_THRESHOLD:
                result = {"status": "classifier_bad"}
            else:
                result = estimate_direction(detection_frame, mask)
            result["blur_classifier_label"] = blur_label
            result["blur_classifier_prob_bad"] = blur_prob_bad
            result["blur_classifier_prob_good"] = blur_prob_good
            result["blur_classifier_bad_threshold"] = RIA_BLUR_BAD_THRESHOLD if USE_RIA_BLUR_CLASSIFIER else ""

            if result.get("status") == "ok":
                raw_angle = float(result["angle_deg"])
                if previous_angle is not None:
                    candidates = [raw_angle - 180.0, raw_angle, raw_angle + 180.0]
                    chosen = min(candidates, key=lambda value: abs(value - previous_angle))
                    if abs(chosen - raw_angle) > 1e-6:
                        result["axis_x"] = -float(result["axis_x"])
                        result["axis_y"] = -float(result["axis_y"])
                    result["angle_deg"] = chosen
                previous_angle = float(result["angle_deg"])
                aligned, affine_matrix, rotation_deg, side_flip_applied = rotate_translate_to_center(
                    frame_u8,
                    float(result["angle_deg"]),
                    (float(result["soma_x"]), float(result["soma_y"])),
                    target_angle_deg=target_angle_deg,
                    line_center=(float(result["line_center_x"]), float(result["line_center_y"])),
                    target_line_side=TARGET_LINE_SIDE,
                )
                result["rotation_deg"] = rotation_deg
                result["side_flip_applied"] = int(side_flip_applied)
                result["affine_matrix"] = affine_matrix
            else:
                aligned = np.zeros_like(frame_u8, dtype=np.uint8)
                result["rotation_deg"] = ""
                result["side_flip_applied"] = ""

            status_counts[result.get("status", "")] += 1
            aligned_frames.append(aligned)
            save_ok_debug = result.get("status") == "ok" and ok_debug_saved < DEBUG_FIRST_OK_FRAMES
            if WRITE_DEBUG and (frame_idx % DEBUG_EVERY_N_FRAMES == 0 or save_ok_debug):
                debug_path = os.path.join(debug_dir, f"{frame_idx:06d}_brightest_line_debug.jpg")
                draw_debug(detection_frame, aligned, result, debug_path, target_angle_deg)
                if save_ok_debug:
                    ok_debug_saved += 1

            rows.append({
                "frame": frame_idx,
                "status": result.get("status", ""),
                "method": result.get("method", ""),
                "soma_x": result.get("soma_x", ""),
                "soma_y": result.get("soma_y", ""),
                "line_center_x": result.get("line_center_x", ""),
                "line_center_y": result.get("line_center_y", ""),
                "axis_x": result.get("axis_x", ""),
                "axis_y": result.get("axis_y", ""),
                "angle_deg": result.get("angle_deg", ""),
                "raw_angle_deg": result.get("raw_angle_deg", ""),
                "rotation_deg": result.get("rotation_deg", ""),
                "target_angle_deg": target_angle_deg,
                "target_line_side": TARGET_LINE_SIDE,
                "side_flip_applied": result.get("side_flip_applied", ""),
                "elongation": result.get("elongation", ""),
                "line_score": result.get("line_score", ""),
                "line_count": result.get("line_count", ""),
                "line_x1": result.get("line_x1", ""),
                "line_y1": result.get("line_y1", ""),
                "line_x2": result.get("line_x2", ""),
                "line_y2": result.get("line_y2", ""),
                "mask_pixels": result.get("mask_pixels", ""),
                "blur_classifier_label": result.get("blur_classifier_label", ""),
                "blur_classifier_prob_bad": f"{blur_prob_bad:.6f}" if np.isfinite(blur_prob_bad) else "",
                "blur_classifier_prob_good": f"{blur_prob_good:.6f}" if np.isfinite(blur_prob_good) else "",
                "blur_classifier_bad_threshold": f"{RIA_BLUR_BAD_THRESHOLD:.6f}" if USE_RIA_BLUR_CLASSIFIER else "",
                "blur_classifier_clahe": int(USE_CLAHE_FOR_BLUR_CLASSIFIER),
            })

    aligned_path = os.path.join(aligned_dir, f"{stack_name}_aligned.tif")
    csv_path = os.path.join(aligned_dir, f"{stack_name}_alignment.csv")
    os.makedirs(aligned_dir, exist_ok=True)
    os.makedirs(preview_dir, exist_ok=True)
    tifffile.imwrite(aligned_path, np.stack(aligned_frames, axis=0).astype(np.uint8))
    fields = [
        "frame", "status", "method", "soma_x", "soma_y", "line_center_x", "line_center_y",
        "axis_x", "axis_y", "angle_deg", "raw_angle_deg", "rotation_deg", "target_angle_deg",
        "target_line_side", "side_flip_applied",
        "elongation", "line_score", "line_count", "line_x1", "line_y1", "line_x2", "line_y2",
        "mask_pixels", "blur_classifier_label", "blur_classifier_prob_bad", "blur_classifier_prob_good",
        "blur_classifier_bad_threshold", "blur_classifier_clahe",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    make_preview(aligned_frames, os.path.join(preview_dir, f"{stack_name}_max_projection.jpg"))
    print(f"[done] {stack_name}: {dict(status_counts)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack", default="", help="Stack name without _crop.tif. Empty = all stacks.")
    parser.add_argument("--limit", type=int, default=0, help="Limit frames per stack for testing. 0 = no limit.")
    parser.add_argument("--target-angle", type=float, default=TARGET_ANGLE_DEG)
    args = parser.parse_args()

    files = crop_stack_files()
    if args.stack:
        files = [f"{args.stack}_crop.tif"]
    if not files:
        print("No crop TIFF files found.")
        return
    limit = args.limit if args.limit > 0 else None
    for name in files:
        process_stack(name, limit=limit, target_angle_deg=args.target_angle)


if __name__ == "__main__":
    main()
