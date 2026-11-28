"""
Manual review tool for low-CC ECC frames.

It loads frames marked low_cc / rotation_over_90 / ecc_failed in step 7,
lets the user manually rotate/translate the current frame against the template,
and reports the ROI Pearson CC for the manual alignment.

Controls:
- Trackbars: frame, angle, tx, ty
- n / p: next / previous bad frame
- s: save current manual result
- q / Esc: quit
"""
import csv
import os

import cv2
import numpy as np


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "old"

JPG_CROP_SUBDIR = "06_crop_jpg"
RIA_MASK_SUBDIR = "04_ria_mask"
ALIGNED_SUBDIR = "07_ria_aligned"

BAD_STATUSES = {"low_cc", "rotation_over_90", "ecc_failed"}
MAX_BAD_FRAMES = 300

USE_CLAHE_FOR_ECC = True
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID_SIZE = (4, 4)
ECC_GAMMA = 1.0
ECC_DISPLAY_MIN = 0
ECC_DISPLAY_MAX = 255

REMOVE_SOMA_FOR_ECC = True
SOMA_REMOVE_RADIUS_PX = 5
SOMA_BRIGHT_PERCENTILE = 96.0
SOMA_MIN_AREA = 3
SOMA_MAX_AREA = 220
SOMA_FILL_MODE = "inpaint"


def ensure_gray_2d(image):
    if image is None:
        return None
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


def apply_ecc_contrast(image):
    image = ensure_gray_2d(image)
    display_min = int(np.clip(ECC_DISPLAY_MIN, 0, 254))
    display_max = int(np.clip(ECC_DISPLAY_MAX, display_min + 1, 255))
    if display_min != 0 or display_max != 255:
        image = image.astype(np.float32)
        image = (image - display_min) * (255.0 / max(1.0, display_max - display_min))
        image = np.clip(image, 0, 255).astype(np.uint8)
    if USE_CLAHE_FOR_ECC and float(CLAHE_CLIP_LIMIT) > 0:
        clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_TILE_GRID_SIZE)
        image = clahe.apply(image)
    if abs(float(ECC_GAMMA) - 1.0) > 1e-6:
        gamma = max(0.05, float(ECC_GAMMA))
        table = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)], dtype=np.uint8)
        image = cv2.LUT(image, table)
    return cv2.GaussianBlur(image, (3, 3), 0)


def detect_soma_mask(image, ria_mask=None):
    image = ensure_gray_2d(image)
    if not REMOVE_SOMA_FOR_ECC:
        return None
    if ria_mask is not None:
        mask = (ria_mask > 0).astype(np.uint8)
        if mask.shape[:2] != image.shape[:2]:
            mask = cv2.resize(mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    else:
        mask = (image > 0).astype(np.uint8)
    if int(mask.sum()) < SOMA_MIN_AREA:
        return None
    values = image[mask > 0]
    threshold = max(float(np.percentile(values, SOMA_BRIGHT_PERCENTILE)), float(values.max()) * 0.75)
    bright = ((image >= threshold) & (mask > 0)).astype(np.uint8)
    if int(bright.sum()) < SOMA_MIN_AREA:
        _, _, _, max_loc = cv2.minMaxLoc(image, mask=mask)
        center = max_loc
    else:
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bright, connectivity=8)
        best_label = None
        best_score = -1.0
        for label in range(1, num_labels):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if area < SOMA_MIN_AREA or area > SOMA_MAX_AREA:
                continue
            component = labels == label
            score = float(image[component].mean()) * np.sqrt(float(area))
            if score > best_score:
                best_score = score
                best_label = label
        if best_label is None:
            _, _, _, max_loc = cv2.minMaxLoc(image, mask=mask)
            center = max_loc
        else:
            cx, cy = centroids[best_label]
            center = (int(round(cx)), int(round(cy)))
    soma = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.circle(soma, center, int(SOMA_REMOVE_RADIUS_PX), 255, -1)
    soma = ((soma > 0) & (mask > 0)).astype(np.uint8) * 255
    return soma if int((soma > 0).sum()) >= SOMA_MIN_AREA else None


