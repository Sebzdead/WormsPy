"""
Step 3: segment the whole worm in full-frame videos with SAM2.

Outputs per stack/video:
- 03_worm_segmentation/<stack_name>/frame_validity.csv
- 03_worm_segmentation/<stack_name>/masks/*.png
- 03_worm_segmentation/<stack_name>/overlays/*.jpg

The CSV is consumed by 4AutoCrop.py to skip frames where the worm mask is too
small or touches the image border.
"""
import csv
import contextlib
import os
import shutil
import sys
import time

import cv2
import matplotlib.pyplot as plt
import numpy as np
import tifffile
import torch
from matplotlib.backend_bases import MouseButton
from PIL import Image
from tqdm import tqdm

from sam2.build_sam import build_sam2_video_predictor  # type: ignore


def quiet_tqdm(iterable=None, *args, **kwargs):
    return iterable if iterable is not None else []


def disable_sam2_progress_bars():
    module_names = (
        "sam2.sam2_video_predictor",
        "sam2.sam2_video_predictor_legacy",
        "sam2.utils.misc",
    )
    for module_name in module_names:
        try:
            module = __import__(module_name, fromlist=["tqdm"])
            module.tqdm = quiet_tqdm
        except Exception:
            pass


disable_sam2_progress_bars()


if torch.cuda.is_available():
    device = torch.device("cuda")
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")
print(f"using device: {device}")

sam2_checkpoint = r"C:\Users\34358\Desktop\Yue_analysis_WormSpy\sam2\checkpoints\sam2.1_hiera_tiny.pt"
model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml"

# Directory configuration. Usually you only need to edit RESULTS_ROOT and RUN_ID.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "old"

STACK_SUBDIR = "01_tiff_stack"
JPG_SUBDIR = "02_tiff_jpg"
WORM_SEG_SUBDIR = "03_worm_segmentation"
RUNNING_MARKER = ".running"
COMPLETE_MARKER = ".complete"
LOCAL_CHUNK_ROOT = os.path.join(SCRIPT_DIR, "_sam2_worm_chunks")

tiff_stack_dir = os.path.join(RESULTS_ROOT, RUN_ID, STACK_SUBDIR)
parent_video_dir = os.path.join(RESULTS_ROOT, RUN_ID, JPG_SUBDIR)
worm_seg_dir = os.path.join(RESULTS_ROOT, RUN_ID, WORM_SEG_SUBDIR)

REUSE_EXISTING_JPG_FRAMES = True
CHUNK_SIZE = 300
OVERLAP = 1

# Validity thresholds. Tune these after inspecting overlays/frame_validity.csv.
MIN_WORM_MASK_AREA = 500
MIN_WORM_AREA_FRACTION = 0.002
BORDER_MARGIN = 5
OVERLAY_INTERVAL = 10
AUTO_PROMPT_FROM_EXISTING_MASK = True
MAX_AUTO_PROMPT_MASK_DISTANCE = 200
AUTO_PROMPT_WORM_YOLO = True
WORM_YOLO_MODEL_PATH = os.path.join(SCRIPT_DIR, "training_runs", "worm_detector", "weights", "best.pt")
WORM_YOLO_CONF_THRESHOLD = 0.50
WORM_YOLO_DEVICE = "cpu"
WORM_YOLO_PADDING = 10
WORM_YOLO_PADDING_FRACTION = 0.05
WORM_YOLO_PREVIEW = True
SAVE_TRAINING_DATA = True
TRAINING_DATA_DIR = os.path.join(SCRIPT_DIR, "training_data_worm_detector")
TRAINING_DATA_VALID_ONLY = True
TRAINING_DATA_INTERVAL = 1
TRAINING_DATA_SAVE_OVERLAYS = True
TQDM_KWARGS = {
    "dynamic_ncols": True,
    "leave": False,
    "mininterval": 0.5,
    "disable": True,
}
PROGRESS_UPDATE_INTERVAL_SEC = 0.5


class OutputDriveUnavailable(RuntimeError):
    pass


def ensure_output_drive_available():
    run_root = os.path.join(RESULTS_ROOT, RUN_ID)
    if not os.path.isdir(run_root):
        raise OutputDriveUnavailable(f"Output drive/path is unavailable: {run_root}")


