"""
This script generates a cropped video around the RIA region.
"""
import csv
import os
import shutil
import sys
import time
import contextlib
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import torch
torch.cuda.empty_cache()
from tqdm import tqdm
import cv2
from matplotlib.backend_bases import MouseButton
import tifffile


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


class SingleLineProgress:
    def __init__(self, label, total, update_interval=0.5):
        self.label = label
        self.total = max(int(total), 1)
        self.count = 0
        self.update_interval = update_interval
        self.last_update = 0.0
        self.last_len = 0

    def update(self, count=None, force=False):
        if count is None:
            self.count += 1
        else:
            self.count = int(count)
        now = time.time()
        if not force and now - self.last_update < self.update_interval and self.count < self.total:
            return
        self.last_update = now
        percent = min(100.0, 100.0 * self.count / self.total)
        text = f"\r{self.label}: {self.count}/{self.total} ({percent:5.1f}%)"
        pad = " " * max(0, self.last_len - len(text))
        print(text + pad, end="", flush=True)
        self.last_len = len(text)

    def close(self):
        if self.last_len:
            print("\r" + " " * self.last_len + "\r", end="", flush=True)
            self.last_len = 0


def safe_rmtree(path, label="directory"):
    if not path or not os.path.exists(path):
        return True
    try:
        shutil.rmtree(path)
        return True
    except OSError as exc:
        print(f"[cleanup] Could not remove {label}: {path} ({exc})")
        return False

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")
print(f"using device: {device}")

from sam2.build_sam import build_sam2_video_predictor # type: ignore
sam2_checkpoint = r"C:\Users\34358\Desktop\Yue_analysis_WormSpy\sam2\checkpoints\sam2.1_hiera_tiny.pt"
model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml"
predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)

# Directory configuration. Usually you only need to edit RESULTS_ROOT and RUN_ID.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260529"
LOCAL_TEMP_ROOT = r"C:\sam2_temp"

STACK_SUBDIR = "01_tiff_stack"
JPG_SUBDIR = "02_tiff_jpg"
WORM_SEG_SUBDIR = "03_worm_segmentation"
CROP_SUBDIR = "04_ria_crop"
JPG_CROP_SUBDIR = "06_crop_jpg"
RIA_ANCHOR_SUBDIR = "04_ria_head_anchor"
RIA_MASK_SUBDIR = "04_ria_mask"
TEMPLATE_SUBDIR = "roi_templates"


def parse_bool_option(value, default=False):
    if value is None:
        return default
    value = str(value).strip().lower()
    if value in ("1", "true", "yes", "y", "on"):
        return True
    if value in ("0", "false", "no", "n", "off"):
        return False
    raise ValueError(f"Expected true/false value, got: {value}")


FORCE_REPROCESS = "--force" in sys.argv
INCLUDE_TOUCH_BORDER_FRAMES = True
ONLY_STACK = ""
for _i, _arg in enumerate(sys.argv[1:], 1):
    if _arg.startswith("--only-stack="):
        ONLY_STACK = _arg.split("=", 1)[1].strip()
    elif _arg == "--only-stack" and _i + 1 < len(sys.argv):
        ONLY_STACK = sys.argv[_i + 1].strip()
    elif _arg.startswith("--include-touch-border="):
        INCLUDE_TOUCH_BORDER_FRAMES = parse_bool_option(_arg.split("=", 1)[1], default=False)
    elif _arg == "--include-touch-border" and _i + 1 < len(sys.argv):
        INCLUDE_TOUCH_BORDER_FRAMES = parse_bool_option(sys.argv[_i + 1], default=False)
if FORCE_REPROCESS:
    print("[options] --force enabled: already-cropped stacks will be queued again.")
if ONLY_STACK:
    print(f"[options] --only-stack enabled: {ONLY_STACK}")
print(f"[options] include_touch_border={INCLUDE_TOUCH_BORDER_FRAMES}")

tiff_stack_dir = os.path.join(RESULTS_ROOT, RUN_ID, STACK_SUBDIR)
parent_video_dir = os.path.join(RESULTS_ROOT, RUN_ID, JPG_SUBDIR)
worm_seg_dir = os.path.join(RESULTS_ROOT, RUN_ID, WORM_SEG_SUBDIR)
crop_dir = os.path.join(RESULTS_ROOT, RUN_ID, CROP_SUBDIR)
jpg_crop_dir = os.path.join(RESULTS_ROOT, RUN_ID, JPG_CROP_SUBDIR)
ria_anchor_dir = os.path.join(RESULTS_ROOT, RUN_ID, RIA_ANCHOR_SUBDIR)
ria_mask_dir = os.path.join(RESULTS_ROOT, RUN_ID, RIA_MASK_SUBDIR)

# Keep False for the normal pipeline: 1ConvertTIFFtoStack.py -> 3AutoCrop.py.
# Set True only if you explicitly want to process folders from 02_tiff_jpg/.
PROCESS_JPG_VIDEOS = False

# Toggle: set to True to also save cropped JPG frame sequences for visualization.
# When False, only the TIFF stack crop is saved (faster, less disk space).
SAVE_JPG_CROP = True
REUSE_EXISTING_JPG_FRAMES = True

CONFIDENCE_THRESHOLD = 0.9
QUALITY_CHECK_INTERVAL = 100
MIN_RIA_MASK_AREA = 80
MIN_RIA_MASK_AREA_FRACTION_OF_RECENT_MEDIAN = 0.45
RIA_MASK_AREA_HISTORY_FRAMES = 300
VIS_INTERVAL = 100
CHUNK_SIZE = 300
OVERLAP = 1
RIA_CROP_SIZE = 110
FRAME_COPY_RETRIES = 3
FRAME_COPY_RETRY_DELAY_SEC = 0.5

# Automatic ROI prompt settings.
AUTO_ROI_YOLO = True
ALLOW_MANUAL_PROMPT = False
YOLO_RIA_MODEL_PATH = os.path.join(SCRIPT_DIR, "training_runs", "ria_detector", "weights", "best.pt")
YOLO_RIA_CONF_THRESHOLD = 0.35
YOLO_RIA_DEVICE = "cpu"
YOLO_RIA_PADDING = 6
YOLO_RIA_PADDING_FRACTION = 0.15
YOLO_RIA_PREVIEW = True
USE_WORM_MASK_TO_FILTER_RIA_YOLO = True
YOLO_RIA_MIN_WORM_NEARBY_RATIO = 0.15
YOLO_RIA_MIN_WORM_INSIDE_RATIO = 0.02
YOLO_RIA_WORM_MASK_DILATE_PX = 12
# 0 scans through the remainder of the current chunk until a reliable RIA is found.
REPROMPT_SCAN_AHEAD_FRAMES = 0

# Find the first frame where the RIA detector can provide a reliable SAM2 seed.
AUTO_SEED_FRAME = True
# 0 scans all worm-valid frames until the first RIA detection is found.
SEED_SCAN_FRAMES = 0

if "--no-auto-seed-frame" in sys.argv:
    AUTO_SEED_FRAME = False
elif "--auto-seed-frame" in sys.argv:
    AUTO_SEED_FRAME = True
if AUTO_SEED_FRAME:
    scan_description = "all worm-valid frames" if SEED_SCAN_FRAMES <= 0 else f"first {SEED_SCAN_FRAMES} frame(s)"
    print(f"[options] auto seed frame enabled: find first YOLO-detectable RIA in {scan_description}")
else:
    print("[options] auto seed frame disabled: use first frame in each chunk")

# Export SAM2 full-frame masks/bboxes for future detector training.
EXPORT_TRAINING_DATA = False
TRAIN_EXPORT_INTERVAL = 10
TRAINING_DATA_SUBDIR = "training_data_ria_detector"

