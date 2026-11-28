"""
Draw free-form polygon or circular ROIs on max-intensity projections of aligned RIA stacks and
export per-frame intensity traces.

Inputs:
- 07_ria_template_bank_all_aligned/<stack>_aligned.tif
- 07_ria_template_bank_all_aligned/<stack>_template_bank_assignments.csv

Outputs:
- 08_roi_intensity/<stack>_max_projection.tif
- 08_roi_intensity/<stack>_roi_overlay.jpg
- 08_roi_intensity/<stack>_rois.csv
- 08_roi_intensity/<stack>_roi_intensity.csv
"""
import csv
import json
import os

import cv2
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np
import tifffile
from tqdm import tqdm


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260529"

ALIGNED_SUBDIR = "07_ria_template_bank_all_aligned"
WORM_SKEL_SUBDIR = "05_worm_head_angle"
STACK_SUBDIR = "01_tiff_stack"
WORM_SEG_SUBDIR = "03_worm_segmentation"
ROI_OUTPUT_SUBDIR = "08_roi_intensity"

ROI_LABELS = {
    "1": "nrv",
    "2": "nrD",
    "3": "loop",
    "4": "soma",
    "5": "otherconsern",
}

DEFAULT_RADIUS = 4.0
RADIUS_STEP = 1.0
MIN_RADIUS = 1.0
ROI_VIDEO_FPS = 10
OVERWRITE_EXISTING = False
EXCLUDED_TEMPLATE_STATES = {
    "blur",
    "z_rotation_ring_visible",
    "no_ria_visible",
}
BRIGHTEST_PIXEL_COUNT = 5
BACKGROUND_WORM_MASK_DILATE_PX = 8
BACKGROUND_TILE_SIZE = 64
BACKGROUND_TILE_MIN_VALID_FRACTION = 0.75
BACKGROUND_TILE_STD_QUANTILE = 0.30
BACKGROUND_TILE_MEDIAN_MAD_MULTIPLIER = 2.5

aligned_dir = os.path.join(RESULTS_ROOT, RUN_ID, ALIGNED_SUBDIR)
worm_skel_dir = os.path.join(RESULTS_ROOT, RUN_ID, WORM_SKEL_SUBDIR)
stack_dir = os.path.join(RESULTS_ROOT, RUN_ID, STACK_SUBDIR)
worm_seg_dir = os.path.join(RESULTS_ROOT, RUN_ID, WORM_SEG_SUBDIR)
roi_output_dir = os.path.join(RESULTS_ROOT, RUN_ID, ROI_OUTPUT_SUBDIR)


def normalize_for_display(image):
    image = image.astype(np.float32)
    if image.max() <= image.min():
        return np.zeros(image.shape, dtype=np.uint8)
    lo, hi = np.percentile(image, (1, 99.8))
    if hi <= lo:
        lo, hi = float(image.min()), float(image.max())
    if hi <= lo:
        return np.zeros(image.shape, dtype=np.uint8)
    out = np.clip((image - lo) / (hi - lo), 0, 1)
    return (out * 255).astype(np.uint8)


def aligned_stack_files():
    if not os.path.isdir(aligned_dir):
        return []
    return sorted(f for f in os.listdir(aligned_dir) if f.endswith("_aligned.tif"))


def stack_name_from_aligned(file_name):
    return file_name[: -len("_aligned.tif")]


def alignment_csv_path(stack_name):
    return os.path.join(aligned_dir, f"{stack_name}_alignment.csv")


def template_bank_assignment_csv_path(stack_name):
    return os.path.join(aligned_dir, f"{stack_name}_template_bank_assignments.csv")


def head_angles_csv_path(stack_name):
    return os.path.join(worm_skel_dir, stack_name, "head_angles.csv")


def truthy(value):
    return str(value).strip().lower() in {"1", "true", "yes"}