def interactive_collect_bboxes(image_path, object_ids=None):
    backend = plt.get_backend().lower()
    if backend in ("agg", "pdf", "ps", "svg", "template"):
        raise RuntimeError(
            f"Matplotlib backend '{plt.get_backend()}' is not interactive; "
            "run this script from an environment that can open a GUI window."
        )
    if object_ids is None:
        object_ids = (1,)
    img = Image.open(image_path)
    fig, ax = plt.subplots(figsize=(12, 9))
    fig.canvas.toolbar_visible = True
    ax.imshow(img)
    ax.set_axis_off()

    storage = {oid: {"boxes": []} for oid in object_ids}
    current_obj = object_ids[0]
    drawing = False
    start_point = None
    current_rect = None
    object_colors = {1: (0.0, 1.0, 0.0)}

    def redraw():
        ax.clear()
        ax.imshow(img)
        ax.set_axis_off()
        for oid in sorted(storage.keys()):
            for box in storage[oid]["boxes"]:
                x1, y1, x2, y2 = box
                rect = plt.Rectangle((x1, y1), x2 - x1, y2 - y1,
                                     linewidth=2, edgecolor=object_colors.get(oid, (0.5, 0.5, 0.5)),
                                     facecolor="none")
                ax.add_patch(rect)
        ax.text(0.01, 0.99,
                "Draw whole-worm box | u=undo, c=clear, enter/q=finish | close without box=skip frame",
                transform=ax.transAxes, va="top", ha="left", color="white",
                bbox=dict(facecolor="black", alpha=0.7, edgecolor="none"))
        fig.canvas.draw_idle()

    def on_press(event):
        nonlocal drawing, start_point
        if event.inaxes != ax or event.button != MouseButton.LEFT:
            return
        if event.xdata is None or event.ydata is None:
            return
        drawing = True
        start_point = (event.xdata, event.ydata)

    def on_motion(event):
        nonlocal current_rect
        if not drawing or start_point is None or event.inaxes != ax:
            return
        if event.xdata is None or event.ydata is None:
            return
        if current_rect is not None:
            current_rect.remove()
            current_rect = None
        x1, y1 = start_point
        current_rect = plt.Rectangle((x1, y1), event.xdata - x1, event.ydata - y1,
                                     linewidth=2, edgecolor="lime", facecolor="none", linestyle="--")
        ax.add_patch(current_rect)
        fig.canvas.draw_idle()

    def on_release(event):
        nonlocal drawing, start_point, current_rect
        if not drawing or start_point is None or event.inaxes != ax:
            return
        if event.xdata is None or event.ydata is None:
            return
        drawing = False
        if current_rect is not None:
            current_rect.remove()
            current_rect = None
        x1, y1 = start_point
        x2, y2 = event.xdata, event.ydata
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
            storage[current_obj]["boxes"].append([x1, y1, x2, y2])
        start_point = None
        redraw()

    def on_key(event):
        key = event.key
        if key == "u":
            if storage[current_obj]["boxes"]:
                storage[current_obj]["boxes"].pop()
            redraw()
        elif key == "c":
            storage[current_obj]["boxes"] = []
            redraw()
        elif key in ("enter", "return", "q", "escape"):
            plt.close(fig)

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)
    fig.canvas.mpl_connect("key_press_event", on_key)
    redraw()
    plt.show()

    out = {}
    for oid, data in storage.items():
        if data["boxes"]:
            out[oid] = np.array(data["boxes"][-1], dtype=np.float32)
    return out


def natural_frame_names(frame_dir):
    if not os.path.isdir(frame_dir):
        return []
    names = [n for n in os.listdir(frame_dir)
             if os.path.splitext(n)[1].lower() in (".jpg", ".jpeg") and os.path.splitext(n)[0].isdigit()]
    return sorted(names, key=lambda n: int(os.path.splitext(n)[0]))


def get_sorted_frame_indices(names):
    return [int(os.path.splitext(name)[0]) for name in names if os.path.splitext(name)[0].isdigit()]


def normalize_frame_to_uint8(frame):
    if frame.dtype == np.uint8:
        return frame
    frame_min = frame.min()
    frame_max = frame.max()
    if frame_max <= frame_min:
        return np.zeros(frame.shape, dtype=np.uint8)
    return ((frame - frame_min) / (frame_max - frame_min) * 255).astype(np.uint8)


def load_tiff_stack(tiff_path):
    stack = tifffile.imread(tiff_path)
    if stack.ndim == 2:
        stack = stack[np.newaxis, ...]
    return stack


def tiff_stack_to_temp_jpgs(tiff_stack, temp_dir):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    frame_names = []
    for i, frame in enumerate(tqdm(tiff_stack, desc="Extracting temporary JPG frames", **TQDM_KWARGS)):
        frame_name = f"{i:06d}.jpg"
        frame_path = os.path.join(temp_dir, frame_name)
        if not cv2.imwrite(frame_path, normalize_frame_to_uint8(frame)):
            raise OutputDriveUnavailable(f"Could not write temporary frame: {frame_path}")
        frame_names.append(frame_name)
    return frame_names