def remove_soma_for_ecc(image, ria_mask=None):
    image = ensure_gray_2d(image)
    soma_mask = detect_soma_mask(image, ria_mask)
    if soma_mask is None:
        return image
    if SOMA_FILL_MODE == "inpaint":
        return cv2.inpaint(image.astype(np.uint8, copy=False), soma_mask.astype(np.uint8, copy=False), 3, cv2.INPAINT_TELEA)
    cleaned = image.copy()
    cleaned[soma_mask > 0] = 0
    return cleaned


def read_csv(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def stack_names():
    aligned_dir = os.path.join(RESULTS_ROOT, RUN_ID, ALIGNED_SUBDIR)
    if not os.path.isdir(aligned_dir):
        return []
    return sorted(name[:-len("_alignment.csv")] for name in os.listdir(aligned_dir) if name.endswith("_alignment.csv"))


def read_jpg_frame(stack_name, frame_idx):
    folder = os.path.join(RESULTS_ROOT, RUN_ID, JPG_CROP_SUBDIR, f"{stack_name}_crop_jpg")
    for name in (f"{frame_idx:06d}.jpg", f"{frame_idx}.jpg"):
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return None


def read_roi(stack_name, shape):
    path = os.path.join(RESULTS_ROOT, RUN_ID, ALIGNED_SUBDIR, "previews", f"{stack_name}_ecc_roi.csv")
    if not os.path.exists(path):
        return None
    rows = read_csv(path)
    if not rows or not rows[0].get("shape"):
        return None
    row = rows[0]
    x = int(float(row["x"]))
    y = int(float(row["y"]))
    w = int(float(row["width"]))
    h = int(float(row["height"]))
    mask = np.zeros(shape, dtype=np.uint8)
    center = (int(round(x + w / 2)), int(round(y + h / 2)))
    axes = (max(1, int(round(w / 2))), max(1, int(round(h / 2))))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
    return mask


def prepare_for_cc(image, roi_mask):
    image = remove_soma_for_ecc(image, None)
    image = apply_ecc_contrast(image)
    if roi_mask is not None:
        image = np.where(roi_mask > 0, image, 0).astype(np.uint8)
    return image


def warp_manual(image, angle_deg, tx, ty):
    h, w = image.shape[:2]
    center = ((w - 1) / 2.0, (h - 1) / 2.0)
    matrix = cv2.getRotationMatrix2D(center, float(angle_deg), 1.0)
    matrix[0, 2] += float(tx)
    matrix[1, 2] += float(ty)
    return cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def roi_pearson_cc(reference, current, roi_mask):
    ref = reference.astype(np.float32)
    cur = current.astype(np.float32)
    if roi_mask is not None:
        keep = roi_mask > 0
        ref = ref[keep]
        cur = cur[keep]
    else:
        ref = ref.reshape(-1)
        cur = cur.reshape(-1)
    if ref.size < 4:
        return np.nan
    ref = ref - float(ref.mean())
    cur = cur - float(cur.mean())
    denom = float(np.linalg.norm(ref) * np.linalg.norm(cur))
    if denom <= 1e-8:
        return np.nan
    return float(np.dot(ref, cur) / denom)


def make_canvas(raw, reference, current, warped, diff, cc, angle, tx, ty, frame_idx, auto_cc, status):
    def tile(img, label):
        img = normalize_uint8(img)
        tile_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        cv2.putText(tile_img, label, (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1, cv2.LINE_AA)
        return tile_img
    tiles = [
        tile(raw, "raw"),
        tile(reference, "reference ROI"),
        tile(current, "current ROI"),
        tile(warped, "manual warped"),
        tile(diff, "abs diff"),
        tile(np.maximum(reference, warped), "max overlay"),
    ]
    h, w = tiles[0].shape[:2]
    canvas = np.vstack([np.hstack(tiles[:3]), np.hstack(tiles[3:])])
    header = np.zeros((48, canvas.shape[1], 3), dtype=np.uint8)
    cv2.putText(
        header,
        f"frame={frame_idx} status={status} auto_cc={auto_cc} manual_cc={cc:.4f} angle={angle:.1f} tx={tx} ty={ty}",
        (6, 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(header, "n/p frame, s save, q quit", (6, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (210, 210, 210), 1, cv2.LINE_AA)
    return np.vstack([header, canvas])


def choose_stack():
    names = stack_names()
    if not names:
        print("No alignment CSV found.")
        return None
    print("Stacks:")
    for i, name in enumerate(names, 1):
        print(f"{i}: {name}")
    raw = input("Choose stack number: ").strip()
    try:
        idx = int(raw) - 1
    except ValueError:
        idx = 0
    return names[max(0, min(len(names) - 1, idx))]


def main():
    stack_name = choose_stack()
    if not stack_name:
        return
    aligned_dir = os.path.join(RESULTS_ROOT, RUN_ID, ALIGNED_SUBDIR)
    rows = read_csv(os.path.join(aligned_dir, f"{stack_name}_alignment.csv"))
    bad_rows = [row for row in rows if row.get("status") in BAD_STATUSES][:MAX_BAD_FRAMES]
    if not bad_rows:
        print(f"No bad ECC frames found for {stack_name}.")
        return
    template_frame = int(float(bad_rows[0].get("template_frame") or 0))
    template = read_jpg_frame(stack_name, template_frame)
    if template is None:
        print(f"Could not read template frame {template_frame}.")
        return
    roi_mask = read_roi(stack_name, template.shape)
    reference = prepare_for_cc(template, roi_mask)
    manual_template_dir = os.path.join(aligned_dir, "manual_templates")
    os.makedirs(manual_template_dir, exist_ok=True)

    state = {"idx": 0, "angle": 0, "tx": 0, "ty": 0}
    window = "Manual ECC CC review"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, 1200, 820)
    cv2.createTrackbar("bad frame index", window, 0, len(bad_rows) - 1, lambda v: state.update(idx=v))
    cv2.createTrackbar("angle +180", window, 180, 360, lambda v: state.update(angle=v - 180))
    cv2.createTrackbar("tx +40", window, 40, 80, lambda v: state.update(tx=v - 40))
    cv2.createTrackbar("ty +40", window, 40, 80, lambda v: state.update(ty=v - 40))

    out_path = os.path.join(aligned_dir, f"{stack_name}_manual_lowcc_review.csv")
    saved = []
    while True:
        row = bad_rows[state["idx"]]
        frame_idx = int(float(row["frame"]))
        raw = read_jpg_frame(stack_name, frame_idx)
        if raw is None:
            raw = np.zeros_like(template)
        current = prepare_for_cc(raw, roi_mask)
        warped = warp_manual(current, state["angle"], state["tx"], state["ty"])
        if roi_mask is not None:
            warped_roi = np.where(roi_mask > 0, warped, 0).astype(np.uint8)
        else:
            warped_roi = warped
        cc = roi_pearson_cc(reference, warped_roi, roi_mask)
        diff = cv2.absdiff(reference, warped_roi)
        canvas = make_canvas(
            raw,
            reference,
            current,
            warped_roi,
            diff,
            cc,
            state["angle"],
            state["tx"],
            state["ty"],
            frame_idx,
            row.get("cc", ""),
            row.get("status", ""),
        )
        cv2.imshow(window, canvas)
        key = cv2.waitKey(30) & 0xFF
        if key in (27, ord("q"), ord("Q")):
            break
        if key in (ord("n"), ord("N")):
            state["idx"] = min(len(bad_rows) - 1, state["idx"] + 1)
            cv2.setTrackbarPos("bad frame index", window, state["idx"])
        if key in (ord("p"), ord("P")):
            state["idx"] = max(0, state["idx"] - 1)
            cv2.setTrackbarPos("bad frame index", window, state["idx"])
        if key in (ord("s"), ord("S")):
            record = {
                "stack": stack_name,
                "frame": frame_idx,
                "status": row.get("status", ""),
                "auto_cc": row.get("cc", ""),
                "manual_cc": f"{cc:.8f}" if np.isfinite(cc) else "",
                "manual_angle_deg": state["angle"],
                "manual_tx": state["tx"],
                "manual_ty": state["ty"],
            }
            saved.append(record)
            frame_template_path = os.path.join(manual_template_dir, f"{stack_name}_manual_frame_{frame_idx:06d}.jpg")
            cv2.imwrite(frame_template_path, warped_roi)
            record["manual_template_frame_path"] = frame_template_path
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(record.keys()))
                writer.writeheader()
                writer.writerows(saved)
            print(
                f"Saved manual CC/template frame: frame={frame_idx}, cc={cc:.4f}, "
                f"template_frame={frame_template_path}, csv={out_path}"
            )
    cv2.destroyWindow(window)
    print(f"Saved {len(saved)} manual review row(s): {out_path}")


if __name__ == "__main__":
    main()
