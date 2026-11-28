"""
Build per-stack template banks, cluster those local templates into one global
bank for a RUN_ID, manually label and align the global templates once, then
apply the two-level transform chain back to each stack separately.

Scale is used only while comparing templates in the manual GUI. It is saved to
CSV but is intentionally not applied to the final crop TIFF.
"""
import csv
import ctypes
import os
import pickle
import random
import runpy
import sys
from concurrent.futures import ThreadPoolExecutor

import cv2
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.widgets import Button, RadioButtons, Slider
import numpy as np
import tifffile
from tqdm import tqdm


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_SCRIPT = os.path.join(SCRIPT_DIR, "7AlignRIA_TemplateBankManual.py")
base = runpy.run_path(BASE_SCRIPT, run_name="__not_main__")

RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260529"
CROP_SUBDIR = "04_ria_crop"
JPG_CROP_SUBDIR = "06_crop_jpg"
HEAD_ANGLE_SUBDIR = "05_worm_head_angle"
OUTPUT_SUBDIR = "07_ria_template_bank_all_aligned"

LOCAL_TEMPLATE_MATCH_THRESHOLD = 0.95
GLOBAL_TEMPLATE_MATCH_THRESHOLD = 0.95
LOCAL_TEMPLATE_FRAME_COVERAGE = 0.95
GLOBAL_TEMPLATE_FRAME_COVERAGE = 0.95
MATCH_WORKERS = min(16, max(1, (os.cpu_count() or 4) - 2))
RANDOM_SEED = 1573
PREVIEW_TILE_COUNT = 25
RESUME_FROM_CHECKPOINT = True
SKIP_COMPLETED_OUTPUTS = True
CHECKPOINT_VERSION = 6
HEAD_ANGLE_REQUIRED_STATUS = "ok"
REMOVE_SOMA_FOR_MATCHING = False
REDRAW_MATCH_ROI = False
ENABLE_GAMEPAD = True
GAMEPAD_DEADZONE = 0.18
GAMEPAD_ROTATION_STEP_DEG = 2.0
GAMEPAD_TRANSLATION_STEP_PX = 0.7
GAMEPAD_SCALE_STEP = 0.003
OVERLAY_REFERENCE_GAIN = 0.35
OVERLAY_CURRENT_GAIN = 1.0

LOOP_LABELS = ("loop_left", "loop_right")
STATE_LABELS = (
    "normal",
    "blur",
    "no_ria_visible",
    "slight_z_rotation",
    "z_rotation_ring_visible",
    "nrd_nrv_substructure_activity",
)

XINPUT_GAMEPAD_DPAD_UP = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT = 0x0008
XINPUT_GAMEPAD_BACK = 0x0020
XINPUT_GAMEPAD_LEFT_SHOULDER = 0x0100
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200
XINPUT_GAMEPAD_A = 0x1000
XINPUT_GAMEPAD_B = 0x2000
XINPUT_GAMEPAD_X = 0x4000
XINPUT_GAMEPAD_Y = 0x8000


class XInputGamepad(ctypes.Structure):
    _fields_ = [
        ("buttons", ctypes.c_ushort),
        ("left_trigger", ctypes.c_ubyte),
        ("right_trigger", ctypes.c_ubyte),
        ("thumb_lx", ctypes.c_short),
        ("thumb_ly", ctypes.c_short),
        ("thumb_rx", ctypes.c_short),
        ("thumb_ry", ctypes.c_short),
    ]


class XInputState(ctypes.Structure):
    _fields_ = [("packet_number", ctypes.c_ulong), ("gamepad", XInputGamepad)]


def load_xinput():
    if not ENABLE_GAMEPAD or os.name != "nt":
        return None
    for dll_name in ("xinput1_4", "xinput1_3", "xinput9_1_0"):
        try:
            dll = ctypes.WinDLL(dll_name)
            dll.XInputGetState.argtypes = [ctypes.c_ulong, ctypes.POINTER(XInputState)]
            dll.XInputGetState.restype = ctypes.c_ulong
            return dll
        except OSError:
            continue
    return None


XINPUT = load_xinput()


def normalized_stick(value):
    value = float(value) / (32767.0 if value >= 0 else 32768.0)
    if abs(value) < GAMEPAD_DEADZONE:
        return 0.0
    return np.sign(value) * (abs(value) - GAMEPAD_DEADZONE) / (1.0 - GAMEPAD_DEADZONE)


def read_gamepad(controller_index=0):
    if XINPUT is None:
        return None
    state = XInputState()
    if XINPUT.XInputGetState(controller_index, ctypes.byref(state)) != 0:
        return None
    gamepad = state.gamepad
    return {
        "buttons": int(gamepad.buttons),
        "lx": normalized_stick(gamepad.thumb_lx),
        "ly": normalized_stick(gamepad.thumb_ly),
        "rx": normalized_stick(gamepad.thumb_rx),
        "ry": normalized_stick(gamepad.thumb_ry),
    }

crop_dir = os.path.join(RESULTS_ROOT, RUN_ID, CROP_SUBDIR)
jpg_crop_dir = os.path.join(RESULTS_ROOT, RUN_ID, JPG_CROP_SUBDIR)
head_angle_dir = os.path.join(RESULTS_ROOT, RUN_ID, HEAD_ANGLE_SUBDIR)
out_dir = os.path.join(RESULTS_ROOT, RUN_ID, OUTPUT_SUBDIR)
preview_dir = os.path.join(out_dir, "previews")
checkpoint_dir = os.path.join(out_dir, "checkpoints")

ensure_gray = base["ensure_gray"]
normalize_uint8 = base["normalize_uint8"]
prepare_match_image = base["prepare_match_image"]
ecc_match_to_template = base["ecc_match_to_template"]
identity_warp = base["identity_warp"]
warp_rotation_deg = base["warp_rotation_deg"]
warp_values = base["warp_values"]
warp_from_row = base["warp_from_row"]
warp_frame = base["warp_frame"]
full_crop_ncc = base["roi_ncc"]
write_csv = base["write_csv"]
make_preview = base["make_preview"]

# Each ECC task gets its own Python worker. Prevent OpenCV from creating another
# full CPU-sized thread pool inside every worker.
cv2.setNumThreads(1)
prepare_match_image.__globals__["REMOVE_SOMA_FOR_MATCHING"] = REMOVE_SOMA_FOR_MATCHING


def checkpoint_signature(stack_info=None):
    signature = {
        "run_id": RUN_ID,
        "local_threshold": LOCAL_TEMPLATE_MATCH_THRESHOLD,
        "global_threshold": GLOBAL_TEMPLATE_MATCH_THRESHOLD,
        "local_template_frame_coverage": LOCAL_TEMPLATE_FRAME_COVERAGE,
        "global_template_frame_coverage": GLOBAL_TEMPLATE_FRAME_COVERAGE,
        "random_seed": RANDOM_SEED,
        "checkpoint_version": CHECKPOINT_VERSION,
        "head_angle_required_status": HEAD_ANGLE_REQUIRED_STATUS,
        "remove_soma_for_matching": REMOVE_SOMA_FOR_MATCHING,
    }
    if stack_info is not None:
        signature["stacks"] = [
            (name, int(info["n_frames"]), tuple(info["source_shape"]))
            for name, info in sorted(stack_info.items())
        ]
        signature["head_angle_statuses"] = [
            (name, tuple(sorted(info["head_angle_status_by_frame"].items())))
            for name, info in sorted(stack_info.items())
        ]
    return signature


def save_checkpoint(name, payload, stack_info=None):
    os.makedirs(checkpoint_dir, exist_ok=True)
    path = os.path.join(checkpoint_dir, name)
    temp_path = f"{path}.tmp"
    wrapper = {
        "signature": checkpoint_signature(stack_info),
        "payload": payload,
    }
    with open(temp_path, "wb") as f:
        pickle.dump(wrapper, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(temp_path, path)
    return path


def load_checkpoint(name, stack_info=None):
    if not RESUME_FROM_CHECKPOINT:
        return None
    path = os.path.join(checkpoint_dir, name)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "rb") as f:
            wrapper = pickle.load(f)
        saved_signature = dict(wrapper.get("signature", {}))
        current_signature = checkpoint_signature(stack_info)
        # Checkpoints created before local/global thresholds were separated
        # stored the shared value as "threshold".
        old_threshold = saved_signature.pop("threshold", None)
        if old_threshold is not None:
            saved_signature["local_threshold"] = old_threshold
            saved_signature["global_threshold"] = old_threshold
        if name == "local_banks.pkl":
            saved_signature.pop("global_threshold", None)
            current_signature.pop("global_threshold", None)
            saved_signature.pop("global_template_frame_coverage", None)
            current_signature.pop("global_template_frame_coverage", None)
        if name == "match_roi.pkl":
            for key in (
                "local_threshold",
                "global_threshold",
                "local_template_frame_coverage",
                "global_template_frame_coverage",
                "random_seed",
                "checkpoint_version",
            ):
                saved_signature.pop(key, None)
                current_signature.pop(key, None)
        if saved_signature != current_signature:
            print(f"[checkpoint] incompatible, rebuilding: {path}")
            return None
        print(f"[checkpoint] resumed: {path}")
        return wrapper["payload"]
    except Exception as error:
        print(f"[checkpoint] could not read {path}: {error}; rebuilding")
        return None


