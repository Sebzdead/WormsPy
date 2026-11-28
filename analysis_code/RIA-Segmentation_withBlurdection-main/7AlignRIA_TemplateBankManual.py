"""
Align RIA crops using a template bank plus manual template alignment.

Workflow:
1. Build a greedy template bank from crop JPG frames.
   A frame joins an existing template only if ROI NCC >= TEMPLATE_MATCH_THRESHOLD.
   Otherwise it becomes a new template, until MAX_TEMPLATES is reached.
2. Let the user manually rotate/translate each template to a common orientation.
3. Apply that template-level transform to every frame assigned to the template.

Inputs:
- 04_ria_crop/<stack>_crop.tif
- 06_crop_jpg/<stack>_crop_jpg/*.jpg
- optional: 07_ria_aligned/previews/<stack>_ecc_roi.csv

Outputs:
- 07_ria_template_bank_aligned/<stack>_aligned.tif
- 07_ria_template_bank_aligned/<stack>_template_bank_assignments.csv
- 07_ria_template_bank_aligned/<stack>_template_transforms.csv
- previews under 07_ria_template_bank_aligned/previews/
"""
import csv
import os
import random
import sys

import cv2
import numpy as np
import tifffile
from tqdm import tqdm


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260529"

CROP_SUBDIR = "04_ria_crop"
JPG_CROP_SUBDIR = "06_crop_jpg"
OLD_ALIGNED_SUBDIR = "07_ria_aligned"
OUTPUT_SUBDIR = "07_ria_template_bank_aligned"

TEMPLATE_MATCH_THRESHOLD = 0.90
MAX_TEMPLATES = 24
RANDOM_SEED = 1573
PREVIEW_TILE_COUNT = 25

WARP_MODE = cv2.MOTION_EUCLIDEAN
MAX_ITERATIONS = 200
TERMINATION_EPS = 1e-6
ECC_GAUSS_FILT_SIZE = 5
ECC_START_ROTATIONS_DEG = (0, -90, 90, -45, 45, -30, 30, -15, 15, 180)

USE_EXISTING_ECC_ROI = True
REMOVE_SOMA_FOR_MATCHING = True
SOMA_REMOVE_RADIUS_PX = 5
SOMA_BRIGHT_PERCENTILE = 96.0


crop_dir = os.path.join(RESULTS_ROOT, RUN_ID, CROP_SUBDIR)
jpg_crop_dir = os.path.join(RESULTS_ROOT, RUN_ID, JPG_CROP_SUBDIR)
old_aligned_dir = os.path.join(RESULTS_ROOT, RUN_ID, OLD_ALIGNED_SUBDIR)
out_dir = os.path.join(RESULTS_ROOT, RUN_ID, OUTPUT_SUBDIR)


def parse_args():
    only_stack = ""
    for idx, arg in enumerate(sys.argv[1:], 1):
        if arg.startswith("--only-stack="):
            only_stack = arg.split("=", 1)[1].strip()
        elif arg == "--only-stack" and idx + 1 < len(sys.argv):
            only_stack = sys.argv[idx + 1].strip()
    return only_stack


def ensure_gray(image):
    image = np.squeeze(image)
    if image.ndim == 2:
        return image
    if image.ndim == 3 and image.shape[2] in (3, 4):
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    raise ValueError(f"Expected grayscale image, got shape={image.shape}")