def interactive_collect_bboxes(image_path, object_ids=None):
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
    object_colors = {1: (1.0, 0.0, 0.0)}

    def redraw():
        ax.clear()
        ax.imshow(img)
        ax.set_axis_off()
        for oid in sorted(storage.keys()):
            boxes = storage[oid]["boxes"]
            if not boxes:
                continue
            color = object_colors.get(oid, (0.5, 0.5, 0.5))
            for box in boxes:
                x1, y1, x2, y2 = box
                rect = plt.Rectangle((x1, y1), x2-x1, y2-y1,
                                     linewidth=2, edgecolor=color, facecolor='none')
                ax.add_patch(rect)
        obj_lines = []
        total = 0
        for oid in sorted(storage.keys()):
            boxes = storage[oid]["boxes"]
            total += len(boxes)
            name = "RIA" if oid == 1 else str(oid)
            obj_lines.append(f"{oid}:{name}  boxes:{len(boxes)}")
        obj_list = ",  ".join(obj_lines)
        ax.text(0.01, 0.99,
            f"Active={current_obj}:{'RIA' if current_obj == 1 else str(current_obj)} | Total boxes: {total}\n"
            f"Keys: 1 select obj, click+drag=draw box, u=undo, c=clear, enter/q=finish\n"
            f"Use toolbar above for zoom/pan. Objects: {obj_list}",
            transform=ax.transAxes, va='top', ha='left', color='white',
            bbox=dict(facecolor='black', alpha=0.7, edgecolor='none'))
        fig.canvas.draw_idle()

    def on_press(event):
        nonlocal drawing, start_point, current_rect
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
        color = object_colors.get(current_obj, (0.5, 0.5, 0.5))
        current_rect = plt.Rectangle((x1, y1), event.xdata-x1, event.ydata-y1,
                                     linewidth=2, edgecolor=color, facecolor='none',
                                     linestyle='--', alpha=0.7)
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
        if abs(x2-x1) > 5 and abs(y2-y1) > 5:
            storage[current_obj]["boxes"].append([x1, y1, x2, y2])
            redraw()
        start_point = None

    def on_key(event):
        nonlocal current_obj
        key = event.key
        if not key:
            return
        if len(key) == 1 and key.isdigit():
            oid = int(key)
            if oid in storage:
                current_obj = oid
                redraw()
            return
        if key == 'u':
            boxes = storage[current_obj]["boxes"]
            if boxes:
                boxes.pop()
            redraw()
            return
        if key == 'c':
            storage[current_obj] = {"boxes": []}
            redraw()
            return
        if key in ('enter', 'return', 'q'):
            plt.close(fig)
            return

    cid1 = fig.canvas.mpl_connect('button_press_event', on_press)
    cid2 = fig.canvas.mpl_connect('motion_notify_event', on_motion)
    cid3 = fig.canvas.mpl_connect('button_release_event', on_release)
    cid4 = fig.canvas.mpl_connect('key_press_event', on_key)
    redraw()
    plt.show()
    fig.canvas.mpl_disconnect(cid1)
    fig.canvas.mpl_disconnect(cid2)
    fig.canvas.mpl_disconnect(cid3)
    fig.canvas.mpl_disconnect(cid4)

    out = {}
    for oid, d in storage.items():
        if len(d["boxes"]) == 0:
            continue
        out[oid] = np.array(d["boxes"][-1], dtype=np.float32)
    return out

def show_mask(mask, ax, obj_id=None, random_color=False):
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        cmap = plt.get_cmap("tab10")
        cmap_idx = 0 if obj_id is None else obj_id
        color = np.array([*cmap(cmap_idx)[:3], 0.6])
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_image)

def show_points(coords, labels, ax, marker_size=20):
    pos_points = coords[labels==1]
    neg_points = coords[labels==0]
    ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)
    ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)

def load_tiff_stack(tiff_path):
    stack = tifffile.imread(tiff_path)
    if stack.ndim == 2:
        stack = stack[np.newaxis, ...]
    return stack

def save_tiff_stack(frames, output_path):
    tifffile.imwrite(output_path, frames)

# [NEW] Returns a set of base names (without extension) of TIFF stacks that
# have already been cropped, by scanning crop_dir for "*_crop.tif" files.
def get_processed_crops(crop_directory):
    processed = set()
    if os.path.isdir(crop_directory):
        for f in os.listdir(crop_directory):
            if f.endswith("_crop.tif"):
                base = f[: -len("_crop.tif")]
                processed.add(base)
    else:
        print(f"Crop directory not found yet: {crop_directory} (will be created on first run)")
    return processed

def get_all_unprocessed_tiff_stacks(stack_dir, crop_directory):
    if not os.path.isdir(stack_dir):
        print(f"TIFF stack directory not found: {stack_dir}")
        return []

    processed = get_processed_crops(crop_directory)
    all_tiffs = sorted(f for f in os.listdir(stack_dir) if f.lower().endswith((".tif", ".tiff")))
    if ONLY_STACK:
        wanted = ONLY_STACK
        if not wanted.lower().endswith((".tif", ".tiff")):
            wanted_base = wanted
        else:
            wanted_base = os.path.splitext(wanted)[0]
        all_tiffs = [f for f in all_tiffs if os.path.splitext(f)[0] == wanted_base]
        if not all_tiffs:
            print(f"[only-stack] No TIFF stack matched: {ONLY_STACK}")
    if FORCE_REPROCESS:
        skipped = []
        pending = all_tiffs
    else:
        skipped = [f for f in all_tiffs if os.path.splitext(f)[0] in processed]
        pending = [f for f in all_tiffs if os.path.splitext(f)[0] not in processed]

    print(f"TIFF stacks total: {len(all_tiffs)}, already processed: {len(skipped)}, to process: {len(pending)}")
    if skipped:
        print("  Skipping:")
        for i, f in enumerate(skipped, 1):
            print(f"    [{i}/{len(skipped)}] {f}")
    if pending:
        print("  Queued:")
        for i, f in enumerate(pending, 1):
            print(f"    [{i}/{len(pending)}] {f}")

    return [os.path.join(stack_dir, f) for f in pending]

def get_all_unprocessed_videos(parent_dir, crop_directory):
    if not os.path.isdir(parent_dir):
        print(f"JPG video directory not found: {parent_dir}")
        return []

    processed = get_processed_crops(crop_directory)
    all_videos = sorted(d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d)))
    if ONLY_STACK:
        all_videos = [video for video in all_videos if video == ONLY_STACK]
    if FORCE_REPROCESS:
        pending = all_videos
        skipped = []
    else:
        pending = [video for video in all_videos if video not in processed]
        skipped = [video for video in all_videos if video in processed]

    print(f"JPG video folders total: {len(all_videos)}, already processed: {len(skipped)}, to process: {len(pending)}")
    return [os.path.join(parent_dir, video) for video in pending]

def get_sorted_frame_indices(names):
    indices = []
    for name in names:
        stem = os.path.splitext(name)[0]
        if stem.isdigit():
            indices.append(int(stem))
    return indices

def get_jpg_frame_names(frame_dir):
    if not os.path.isdir(frame_dir):
        return []
    frame_names = [
        name for name in os.listdir(frame_dir)
        if os.path.splitext(name)[-1].lower() in (".jpg", ".jpeg")
        and os.path.splitext(name)[0].isdigit()
    ]
    return sorted(frame_names, key=lambda name: int(os.path.splitext(name)[0]))

def normalize_frame_to_uint8(frame):
    if frame.dtype == np.uint8:
        return frame
    frame_min = frame.min()
    frame_max = frame.max()
    if frame_max <= frame_min:
        return np.zeros(frame.shape, dtype=np.uint8)
    return ((frame - frame_min) / (frame_max - frame_min) * 255).astype(np.uint8)

def tiff_stack_to_temp_jpgs(tiff_stack, temp_dir):
    if os.path.exists(temp_dir):
        safe_rmtree(temp_dir, "temporary frame directory")
    os.makedirs(temp_dir, exist_ok=True)

    frame_names = []
    progress = SingleLineProgress("Extracting temporary JPG frames", len(tiff_stack))
    try:
        for i, frame in enumerate(tiff_stack):
            frame_name = f"{i:06d}.jpg"
            frame_path = os.path.join(temp_dir, frame_name)
            cv2.imwrite(frame_path, normalize_frame_to_uint8(frame))
            frame_names.append(frame_name)
            progress.update()
    finally:
        progress.close()
    return frame_names

def create_chunk_dir(base_dir, indices, chunk_root, chunk_id):
    os.makedirs(chunk_root, exist_ok=True)
    chunk_dir = os.path.join(chunk_root, f"chunk_{chunk_id:04d}")
    if os.path.exists(chunk_dir):
        if not safe_rmtree(chunk_dir, f"chunk {chunk_id} directory"):
            chunk_dir = os.path.join(chunk_root, f"chunk_{chunk_id:04d}_{int(time.time() * 1000)}")
    os.makedirs(chunk_dir, exist_ok=True)
    local_to_global = []
    skipped = []
    for global_idx in indices:
        cand_a = os.path.join(base_dir, f"{global_idx:06d}.jpg")
        cand_b = os.path.join(base_dir, f"{global_idx}.jpg")
        src = cand_a if os.path.exists(cand_a) else cand_b
        src_abs = os.path.abspath(src)
        if not os.path.exists(src_abs):
            print(f"[chunk {chunk_id}] Missing source frame; skipping {global_idx}: {src_abs}")
            skipped.append((global_idx, src_abs, "missing"))
            continue

        dst = os.path.join(chunk_dir, f"{len(local_to_global):06d}.jpg")
        copied = False
        last_error = None
        for attempt in range(1, FRAME_COPY_RETRIES + 1):
            try:
                shutil.copy2(src_abs, dst)
                copied = True
                break
            except OSError as exc:
                last_error = exc
                print(f"[chunk {chunk_id}] Copy failed frame {global_idx} attempt {attempt}/{FRAME_COPY_RETRIES}: {src_abs} ({exc})")
                time.sleep(FRAME_COPY_RETRY_DELAY_SEC)
        if not copied:
            skipped.append((global_idx, src_abs, str(last_error)))
            if os.path.exists(dst):
                try:
                    os.remove(dst)
                except OSError:
                    pass
            continue
        local_to_global.append(global_idx)
    if skipped:
        print(f"[chunk {chunk_id}] Skipped {len(skipped)} frame(s) due to copy/read errors.")
    if not local_to_global:
        raise RuntimeError(f"Chunk {chunk_id} has no readable frames after copy retries.")
    return chunk_dir, local_to_global