def resolve_image_path(dir_path, frame_idx):
    a = os.path.join(dir_path, f"{frame_idx:06d}.jpg")
    b = os.path.join(dir_path, f"{frame_idx}.jpg")
    if os.path.exists(a):
        return a
    if os.path.exists(b):
        return b
    return a


def create_chunk_dir(base_dir, indices, chunk_root, chunk_id):
    ensure_output_drive_available()
    os.makedirs(chunk_root, exist_ok=True)
    chunk_dir = os.path.join(chunk_root, f"chunk_{chunk_id:04d}")
    os.makedirs(chunk_dir, exist_ok=True)
    local_to_global = []
    for local_idx, global_idx in enumerate(indices):
        src = resolve_image_path(base_dir, global_idx)
        dst = os.path.join(chunk_dir, f"{local_idx:06d}.jpg")
        if not os.path.exists(src):
            raise OutputDriveUnavailable(f"Could not find source frame: {src}")
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
        local_to_global.append(global_idx)
    return chunk_dir, local_to_global


def clear_accelerator_cache():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        torch.mps.empty_cache()


class SingleLineProgress:
    def __init__(self, label, total, update_interval=PROGRESS_UPDATE_INTERVAL_SEC):
        self.label = label
        self.total = max(int(total), 1)
        self.count = 0
        self.update_interval = update_interval
        self.last_update = 0.0
        self.last_len = 0

    def update(self, frame=None, status=None, area=None, force=False):
        self.count += 1
        now = time.time()
        if not force and now - self.last_update < self.update_interval and self.count < self.total:
            return
        self.last_update = now
        percent = min(100.0, 100.0 * self.count / self.total)
        parts = [f"\r{self.label}: {self.count}/{self.total} ({percent:5.1f}%)"]
        if frame is not None:
            parts.append(f"frame={frame}")
        if status is not None:
            parts.append(f"status={status}")
        if area is not None:
            parts.append(f"area={area}")
        text = " | ".join(parts)
        pad = " " * max(0, self.last_len - len(text))
        sys.stdout.write(text + pad)
        sys.stdout.flush()
        self.last_len = len(text)

    def close(self):
        if self.last_len:
            sys.stdout.write("\r" + " " * self.last_len + "\r")
            sys.stdout.flush()
            self.last_len = 0


def mask_to_bbox(mask):
    if isinstance(mask, torch.Tensor):
        mask = mask.cpu().numpy()
    mask = np.squeeze(mask)
    if mask.dtype != bool:
        mask = mask > 0.5
    ys, xs = np.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        return None, mask
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1), mask


def build_bbox_from_mask(mask, img_shape):
    bbox, mask = mask_to_bbox(mask)
    if bbox is None:
        return None
    x1, y1, x2, y2 = bbox
    h, w = img_shape[:2]
    pad = 6
    return np.array([max(0, x1 - pad), max(0, y1 - pad), min(w - 1, x2 + pad), min(h - 1, y2 + pad)], dtype=np.float32)


_worm_yolo_model = None


def expand_bbox_with_padding(bbox, image_shape, padding_px, padding_fraction):
    h, w = image_shape[:2]
    x1, y1, x2, y2 = [float(v) for v in bbox]
    bw = max(1.0, x2 - x1)
    bh = max(1.0, y2 - y1)
    pad_x = padding_px + bw * padding_fraction
    pad_y = padding_px + bh * padding_fraction
    return np.array([
        max(0.0, x1 - pad_x),
        max(0.0, y1 - pad_y),
        min(float(w - 1), x2 + pad_x),
        min(float(h - 1), y2 + pad_y),
    ], dtype=np.float32)


def get_worm_yolo_model():
    global _worm_yolo_model
    if _worm_yolo_model is not None:
        return _worm_yolo_model
    if not os.path.exists(WORM_YOLO_MODEL_PATH):
        print(f"[worm yolo] model not found: {WORM_YOLO_MODEL_PATH}")
        return None
    os.environ.setdefault("YOLO_CONFIG_DIR", os.path.join(SCRIPT_DIR, "Ultralytics"))
    try:
        from ultralytics import YOLO
    except Exception as exc:
        print(f"[worm yolo] could not import ultralytics: {exc}")
        return None
    _worm_yolo_model = YOLO(WORM_YOLO_MODEL_PATH)
    return _worm_yolo_model