def load_aligned_ok_frames(stack_name):
    path = alignment_csv_path(stack_name)
    csv_kind = "ecc"
    if not os.path.exists(path):
        path = template_bank_assignment_csv_path(stack_name)
        csv_kind = "template_bank"
    if not os.path.exists(path):
        print(f"[warn] No alignment/template-bank CSV for {stack_name}; no aligned-success frames available")
        return set(), {}

    ok_frames = set()
    alignment_rows = {}
    excluded_counts = {}
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                frame = int(row["frame"])
            except (KeyError, TypeError, ValueError):
                continue
            alignment_rows[frame] = row

            if csv_kind == "ecc":
                if row.get("status") == "ok":
                    ok_frames.add(frame)
                continue

            if "ria_align_status" in row:
                align_status = str(row.get("ria_align_status", "")).strip().lower()
                output_is_black = truthy(row.get("output_is_black_frame", ""))
                template_state = str(row.get("template_state_label", "")).strip().lower()
                if align_status == "ok" and not output_is_black and template_state not in EXCLUDED_TEMPLATE_STATES:
                    ok_frames.add(frame)
                else:
                    reason = (
                        f"template_state={template_state}"
                        if template_state in EXCLUDED_TEMPLATE_STATES
                        else f"align_status={align_status or 'missing'}"
                    )
                    excluded_counts[reason] = excluded_counts.get(reason, 0) + 1
                continue

            # Compatibility with older template-bank output.
            try:
                cc = float(row.get("class_match_cc", "nan"))
            except (TypeError, ValueError):
                cc = float("nan")
            if not truthy(row.get("class_forced_low_cc", "")) and cc >= 0.90:
                ok_frames.add(frame)
    print(
        f"[align] {stack_name}: using {csv_kind} CSV, "
        f"usable aligned frames={len(ok_frames)}/{len(alignment_rows)}"
    )
    if excluded_counts:
        print(
            "[align] excluded: "
            + ", ".join(f"{reason}={count}" for reason, count in sorted(excluded_counts.items()))
        )
    return ok_frames, alignment_rows


def load_head_angles(stack_name):
    path = head_angles_csv_path(stack_name)
    angles = {}
    if not os.path.exists(path):
        print(f"[warn] No head angle CSV for {stack_name}: {path}")
        return angles
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                frame = int(row["frame"])
            except (KeyError, TypeError, ValueError):
                continue
            angles[frame] = row
    return angles


def iter_tiff_frames(path):
    with tifffile.TiffFile(path) as tif:
        series_shape = tif.series[0].shape
        if len(series_shape) == 2:
            yield 0, tif.asarray()
            return
        if len(tif.pages) == series_shape[0]:
            for idx, page in enumerate(tif.pages):
                yield idx, page.asarray()
        else:
            stack = tif.asarray()
            for idx, frame in enumerate(stack):
                yield idx, frame


def tiff_frame_count_and_shape(path):
    with tifffile.TiffFile(path) as tif:
        series_shape = tif.series[0].shape
        if len(series_shape) == 2:
            return 1, series_shape
        return int(series_shape[0]), tuple(series_shape[1:3])


def max_projection(path, include_frames=None):
    n_frames, shape = tiff_frame_count_and_shape(path)
    projection = None
    for frame_idx, frame in tqdm(iter_tiff_frames(path), total=n_frames, desc="Max projection"):
        if include_frames is not None and frame_idx not in include_frames:
            continue
        frame = np.asarray(frame)
        if projection is None:
            projection = frame.copy()
        else:
            projection = np.maximum(projection, frame)
    if projection is None:
        projection = np.zeros(shape, dtype=np.uint8)
    return projection


def circular_roi_mask(shape, x, y, radius):
    h, w = shape
    yy, xx = np.ogrid[:h, :w]
    return (xx - x) ** 2 + (yy - y) ** 2 <= radius ** 2


def roi_to_mask(shape, roi):
    if roi.get("shape", "circle") == "polygon":
        points = np.asarray(roi.get("points", []), dtype=np.float32)
        mask = np.zeros(shape, dtype=np.uint8)
        if len(points) >= 3:
            cv2.fillPoly(mask, [np.round(points).astype(np.int32)], 255)
        return mask > 0
    return circular_roi_mask(shape, roi["x"], roi["y"], roi["radius"])


def original_stack_path(stack_name):
    for extension in (".tiff", ".tif"):
        path = os.path.join(stack_dir, stack_name + extension)
        if os.path.exists(path):
            return path
    return None


def worm_mask_path(stack_name, frame_idx):
    return os.path.join(worm_seg_dir, stack_name, "masks", f"{frame_idx:06d}_worm_mask.png")


