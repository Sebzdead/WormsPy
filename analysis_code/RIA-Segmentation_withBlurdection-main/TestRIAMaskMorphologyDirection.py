"""
Test RIA direction estimation from the existing RIA mask.

This does not modify pipeline outputs. It reads crop JPG/TIFF and RIA masks,
then estimates a morphology direction inside the dilated RIA mask:
- soma candidate: brightest component inside mask
- direction: PCA axis of bright pixels inside mask, oriented from soma toward
  the masked bright-pixel centroid

Outputs:
- morphology_direction_test/<stack>/overlays/*.jpg
- morphology_direction_test/<stack>/aligned_by_brightest_line.tif
- morphology_direction_test/<stack>/aligned_overlays/*.jpg
- morphology_direction_test/<stack>/direction.csv
"""
import argparse
import csv
import os

import cv2
import numpy as np
import tifffile


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260529"

CROP_SUBDIR = "04_ria_crop"
JPG_CROP_SUBDIR = "06_crop_jpg"
RIA_MASK_SUBDIR = "04_ria_mask"
OUTPUT_SUBDIR = "morphology_direction_test"

crop_dir = os.path.join(RESULTS_ROOT, RUN_ID, CROP_SUBDIR)
jpg_crop_dir = os.path.join(RESULTS_ROOT, RUN_ID, JPG_CROP_SUBDIR)
ria_mask_dir = os.path.join(RESULTS_ROOT, RUN_ID, RIA_MASK_SUBDIR)
output_root = os.path.join(RESULTS_ROOT, RUN_ID, OUTPUT_SUBDIR)


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


def stack_name_from_crop(name):
    return name[:-len("_crop.tif")]


def crop_stack_files():
    return sorted(f for f in os.listdir(crop_dir) if f.endswith("_crop.tif")) if os.path.isdir(crop_dir) else []


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


def preprocess_display(image):
    image = normalize_uint8(image)
    bg = cv2.GaussianBlur(image, (0, 0), 8)
    flat = cv2.subtract(image, bg)
    flat = normalize_uint8(flat)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    return clahe.apply(flat)


def pca_axis(points):
    centroid = points.mean(axis=0)
    centered = points - centroid
    cov = centered.T @ centered / max(len(points) - 1, 1)
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    major = eigvecs[:, order[0]]
    minor = eigvals[order[1]] if len(eigvals) > 1 else 0.0
    major_val = eigvals[order[0]]
    elongation = float(major_val / (minor + 1e-6))
    return centroid, major, elongation


def brightest_line_in_mask(proc, residual_mask, min_pixels=8, stripe_radius=1.25):
    ys, xs = np.where(residual_mask)
    if len(xs) < min_pixels:
        return None

    points = np.column_stack([xs.astype(np.float32), ys.astype(np.float32)])
    weights = proc[ys, xs].astype(np.float32) + 1.0
    center = np.average(points, axis=0, weights=weights)

    best = None
    best_score = -1.0
    best_count = 0
    best_angle = None
    for angle_deg in np.arange(0.0, 180.0, 2.0):
        theta = np.deg2rad(angle_deg)
        direction = np.array([np.cos(theta), np.sin(theta)], dtype=np.float32)
        normal = np.array([-direction[1], direction[0]], dtype=np.float32)
        signed_dist = (points - center) @ normal

        # Search line offsets around the weighted center. The chosen line is
        # the narrow stripe with the highest mean*sqrt(count), favoring bright
        # linear signal over large dim mask regions.
        lo, hi = np.percentile(signed_dist, (5, 95))
        offsets = np.linspace(lo, hi, 31)
        for offset in offsets:
            in_stripe = np.abs(signed_dist - offset) <= stripe_radius
            count = int(in_stripe.sum())
            if count < min_pixels:
                continue
            stripe_weights = weights[in_stripe]
            score = float(stripe_weights.mean() * np.sqrt(count))
            if score > best_score:
                stripe_points = points[in_stripe]
                proj = (stripe_points - center) @ direction
                p1 = center + direction * float(proj.min())
                p2 = center + direction * float(proj.max())
                best = (center + normal * float(offset), direction, p1, p2, stripe_points)
                best_score = score
                best_count = count
                best_angle = angle_deg

    if best is None:
        return None
    line_center, direction, p1, p2, stripe_points = best
    return {
        "center": line_center,
        "direction": direction,
        "p1": p1,
        "p2": p2,
        "points": stripe_points,
        "score": best_score,
        "count": best_count,
        "angle_deg": float(best_angle),
    }