def save_worm_yolo_prompt_preview(frame_path, output_dir, frame_idx, raw_bbox, padded_bbox, conf):
    if not WORM_YOLO_PREVIEW:
        return
    image = cv2.imread(frame_path)
    if image is None:
        return
    os.makedirs(output_dir, exist_ok=True)
    x1, y1, x2, y2 = [int(round(v)) for v in raw_bbox]
    px1, py1, px2, py2 = [int(round(v)) for v in padded_bbox]
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 255), 2)
    cv2.rectangle(image, (px1, py1), (px2, py2), (0, 0, 255), 2)
    cv2.putText(
        image,
        f"worm yolo {conf:.3f}",
        (max(6, px1), max(18, py1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 255),
        2,
    )
    preview_path = os.path.join(output_dir, f"{frame_idx:06d}_worm_yolo_prompt.jpg")
    cv2.imwrite(preview_path, image)


def auto_find_worm_bbox_yolo(frame_path, preview_dir=None, frame_idx=0):
    if not AUTO_PROMPT_WORM_YOLO:
        return None, None
    model = get_worm_yolo_model()
    if model is None:
        return None, None
    image = cv2.imread(frame_path)
    if image is None:
        return None, None
    try:
        with open(os.devnull, "w", encoding="utf-8") as devnull, contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            results = model.predict(
                source=frame_path,
                imgsz=640,
                conf=WORM_YOLO_CONF_THRESHOLD,
                device=WORM_YOLO_DEVICE,
                verbose=False,
                stream=False,
            )
    except Exception as exc:
        print(f"[worm yolo] prediction failed: {exc}")
        return None, None
    if not results or results[0].boxes is None or len(results[0].boxes) == 0:
        return None, None
    boxes = results[0].boxes
    confs = boxes.conf.cpu().numpy()
    best_idx = int(np.argmax(confs))
    best_conf = float(confs[best_idx])
    raw_bbox = boxes.xyxy[best_idx].cpu().numpy()
    padded_bbox = expand_bbox_with_padding(raw_bbox, image.shape, WORM_YOLO_PADDING, WORM_YOLO_PADDING_FRACTION)
    if preview_dir is not None:
        save_worm_yolo_prompt_preview(frame_path, preview_dir, frame_idx, raw_bbox, padded_bbox, best_conf)
    return padded_bbox, best_conf


def existing_mask_path(output_dir, frame_idx):
    return os.path.join(output_dir, "masks", f"{frame_idx:06d}_worm_mask.png")


def existing_mask_frame_indices(output_dir):
    mask_dir = os.path.join(output_dir, "masks")
    if not os.path.isdir(mask_dir):
        return []
    indices = []
    for name in os.listdir(mask_dir):
        if not name.endswith("_worm_mask.png"):
            continue
        try:
            indices.append(int(name[:6]))
        except ValueError:
            continue
    return sorted(indices)


def find_existing_prompt_mask(output_dir, target_frame):
    exact_path = existing_mask_path(output_dir, target_frame)
    if os.path.exists(exact_path):
        return target_frame, exact_path
    indices = existing_mask_frame_indices(output_dir)
    if not indices:
        return None, None
    nearest = min(indices, key=lambda idx: abs(idx - target_frame))
    if abs(nearest - target_frame) > MAX_AUTO_PROMPT_MASK_DISTANCE:
        return None, None
    return nearest, existing_mask_path(output_dir, nearest)


def build_bbox_from_existing_mask_file(mask_path, img_shape):
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return None
    return build_bbox_from_mask(mask > 0, img_shape)


def evaluate_worm_mask(mask, image_shape):
    bbox, mask = mask_to_bbox(mask)
    h, w = image_shape[:2]
    area = int(mask.sum())
    area_fraction = area / float(h * w)
    touches_border = False
    if bbox is not None:
        x1, y1, x2, y2 = bbox
        touches_border = x1 <= BORDER_MARGIN or y1 <= BORDER_MARGIN or x2 >= w - BORDER_MARGIN or y2 >= h - BORDER_MARGIN
    valid = area >= MIN_WORM_MASK_AREA and area_fraction >= MIN_WORM_AREA_FRACTION and not touches_border
    if area < MIN_WORM_MASK_AREA or area_fraction < MIN_WORM_AREA_FRACTION:
        reason = "mask_too_small"
    elif touches_border:
        reason = "touches_border"
    else:
        reason = "valid"
    return valid, area, area_fraction, touches_border, reason, mask, bbox


def save_mask_and_overlay(output_dir, frame_idx, image, mask, bbox, valid, reason):
    ensure_output_drive_available()
    mask_dir = os.path.join(output_dir, "masks")
    overlay_dir = os.path.join(output_dir, "overlays")
    os.makedirs(mask_dir, exist_ok=True)
    os.makedirs(overlay_dir, exist_ok=True)
    mask_path = os.path.join(mask_dir, f"{frame_idx:06d}_worm_mask.png")
    if not cv2.imwrite(mask_path, mask.astype(np.uint8) * 255):
        raise OutputDriveUnavailable(f"Could not write mask: {mask_path}")
    if frame_idx % OVERLAY_INTERVAL != 0:
        return
    overlay = image.copy()
    color = np.zeros_like(overlay)
    color[:, :, 1] = 255 if valid else 128
    color[:, :, 2] = 0 if valid else 255
    overlay = np.where(mask[:, :, None], cv2.addWeighted(overlay, 0.55, color, 0.45, 0), overlay)
    if bbox is not None:
        x1, y1, x2, y2 = bbox
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0) if valid else (0, 0, 255), 2)
    cv2.putText(overlay, reason, (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    overlay_path = os.path.join(overlay_dir, f"{frame_idx:06d}_overlay.jpg")
    if not cv2.imwrite(overlay_path, overlay):
        raise OutputDriveUnavailable(f"Could not write overlay: {overlay_path}")


def sanitize_filename(text):
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    return "".join(ch if ch in allowed else "_" for ch in text)


def bbox_to_yolo_line(bbox, image_shape, class_id=0):
    if bbox is None:
        return None
    h, w = image_shape[:2]
    if h <= 0 or w <= 0:
        return None
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(w - 1, int(x1)))
    x2 = max(0, min(w - 1, int(x2)))
    y1 = max(0, min(h - 1, int(y1)))
    y2 = max(0, min(h - 1, int(y2)))
    if x2 <= x1 or y2 <= y1:
        return None
    cx = ((x1 + x2) / 2.0) / w
    cy = ((y1 + y2) / 2.0) / h
    bw = (x2 - x1) / w
    bh = (y2 - y1) / h
    return f"{class_id} {cx:.8f} {cy:.8f} {bw:.8f} {bh:.8f}\n"


def save_training_data(stack_name, frame_idx, image, mask, bbox, valid, reason):
    if not SAVE_TRAINING_DATA:
        return
    if TRAINING_DATA_VALID_ONLY and not valid:
        return
    if TRAINING_DATA_INTERVAL > 1 and frame_idx % TRAINING_DATA_INTERVAL != 0:
        return
    label_line = bbox_to_yolo_line(bbox, image.shape)
    if label_line is None:
        return

    safe_stack = sanitize_filename(stack_name)
    sample_name = f"{safe_stack}_{frame_idx:06d}"
    image_dir = os.path.join(TRAINING_DATA_DIR, "images")
    mask_dir = os.path.join(TRAINING_DATA_DIR, "masks")
    label_dir = os.path.join(TRAINING_DATA_DIR, "labels_yolo")
    overlay_dir = os.path.join(TRAINING_DATA_DIR, "overlays")
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(mask_dir, exist_ok=True)
    os.makedirs(label_dir, exist_ok=True)
    if TRAINING_DATA_SAVE_OVERLAYS:
        os.makedirs(overlay_dir, exist_ok=True)

    image_path = os.path.join(image_dir, sample_name + ".jpg")
    mask_path = os.path.join(mask_dir, sample_name + "_worm_mask.png")
    label_path = os.path.join(label_dir, sample_name + ".txt")
    if not cv2.imwrite(image_path, image):
        raise OutputDriveUnavailable(f"Could not write training image: {image_path}")
    if not cv2.imwrite(mask_path, mask.astype(np.uint8) * 255):
        raise OutputDriveUnavailable(f"Could not write training mask: {mask_path}")
    with open(label_path, "w", encoding="utf-8") as f:
        f.write(label_line)

    if TRAINING_DATA_SAVE_OVERLAYS:
        overlay = image.copy()
        color = np.zeros_like(overlay)
        color[:, :, 1] = 255 if valid else 128
        color[:, :, 2] = 0 if valid else 255
        overlay = np.where(mask[:, :, None], cv2.addWeighted(overlay, 0.55, color, 0.45, 0), overlay)
        x1, y1, x2, y2 = bbox
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0) if valid else (0, 0, 255), 2)
        cv2.putText(overlay, reason, (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        overlay_path = os.path.join(overlay_dir, sample_name + "_overlay.jpg")
        if not cv2.imwrite(overlay_path, overlay):
            raise OutputDriveUnavailable(f"Could not write training overlay: {overlay_path}")


def write_validity_csv(output_dir, rows, filename="frame_validity.csv", quiet=False):
    ensure_output_drive_available()
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, filename)
    tmp_path = csv_path + ".tmp"
    fields = ["frame", "valid", "reason", "worm_area", "area_fraction", "touches_border", "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2"]
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    os.replace(tmp_path, csv_path)
    if not quiet:
        print(f"Frame validity CSV saved to: {csv_path}")


def get_processed_outputs(output_root):
    processed = set()
    try:
        if os.path.isdir(output_root):
            for name in os.listdir(output_root):
                sample_dir = os.path.join(output_root, name)
                if (
                    os.path.exists(os.path.join(sample_dir, "frame_validity.csv"))
                    and os.path.exists(os.path.join(sample_dir, COMPLETE_MARKER))
                ):
                    processed.add(name)
    except OSError as exc:
        raise OutputDriveUnavailable(f"Could not read output directory: {output_root}\n{exc}") from exc
    return processed


def collect_tiff_inputs():
    processed = get_processed_outputs(worm_seg_dir)
    if REUSE_EXISTING_JPG_FRAMES:
        try:
            video_names = sorted(
                name for name in os.listdir(parent_video_dir)
                if os.path.isdir(os.path.join(parent_video_dir, name))
            )
        except OSError as exc:
            raise OutputDriveUnavailable(f"Could not read JPG frame directory: {parent_video_dir}\n{exc}") from exc
        if video_names:
            pending = [name for name in video_names if name not in processed]
            print(f"JPG frame folders total: {len(video_names)}, already worm-segmented: {len(video_names) - len(pending)}, to process: {len(pending)}")
            return [os.path.join(parent_video_dir, name) for name in pending]

    try:
        if not os.path.isdir(tiff_stack_dir):
            raise FileNotFoundError(tiff_stack_dir)
        all_tiffs = sorted(f for f in os.listdir(tiff_stack_dir) if f.lower().endswith((".tif", ".tiff")))
        pending = [f for f in all_tiffs if os.path.splitext(f)[0] not in processed]
        print(f"TIFF stacks total: {len(all_tiffs)}, already worm-segmented: {len(all_tiffs) - len(pending)}, to process: {len(pending)}")
        return [os.path.join(tiff_stack_dir, f) for f in pending]
    except OSError as exc:
        if not REUSE_EXISTING_JPG_FRAMES:
            raise OutputDriveUnavailable(f"Could not read TIFF stack directory: {tiff_stack_dir}\n{exc}") from exc
        print(f"Warning: could not read TIFF stack directory, falling back to JPG frame folders.\n{exc}")
        try:
            video_names = sorted(
                name for name in os.listdir(parent_video_dir)
                if os.path.isdir(os.path.join(parent_video_dir, name))
            )
        except OSError as video_exc:
            raise OutputDriveUnavailable(f"Could not read JPG frame directory: {parent_video_dir}\n{video_exc}") from video_exc
        pending = [name for name in video_names if name not in processed]
        print(f"JPG frame folders total: {len(video_names)}, already worm-segmented: {len(video_names) - len(pending)}, to process: {len(pending)}")
        return [os.path.join(parent_video_dir, name) for name in pending]


def validate_paths():
    missing = []
    for label, path in (
        ("JPG frame directory", parent_video_dir),
        ("SAM2 checkpoint", sam2_checkpoint),
    ):
        try:
            exists = os.path.exists(path)
        except OSError as exc:
            raise OutputDriveUnavailable(f"Could not access {label}: {path}\n{exc}") from exc
        if not exists:
            missing.append(f"{label}: {path}")
    if not REUSE_EXISTING_JPG_FRAMES:
        try:
            tiff_exists = os.path.exists(tiff_stack_dir)
        except OSError as exc:
            raise OutputDriveUnavailable(f"Could not access TIFF stack directory: {tiff_stack_dir}\n{exc}") from exc
        if not tiff_exists:
            missing.append(f"TIFF stack directory: {tiff_stack_dir}")
    if missing:
        raise FileNotFoundError("Missing required path(s):\n" + "\n".join(missing))


def mark_running(output_dir, stack_name):
    ensure_output_drive_available()
    os.makedirs(output_dir, exist_ok=True)
    marker_path = os.path.join(output_dir, RUNNING_MARKER)
    with open(marker_path, "w", encoding="utf-8") as f:
        f.write(f"{stack_name}\nstarted={time.strftime('%Y-%m-%d %H:%M:%S')}\n")


def mark_complete(output_dir, stack_name):
    ensure_output_drive_available()
    complete_path = os.path.join(output_dir, COMPLETE_MARKER)
    with open(complete_path, "w", encoding="utf-8") as f:
        f.write(f"{stack_name}\ncompleted={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    running_path = os.path.join(output_dir, RUNNING_MARKER)
    if os.path.exists(running_path):
        os.remove(running_path)


def main():
    validate_paths()
    inputs = collect_tiff_inputs()
    if not inputs:
        print("All files have worm segmentation outputs.")
        return
    predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint, device=device)

    stopped_early = False
    for file_idx, input_path in enumerate(inputs, 1):
        stack_name = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = os.path.join(worm_seg_dir, stack_name)
        print(f"\n{'=' * 60}")
        print(f"[{file_idx}/{len(inputs)}] Segmenting whole worm: {stack_name}")
        print(f"{'=' * 60}")
        temp_dir = None
        chunk_root = None

        try:
            mark_running(output_dir, stack_name)
            cached_jpg_dir = os.path.join(parent_video_dir, stack_name)
            frame_names = natural_frame_names(cached_jpg_dir) if REUSE_EXISTING_JPG_FRAMES else []
            if frame_names:
                video_dir = cached_jpg_dir
                print(f"Using existing JPG frames: {video_dir} ({len(frame_names)} frame(s))")
            else:
                tiff_stack = load_tiff_stack(input_path)
                temp_dir = os.path.join(output_dir, ".temp_frames")
                frame_names = tiff_stack_to_temp_jpgs(tiff_stack, temp_dir)
                video_dir = temp_dir
                print(f"Generated temporary JPG frames: {video_dir} ({len(frame_names)} frame(s))")

            all_indices = get_sorted_frame_indices(frame_names)
            if not all_indices:
                print("No readable frames. Skipping this file.")
                continue

            frame_rows = {}
            worm_segments = {}
            chunk_root = os.path.join(LOCAL_CHUNK_ROOT, stack_name)
            if os.path.exists(chunk_root):
                shutil.rmtree(chunk_root)
            os.makedirs(chunk_root, exist_ok=True)

            i = 0
            chunk_id = 0
            while i < len(all_indices):
                ensure_output_drive_available()
                end_idx_exclusive = min(i + CHUNK_SIZE, len(all_indices))
                start_i = i if chunk_id == 0 else max(i - OVERLAP, 0)
                indices = all_indices[start_i:end_idx_exclusive]
                chunk_id += 1
                chunk_dir, local_to_global = create_chunk_dir(video_dir, indices, chunk_root, chunk_id)
                print(f"[worm chunk {chunk_id}] Preparing SAM2 state for {len(local_to_global)} frame(s)...")
                inference_state = predictor.init_state(video_path=chunk_dir)
                seed_local_idx = 0
                seed_global_idx = local_to_global[0]
                seed_frame_path = os.path.join(chunk_dir, f"{seed_local_idx:06d}.jpg")
                print(f"\n--- Worm chunk {chunk_id} start (global frame {seed_global_idx}) ---")

                seeded = False
                if chunk_id > 1 and seed_global_idx in worm_segments:
                    prev_mask = next(iter(worm_segments[seed_global_idx].values()))
                    seed_img = cv2.imread(seed_frame_path)
                    seed_bbox = build_bbox_from_mask(prev_mask, seed_img.shape if seed_img is not None else (1, 1, 3))
                    if seed_bbox is not None:
                        predictor.add_new_points_or_box(inference_state=inference_state, frame_idx=seed_local_idx, obj_id=1, box=seed_bbox)
                        seeded = True
                        print(f"[worm chunk {chunk_id}] Auto-seeded from previous worm mask")

                if not seeded and AUTO_PROMPT_FROM_EXISTING_MASK:
                    seed_img = cv2.imread(seed_frame_path)
                    if seed_img is not None:
                        prompt_frame, prompt_mask_path = find_existing_prompt_mask(output_dir, seed_global_idx)
                        if prompt_mask_path is not None:
                            seed_bbox = build_bbox_from_existing_mask_file(prompt_mask_path, seed_img.shape)
                            if seed_bbox is not None:
                                predictor.add_new_points_or_box(
                                    inference_state=inference_state,
                                    frame_idx=seed_local_idx,
                                    obj_id=1,
                                    box=seed_bbox,
                                )
                                seeded = True
                                distance = abs(prompt_frame - seed_global_idx)
                                print(
                                    f"[worm chunk {chunk_id}] Auto-prompted from existing mask "
                                    f"frame {prompt_frame} (distance={distance})"
                                )

                if not seeded and AUTO_PROMPT_WORM_YOLO:
                    preview_dir = os.path.join(output_dir, "auto_yolo_prompt_previews")
                    seed_bbox, yolo_conf = auto_find_worm_bbox_yolo(
                        seed_frame_path,
                        preview_dir=preview_dir,
                        frame_idx=seed_global_idx,
                    )
                    if seed_bbox is not None:
                        predictor.add_new_points_or_box(
                            inference_state=inference_state,
                            frame_idx=seed_local_idx,
                            obj_id=1,
                            box=seed_bbox,
                        )
                        seeded = True
                        print(
                            f"[worm chunk {chunk_id}] Auto-prompted by worm YOLO "
                            f"(conf={yolo_conf:.3f}, frame={seed_global_idx})"
                        )
                    else:
                        print(f"[worm chunk {chunk_id}] Worm YOLO auto-prompt failed; manual prompt required.")

                if not seeded:
                    print("Draw a bounding box around the whole worm. Close/finish without a box to mark this frame invalid and try next frame.")
                    user_bboxes = interactive_collect_bboxes(seed_frame_path, object_ids=(1,))
                    if not user_bboxes or 1 not in user_bboxes:
                        image = cv2.imread(seed_frame_path)
                        h, w = image.shape[:2] if image is not None else (0, 0)
                        frame_rows[seed_global_idx] = {
                            "frame": seed_global_idx, "valid": False, "reason": "no_prompt", "worm_area": 0,
                            "area_fraction": 0.0, "touches_border": False,
                            "bbox_x1": "", "bbox_y1": "", "bbox_x2": "", "bbox_y2": "",
                        }
                        print(f"[worm chunk {chunk_id}] No prompt at frame {seed_global_idx}; skipping this frame.")
                        del inference_state
                        clear_accelerator_cache()
                        i += 1
                        continue
                    predictor.add_new_points_or_box(inference_state=inference_state, frame_idx=seed_local_idx, obj_id=1, box=user_bboxes[1])

                chunk_start_time = time.time()
                expected_frames = max(0, len(local_to_global) - seed_local_idx)
                progress = SingleLineProgress(f"Worm chunk {chunk_id}", expected_frames)
                try:
                    with open(os.devnull, "w", encoding="utf-8") as devnull, contextlib.redirect_stderr(devnull):
                        propagation = predictor.propagate_in_video(
                            inference_state,
                            start_frame_idx=seed_local_idx,
                            reverse=False,
                        )
                        for out_local_idx, out_obj_ids, out_mask_logits in propagation:
                            global_idx = local_to_global[out_local_idx]
                            if chunk_id > 1 and out_local_idx == 0 and global_idx in worm_segments:
                                progress.update(frame=global_idx, status="overlap")
                                continue
                            worm_segments[global_idx] = {
                                out_obj_id: (out_mask_logits[k] > 0.0).cpu().numpy()
                                for k, out_obj_id in enumerate(out_obj_ids)
                            }
                            image_path = os.path.join(chunk_dir, f"{out_local_idx:06d}.jpg")
                            image = cv2.imread(image_path)
                            if image is None:
                                raise OutputDriveUnavailable(f"Could not read frame: {image_path}")
                            mask = next(iter(worm_segments[global_idx].values()))
                            valid, area, area_fraction, touches_border, reason, mask_bool, bbox = evaluate_worm_mask(mask, image.shape)
                            save_mask_and_overlay(output_dir, global_idx, image, mask_bool, bbox, valid, reason)
                            save_training_data(stack_name, global_idx, image, mask_bool, bbox, valid, reason)
                            if bbox is None:
                                bx1 = by1 = bx2 = by2 = ""
                            else:
                                bx1, by1, bx2, by2 = bbox
                            frame_rows[global_idx] = {
                                "frame": global_idx,
                                "valid": valid,
                                "reason": reason,
                                "worm_area": area,
                                "area_fraction": f"{area_fraction:.8f}",
                                "touches_border": touches_border,
                                "bbox_x1": bx1,
                                "bbox_y1": by1,
                                "bbox_x2": bx2,
                                "bbox_y2": by2,
                            }
                            progress.update(frame=global_idx, status=reason, area=area)
                finally:
                    progress.close()
                    del inference_state
                    clear_accelerator_cache()

                elapsed = time.time() - chunk_start_time
                print(f"[worm chunk {chunk_id}] Finished {len(local_to_global)} frame(s) in {elapsed:.1f}s")
                if frame_rows:
                    write_validity_csv(
                        output_dir,
                        [frame_rows[idx] for idx in sorted(frame_rows)],
                        "frame_validity_partial.csv",
                        quiet=True,
                    )
                i = end_idx_exclusive

            for frame_idx in all_indices:
                if frame_idx not in frame_rows:
                    frame_rows[frame_idx] = {
                        "frame": frame_idx, "valid": False, "reason": "not_processed", "worm_area": 0,
                        "area_fraction": 0.0, "touches_border": False,
                        "bbox_x1": "", "bbox_y1": "", "bbox_x2": "", "bbox_y2": "",
                    }

            write_validity_csv(output_dir, [frame_rows[idx] for idx in sorted(frame_rows)])
            mark_complete(output_dir, stack_name)
        except (OutputDriveUnavailable, OSError) as exc:
            print(f"\nOutput drive became unavailable. Stopping before the next file.\n{exc}")
            stopped_early = True
            break
        finally:
            if chunk_root is not None and os.path.exists(chunk_root):
                try:
                    shutil.rmtree(chunk_root)
                except Exception:
                    pass
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)

    if stopped_early:
        print("\nWhole-worm segmentation stopped early because the output drive became unavailable.")
    else:
        print("\nWhole-worm segmentation step complete.")


if __name__ == "__main__":
    main()