def read_tiff_frame(tif, frame_idx):
    if len(tif.pages) > frame_idx:
        return np.asarray(tif.pages[frame_idx].asarray())
    stack = tif.asarray()
    if stack.ndim == 2:
        return stack if frame_idx == 0 else None
    return np.asarray(stack[frame_idx]) if frame_idx < len(stack) else None


def estimate_background_from_original(original_frame, worm_mask):
    frame = np.squeeze(np.asarray(original_frame))
    if frame.ndim != 2 or worm_mask is None:
        return None
    if worm_mask.shape != frame.shape:
        worm_mask = cv2.resize(
            worm_mask,
            (frame.shape[1], frame.shape[0]),
            interpolation=cv2.INTER_NEAREST,
        )

    worm_mask = worm_mask > 0
    padding = max(0, int(BACKGROUND_WORM_MASK_DILATE_PX))
    if padding > 0:
        size = 2 * padding + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
        worm_mask = cv2.dilate(worm_mask.astype(np.uint8), kernel).astype(bool)
    candidate_mask = (~worm_mask) & np.isfinite(frame)

    tile_size = max(8, int(BACKGROUND_TILE_SIZE))
    tiles = []
    for y in range(0, frame.shape[0], tile_size):
        for x in range(0, frame.shape[1], tile_size):
            tile = frame[y:y + tile_size, x:x + tile_size]
            valid = candidate_mask[y:y + tile_size, x:x + tile_size]
            if valid.mean() < BACKGROUND_TILE_MIN_VALID_FRACTION:
                continue
            values = tile[valid].astype(np.float64, copy=False)
            if values.size:
                tiles.append((values, float(np.median(values)), float(values.std())))
    if not tiles:
        return None

    tile_medians = np.array([item[1] for item in tiles], dtype=float)
    tile_stds = np.array([item[2] for item in tiles], dtype=float)
    median_center = float(np.median(tile_medians))
    median_mad = float(np.median(np.abs(tile_medians - median_center)))
    median_tolerance = max(1.0, BACKGROUND_TILE_MEDIAN_MAD_MULTIPLIER * 1.4826 * median_mad)
    std_threshold = float(np.quantile(tile_stds, BACKGROUND_TILE_STD_QUANTILE))

    selected = [
        values
        for values, tile_median, tile_std in tiles
        if abs(tile_median - median_center) <= median_tolerance and tile_std <= std_threshold
    ]
    if not selected:
        best_index = int(np.argmin(tile_stds))
        selected = [tiles[best_index][0]]

    background_values = np.concatenate(selected)
    return {
        "values": background_values,
        "candidate_pixels": int(candidate_mask.sum()),
        "selected_tile_count": len(selected),
        "candidate_tile_count": len(tiles),
        "selected_tile_std_threshold": std_threshold,
    }


def roi_color(label):
    colors = {
        "nrv": (255, 80, 80),
        "nrD": (80, 180, 255),
        "loop": (255, 220, 60),
        "soma": (80, 255, 120),
        "otherconsern": (220, 120, 255),
    }
    return colors.get(label, (255, 255, 255))


def load_rois(path):
    if not os.path.exists(path):
        return []
    rois = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                roi = {
                    "roi_id": row["roi_id"],
                    "label": row["label"],
                    "shape": row.get("shape", "circle") or "circle",
                }
                if roi["shape"] == "polygon":
                    roi["points"] = json.loads(row.get("points", "[]"))
                else:
                    roi.update({
                        "x": float(row["x"]),
                        "y": float(row["y"]),
                        "radius": float(row["radius"]),
                    })
                rois.append(roi)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
    return rois


def save_rois(path, rois):
    with open(path, "w", newline="", encoding="utf-8") as f:
        fields = ["roi_id", "label", "shape", "x", "y", "radius", "points"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for roi in rois:
            row = {key: roi.get(key, "") for key in fields}
            row["points"] = json.dumps(roi.get("points", []), separators=(",", ":"))
            writer.writerow(row)


def intensity_csv_matches_current_format(path):
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, [])
    except OSError:
        return False
    return (
        "ria_head_angle_deg" in header
        and "ria_align_status" in header
        and "global_template_id" in header
        and "template_state_label" in header
        and "background_median_intensity" in header
        and "background_source" in header
        and any(name.startswith("brightest5_mean_intensity_") for name in header)
    )