def estimate_direction(image, mask, mask_dilate=1, soma_radius=6, min_pixels=8):
    image = normalize_uint8(image)
    mask = np.squeeze(mask)
    if mask.ndim != 2:
        return {"status": "bad_mask"}
    if mask.shape[:2] != image.shape[:2]:
        mask = cv2.resize(mask.astype(np.uint8), (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    mask = (mask > 0).astype(np.uint8)
    if int(mask.sum()) < min_pixels:
        return {"status": "mask_too_small"}
    if mask_dilate > 0:
        kernel = np.ones((3, 3), dtype=np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=mask_dilate)

    proc = preprocess_display(image)
    masked_values = proc[mask > 0]
    if masked_values.size < min_pixels:
        return {"status": "no_signal"}

    # Soma candidate: brightest connected component in a high-percentile mask.
    high_thr = np.percentile(masked_values, 90)
    high = ((proc >= high_thr) & (mask > 0)).astype(np.uint8)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(high, 8)
    if n_labels <= 1:
        return {"status": "no_soma"}
    best_label = None
    best_score = -1.0
    for label_id in range(1, n_labels):
        area = stats[label_id, cv2.CC_STAT_AREA]
        if area < 1:
            continue
        cx, cy = centroids[label_id]
        score = float(proc[labels == label_id].mean()) * np.sqrt(area)
        if score > best_score:
            best_score = score
            best_label = label_id
            soma = (float(cx), float(cy))
    if best_label is None:
        return {"status": "no_soma"}

    # Direction from the brightest line inside the RIA mask after removing soma.
    yy, xx = np.indices(image.shape[:2])
    soma_disk = (xx - soma[0]) ** 2 + (yy - soma[1]) ** 2 <= soma_radius ** 2
    residual_mask = (mask > 0) & (~soma_disk)
    line = brightest_line_in_mask(proc, residual_mask, min_pixels=min_pixels)
    if line is None:
        return {"status": "no_bright_line", "soma_x": soma[0], "soma_y": soma[1]}

    method = "brightest_line"
    dir_mask = residual_mask
    points = line["points"]
    centroid = line["center"]
    major = line["direction"]
    _, _, elongation = pca_axis(points)

    soma_to_centroid = centroid - np.array(soma, dtype=np.float32)
    if np.dot(major, soma_to_centroid) < 0:
        major = -major
    if np.linalg.norm(soma_to_centroid) < 2.0:
        return {"status": "ambiguous_direction", "soma_x": soma[0], "soma_y": soma[1], "elongation": elongation}

    angle_deg = float(np.degrees(np.arctan2(major[1], major[0])))
    return {
        "status": "ok",
        "soma_x": soma[0],
        "soma_y": soma[1],
        "bar_center_x": float(centroid[0]),
        "bar_center_y": float(centroid[1]),
        "axis_x": float(major[0]),
        "axis_y": float(major[1]),
        "angle_deg": angle_deg,
        "raw_angle_deg": angle_deg,
        "elongation": elongation,
        "direction_pixels": int(len(points)),
        "mask_pixels": int(mask.sum()),
        "method": method,
        "line_score": float(line["score"]),
        "line_count": int(line["count"]),
        "line_x1": float(line["p1"][0]),
        "line_y1": float(line["p1"][1]),
        "line_x2": float(line["p2"][0]),
        "line_y2": float(line["p2"][1]),
        "proc": proc,
        "mask": mask,
        "dir_mask": dir_mask,
    }


def draw_overlay(image, result, out_path):
    base = cv2.applyColorMap(normalize_uint8(image), cv2.COLORMAP_INFERNO)
    mask = result.get("mask")
    if mask is not None:
        contours, _ = cv2.findContours((mask > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(base, contours, -1, (0, 255, 255), 1)
    if result.get("status") == "ok":
        sx, sy = result["soma_x"], result["soma_y"]
        cx, cy = result["bar_center_x"], result["bar_center_y"]
        ax, ay = result["axis_x"], result["axis_y"]
        cv2.circle(base, (int(round(sx)), int(round(sy))), 4, (0, 0, 255), -1)
        cv2.circle(base, (int(round(cx)), int(round(cy))), 3, (255, 255, 255), -1)
        if all(key in result for key in ("line_x1", "line_y1", "line_x2", "line_y2")):
            p_line1 = (int(round(result["line_x1"])), int(round(result["line_y1"])))
            p_line2 = (int(round(result["line_x2"])), int(round(result["line_y2"])))
            cv2.line(base, p_line1, p_line2, (255, 255, 0), 1, cv2.LINE_AA)
        p1 = (int(round(sx)), int(round(sy)))
        p2 = (int(round(sx + ax * 18)), int(round(sy + ay * 18)))
        cv2.arrowedLine(base, p1, p2, (0, 255, 0), 1, tipLength=0.25)
        text = f"angle={result['angle_deg']:.1f} elong={result['elongation']:.1f} {result.get('method', '')}"
    else:
        text = result.get("status", "")
    cv2.putText(base, text, (4, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (255, 255, 255), 1, cv2.LINE_AA)
    scale = 5
    base = cv2.resize(base, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(out_path, base)


def rotate_translate_to_center(image, angle_deg, source_center, target_angle_deg=0.0):
    image = normalize_uint8(image)
    h, w = image.shape[:2]
    target_center = np.array([w / 2.0, h / 2.0], dtype=np.float32)
    source_center = np.array(source_center, dtype=np.float32)
    # angle_deg is measured in image coordinates (x right, y down). OpenCV's
    # positive affine angle maps that vector to angle_deg - rotation_deg, so
    # use angle-target to make the detected line land on target_angle_deg.
    rotation_deg = float(angle_deg - target_angle_deg)
    rotation_deg = ((rotation_deg + 180.0) % 360.0) - 180.0
    matrix = cv2.getRotationMatrix2D((float(source_center[0]), float(source_center[1])), rotation_deg, 1.0)
    rotated_source = np.array([
        matrix[0, 0] * source_center[0] + matrix[0, 1] * source_center[1] + matrix[0, 2],
        matrix[1, 0] * source_center[0] + matrix[1, 1] * source_center[1] + matrix[1, 2],
    ], dtype=np.float32)
    shift = target_center - rotated_source
    matrix[0, 2] += float(shift[0])
    matrix[1, 2] += float(shift[1])
    aligned = cv2.warpAffine(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    return aligned, matrix


def draw_aligned_overlay(aligned, result, out_path, target_angle_deg=0.0):
    base = cv2.applyColorMap(normalize_uint8(aligned), cv2.COLORMAP_INFERNO)
    h, w = aligned.shape[:2]
    center = (int(round(w / 2.0)), int(round(h / 2.0)))
    cv2.drawMarker(base, center, (0, 0, 255), markerType=cv2.MARKER_CROSS, markerSize=8, thickness=1)
    theta = np.deg2rad(target_angle_deg)
    direction = np.array([np.cos(theta), np.sin(theta)], dtype=np.float32)
    p1 = (int(round(center[0] - direction[0] * 18)), int(round(center[1] - direction[1] * 18)))
    p2 = (int(round(center[0] + direction[0] * 18)), int(round(center[1] + direction[1] * 18)))
    cv2.line(base, p1, p2, (255, 255, 0), 1, cv2.LINE_AA)
    text = result.get("status", "")
    if result.get("status") == "ok":
        text = f"rot={result.get('rotation_deg', 0.0):.1f} angle={result['angle_deg']:.1f}"
    cv2.putText(base, text, (4, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (255, 255, 255), 1, cv2.LINE_AA)
    base = cv2.resize(base, None, fx=5, fy=5, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(out_path, base)


def process_stack(crop_name, limit, target_angle_deg):
    stack_name = stack_name_from_crop(crop_name)
    crop_path = os.path.join(crop_dir, crop_name)
    mask_path = os.path.join(ria_mask_dir, f"{stack_name}_ria_mask.tif")
    if not os.path.exists(mask_path):
        print(f"[skip] no mask: {stack_name}")
        return

    out_dir = os.path.join(output_root, stack_name)
    overlay_dir = os.path.join(out_dir, "overlays")
    aligned_overlay_dir = os.path.join(out_dir, "aligned_overlays")
    os.makedirs(overlay_dir, exist_ok=True)
    os.makedirs(aligned_overlay_dir, exist_ok=True)
    rows = []
    aligned_frames = []
    previous_angle = None
    with tifffile.TiffFile(crop_path) as tif, tifffile.TiffFile(mask_path) as mtif:
        n_frames = min(len(tif.pages), len(mtif.pages), limit)
        for frame_idx in range(n_frames):
            frame = tif.pages[frame_idx].asarray()
            frame_u8 = read_crop_jpg(stack_name, frame_idx, normalize_uint8(frame).shape[:2])
            if frame_u8 is None:
                frame_u8 = normalize_uint8(frame)
            mask = mtif.pages[frame_idx].asarray()
            result = estimate_direction(frame_u8, mask)
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
                aligned, _ = rotate_translate_to_center(
                    frame_u8,
                    float(result["angle_deg"]),
                    (float(result["soma_x"]), float(result["soma_y"])),
                    target_angle_deg=target_angle_deg,
                )
                result["rotation_deg"] = float(float(result["angle_deg"]) - target_angle_deg)
                result["rotation_deg"] = ((result["rotation_deg"] + 180.0) % 360.0) - 180.0
            else:
                aligned = np.zeros_like(frame_u8, dtype=np.uint8)
            out_path = os.path.join(overlay_dir, f"{frame_idx:06d}_morphology_direction.jpg")
            draw_overlay(frame_u8, result, out_path)
            aligned_out_path = os.path.join(aligned_overlay_dir, f"{frame_idx:06d}_aligned_brightest_line.jpg")
            draw_aligned_overlay(aligned, result, aligned_out_path, target_angle_deg=target_angle_deg)
            aligned_frames.append(aligned)
            row = {
                "frame": frame_idx,
                "status": result.get("status", ""),
                "soma_x": result.get("soma_x", ""),
                "soma_y": result.get("soma_y", ""),
                "bar_center_x": result.get("bar_center_x", ""),
                "bar_center_y": result.get("bar_center_y", ""),
                "axis_x": result.get("axis_x", ""),
                "axis_y": result.get("axis_y", ""),
                "angle_deg": result.get("angle_deg", ""),
                "raw_angle_deg": result.get("raw_angle_deg", ""),
                "elongation": result.get("elongation", ""),
                "direction_pixels": result.get("direction_pixels", ""),
                "mask_pixels": result.get("mask_pixels", ""),
                "method": result.get("method", ""),
                "line_score": result.get("line_score", ""),
                "line_count": result.get("line_count", ""),
                "line_x1": result.get("line_x1", ""),
                "line_y1": result.get("line_y1", ""),
                "line_x2": result.get("line_x2", ""),
                "line_y2": result.get("line_y2", ""),
                "rotation_deg": result.get("rotation_deg", ""),
                "target_angle_deg": target_angle_deg,
            }
            rows.append(row)
    aligned_tif_path = os.path.join(out_dir, "aligned_by_brightest_line.tif")
    if aligned_frames:
        tifffile.imwrite(aligned_tif_path, np.stack(aligned_frames, axis=0).astype(np.uint8))
    csv_path = os.path.join(out_dir, "direction.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fields = [
            "frame", "status", "soma_x", "soma_y", "bar_center_x", "bar_center_y",
            "axis_x", "axis_y", "angle_deg", "raw_angle_deg", "elongation",
            "direction_pixels", "mask_pixels", "method", "line_score", "line_count",
            "line_x1", "line_y1", "line_x2", "line_y2", "rotation_deg", "target_angle_deg",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    ok = sum(1 for row in rows if row["status"] == "ok")
    print(f"{stack_name}: ok={ok}/{len(rows)}, aligned_tif={aligned_tif_path}, overlays={aligned_overlay_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack", default="", help="Stack name without _crop.tif. Empty = first crop stack.")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--target-angle", type=float, default=0.0, help="Target line angle after correction, in degrees.")
    args = parser.parse_args()

    files = crop_stack_files()
    if args.stack:
        files = [f"{args.stack}_crop.tif"]
    elif files:
        files = [files[0]]
    if not files:
        print("No crop files found.")
        return
    for name in files:
        process_stack(name, args.limit, args.target_angle)


if __name__ == "__main__":
    main()