def resolve_image_path(dir_path, frame_idx):
    a = os.path.join(dir_path, f"{frame_idx:06d}.jpg")
    b = os.path.join(dir_path, f"{frame_idx}.jpg")
    if os.path.exists(a):
        return a
    if os.path.exists(b):
        return b
    for fn in os.listdir(dir_path):
        name, ext = os.path.splitext(fn)
        if ext.lower() in ('.jpg', '.jpeg') and name == str(frame_idx).zfill(6):
            return os.path.join(dir_path, fn)
    return a

def read_gray_image(path):
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return None
    return image


def select_seed_position(video_dir, all_indices, sample_name):
    if not AUTO_SEED_FRAME:
        return 0, None, 0.0

    scan_count = len(all_indices) if SEED_SCAN_FRAMES <= 0 else min(SEED_SCAN_FRAMES, len(all_indices))
    scan_indices = all_indices[:scan_count]
    for pos, frame_idx in enumerate(scan_indices):
        frame_path = resolve_image_path(video_dir, frame_idx)
        bbox, conf = auto_find_roi_bbox_yolo(
            frame_path,
            output_dir=None,
            frame_idx=frame_idx,
            sample_name=sample_name,
        )
        if bbox is not None:
            print(
                f"[seed] First YOLO-detectable RIA: frame {frame_idx} "
                f"({pos + 1}/{len(scan_indices)} scanned), conf={conf:.3f}"
            )
            return pos, bbox, conf
        if (pos + 1) % 25 == 0:
            print(f"[seed] Scanned {pos + 1}/{len(scan_indices)} frame(s); no RIA detection yet")

    print(f"[seed] No YOLO-detectable RIA found in {len(scan_indices)} frame(s); using first frame for manual prompt")
    return 0, None, 0.0


_ria_yolo_model = None


def get_ria_yolo_model():
    global _ria_yolo_model
    if not AUTO_ROI_YOLO:
        return None
    if _ria_yolo_model is not None:
        return _ria_yolo_model
    if not os.path.exists(YOLO_RIA_MODEL_PATH):
        print(f"[auto ROI YOLO] Model not found: {YOLO_RIA_MODEL_PATH}")
        return None
    try:
        os.environ.setdefault("YOLO_CONFIG_DIR", os.path.join(SCRIPT_DIR, "Ultralytics"))
        from ultralytics import YOLO
        _ria_yolo_model = YOLO(YOLO_RIA_MODEL_PATH)
        print(f"[auto ROI YOLO] Loaded model: {YOLO_RIA_MODEL_PATH}")
    except Exception as exc:
        print(f"[auto ROI YOLO] Could not load model; falling back to manual prompt. {exc}")
        _ria_yolo_model = None
    return _ria_yolo_model


def expand_bbox_with_padding(bbox, image_shape, padding_px, padding_fraction):
    h, w = image_shape[:2]
    x1, y1, x2, y2 = [float(v) for v in bbox]
    box_w = max(1.0, x2 - x1)
    box_h = max(1.0, y2 - y1)
    pad_x = max(float(padding_px), box_w * float(padding_fraction))
    pad_y = max(float(padding_px), box_h * float(padding_fraction))
    return np.array([
        max(0.0, x1 - pad_x),
        max(0.0, y1 - pad_y),
        min(float(w - 1), x2 + pad_x),
        min(float(h - 1), y2 + pad_y),
    ], dtype=np.float32)


def worm_mask_path(sample_name, frame_idx):
    return os.path.join(worm_seg_dir, sample_name, "masks", f"{int(frame_idx):06d}_worm_mask.png")