def reset_global_annotations_if_requested():
    if "--redo-global-annotations" not in sys.argv:
        return
    names = (
        "manual_template_transforms.pkl",
        "completed_aligned_stacks.pkl",
    )
    removed = []
    for name in names:
        path = os.path.join(checkpoint_dir, name)
        if os.path.isfile(path):
            os.remove(path)
            removed.append(name)
    partial_csv = os.path.join(out_dir, "global_template_labels_transforms_partial.csv")
    if os.path.isfile(partial_csv):
        os.remove(partial_csv)
    print(
        "[redo] Global manual rotations and labels reset. "
        "Local/global template banks and the oriented reference with circles were preserved."
    )
    if removed:
        print(f"[redo] Removed checkpoint(s): {', '.join(removed)}")


def redo_selected_templates_if_requested(stack_info):
    prefix = "--redo-template-id="
    requested = []
    for index, arg in enumerate(sys.argv):
        if arg.startswith(prefix):
            requested.extend(arg[len(prefix):].split(","))
        elif arg == "--redo-template-id" and index + 1 < len(sys.argv):
            requested.extend(sys.argv[index + 1].split(","))
    requested = [value.strip() for value in requested if value.strip()]
    if not requested:
        return
    template_ids = {int(value) for value in requested}
    checkpoint = load_checkpoint("manual_template_transforms.pkl", stack_info) or {}
    transforms = checkpoint.get("transforms", {})
    removed = []
    for template_id in template_ids:
        if template_id in transforms:
            transforms.pop(template_id)
            removed.append(template_id)
        elif str(template_id) in transforms:
            transforms.pop(str(template_id))
            removed.append(template_id)
    save_checkpoint(
        "manual_template_transforms.pkl",
        {"transforms": transforms},
        stack_info,
    )
    completed_path = os.path.join(checkpoint_dir, "completed_aligned_stacks.pkl")
    if os.path.isfile(completed_path):
        os.remove(completed_path)
    partial_path = os.path.join(out_dir, "global_template_labels_transforms_partial.csv")
    write_csv(partial_path, list(transforms.values()))
    print(
        f"[redo template] removed manual annotation for template ID(s): "
        f"{', '.join(map(str, sorted(removed)))}; aligned outputs will be rebuilt"
    )


def save_local_artifacts(stack_name, local_templates, local_assignments):
    template_folder = os.path.join(checkpoint_dir, "local_templates", stack_name)
    assignment_folder = os.path.join(checkpoint_dir, "local_assignments")
    os.makedirs(template_folder, exist_ok=True)
    os.makedirs(assignment_folder, exist_ok=True)
    summary = []
    for template in local_templates:
        image_path = os.path.join(
            template_folder,
            f"local_template_{int(template['id']):04d}_frame_{int(template['frame']):06d}.jpg",
        )
        cv2.imwrite(image_path, normalize_uint8(template["image"]))
        summary.append({
            "local_template_id": template["id"],
            "stack": template["stack"],
            "source_frame": template["frame"],
            "represented_frame_count": template["count"],
            "retained_for_coverage": template.get("retained_for_coverage", 1),
            "image_path": image_path,
        })
    write_csv(os.path.join(template_folder, "local_template_summary.csv"), summary)
    write_csv(
        os.path.join(assignment_folder, f"{stack_name}_local_assignments.csv"),
        list(local_assignments.values()),
    )


def crop_tifs():
    if not os.path.isdir(crop_dir):
        return []
    return sorted(name for name in os.listdir(crop_dir) if name.endswith("_crop.tif"))


def stack_name_from_crop(name):
    return name[:-len("_crop.tif")]


def load_ok_head_angle_frames(stack_name, n_frames):
    path = os.path.join(head_angle_dir, stack_name, "head_angles.csv")
    if not os.path.isfile(path):
        print(f"[head angle] missing CSV, no frames will be used: {path}")
        return set(), {}, path
    valid = set()
    statuses = {}
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                frame_idx = int(row["frame"])
            except (KeyError, TypeError, ValueError):
                continue
            if not 0 <= frame_idx < n_frames:
                continue
            status = str(row.get("status", "")).strip()
            statuses[frame_idx] = status
            if status.lower() == HEAD_ANGLE_REQUIRED_STATUS:
                valid.add(frame_idx)
    return valid, statuses, path


def jpg_folder(stack_name):
    return os.path.join(jpg_crop_dir, f"{stack_name}_crop_jpg")


def read_jpg_frame(stack_name, frame_idx, shape):
    folder = jpg_folder(stack_name)
    for name in (f"{frame_idx:06d}.jpg", f"{frame_idx}.jpg"):
        image = cv2.imread(os.path.join(folder, name), cv2.IMREAD_GRAYSCALE)
        if image is not None:
            if image.shape != shape:
                image = cv2.resize(image, (shape[1], shape[0]), interpolation=cv2.INTER_AREA)
            return image
    return None


def build_all_frame_max_projection(stack_info, shape):
    maximum = np.zeros(shape, dtype=np.uint8)
    loaded = 0
    total = sum(info["n_frames"] for info in stack_info.values())
    with tqdm(total=total, desc="Build all-frame max projection") as progress:
        for stack_name, info in sorted(stack_info.items()):
            for frame_idx in range(info["n_frames"]):
                image = read_jpg_frame(stack_name, frame_idx, shape)
                if image is not None:
                    maximum = np.maximum(maximum, image)
                    loaded += 1
                progress.update(1)
    print(f"[match ROI] max projection built from {loaded}/{total} crop JPG frame(s)")
    return maximum