def draw_rois(projection, stack_name, existing_rois=None):
    rois = list(existing_rois or [])
    state = {
        "label_key": "1",
        "radius": DEFAULT_RADIUS,
        "mode": "polygon",
        "current_points": [],
        "done": False,
    }

    fig, ax = plt.subplots(figsize=(7, 7))
    fig.canvas.manager.set_window_title(f"Draw ROIs: {stack_name}")

    def render():
        ax.clear()
        ax.imshow(normalize_for_display(projection), cmap="gray")
        ax.set_axis_off()
        for roi in rois:
            color = np.array(roi_color(roi["label"])) / 255.0
            if roi.get("shape", "circle") == "polygon":
                points = np.asarray(roi["points"], dtype=float)
                closed = np.vstack([points, points[0]])
                ax.plot(closed[:, 0], closed[:, 1], color=color, linewidth=2)
                label_x, label_y = points.mean(axis=0)
            else:
                patch = Circle((roi["x"], roi["y"]), roi["radius"], fill=False, color=color, linewidth=2)
                ax.add_patch(patch)
                label_x, label_y = roi["x"], roi["y"] - roi["radius"] - 1
            ax.text(
                label_x,
                label_y,
                roi["roi_id"],
                color=color,
                fontsize=8,
                ha="center",
                va="bottom",
            )
        if state["current_points"]:
            points = np.asarray(state["current_points"], dtype=float)
            ax.plot(points[:, 0], points[:, 1], "o-", color="lime", linewidth=1.5, markersize=4)
        label_text = ROI_LABELS[state["label_key"]]
        fig.suptitle(
            f"{stack_name} | {state['mode']} | label {state['label_key']}={label_text}, "
            f"radius={state['radius']:.1f}\n"
            "p=polygon, c=circle, left click=add point/ROI, Enter=close polygon, "
            "right click=undo point, u=undo ROI, s=save",
            fontsize=9,
        )
        fig.tight_layout()
        fig.canvas.draw_idle()

    def next_roi_id(label):
        count = sum(1 for roi in rois if roi["label"] == label) + 1
        return f"{label}_{count:02d}"

    def add_circle(x, y):
        label = ROI_LABELS[state["label_key"]]
        rois.append({
            "roi_id": next_roi_id(label),
            "label": label,
            "shape": "circle",
            "x": round(float(x), 3),
            "y": round(float(y), 3),
            "radius": round(float(state["radius"]), 3),
        })

    def on_click(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return
        if event.button == 3 and state["current_points"]:
            state["current_points"].pop()
            render()
            return
        if event.button != 1:
            return
        if state["mode"] == "circle":
            add_circle(float(event.xdata), float(event.ydata))
        else:
            state["current_points"].append([
                round(float(event.xdata), 3),
                round(float(event.ydata), 3),
            ])
        render()

    def on_key(event):
        key = event.key
        if key in ROI_LABELS:
            state["label_key"] = key
        elif key == "p":
            state["mode"] = "polygon"
            state["current_points"] = []
        elif key == "c":
            state["mode"] = "circle"
            state["current_points"] = []
        elif key in ("enter", " "):
            if state["mode"] == "polygon" and len(state["current_points"]) >= 3:
                label = ROI_LABELS[state["label_key"]]
                rois.append({
                    "roi_id": next_roi_id(label),
                    "label": label,
                    "shape": "polygon",
                    "points": state["current_points"],
                })
                state["current_points"] = []
        elif key in ("+", "="):
            state["radius"] += RADIUS_STEP
        elif key in ("-", "_"):
            state["radius"] = max(MIN_RADIUS, state["radius"] - RADIUS_STEP)
        elif key == "u":
            if state["current_points"]:
                state["current_points"] = []
            elif rois:
                rois.pop()
        elif key == "s":
            state["done"] = True
            plt.close(fig)
            return
        elif key in ("q", "escape"):
            state["done"] = True
            plt.close(fig)
            return
        render()

    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.canvas.mpl_connect("key_press_event", on_key)
    render()
    plt.show()
    return rois


def save_roi_overlay(projection, rois, out_path):
    image = cv2.cvtColor(normalize_for_display(projection), cv2.COLOR_GRAY2BGR)
    for roi in rois:
        color = roi_color(roi["label"])
        if roi.get("shape", "circle") == "polygon":
            points = np.round(np.asarray(roi["points"])).astype(np.int32)
            cv2.polylines(image, [points], True, color, 1, lineType=cv2.LINE_AA)
            center = tuple(np.round(points.mean(axis=0)).astype(int))
            radius = 0
        else:
            center = (int(round(roi["x"])), int(round(roi["y"])))
            radius = int(round(roi["radius"]))
            cv2.circle(image, center, radius, color, 1, lineType=cv2.LINE_AA)
        cv2.putText(
            image,
            roi["roi_id"],
            (center[0] - radius, max(0, center[1] - radius - 3)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.28,
            color,
            1,
            cv2.LINE_AA,
        )
    cv2.imwrite(out_path, image)


def draw_rois_on_frame(frame, rois):
    image = cv2.cvtColor(normalize_for_display(frame), cv2.COLOR_GRAY2BGR)
    for roi in rois:
        color = roi_color(roi["label"])
        if roi.get("shape", "circle") == "polygon":
            points = np.round(np.asarray(roi["points"])).astype(np.int32)
            cv2.polylines(image, [points], True, color, 1, lineType=cv2.LINE_AA)
            center = tuple(np.round(points.mean(axis=0)).astype(int))
            radius = 0
        else:
            center = (int(round(roi["x"])), int(round(roi["y"])))
            radius = int(round(roi["radius"]))
            cv2.circle(image, center, radius, color, 1, lineType=cv2.LINE_AA)
        cv2.putText(
            image,
            roi["roi_id"],
            (center[0] - radius, max(0, center[1] - radius - 3)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.28,
            color,
            1,
            cv2.LINE_AA,
        )
    return image


def save_roi_video(stack_path, rois, out_path, include_frames=None, fps=ROI_VIDEO_FPS):
    n_frames, shape = tiff_frame_count_and_shape(stack_path)
    height, width = shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height), True)
    if not writer.isOpened():
        raise RuntimeError(f"Could not open video writer: {out_path}")
    try:
        for frame_idx, frame in tqdm(iter_tiff_frames(stack_path), total=n_frames, desc="Write ROI video"):
            if include_frames is not None and frame_idx not in include_frames:
                continue
            writer.write(draw_rois_on_frame(np.asarray(frame), rois))
    finally:
        writer.release()


def measure_intensity(
    stack_name,
    stack_path,
    rois,
    out_csv_path,
    include_frames,
    head_angles,
    alignment_rows,
):
    n_frames, shape = tiff_frame_count_and_shape(stack_path)
    prepared_rois = []
    for roi in rois:
        mask = roi_to_mask(shape, roi)
        prepared_rois.append((roi, mask, int(mask.sum())))

    raw_stack_path = original_stack_path(stack_name)
    if raw_stack_path is None:
        raise FileNotFoundError(f"No original TIFF stack found for background calculation: {stack_name}")

    fields = [
        "frame",
        "head_angle_status",
        "ria_head_angle_deg",
        "ria_head_abs_angle_deg",
        "raw_three_point_angle_deg",
        "ria_align_status",
        "local_template_id",
        "global_template_id",
        "local_match_cc",
        "global_match_cc",
        "template_loop_label",
        "template_state_label",
        "background_source",
        "background_mean_intensity",
        "background_median_intensity",
        "background_area_pixels",
        "background_candidate_area_pixels",
        "background_retained_fraction",
        "background_selected_tile_count",
        "background_candidate_tile_count",
        "background_tile_std_threshold",
    ]
    metrics = [
        "mean_intensity",
        "median_intensity",
        "max_intensity",
        "brightest5_mean_intensity",
        "sum_intensity",
        "area_pixels",
        "background_corrected_mean_intensity",
        "background_corrected_median_intensity",
        "background_corrected_max_intensity",
        "background_corrected_brightest5_mean_intensity",
        "background_corrected_sum_intensity",
    ]
    for metric in metrics:
        for roi, _, _ in prepared_rois:
            fields.append(f"{metric}_{roi['roi_id']}")

    with open(out_csv_path, "w", newline="", encoding="utf-8") as f, tifffile.TiffFile(raw_stack_path) as raw_tif:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for frame_idx, frame in tqdm(iter_tiff_frames(stack_path), total=n_frames, desc="Measure ROI intensity"):
            if frame_idx not in include_frames:
                continue
            frame = np.asarray(frame)
            angle_row = head_angles.get(frame_idx, {})
            alignment_row = alignment_rows.get(frame_idx, {})
            row = {
                "frame": frame_idx,
                "head_angle_status": angle_row.get("status", ""),
                "ria_head_angle_deg": angle_row.get("ria_head_angle_deg", ""),
                "ria_head_abs_angle_deg": angle_row.get("ria_head_abs_angle_deg", ""),
                "raw_three_point_angle_deg": angle_row.get("raw_three_point_angle_deg", ""),
                "ria_align_status": alignment_row.get("ria_align_status", alignment_row.get("status", "")),
                "local_template_id": alignment_row.get("local_template_id", ""),
                "global_template_id": alignment_row.get("global_template_id", ""),
                "local_match_cc": alignment_row.get("local_match_cc", ""),
                "global_match_cc": alignment_row.get("global_match_cc", ""),
                "template_loop_label": alignment_row.get("template_loop_label", ""),
                "template_state_label": alignment_row.get("template_state_label", ""),
                "background_source": "original_tiff_minus_worm_mask_uniform_tiles",
            }
            original_frame = read_tiff_frame(raw_tif, frame_idx)
            worm_mask = cv2.imread(worm_mask_path(stack_name, frame_idx), cv2.IMREAD_GRAYSCALE)
            background_result = estimate_background_from_original(original_frame, worm_mask)
            if background_result is not None:
                background_values = background_result["values"]
                background_candidate_area = background_result["candidate_pixels"]
                background_mean = float(background_values.mean())
                background_median = float(np.median(background_values))
                row["background_mean_intensity"] = f"{background_mean:.6f}"
                row["background_median_intensity"] = f"{background_median:.6f}"
                row["background_area_pixels"] = int(background_values.size)
                row["background_candidate_area_pixels"] = background_candidate_area
                row["background_retained_fraction"] = f"{background_values.size / max(1, background_candidate_area):.6f}"
                row["background_selected_tile_count"] = background_result["selected_tile_count"]
                row["background_candidate_tile_count"] = background_result["candidate_tile_count"]
                row["background_tile_std_threshold"] = f"{background_result['selected_tile_std_threshold']:.6f}"
            else:
                background_mean = np.nan
                background_median = np.nan
                row["background_mean_intensity"] = ""
                row["background_median_intensity"] = ""
                row["background_area_pixels"] = 0
                row["background_candidate_area_pixels"] = ""
                row["background_retained_fraction"] = ""
                row["background_selected_tile_count"] = 0
                row["background_candidate_tile_count"] = 0
                row["background_tile_std_threshold"] = ""

            for roi, mask, area in prepared_rois:
                prefix = roi["roi_id"]
                values = frame[mask].astype(np.float64, copy=False)
                if values.size == 0:
                    row[f"mean_intensity_{prefix}"] = ""
                    row[f"median_intensity_{prefix}"] = ""
                    row[f"max_intensity_{prefix}"] = ""
                    row[f"brightest5_mean_intensity_{prefix}"] = ""
                    row[f"sum_intensity_{prefix}"] = ""
                    row[f"area_pixels_{prefix}"] = 0
                    row[f"background_corrected_mean_intensity_{prefix}"] = ""
                    row[f"background_corrected_median_intensity_{prefix}"] = ""
                    row[f"background_corrected_max_intensity_{prefix}"] = ""
                    row[f"background_corrected_brightest5_mean_intensity_{prefix}"] = ""
                    row[f"background_corrected_sum_intensity_{prefix}"] = ""
                else:
                    mean_value = float(values.mean())
                    median_value = float(np.median(values))
                    max_value = float(values.max())
                    sum_value = float(values.sum())
                    brightest_count = min(BRIGHTEST_PIXEL_COUNT, values.size)
                    brightest_mean = float(np.partition(values, values.size - brightest_count)[-brightest_count:].mean())

                    row[f"mean_intensity_{prefix}"] = f"{mean_value:.6f}"
                    row[f"median_intensity_{prefix}"] = f"{median_value:.6f}"
                    row[f"max_intensity_{prefix}"] = f"{max_value:.6f}"
                    row[f"brightest5_mean_intensity_{prefix}"] = f"{brightest_mean:.6f}"
                    row[f"sum_intensity_{prefix}"] = f"{sum_value:.6f}"
                    row[f"area_pixels_{prefix}"] = area
                    if np.isfinite(background_median):
                        row[f"background_corrected_mean_intensity_{prefix}"] = f"{mean_value - background_median:.6f}"
                        row[f"background_corrected_median_intensity_{prefix}"] = f"{median_value - background_median:.6f}"
                        row[f"background_corrected_max_intensity_{prefix}"] = f"{max_value - background_median:.6f}"
                        row[f"background_corrected_brightest5_mean_intensity_{prefix}"] = f"{brightest_mean - background_median:.6f}"
                        row[f"background_corrected_sum_intensity_{prefix}"] = f"{sum_value - background_median * area:.6f}"
                    else:
                        row[f"background_corrected_mean_intensity_{prefix}"] = ""
                        row[f"background_corrected_median_intensity_{prefix}"] = ""
                        row[f"background_corrected_max_intensity_{prefix}"] = ""
                        row[f"background_corrected_brightest5_mean_intensity_{prefix}"] = ""
                        row[f"background_corrected_sum_intensity_{prefix}"] = ""
            writer.writerow(row)


def process_stack(file_name):
    os.makedirs(roi_output_dir, exist_ok=True)
    stack_name = stack_name_from_aligned(file_name)
    stack_path = os.path.join(aligned_dir, file_name)
    projection_path = os.path.join(roi_output_dir, f"{stack_name}_max_projection.tif")
    projection_preview_path = os.path.join(roi_output_dir, f"{stack_name}_max_projection.jpg")
    rois_path = os.path.join(roi_output_dir, f"{stack_name}_rois.csv")
    overlay_path = os.path.join(roi_output_dir, f"{stack_name}_roi_overlay.jpg")
    video_path = os.path.join(roi_output_dir, f"{stack_name}_roi_overlay.mp4")
    intensity_path = os.path.join(roi_output_dir, f"{stack_name}_roi_intensity.csv")

    complete_outputs = [
        projection_path,
        projection_preview_path,
        rois_path,
        overlay_path,
        video_path,
        intensity_path,
    ]
    if (
        not OVERWRITE_EXISTING
        and all(os.path.exists(path) for path in complete_outputs)
        and intensity_csv_matches_current_format(intensity_path)
    ):
        print(f"[skip] {stack_name}: ROI outputs already exist")
        return

    print(f"\nProcessing {stack_name}")
    aligned_ok_frames, alignment_rows = load_aligned_ok_frames(stack_name)
    if not aligned_ok_frames:
        print(f"[skip] {stack_name}: no usable frames in the new 07 alignment CSV")
        return
    head_angles = load_head_angles(stack_name)
    print(f"Using {len(aligned_ok_frames)} usable aligned frame(s) for projection, video, and intensity.")

    projection = max_projection(stack_path, aligned_ok_frames)
    tifffile.imwrite(projection_path, projection)
    cv2.imwrite(projection_preview_path, normalize_for_display(projection))

    existing_rois = load_rois(rois_path)
    if existing_rois:
        answer = input(f"Found existing ROI file for {stack_name}. Reuse without editing? [y/N]: ").strip().lower()
        rois = existing_rois if answer in ("y", "yes") else draw_rois(projection, stack_name, existing_rois)
    else:
        rois = draw_rois(projection, stack_name)

    if not rois:
        print(f"No ROIs for {stack_name}; skipping intensity export.")
        return

    save_rois(rois_path, rois)
    save_roi_overlay(projection, rois, overlay_path)
    save_roi_video(stack_path, rois, video_path, aligned_ok_frames)
    measure_intensity(
        stack_name,
        stack_path,
        rois,
        intensity_path,
        aligned_ok_frames,
        head_angles,
        alignment_rows,
    )
    print(f"Saved max projection: {projection_path}")
    print(f"Saved ROI overlay: {overlay_path}")
    print(f"Saved ROI video: {video_path}")
    print(f"Saved ROIs: {rois_path}")
    print(f"Saved intensity CSV: {intensity_path}")


def main():
    files = aligned_stack_files()
    if not files:
        print(f"No aligned TIFF files found in {aligned_dir}")
        return
    for file_name in files:
        process_stack(file_name)


if __name__ == "__main__":
    main()
