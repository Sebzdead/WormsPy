"""
Align cropped RIA frames using ECC motion correction.

This version keeps the same folder structure as 5AlignRIATemplate.py, but replaces
its morphology/template-rotation alignment with the ECC registration method from
tempMatch2.py.

Inputs:
- 04_ria_crop/<stack>_crop.tif
- optional: 04_ria_head_anchor/<stack>_ria_anchor.csv, used only to choose a good template frame

Outputs:
- 07_ria_aligned/<stack>_aligned.tif
- 07_ria_aligned/<stack>_alignment.csv
- 07_ria_aligned/previews/<stack>_preview.jpg
- 07_ria_aligned/previews/<stack>_template_frame_<n>.jpg
- optional debug images in 07_ria_aligned/debug/<stack>/
"""
import csv
import os
import shutil
import sys
from collections import Counter

import cv2
import numpy as np
import tifffile
from tqdm import tqdm


# =========================
# Directory settings
# =========================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "old"
LOCAL_TEMP_ROOT = r"C:\sam2_temp"

CROP_SUBDIR = "04_ria_crop"
JPG_CROP_SUBDIR = "06_crop_jpg"
RIA_ANCHOR_SUBDIR = "04_ria_head_anchor"
RIA_MASK_SUBDIR = "04_ria_mask"
ALIGNED_SUBDIR = "07_ria_aligned"
MANUAL_TEMPLATE_SUBDIR = "manual_templates"

crop_dir = os.path.join(RESULTS_ROOT, RUN_ID, CROP_SUBDIR)
jpg_crop_dir = os.path.join(RESULTS_ROOT, RUN_ID, JPG_CROP_SUBDIR)
ria_anchor_dir = os.path.join(RESULTS_ROOT, RUN_ID, RIA_ANCHOR_SUBDIR)
ria_mask_dir = os.path.join(RESULTS_ROOT, RUN_ID, RIA_MASK_SUBDIR)
aligned_dir = os.path.join(RESULTS_ROOT, RUN_ID, ALIGNED_SUBDIR)
manual_template_dir = os.path.join(aligned_dir, MANUAL_TEMPLATE_SUBDIR)


# =========================
# ECC settings
# =========================
# cv2.MOTION_TRANSLATION = x/y translation only, most stable
# cv2.MOTION_EUCLIDEAN = translation + rotation, recommended for your RIA crops
# cv2.MOTION_AFFINE = translation + rotation + scale/shear, more flexible but less stable
WARP_MODE = cv2.MOTION_EUCLIDEAN
MAX_ITERATIONS = 300
TERMINATION_EPS = 1e-6
ECC_GAUSS_FILT_SIZE = 5

# Template choice. If None, the script chooses a high-signal frame automatically.
TEMPLATE_FRAME = None
TEMPLATE_SEARCH_LIMIT = 500
MIN_TEMPLATE_BLUR_SCORE = 5.0
INTERACTIVE_TEMPLATE_SELECTION = "--auto-template" not in sys.argv
TEMPLATE_CANDIDATE_COUNT = 30

# If True, use the previous frame's successful warp as the initial guess.
# This makes ECC smoother and usually faster.
USE_PREVIOUS_WARP = False
LIMIT_ROTATION_BY_PREVIOUS_FRAME = False
MAX_ROTATION_DELTA_DEG = 8.0
LIMIT_TRANSLATION_BY_PREVIOUS_FRAME = False
MAX_TRANSLATION_DELTA_PX = 4.0
USE_DYNAMIC_MAX_REFERENCE = False
ECC_MULTI_START = True
ECC_MULTI_START_RETRY_BELOW_CC = 0.6
ECC_MULTI_START_ROTATIONS_DEG = (-45, -30, -20, -10, 10, 20, 30, 45, 90, -90)
ECC_MULTI_START_TRANSLATIONS_PX = (0,)
MIN_ECC_CC = 0.6
MAX_ECC_ROTATION_ABS_DEG = None

# If ECC fails or a frame is skipped, write a zero frame.
FAILED_FRAME_MODE = "black"

# Debug preview settings
SAVE_DEBUG = True
DEBUG_CLEAR_ON_START = True
DEBUG_EVERY_N_FRAMES = 100
DEBUG_PRINT_EVERY_N_FRAMES = 5
DEBUG_PANEL_EVERY_N_FRAMES = 10
DEBUG_LOW_CC_THRESHOLD = 0.65
DEBUG_ROTATION_JUMP_DEG = 25.0
DEBUG_TRANSLATION_MAGNITUDE_PX = 12.0
PREVIEW_TILE_COUNT = 25

# If available, use SAM2 crop masks only to estimate the ECC warp.
# The saved aligned TIFF remains the original crop warped by that transform.
USE_RIA_MASK_FOR_ECC = True
REQUIRE_RIA_MASK_FOR_ECC = False
USE_RIA_MASK_BBOX_FOR_ECC = False
MASK_BBOX_PADDING = 4
MASK_BBOX_PADDING_FRACTION = 0.12
MASK_DILATE_ITERATIONS = 1
USE_CROP_JPG_FOR_ECC = True
REQUIRE_CROP_JPG_FOR_ECC = True
USE_FULL_CROP_FOR_ECC = True
USE_CLAHE_FOR_ECC = True
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID_SIZE = (4, 4)
ECC_GAMMA = 1.0
ECC_CONTRAST_ALPHA = 1.0
ECC_BRIGHTNESS_BETA = 0
ECC_DISPLAY_MIN = 0
ECC_DISPLAY_MAX = 255
INTERACTIVE_CONTRAST_TUNING = "--no-contrast-ui" not in sys.argv
# Default: tune each stack separately. Use --shared-contrast to tune once and
# reuse the same parameters for the remaining stacks.
TUNE_CONTRAST_EACH_STACK = "--shared-contrast" not in sys.argv
_contrast_tuned_once = False
INTERACTIVE_ECC_ROI = "--no-roi-ui" not in sys.argv
USE_SELECTED_ROI_FOR_ECC = True
REMOVE_SOMA_FOR_ECC = True
SOMA_REMOVE_RADIUS_PX = 7
SOMA_BRIGHT_PERCENTILE = 96.0
SOMA_MIN_AREA = 3
SOMA_MAX_AREA = 220
SOMA_FILL_MODE = "zero"  # "inpaint", "median", or "zero"

# Laplacian blur scores are kept only as diagnostics in the CSV.
# Frame rejection now uses the learned RIA blur classifier below.
ENABLE_MASKED_JPG_BLUR_DETECTION = False
MIN_TEMPLATE_MASKED_JPG_BLUR_SCORE = 200.0
MIN_FRAME_MASKED_JPG_BLUR_SCORE = 180.0
SKIP_BLURRY_ECC_FRAMES = False

# Optional learned frame-quality classifier. It runs before ECC and can reject
# blurry/ghosted/missing RIA frames that a simple Laplacian threshold misses.
USE_RIA_BLUR_CLASSIFIER = False
RIA_BLUR_CLASSIFIER_PATH = os.path.join(SCRIPT_DIR, "training_runs", "ria_blur_classifier", "weights", "best.pt")
RIA_BLUR_CLASSIFIER_DEVICE = "cpu"
RIA_BLUR_CLASSIFIER_IMGSZ = 64
RIA_BLUR_BAD_THRESHOLD = 0.5


# =========================
# Helper functions
# =========================
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
    out = np.clip((image - lo) / (hi - lo), 0, 1)
    return (out * 255).astype(np.uint8)


def ensure_gray_2d(image):
    image = normalize_uint8(image)
    image = np.squeeze(image)
    if image.ndim == 2:
        return image
    if image.ndim == 3:
        if image.shape[2] in (3, 4):
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if image.shape[0] in (3, 4):
            return cv2.cvtColor(np.transpose(image, (1, 2, 0)), cv2.COLOR_BGR2GRAY)
    raise ValueError(f"Expected a 2D grayscale image for ECC, got shape={image.shape}")


def apply_ecc_contrast(image):
    image = ensure_gray_2d(image)
    display_min = int(np.clip(ECC_DISPLAY_MIN, 0, 254))
    display_max = int(np.clip(ECC_DISPLAY_MAX, display_min + 1, 255))
    if display_min != 0 or display_max != 255:
        image = image.astype(np.float32)
        image = (image - display_min) * (255.0 / max(1.0, display_max - display_min))
        image = np.clip(image, 0, 255).astype(np.uint8)
    if abs(float(ECC_CONTRAST_ALPHA) - 1.0) > 1e-6 or int(ECC_BRIGHTNESS_BETA) != 0:
        image = cv2.convertScaleAbs(
            image,
            alpha=max(0.05, float(ECC_CONTRAST_ALPHA)),
            beta=int(ECC_BRIGHTNESS_BETA),
        )
    if USE_CLAHE_FOR_ECC and float(CLAHE_CLIP_LIMIT) > 0:
        clahe = cv2.createCLAHE(
            clipLimit=CLAHE_CLIP_LIMIT,
            tileGridSize=CLAHE_TILE_GRID_SIZE,
        )
        image = clahe.apply(image)
    if abs(float(ECC_GAMMA) - 1.0) > 1e-6:
        gamma = max(0.05, float(ECC_GAMMA))
        table = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)], dtype=np.uint8)
        image = cv2.LUT(image, table)
    return image


def preprocess_for_ecc(image):
    image = apply_ecc_contrast(image)
    image = cv2.GaussianBlur(image, (3, 3), 0)
    return image.astype(np.float32) / 255.0