def normalize_uint8(image):
    image = np.asarray(image)
    if image.dtype == np.uint8:
        return image
    finite = image[np.isfinite(image)]
    if finite.size == 0:
        return np.zeros(image.shape, dtype=np.uint8)
    lo = float(finite.min())
    hi = float(finite.max())
    if hi <= lo:
        return np.zeros(image.shape, dtype=np.uint8)
    return np.clip((image.astype(np.float32) - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)


def stack_name_from_crop_name(name):
    return name[:-len("_crop.tif")]


def crop_tifs():
    if not os.path.isdir(crop_dir):
        return []
    return sorted(name for name in os.listdir(crop_dir) if name.endswith("_crop.tif"))


def jpg_folder_for_stack(stack_name):
    return os.path.join(jpg_crop_dir, f"{stack_name}_crop_jpg")


def read_jpg_frame(stack_name, frame_idx, shape=None):
    folder = jpg_folder_for_stack(stack_name)
    for name in (f"{frame_idx:06d}.jpg", f"{frame_idx}.jpg"):
        path = os.path.join(folder, name)
        if os.path.exists(path):
            image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if image is not None and shape is not None and image.shape[:2] != shape:
                image = cv2.resize(image, (shape[1], shape[0]), interpolation=cv2.INTER_AREA)
            return image
    return None


def read_csv(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def existing_roi_mask(stack_name, shape):
    if not USE_EXISTING_ECC_ROI:
        return None
    path = os.path.join(old_aligned_dir, "previews", f"{stack_name}_ecc_roi.csv")
    if not os.path.exists(path):
        return None
    rows = read_csv(path)
    if not rows or not rows[0].get("shape"):
        return None
    row = rows[0]
    try:
        x = int(float(row["x"]))
        y = int(float(row["y"]))
        w = int(float(row["width"]))
        h = int(float(row["height"]))
    except (KeyError, ValueError):
        return None
    mask = np.zeros(shape, dtype=np.uint8)
    center = (int(round(x + w / 2)), int(round(y + h / 2)))
    axes = (max(1, int(round(w / 2))), max(1, int(round(h / 2))))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
    return mask


def max_projection_from_jpg(stack_name, shape):
    folder = jpg_folder_for_stack(stack_name)
    max_img = None
    if os.path.isdir(folder):
        names = sorted(name for name in os.listdir(folder) if name.lower().endswith((".jpg", ".jpeg", ".png")))
        for name in names:
            image = cv2.imread(os.path.join(folder, name), cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue
            if image.shape[:2] != shape:
                image = cv2.resize(image, (shape[1], shape[0]), interpolation=cv2.INTER_AREA)
            max_img = image if max_img is None else np.maximum(max_img, image)
    return max_img if max_img is not None else np.zeros(shape, dtype=np.uint8)


def draw_ellipse_roi(stack_name, image):
    scale = 8 if max(image.shape[:2]) <= 90 else 3
    display = cv2.resize(cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    state = {"drawing": False, "start": None, "current": None, "roi": None}

    def norm_box(a, b):
        x1, y1 = a
        x2, y2 = b
        return min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)

    def on_mouse(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            state["drawing"] = True
            state["start"] = (x, y)
            state["current"] = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and state["drawing"]:
            state["current"] = (x, y)
        elif event == cv2.EVENT_LBUTTONUP and state["drawing"]:
            state["drawing"] = False
            state["current"] = (x, y)
            box = norm_box(state["start"], state["current"])
            if box[2] > 2 and box[3] > 2:
                state["roi"] = box

    window = f"Draw template-bank ROI: {stack_name}"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, 900, 700)
    cv2.setMouseCallback(window, on_mouse)
    while True:
        canvas = display.copy()
        cv2.putText(canvas, "Drag ellipse ROI. Enter accept, Esc/q full image", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        box = state["roi"]
        if state["drawing"] and state["start"] is not None and state["current"] is not None:
            box = norm_box(state["start"], state["current"])
        if box is not None:
            x, y, w, h = box
            cv2.ellipse(canvas, (int(x + w / 2), int(y + h / 2)), (max(1, int(w / 2)), max(1, int(h / 2))), 0, 0, 360, (0, 255, 255), 2)
        cv2.imshow(window, canvas)
        key = cv2.waitKey(30) & 0xFF
        if key in (13, 32, 27, ord("q"), ord("Q")):
            break
    cv2.destroyWindow(window)
    if state["roi"] is None:
        return None
    x, y, w, h = state["roi"]
    x, y, w, h = [int(round(v / scale)) for v in (x, y, w, h)]
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    center = (int(round(x + w / 2)), int(round(y + h / 2)))
    axes = (max(1, int(round(w / 2))), max(1, int(round(h / 2))))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
    return mask


def detect_soma_mask(image, roi_mask=None):
    if not REMOVE_SOMA_FOR_MATCHING:
        return None
    image = ensure_gray(image)
    mask = roi_mask if roi_mask is not None else (image > 0).astype(np.uint8) * 255
    if int((mask > 0).sum()) < 3:
        return None
    values = image[mask > 0]
    if values.size == 0:
        return None
    threshold = max(float(np.percentile(values, SOMA_BRIGHT_PERCENTILE)), float(values.max()) * 0.75)
    bright = ((image >= threshold) & (mask > 0)).astype(np.uint8)
    if int(bright.sum()) < 3:
        _, _, _, max_loc = cv2.minMaxLoc(image, mask=mask)
        center = max_loc
    else:
        _n, _labels, _stats, centroids = cv2.connectedComponentsWithStats(bright, connectivity=8)
        center = tuple(int(round(v)) for v in centroids[1]) if len(centroids) > 1 else cv2.minMaxLoc(image, mask=mask)[3]
    soma = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.circle(soma, center, SOMA_REMOVE_RADIUS_PX, 255, -1)
    return ((soma > 0) & (mask > 0)).astype(np.uint8) * 255


def prepare_match_image(image, roi_mask):
    image = normalize_uint8(ensure_gray(image))
    soma_mask = detect_soma_mask(image, roi_mask)
    if soma_mask is not None:
        image = cv2.inpaint(image, soma_mask, 3, cv2.INPAINT_TELEA)
    image = cv2.GaussianBlur(image, (3, 3), 0)
    if roi_mask is not None:
        image = np.where(roi_mask > 0, image, 0).astype(np.uint8)
    return image


def roi_ncc(a, b, roi_mask):
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    if roi_mask is not None:
        keep = roi_mask > 0
        a = a[keep]
        b = b[keep]
    else:
        a = a.reshape(-1)
        b = b.reshape(-1)
    if a.size < 4:
        return np.nan
    a -= float(a.mean())
    b -= float(b.mean())
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-8:
        return np.nan
    return float(np.dot(a, b) / denom)


def rotate_translate(image, angle_deg, tx=0, ty=0):
    h, w = image.shape[:2]
    center = ((w - 1) / 2.0, (h - 1) / 2.0)
    matrix = cv2.getRotationMatrix2D(center, float(angle_deg), 1.0)
    matrix[0, 2] += float(tx)
    matrix[1, 2] += float(ty)
    return cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def warp_frame(frame, warp_matrix):
    h, w = frame.shape[:2]
    return cv2.warpAffine(
        frame,
        warp_matrix,
        (w, h),
        flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )


def identity_warp():
    return np.eye(2, 3, dtype=np.float32)


def initial_warp(angle_deg=0.0):
    theta = np.deg2rad(float(angle_deg))
    matrix = np.eye(2, 3, dtype=np.float32)
    matrix[0, 0] = np.cos(theta)
    matrix[0, 1] = -np.sin(theta)
    matrix[1, 0] = np.sin(theta)
    matrix[1, 1] = np.cos(theta)
    return matrix


def warp_rotation_deg(warp_matrix):
    if warp_matrix is None:
        return np.nan
    return float(np.degrees(np.arctan2(float(warp_matrix[1, 0]), float(warp_matrix[0, 0]))))


def warp_values(prefix, warp_matrix):
    if warp_matrix is None:
        return {f"{prefix}{name}": "" for name in ("M00", "M01", "M02", "M10", "M11", "M12")}
    return {
        f"{prefix}M00": f"{float(warp_matrix[0, 0]):.8f}",
        f"{prefix}M01": f"{float(warp_matrix[0, 1]):.8f}",
        f"{prefix}M02": f"{float(warp_matrix[0, 2]):.8f}",
        f"{prefix}M10": f"{float(warp_matrix[1, 0]):.8f}",
        f"{prefix}M11": f"{float(warp_matrix[1, 1]):.8f}",
        f"{prefix}M12": f"{float(warp_matrix[1, 2]):.8f}",
    }


def warp_from_row(row, prefix="ecc_"):
    try:
        return np.array([
            [float(row[f"{prefix}M00"]), float(row[f"{prefix}M01"]), float(row[f"{prefix}M02"])],
            [float(row[f"{prefix}M10"]), float(row[f"{prefix}M11"]), float(row[f"{prefix}M12"])],
        ], dtype=np.float32)
    except (KeyError, TypeError, ValueError):
        return identity_warp()


def ecc_match_to_template(template_image, current_image, roi_mask):
    template_proc = template_image.astype(np.float32) / 255.0
    current_proc = current_image.astype(np.float32) / 255.0
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, MAX_ITERATIONS, TERMINATION_EPS)
    best = None
    errors = 0
    for start_angle in ECC_START_ROTATIONS_DEG:
        try:
            cc, warp = cv2.findTransformECC(
                template_proc,
                current_proc,
                initial_warp(start_angle),
                WARP_MODE,
                criteria,
                roi_mask,
                ECC_GAUSS_FILT_SIZE,
            )
        except cv2.error:
            errors += 1
            continue
        if best is None or float(cc) > best["cc"]:
            best = {"cc": float(cc), "warp": warp.copy(), "start_angle": start_angle, "errors": errors}
    if best is None:
        return np.nan, None, "", errors
    return best["cc"], best["warp"], best["start_angle"], best["errors"]


def build_template_bank(stack_name, n_frames, shape, roi_mask):
    templates = []
    assignments = []
    prepared_frames = {}
    for frame_idx in tqdm(range(n_frames), desc=f"Load match frames {stack_name}"):
        image = read_jpg_frame(stack_name, frame_idx, shape)
        if image is not None:
            prepared_frames[frame_idx] = prepare_match_image(image, roi_mask)
    remaining = set(prepared_frames.keys())
    rng = random.Random(RANDOM_SEED)
    assignment_by_frame = {}

    while remaining and len(templates) < MAX_TEMPLATES:
        template_frame = rng.choice(sorted(remaining))
        template_id = len(templates)
        template_image = prepared_frames[template_frame]
        template = {"id": template_id, "frame": template_frame, "image": template_image, "count": 0}
        templates.append(template)
        print(f"[template bank] template {template_id}: seed frame {template_frame}, remaining={len(remaining)}")

        matched_now = []
        for frame_idx in tqdm(sorted(remaining), desc=f"Match template {template_id}", leave=False):
            current = prepared_frames[frame_idx]
            if frame_idx == template_frame:
                cc = 1.0
                warp = identity_warp()
                start_angle = 0
                errors = 0
            else:
                cc, warp, start_angle, errors = ecc_match_to_template(template_image, current, roi_mask)
            if np.isfinite(cc) and cc >= TEMPLATE_MATCH_THRESHOLD:
                assignment = {
                    "frame": frame_idx,
                    "template_id": template_id,
                    "template_frame": template_frame,
                    "match_cc": cc,
                    "ecc_start_angle": start_angle,
                    "ecc_rotation_deg": warp_rotation_deg(warp),
                    "ecc_errors": errors,
                    "added_template": 1 if frame_idx == template_frame else 0,
                }
                assignment.update(warp_values("ecc_", warp))
                assignment_by_frame[frame_idx] = assignment
                matched_now.append(frame_idx)
        for frame_idx in matched_now:
            remaining.discard(frame_idx)
        template["count"] = len(matched_now)
        print(f"[template bank] template {template_id}: matched {len(matched_now)} frame(s) with CC >= {TEMPLATE_MATCH_THRESHOLD:.2f}")

    if remaining:
        print(f"[template bank] {len(remaining)} frame(s) remained unmatched; assigning to best existing template.")
        for frame_idx in tqdm(sorted(remaining), desc="Assign leftovers", leave=False):
            current = prepared_frames[frame_idx]
            best = None
            for template in templates:
                cc, warp, start_angle, errors = ecc_match_to_template(template["image"], current, roi_mask)
                if best is None or (np.isfinite(cc) and cc > best["match_cc"]):
                    best = {
                        "frame": frame_idx,
                        "template_id": template["id"],
                        "template_frame": template["frame"],
                        "match_cc": cc,
                        "ecc_start_angle": start_angle,
                        "ecc_rotation_deg": warp_rotation_deg(warp),
                        "ecc_errors": errors,
                        "added_template": 0,
                        "forced_low_cc": 1,
                    }
                    best.update(warp_values("ecc_", warp))
            if best is not None:
                assignment_by_frame[frame_idx] = best
                templates[int(best["template_id"])]["count"] += 1

    assignments = [assignment_by_frame[idx] for idx in sorted(assignment_by_frame)]
    return templates, assignments


def make_template_bank_preview(templates, out_path):
    if not templates:
        return
    tiles = []
    for t in templates:
        tile = cv2.cvtColor(normalize_uint8(t["image"]), cv2.COLOR_GRAY2BGR)
        cv2.putText(tile, f"id={t['id']} f={t['frame']} n={t['count']}", (3, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
        tiles.append(tile)
    h, w = tiles[0].shape[:2]
    cols = 6
    rows = int(np.ceil(len(tiles) / cols))
    canvas = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
    for i, tile in enumerate(tiles):
        y = (i // cols) * h
        x = (i % cols) * w
        canvas[y:y + h, x:x + w] = tile
    cv2.imwrite(out_path, cv2.resize(canvas, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST))


def manual_align_templates(stack_name, templates, roi_mask):
    transforms = {}
    if not templates:
        return transforms
    base = templates[0]["image"]
    total_templates = len(templates)
    window = f"Manual align template bank: {stack_name}"
    for template_number, t in enumerate(templates, start=1):
        is_first = template_number == 1
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window, 1200, 820)
        state = {"angle": 180, "tx": 40, "ty": 40, "saved": False}
        cv2.createTrackbar("angle +180", window, state["angle"], 360, lambda v, s=state: s.update(angle=v))
        cv2.createTrackbar("tx +40", window, state["tx"], 80, lambda v, s=state: s.update(tx=v))
        cv2.createTrackbar("ty +40", window, state["ty"], 80, lambda v, s=state: s.update(ty=v))
        quit_early = False
        while True:
            angle = state["angle"] - 180
            tx = state["tx"] - 40
            ty = state["ty"] - 40
            warped = rotate_translate(t["image"], angle, tx, ty)
            cc = 1.0 if is_first else roi_ncc(base, warped, roi_mask)
            diff = cv2.absdiff(base, warped)
            max_overlay = np.maximum(base, warped)
            tiles = [
                ("orientation reference", base),
                (f"template {t['id']} raw", t["image"]),
                ("manual warped", warped),
                ("abs diff", diff),
                ("max overlay", max_overlay),
            ]
            vis_tiles = []
            for label, img in tiles:
                tile = cv2.cvtColor(normalize_uint8(img), cv2.COLOR_GRAY2BGR)
                cv2.putText(tile, label, (3, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
                vis_tiles.append(tile)
            blank = np.zeros_like(vis_tiles[0])
            canvas = np.vstack([np.hstack(vis_tiles[:3]), np.hstack(vis_tiles[3:] + [blank])])
            display_scale = max(1, int(np.ceil(1000 / canvas.shape[1])))
            if display_scale > 1:
                canvas = cv2.resize(
                    canvas,
                    None,
                    fx=display_scale,
                    fy=display_scale,
                    interpolation=cv2.INTER_NEAREST,
                )
            header = np.zeros((68, canvas.shape[1], 3), dtype=np.uint8)
            progress_text = (
                f"Template {template_number}/{total_templates} | id={t['id']} | "
                f"seed frame={t['frame']} | class frames={t['count']}"
            )
            instruction = "First template: rotate to the common orientation, then save" if is_first else f"CC={cc:.4f}"
            settings_text = f"{instruction} | angle={angle} tx={tx} ty={ty} | S/Enter save, Q quit"
            cv2.putText(header, progress_text, (5, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 255), 1)
            cv2.putText(header, settings_text, (5, 49), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1)
            cv2.imshow(window, np.vstack([header, canvas]))
            key = cv2.waitKey(30) & 0xFF
            if key in (ord("s"), ord("S"), 13, 32):
                transforms[t["id"]] = {"template_id": t["id"], "template_frame": t["frame"], "angle": angle, "tx": tx, "ty": ty, "manual_cc": "" if is_first else cc}
                if is_first:
                    base = warped.copy()
                break
            if key in (27, ord("q"), ord("Q")):
                transforms[t["id"]] = {"template_id": t["id"], "template_frame": t["frame"], "angle": angle, "tx": tx, "ty": ty, "manual_cc": "" if is_first else cc}
                if is_first:
                    base = warped.copy()
                quit_early = True
                break
        try:
            cv2.destroyWindow(window)
        except Exception:
            pass
        if quit_early:
            return transforms
    return transforms


def write_csv(path, rows, fieldnames=None):
    if not rows:
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    extra = sorted({key for row in rows for key in row.keys()} - set(fieldnames))
    fieldnames = list(fieldnames) + extra
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_preview(frames, out_path):
    if not frames:
        return
    frames = [normalize_uint8(f) for f in frames[:PREVIEW_TILE_COUNT]]
    h, w = frames[0].shape[:2]
    cols = 5
    rows = int(np.ceil(len(frames) / cols))
    canvas = np.zeros((rows * h, cols * w), dtype=np.uint8)
    for i, frame in enumerate(frames):
        y = (i // cols) * h
        x = (i % cols) * w
        canvas[y:y + h, x:x + w] = frame
    cv2.imwrite(out_path, canvas)


def process_stack(crop_name):
    stack_name = stack_name_from_crop_name(crop_name)
    crop_path = os.path.join(crop_dir, crop_name)
    with tifffile.TiffFile(crop_path) as tif:
        shape = tif.pages[0].shape[:2]
        n_frames = len(tif.pages)

    preview_dir = os.path.join(out_dir, "previews")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(preview_dir, exist_ok=True)

    roi_mask = existing_roi_mask(stack_name, shape)
    if roi_mask is None:
        roi_mask = draw_ellipse_roi(stack_name, max_projection_from_jpg(stack_name, shape))
    if roi_mask is not None:
        cv2.imwrite(os.path.join(preview_dir, f"{stack_name}_template_bank_roi.jpg"), roi_mask)

    templates, assignments = build_template_bank(stack_name, n_frames, shape, roi_mask)
    if not templates:
        print(f"[template bank] {stack_name}: no templates built; skipping")
        return
    print(f"[template bank] {stack_name}: built {len(templates)} template(s)")
    make_template_bank_preview(templates, os.path.join(preview_dir, f"{stack_name}_template_bank.jpg"))

    transforms = manual_align_templates(stack_name, templates, roi_mask)
    transform_rows = list(transforms.values())
    write_csv(os.path.join(out_dir, f"{stack_name}_template_transforms.csv"), transform_rows)

    assign_by_frame = {int(row["frame"]): row for row in assignments}
    output_tif = os.path.join(out_dir, f"{stack_name}_aligned.tif")
    output_csv = os.path.join(out_dir, f"{stack_name}_template_bank_assignments.csv")
    preview_frames = []
    final_rows = []

    last_assignment = assignments[0] if assignments else None
    with tifffile.TiffFile(crop_path) as tif, tifffile.TiffWriter(output_tif, bigtiff=False) as out:
        for frame_idx, page in enumerate(tqdm(tif.pages, desc=f"Apply bank {stack_name}")):
            frame = ensure_gray(page.asarray())
            assignment = assign_by_frame.get(frame_idx)
            if assignment is None:
                assignment = last_assignment
            else:
                last_assignment = assignment
            template_id = int(assignment["template_id"]) if assignment is not None else 0
            tr = transforms.get(template_id, transforms.get(0, {"angle": 0, "tx": 0, "ty": 0, "manual_cc": ""}))
            ecc_warp = warp_from_row(assignment, "ecc_") if assignment is not None else identity_warp()
            frame_to_template = warp_frame(frame, ecc_warp)
            aligned = rotate_translate(frame_to_template, tr["angle"], tr["tx"], tr["ty"])
            out.write(aligned, contiguous=True)
            if len(preview_frames) < PREVIEW_TILE_COUNT:
                preview_frames.append(aligned)
            final_rows.append({
                "frame": frame_idx,
                "template_id": template_id,
                "template_frame": assignment.get("template_frame", "") if assignment else "",
                "class_match_cc": f"{float(assignment.get('match_cc', np.nan)):.8f}" if assignment else "",
                "class_ecc_rotation_deg": assignment.get("ecc_rotation_deg", "") if assignment else "",
                "class_ecc_start_angle": assignment.get("ecc_start_angle", "") if assignment else "",
                "class_forced_low_cc": assignment.get("forced_low_cc", 0) if assignment else "",
                "template_manual_angle_deg": tr["angle"],
                "template_manual_tx": tr["tx"],
                "template_manual_ty": tr["ty"],
                "template_manual_cc": f"{float(tr['manual_cc']):.8f}" if tr.get("manual_cc") != "" else "",
            })
            final_rows[-1].update({key: assignment.get(key, "") for key in ("ecc_M00", "ecc_M01", "ecc_M02", "ecc_M10", "ecc_M11", "ecc_M12")} if assignment else {})

    write_csv(output_csv, final_rows)
    make_preview(preview_frames, os.path.join(preview_dir, f"{stack_name}_preview.jpg"))
    print(f"Saved template-bank aligned stack: {output_tif}")
    print(f"Saved assignments: {output_csv}")


def main():
    only_stack = parse_args()
    files = crop_tifs()
    if only_stack:
        target = f"{only_stack}_crop.tif"
        files = [name for name in files if name == target]
    if not files:
        print(f"No crop TIFF files found in {crop_dir}")
        return
    print(f"Found {len(files)} crop stack(s).")
    for idx, name in enumerate(files, 1):
        print(f"\n[{idx}/{len(files)}] Processing {name}")
        process_stack(name)


if __name__ == "__main__":
    main()