def draw_match_ellipse_roi(image):
    scale = 8 if max(image.shape[:2]) <= 90 else 5
    display = cv2.resize(
        cv2.cvtColor(normalize_uint8(image), cv2.COLOR_GRAY2BGR),
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_NEAREST,
    )
    state = {"drawing": False, "start": None, "current": None, "roi": None}

    def normalized_box(a, b):
        x1, y1 = a
        x2, y2 = b
        return min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)

    def on_mouse(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            state.update({"drawing": True, "start": (x, y), "current": (x, y)})
        elif event == cv2.EVENT_MOUSEMOVE and state["drawing"]:
            state["current"] = (x, y)
        elif event == cv2.EVENT_LBUTTONUP and state["drawing"]:
            state["drawing"] = False
            state["current"] = (x, y)
            box = normalized_box(state["start"], state["current"])
            if box[2] > 2 and box[3] > 2:
                state["roi"] = box

    window = "Draw ECC match ROI on all-frame max intensity"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, 900, 700)
    cv2.setMouseCallback(window, on_mouse)
    accepted = False
    while True:
        canvas = display.copy()
        cv2.putText(
            canvas,
            "Drag ellipse | Enter/Space accept | R/Backspace redraw",
            (8, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (255, 255, 255),
            1,
        )
        box = state["roi"]
        if state["drawing"]:
            box = normalized_box(state["start"], state["current"])
        if box is not None:
            x, y, w, h = box
            cv2.ellipse(
                canvas,
                (int(x + w / 2), int(y + h / 2)),
                (max(1, int(w / 2)), max(1, int(h / 2))),
                0, 0, 360, (0, 255, 255), 2,
            )
        cv2.imshow(window, canvas)
        key = cv2.waitKey(30) & 0xFF
        if key in (ord("r"), ord("R"), 8):
            state.update({"drawing": False, "start": None, "current": None, "roi": None})
        elif key in (13, 32) and state["roi"] is not None:
            accepted = True
            break
        elif key in (27, ord("q"), ord("Q")):
            break
    try:
        cv2.destroyWindow(window)
    except cv2.error:
        pass
    if not accepted:
        raise RuntimeError("ECC match ROI was not accepted")
    x, y, w, h = [value / scale for value in state["roi"]]
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.ellipse(
        mask,
        (int(round(x + w / 2)), int(round(y + h / 2))),
        (max(1, int(round(w / 2))), max(1, int(round(h / 2)))),
        0, 0, 360, 255, -1,
    )
    return mask


def reset_after_match_roi_redraw():
    names = (
        "local_banks.pkl",
        "global_bank.pkl",
        "reference_setup.pkl",
        "manual_template_transforms.pkl",
        "completed_aligned_stacks.pkl",
    )
    removed = []
    for name in names:
        path = os.path.join(checkpoint_dir, name)
        if os.path.isfile(path):
            os.remove(path)
            removed.append(name)
    print(f"[match ROI] reset {len(removed)} downstream checkpoint(s)")


def load_or_draw_match_roi(stack_info, shape):
    redraw = REDRAW_MATCH_ROI or "--redraw-roi" in sys.argv
    if not redraw:
        checkpoint = load_checkpoint("match_roi.pkl", stack_info)
        if checkpoint is not None:
            return checkpoint["mask"]
    maximum = build_all_frame_max_projection(stack_info, shape)
    cv2.imwrite(os.path.join(preview_dir, "all_frame_max_intensity.jpg"), maximum)
    mask = draw_match_ellipse_roi(maximum)
    cv2.imwrite(os.path.join(preview_dir, "ecc_match_roi.png"), mask)
    if redraw:
        reset_after_match_roi_redraw()
    save_checkpoint("match_roi.pkl", {"mask": mask}, stack_info)
    return mask


def load_or_create_reference_setup(global_templates, stack_info):
    redraw = "--redraw-reference" in sys.argv
    if not redraw:
        setup = load_checkpoint("reference_setup.pkl", stack_info)
        if setup is not None:
            return setup

    if not global_templates:
        raise RuntimeError("No template source was available for reference selection")
    print(f"[reference] choose the first reference from {len(global_templates)} global template(s)")
    selected_id = choose_reference_template(
        global_templates,
        title="Choose the first global reference template to orient",
    )
    selected = next(template for template in global_templates if int(template["id"]) == selected_id)
    print("[reference] orient the selected first reference template")
    reference_transform = orient_reference_template(selected)
    print("[reference] draw two circles on the oriented first reference template")
    reference_circles = draw_reference_circles(reference_transform["image"])
    reference_setup = {
        "reference_id": int(selected["id"]),
        "reference_stack": selected["stack"],
        "reference_frame": int(selected["frame"]),
        "reference_count": int(selected["count"]),
        "reference_transform": reference_transform,
        "reference_circles": reference_circles,
    }
    if redraw:
        reset_after_reference_redraw()
    save_checkpoint("reference_setup.pkl", reference_setup, stack_info)
    return reference_setup


def reset_after_reference_redraw():
    names = (
        "manual_template_transforms.pkl",
        "completed_aligned_stacks.pkl",
    )
    removed = []
    for name in names:
        path = os.path.join(checkpoint_dir, name)
        if os.path.isfile(path):
            os.remove(path)
            removed.append(name)
    print(
        "[reference] New orientation and circles accepted; preserving local/global banks and "
        "resetting manual alignment "
        f"from this point. Removed {len(removed)} downstream checkpoint(s)."
    )


def global_key(stack_name, frame_idx):
    return f"{stack_name}::{int(frame_idx):06d}"


def transform_image(image, angle_deg=0.0, tx=0.0, ty=0.0, scale=1.0):
    h, w = image.shape[:2]
    center = ((w - 1) / 2.0, (h - 1) / 2.0)
    matrix = cv2.getRotationMatrix2D(center, float(angle_deg), float(scale))
    matrix[0, 2] += float(tx)
    matrix[1, 2] += float(ty)
    return cv2.warpAffine(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )


def load_stack_frames():
    files = crop_tifs()
    if not files:
        return {}, None

    shape = None
    stack_info = {}
    for crop_name in files:
        stack_name = stack_name_from_crop(crop_name)
        crop_path = os.path.join(crop_dir, crop_name)
        with tifffile.TiffFile(crop_path) as tif:
            stack_shape = tuple(tif.pages[0].shape[:2])
            n_frames = len(tif.pages)
        valid_frames, statuses, head_angle_path = load_ok_head_angle_frames(stack_name, n_frames)
        if shape is None:
            shape = stack_shape
        stack_info[stack_name] = {
            "crop_name": crop_name,
            "crop_path": crop_path,
            "n_frames": n_frames,
            "source_shape": stack_shape,
            "valid_frames": valid_frames,
            "head_angle_status_by_frame": statuses,
            "head_angle_path": head_angle_path,
        }
    return stack_info, shape


def assignment_row(item, template, cc, warp, start_angle, errors, level="local"):
    row = {
        "stack": item["stack"],
        "frame": item["frame"],
        "global_key": global_key(item["stack"], item["frame"]),
        f"{level}_template_id": template["id"],
        "template_stack": template["stack"],
        "template_frame": template["frame"],
        f"{level}_match_cc": cc,
        f"{level}_ecc_start_angle": start_angle,
        f"{level}_ecc_rotation_deg": warp_rotation_deg(warp),
        f"{level}_ecc_errors": errors,
    }
    row.update(warp_values(f"{level}_ecc_", warp))
    return row


def build_bank(prepared, level, description, match_roi):
    templates = []
    assignments = {}
    remaining = set(prepared)
    rng = random.Random(RANDOM_SEED)
    threshold = (
        LOCAL_TEMPLATE_MATCH_THRESHOLD
        if level == "local"
        else GLOBAL_TEMPLATE_MATCH_THRESHOLD
    )

    def match_one(key, template):
        item = prepared[key]
        if key == template["key"]:
            cc, warp, start_angle, errors = 1.0, identity_warp(), 0, 0
        else:
            cc, warp, start_angle, errors = ecc_match_to_template(
                template["image"],
                item["image"],
                match_roi,
            )
        return key, cc, warp, start_angle, errors

    with ThreadPoolExecutor(max_workers=MATCH_WORKERS, thread_name_prefix="ecc") as executor:
        while remaining:
            seed_key = rng.choice(sorted(remaining))
            seed = prepared[seed_key]
            template = {
                "id": len(templates),
                "key": seed_key,
                "stack": seed["stack"],
                "frame": seed["frame"],
                "image": seed["image"],
                "count": 0,
            }
            print(
                f"[{description}] candidate {template['id']}: "
                f"{template['stack']} frame {template['frame']}, remaining={len(remaining)}"
            )

            keys = sorted(remaining)
            results = executor.map(lambda key: match_one(key, template), keys)
            matched = []
            matched_rows = {}
            for key, cc, warp, start_angle, errors in tqdm(
                results,
                total=len(keys),
                desc=f"Match {description} candidate {template['id']}",
                leave=False,
            ):
                item = prepared[key]
                if np.isfinite(cc) and cc >= threshold:
                    matched_rows[key] = assignment_row(
                        item,
                        template,
                        cc,
                        warp,
                        start_angle,
                        errors,
                        level=level,
                    )
                    matched.append(key)
            templates.append(template)
            assignments.update(matched_rows)
            for key in matched:
                remaining.discard(key)
            template["count"] = len(matched)
            print(f"[{description}] template {template['id']}: matched {len(matched)} item(s)")

    return templates, assignments


def retain_local_templates_for_coverage(templates, assignments):
    total_frames = sum(int(template["count"]) for template in templates)
    target_frames = int(np.ceil(total_frames * LOCAL_TEMPLATE_FRAME_COVERAGE))
    ranked = sorted(
        templates,
        key=lambda template: (-int(template["count"]), int(template["id"])),
    )
    retained_ids = set()
    retained_frames = 0
    for template in ranked:
        if retained_frames >= target_frames:
            break
        retained_ids.add(int(template["id"]))
        retained_frames += int(template["count"])

    for template in templates:
        template["retained_for_coverage"] = int(int(template["id"]) in retained_ids)
    for row in assignments.values():
        local_template_id = int(row["local_template_id"])
        if local_template_id not in retained_ids:
            row["original_local_template_id"] = local_template_id
            row["local_template_id"] = -1
            row["dropped_local_coverage_tail"] = 1

    retained_templates = [
        template for template in templates
        if int(template["id"]) in retained_ids
    ]
    return retained_templates, retained_frames, total_frames


def build_local_banks(stack_info, shape, match_roi):
    checkpoint = load_checkpoint("local_banks.pkl", stack_info) or {}
    all_local_templates = checkpoint.get("local_templates", [])
    frame_assignments = checkpoint.get("frame_assignments", {})
    completed_stacks = set(checkpoint.get("completed_stacks", []))
    for stack_number, (stack_name, info) in enumerate(sorted(stack_info.items()), start=1):
        if stack_name in completed_stacks:
            print(f"[checkpoint] local bank already complete: {stack_name}")
            continue
        prepared = {}
        valid_frames = sorted(info["valid_frames"])
        if not valid_frames:
            print(f"[head angle] {stack_name}: no status={HEAD_ANGLE_REQUIRED_STATUS} frames; skipping")
            completed_stacks.add(stack_name)
            save_checkpoint(
                "local_banks.pkl",
                {
                    "local_templates": all_local_templates,
                    "frame_assignments": frame_assignments,
                    "completed_stacks": sorted(completed_stacks),
                },
                stack_info,
            )
            continue
        for frame_idx in tqdm(valid_frames, desc=f"Load valid local {stack_number}/{len(stack_info)}"):
            image = read_jpg_frame(stack_name, frame_idx, shape)
            if image is None:
                continue
            key = global_key(stack_name, frame_idx)
            prepared[key] = {
                "stack": stack_name,
                "frame": frame_idx,
                "image": prepare_match_image(image, match_roi),
            }
        all_candidate_templates, local_assignments = build_bank(
            prepared,
            level="local",
            description=f"local {stack_name}",
            match_roi=match_roi,
        )
        local_templates, retained_frames, total_matched_frames = retain_local_templates_for_coverage(
            all_candidate_templates,
            local_assignments,
        )
        save_local_artifacts(stack_name, all_candidate_templates, local_assignments)
        for template in local_templates:
            template["local_template_id"] = template["id"]
            template["local_key"] = f"{stack_name}::local::{template['id']:04d}"
            template["id"] = len(all_local_templates)
            template["key"] = template["local_key"]
            all_local_templates.append(template)
        local_id_map = {
            int(template["local_template_id"]): int(template["id"])
            for template in all_local_templates
            if template["stack"] == stack_name
        }
        for key, row in local_assignments.items():
            if int(row["local_template_id"]) >= 0:
                row["local_template_id"] = local_id_map[int(row["local_template_id"])]
            frame_assignments[key] = row
        completed_stacks.add(stack_name)
        save_checkpoint(
            "local_banks.pkl",
            {
                "local_templates": all_local_templates,
                "frame_assignments": frame_assignments,
                "completed_stacks": sorted(completed_stacks),
            },
            stack_info,
        )
        print(
            f"[local summary] {stack_name}: {len(prepared)}/{info['n_frames']} "
            f"status={HEAD_ANGLE_REQUIRED_STATUS} frame(s) -> "
            f"built {len(all_candidate_templates)}, retained {len(local_templates)} local template(s), "
            f"coverage={retained_frames}/{total_matched_frames} "
            f"({retained_frames / max(1, total_matched_frames):.1%})"
        )
    return all_local_templates, frame_assignments


def build_global_bank_from_local_templates(local_templates, match_roi, stack_info=None):
    checkpoint = load_checkpoint("global_bank.pkl", stack_info)
    if checkpoint is not None:
        return checkpoint["global_templates"], checkpoint["local_to_global"]
    prepared = {}
    for template in local_templates:
        prepared[template["local_key"]] = {
            "stack": template["stack"],
            "frame": template["frame"],
            "image": template["image"],
            "local_template_id": template["id"],
        }
    global_templates, local_to_global = build_bank(
        prepared,
        level="global",
        description="global local-template",
        match_roi=match_roi,
    )
    local_counts = {int(template["id"]): int(template["count"]) for template in local_templates}
    global_counts = {int(template["id"]): 0 for template in global_templates}
    for local_key, row in local_to_global.items():
        local_template_id = int(prepared[local_key]["local_template_id"])
        row["local_template_id"] = local_template_id
        global_counts[int(row["global_template_id"])] += local_counts[local_template_id]
    for template in global_templates:
        template["local_template_id"] = prepared[template["key"]]["local_template_id"]
        template["local_template_count"] = template["count"]
        template["count"] = global_counts[int(template["id"])]

    ranked_global_templates = sorted(
        global_templates,
        key=lambda template: (-int(template["count"]), int(template["id"])),
    )
    total_global_frames = sum(int(template["count"]) for template in ranked_global_templates)
    target_global_frames = int(np.ceil(total_global_frames * GLOBAL_TEMPLATE_FRAME_COVERAGE))
    retained_global_ids = set()
    retained_global_frames = 0
    for template in ranked_global_templates:
        if retained_global_frames >= target_global_frames:
            break
        retained_global_ids.add(int(template["id"]))
        retained_global_frames += int(template["count"])
    dropped_templates = [
        template
        for template in global_templates
        if int(template["id"]) not in retained_global_ids
    ]
    global_templates = [
        template
        for template in global_templates
        if int(template["id"]) in retained_global_ids
    ]
    for row in local_to_global.values():
        row["global_template_retained"] = int(
            int(row["global_template_id"]) in retained_global_ids
        )
    print(
        f"[global coverage] retained {len(global_templates)}/{len(ranked_global_templates)} "
        f"template(s), covering {retained_global_frames}/{total_global_frames} frame(s) "
        f"({retained_global_frames / max(1, total_global_frames):.1%}); "
        f"dropped {len(dropped_templates)} coverage-tail template(s)"
    )
    save_checkpoint(
        "global_bank.pkl",
        {
            "global_templates": global_templates,
            "local_to_global": local_to_global,
        },
        stack_info,
    )
    return global_templates, local_to_global


def save_global_template_frame_distribution(global_templates):
    if not global_templates:
        return
    os.makedirs(preview_dir, exist_ok=True)
    ranked = sorted(
        global_templates,
        key=lambda template: (-int(template["count"]), int(template["id"])),
    )
    rows = [
        {
            "rank": rank,
            "global_template_id": int(template["id"]),
            "represented_frame_count": int(template["count"]),
            "template_stack": template["stack"],
            "template_frame": int(template["frame"]),
        }
        for rank, template in enumerate(ranked, start=1)
    ]
    write_csv(os.path.join(out_dir, "global_template_frame_distribution.csv"), rows)

    counts = np.array([row["represented_frame_count"] for row in rows], dtype=int)
    plt.figure(figsize=(14, 5))
    plt.bar(np.arange(1, len(counts) + 1), counts, width=0.85)
    plt.xlabel("Retained global template rank (sorted by represented frames)")
    plt.ylabel("Represented frame count")
    plt.title(
        f"Retained global template frame distribution: "
        f"{len(counts)} templates, {int(counts.sum())} frames"
    )
    plt.yscale("log")
    plt.tight_layout()
    plt.savefig(
        os.path.join(preview_dir, "global_template_frame_counts_ranked.png"),
        dpi=180,
    )
    plt.close()

    plt.figure(figsize=(9, 5))
    bins = np.unique(np.geomspace(1, max(2, int(counts.max()) + 1), 20).astype(int))
    plt.hist(counts, bins=bins)
    plt.xscale("log")
    plt.xlabel("Represented frame count per retained global template")
    plt.ylabel("Number of global templates")
    plt.title("Retained global template support histogram")
    plt.tight_layout()
    plt.savefig(
        os.path.join(preview_dir, "global_template_frame_counts_histogram.png"),
        dpi=180,
    )
    plt.close()
    print(
        f"[global distribution] saved frame-count plots for "
        f"{len(global_templates)} retained template(s)"
    )


def choose_reference_template(
    templates,
    title="Choose the common reference template. Templates are ordered by represented frame count, largest first.",
):
    display_templates = sorted(
        templates,
        key=lambda template: (-int(template["count"]), int(template["id"])),
    )[:20]
    cols = 5
    rows = int(np.ceil(len(display_templates) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(15, max(4, rows * 3)))
    axes = np.atleast_1d(axes).reshape(-1)
    selected = {"id": None}

    for rank, (ax, template) in enumerate(zip(axes, display_templates), start=1):
        ax.imshow(template["image"], cmap="gray")
        ax.set_title(
            f"Rank {rank} | Template {template['id']} | class frames={template['count']}\n"
            f"{template['stack']} f={template['frame']}",
            fontsize=9,
        )
        ax.text(
            0.02,
            0.98,
            f"{template['count']} frames",
            transform=ax.transAxes,
            va="top",
            ha="left",
            color="yellow",
            fontsize=10,
            fontweight="bold",
            bbox={"facecolor": "black", "alpha": 0.75, "edgecolor": "none"},
        )
        ax.set_axis_off()
        ax._template_id = template["id"]
    for ax in axes[len(display_templates):]:
        ax.set_axis_off()

    def on_click(event):
        if event.inaxes is None or not hasattr(event.inaxes, "_template_id"):
            return
        selected["id"] = int(event.inaxes._template_id)
        plt.close(fig)

    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.suptitle(title)
    plt.tight_layout()
    plt.show()
    if selected["id"] is None:
        raise RuntimeError("No reference template selected")
    return selected["id"]


def draw_reference_circles(reference_image):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(reference_image, cmap="gray")
    circles = []
    state = {"center": None, "done": False}

    def redraw():
        ax.clear()
        ax.imshow(reference_image, cmap="gray")
        for idx, circle in enumerate(circles):
            ax.add_patch(Circle(
                (circle["x"], circle["y"]),
                circle["radius"],
                fill=False,
                color=("cyan" if idx == 0 else "yellow"),
                linewidth=2,
            ))
        if state["center"] is not None:
            ax.plot(state["center"][0], state["center"][1], "+", color="red", markersize=12, markeredgewidth=2)
        circle_number = min(len(circles) + 1, 2)
        action = "click center" if state["center"] is None else "click edge to set radius"
        ax.set_title(
            f"Circle {circle_number}/2: {action}\n"
            "Left click: draw | Right click: undo"
        )
        ax.set_axis_off()
        fig.canvas.draw_idle()

    def on_click(event):
        if event.inaxes != ax:
            return
        if event.button == 3:
            if state["center"] is not None:
                state["center"] = None
            elif circles:
                circles.pop()
            redraw()
            return
        if event.button != 1 or event.xdata is None or event.ydata is None:
            return
        point = (float(event.xdata), float(event.ydata))
        if state["center"] is None:
            state["center"] = point
            redraw()
            return
        center = state["center"]
        radius = float(np.hypot(point[0] - center[0], point[1] - center[1]))
        if radius > 0:
            circles.append({"x": center[0], "y": center[1], "radius": radius})
        state["center"] = None
        if len(circles) >= 2:
            state["done"] = True
            plt.close(fig)
        else:
            redraw()

    fig.canvas.mpl_connect("button_press_event", on_click)
    redraw()
    plt.show()
    if not state["done"]:
        raise RuntimeError("Two reference circles were not completed")
    plt.close(fig)
    return circles


def orient_reference_template(reference):
    fig = plt.figure(figsize=(10, 9))
    ax_image = fig.add_axes([0.08, 0.25, 0.84, 0.70])
    ax_angle = fig.add_axes([0.12, 0.17, 0.60, 0.03])
    ax_tx = fig.add_axes([0.12, 0.12, 0.60, 0.03])
    ax_ty = fig.add_axes([0.12, 0.07, 0.60, 0.03])
    ax_save = fig.add_axes([0.77, 0.07, 0.16, 0.10])

    angle_slider = Slider(ax_angle, "angle", -180, 180, valinit=0, valstep=1)
    tx_slider = Slider(ax_tx, "tx", -50, 50, valinit=0, valstep=1)
    ty_slider = Slider(ax_ty, "ty", -50, 50, valinit=0, valstep=1)
    save_button = Button(ax_save, "Save reference")
    result = {
        "saved": False,
        "gamepad_buttons": 0,
        "gamepad_connected": read_gamepad() is not None,
    }

    def redraw(_value=None):
        image = transform_image(
            reference["image"],
            angle_slider.val,
            tx_slider.val,
            ty_slider.val,
            scale=1.0,
        )
        ax_image.clear()
        ax_image.imshow(image, cmap="gray")
        ax_image.set_title(
            f"Orient reference template id={reference['id']} | "
            f"class frames={reference['count']} | "
            f"gamepad={'connected' if result['gamepad_connected'] else 'not detected'}"
        )
        ax_image.set_axis_off()
        fig.canvas.draw_idle()

    def save(_event):
        result.update({
            "saved": True,
            "angle": float(angle_slider.val),
            "tx": float(tx_slider.val),
            "ty": float(ty_slider.val),
        })
        if "gamepad_timer" in result:
            result["gamepad_timer"].stop()
        plt.close(fig)

    def set_slider(slider, value):
        slider.set_val(float(np.clip(value, slider.valmin, slider.valmax)))

    def poll_gamepad():
        if result["saved"]:
            return False
        gamepad = read_gamepad()
        if gamepad is None:
            result["gamepad_connected"] = False
            result["gamepad_buttons"] = 0
            return True
        result["gamepad_connected"] = True
        buttons = gamepad["buttons"]
        pressed = buttons & ~result["gamepad_buttons"]
        result["gamepad_buttons"] = buttons
        if gamepad["lx"]:
            set_slider(tx_slider, tx_slider.val + gamepad["lx"] * GAMEPAD_TRANSLATION_STEP_PX)
        if gamepad["ly"]:
            set_slider(ty_slider, ty_slider.val - gamepad["ly"] * GAMEPAD_TRANSLATION_STEP_PX)
        if gamepad["rx"]:
            set_slider(angle_slider, angle_slider.val + gamepad["rx"] * GAMEPAD_ROTATION_STEP_DEG)
        if pressed & XINPUT_GAMEPAD_DPAD_LEFT:
            set_slider(angle_slider, angle_slider.val - 1)
        if pressed & XINPUT_GAMEPAD_DPAD_RIGHT:
            set_slider(angle_slider, angle_slider.val + 1)
        if pressed & XINPUT_GAMEPAD_BACK:
            angle_slider.reset()
            tx_slider.reset()
            ty_slider.reset()
        if pressed & XINPUT_GAMEPAD_A:
            save(None)
            return False
        return True

    for slider in (angle_slider, tx_slider, ty_slider):
        slider.on_changed(redraw)
    save_button.on_clicked(save)
    gamepad_timer = fig.canvas.new_timer(interval=40)
    gamepad_timer.add_callback(poll_gamepad)
    result["gamepad_timer"] = gamepad_timer
    gamepad_timer.start()
    redraw()
    plt.show()
    if not result["saved"]:
        raise RuntimeError("Reference orientation closed without saving")
    result["image"] = transform_image(
        reference["image"],
        result["angle"],
        result["tx"],
        result["ty"],
        scale=1.0,
    )
    result.pop("gamepad_timer", None)
    result.pop("gamepad_buttons", None)
    result.pop("gamepad_connected", None)
    return result


def add_circles(ax, circles):
    for idx, circle in enumerate(circles):
        ax.add_patch(
            Circle(
                (circle["x"], circle["y"]),
                circle["radius"],
                fill=False,
                color=("cyan" if idx == 0 else "yellow"),
                linewidth=2,
            )
        )


def alignment_overlay(reference_image, current_image, match_roi):
    reference = normalize_uint8(reference_image).astype(np.float32)
    current = normalize_uint8(current_image).astype(np.float32)
    reference = np.clip(reference * OVERLAY_REFERENCE_GAIN, 0, 255).astype(np.uint8)
    current = np.clip(current * OVERLAY_CURRENT_GAIN, 0, 255).astype(np.uint8)
    overlay = np.zeros((*reference.shape[:2], 3), dtype=np.uint8)
    overlay[..., 0] = reference
    overlay[..., 2] = reference
    overlay[..., 1] = current
    overlay[match_roi == 0] = (overlay[match_roi == 0].astype(np.float32) * 0.2).astype(np.uint8)
    return overlay


def annotate_and_align_templates(
    templates,
    reference_id,
    reference_transform,
    circles,
    match_roi,
    existing_results=None,
    stack_info=None,
    checkpoint_name="manual_template_transforms.pkl",
    partial_csv_name="global_template_labels_transforms_partial.csv",
    annotation_prefix="Template",
    reference_image_override=None,
):
    if reference_image_override is None:
        reference = next(t for t in templates if t["id"] == reference_id)
        reference_image = reference_transform["image"]
        ordered = [reference] + [t for t in templates if t["id"] != reference_id]
    else:
        reference_image = reference_image_override
        ordered = list(templates)
    results = dict(existing_results or {})

    for number, template in enumerate(ordered, start=1):
        if template["id"] in results:
            print(
                f"[checkpoint] manual template already complete: "
                f"{number}/{len(ordered)} id={template['id']}"
            )
            continue
        is_reference = reference_image_override is None and template["id"] == reference_id
        fig = plt.figure(figsize=(18, 9))
        ax_ref = fig.add_axes([0.02, 0.30, 0.30, 0.63])
        ax_current = fig.add_axes([0.35, 0.30, 0.30, 0.63])
        ax_overlay = fig.add_axes([0.68, 0.30, 0.30, 0.63])
        ax_angle = fig.add_axes([0.08, 0.20, 0.35, 0.025])
        ax_tx = fig.add_axes([0.08, 0.155, 0.35, 0.025])
        ax_ty = fig.add_axes([0.08, 0.11, 0.35, 0.025])
        ax_scale = fig.add_axes([0.08, 0.065, 0.35, 0.025])
        ax_loop = fig.add_axes([0.52, 0.13, 0.16, 0.10])
        ax_state = fig.add_axes([0.72, 0.035, 0.26, 0.22])
        ax_save = fig.add_axes([0.37, 0.04, 0.095, 0.055])
        ax_blur = fig.add_axes([0.47, 0.04, 0.095, 0.055])
        ax_ring = fig.add_axes([0.57, 0.04, 0.105, 0.055])
        ax_no_ria = fig.add_axes([0.68, 0.04, 0.105, 0.055])

        angle_slider = Slider(ax_angle, "angle", -180, 180, valinit=0, valstep=1)
        tx_slider = Slider(ax_tx, "tx", -50, 50, valinit=0, valstep=1)
        ty_slider = Slider(ax_ty, "ty", -50, 50, valinit=0, valstep=1)
        scale_slider = Slider(ax_scale, "match scale", 0.70, 1.30, valinit=1.0, valstep=0.01)
        loop_radio = RadioButtons(ax_loop, LOOP_LABELS, active=0)
        state_radio = RadioButtons(ax_state, STATE_LABELS, active=0)
        save_button = Button(ax_save, "Save / Next")
        blur_button = Button(ax_blur, "Mark blur / Next")
        ring_button = Button(ax_ring, "Mark ring / Next")
        no_ria_button = Button(ax_no_ria, "No RIA / Next")
        state = {
            "saved": False,
            "cc": np.nan,
            "gamepad_buttons": 0,
            "gamepad_connected": read_gamepad() is not None,
        }

        def redraw(_value=None):
            angle = reference_transform["angle"] if is_reference else angle_slider.val
            tx = reference_transform["tx"] if is_reference else tx_slider.val
            ty = reference_transform["ty"] if is_reference else ty_slider.val
            scale = 1.0 if is_reference else scale_slider.val
            warped = reference_image if is_reference else transform_image(template["image"], angle, tx, ty, scale)
            cc = 1.0 if is_reference else full_crop_ncc(reference_image, warped, match_roi)
            state["cc"] = cc
            ax_ref.clear()
            ax_current.clear()
            ax_overlay.clear()
            ax_ref.imshow(reference_image, cmap="gray")
            ax_current.imshow(warped, cmap="gray")
            ax_overlay.imshow(alignment_overlay(reference_image, warped, match_roi))
            add_circles(ax_ref, circles)
            add_circles(ax_current, circles)
            add_circles(ax_overlay, circles)
            ax_ref.set_title(f"Reference template id={reference_id}")
            ax_current.set_title(
                f"Current template (grayscale; inspect blur)\n"
                f"{annotation_prefix} {number}/{len(ordered)} id={template['id']} | "
                f"class frames={template['count']} | CC={cc:.4f} | "
                f"gamepad={'connected' if state['gamepad_connected'] else 'not detected'}"
            )
            ax_overlay.set_title("Alignment overlay: current=green, reference=magenta")
            ax_ref.set_axis_off()
            ax_current.set_axis_off()
            ax_overlay.set_axis_off()
            fig.canvas.draw_idle()

        def save_result(state_label, use_manual_transform):
            results[template["id"]] = {
                "template_id": template["id"],
                "template_stack": template["stack"],
                "template_frame": template["frame"],
                "class_frame_count": template["count"],
                "is_reference": int(is_reference),
                "angle": (
                    float(reference_transform["angle"])
                    if is_reference
                    else float(angle_slider.val) if use_manual_transform else 0.0
                ),
                "tx": (
                    float(reference_transform["tx"])
                    if is_reference
                    else float(tx_slider.val) if use_manual_transform else 0.0
                ),
                "ty": (
                    float(reference_transform["ty"])
                    if is_reference
                    else float(ty_slider.val) if use_manual_transform else 0.0
                ),
                "match_scale": 1.0 if is_reference or not use_manual_transform else float(scale_slider.val),
                "manual_cc": 1.0 if is_reference else float(state["cc"]) if use_manual_transform else np.nan,
                "loop_label": loop_radio.value_selected,
                "state_label": state_label,
                "manual_alignment_skipped": int(not use_manual_transform),
            }
            save_checkpoint(
                checkpoint_name,
                {"transforms": results},
                stack_info,
            )
            write_csv(
                os.path.join(out_dir, partial_csv_name),
                list(results.values()),
            )
            state["saved"] = True
            if "gamepad_timer" in state:
                state["gamepad_timer"].stop()
            plt.close(fig)

        def save_and_close(_event):
            save_result(state_radio.value_selected, use_manual_transform=True)

        def mark_blur_and_close(_event):
            save_result("blur", use_manual_transform=False)

        def mark_ring_and_close(_event):
            save_result("z_rotation_ring_visible", use_manual_transform=False)

        def mark_no_ria_and_close(_event):
            save_result("no_ria_visible", use_manual_transform=False)

        def set_slider(slider, value):
            slider.set_val(float(np.clip(value, slider.valmin, slider.valmax)))

        def poll_gamepad():
            if state["saved"]:
                return False
            gamepad = read_gamepad()
            if gamepad is None:
                state["gamepad_connected"] = False
                state["gamepad_buttons"] = 0
                return True
            state["gamepad_connected"] = True
            buttons = gamepad["buttons"]
            pressed = buttons & ~state["gamepad_buttons"]
            state["gamepad_buttons"] = buttons

            if not is_reference:
                if gamepad["lx"]:
                    set_slider(tx_slider, tx_slider.val + gamepad["lx"] * GAMEPAD_TRANSLATION_STEP_PX)
                if gamepad["ly"]:
                    set_slider(ty_slider, ty_slider.val - gamepad["ly"] * GAMEPAD_TRANSLATION_STEP_PX)
                if gamepad["rx"]:
                    set_slider(angle_slider, angle_slider.val + gamepad["rx"] * GAMEPAD_ROTATION_STEP_DEG)
                if gamepad["ry"]:
                    set_slider(scale_slider, scale_slider.val + gamepad["ry"] * GAMEPAD_SCALE_STEP)
                if pressed & XINPUT_GAMEPAD_DPAD_LEFT:
                    set_slider(angle_slider, angle_slider.val - 1)
                if pressed & XINPUT_GAMEPAD_DPAD_RIGHT:
                    set_slider(angle_slider, angle_slider.val + 1)
                if pressed & XINPUT_GAMEPAD_DPAD_UP:
                    set_slider(scale_slider, scale_slider.val + 0.01)
                if pressed & XINPUT_GAMEPAD_DPAD_DOWN:
                    set_slider(scale_slider, scale_slider.val - 0.01)
                if pressed & XINPUT_GAMEPAD_BACK:
                    angle_slider.reset()
                    tx_slider.reset()
                    ty_slider.reset()
                    scale_slider.reset()
            if pressed & XINPUT_GAMEPAD_LEFT_SHOULDER:
                loop_radio.set_active(0)
            if pressed & XINPUT_GAMEPAD_RIGHT_SHOULDER:
                loop_radio.set_active(1)
            if pressed & XINPUT_GAMEPAD_A:
                save_and_close(None)
                return False
            if pressed & XINPUT_GAMEPAD_B:
                mark_blur_and_close(None)
                return False
            if pressed & XINPUT_GAMEPAD_Y:
                mark_ring_and_close(None)
                return False
            if pressed & XINPUT_GAMEPAD_X:
                mark_no_ria_and_close(None)
                return False
            return True

        for slider in (angle_slider, tx_slider, ty_slider, scale_slider):
            slider.on_changed(redraw)
        save_button.on_clicked(save_and_close)
        blur_button.on_clicked(mark_blur_and_close)
        ring_button.on_clicked(mark_ring_and_close)
        no_ria_button.on_clicked(mark_no_ria_and_close)
        gamepad_timer = fig.canvas.new_timer(interval=40)
        gamepad_timer.add_callback(poll_gamepad)
        state["gamepad_timer"] = gamepad_timer
        gamepad_timer.start()
        redraw()
        plt.show()
        if not state["saved"]:
            raise RuntimeError(f"Template annotation closed without saving: id={template['id']}")
    return results


def save_reference_metadata(reference_id, reference_image, circles, templates, transforms):
    write_csv(
        os.path.join(out_dir, "global_reference_circles.csv"),
        [{"reference_template_id": reference_id, "circle_id": idx + 1, **circle} for idx, circle in enumerate(circles)],
    )
    write_csv(os.path.join(out_dir, "global_template_labels_transforms.csv"), list(transforms.values()))
    cv2.imwrite(os.path.join(preview_dir, "global_oriented_reference.jpg"), normalize_uint8(reference_image))
    make_global_template_preview(
        templates,
        os.path.join(preview_dir, "global_template_bank.jpg"),
        reference_id,
    )



def save_frame_label_manifest(frame_assignments, local_to_global, transforms):
    global_by_local_id = {
        int(row["local_template_id"]): row
        for row in local_to_global.values()
    }
    rows = []
    blur_rows = []
    ring_rows = []
    no_ria_rows = []
    for assignment in frame_assignments.values():
        global_assignment = global_by_local_id.get(int(assignment["local_template_id"]))
        if global_assignment is None:
            continue
        if not int(float(global_assignment.get("global_template_retained", 1) or 0)):
            continue
        transform = transforms[int(global_assignment["global_template_id"])]
        frame_idx = int(assignment["frame"])
        row = {
            "stack": assignment["stack"],
            "frame": frame_idx,
            "jpg_path": os.path.join(jpg_folder(assignment["stack"]), f"{frame_idx:06d}.jpg"),
            "local_template_id": assignment["local_template_id"],
            "global_template_id": global_assignment["global_template_id"],
            "local_match_cc": assignment["local_match_cc"],
            "global_match_cc": global_assignment["global_match_cc"],
            "class_frame_count": transform["class_frame_count"],
            "loop_label": transform["loop_label"],
            "state_label": transform["state_label"],
            "manual_alignment_skipped": transform.get("manual_alignment_skipped", 0),
        }
        rows.append(row)
        if transform["state_label"] == "blur":
            blur_rows.append(row)
        if transform["state_label"] == "z_rotation_ring_visible":
            ring_rows.append(row)
        if transform["state_label"] == "no_ria_visible":
            no_ria_rows.append(row)
    write_csv(os.path.join(out_dir, "all_valid_frame_template_labels.csv"), rows)
    write_csv(os.path.join(out_dir, "blur_classifier_training_manifest.csv"), blur_rows)
    write_csv(os.path.join(out_dir, "z_rotation_ring_training_manifest.csv"), ring_rows)
    write_csv(os.path.join(out_dir, "no_ria_visible_training_manifest.csv"), no_ria_rows)
    print(
        f"[labels] expanded template labels to {len(rows)} valid frame(s), "
        f"blur={len(blur_rows)}, z_rotation_ring_visible={len(ring_rows)}, "
        f"no_ria_visible={len(no_ria_rows)}"
    )


def make_global_template_preview(templates, out_path, reference_id):
    if not templates:
        return
    tiles = []
    for template in templates:
        tile = cv2.cvtColor(normalize_uint8(template["image"]), cv2.COLOR_GRAY2BGR)
        color = (0, 255, 0) if template["id"] == reference_id else (0, 255, 255)
        cv2.putText(
            tile,
            f"id={template['id']} n={template['count']}",
            (3, 13),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            color,
            1,
        )
        tiles.append(tile)
    h, w = tiles[0].shape[:2]
    cols = 6
    rows = int(np.ceil(len(tiles) / cols))
    canvas = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
    for idx, tile in enumerate(tiles):
        y, x = (idx // cols) * h, (idx % cols) * w
        canvas[y:y + h, x:x + w] = tile
    cv2.imwrite(out_path, cv2.resize(canvas, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST))


def save_template_alignment_overview(templates, transforms, circles):
    if not templates:
        return
    tiles = []
    aligned_normal = []
    loop_audit_tiles = {"loop_left": [], "loop_right": []}
    loop_audit_rows = []
    for template in sorted(templates, key=lambda item: int(item["id"])):
        transform = transforms[int(template["id"])]
        aligned = transform_image(
            template["image"],
            transform["angle"],
            transform["tx"],
            transform["ty"],
            scale=1.0,
        )
        state_label = str(transform.get("state_label", ""))
        if state_label == "normal":
            aligned_normal.append(normalize_uint8(aligned))
        tile = cv2.cvtColor(normalize_uint8(aligned), cv2.COLOR_GRAY2BGR)
        for idx, circle in enumerate(circles):
            cv2.circle(
                tile,
                (int(round(circle["x"])), int(round(circle["y"]))),
                max(1, int(round(circle["radius"]))),
                (255, 255, 0) if idx == 0 else (0, 255, 255),
                1,
                cv2.LINE_AA,
            )
        try:
            cc = float(transform.get("manual_cc", np.nan))
        except (TypeError, ValueError):
            cc = np.nan
        cc_text = f"{cc:.3f}" if np.isfinite(cc) else "skip"
        cv2.putText(
            tile,
            f"id={template['id']} n={template['count']} cc={cc_text}",
            (2, 11),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.28,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            tile,
            state_label,
            (2, tile.shape[0] - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.25,
            (0, 255, 0) if state_label == "normal" else (0, 180, 255),
            1,
            cv2.LINE_AA,
        )
        tiles.append(tile)

        loop_label = str(transform.get("loop_label", ""))
        loop_audit_rows.append({
            "template_id": int(template["id"]),
            "represented_frames": int(template["count"]),
            "loop_label": loop_label,
            "state_label": state_label,
            "manual_cc": cc_text,
            "source_stack": str(template.get("stack", "")),
            "source_frame": int(template.get("frame", -1)),
        })
        if loop_label in loop_audit_tiles:
            original_tile = cv2.cvtColor(
                normalize_uint8(template["image"]),
                cv2.COLOR_GRAY2BGR,
            )
            aligned_tile = cv2.cvtColor(
                normalize_uint8(aligned),
                cv2.COLOR_GRAY2BGR,
            )
            for circle_idx, circle in enumerate(circles):
                cv2.circle(
                    aligned_tile,
                    (int(round(circle["x"])), int(round(circle["y"]))),
                    max(1, int(round(circle["radius"]))),
                    (255, 255, 0) if circle_idx == 0 else (0, 255, 255),
                    1,
                    cv2.LINE_AA,
                )
            audit_tile = np.concatenate([original_tile, aligned_tile], axis=1)
            cv2.putText(
                audit_tile,
                "ORIGINAL",
                (2, 11),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.28,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                audit_tile,
                "ALIGNED",
                (original_tile.shape[1] + 2, 11),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.28,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                audit_tile,
                f"id={template['id']} n={template['count']} {state_label}",
                (2, audit_tile.shape[0] - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.25,
                (0, 255, 0) if state_label == "normal" else (0, 180, 255),
                1,
                cv2.LINE_AA,
            )
            loop_audit_tiles[loop_label].append((
                int(template["count"]),
                int(template["id"]),
                audit_tile,
            ))

    h, w = tiles[0].shape[:2]
    cols = min(8, len(tiles))
    rows = int(np.ceil(len(tiles) / cols))
    canvas = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
    for idx, tile in enumerate(tiles):
        y, x = (idx // cols) * h, (idx % cols) * w
        canvas[y:y + h, x:x + w] = tile
    overview_path = os.path.join(preview_dir, "global_template_alignment_overview.jpg")
    cv2.imwrite(
        overview_path,
        cv2.resize(canvas, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
    )

    if aligned_normal:
        normal_stack = np.stack(aligned_normal)
        cv2.imwrite(
            os.path.join(preview_dir, "aligned_normal_templates_max_intensity.jpg"),
            normalize_uint8(normal_stack.max(axis=0)),
        )
        cv2.imwrite(
            os.path.join(preview_dir, "aligned_normal_templates_mean_intensity.jpg"),
            normalize_uint8(normal_stack.mean(axis=0)),
        )

    loop_audit_dir = os.path.join(preview_dir, "loop_label_audit")
    os.makedirs(loop_audit_dir, exist_ok=True)
    for loop_label, audit_items in loop_audit_tiles.items():
        if not audit_items:
            continue
        audit_items.sort(key=lambda item: (-item[0], item[1]))
        audit_tiles = [item[2] for item in audit_items]
        audit_h, audit_w = audit_tiles[0].shape[:2]
        audit_cols = min(5, len(audit_tiles))
        audit_rows = int(np.ceil(len(audit_tiles) / audit_cols))
        audit_canvas = np.zeros(
            (audit_rows * audit_h, audit_cols * audit_w, 3),
            dtype=np.uint8,
        )
        for idx, audit_tile in enumerate(audit_tiles):
            y = (idx // audit_cols) * audit_h
            x = (idx % audit_cols) * audit_w
            audit_canvas[y:y + audit_h, x:x + audit_w] = audit_tile
        cv2.imwrite(
            os.path.join(loop_audit_dir, f"{loop_label}_templates.jpg"),
            cv2.resize(
                audit_canvas,
                None,
                fx=3,
                fy=3,
                interpolation=cv2.INTER_NEAREST,
            ),
        )
    write_csv(
        os.path.join(loop_audit_dir, "loop_label_audit.csv"),
        sorted(loop_audit_rows, key=lambda row: (-row["represented_frames"], row["template_id"])),
    )
    print(f"[alignment overview] saved: {overview_path}")
    print(f"[loop label audit] saved: {loop_audit_dir}")


def apply_hierarchical_bank(stack_info, frame_assignments, local_to_global, transforms):
    apply_checkpoint = load_checkpoint("completed_aligned_stacks.pkl", stack_info) or {}
    transform_signature = tuple(sorted(
        (
            str(prefix),
            int(template_id),
            str(transform.get("state_label", "")),
            str(transform.get("loop_label", "")),
            float(transform.get("angle", 0)),
            float(transform.get("tx", 0)),
            float(transform.get("ty", 0)),
        )
        for template_id, transform in transforms.items()
        for prefix in ("global",)
    ))
    if apply_checkpoint.get("transform_signature") != transform_signature:
        apply_checkpoint = {}
    completed_stacks = set(apply_checkpoint.get("completed_stacks", []))
    assignments_by_stack = {}
    for row in frame_assignments.values():
        assignments_by_stack.setdefault(row["stack"], {})[int(row["frame"])] = row
    global_by_local_id = {
        int(row["local_template_id"]): row
        for row in local_to_global.values()
    }

    for stack_number, (stack_name, info) in enumerate(sorted(stack_info.items()), start=1):
        stack_assignments = assignments_by_stack.get(stack_name, {})
        if not stack_assignments:
            print(f"[apply] {stack_name}: no assignments, skipping")
            continue
        output_tif = os.path.join(out_dir, f"{stack_name}_aligned.tif")
        output_csv = os.path.join(out_dir, f"{stack_name}_template_bank_assignments.csv")
        if (
            SKIP_COMPLETED_OUTPUTS
            and stack_name in completed_stacks
            and os.path.isfile(output_tif)
            and os.path.isfile(output_csv)
        ):
            print(f"[checkpoint] aligned output already complete: {stack_name}")
            continue
        rows = []
        previews = []
        with tifffile.TiffFile(info["crop_path"]) as tif, tifffile.TiffWriter(output_tif, bigtiff=False) as writer:
            for frame_idx, page in enumerate(tqdm(tif.pages, desc=f"Apply global bank {stack_number}/{len(stack_info)}")):
                frame = ensure_gray(page.asarray())
                head_angle_status = info["head_angle_status_by_frame"].get(
                    frame_idx,
                    "missing_head_angle_row",
                )
                if head_angle_status.lower() != HEAD_ANGLE_REQUIRED_STATUS:
                    writer.write(np.zeros_like(frame), contiguous=True)
                    rows.append({
                        "stack": stack_name,
                        "frame": frame_idx,
                        "global_key": global_key(stack_name, frame_idx),
                        "head_angle_status": head_angle_status,
                        "ria_align_status": "skipped_head_angle_status",
                        "output_is_black_frame": 1,
                    })
                    continue
                assignment = stack_assignments.get(frame_idx)
                if assignment is None:
                    writer.write(np.zeros_like(frame), contiguous=True)
                    rows.append({
                        "stack": stack_name,
                        "frame": frame_idx,
                        "global_key": global_key(stack_name, frame_idx),
                        "head_angle_status": head_angle_status,
                        "ria_align_status": "missing_local_assignment",
                        "output_is_black_frame": 1,
                    })
                    continue
                if int(float(assignment.get("dropped_local_coverage_tail", 0) or 0)):
                    writer.write(np.zeros_like(frame), contiguous=True)
                    rows.append({
                        **assignment,
                        "head_angle_status": head_angle_status,
                        "ria_align_status": "dropped_local_coverage_tail",
                        "output_is_black_frame": 1,
                    })
                    continue
                local_template_id = int(assignment["local_template_id"])
                global_assignment = global_by_local_id.get(local_template_id)
                if global_assignment is None:
                    writer.write(np.zeros_like(frame), contiguous=True)
                    rows.append({
                        **assignment,
                        "head_angle_status": head_angle_status,
                        "ria_align_status": "missing_global_assignment",
                        "output_is_black_frame": 1,
                    })
                    continue
                if not int(float(global_assignment.get("global_template_retained", 1) or 0)):
                    writer.write(np.zeros_like(frame), contiguous=True)
                    row = dict(assignment)
                    row.update({
                        key: value
                        for key, value in global_assignment.items()
                        if key.startswith("global_")
                    })
                    row.update({
                        "head_angle_status": head_angle_status,
                        "ria_align_status": "dropped_global_coverage_tail",
                        "output_is_black_frame": 1,
                    })
                    rows.append(row)
                    continue
                global_template_id = int(global_assignment["global_template_id"])
                transform = transforms[global_template_id]
                if transform["state_label"] == "no_ria_visible":
                    writer.write(np.zeros_like(frame), contiguous=True)
                    row = dict(assignment)
                    row.update({
                        key: value
                        for key, value in global_assignment.items()
                        if key.startswith("global_")
                    })
                    row.update({
                        "global_template_id": global_template_id,
                        "global_template_stack": global_assignment["template_stack"],
                        "global_template_frame": global_assignment["template_frame"],
                        "head_angle_status": head_angle_status,
                        "ria_align_status": "skipped_no_ria_visible",
                        "output_is_black_frame": 1,
                        "template_manual_angle_deg": transform["angle"],
                        "template_manual_tx": transform["tx"],
                        "template_manual_ty": transform["ty"],
                        "template_match_scale_not_applied": transform["match_scale"],
                        "template_loop_label": transform["loop_label"],
                        "template_state_label": transform["state_label"],
                        "template_manual_alignment_skipped": transform.get("manual_alignment_skipped", 0),
                    })
                    rows.append(row)
                    continue
                frame_to_local = warp_frame(frame, warp_from_row(assignment, "local_ecc_"))
                frame_to_global = warp_frame(
                    frame_to_local,
                    warp_from_row(global_assignment, "global_ecc_"),
                )
                # match_scale is deliberately excluded from final crop transformation.
                aligned = transform_image(
                    frame_to_global,
                    transform["angle"],
                    transform["tx"],
                    transform["ty"],
                    scale=1.0,
                )
                writer.write(aligned, contiguous=True)
                if len(previews) < PREVIEW_TILE_COUNT:
                    previews.append(aligned)
                row = dict(assignment)
                row.update({
                    key: value
                    for key, value in global_assignment.items()
                    if key.startswith("global_")
                })
                row.update({
                    "global_template_id": global_template_id,
                    "global_template_stack": global_assignment["template_stack"],
                    "global_template_frame": global_assignment["template_frame"],
                    "head_angle_status": head_angle_status,
                    "ria_align_status": "ok",
                    "output_is_black_frame": 0,
                    "template_manual_angle_deg": transform["angle"],
                    "template_manual_tx": transform["tx"],
                    "template_manual_ty": transform["ty"],
                    "template_match_scale_not_applied": transform["match_scale"],
                    "template_loop_label": transform["loop_label"],
                    "template_state_label": transform["state_label"],
                    "template_manual_alignment_skipped": transform.get("manual_alignment_skipped", 0),
                })
                rows.append(row)
        write_csv(output_csv, rows)
        make_preview(previews, os.path.join(preview_dir, f"{stack_name}_preview.jpg"))
        completed_stacks.add(stack_name)
        save_checkpoint(
            "completed_aligned_stacks.pkl",
            {
                "completed_stacks": sorted(completed_stacks),
                "transform_signature": transform_signature,
            },
            stack_info,
        )
        print(f"[apply] saved: {output_tif}")


def main():
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(preview_dir, exist_ok=True)
    os.makedirs(checkpoint_dir, exist_ok=True)
    reset_global_annotations_if_requested()
    stack_info, shape = load_stack_frames()
    if not stack_info:
        print(f"No crop TIFF stacks found under RUN_ID={RUN_ID}")
        return
    total_frames = sum(info["n_frames"] for info in stack_info.values())
    valid_frames = sum(len(info["valid_frames"]) for info in stack_info.values())
    print(f"Found {total_frames} frame(s) from {len(stack_info)} stack(s), common shape={shape}")
    print(
        f"Head-angle filter: {valid_frames}/{total_frames} frame(s) "
        f"have status={HEAD_ANGLE_REQUIRED_STATUS}; all other frames will be zero"
    )
    print(f"ECC matching: {MATCH_WORKERS} worker threads, OpenCV internal threads={cv2.getNumThreads()}")
    print(
        "Gamepad: "
        + (
            "connected"
            if read_gamepad() is not None
            else "not detected (mouse controls remain available)"
        )
    )
    print(
        f"Template thresholds: local={LOCAL_TEMPLATE_MATCH_THRESHOLD:.2f}, "
        f"global={GLOBAL_TEMPLATE_MATCH_THRESHOLD:.2f}"
    )
    print(
        "Local bank selection: unlimited candidate templates, retain the largest classes "
        f"covering at least {LOCAL_TEMPLATE_FRAME_COVERAGE:.0%} of matched frames"
    )
    print(
        "Global bank selection: retain the largest classes covering at least "
        f"{GLOBAL_TEMPLATE_FRAME_COVERAGE:.0%} of represented frames"
    )
    print(f"ECC matching area: ellipse drawn on all-frame max intensity; remove soma={REMOVE_SOMA_FOR_MATCHING}")

    match_roi = load_or_draw_match_roi(stack_info, shape)

    local_templates, frame_assignments = build_local_banks(stack_info, shape, match_roi)
    print(f"Built {len(local_templates)} local template(s)")
    write_csv(os.path.join(out_dir, "all_frame_local_assignments.csv"), list(frame_assignments.values()))
    if not local_templates:
        print(f"No status={HEAD_ANGLE_REQUIRED_STATUS} frames with crop JPG input were available; stopping")
        return

    global_templates, local_to_global = build_global_bank_from_local_templates(
        local_templates,
        match_roi,
        stack_info,
    )
    print(f"Built {len(global_templates)} global template class(es)")
    write_csv(os.path.join(out_dir, "local_template_global_assignments.csv"), list(local_to_global.values()))
    save_global_template_frame_distribution(global_templates)
    redo_selected_templates_if_requested(stack_info)

    reference_setup = load_or_create_reference_setup(global_templates, stack_info)
    reference_id = int(reference_setup["reference_id"])
    reference_transform = reference_setup["reference_transform"]
    circles = reference_setup["reference_circles"]
    print(
        "[reference] using oriented reference and circles from "
        f"{reference_setup['reference_stack']} frame {reference_setup['reference_frame']}"
    )

    transform_checkpoint = load_checkpoint("manual_template_transforms.pkl", stack_info) or {}
    transforms = annotate_and_align_templates(
        global_templates,
        reference_id,
        reference_transform,
        circles,
        match_roi,
        existing_results=transform_checkpoint.get("transforms", {}),
        stack_info=stack_info,
        reference_image_override=reference_transform["image"],
    )

    save_template_alignment_overview(global_templates, transforms, circles)
    save_reference_metadata(reference_id, reference_transform["image"], circles, global_templates, transforms)
    save_frame_label_manifest(frame_assignments, local_to_global, transforms)
    apply_hierarchical_bank(stack_info, frame_assignments, local_to_global, transforms)
    print(f"Completed global template-bank alignment: {out_dir}")


if __name__ == "__main__":
    main()