def load_worm_mask_for_frame(sample_name, frame_idx, image_shape):
    if not USE_WORM_MASK_TO_FILTER_RIA_YOLO or not sample_name:
        return None
    path = worm_mask_path(sample_name, frame_idx)
    if not os.path.exists(path):
        return None
    mask = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return None
    target_h, target_w = image_shape[:2]
    if mask.shape[:2] != (target_h, target_w):
        mask = cv2.resize(mask, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
    mask = (mask > 0).astype(np.uint8)
    if int(mask.sum()) < 8:
        return None
    return mask


def dilate_binary_mask(mask, radius_px):
    if mask is None or radius_px <= 0:
        return mask
    k = max(1, int(radius_px) * 2 + 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    return cv2.dilate(mask.astype(np.uint8), kernel, iterations=1)


def bbox_mask_overlap_ratios(bbox, mask, nearby_mask=None):
    if mask is None:
        return np.nan, np.nan
    h, w = mask.shape[:2]
    x1, y1, x2, y2 = [int(round(v)) for v in bbox]
    x1 = max(0, min(w - 1, x1))
    x2 = max(0, min(w, x2))
    y1 = max(0, min(h - 1, y1))
    y2 = max(0, min(h, y2))
    if x2 <= x1 or y2 <= y1:
        return 0.0, 0.0
    area = float((x2 - x1) * (y2 - y1))
    roi = mask[y1:y2, x1:x2] > 0
    inside_ratio = float(np.count_nonzero(roi) / area)
    if nearby_mask is None:
        nearby_ratio = inside_ratio
    else:
        nearby_roi = nearby_mask[y1:y2, x1:x2] > 0
        nearby_ratio = float(np.count_nonzero(nearby_roi) / area)
    return inside_ratio, nearby_ratio


def bbox_mean_intensity(image, bbox):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    h, w = gray.shape[:2]
    x1, y1, x2, y2 = [int(round(v)) for v in bbox]
    x1 = max(0, min(w - 1, x1))
    x2 = max(0, min(w, x2))
    y1 = max(0, min(h - 1, y1))
    y2 = max(0, min(h, y2))
    if x2 <= x1 or y2 <= y1:
        return 0.0
    return float(gray[y1:y2, x1:x2].mean())


def save_yolo_prompt_preview(frame_path, bbox, raw_bbox, conf, output_dir, frame_idx, worm_mask=None, score_info=None):
    if not YOLO_RIA_PREVIEW:
        return
    image = cv2.imread(frame_path)
    if image is None:
        return
    os.makedirs(output_dir, exist_ok=True)
    if worm_mask is not None:
        contours, _ = cv2.findContours((worm_mask > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(image, contours, -1, (0, 180, 255), 1)
    rx1, ry1, rx2, ry2 = [int(round(v)) for v in raw_bbox]
    x1, y1, x2, y2 = [int(round(v)) for v in bbox]
    cv2.rectangle(image, (rx1, ry1), (rx2, ry2), (255, 0, 255), 2)
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.putText(image, f"YOLO RIA {conf:.3f}", (x1, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    if score_info:
        cv2.putText(image, score_info, (x1, min(image.shape[0] - 8, y2 + 18)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
    preview_path = os.path.join(output_dir, f"auto_yolo_prompt_frame{frame_idx:06d}.jpg")
    cv2.imwrite(preview_path, image)


def auto_find_roi_bbox_yolo(frame_path, output_dir=None, frame_idx=0, sample_name=None):
    model = get_ria_yolo_model()
    if model is None:
        return None, 0.0
    image = cv2.imread(frame_path)
    if image is None:
        print(f"[auto ROI YOLO] Could not read frame: {frame_path}")
        return None, 0.0
    try:
        with open(os.devnull, "w", encoding="utf-8") as devnull, contextlib.redirect_stdout(devnull):
            results = model.predict(
                source=frame_path,
                imgsz=640,
                conf=YOLO_RIA_CONF_THRESHOLD,
                device=YOLO_RIA_DEVICE,
                verbose=False,
            )
    except Exception as exc:
        print(f"[auto ROI YOLO] Prediction failed; falling back to manual prompt. {exc}")
        return None, 0.0
    if not results or results[0].boxes is None or len(results[0].boxes) == 0:
        return None, 0.0

    h, w = image.shape[:2]
    center_x = w / 2.0
    center_y = h / 2.0
    worm_mask = load_worm_mask_for_frame(sample_name, frame_idx, image.shape)
    nearby_worm_mask = dilate_binary_mask(worm_mask, YOLO_RIA_WORM_MASK_DILATE_PX)
    best_box = None
    best_conf = -1.0
    best_raw_box = None
    best_distance = float("inf")
    best_score = -float("inf")
    best_inside_ratio = np.nan
    best_nearby_ratio = np.nan
    detections_above_threshold = 0
    detections_after_worm_filter = 0
    for box in results[0].boxes:
        conf = float(box.conf[0])
        if conf < YOLO_RIA_CONF_THRESHOLD:
            best_conf = max(best_conf, conf)
            continue
        raw_box = box.xyxy[0].detach().cpu().numpy()
        x1, y1, x2, y2 = [float(v) for v in raw_box]
        box_center_x = (x1 + x2) / 2.0
        box_center_y = (y1 + y2) / 2.0
        distance = float(np.hypot(box_center_x - center_x, box_center_y - center_y))
        detections_above_threshold += 1
        inside_ratio, nearby_ratio = bbox_mask_overlap_ratios(raw_box, worm_mask, nearby_worm_mask)
        if worm_mask is not None:
            if (
                nearby_ratio < YOLO_RIA_MIN_WORM_NEARBY_RATIO
                or inside_ratio < YOLO_RIA_MIN_WORM_INSIDE_RATIO
            ):
                continue
            detections_after_worm_filter += 1
        mean_intensity = bbox_mean_intensity(image, raw_box) / 255.0
        center_score = 1.0 / (1.0 + distance / max(1.0, min(h, w)))
        if worm_mask is None:
            score = center_score + 0.25 * conf + 0.10 * mean_intensity
        else:
            score = (
                3.0 * float(inside_ratio)
                + 1.5 * float(nearby_ratio)
                + 0.35 * conf
                + 0.15 * mean_intensity
                + 0.10 * center_score
            )
        if score > best_score:
            best_score = score
            best_distance = distance
            best_conf = conf
            best_box = raw_box
            best_raw_box = raw_box
            best_inside_ratio = inside_ratio
            best_nearby_ratio = nearby_ratio
    if best_box is None or best_conf < YOLO_RIA_CONF_THRESHOLD:
        if worm_mask is not None and detections_above_threshold > 0:
            print(
                f"[auto ROI YOLO] No detection passed worm-mask filter on frame {frame_idx}: "
                f"candidates={detections_above_threshold}, "
                f"min_inside={YOLO_RIA_MIN_WORM_INSIDE_RATIO:.2f}, "
                f"min_nearby={YOLO_RIA_MIN_WORM_NEARBY_RATIO:.2f}"
            )
        return None, best_conf
    if detections_above_threshold > 1:
        if worm_mask is None:
            print(
                f"[auto ROI YOLO] {detections_above_threshold} detections above threshold; "
                f"selected nearest to image center (distance={best_distance:.1f}, conf={best_conf:.3f})"
            )
        else:
            print(
                f"[auto ROI YOLO] {detections_above_threshold} detections above threshold, "
                f"{detections_after_worm_filter} passed worm-mask filter; "
                f"selected overlap inside={best_inside_ratio:.2f}, nearby={best_nearby_ratio:.2f}, conf={best_conf:.3f}"
            )

    padded_bbox = expand_bbox_with_padding(
        best_box,
        image.shape,
        YOLO_RIA_PADDING,
        YOLO_RIA_PADDING_FRACTION,
    )
    if output_dir is not None:
        score_info = ""
        if worm_mask is not None:
            score_info = f"worm inside={best_inside_ratio:.2f} nearby={best_nearby_ratio:.2f}"
        save_yolo_prompt_preview(frame_path, padded_bbox, best_raw_box, best_conf, output_dir, frame_idx, worm_mask, score_info)
    return padded_bbox, best_conf


def find_forward_ria_prompt(chunk_dir, local_to_global, start_local_idx, sample_name, output_dir):
    if REPROMPT_SCAN_AHEAD_FRAMES <= 0:
        end_local_idx = len(local_to_global)
    else:
        end_local_idx = min(
            len(local_to_global),
            start_local_idx + REPROMPT_SCAN_AHEAD_FRAMES + 1,
        )
    for local_idx in range(start_local_idx, end_local_idx):
        global_idx = local_to_global[local_idx]
        frame_path = os.path.join(chunk_dir, f"{local_idx:06d}.jpg")
        bbox, conf = auto_find_roi_bbox_yolo(
            frame_path,
            output_dir=output_dir,
            frame_idx=global_idx,
            sample_name=sample_name,
        )
        if bbox is not None:
            offset = local_idx - start_local_idx
            print(
                f"[auto ROI YOLO] Reliable correction found at frame {global_idx} "
                f"(+{offset} frame(s), conf={conf:.3f})"
            )
            return bbox, conf, local_idx, global_idx, frame_path

    scanned = end_local_idx - start_local_idx
    print(
        f"[auto ROI YOLO] No reliable RIA detection from current frame through "
        f"the next {max(0, scanned - 1)} frame(s)"
    )
    return None, 0.0, start_local_idx, local_to_global[start_local_idx], os.path.join(
        chunk_dir,
        f"{start_local_idx:06d}.jpg",
    )


def build_bbox_from_existing_masks(masks_for_frame, img_shape):
    bboxes = {}
    for obj_id, mask in masks_for_frame.items():
        if obj_id is None:
            continue
        if isinstance(mask, torch.Tensor):
            mask = mask.cpu().numpy()
        mask = mask.squeeze()
        if mask.ndim != 2:
            continue
        y_coords, x_coords = np.where(mask > 0.5)
        if len(x_coords) == 0 or len(y_coords) == 0:
            continue
        x1, x2 = float(np.min(x_coords)), float(np.max(x_coords))
        y1, y2 = float(np.min(y_coords)), float(np.max(y_coords))
        mask_h, mask_w = mask.shape
        img_h, img_w = img_shape[:2]
        if mask_h != img_h or mask_w != img_w:
            x1 = x1 / max(mask_w-1, 1) * (img_w-1)
            x2 = x2 / max(mask_w-1, 1) * (img_w-1)
            y1 = y1 / max(mask_h-1, 1) * (img_h-1)
            y2 = y2 / max(mask_h-1, 1) * (img_h-1)
        padding = 2
        x1 = max(0, x1-padding)
        y1 = max(0, y1-padding)
        x2 = min(img_w-1, x2+padding)
        y2 = min(img_h-1, y2+padding)
        bboxes[int(obj_id)] = np.array([x1, y1, x2, y2], dtype=np.float32)
    return bboxes

def calculate_fixed_crop_window(video_segments, original_size, crop_size, n_frames=None):
    orig_height, orig_width = original_size
    default_center = (orig_width // 2, orig_height // 2)
    known_centers = {}
    empty_masks = 0
    total_masks = 0

    for frame_num in sorted(video_segments.keys()):
        masks_for_frame = video_segments[frame_num]
        if not masks_for_frame:
            empty_masks += 1
            total_masks += 1
            continue
        mask = next(iter(masks_for_frame.values()))
        if isinstance(mask, torch.Tensor):
            mask = mask.cpu().numpy()
        mask = np.squeeze(mask)
        total_masks += 1
        y_coords, x_coords = np.where(mask > 0.5)
        if len(x_coords) > 0 and len(y_coords) > 0:
            center_x = int((x_coords.min() + x_coords.max()) // 2)
            center_y = int((y_coords.min() + y_coords.max()) // 2)
            known_centers[int(frame_num)] = (center_x, center_y)
        else:
            empty_masks += 1

    if not known_centers:
        count = n_frames if n_frames is not None else len(video_segments)
        centers = [default_center] * count
    elif n_frames is None:
        centers = [known_centers.get(frame_num, default_center) for frame_num in sorted(video_segments.keys())]
    else:
        sorted_known = sorted(known_centers)
        first_known_frame = sorted_known[0]
        first_center = known_centers[first_known_frame]
        last_center = first_center
        centers = []
        for frame_idx in range(n_frames):
            if frame_idx in known_centers:
                last_center = known_centers[frame_idx]
                centers.append(last_center)
            elif frame_idx < first_known_frame:
                centers.append(first_center)
            else:
                centers.append(last_center)

    crop_windows = []
    for center_x, center_y in centers:
        left = max(0, center_x - crop_size // 2)
        top = max(0, center_y - crop_size // 2)
        right = min(orig_width, left + crop_size)
        bottom = min(orig_height, top + crop_size)
        if right == orig_width:
            left = right - crop_size
        if bottom == orig_height:
            top = bottom - crop_size
        crop_windows.append((left, top, right, bottom))

    return crop_windows, (crop_size, crop_size), empty_masks, total_masks


def mask_centroid_and_bbox(mask):
    if isinstance(mask, torch.Tensor):
        mask = mask.cpu().numpy()
    mask = np.squeeze(mask)
    if mask.ndim != 2:
        return None
    ys, xs = np.where(mask > 0.5)
    if len(xs) == 0 or len(ys) == 0:
        return None
    return {
        "centroid_x": float(np.mean(xs)),
        "centroid_y": float(np.mean(ys)),
        "bbox_x1": int(xs.min()),
        "bbox_y1": int(ys.min()),
        "bbox_x2": int(xs.max()) + 1,
        "bbox_y2": int(ys.max()) + 1,
        "area": int(len(xs)),
    }


def crop_sam2_mask_for_frame(video_segments, frame_idx, crop_window, output_shape, object_id=1, source_shape=None):
    crop_height, crop_width = output_shape
    if frame_idx not in video_segments or object_id not in video_segments[frame_idx]:
        return np.zeros((crop_height, crop_width), dtype=np.uint8)

    mask = video_segments[frame_idx][object_id]
    if isinstance(mask, torch.Tensor):
        mask = mask.cpu().numpy()
    mask = np.squeeze(mask)
    if mask.ndim != 2:
        return np.zeros((crop_height, crop_width), dtype=np.uint8)
    mask = (mask > 0.5).astype(np.uint8)

    if source_shape is not None and mask.shape[:2] != source_shape:
        source_h, source_w = source_shape
        mask = cv2.resize(mask, (source_w, source_h), interpolation=cv2.INTER_NEAREST)

    left, top, right, bottom = crop_window
    cropped_mask = mask[top:bottom, left:right]
    if cropped_mask.shape[:2] != (crop_height, crop_width):
        cropped_mask = cv2.resize(cropped_mask, (crop_width, crop_height), interpolation=cv2.INTER_NEAREST)
    return (cropped_mask > 0).astype(np.uint8) * 255


def save_ria_head_anchor_csv(video_segments, sample_name, object_id=1):
    os.makedirs(ria_anchor_dir, exist_ok=True)
    csv_path = os.path.join(ria_anchor_dir, f"{sample_name}_ria_anchor.csv")
    fields = [
        "frame", "object_id", "centroid_x", "centroid_y",
        "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2", "area",
    ]
    rows = []
    for frame_idx in sorted(video_segments):
        masks_for_frame = video_segments[frame_idx]
        if object_id not in masks_for_frame:
            continue
        stats = mask_centroid_and_bbox(masks_for_frame[object_id])
        if stats is None:
            continue
        row = {"frame": int(frame_idx), "object_id": object_id}
        row.update(stats)
        rows.append(row)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"RIA/head anchor CSV saved to: {csv_path} ({len(rows)} frame(s))")
    return csv_path


def process_tiff_stack_fixed_crop(tiff_path, output_path, video_segments, crop_size, mask_output_path=None):
    with tifffile.TiffFile(tiff_path) as tif:
        series_shape = tif.series[0].shape
        if len(series_shape) == 2:
            n_frames = 1
            height, width = series_shape
        else:
            n_frames, height, width = series_shape[:3]

    crop_windows, (crop_height, crop_width), empty_masks, total_masks = calculate_fixed_crop_window(
        video_segments, (height, width), crop_size, n_frames=n_frames
    )
    if not crop_windows:
        print("No crop windows were generated; skipping TIFF crop save.")
        return 0, (crop_height, crop_width)
    if len(crop_windows) < n_frames:
        print(f"Warning: only {len(crop_windows)} crop windows for {n_frames} frames; reusing the last window for remaining frames.")
        crop_windows.extend([crop_windows[-1]] * (n_frames - len(crop_windows)))

    print(f"Empty masks: {empty_masks}/{total_masks}")
    print(f"Crop size: {crop_height}x{crop_width}")
    local_output_dir = os.path.join(LOCAL_TEMP_ROOT, ".crop_output")
    os.makedirs(local_output_dir, exist_ok=True)
    local_output_path = os.path.join(local_output_dir, os.path.basename(output_path))
    local_mask_output_path = None
    if mask_output_path is not None:
        local_mask_output_path = os.path.join(local_output_dir, os.path.basename(mask_output_path))

    written = 0
    with tifffile.TiffFile(tiff_path) as tif, tifffile.TiffWriter(local_output_path, bigtiff=False) as out_tif:
        mask_tif = tifffile.TiffWriter(local_mask_output_path, bigtiff=False) if local_mask_output_path else None
        if len(tif.pages) == n_frames and n_frames > 1:
            frame_iter = (page.asarray() for page in tif.pages)
        else:
            stack = tif.asarray()
            if stack.ndim == 2:
                frame_iter = iter([stack])
            else:
                frame_iter = iter(stack)

        progress = SingleLineProgress("Processing TIFF frames", n_frames)
        try:
            for idx, frame in enumerate(frame_iter):
                left, top, right, bottom = crop_windows[idx]
                cropped_frame = frame[top:bottom, left:right]
                if cropped_frame.shape[:2] != (crop_height, crop_width):
                    cropped_frame = cv2.resize(cropped_frame, (crop_width, crop_height))
                out_tif.write(cropped_frame, contiguous=True)
                if mask_tif is not None:
                    cropped_mask = crop_sam2_mask_for_frame(
                        video_segments,
                        idx,
                        crop_windows[idx],
                        (crop_height, crop_width),
                        object_id=1,
                        source_shape=(height, width),
                    )
                    mask_tif.write(cropped_mask, contiguous=True)
                written += 1
                progress.update()
        finally:
            progress.close()
            if mask_tif is not None:
                mask_tif.close()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    shutil.move(local_output_path, output_path)
    if mask_output_path is not None and local_mask_output_path is not None:
        os.makedirs(os.path.dirname(mask_output_path), exist_ok=True)
        shutil.move(local_mask_output_path, mask_output_path)
        print(f"Cropped RIA mask stack saved to: {mask_output_path}")
    print(f"Cropped TIFF stack saved to: {output_path}")
    return written, (crop_height, crop_width)


def process_jpg_frames_fixed_crop_to_tiff(video_dir, frame_names, output_path, video_segments, crop_size):
    first_frame = cv2.imread(os.path.join(video_dir, frame_names[0]), cv2.IMREAD_GRAYSCALE)
    if first_frame is None:
        print(f"Could not read first JPG frame from {video_dir}; skipping crop TIFF save.")
        return 0, (crop_size, crop_size)

    all_indices = get_sorted_frame_indices(frame_names)
    crop_windows, (crop_height, crop_width), empty_masks, total_masks = calculate_fixed_crop_window(
        video_segments,
        first_frame.shape[:2],
        crop_size,
        n_frames=len(all_indices),
    )
    if not crop_windows:
        print("No crop windows were generated; skipping JPG-to-TIFF crop save.")
        return 0, (crop_height, crop_width)

    print(f"Empty masks: {empty_masks}/{total_masks}")
    print(f"Crop size: {crop_height}x{crop_width}")
    local_output_dir = os.path.join(LOCAL_TEMP_ROOT, ".crop_output")
    os.makedirs(local_output_dir, exist_ok=True)
    local_output_path = os.path.join(local_output_dir, os.path.basename(output_path))

    with tifffile.TiffWriter(local_output_path, bigtiff=False) as tif:
        written = 0
        progress = SingleLineProgress("Processing JPG crop frames", len(all_indices))
        try:
            iterator = enumerate(all_indices)
            for idx, frame_idx in iterator:
                frame_path = resolve_image_path(video_dir, frame_idx)
                frame = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
                if frame is None:
                    progress.update()
                    continue
                left, top, right, bottom = crop_windows[idx]
                cropped_frame = frame[top:bottom, left:right]
                if cropped_frame.shape[:2] != (crop_height, crop_width):
                    cropped_frame = cv2.resize(cropped_frame, (crop_width, crop_height))
                tif.write(cropped_frame, contiguous=True)
                written += 1
                progress.update()
        finally:
            progress.close()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    shutil.move(local_output_path, output_path)
    print(f"Cropped TIFF stack saved from JPG frames to: {output_path}")
    return written, (crop_height, crop_width)


def process_frames_fixed_crop(video_dir, output_folder, video_segments, original_size, crop_size):
    frame_names = get_jpg_frame_names(video_dir)
    if not frame_names:
        print(f"No JPG frames found in {video_dir}; skipping JPG crop sequence.")
        return 0, (crop_size, crop_size)

    all_indices = get_sorted_frame_indices(frame_names)
    crop_windows, (crop_height, crop_width), empty_masks, total_masks = calculate_fixed_crop_window(
        video_segments,
        original_size,
        crop_size,
        n_frames=len(all_indices),
    )
    if not crop_windows:
        print("No crop windows were generated; skipping JPG crop sequence.")
        return 0, (crop_height, crop_width)
    if len(crop_windows) < len(all_indices):
        crop_windows.extend([crop_windows[-1]] * (len(all_indices) - len(crop_windows)))

    print(f"Empty masks for JPG crop sequence: {empty_masks}/{total_masks}")
    print(f"JPG crop size: {crop_height}x{crop_width}")

    local_output_root = os.path.join(LOCAL_TEMP_ROOT, ".jpg_crop_output")
    local_output_folder = os.path.join(local_output_root, os.path.basename(output_folder))
    if os.path.exists(local_output_folder):
        if not safe_rmtree(local_output_folder, "local JPG crop output folder"):
            local_output_folder = os.path.join(local_output_root, f"{os.path.basename(output_folder)}_{int(time.time() * 1000)}")
    os.makedirs(local_output_folder, exist_ok=True)

    written = 0
    progress = SingleLineProgress("Saving JPG crop frames", len(all_indices))
    try:
        for idx, frame_idx in enumerate(all_indices):
            frame_path = resolve_image_path(video_dir, frame_idx)
            frame = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
            if frame is None:
                progress.update()
                continue
            left, top, right, bottom = crop_windows[idx]
            cropped_frame = frame[top:bottom, left:right]
            if cropped_frame.shape[:2] != (crop_height, crop_width):
                cropped_frame = cv2.resize(cropped_frame, (crop_width, crop_height))
            out_path = os.path.join(local_output_folder, f"{frame_idx:06d}.jpg")
            if not cv2.imwrite(out_path, cropped_frame, [cv2.IMWRITE_JPEG_QUALITY, 100]):
                raise OSError(f"Could not write JPG crop frame: {out_path}")
            written += 1
            progress.update()

        os.makedirs(os.path.dirname(output_folder), exist_ok=True)
        if os.path.exists(output_folder):
            safe_rmtree(output_folder, "existing JPG crop output folder")
        shutil.move(local_output_folder, output_folder)
    finally:
        progress.close()
        if os.path.isdir(local_output_folder):
            safe_rmtree(local_output_folder, "local JPG crop output folder")

    return written, (crop_height, crop_width)


def mask_area(mask):
    if isinstance(mask, torch.Tensor):
        mask = mask.cpu().numpy()
    mask = np.squeeze(mask)
    if mask.ndim != 2:
        return 0
    return int(np.count_nonzero(mask > 0.5))


def recent_mask_area_median(video_segments, frame_idx, object_id=1, history_frames=RIA_MASK_AREA_HISTORY_FRAMES):
    areas = []
    start = max(0, int(frame_idx) - int(history_frames))
    for idx in range(start, int(frame_idx)):
        masks_for_frame = video_segments.get(idx)
        if not masks_for_frame or object_id not in masks_for_frame:
            continue
        area = mask_area(masks_for_frame[object_id])
        if area >= MIN_RIA_MASK_AREA:
            areas.append(area)
    if not areas:
        return None
    return float(np.median(areas))


def check_mask_quality(video_segments, frame_idx, confidence_scores=None):
    quality_report = {"frame": frame_idx, "issues": []}
    needs_reprompt = False
    if frame_idx not in video_segments or not video_segments[frame_idx]:
        quality_report["issues"].append("No masks found")
        return True, quality_report
    masks_for_frame = video_segments[frame_idx]
    if 1 not in masks_for_frame:
        quality_report["issues"].append("RIA object 1 missing")
        return True, quality_report
    current_area = mask_area(masks_for_frame[1])
    recent_median = recent_mask_area_median(video_segments, frame_idx, object_id=1)
    dynamic_min_area = MIN_RIA_MASK_AREA
    if recent_median is not None:
        dynamic_min_area = max(
            MIN_RIA_MASK_AREA,
            int(round(recent_median * MIN_RIA_MASK_AREA_FRACTION_OF_RECENT_MEDIAN)),
        )
    quality_report["mask_area"] = current_area
    quality_report["recent_median_area"] = recent_median
    quality_report["min_mask_area"] = dynamic_min_area
    # Keep mask area diagnostics in the report, but do not reprompt only because
    # the RIA mask is small. Some valid frames contain only a compact soma-like
    # signal, and automatic reprompting here can interrupt otherwise good runs.
    low_confidence = []
    if confidence_scores:
        for obj_id, confidence in confidence_scores.items():
            if confidence < CONFIDENCE_THRESHOLD:
                low_confidence.append(obj_id)
                needs_reprompt = True
    if low_confidence:
        quality_report["issues"].append(f"Low confidence (< {CONFIDENCE_THRESHOLD}): {low_confidence}")
    quality_report["status"] = "needs_reprompt" if needs_reprompt else "good"
    return needs_reprompt, quality_report

def safe_name(value):
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)


def prepare_training_export_dir():
    root = os.path.join(SCRIPT_DIR, TRAINING_DATA_SUBDIR)
    for subdir in ("images", "masks", "labels_yolo", "overlays"):
        os.makedirs(os.path.join(root, subdir), exist_ok=True)
    return root


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


def yolo_label_from_bbox(bbox, image_shape, class_id=0):
    h, w = image_shape[:2]
    x1, y1, x2, y2 = bbox
    x_center = ((x1 + x2) / 2) / w
    y_center = ((y1 + y2) / 2) / h
    box_w = (x2 - x1) / w
    box_h = (y2 - y1) / h
    return f"{class_id} {x_center:.6f} {y_center:.6f} {box_w:.6f} {box_h:.6f}\n"


def export_training_sample(video_dir, frame_idx, masks_for_frame, sample_prefix, first_frame_idx=0):
    if not EXPORT_TRAINING_DATA:
        return
    if (frame_idx - first_frame_idx) % TRAIN_EXPORT_INTERVAL != 0:
        return
    if not masks_for_frame:
        return

    frame_path = resolve_image_path(video_dir, frame_idx)
    image = cv2.imread(frame_path)
    if image is None:
        print(f"[train export] Could not read frame {frame_path}")
        return

    obj_id = sorted(masks_for_frame.keys())[0]
    bbox, mask = mask_to_bbox(masks_for_frame[obj_id])
    if bbox is None:
        return

    export_root = prepare_training_export_dir()
    sample_name = f"{safe_name(sample_prefix)}_{frame_idx:06d}"
    image_out = os.path.join(export_root, "images", sample_name + ".jpg")
    mask_out = os.path.join(export_root, "masks", sample_name + "_mask.png")
    label_out = os.path.join(export_root, "labels_yolo", sample_name + ".txt")
    overlay_out = os.path.join(export_root, "overlays", sample_name + ".jpg")

    shutil.copy2(frame_path, image_out)
    cv2.imwrite(mask_out, (mask.astype(np.uint8) * 255))
    with open(label_out, "w", encoding="utf-8") as f:
        f.write(yolo_label_from_bbox(bbox, image.shape))

    overlay = image.copy()
    color = np.zeros_like(overlay)
    color[:, :, 1] = 255
    overlay = np.where(mask[:, :, None], cv2.addWeighted(overlay, 0.55, color, 0.45, 0), overlay)
    x1, y1, x2, y2 = bbox
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 255), 1)
    cv2.imwrite(overlay_out, overlay)


def overlay_predictions_on_frame(video_dir, frame_idx, video_segments, alpha=0.6):
    COLORS = {1: (255, 0, 0), 2: (0, 0, 255), 3: (0, 255, 0)}
    frame_path = os.path.join(video_dir, f"{frame_idx:06d}.jpg")
    if not os.path.exists(frame_path):
        frame_names = sorted([f for f in os.listdir(video_dir) if f.endswith('.jpg')])
        if frame_idx < len(frame_names):
            frame_path = os.path.join(video_dir, frame_names[frame_idx])
        else:
            print(f"Frame {frame_idx} not found")
            return
    image = cv2.imread(frame_path)
    if image is None:
        print(f"Could not read image from {frame_path}")
        return
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    overlay = np.zeros_like(image)
    if frame_idx in video_segments:
        for mask_id, mask in video_segments[frame_idx].items():
            if isinstance(mask, torch.Tensor):
                mask = mask.cpu().numpy()
            if mask.dtype != bool:
                mask = mask > 0.5
            if mask.ndim > 2:
                mask = mask.squeeze()
            mask_resized = cv2.resize(mask.astype(np.uint8), (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
            colored_mask = np.zeros_like(image)
            colored_mask[mask_resized == 1] = COLORS.get(mask_id, (128, 128, 128))
            overlay = cv2.addWeighted(overlay, 1, colored_mask, 1, 0)
        overlaid_image = cv2.addWeighted(image, 1, overlay, alpha, 0)
    else:
        print(f"No predictions found for frame {frame_idx}")
        overlaid_image = image
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(overlaid_image)
    ax.set_title(f"Frame {frame_idx:06d} - RIA Region Tracking")
    ax.set_axis_off()
    if frame_idx in video_segments:
        legend_text = [f"{mid}: RIA Region" for mid in sorted(video_segments[frame_idx].keys())]
        if legend_text:
            ax.text(0.02, 0.98, '\n'.join(legend_text), transform=ax.transAxes,
                    va='top', ha='left', color='white', fontsize=10,
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none'))
    plt.tight_layout()
    plt.show(block=False)
    plt.pause(2)
    plt.close(fig)
    cv2.imwrite("frame_prediction_overlay.png", cv2.cvtColor(overlaid_image, cv2.COLOR_RGB2BGR))
    print(f"Overlaid image saved to frame_prediction_overlay.png")

def load_valid_frame_set(sample_name):
    csv_path = os.path.join(worm_seg_dir, sample_name, "frame_validity.csv")
    if not os.path.exists(csv_path):
        print(f"[worm validity] No frame_validity.csv found for {sample_name}; processing all frames.")
        return None

    valid_frames = set()
    invalid_count = 0
    touch_border_count = 0
    included_touch_border_count = 0
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            frame = int(row["frame"])
            is_valid = str(row.get("valid", "")).lower() in ("true", "1", "yes")
            is_touch_border = (
                str(row.get("touches_border", "")).lower() in ("true", "1", "yes")
                or str(row.get("reason", "")).lower() == "touches_border"
            )
            if is_touch_border:
                touch_border_count += 1
            if is_valid or (INCLUDE_TOUCH_BORDER_FRAMES and is_touch_border):
                valid_frames.add(frame)
                if not is_valid and is_touch_border:
                    included_touch_border_count += 1
            else:
                invalid_count += 1
    print(
        f"[worm validity] {sample_name}: valid frames={len(valid_frames)}, "
        f"skipped frames={invalid_count}, touch_border={touch_border_count}, "
        f"included_touch_border={included_touch_border_count}"
    )
    return valid_frames


def filter_indices_by_worm_validity(all_indices, valid_frames, sample_name):
    if valid_frames is None:
        return all_indices
    filtered = [idx for idx in all_indices if idx in valid_frames]
    skipped = len(all_indices) - len(filtered)
    print(f"[worm validity] {sample_name}: keeping {len(filtered)}/{len(all_indices)} frame(s), skipping {skipped}")
    return filtered


# ---------------------------------------------------------------------------
# Main: collect all unprocessed inputs
# ---------------------------------------------------------------------------

# [CHANGED] Use tiff_stack_dir instead of tiff_dir; skip already-cropped files.
unprocessed_tiffs = get_all_unprocessed_tiff_stacks(tiff_stack_dir, crop_dir)
unprocessed_videos = get_all_unprocessed_videos(parent_video_dir, crop_dir) if PROCESS_JPG_VIDEOS else []

all_inputs = [(path, "tiff") for path in unprocessed_tiffs]
if PROCESS_JPG_VIDEOS:
    all_inputs.extend((path, "video") for path in unprocessed_videos)

if not all_inputs:
    print("All files have been processed.")
    exit()

# [NEW] Print overall numbered queue across both input types.
print(f"\nTotal files queued for processing: {len(all_inputs)}")
for idx, (path, itype) in enumerate(all_inputs, 1):
    print(f"  [{idx}/{len(all_inputs)}] ({itype}) {os.path.basename(path)}")
print()

for file_idx, (input_path, input_type) in enumerate(all_inputs, 1):
    print(f"\n{'='*60}")
    # [CHANGED] Added [i/n] numbering to the per-file header.
    print(f"[{file_idx}/{len(all_inputs)}] Processing {input_type}: {input_path}")
    print(f"{'='*60}")

    temp_dir = None
    tiff_stack = None
    if input_type == 'tiff':
        stack_name = os.path.splitext(os.path.basename(input_path))[0]
        cached_jpg_dir = os.path.join(parent_video_dir, stack_name)
        cached_frame_names = get_jpg_frame_names(cached_jpg_dir) if REUSE_EXISTING_JPG_FRAMES else []

        if cached_frame_names:
            random_video_dir = cached_jpg_dir
            frame_names = cached_frame_names
            print(f"Using existing JPG frames: {cached_jpg_dir} ({len(frame_names)} frame(s))")
        else:
            tiff_stack = load_tiff_stack(input_path)
            temp_dir = os.path.join(LOCAL_TEMP_ROOT, ".temp_frames", stack_name)
            frame_names = tiff_stack_to_temp_jpgs(tiff_stack, temp_dir)
            random_video_dir = temp_dir
            print(f"Generated temporary JPG frames: {temp_dir} ({len(frame_names)} frame(s))")
    else:
        random_video_dir = input_path
        frame_names = get_jpg_frame_names(random_video_dir)

    all_indices = get_sorted_frame_indices(frame_names)
    if not all_indices:
        print(f"No readable JPG frames found for {input_path}. Skipping this file.")
        continue

    sample_prefix = os.path.splitext(os.path.basename(input_path))[0]
    valid_frames = load_valid_frame_set(sample_prefix)
    all_indices = filter_indices_by_worm_validity(all_indices, valid_frames, sample_prefix)
    if not all_indices:
        print(f"No worm-valid frames found for {sample_prefix}. Skipping this file.")
        continue
    seed_start_pos, detected_seed_bbox, detected_seed_conf = select_seed_position(
        random_video_dir,
        all_indices,
        sample_prefix,
    )
    video_segments = {}

    chunk_root = os.path.join(LOCAL_TEMP_ROOT, ".tmp_chunks", sample_prefix)
    if os.path.exists(chunk_root):
        if not safe_rmtree(chunk_root, "chunk root directory"):
            chunk_root = os.path.join(LOCAL_TEMP_ROOT, ".tmp_chunks", f"{sample_prefix}_{int(time.time() * 1000)}")
    os.makedirs(chunk_root, exist_ok=True)

    i = seed_start_pos
    chunk_id = 0
    first_frame_idx = all_indices[seed_start_pos] if all_indices else 0

    while i < len(all_indices):
        end_idx_exclusive = min(i + CHUNK_SIZE, len(all_indices))
        start_i = i if chunk_id == 0 else max(i - OVERLAP, 0)
        indices = all_indices[start_i:end_idx_exclusive]
        chunk_id += 1
        chunk_dir, local_to_global = create_chunk_dir(random_video_dir, indices, chunk_root, chunk_id)

        inference_state = predictor.init_state(video_path=chunk_dir)
        chunk_has_seed = False

        seed_local_idx  = 0
        seed_global_idx = local_to_global[seed_local_idx]
        seed_frame_path = os.path.join(chunk_dir, f"{seed_local_idx:06d}.jpg")
        print(f"\n--- Chunk {chunk_id} start (global frame {seed_global_idx}) ---")

        if chunk_id == 1:
            bbox = detected_seed_bbox
            if bbox is not None:
                yolo_score = detected_seed_conf
                seed_preview_image = cv2.imread(seed_frame_path)
                if seed_preview_image is not None:
                    save_yolo_prompt_preview(
                        seed_frame_path,
                        bbox,
                        bbox,
                        yolo_score,
                        os.path.join(crop_dir, "auto_yolo_prompt_previews"),
                        seed_global_idx,
                        load_worm_mask_for_frame(sample_prefix, seed_global_idx, seed_preview_image.shape),
                        "first detector-positive seed frame",
                    )
                print(f"[auto ROI YOLO] Using scanned detector prompt on frame {seed_global_idx}: conf={yolo_score:.3f}, padded_box={bbox.tolist()}")
            elif AUTO_ROI_YOLO:
                bbox, yolo_score = auto_find_roi_bbox_yolo(
                    seed_frame_path,
                    output_dir=os.path.join(crop_dir, "auto_yolo_prompt_previews"),
                    frame_idx=seed_global_idx,
                    sample_name=sample_prefix,
                )
                if bbox is not None:
                    print(f"[auto ROI YOLO] Using detector prompt on frame {seed_global_idx}: conf={yolo_score:.3f}, padded_box={bbox.tolist()}")
                else:
                    print(f"[auto ROI YOLO] No confident detection on frame {seed_global_idx}; best/threshold={yolo_score:.3f}/{YOLO_RIA_CONF_THRESHOLD:.3f}")

            if bbox is None:
                if not ALLOW_MANUAL_PROMPT:
                    print("[auto ROI YOLO] No reliable RIA seed found; manual prompt disabled. Skipping this file.")
                    break
                print("\nDraw a bounding box around the RIA region.")
                print("- Number key 1 = select RIA object")
                print("- Click and drag = draw bounding box")
                print("- u = undo last box  |  c = clear all  |  enter/q = finish")
                user_bboxes = interactive_collect_bboxes(seed_frame_path, object_ids=(1,))
                if not user_bboxes or 1 not in user_bboxes:
                    print("No bounding box provided for RIA region. Skipping this file...")
                    break
                bbox = user_bboxes[1]

            _, out_obj_ids, out_mask_logits = predictor.add_new_points_or_box(
                inference_state=inference_state,
                frame_idx=seed_local_idx,
                obj_id=1,
                box=bbox,
            )
            chunk_has_seed = True

            plt.figure(figsize=(12, 8))
            plt.imshow(Image.open(seed_frame_path))
            x1, y1, x2, y2 = bbox
            rect = plt.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=2, edgecolor='red', facecolor='none')
            plt.gca().add_patch(rect)
            for k, out_obj_id in enumerate(out_obj_ids):
                show_mask((out_mask_logits[k] > 0.0).cpu().numpy(), plt.gca(), obj_id=out_obj_id)
            plt.savefig("ria_prompt.png")
            plt.close()
        else:
            if seed_global_idx in video_segments:
                prev_masks = video_segments[seed_global_idx]
                img_path   = resolve_image_path(chunk_dir, seed_local_idx)
                img        = cv2.imread(img_path)
                img_shape  = img.shape if img is not None else (RIA_CROP_SIZE, RIA_CROP_SIZE, 3)
                auto_bboxes = build_bbox_from_existing_masks(prev_masks, img_shape)
                if auto_bboxes:
                    for obj_id, bbox in sorted(auto_bboxes.items()):
                        print(f"[chunk {chunk_id}] Auto-seeding obj {obj_id} with bbox from previous masks")
                        predictor.add_new_points_or_box(
                            inference_state=inference_state,
                            frame_idx=seed_local_idx,
                            obj_id=int(obj_id),
                            box=bbox,
                        )
                        chunk_has_seed = True
                else:
                    print(f"[chunk {chunk_id}] No bboxes from previous masks; searching forward for RIA")
                    (
                        forward_bbox,
                        forward_score,
                        forward_local_idx,
                        forward_global_idx,
                        forward_frame_path,
                    ) = find_forward_ria_prompt(
                        chunk_dir,
                        local_to_global,
                        seed_local_idx,
                        sample_prefix,
                        output_dir=os.path.join(crop_dir, "auto_yolo_chunk_seed_previews"),
                    )
                    if forward_bbox is not None:
                        seed_local_idx = forward_local_idx
                        seed_global_idx = forward_global_idx
                        seed_frame_path = forward_frame_path
                        predictor.add_new_points_or_box(
                            inference_state=inference_state,
                            frame_idx=seed_local_idx,
                            obj_id=1,
                            box=forward_bbox,
                        )
                        chunk_has_seed = True
                        print(
                            f"[chunk {chunk_id}] YOLO-seeded at frame {seed_global_idx}: "
                            f"conf={forward_score:.3f}"
                        )
                    else:
                        print(f"[chunk {chunk_id}] No reliable RIA found through chunk end; proceeding without seeding")
            else:
                print(f"[chunk {chunk_id}] No previous masks to auto-seed; searching forward for RIA")
                (
                    forward_bbox,
                    forward_score,
                    forward_local_idx,
                    forward_global_idx,
                    forward_frame_path,
                ) = find_forward_ria_prompt(
                    chunk_dir,
                    local_to_global,
                    seed_local_idx,
                    sample_prefix,
                    output_dir=os.path.join(crop_dir, "auto_yolo_chunk_seed_previews"),
                )
                if forward_bbox is not None:
                    seed_local_idx = forward_local_idx
                    seed_global_idx = forward_global_idx
                    seed_frame_path = forward_frame_path
                    predictor.add_new_points_or_box(
                        inference_state=inference_state,
                        frame_idx=seed_local_idx,
                        obj_id=1,
                        box=forward_bbox,
                    )
                    chunk_has_seed = True
                    print(
                        f"[chunk {chunk_id}] YOLO-seeded at frame {seed_global_idx}: "
                        f"conf={forward_score:.3f}"
                    )
                else:
                    print(f"[chunk {chunk_id}] No reliable RIA found through chunk end; proceeding without seeding")

        if not chunk_has_seed:
            print(f"[chunk {chunk_id}] Skipping chunk: no RIA seed available for SAM2 propagation")
            i = end_idx_exclusive
            continue

        last_quality_check = seed_global_idx

        with open(os.devnull, "w", encoding="utf-8") as devnull, contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            propagation = predictor.propagate_in_video(
                inference_state,
                start_frame_idx=seed_local_idx,
                reverse=False,
            )
            for out_local_idx, out_obj_ids, out_mask_logits in propagation:
                global_idx = local_to_global[out_local_idx]
                if chunk_id > 1 and out_local_idx == 0 and global_idx in video_segments:
                    continue

                video_segments[global_idx] = {
                    out_obj_id: (out_mask_logits[k] > 0.0).cpu().numpy()
                    for k, out_obj_id in enumerate(out_obj_ids)
                }
                export_training_sample(random_video_dir, global_idx, video_segments[global_idx], sample_prefix, first_frame_idx)

                confidence_scores = {}
                for k, out_obj_id in enumerate(out_obj_ids):
                    if isinstance(out_mask_logits[k], torch.Tensor):
                        probs = torch.sigmoid(out_mask_logits[k])
                        positive_mask = out_mask_logits[k] > 0.0
                        confidence_scores[out_obj_id] = torch.mean(probs[positive_mask]).item() \
                            if torch.sum(positive_mask) > 0 else 0.0

                if (global_idx - last_quality_check) >= QUALITY_CHECK_INTERVAL:
                    needs_reprompt, quality_report = check_mask_quality(video_segments, global_idx, confidence_scores)
                    if needs_reprompt:
                        print(f"\n!!! Quality check failed at frame {global_idx} !!!")
                        print(f"Issues: {', '.join(quality_report['issues'])}")
                        current_frame_path = os.path.join(chunk_dir, f"{out_local_idx:06d}.jpg")
                        correction_bbox = None
                        correction_local_idx = out_local_idx
                        correction_global_idx = global_idx
                        correction_frame_path = current_frame_path
                        if AUTO_ROI_YOLO:
                            (
                                correction_bbox,
                                yolo_score,
                                correction_local_idx,
                                correction_global_idx,
                                correction_frame_path,
                            ) = find_forward_ria_prompt(
                                chunk_dir,
                                local_to_global,
                                out_local_idx,
                                sample_prefix,
                                output_dir=os.path.join(crop_dir, "auto_yolo_reprompt_previews"),
                            )

                        if correction_bbox is None and ALLOW_MANUAL_PROMPT:
                            new_bboxes = interactive_collect_bboxes(correction_frame_path, object_ids=(1,))
                            if new_bboxes and 1 in new_bboxes:
                                correction_bbox = new_bboxes[1]

                        if correction_bbox is not None:
                            predictor.add_new_points_or_box(
                                inference_state=inference_state,
                                frame_idx=correction_local_idx,
                                obj_id=1,
                                box=correction_bbox,
                            )
                            print(f"Correction bbox added at frame {correction_global_idx}. Continuing propagation...")
                        else:
                            print("No new bbox provided. Continuing with current tracking...")
                        last_quality_check = global_idx
                    else:
                        print(f"[quality] Frame {global_idx}: {quality_report['status']}")
                        last_quality_check = global_idx

                if ((global_idx - first_frame_idx) % VIS_INTERVAL) == 0:
                    try:
                        overlay_predictions_on_frame(random_video_dir, global_idx, video_segments, alpha=0.6)
                        print(f"[viz] Overlay saved for frame {global_idx:06d}")
                        if confidence_scores:
                            conf_str = ", ".join([f"obj{oid}:{conf:.2f}" for oid, conf in confidence_scores.items()])
                            print(f"[confidence] {conf_str}")
                    except Exception as e:
                        print(f"[viz] Failed for frame {global_idx}: {e}")

        i = end_idx_exclusive

    try:
        safe_rmtree(chunk_root, "chunk root directory")
    except Exception:
        pass

    if video_segments:
        os.makedirs(crop_dir, exist_ok=True)
        save_ria_head_anchor_csv(video_segments, sample_prefix, object_id=1)
        if input_type == 'tiff':
            os.makedirs(ria_mask_dir, exist_ok=True)
            output_path = os.path.join(crop_dir, os.path.splitext(os.path.basename(input_path))[0] + "_crop.tif")
            mask_output_path = os.path.join(ria_mask_dir, os.path.splitext(os.path.basename(input_path))[0] + "_ria_mask.tif")
            process_tiff_stack_fixed_crop(input_path, output_path, video_segments, RIA_CROP_SIZE, mask_output_path)

            # [NEW] Optionally save cropped JPG sequence to the dedicated visualization folder.
            if SAVE_JPG_CROP:
                os.makedirs(jpg_crop_dir, exist_ok=True)
                jpg_output_folder = os.path.join(jpg_crop_dir,
                                                 os.path.splitext(os.path.basename(input_path))[0] + "_crop_jpg")
                first_frame = cv2.imread(os.path.join(random_video_dir, frame_names[0]))
                original_size_vid = first_frame.shape[:2]
                process_frames_fixed_crop(random_video_dir, jpg_output_folder, video_segments, original_size_vid, RIA_CROP_SIZE)
                print(f"JPG crop sequence saved to: {jpg_output_folder}")

            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            if SAVE_JPG_CROP:
                os.makedirs(jpg_crop_dir, exist_ok=True)
                output_folder = os.path.join(jpg_crop_dir, os.path.basename(random_video_dir) + "_crop_jpg")
                first_frame = cv2.imread(os.path.join(random_video_dir, frame_names[0]))
                original_size = first_frame.shape[:2]
                process_frames_fixed_crop(random_video_dir, output_folder, video_segments, original_size, RIA_CROP_SIZE)
                print(f"JPG crop sequence saved to: {output_folder}")

    # [CHANGED] Added [i/n] numbering to the completion message.
    print(f"\n[{file_idx}/{len(all_inputs)}] Completed: {os.path.basename(input_path)}")

print(f"\nAll {len(all_inputs)} files processed successfully!")