def prepare_ecc_mask(mask, shape):
    if mask is None:
        return None
    mask = np.squeeze(mask)
    if mask.ndim != 2:
        return None
    if mask.shape[:2] != shape:
        mask = cv2.resize(mask.astype(np.uint8), (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)
    mask = (mask > 0).astype(np.uint8)
    if int(mask.sum()) < 8:
        return None
    if USE_RIA_MASK_BBOX_FOR_ECC:
        ys, xs = np.where(mask > 0)
        if len(xs) < 2 or len(ys) < 2:
            return None
        h, w = shape
        x1 = int(xs.min())
        x2 = int(xs.max()) + 1
        y1 = int(ys.min())
        y2 = int(ys.max()) + 1
        box_w = max(1, x2 - x1)
        box_h = max(1, y2 - y1)
        pad_x = max(int(MASK_BBOX_PADDING), int(round(box_w * MASK_BBOX_PADDING_FRACTION)))
        pad_y = max(int(MASK_BBOX_PADDING), int(round(box_h * MASK_BBOX_PADDING_FRACTION)))
        x1 = max(0, x1 - pad_x)
        x2 = min(w, x2 + pad_x)
        y1 = max(0, y1 - pad_y)
        y2 = min(h, y2 + pad_y)
        box_mask = np.zeros((h, w), dtype=np.uint8)
        box_mask[y1:y2, x1:x2] = 1
        return box_mask * 255
    if MASK_DILATE_ITERATIONS > 0:
        kernel = np.ones((3, 3), dtype=np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=MASK_DILATE_ITERATIONS)
    return (mask > 0).astype(np.uint8) * 255


def apply_mask_for_ecc(image, mask):
    image = ensure_gray_2d(image)
    if mask is None:
        return image
    mask = np.squeeze(mask)
    if mask.shape[:2] != image.shape[:2]:
        mask = cv2.resize(mask.astype(np.uint8), (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    return np.where(mask > 0, image, 0).astype(image.dtype, copy=False)


def detect_soma_mask(image, ria_mask=None):
    image = ensure_gray_2d(image)
    if not REMOVE_SOMA_FOR_ECC:
        return None
    if ria_mask is not None:
        mask = np.squeeze(ria_mask)
        if mask.shape[:2] != image.shape[:2]:
            mask = cv2.resize(mask.astype(np.uint8), (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
        mask = (mask > 0).astype(np.uint8)
    else:
        mask = (image > 0).astype(np.uint8)
    if int(mask.sum()) < SOMA_MIN_AREA:
        return None

    values = image[mask > 0]
    if values.size == 0:
        return None
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
        return image, 0
    cleaned = image.copy()
    soma_pixels = soma_mask > 0
    if SOMA_FILL_MODE == "inpaint":
        cleaned = cv2.inpaint(
            image.astype(np.uint8, copy=False),
            soma_mask.astype(np.uint8, copy=False),
            3,
            cv2.INPAINT_TELEA,
        )
    elif SOMA_FILL_MODE == "median":
        if ria_mask is not None:
            mask = np.squeeze(ria_mask)
            if mask.shape[:2] != image.shape[:2]:
                mask = cv2.resize(mask.astype(np.uint8), (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
            background = image[(mask > 0) & (~soma_pixels)]
        else:
            background = image[~soma_pixels]
        fill_value = int(np.median(background)) if background.size else 0
        cleaned[soma_pixels] = fill_value
    else:
        cleaned[soma_pixels] = 0
    return cleaned, int(np.count_nonzero(soma_pixels))


def masked_jpg_blur_score(image, mask):
    image = ensure_gray_2d(image)
    if mask is None:
        roi = image
    else:
        mask = mask > 0
        ys, xs = np.where(mask)
        if len(xs) < 8:
            return 0.0
        x1, x2 = int(xs.min()), int(xs.max()) + 1
        y1, y2 = int(ys.min()), int(ys.max()) + 1
        roi = np.where(mask, image, 0)[y1:y2, x1:x2]
    if roi.size == 0 or roi.max() <= roi.min():
        return 0.0
    return float(cv2.Laplacian(roi, cv2.CV_64F).var())


def blur_score(image):
    image = ensure_gray_2d(image)
    return float(cv2.Laplacian(image, cv2.CV_64F).var())


def make_contrast_tuning_canvas(raw_image, processed_image, stack_name, frame_idx=None):
    raw = ensure_gray_2d(raw_image)
    processed = ensure_gray_2d(processed_image)
    raw_bgr = cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR)
    processed_bgr = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
    canvas = np.concatenate([raw_bgr, processed_bgr], axis=1)
    scale = 5 if canvas.shape[0] <= 120 else 2
    canvas = cv2.resize(canvas, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    text = (
        f"{stack_name} | left raw, right ECC contrast | "
        f"min={ECC_DISPLAY_MIN}, max={ECC_DISPLAY_MAX}, "
        f"gamma={ECC_GAMMA:.2f}, CLAHE clip={CLAHE_CLIP_LIMIT:.1f}"
    )
    if frame_idx is not None:
        text += f", frame={frame_idx}"
    cv2.putText(canvas, text, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(
        canvas,
        f"Fiji range: min={ECC_DISPLAY_MIN} max={ECC_DISPLAY_MAX}",
        (8, 44),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(canvas, "Enter/Space: accept   Esc: keep current", (8, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    return canvas


def tune_ecc_contrast_if_needed(stack_name, example_image, frame_count=1, initial_frame_idx=0, frame_loader=None):
    global CLAHE_CLIP_LIMIT, CLAHE_TILE_GRID_SIZE, ECC_GAMMA
    global ECC_CONTRAST_ALPHA, ECC_BRIGHTNESS_BETA
    global ECC_DISPLAY_MIN, ECC_DISPLAY_MAX, _contrast_tuned_once
    if not INTERACTIVE_CONTRAST_TUNING:
        return
    if _contrast_tuned_once and not TUNE_CONTRAST_EACH_STACK:
        return

    raw = ensure_gray_2d(example_image)
    window_name = "ECC contrast tuning"
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 900, 700)
        if frame_count > 1:
            cv2.createTrackbar("frame", window_name, int(initial_frame_idx), max(1, int(frame_count) - 1), lambda _v: None)
        cv2.createTrackbar("min", window_name, int(ECC_DISPLAY_MIN), 254, lambda _v: None)
        cv2.createTrackbar("max", window_name, int(ECC_DISPLAY_MAX), 255, lambda _v: None)
        cv2.createTrackbar("gamma x100", window_name, max(5, int(round(ECC_GAMMA * 100))), 300, lambda _v: None)
        cv2.createTrackbar("CLAHE clip x10", window_name, max(0, int(round(CLAHE_CLIP_LIMIT * 10))), 100, lambda _v: None)
        cv2.createTrackbar("tile size", window_name, int(CLAHE_TILE_GRID_SIZE[0]), 16, lambda _v: None)
        last_frame_idx = None
        while True:
            frame_idx = int(cv2.getTrackbarPos("frame", window_name)) if frame_count > 1 else int(initial_frame_idx)
            if frame_idx != last_frame_idx and frame_loader is not None:
                loaded = frame_loader(frame_idx)
                if loaded is not None:
                    raw = ensure_gray_2d(loaded)
                last_frame_idx = frame_idx
            min_pos = cv2.getTrackbarPos("min", window_name)
            max_pos = cv2.getTrackbarPos("max", window_name)
            gamma_pos = max(5, cv2.getTrackbarPos("gamma x100", window_name))
            clip_pos = max(0, cv2.getTrackbarPos("CLAHE clip x10", window_name))
            tile_pos = max(2, cv2.getTrackbarPos("tile size", window_name))
            ECC_DISPLAY_MIN = int(min_pos)
            ECC_DISPLAY_MAX = int(max(max_pos, min_pos + 1))
            if ECC_DISPLAY_MAX != max_pos:
                cv2.setTrackbarPos("max", window_name, ECC_DISPLAY_MAX)
            CLAHE_CLIP_LIMIT = clip_pos / 10.0
            CLAHE_TILE_GRID_SIZE = (tile_pos, tile_pos)
            ECC_GAMMA = gamma_pos / 100.0
            processed = apply_ecc_contrast(raw)
            cv2.imshow(window_name, make_contrast_tuning_canvas(raw, processed, stack_name, frame_idx=frame_idx))
            key = cv2.waitKey(60) & 0xFF
            if key in (13, 32, 27, ord("q")):
                break
        cv2.destroyWindow(window_name)
        _contrast_tuned_once = True
        print(
            f"[contrast] ECC parameters: display_min={ECC_DISPLAY_MIN}, display_max={ECC_DISPLAY_MAX}, "
            f"gamma={ECC_GAMMA:.2f}, "
            f"CLAHE clip={CLAHE_CLIP_LIMIT:.2f}, tile={CLAHE_TILE_GRID_SIZE}"
        )
    except Exception as exc:
        print(f"[contrast] Could not open contrast tuning window; using current parameters. {exc}")


def build_ecc_max_projection(stack_name, crop_path, height, width, use_preprocessed=True):
    max_img = None

    def prepare_projection_frame(frame):
        frame = ensure_gray_2d(frame)
        if frame.shape[:2] != (height, width):
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
        if use_preprocessed:
            frame = preprocess_for_ecc(frame)
            frame = np.clip(frame * 255.0, 0, 255).astype(np.uint8)
        return frame

    folder = ecc_jpg_dir_for_stack(stack_name)
    if USE_CROP_JPG_FOR_ECC and os.path.isdir(folder):
        names = sorted(
            name for name in os.listdir(folder)
            if os.path.splitext(name)[-1].lower() in (".jpg", ".jpeg", ".png")
            and os.path.splitext(name)[0].isdigit()
        )
        for name in names:
            frame = cv2.imread(os.path.join(folder, name), cv2.IMREAD_GRAYSCALE)
            if frame is None:
                continue
            frame = prepare_projection_frame(frame)
            max_img = frame if max_img is None else np.maximum(max_img, frame)
    if max_img is not None:
        return max_img

    with tifffile.TiffFile(crop_path) as tif:
        for page in tif.pages:
            frame = prepare_projection_frame(page.asarray())
            max_img = frame if max_img is None else np.maximum(max_img, frame)
    return max_img if max_img is not None else np.zeros((height, width), dtype=np.uint8)


def draw_roi_preview(image, roi, out_path):
    canvas = cv2.cvtColor(ensure_gray_2d(image), cv2.COLOR_GRAY2BGR)
    if roi is not None:
        x, y, w, h = roi
        center = (int(round(x + w / 2)), int(round(y + h / 2)))
        axes = (max(1, int(round(w / 2))), max(1, int(round(h / 2))))
        cv2.ellipse(canvas, center, axes, 0, 0, 360, (0, 255, 255), 1)
    scale = 6 if max(canvas.shape[:2]) <= 120 else 2
    canvas = cv2.resize(canvas, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(out_path, canvas)


def select_ellipse_roi(window_name, image, scale):
    state = {
        "drawing": False,
        "start": None,
        "current": None,
        "roi": None,
    }

    def normalize_box(p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        return x, y, w, h

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
            bx, by, bw, bh = normalize_box(state["start"], state["current"])
            if bw > 2 and bh > 2:
                state["roi"] = (bx, by, bw, bh)

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 900, 700)
    cv2.setMouseCallback(window_name, on_mouse)
    while True:
        canvas = image.copy()
        cv2.putText(
            canvas,
            "Drag ellipse ROI. Enter/Space accept, c clear, Esc/q cancel",
            (8, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        box = state["roi"]
        if state["drawing"] and state["start"] is not None and state["current"] is not None:
            box = normalize_box(state["start"], state["current"])
        if box is not None:
            x, y, w, h = box
            center = (int(round(x + w / 2)), int(round(y + h / 2)))
            axes = (max(1, int(round(w / 2))), max(1, int(round(h / 2))))
            cv2.ellipse(canvas, center, axes, 0, 0, 360, (0, 255, 255), 2)
        cv2.imshow(window_name, canvas)
        key = cv2.waitKey(30) & 0xFF
        if key in (13, 32):
            break
        if key in (ord("c"), ord("C")):
            state["roi"] = None
        if key in (27, ord("q"), ord("Q")):
            state["roi"] = None
            break
    cv2.destroyWindow(window_name)
    if state["roi"] is None:
        return None
    sx, sy, sw, sh = state["roi"]
    return (
        max(0, int(round(sx / scale))),
        max(0, int(round(sy / scale))),
        max(1, int(round(sw / scale))),
        max(1, int(round(sh / scale))),
    )


def select_ecc_roi_from_max_projection(stack_name, crop_path, height, width, preview_dir):
    max_img = build_ecc_max_projection(stack_name, crop_path, height, width, use_preprocessed=True)
    max_path = os.path.join(preview_dir, f"{stack_name}_preprocessed_max_intensity.jpg")
    cv2.imwrite(max_path, max_img)
    roi_preview_path = os.path.join(preview_dir, f"{stack_name}_ecc_roi.jpg")
    roi_csv_path = os.path.join(preview_dir, f"{stack_name}_ecc_roi.csv")

    roi = None
    if INTERACTIVE_ECC_ROI:
        window_name = f"Draw ECC ROI: {stack_name}"
        try:
            display = cv2.cvtColor(max_img, cv2.COLOR_GRAY2BGR)
            scale = 8 if max_img.shape[0] <= 80 and max_img.shape[1] <= 80 else 3
            display = cv2.resize(display, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
            roi = select_ellipse_roi(window_name, display, scale)
            if roi is not None:
                x, y, w, h = roi
                if x + w > width:
                    w = width - x
                if y + h > height:
                    h = height - y
                roi = (x, y, max(1, w), max(1, h))
        except Exception as exc:
            print(f"[roi] Could not open ROI selector; ECC uses default region. {exc}")

    draw_roi_preview(max_img, roi, roi_preview_path)
    with open(roi_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["stack", "shape", "x", "y", "width", "height", "max_projection_path", "roi_preview_path"])
        writer.writeheader()
        writer.writerow({
            "stack": stack_name,
            "shape": "ellipse" if roi is not None else "",
            "x": "" if roi is None else roi[0],
            "y": "" if roi is None else roi[1],
            "width": "" if roi is None else roi[2],
            "height": "" if roi is None else roi[3],
            "max_projection_path": max_path,
            "roi_preview_path": roi_preview_path,
        })
    if roi is None:
        print(f"[roi] {stack_name}: no ROI selected; ECC uses default region. Max projection: {max_path}")
        return None, max_path, roi_preview_path
    print(f"[roi] {stack_name}: selected ROI x={roi[0]}, y={roi[1]}, w={roi[2]}, h={roi[3]}")
    print(f"[roi] {stack_name}: max projection saved: {max_path}")
    return roi, max_path, roi_preview_path


def roi_to_mask(roi, height, width):
    if roi is None:
        return None
    x, y, w, h = roi
    mask = np.zeros((height, width), dtype=np.uint8)
    center = (int(round(x + w / 2)), int(round(y + h / 2)))
    axes = (max(1, int(round(w / 2))), max(1, int(round(h / 2))))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
    return mask


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
    prob_bad = prob_by_label.get("bad", np.nan)
    prob_good = prob_by_label.get("good", np.nan)
    return str(label), prob_bad, prob_good


def signal_mask(image):
    image = normalize_uint8(image)
    positive = image[image > 0]
    if positive.size == 0:
        return np.zeros(image.shape, dtype=bool)
    threshold = np.percentile(positive, 70)
    return image >= threshold


def get_identity_warp(warp_mode):
    if warp_mode == cv2.MOTION_HOMOGRAPHY:
        return np.eye(3, 3, dtype=np.float32)
    return np.eye(2, 3, dtype=np.float32)


def make_initial_warp(warp_mode, angle_deg=0.0, tx=0.0, ty=0.0):
    if warp_mode == cv2.MOTION_HOMOGRAPHY:
        theta = np.deg2rad(float(angle_deg))
        matrix = np.eye(3, 3, dtype=np.float32)
        matrix[0, 0] = np.cos(theta)
        matrix[0, 1] = -np.sin(theta)
        matrix[1, 0] = np.sin(theta)
        matrix[1, 1] = np.cos(theta)
        matrix[0, 2] = float(tx)
        matrix[1, 2] = float(ty)
        return matrix
    if warp_mode == cv2.MOTION_TRANSLATION:
        matrix = np.eye(2, 3, dtype=np.float32)
        matrix[0, 2] = float(tx)
        matrix[1, 2] = float(ty)
        return matrix
    theta = np.deg2rad(float(angle_deg))
    matrix = np.eye(2, 3, dtype=np.float32)
    matrix[0, 0] = np.cos(theta)
    matrix[0, 1] = -np.sin(theta)
    matrix[1, 0] = np.sin(theta)
    matrix[1, 1] = np.cos(theta)
    matrix[0, 2] = float(tx)
    matrix[1, 2] = float(ty)
    return matrix


def ecc_initial_warps(primary_warp, warp_mode):
    warps = [("primary", primary_warp.copy())]
    if not ECC_MULTI_START:
        return warps
    seen = {"primary"}
    for angle in ECC_MULTI_START_ROTATIONS_DEG:
        for shift in ECC_MULTI_START_TRANSLATIONS_PX:
            candidates = [(0.0, 0.0)] if float(shift) == 0 else [
                (0.0, 0.0),
                (float(shift), 0.0),
                (-float(shift), 0.0),
                (0.0, float(shift)),
                (0.0, -float(shift)),
            ]
            for tx, ty in candidates:
                label = f"rot{float(angle):+.0f}_tx{tx:+.0f}_ty{ty:+.0f}"
                if label in seen:
                    continue
                seen.add(label)
                warps.append((label, make_initial_warp(warp_mode, angle, tx, ty)))
    return warps


def run_ecc_multistart(reference_proc, current_proc, primary_warp, warp_mode, criteria, input_mask, gauss_size):
    best_cc = -np.inf
    best_warp = None
    best_label = ""
    attempts = 0
    errors = 0
    rejected_rotation = 0
    attempt_summaries = []
    primary_error = None

    for label, init in ecc_initial_warps(primary_warp, warp_mode):
        attempts += 1
        try:
            cc, warp = cv2.findTransformECC(
                reference_proc,
                current_proc,
                init.copy(),
                warp_mode,
                criteria,
                input_mask,
                gauss_size,
            )
        except cv2.error as exc:
            errors += 1
            if label == "primary":
                primary_error = exc
            attempt_summaries.append(f"{label}:err")
            continue
        angle = warp_rotation_deg(warp)
        if (
            MAX_ECC_ROTATION_ABS_DEG is not None
            and np.isfinite(angle)
            and abs(float(angle)) > MAX_ECC_ROTATION_ABS_DEG
        ):
            rejected_rotation += 1
            attempt_summaries.append(f"{label}:cc={float(cc):.3f},rot={angle:.1f},reject_rot")
            continue
        attempt_summaries.append(f"{label}:cc={float(cc):.3f},rot={angle:.1f}")
        if np.isfinite(cc) and float(cc) > best_cc:
            best_cc = float(cc)
            best_warp = warp.copy()
            best_label = label
        if label == "primary" and best_cc >= ECC_MULTI_START_RETRY_BELOW_CC:
            break

    if best_warp is None:
        if rejected_rotation > 0:
            summary = " | ".join(attempt_summaries[:24])
            return np.nan, None, "rotation_over_90", attempts, errors, rejected_rotation, summary
        if primary_error is not None:
            raise primary_error
        raise cv2.error("findTransformECC failed for all multistart initializations")
    summary = " | ".join(attempt_summaries[:24])
    return best_cc, best_warp, best_label, attempts, errors, rejected_rotation, summary


def run_ecc_multitemplate(reference_entries, current_proc, primary_warp, warp_mode, criteria, input_mask, gauss_size):
    best = None
    total_attempts = 0
    total_errors = 0
    total_rejected_rotation = 0
    summaries = []
    rotation_over_90_only = False

    for template_label, reference_image, reference_proc in reference_entries:
        try:
            cc, warp, start_label, attempts, errors, rejected_rotation, summary = run_ecc_multistart(
                reference_proc,
                current_proc,
                primary_warp,
                warp_mode,
                criteria,
                input_mask,
                gauss_size,
            )
        except cv2.error:
            summaries.append(f"{template_label}:err")
            total_errors += 1
            continue

        total_attempts += attempts
        total_errors += errors
        total_rejected_rotation += rejected_rotation
        summaries.append(f"{template_label}[{start_label}]:cc={cc:.3f}; {summary}")
        if warp is None and start_label == "rotation_over_90":
            rotation_over_90_only = True
            continue
        if warp is None or not np.isfinite(cc):
            continue
        if best is None or float(cc) > float(best["cc"]):
            best = {
                "cc": float(cc),
                "warp": warp.copy(),
                "start_label": start_label,
                "template_label": template_label,
                "reference_image": reference_image,
            }

    summary_text = " || ".join(summaries[:12])
    if best is None:
        if rotation_over_90_only:
            return np.nan, None, "rotation_over_90", "", total_attempts, total_errors, total_rejected_rotation, summary_text, None
        raise cv2.error("ECC failed for all templates")
    return (
        best["cc"],
        best["warp"],
        best["start_label"],
        best["template_label"],
        total_attempts,
        total_errors,
        total_rejected_rotation,
        summary_text,
        best["reference_image"],
    )


def warp_frame(frame, warp_matrix, warp_mode, width, height):
    if warp_mode == cv2.MOTION_HOMOGRAPHY:
        return cv2.warpPerspective(
            frame,
            warp_matrix,
            (width, height),
            flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )
    return cv2.warpAffine(
        frame,
        warp_matrix,
        (width, height),
        flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )


def crop_stack_files():
    if not os.path.isdir(crop_dir):
        return []
    return sorted(f for f in os.listdir(crop_dir) if f.endswith("_crop.tif"))


def stack_name_from_crop(crop_name):
    return crop_name[:-len("_crop.tif")]


def load_manual_template_frames(stack_name, shape):
    if not os.path.isdir(manual_template_dir):
        return []
    prefix = f"{stack_name}_manual_frame_"
    templates = []
    for name in sorted(os.listdir(manual_template_dir)):
        if not name.startswith(prefix) or not name.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        path = os.path.join(manual_template_dir, name)
        image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            continue
        if image.shape[:2] != shape:
            image = cv2.resize(image, (shape[1], shape[0]), interpolation=cv2.INTER_AREA)
        label = os.path.splitext(name[len(prefix):])[0]
        templates.append((f"manual_{label}", image, path))
    return templates


def ria_mask_path_for_stack(stack_name):
    return os.path.join(ria_mask_dir, f"{stack_name}_ria_mask.tif")


def ecc_jpg_dir_for_stack(stack_name):
    return os.path.join(jpg_crop_dir, f"{stack_name}_crop_jpg")


def read_ecc_jpg_frame(stack_name, frame_idx, target_shape):
    if not USE_CROP_JPG_FOR_ECC:
        return None
    folder = ecc_jpg_dir_for_stack(stack_name)
    candidates = [
        os.path.join(folder, f"{frame_idx:06d}.jpg"),
        os.path.join(folder, f"{frame_idx}.jpg"),
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            continue
        if image.shape[:2] != target_shape:
            image = cv2.resize(image, (target_shape[1], target_shape[0]), interpolation=cv2.INTER_AREA)
        return image
    return None


def load_anchor_frames(stack_name):
    path = os.path.join(ria_anchor_dir, f"{stack_name}_ria_anchor.csv")
    if not os.path.exists(path):
        return set()
    frames = set()
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                frames.add(int(row["frame"]))
            except (KeyError, ValueError):
                continue
    return frames


def choose_template_candidates(crop_path, anchor_frames, count=TEMPLATE_CANDIDATE_COUNT):
    with tifffile.TiffFile(crop_path) as tif:
        n_pages = len(tif.pages)
    if n_pages <= 0:
        return []
    if anchor_frames:
        candidates = [idx for idx in sorted(anchor_frames) if 0 <= idx < n_pages]
    else:
        candidates = list(range(n_pages))
    if not candidates:
        candidates = list(range(n_pages))
    if len(candidates) <= count:
        return candidates
    positions = np.linspace(0, len(candidates) - 1, count)
    return [candidates[int(round(pos))] for pos in positions]


def make_template_candidate_grid(stack_name, crop_path, candidates, target_shape):
    thumbs = []
    labels = []
    with tifffile.TiffFile(crop_path) as tif:
        for display_idx, frame_idx in enumerate(candidates, 1):
            image = read_ecc_jpg_frame(stack_name, frame_idx, target_shape)
            if image is None:
                image = normalize_uint8(tif.pages[frame_idx].asarray())
            image = ensure_gray_2d(image)
            tile = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            cv2.putText(
                tile,
                f"{display_idx}:{frame_idx}",
                (3, 12),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (0, 255, 255),
                1,
                cv2.LINE_AA,
            )
            thumbs.append(tile)
            labels.append((display_idx, frame_idx))
    if not thumbs:
        return None, labels
    h, w = thumbs[0].shape[:2]
    cols = 5
    rows = int(np.ceil(len(thumbs) / cols))
    canvas = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
    for idx, tile in enumerate(thumbs):
        y = (idx // cols) * h
        x = (idx % cols) * w
        canvas[y:y + h, x:x + w] = tile
    scale = 4 if max(h, w) <= 80 else 2
    canvas = cv2.resize(canvas, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    cv2.putText(
        canvas,
        "Choose template: type 1-30 then Enter. Esc/q = auto.",
        (8, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    return canvas, labels


def interactive_choose_template_frame(stack_name, crop_path, anchor_frames, target_shape):
    if not INTERACTIVE_TEMPLATE_SELECTION:
        return None
    candidates = choose_template_candidates(crop_path, anchor_frames)
    if not candidates:
        return None
    canvas, labels = make_template_candidate_grid(stack_name, crop_path, candidates, target_shape)
    if canvas is None:
        return None
    preview_dir = os.path.join(aligned_dir, "previews")
    os.makedirs(preview_dir, exist_ok=True)
    grid_path = os.path.join(preview_dir, f"{stack_name}_template_candidates.jpg")
    cv2.imwrite(grid_path, canvas)
    window_name = f"Choose template: {stack_name}"
    typed = ""
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1200, 900)
        while True:
            shown = canvas.copy()
            cv2.putText(
                shown,
                f"selected number: {typed}",
                (8, 52),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                1,
                cv2.LINE_AA,
            )
            cv2.imshow(window_name, shown)
            key = cv2.waitKey(50) & 0xFF
            if ord("0") <= key <= ord("9"):
                typed += chr(key)
                typed = typed[-2:]
            elif key in (8, 127):
                typed = typed[:-1]
            elif key in (13, 32):
                if typed:
                    selected_num = int(typed)
                    for display_idx, frame_idx in labels:
                        if display_idx == selected_num:
                            cv2.destroyWindow(window_name)
                            print(f"[template] {stack_name}: user selected candidate {display_idx}, frame {frame_idx}")
                            print(f"[template] {stack_name}: candidate grid saved: {grid_path}")
                            return int(frame_idx)
                typed = ""
            elif key in (27, ord("q"), ord("Q")):
                break
        cv2.destroyWindow(window_name)
    except Exception as exc:
        print(f"[template] Could not open template selector; using automatic template. {exc}")
    print(f"[template] {stack_name}: no user template selected; using automatic template. Candidate grid: {grid_path}")
    return None


def choose_template_frame(crop_path, anchor_frames, stack_name=None, target_shape=None):
    if TEMPLATE_FRAME is not None:
        return int(TEMPLATE_FRAME)
    if stack_name is not None and target_shape is not None:
        selected = interactive_choose_template_frame(stack_name, crop_path, anchor_frames, target_shape)
        if selected is not None:
            return int(selected)

    best_idx = None
    best_score = -1.0
    checked = 0

    with tifffile.TiffFile(crop_path) as tif:
        n_pages = len(tif.pages)
        if anchor_frames:
            candidate_frames = [idx for idx in sorted(anchor_frames) if 0 <= idx < n_pages]
        else:
            candidate_frames = list(range(n_pages))

        for frame_idx in candidate_frames[:TEMPLATE_SEARCH_LIMIT]:
            frame = tif.pages[frame_idx].asarray()
            frame_u8 = normalize_uint8(frame)
            mask = signal_mask(frame_u8)
            area = int(mask.sum())
            if area < 8:
                continue
            blur = blur_score(frame_u8)
            if blur < MIN_TEMPLATE_BLUR_SCORE:
                checked += 1
                continue
            score = 0.65 * blur + 0.25 * float(frame_u8[mask].mean()) + 0.10 * float(frame_u8[mask].max())
            if score > best_score:
                best_score = score
                best_idx = frame_idx
            checked += 1

    if best_idx is None:
        return 0
    return int(best_idx)


def make_preview(frames, out_path, max_tiles=PREVIEW_TILE_COUNT):
    if not frames:
        return
    sample = [normalize_uint8(x) for x in frames[:max_tiles]]
    h, w = sample[0].shape[:2]
    cols = 5
    rows = int(np.ceil(len(sample) / cols))
    canvas = np.zeros((rows * h, cols * w), dtype=np.uint8)
    for idx, frame in enumerate(sample):
        if frame.ndim == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        y = (idx // cols) * h
        x = (idx % cols) * w
        canvas[y:y + h, x:x + w] = frame
    cv2.imwrite(out_path, canvas)


def to_debug_uint8(image):
    if image is None:
        return None
    image = np.asarray(image)
    if image.dtype == np.float32 or image.dtype == np.float64:
        image = np.clip(image * 255.0, 0, 255).astype(np.uint8)
    else:
        image = normalize_uint8(image)
    return ensure_gray_2d(image)


def label_debug_tile(image, label):
    image = to_debug_uint8(image)
    if image is None:
        image = np.zeros((80, 80), dtype=np.uint8)
    tile = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    cv2.putText(tile, label, (4, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1, cv2.LINE_AA)
    return tile


def apply_debug_roi(image, roi_mask, outside_value=0):
    image = to_debug_uint8(image)
    if image is None or roi_mask is None:
        return image
    mask = np.squeeze(roi_mask)
    if mask.shape[:2] != image.shape[:2]:
        mask = cv2.resize(mask.astype(np.uint8), (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    masked = image.copy()
    masked[mask <= 0] = outside_value
    return masked


def save_ecc_debug_panel(
    out_path,
    frame_idx,
    status,
    cc,
    reference_for_debug,
    frame_ecc_image,
    frame_for_ecc,
    warped_ecc,
    corrected,
    warp_matrix,
    rotation_deg,
    translation_x,
    translation_y,
    soma_removed_area,
    frame_mask_area,
    roi_mask_for_debug=None,
    ecc_start_label="",
    ecc_attempts=0,
    ecc_errors=0,
):
    ref_u8 = apply_debug_roi(reference_for_debug, roi_mask_for_debug)
    used_u8 = apply_debug_roi(frame_for_ecc, roi_mask_for_debug)
    warped_u8 = apply_debug_roi(warped_ecc, roi_mask_for_debug)
    if ref_u8 is not None and warped_u8 is not None:
        diff = cv2.absdiff(ref_u8, warped_u8)
    else:
        diff = np.zeros_like(to_debug_uint8(frame_for_ecc))

    tiles = [
        label_debug_tile(frame_ecc_image, "raw ECC jpg"),
        label_debug_tile(used_u8, "ROI used for ECC"),
        label_debug_tile(ref_u8, "ROI reference"),
        label_debug_tile(warped_u8, "ROI warped ECC"),
        label_debug_tile(diff, "ROI abs diff"),
        label_debug_tile(corrected, "saved output"),
    ]
    h = max(tile.shape[0] for tile in tiles)
    w = max(tile.shape[1] for tile in tiles)
    resized = []
    for tile in tiles:
        if tile.shape[:2] != (h, w):
            tile = cv2.resize(tile, (w, h), interpolation=cv2.INTER_NEAREST)
        resized.append(tile)
    top = np.hstack(resized[:3])
    bottom = np.hstack(resized[3:])
    canvas = np.vstack([top, bottom])
    header = np.zeros((42, canvas.shape[1], 3), dtype=np.uint8)
    cc_text = f"{cc:.5f}" if np.isfinite(cc) else "nan"
    rot_text = f"{rotation_deg:.2f}" if np.isfinite(rotation_deg) else "nan"
    tx_text = f"{translation_x:.2f}" if np.isfinite(translation_x) else "nan"
    ty_text = f"{translation_y:.2f}" if np.isfinite(translation_y) else "nan"
    cv2.putText(
        header,
        f"frame={frame_idx} status={status} cc={cc_text} rot={rot_text} tx={tx_text} ty={ty_text} soma_area={soma_removed_area} mask_area={frame_mask_area} roi={int(roi_mask_for_debug is not None)}",
        (4, 16),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.43,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    if warp_matrix is not None:
        flat = " ".join(f"{float(v):.3f}" for v in warp_matrix.reshape(-1))
        cv2.putText(
            header,
            f"start={ecc_start_label} attempts={ecc_attempts} errors={ecc_errors} warp=[{flat}]",
            (4, 34),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (210, 210, 210),
            1,
            cv2.LINE_AA,
        )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cv2.imwrite(out_path, np.vstack([header, canvas]))


def save_ecc_debug_singles(
    debug_dir,
    frame_idx,
    status,
    reason_text,
    reference_for_debug,
    frame_ecc_image,
    frame_for_ecc,
    warped_ecc,
    corrected,
    roi_mask_for_debug=None,
):
    single_dir = os.path.join(debug_dir, "singles")
    os.makedirs(single_dir, exist_ok=True)
    prefix = os.path.join(single_dir, f"{frame_idx:06d}_{status}_{reason_text}")
    images = {
        "raw_ecc_jpg": frame_ecc_image,
        "roi_used_for_ecc": apply_debug_roi(frame_for_ecc, roi_mask_for_debug),
        "roi_reference": apply_debug_roi(reference_for_debug, roi_mask_for_debug),
        "roi_warped_ecc": apply_debug_roi(warped_ecc, roi_mask_for_debug),
        "saved_output": corrected,
    }
    ref_u8 = apply_debug_roi(reference_for_debug, roi_mask_for_debug)
    warped_u8 = apply_debug_roi(warped_ecc, roi_mask_for_debug)
    if ref_u8 is not None and warped_u8 is not None:
        images["roi_abs_diff"] = cv2.absdiff(ref_u8, warped_u8)
    if roi_mask_for_debug is not None:
        images["ecc_roi_mask"] = roi_mask_for_debug
    for label, image in images.items():
        if image is None:
            continue
        cv2.imwrite(f"{prefix}_{label}.jpg", to_debug_uint8(image))


def debug_trigger_reasons(frame_idx, status, cc, raw_rotation_deg, last_debug_rotation_deg, tx, ty):
    reasons = []
    if frame_idx % DEBUG_PANEL_EVERY_N_FRAMES == 0:
        reasons.append("interval")
    if status != "ok":
        reasons.append(status)
    if np.isfinite(cc) and cc < DEBUG_LOW_CC_THRESHOLD:
        reasons.append("low_cc")
    if np.isfinite(raw_rotation_deg) and last_debug_rotation_deg is not None:
        unwrapped = nearest_equivalent_angle(raw_rotation_deg, last_debug_rotation_deg)
        if abs(unwrapped - last_debug_rotation_deg) >= DEBUG_ROTATION_JUMP_DEG:
            reasons.append("rotation_jump")
    if np.isfinite(tx) and np.isfinite(ty) and float(np.hypot(tx, ty)) >= DEBUG_TRANSLATION_MAGNITUDE_PX:
        reasons.append("large_translation")
    return reasons


def status_color(status):
    colors = {
        "ok": (80, 220, 80),
        "classifier_bad": (60, 60, 230),
        "no_ria_mask": (230, 180, 40),
        "ecc_failed": (190, 60, 190),
        "unstable_warp": (60, 140, 230),
    }
    return colors.get(status, (150, 150, 150))


def save_status_timeline(rows, out_path, title=None, width=1400, row_height=24):
    if not rows:
        return
    n = len(rows)
    width = max(200, int(width))
    bar = np.zeros((row_height, width, 3), dtype=np.uint8)
    for x in range(width):
        idx = min(n - 1, int(x * n / width))
        bar[:, x, :] = status_color(rows[idx].get("status", ""))

    legend_items = []
    seen = []
    for row in rows:
        status = row.get("status", "")
        if status and status not in seen:
            seen.append(status)
    for status in seen:
        legend_items.append((status, status_color(status)))

    legend_h = 24 * max(1, int(np.ceil(len(legend_items) / 3)))
    title_h = 30 if title else 0
    canvas = np.zeros((title_h + row_height + legend_h + 8, width, 3), dtype=np.uint8)
    y = 0
    if title:
        cv2.putText(canvas, title, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        y += title_h
    canvas[y:y + row_height, :, :] = bar
    y += row_height + 8
    for i, (status, color) in enumerate(legend_items):
        col = i % 3
        row = i // 3
        x = col * (width // 3) + 8
        yy = y + row * 24
        cv2.rectangle(canvas, (x, yy), (x + 16, yy + 16), color, -1)
        cv2.putText(canvas, status, (x + 22, yy + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (230, 230, 230), 1, cv2.LINE_AA)
    cv2.imwrite(out_path, canvas)


def save_all_status_timeline(alignment_csv_paths, out_path, width=1400, row_height=14):
    timelines = []
    for csv_path in alignment_csv_paths:
        stack_name = os.path.basename(csv_path)[:-len("_alignment.csv")]
        rows = []
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows.append(row)
        if rows:
            timelines.append((stack_name, rows))
    if not timelines:
        return

    left = 330
    header = 30
    legend_h = 80
    height = header + len(timelines) * row_height + legend_h
    canvas = np.zeros((height, left + width, 3), dtype=np.uint8)
    cv2.putText(canvas, "Alignment frame status by stack", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    y = header
    for stack_name, rows in timelines:
        cv2.putText(canvas, stack_name[:42], (8, y + row_height - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (230, 230, 230), 1, cv2.LINE_AA)
        n = len(rows)
        for x in range(width):
            idx = min(n - 1, int(x * n / width))
            canvas[y:y + row_height, left + x, :] = status_color(rows[idx].get("status", ""))
        y += row_height

    legend_statuses = ["ok", "classifier_bad", "no_ria_mask", "ecc_failed", "unstable_warp"]
    y += 12
    for i, status in enumerate(legend_statuses):
        x = 8 + (i % 3) * 210
        yy = y + (i // 3) * 24
        cv2.rectangle(canvas, (x, yy), (x + 16, yy + 16), status_color(status), -1)
        cv2.putText(canvas, status, (x + 22, yy + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (230, 230, 230), 1, cv2.LINE_AA)
    cv2.imwrite(out_path, canvas)


def warp_values_for_csv(warp_matrix, warp_mode):
    if warp_matrix is None:
        if warp_mode == cv2.MOTION_HOMOGRAPHY:
            return {f"M{i}{j}": "" for i in range(3) for j in range(3)}
        return {"M00": "", "M01": "", "M02": "", "M10": "", "M11": "", "M12": ""}

    if warp_mode == cv2.MOTION_HOMOGRAPHY:
        return {f"M{i}{j}": f"{float(warp_matrix[i, j]):.8f}" for i in range(3) for j in range(3)}
    return {
        "M00": f"{float(warp_matrix[0, 0]):.8f}",
        "M01": f"{float(warp_matrix[0, 1]):.8f}",
        "M02": f"{float(warp_matrix[0, 2]):.8f}",
        "M10": f"{float(warp_matrix[1, 0]):.8f}",
        "M11": f"{float(warp_matrix[1, 1]):.8f}",
        "M12": f"{float(warp_matrix[1, 2]):.8f}",
    }


def warp_rotation_deg(warp_matrix):
    if warp_matrix is None or warp_matrix.shape[0] < 2 or warp_matrix.shape[1] < 2:
        return np.nan
    return float(np.degrees(np.arctan2(float(warp_matrix[1, 0]), float(warp_matrix[0, 0]))))


def nearest_equivalent_angle(angle_deg, reference_deg):
    candidates = [angle_deg - 360.0, angle_deg, angle_deg + 360.0]
    return min(candidates, key=lambda value: abs(value - reference_deg))


def limit_warp_rotation(warp_matrix, previous_rotation_deg):
    if (
        not LIMIT_ROTATION_BY_PREVIOUS_FRAME
        or previous_rotation_deg is None
        or warp_matrix is None
        or WARP_MODE not in (cv2.MOTION_EUCLIDEAN, cv2.MOTION_AFFINE)
    ):
        return warp_matrix, warp_rotation_deg(warp_matrix), warp_rotation_deg(warp_matrix), 0

    raw_angle = warp_rotation_deg(warp_matrix)
    if not np.isfinite(raw_angle):
        return warp_matrix, raw_angle, raw_angle, 0
    unwrapped = nearest_equivalent_angle(raw_angle, previous_rotation_deg)
    delta = unwrapped - previous_rotation_deg
    limited_delta = float(np.clip(delta, -MAX_ROTATION_DELTA_DEG, MAX_ROTATION_DELTA_DEG))
    if abs(limited_delta - delta) < 1e-6:
        return warp_matrix, raw_angle, unwrapped, 0

    limited_angle = previous_rotation_deg + limited_delta
    limited = warp_matrix.copy()
    scale = float(np.hypot(float(warp_matrix[0, 0]), float(warp_matrix[1, 0])))
    if scale <= 0:
        scale = 1.0
    theta = np.deg2rad(limited_angle)
    limited[0, 0] = scale * np.cos(theta)
    limited[0, 1] = -scale * np.sin(theta)
    limited[1, 0] = scale * np.sin(theta)
    limited[1, 1] = scale * np.cos(theta)
    return limited, raw_angle, limited_angle, 1


def warp_translation_xy(warp_matrix):
    if warp_matrix is None or warp_matrix.shape[0] < 2 or warp_matrix.shape[1] < 3:
        return np.nan, np.nan
    return float(warp_matrix[0, 2]), float(warp_matrix[1, 2])


def limit_warp_translation(warp_matrix, previous_translation_xy):
    raw_tx, raw_ty = warp_translation_xy(warp_matrix)
    if (
        not LIMIT_TRANSLATION_BY_PREVIOUS_FRAME
        or previous_translation_xy is None
        or warp_matrix is None
        or not np.isfinite(raw_tx)
        or not np.isfinite(raw_ty)
        or WARP_MODE == cv2.MOTION_HOMOGRAPHY
    ):
        return warp_matrix, raw_tx, raw_ty, raw_tx, raw_ty, 0

    prev_tx, prev_ty = previous_translation_xy
    limited_tx = float(prev_tx + np.clip(raw_tx - prev_tx, -MAX_TRANSLATION_DELTA_PX, MAX_TRANSLATION_DELTA_PX))
    limited_ty = float(prev_ty + np.clip(raw_ty - prev_ty, -MAX_TRANSLATION_DELTA_PX, MAX_TRANSLATION_DELTA_PX))
    limited = int(abs(limited_tx - raw_tx) > 1e-6 or abs(limited_ty - raw_ty) > 1e-6)
    if limited:
        warp_matrix = warp_matrix.copy()
        warp_matrix[0, 2] = limited_tx
        warp_matrix[1, 2] = limited_ty
    return warp_matrix, raw_tx, raw_ty, limited_tx, limited_ty, limited


def align_stack_with_ecc(crop_path):
    stack_name = stack_name_from_crop(os.path.basename(crop_path))
    anchor_frames = load_anchor_frames(stack_name)

    os.makedirs(aligned_dir, exist_ok=True)
    preview_dir = os.path.join(aligned_dir, "previews")
    debug_dir = os.path.join(aligned_dir, "debug", stack_name)
    status_dir = os.path.join(aligned_dir, "status_timelines")
    os.makedirs(preview_dir, exist_ok=True)
    os.makedirs(status_dir, exist_ok=True)
    if SAVE_DEBUG:
        if DEBUG_CLEAR_ON_START and os.path.isdir(debug_dir):
            shutil.rmtree(debug_dir)
        os.makedirs(debug_dir, exist_ok=True)

    aligned_path = os.path.join(aligned_dir, f"{stack_name}_aligned.tif")
    csv_path = os.path.join(aligned_dir, f"{stack_name}_alignment.csv")
    preview_path = os.path.join(preview_dir, f"{stack_name}_preview.jpg")
    status_timeline_path = os.path.join(status_dir, f"{stack_name}_status_timeline.png")
    stale_dynamic_reference_path = os.path.join(preview_dir, f"{stack_name}_dynamic_max_reference.jpg")
    if not USE_DYNAMIC_MAX_REFERENCE and os.path.exists(stale_dynamic_reference_path):
        os.remove(stale_dynamic_reference_path)

    local_output_dir = os.path.join(LOCAL_TEMP_ROOT, ".ria_aligned_ecc")
    os.makedirs(local_output_dir, exist_ok=True)
    local_aligned_path = os.path.join(local_output_dir, f"{stack_name}_aligned.tif")

    with tifffile.TiffFile(crop_path) as tif:
        series_shape = tif.series[0].shape
        if len(series_shape) == 2:
            n_frames = 1
            height, width = series_shape
        else:
            n_frames = series_shape[0]
            height, width = series_shape[1:3]

    template_frame_idx = choose_template_frame(crop_path, anchor_frames, stack_name=stack_name, target_shape=(height, width))
    template_ecc_image = read_ecc_jpg_frame(stack_name, template_frame_idx, (height, width))
    if template_ecc_image is None:
        jpg_folder = ecc_jpg_dir_for_stack(stack_name)
        if REQUIRE_CROP_JPG_FOR_ECC:
            raise FileNotFoundError(
                f"Missing crop JPG for ECC template frame {template_frame_idx}: {jpg_folder}. "
                "Run 6CropTIFF2JPG.py first."
            )
        with tifffile.TiffFile(crop_path) as tif:
            template_ecc_image = normalize_uint8(tif.pages[template_frame_idx].asarray())
        ecc_source = "normalized_crop_tiff_fallback"
    else:
        ecc_source = "crop_jpg"

    mask_path = ria_mask_path_for_stack(stack_name)
    mask_tif = tifffile.TiffFile(mask_path) if USE_RIA_MASK_FOR_ECC and os.path.exists(mask_path) else None
    if REQUIRE_RIA_MASK_FOR_ECC and mask_tif is None:
        raise FileNotFoundError(f"Missing RIA mask TIFF for ECC: {mask_path}. Run 4AutoCrop.py first.")
    template_mask = None
    if mask_tif is not None and template_frame_idx < len(mask_tif.pages):
        template_mask = prepare_ecc_mask(mask_tif.pages[template_frame_idx].asarray(), (height, width))
    if REQUIRE_RIA_MASK_FOR_ECC and template_mask is None:
        raise RuntimeError(f"Template frame {template_frame_idx} has no detected RIA mask in {mask_path}.")
    template = template_ecc_image if USE_FULL_CROP_FOR_ECC else apply_mask_for_ecc(template_ecc_image, template_mask)
    template_for_ecc, template_soma_removed_area = remove_soma_for_ecc(template, template_mask)
    template_blur_score = masked_jpg_blur_score(template_ecc_image, template_mask)
    if ENABLE_MASKED_JPG_BLUR_DETECTION and template_blur_score < MIN_TEMPLATE_MASKED_JPG_BLUR_SCORE:
        raise RuntimeError(
            f"Template frame {template_frame_idx} is blurry after JPG+mask: "
            f"blur={template_blur_score:.3f}, min={MIN_TEMPLATE_MASKED_JPG_BLUR_SCORE:.3f}. "
            "Choose another template frame or inspect 06_crop_jpg/04_ria_mask."
        )
    def load_tuning_frame(frame_idx):
        frame = read_ecc_jpg_frame(stack_name, int(frame_idx), (height, width))
        if frame is not None:
            return frame
        return template

    tune_ecc_contrast_if_needed(
        stack_name,
        template,
        frame_count=n_frames,
        initial_frame_idx=template_frame_idx,
        frame_loader=load_tuning_frame,
    )
    selected_roi, max_projection_path, roi_preview_path = select_ecc_roi_from_max_projection(
        stack_name,
        crop_path,
        height,
        width,
        preview_dir,
    )
    roi_mask = roi_to_mask(selected_roi, height, width)
    reference_image = template_for_ecc.copy()
    manual_template_frames = load_manual_template_frames(stack_name, (height, width))
    manual_template_loaded = len(manual_template_frames)
    reference_entries = [("base", reference_image, preprocess_for_ecc(reference_image))]
    for label, image, _path in manual_template_frames:
        reference_entries.append((label, image, preprocess_for_ecc(image)))
    reference_preview = reference_image.copy()
    for _label, image, _path in manual_template_frames:
        reference_preview = np.maximum(reference_preview, image)
    reference_update_count = 0
    if USE_SELECTED_ROI_FOR_ECC and roi_mask is not None:
        ecc_input_mask = roi_mask
    else:
        ecc_input_mask = None if USE_FULL_CROP_FOR_ECC else template_mask

    template_out_path = os.path.join(preview_dir, f"{stack_name}_template_frame_{template_frame_idx}.jpg")
    template_no_soma_path = os.path.join(preview_dir, f"{stack_name}_template_frame_{template_frame_idx}_no_soma_for_ecc.jpg")
    template_reference_path = os.path.join(preview_dir, f"{stack_name}_reference_templates_preview.jpg")
    cv2.imwrite(template_out_path, template)
    cv2.imwrite(template_no_soma_path, template_for_ecc)
    cv2.imwrite(template_reference_path, reference_preview)
    print(f"[template] {stack_name}: using frame {template_frame_idx}")
    print(f"[template] {stack_name}: masked JPG blur score = {template_blur_score:.3f}")
    print(f"[ecc] {stack_name}: ECC image source = {ecc_source}")
    print(f"[ecc] {stack_name}: ECC region = {'full_crop' if USE_FULL_CROP_FOR_ECC else 'ria_mask'}")
    print(
        f"[ecc] {stack_name}: CLAHE={int(USE_CLAHE_FOR_ECC)}, "
        f"clip={CLAHE_CLIP_LIMIT:.2f}, tile={CLAHE_TILE_GRID_SIZE}, "
        f"display_min={ECC_DISPLAY_MIN}, display_max={ECC_DISPLAY_MAX}, gamma={ECC_GAMMA:.2f}"
    )
    print(
        f"[ecc] {stack_name}: reference={'dynamic_max_previous_ok' if USE_DYNAMIC_MAX_REFERENCE else 'template'}, "
        f"previous_warp_init={int(USE_PREVIOUS_WARP)}"
    )
    if manual_template_loaded:
        print(f"[ecc] {stack_name}: loaded {manual_template_loaded} manual template frame(s) for per-frame best-template matching.")
    print(
        f"[ecc] {stack_name}: min_cc={MIN_ECC_CC:.2f}, "
        f"multi_start={int(ECC_MULTI_START)}, retry_below_cc={ECC_MULTI_START_RETRY_BELOW_CC:.2f}, "
        f"max_abs_rotation={'off' if MAX_ECC_ROTATION_ABS_DEG is None else f'{MAX_ECC_ROTATION_ABS_DEG:.1f}'}"
    )
    if not USE_DYNAMIC_MAX_REFERENCE:
        print(f"[ecc] {stack_name}: dynamic reference accumulation is OFF; debug reference should remain the fixed no-soma template.")
    print(f"[ecc] {stack_name}: selected_roi_for_ecc={int(roi_mask is not None and USE_SELECTED_ROI_FOR_ECC)}")
    print(
        f"[ecc] {stack_name}: remove_soma={int(REMOVE_SOMA_FOR_ECC)}, "
        f"radius={SOMA_REMOVE_RADIUS_PX}px, fill={SOMA_FILL_MODE}, template_removed_area={template_soma_removed_area}"
    )
    print(
        f"[ecc] {stack_name}: rotation_limit={int(LIMIT_ROTATION_BY_PREVIOUS_FRAME)}, "
        f"max_delta={MAX_ROTATION_DELTA_DEG:.2f} deg/frame"
    )
    print(
        f"[ecc] {stack_name}: translation_limit={int(LIMIT_TRANSLATION_BY_PREVIOUS_FRAME)}, "
        f"max_delta={MAX_TRANSLATION_DELTA_PX:.2f} px/frame"
    )
    if mask_tif is not None:
        print(f"[mask] {stack_name}: using RIA crop mask {mask_path}")
        if USE_RIA_MASK_BBOX_FOR_ECC:
            print(
                f"[mask] {stack_name}: ECC mask mode=bbox, "
                f"padding={MASK_BBOX_PADDING}px + {MASK_BBOX_PADDING_FRACTION:.2f}*box"
            )
        else:
            print(f"[mask] {stack_name}: ECC mask mode=ria_mask, dilation_iterations={MASK_DILATE_ITERATIONS}")
    else:
        print(f"[mask] {stack_name}: no RIA crop mask found; ECC uses full crop")

    criteria = (
        cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
        MAX_ITERATIONS,
        TERMINATION_EPS,
    )

    rows = []
    preview_frames = []
    frame_blur_scores = []
    last_warp = get_identity_warp(WARP_MODE)
    last_rotation_deg = None
    last_translation_xy = None
    last_debug_rotation_deg = None

    try:
        with tifffile.TiffFile(crop_path) as tif, tifffile.TiffWriter(local_aligned_path, bigtiff=False) as out_tif:
            if len(tif.pages) == n_frames and n_frames > 1:
                frame_iter = (page.asarray() for page in tif.pages)
            else:
                stack = tif.asarray()
                frame_iter = iter([stack]) if stack.ndim == 2 else iter(stack)

            for frame_idx, frame in enumerate(tqdm(frame_iter, total=n_frames, desc=f"ECC align {stack_name}")):
                frame_u8 = ensure_gray_2d(frame)
                frame_mask = None
                if mask_tif is not None and frame_idx < len(mask_tif.pages):
                    frame_mask = prepare_ecc_mask(mask_tif.pages[frame_idx].asarray(), (height, width))
                frame_ecc_image = read_ecc_jpg_frame(stack_name, frame_idx, (height, width))
                if frame_ecc_image is None:
                    if REQUIRE_CROP_JPG_FOR_ECC:
                        raise FileNotFoundError(
                            f"Missing crop JPG for ECC frame {frame_idx}: {ecc_jpg_dir_for_stack(stack_name)}. "
                            "Run 6CropTIFF2JPG.py first."
                        )
                    frame_ecc_image = frame_u8
                frame_for_ecc = frame_ecc_image if USE_FULL_CROP_FOR_ECC else apply_mask_for_ecc(frame_ecc_image, frame_mask)
                frame_for_ecc, soma_removed_area = remove_soma_for_ecc(frame_for_ecc, frame_mask)
                init_warp = last_warp.copy() if USE_PREVIOUS_WARP else get_identity_warp(WARP_MODE)

                status = "ok"
                cc = np.nan
                warp_matrix = None
                raw_rotation_deg = np.nan
                limited_rotation_deg = np.nan
                rotation_limited = 0
                translation_raw_x = np.nan
                translation_raw_y = np.nan
                translation_limited_x = np.nan
                translation_limited_y = np.nan
                translation_limited = 0
                ecc_start_label = ""
                ecc_attempts = 0
                ecc_errors = 0
                ecc_rejected_rotation = 0
                ecc_attempt_summary = ""
                ecc_template_label = ""
                corrected = frame_u8
                reference_before_ecc = reference_image.copy()
                warped_ecc_for_debug = None
                mask_used = (not USE_FULL_CROP_FOR_ECC) and template_mask is not None and frame_mask is not None
                frame_mask_area = int((frame_mask > 0).sum()) if frame_mask is not None else 0
                frame_blur_score = masked_jpg_blur_score(frame_ecc_image, frame_mask)
                frame_blur_scores.append(frame_blur_score)
                blur_cls_label, blur_cls_prob_bad, blur_cls_prob_good = classify_ria_frame_quality(frame_ecc_image)

                if frame_mask is None:
                    status = "no_ria_mask"
                    corrected = np.zeros((height, width), dtype=np.uint8)
                elif USE_RIA_BLUR_CLASSIFIER and np.isfinite(blur_cls_prob_bad) and blur_cls_prob_bad >= RIA_BLUR_BAD_THRESHOLD:
                    status = "classifier_bad"
                    corrected = np.zeros((height, width), dtype=np.uint8)
                else:
                    current_proc = preprocess_for_ecc(frame_for_ecc)
                    try:
                        (
                            cc,
                            warp_matrix,
                            ecc_start_label,
                            ecc_template_label,
                            ecc_attempts,
                            ecc_errors,
                            ecc_rejected_rotation,
                            ecc_attempt_summary,
                            selected_reference_image,
                        ) = run_ecc_multitemplate(
                            reference_entries,
                            current_proc,
                            init_warp,
                            WARP_MODE,
                            criteria,
                            ecc_input_mask,
                            ECC_GAUSS_FILT_SIZE,
                        )
                        if selected_reference_image is not None:
                            reference_before_ecc = selected_reference_image.copy()
                        if warp_matrix is None and ecc_start_label == "rotation_over_90":
                            status = "rotation_over_90"
                            if FAILED_FRAME_MODE == "black":
                                corrected = np.zeros((height, width), dtype=np.uint8)
                            else:
                                corrected = frame_u8
                        elif np.isfinite(cc) and float(cc) < MIN_ECC_CC:
                            status = "low_cc"
                            if FAILED_FRAME_MODE == "black":
                                corrected = np.zeros((height, width), dtype=np.uint8)
                            else:
                                corrected = frame_u8
                        else:
                            warp_matrix, raw_rotation_deg, limited_rotation_deg, rotation_limited = limit_warp_rotation(
                                warp_matrix,
                                last_rotation_deg,
                            )
                            (
                                warp_matrix,
                                translation_raw_x,
                                translation_raw_y,
                                translation_limited_x,
                                translation_limited_y,
                                translation_limited,
                            ) = limit_warp_translation(warp_matrix, last_translation_xy)
                            corrected = warp_frame(frame_u8, warp_matrix, WARP_MODE, width, height)
                            warped_ecc_for_debug = warp_frame(frame_for_ecc, warp_matrix, WARP_MODE, width, height)
                            last_warp = warp_matrix.copy()
                            if np.isfinite(limited_rotation_deg):
                                last_rotation_deg = float(limited_rotation_deg)
                            if np.isfinite(translation_limited_x) and np.isfinite(translation_limited_y):
                                last_translation_xy = (float(translation_limited_x), float(translation_limited_y))
                            if USE_DYNAMIC_MAX_REFERENCE:
                                corrected_for_reference = warp_frame(
                                    frame_for_ecc,
                                    warp_matrix,
                                    WARP_MODE,
                                    width,
                                    height,
                                )
                                reference_image = np.maximum(reference_image, corrected_for_reference)
                                reference_entries[0] = ("base", reference_image, preprocess_for_ecc(reference_image))
                                reference_update_count += 1
                    except cv2.error:
                        status = "ecc_failed"
                        if FAILED_FRAME_MODE == "black":
                            corrected = np.zeros((height, width), dtype=np.uint8)
                        else:
                            corrected = frame_u8

                out_tif.write(corrected, contiguous=True)
                if len(preview_frames) < PREVIEW_TILE_COUNT:
                    preview_frames.append(corrected)

                row = {
                    "frame": frame_idx,
                    "status": status,
                    "cc": f"{float(cc):.8f}" if np.isfinite(cc) else "",
                    "min_ecc_cc": f"{MIN_ECC_CC:.6f}",
                    "ecc_multistart": "1" if ECC_MULTI_START else "0",
                    "ecc_template_label": ecc_template_label,
                    "ecc_template_count": len(reference_entries),
                    "ecc_start_label": ecc_start_label,
                    "ecc_attempts": ecc_attempts,
                    "ecc_errors": ecc_errors,
                    "ecc_rejected_rotation": ecc_rejected_rotation,
                    "ecc_attempt_summary": ecc_attempt_summary,
                    "template_frame": template_frame_idx,
                    "warp_mode": WARP_MODE,
                    "mask_used": "1" if mask_used else "0",
                    "ecc_source": ecc_source,
                    "ecc_region": "full_crop" if USE_FULL_CROP_FOR_ECC else "ria_mask",
                    "ecc_roi_used": "1" if (roi_mask is not None and USE_SELECTED_ROI_FOR_ECC) else "0",
                    "ecc_roi_shape": "ellipse" if selected_roi is not None else "",
                    "ecc_roi_x": "" if selected_roi is None else selected_roi[0],
                    "ecc_roi_y": "" if selected_roi is None else selected_roi[1],
                    "ecc_roi_width": "" if selected_roi is None else selected_roi[2],
                    "ecc_roi_height": "" if selected_roi is None else selected_roi[3],
                    "ecc_reference_mode": "dynamic_max_previous_ok" if USE_DYNAMIC_MAX_REFERENCE else "template",
                    "ecc_reference_updates": reference_update_count,
                    "manual_template_loaded": "1" if manual_template_loaded else "0",
                    "manual_template_count": manual_template_loaded,
                    "ecc_remove_soma": "1" if REMOVE_SOMA_FOR_ECC else "0",
                    "ecc_soma_fill_mode": SOMA_FILL_MODE if REMOVE_SOMA_FOR_ECC else "",
                    "template_soma_removed_area": template_soma_removed_area,
                    "frame_soma_removed_area": soma_removed_area,
                    "ecc_clahe": "1" if USE_CLAHE_FOR_ECC else "0",
                    "ecc_clahe_clip_limit": f"{CLAHE_CLIP_LIMIT:.6f}",
                    "ecc_clahe_tile_size": CLAHE_TILE_GRID_SIZE[0],
                    "ecc_contrast_alpha": f"{ECC_CONTRAST_ALPHA:.6f}",
                    "ecc_brightness_beta": int(ECC_BRIGHTNESS_BETA),
                    "ecc_display_min": int(ECC_DISPLAY_MIN),
                    "ecc_display_max": int(ECC_DISPLAY_MAX),
                    "ecc_gamma": f"{ECC_GAMMA:.6f}",
                    "template_masked_jpg_blur_score": f"{template_blur_score:.6f}",
                    "frame_masked_jpg_blur_score": f"{frame_blur_score:.6f}",
                    "blur_classifier_label": blur_cls_label,
                    "blur_classifier_prob_bad": f"{blur_cls_prob_bad:.6f}" if np.isfinite(blur_cls_prob_bad) else "",
                    "blur_classifier_prob_good": f"{blur_cls_prob_good:.6f}" if np.isfinite(blur_cls_prob_good) else "",
                    "blur_classifier_bad_threshold": f"{RIA_BLUR_BAD_THRESHOLD:.6f}" if USE_RIA_BLUR_CLASSIFIER else "",
                    "frame_mask_area": frame_mask_area,
                    "rotation_raw_deg": f"{raw_rotation_deg:.6f}" if np.isfinite(raw_rotation_deg) else "",
                    "rotation_limited_deg": f"{limited_rotation_deg:.6f}" if np.isfinite(limited_rotation_deg) else "",
                    "rotation_limited": rotation_limited,
                    "max_rotation_delta_deg": f"{MAX_ROTATION_DELTA_DEG:.6f}" if LIMIT_ROTATION_BY_PREVIOUS_FRAME else "",
                    "translation_raw_x": f"{translation_raw_x:.6f}" if np.isfinite(translation_raw_x) else "",
                    "translation_raw_y": f"{translation_raw_y:.6f}" if np.isfinite(translation_raw_y) else "",
                    "translation_limited_x": f"{translation_limited_x:.6f}" if np.isfinite(translation_limited_x) else "",
                    "translation_limited_y": f"{translation_limited_y:.6f}" if np.isfinite(translation_limited_y) else "",
                    "translation_limited": translation_limited,
                    "max_translation_delta_px": f"{MAX_TRANSLATION_DELTA_PX:.6f}" if LIMIT_TRANSLATION_BY_PREVIOUS_FRAME else "",
                }
                row.update(warp_values_for_csv(warp_matrix, WARP_MODE))
                rows.append(row)

                if SAVE_DEBUG and (
                    frame_idx % DEBUG_PRINT_EVERY_N_FRAMES == 0
                    or status != "ok"
                    or not np.isfinite(cc)
                ):
                    cc_text = f"{float(cc):.5f}" if np.isfinite(cc) else "nan"
                    rot_text = f"{raw_rotation_deg:.2f}" if np.isfinite(raw_rotation_deg) else "nan"
                    tx_text = f"{translation_raw_x:.2f}" if np.isfinite(translation_raw_x) else "nan"
                    ty_text = f"{translation_raw_y:.2f}" if np.isfinite(translation_raw_y) else "nan"
                    print(
                        f"\r[ecc debug] {stack_name} frame={frame_idx}/{n_frames - 1} "
                        f"status={status} cc={cc_text} rot={rot_text} tx={tx_text} ty={ty_text} "
                        f"template={ecc_template_label} start={ecc_start_label} attempts={ecc_attempts} errors={ecc_errors} reject_rot={ecc_rejected_rotation} "
                        f"soma_area={soma_removed_area} mask_area={frame_mask_area} ref_updates={reference_update_count}"
                    )

                debug_reasons = []
                if SAVE_DEBUG:
                    debug_reasons = debug_trigger_reasons(
                        frame_idx,
                        status,
                        cc,
                        raw_rotation_deg,
                        last_debug_rotation_deg,
                        translation_raw_x,
                        translation_raw_y,
                    )
                    if np.isfinite(raw_rotation_deg):
                        last_debug_rotation_deg = nearest_equivalent_angle(
                            raw_rotation_deg,
                            last_debug_rotation_deg if last_debug_rotation_deg is not None else raw_rotation_deg,
                        )

                if SAVE_DEBUG and debug_reasons:
                    reason_text = "-".join(debug_reasons[:3])
                    panel_path = os.path.join(debug_dir, f"ecc_panel_{frame_idx:06d}_{status}_{reason_text}.jpg")
                    save_ecc_debug_panel(
                        panel_path,
                        frame_idx,
                        status,
                        cc,
                        reference_before_ecc,
                        frame_ecc_image,
                        frame_for_ecc,
                        warped_ecc_for_debug,
                        corrected,
                        warp_matrix,
                        raw_rotation_deg,
                        translation_raw_x,
                        translation_raw_y,
                        soma_removed_area,
                        frame_mask_area,
                        ecc_input_mask,
                        ecc_start_label,
                        ecc_attempts,
                        ecc_errors,
                    )
                    save_ecc_debug_singles(
                        debug_dir,
                        frame_idx,
                        status,
                        reason_text,
                        reference_before_ecc,
                        frame_ecc_image,
                        frame_for_ecc,
                        warped_ecc_for_debug,
                        corrected,
                        ecc_input_mask,
                    )

                if SAVE_DEBUG and frame_idx % DEBUG_EVERY_N_FRAMES == 0:
                    debug_before = cv2.cvtColor(frame_u8, cv2.COLOR_GRAY2BGR) if frame_u8.ndim == 2 else frame_u8.copy()
                    debug_after = cv2.cvtColor(corrected, cv2.COLOR_GRAY2BGR) if corrected.ndim == 2 else corrected.copy()
                    cv2.putText(
                        debug_before,
                        f"frame={frame_idx}, status={status}, mask={int(mask_used)}",
                        (5, 18),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.45,
                        (255, 255, 255),
                        1,
                    )
                    cv2.imwrite(os.path.join(debug_dir, f"debug_before_{frame_idx:06d}.png"), debug_before)
                    cv2.imwrite(os.path.join(debug_dir, f"debug_after_{frame_idx:06d}.png"), debug_after)
    finally:
        if mask_tif is not None:
            mask_tif.close()

    fieldnames = [
        "frame",
        "status",
        "cc",
        "min_ecc_cc",
        "ecc_multistart",
        "ecc_template_label",
        "ecc_template_count",
        "ecc_start_label",
        "ecc_attempts",
        "ecc_errors",
        "ecc_rejected_rotation",
        "ecc_attempt_summary",
        "template_frame",
        "warp_mode",
        "mask_used",
        "ecc_source",
        "ecc_region",
        "ecc_roi_used",
        "ecc_roi_shape",
        "ecc_roi_x",
        "ecc_roi_y",
        "ecc_roi_width",
        "ecc_roi_height",
        "ecc_reference_mode",
        "ecc_reference_updates",
        "manual_template_loaded",
        "manual_template_count",
        "ecc_remove_soma",
        "ecc_soma_fill_mode",
        "template_soma_removed_area",
        "frame_soma_removed_area",
        "ecc_clahe",
        "ecc_clahe_clip_limit",
        "ecc_clahe_tile_size",
        "ecc_contrast_alpha",
        "ecc_brightness_beta",
        "ecc_display_min",
        "ecc_display_max",
        "ecc_gamma",
        "template_masked_jpg_blur_score",
        "frame_masked_jpg_blur_score",
        "blur_classifier_label",
        "blur_classifier_prob_bad",
        "blur_classifier_prob_good",
        "blur_classifier_bad_threshold",
        "frame_mask_area",
        "rotation_raw_deg",
        "rotation_limited_deg",
        "rotation_limited",
        "max_rotation_delta_deg",
        "translation_raw_x",
        "translation_raw_y",
        "translation_limited_x",
        "translation_limited_y",
        "translation_limited",
        "max_translation_delta_px",
    ]
    if WARP_MODE == cv2.MOTION_HOMOGRAPHY:
        fieldnames += [f"M{i}{j}" for i in range(3) for j in range(3)]
    else:
        fieldnames += ["M00", "M01", "M02", "M10", "M11", "M12"]
    extra_fields = sorted({key for row in rows for key in row.keys()} - set(fieldnames))
    if extra_fields:
        print(f"[csv] Adding extra row fields to header: {extra_fields}")
        fieldnames += extra_fields

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    status_counts = Counter(row.get("status", "") for row in rows)
    total_frames = len(rows)
    ok_frames = status_counts.get("ok", 0)
    dropped_frames = total_frames - ok_frames
    if total_frames:
        print(
            f"[status] {stack_name}: ok={ok_frames}/{total_frames}, "
            f"dropped={dropped_frames}/{total_frames} ({dropped_frames / total_frames:.1%})"
        )
        for status, count in sorted(status_counts.items()):
            if status == "ok":
                continue
            print(f"[status] {stack_name}: {status}={count}")
    save_status_timeline(
        rows,
        status_timeline_path,
        title=f"{stack_name}: ok={ok_frames}/{total_frames}, dropped={dropped_frames}/{total_frames}",
    )

    dynamic_reference_path = ""
    if USE_DYNAMIC_MAX_REFERENCE:
        dynamic_reference_path = os.path.join(preview_dir, f"{stack_name}_dynamic_max_reference.jpg")
        cv2.imwrite(dynamic_reference_path, normalize_uint8(reference_image))

    make_preview(preview_frames, preview_path)
    if frame_blur_scores:
        blur_values = np.array(frame_blur_scores, dtype=np.float64)
        print(
            f"[blur diagnostic] {stack_name}: template={template_blur_score:.3f}, "
            f"frame min={blur_values.min():.3f}, median={np.median(blur_values):.3f}, "
            f"max={blur_values.max():.3f}; classifier controls bad-frame rejection"
        )
    if os.path.exists(aligned_path):
        os.remove(aligned_path)
    shutil.move(local_aligned_path, aligned_path)

    print(f"Saved aligned stack: {aligned_path}")
    print(f"Saved alignment CSV: {csv_path}")
    print(f"Saved preview: {preview_path}")
    print(f"Saved status timeline: {status_timeline_path}")
    print(f"Saved template preview: {template_out_path}")
    print(f"Saved no-soma ECC template preview: {template_no_soma_path}")
    print(f"Saved ECC reference preview: {template_reference_path}")
    if dynamic_reference_path:
        print(f"Saved dynamic max reference: {dynamic_reference_path}")


def main():
    files = crop_stack_files()
    if not files:
        print(f"No crop TIFF files found in {crop_dir}")
        return
    print(f"Found {len(files)} crop TIFF file(s).")
    for idx, name in enumerate(files, 1):
        print(f"\n[{idx}/{len(files)}] Processing {name}")
        align_stack_with_ecc(os.path.join(crop_dir, name))
    alignment_csv_paths = [
        os.path.join(aligned_dir, f"{stack_name_from_crop(name)}_alignment.csv")
        for name in files
        if os.path.exists(os.path.join(aligned_dir, f"{stack_name_from_crop(name)}_alignment.csv"))
    ]
    if alignment_csv_paths:
        status_dir = os.path.join(aligned_dir, "status_timelines")
        os.makedirs(status_dir, exist_ok=True)
        overview_path = os.path.join(status_dir, "all_stacks_status_timeline.png")
        save_all_status_timeline(alignment_csv_paths, overview_path)
        print(f"Saved all-stack status timeline: {overview_path}")


if __name__ == "__main__":
    main()
