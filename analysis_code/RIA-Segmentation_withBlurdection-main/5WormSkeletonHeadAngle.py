"""
Post-process whole-worm masks into skeleton centerlines and head angles.

Inputs per stack/video:
- results/<RUN_ID>/03_worm_segmentation/<stack_name>/masks/*_worm_mask.png
- results/<RUN_ID>/02_tiff_jpg/<stack_name>/*.jpg

Outputs per stack/video:
- 05_worm_head_angle/<stack_name>/head_angles.csv
- 05_worm_head_angle/<stack_name>/overlays/*.jpg

On the first usable frame of each stack, click the worm head endpoint once.
Later frames orient the skeleton path by temporal continuity.
"""
import csv
import os
import sys
import time
from bisect import bisect_left
from collections import deque

import cv2
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage as ndi
from skimage.measure import label, regionprops
from skimage.morphology import medial_axis, remove_small_holes, remove_small_objects, skeletonize
from tqdm import tqdm


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260529"

JPG_SUBDIR = "02_tiff_jpg"
WORM_SEG_SUBDIR = "03_worm_segmentation"
WORM_SKEL_SUBDIR = "05_worm_head_angle"
RIA_ANCHOR_SUBDIR = "04_ria_head_anchor"

parent_video_dir = os.path.join(RESULTS_ROOT, RUN_ID, JPG_SUBDIR)
worm_seg_dir = os.path.join(RESULTS_ROOT, RUN_ID, WORM_SEG_SUBDIR)
worm_skel_dir = os.path.join(RESULTS_ROOT, RUN_ID, WORM_SKEL_SUBDIR)
ria_anchor_dir = os.path.join(RESULTS_ROOT, RUN_ID, RIA_ANCHOR_SUBDIR)

MIN_MASK_PIXELS = 500
MIN_SKELETON_PIXELS = 20
HEAD_TANGENT_PIXELS = 30
OVERLAY_INTERVAL = 50
WRITE_OVERLAYS = True
FAST_MODE = True
REQUIRE_CURRENT_RIA_ANCHOR = True
OVERWRITE_EXISTING = False
COMPLETE_MARKER = ".complete"
PROGRESS_UPDATE_INTERVAL_SEC = 0.5
SHOW_FRAME_PROGRESS = False


NEIGHBORS_8 = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]


class SingleLineProgress:
    def __init__(self, label, total, update_interval=PROGRESS_UPDATE_INTERVAL_SEC):
        self.label = label
        self.total = max(int(total), 1)
        self.count = 0
        self.update_interval = update_interval
        self.last_update = 0.0
        self.last_len = 0

    def update(self, status=None, frame=None, force=False):
        self.count += 1
        if not SHOW_FRAME_PROGRESS:
            return
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
        text = " | ".join(parts)
        pad = " " * max(0, self.last_len - len(text))
        sys.stdout.write(text + pad)
        sys.stdout.flush()
        self.last_len = len(text)

    def close(self):
        if not SHOW_FRAME_PROGRESS:
            return
        if self.last_len:
            sys.stdout.write("\r" + " " * self.last_len + "\r")
            sys.stdout.flush()
            self.last_len = 0


def natural_frame_names(frame_dir):
    if not os.path.isdir(frame_dir):
        return []
    names = [
        n for n in os.listdir(frame_dir)
        if os.path.splitext(n)[1].lower() in (".jpg", ".jpeg") and os.path.splitext(n)[0].isdigit()
    ]
    return sorted(names, key=lambda n: int(os.path.splitext(n)[0]))


def mask_names(mask_dir):
    if not os.path.isdir(mask_dir):
        return []
    names = [
        n for n in os.listdir(mask_dir)
        if n.endswith("_worm_mask.png") and n[:6].isdigit()
    ]
    return sorted(names, key=lambda n: int(n[:6]))


def read_mask(path):
    mask = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return None
    return mask > 0


def load_ria_head_anchors(stack_name):
    csv_path = os.path.join(ria_anchor_dir, f"{stack_name}_ria_anchor.csv")
    anchors = {}
    if not os.path.exists(csv_path):
        return anchors
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                frame = int(row["frame"])
                x = float(row["centroid_x"])
                y = float(row["centroid_y"])
            except (KeyError, TypeError, ValueError):
                continue
            anchors[frame] = (x, y)
    print(f"Loaded {len(anchors)} RIA/head anchor(s): {csv_path}")
    return anchors


def nearest_anchor(frame_idx, anchor_frames, anchors):
    if not anchor_frames:
        return None, None
    pos = bisect_left(anchor_frames, frame_idx)
    candidates = []
    if pos < len(anchor_frames):
        candidates.append(anchor_frames[pos])
    if pos > 0:
        candidates.append(anchor_frames[pos - 1])
    nearest_frame = min(candidates, key=lambda f: abs(f - frame_idx))
    return nearest_frame, anchors[nearest_frame]


def largest_component(mask):
    mask = remove_small_objects(mask.astype(bool), min_size=MIN_MASK_PIXELS)
    labeled = label(mask)
    props = regionprops(labeled)
    if not props:
        return None, None
    largest = max(props, key=lambda p: p.area)
    return labeled == largest.label, largest


def preprocess_mask(mask):
    mask = mask.astype(bool)
    if not np.any(mask):
        return mask

    filled = remove_small_holes(mask, area_threshold=500)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    larger_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask_u8 = filled.astype(np.uint8)
    closed = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)
    closed_again = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, larger_kernel)
    blurred = ndi.gaussian_filter(closed_again.astype(np.float32), sigma=3.0)
    blurred = ndi.gaussian_filter(blurred, sigma=2.0)
    smoothed = blurred >= 0.4
    return smoothed


def skeleton_degrees(skel):
    degrees = np.zeros(skel.shape, dtype=np.uint8)
    ys, xs = np.where(skel)
    for y, x in zip(ys, xs):
        count = 0
        for dy, dx in NEIGHBORS_8:
            yy, xx = y + dy, x + dx
            if 0 <= yy < skel.shape[0] and 0 <= xx < skel.shape[1] and skel[yy, xx]:
                count += 1
        degrees[y, x] = count
    return degrees


def skeleton_points(skel):
    ys, xs = np.where(skel)
    return list(zip(ys.tolist(), xs.tolist()))


def prune_to_largest_skeleton_component(skel):
    labeled, count = ndi.label(skel, structure=np.ones((3, 3), dtype=np.uint8))
    if count == 0:
        return skel
    sizes = ndi.sum(skel, labeled, index=np.arange(1, count + 1))
    largest_label = int(np.argmax(sizes)) + 1
    return labeled == largest_label


def graph_neighbors(point, skel):
    y, x = point
    for dy, dx in NEIGHBORS_8:
        yy, xx = y + dy, x + dx
        if 0 <= yy < skel.shape[0] and 0 <= xx < skel.shape[1] and skel[yy, xx]:
            yield yy, xx


def bfs_farthest(start, skel):
    queue = deque([start])
    parent = {start: None}
    dist = {start: 0}
    farthest = start
    while queue:
        point = queue.popleft()
        if dist[point] > dist[farthest]:
            farthest = point
        for nxt in graph_neighbors(point, skel):
            if nxt not in parent:
                parent[nxt] = point
                dist[nxt] = dist[point] + 1
                queue.append(nxt)
    return farthest, parent, dist


def shortest_path_between(start, end, skel):
    queue = deque([start])
    parent = {start: None}
    while queue:
        point = queue.popleft()
        if point == end:
            break
        for nxt in graph_neighbors(point, skel):
            if nxt not in parent:
                parent[nxt] = point
                queue.append(nxt)
    if end not in parent:
        return []
    path = []
    point = end
    while point is not None:
        path.append(point)
        point = parent[point]
    path.reverse()
    return path


def extract_centerline(mask):
    clean_mask, props = largest_component(mask)
    if clean_mask is None:
        return None
    processed_mask = preprocess_mask(clean_mask)
    if not np.any(processed_mask):
        processed_mask = clean_mask
    if FAST_MODE:
        skel = skeletonize(processed_mask)
    else:
        skel = medial_axis(processed_mask)
    if not np.any(skel):
        skel = skeletonize(clean_mask)
    skel = prune_to_largest_skeleton_component(skel)
    points = skeleton_points(skel)
    if len(points) < MIN_SKELETON_PIXELS:
        return None

    degrees = skeleton_degrees(skel)
    endpoints = list(zip(*np.where(skel & (degrees == 1))))
    branchpoints = list(zip(*np.where(skel & (degrees > 2))))

    if len(endpoints) >= 2:
        best_path = []
        for start in endpoints:
            farthest, parent, dist = bfs_farthest(start, skel)
            endpoint_distances = [(dist[p], p) for p in endpoints if p in dist and p != start]
            if not endpoint_distances:
                continue
            _, end = max(endpoint_distances)
            path = shortest_path_between(start, end, skel)
            if len(path) > len(best_path):
                best_path = path
    else:
        start = points[0]
        a, _, _ = bfs_farthest(start, skel)
        b, _, _ = bfs_farthest(a, skel)
        best_path = shortest_path_between(a, b, skel)

    if len(best_path) < MIN_SKELETON_PIXELS:
        return None

    return {
        "mask": clean_mask,
        "processed_mask": processed_mask,
        "props": props,
        "skeleton": skel,
        "degrees": degrees,
        "endpoints": endpoints,
        "branchpoints": branchpoints,
        "path_yx": best_path,
    }


def point_yx_to_xy(point):
    y, x = point
    return float(x), float(y)


def orient_path(path, head_xy=None):
    if not path:
        return path
    start_xy = np.array(point_yx_to_xy(path[0]))
    end_xy = np.array(point_yx_to_xy(path[-1]))
    if head_xy is None:
        return path
    head_xy = np.array(head_xy, dtype=float)
    if np.linalg.norm(end_xy - head_xy) < np.linalg.norm(start_xy - head_xy):
        return list(reversed(path))
    return path


def three_point_angle(p1, p2, p3):
    v1 = p1 - p2
    v2 = p3 - p2
    mag1 = np.linalg.norm(v1)
    mag2 = np.linalg.norm(v2)
    if mag1 == 0 or mag2 == 0:
        return None
    cos_angle = np.dot(v1, v2) / (mag1 * mag2)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def ria_anchor_head_angle_from_path(path, anchor_xy, body_pixels=HEAD_TANGENT_PIXELS):
    if len(path) < 3 or anchor_xy is None:
        return None

    points_xy = np.array([point_yx_to_xy(point) for point in path], dtype=float)
    anchor_xy = np.array(anchor_xy, dtype=float)
    anchor_idx = int(np.argmin(np.linalg.norm(points_xy - anchor_xy, axis=1)))

    head = np.array(point_yx_to_xy(path[0]))
    anchor_on_path = points_xy[anchor_idx]
    ria_to_head_straight_distance = float(np.linalg.norm(head - anchor_xy))
    if anchor_idx > 0:
        ria_to_head_skeleton_distance = float(
            np.linalg.norm(np.diff(points_xy[:anchor_idx + 1], axis=0), axis=1).sum()
        )
    else:
        ria_to_head_skeleton_distance = 0.0
    body_idx = min(len(points_xy) - 1, max(anchor_idx + body_pixels, 1))
    if body_idx == anchor_idx:
        body_idx = len(points_xy) - 1
    body = points_xy[body_idx]

    angle = three_point_angle(head, anchor_on_path, body)
    if angle is None:
        return None
    deviation = abs(180.0 - angle)

    v1 = anchor_on_path - head
    v2 = body - anchor_on_path
    cross_z = v1[0] * v2[1] - v1[1] * v2[0]
    signed_deviation = deviation if cross_z >= 0 else -deviation
    return {
        "angle_deg": float(signed_deviation),
        "abs_angle_deg": float(abs(signed_deviation)),
        "raw_three_point_angle_deg": float(angle),
        "head": head,
        "anchor_on_path": anchor_on_path,
        "body": body,
        "anchor_path_index": anchor_idx,
        "body_path_index": int(body_idx),
        "ria_to_head_straight_distance_px": ria_to_head_straight_distance,
        "ria_to_head_skeleton_distance_px": ria_to_head_skeleton_distance,
    }


def draw_overlay(image, analysis, path, angle_result, anchor_xy, out_path):
    overlay = image.copy()
    mask = analysis["mask"]
    overlay[mask] = cv2.addWeighted(overlay[mask], 0.55, np.full_like(overlay[mask], (0, 180, 0)), 0.45, 0)
    processed_mask = analysis.get("processed_mask")
    if processed_mask is not None:
        boundary = processed_mask & ~ndi.binary_erosion(processed_mask)
        overlay[boundary] = (0, 128, 255)

    ys, xs = np.where(analysis["skeleton"])
    overlay[ys, xs] = (255, 0, 0)
    for y, x in path:
        cv2.circle(overlay, (x, y), 1, (255, 255, 0), -1)

    if angle_result is not None:
        angle_deg = angle_result["angle_deg"]
        head = angle_result["head"]
        anchor_on_path = angle_result["anchor_on_path"]
        body = angle_result["body"]
        hx, hy = int(round(head[0])), int(round(head[1]))
        axp, ayp = int(round(anchor_on_path[0])), int(round(anchor_on_path[1]))
        bx, by = int(round(body[0])), int(round(body[1]))
        cv2.circle(overlay, (hx, hy), 6, (0, 0, 255), -1)
        cv2.circle(overlay, (axp, ayp), 5, (0, 165, 255), -1)
        cv2.circle(overlay, (bx, by), 5, (255, 255, 0), -1)
        cv2.line(overlay, (hx, hy), (axp, ayp), (0, 255, 255), 2)
        cv2.line(overlay, (axp, ayp), (bx, by), (0, 255, 255), 2)
        cv2.putText(overlay, f"RIA head angle {angle_deg:.1f}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    if anchor_xy is not None:
        ax, ay = int(round(anchor_xy[0])), int(round(anchor_xy[1]))
        cv2.drawMarker(overlay, (ax, ay), (0, 165, 255), markerType=cv2.MARKER_CROSS, markerSize=16, thickness=2)
        cv2.putText(overlay, "RIA anchor", (ax + 8, ay), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)

    cv2.imwrite(out_path, overlay)


def analyze_stack(stack_name):
    mask_dir = os.path.join(worm_seg_dir, stack_name, "masks")
    image_dir = os.path.join(parent_video_dir, stack_name)
    output_dir = os.path.join(worm_skel_dir, stack_name)
    overlay_dir = os.path.join(output_dir, "overlays")
    csv_path = os.path.join(output_dir, "head_angles.csv")
    complete_path = os.path.join(output_dir, COMPLETE_MARKER)
    if (
        not OVERWRITE_EXISTING
        and os.path.exists(csv_path)
        and os.path.exists(complete_path)
    ):
        print(f"[skip] {stack_name}: head_angles.csv already exists")
        return
    os.makedirs(overlay_dir, exist_ok=True)

    names = mask_names(mask_dir)
    if not names:
        print(f"No masks found for {stack_name}")
        return

    anchors = load_ria_head_anchors(stack_name)
    rows = []
    status_counts = {}

    progress = SingleLineProgress(f"Skeleton {stack_name}", len(names))
    try:
        for name in names:
            frame_idx = int(name[:6])
            anchor_xy = anchors.get(frame_idx)
            anchor_frame = frame_idx if anchor_xy is not None else None
            if anchor_xy is None and REQUIRE_CURRENT_RIA_ANCHOR:
                rows.append({"frame": frame_idx, "status": "missing_ria_anchor"})
                status_counts["missing_ria_anchor"] = status_counts.get("missing_ria_anchor", 0) + 1
                progress.update(status="missing_ria_anchor", frame=frame_idx)
                continue

            mask_path = os.path.join(mask_dir, name)
            mask = read_mask(mask_path)
            if mask is None:
                rows.append({"frame": frame_idx, "status": "missing_input"})
                status_counts["missing_input"] = status_counts.get("missing_input", 0) + 1
                progress.update(status="missing_input", frame=frame_idx)
                continue

            analysis = extract_centerline(mask)
            if analysis is None:
                rows.append({"frame": frame_idx, "status": "no_centerline"})
                status_counts["no_centerline"] = status_counts.get("no_centerline", 0) + 1
                progress.update(status="no_centerline", frame=frame_idx)
                continue

            head_reference_xy = anchor_xy
            head_source = "ria_anchor"
            path = orient_path(analysis["path_yx"], head_reference_xy)
            angle_result = ria_anchor_head_angle_from_path(path, anchor_xy)
            if angle_result is None:
                rows.append({"frame": frame_idx, "status": "no_angle"})
                status_counts["no_angle"] = status_counts.get("no_angle", 0) + 1
                progress.update(status="no_angle", frame=frame_idx)
                continue

            head = angle_result["head"]
            anchor_on_path = angle_result["anchor_on_path"]
            body = angle_result["body"]
            tail = np.array(point_yx_to_xy(path[-1]))
            anchor_distance = float(np.linalg.norm(anchor_on_path - np.array(anchor_xy))) if anchor_xy is not None else ""
            props = analysis["props"]
            status = "looped_or_branched" if props.euler_number < 1 or len(analysis["branchpoints"]) > 0 else "ok"
            status_counts[status] = status_counts.get(status, 0) + 1

            rows.append({
                "frame": frame_idx,
                "status": status,
                "head_source": head_source,
                "ria_head_angle_deg": f"{angle_result['angle_deg']:.6f}",
                "ria_head_abs_angle_deg": f"{angle_result['abs_angle_deg']:.6f}",
                "raw_three_point_angle_deg": f"{angle_result['raw_three_point_angle_deg']:.6f}",
                "head_x": f"{head[0]:.3f}",
                "head_y": f"{head[1]:.3f}",
                "anchor_x": f"{anchor_xy[0]:.3f}" if anchor_xy is not None else "",
                "anchor_y": f"{anchor_xy[1]:.3f}" if anchor_xy is not None else "",
                "anchor_frame": int(anchor_frame) if anchor_frame is not None else "",
                "anchor_path_x": f"{anchor_on_path[0]:.3f}",
                "anchor_path_y": f"{anchor_on_path[1]:.3f}",
                "anchor_path_index": int(angle_result["anchor_path_index"]),
                "body_ref_x": f"{body[0]:.3f}",
                "body_ref_y": f"{body[1]:.3f}",
                "body_path_index": int(angle_result["body_path_index"]),
                "anchor_to_path_distance": f"{anchor_distance:.3f}" if anchor_xy is not None else "",
                "ria_to_head_straight_distance_px": f"{angle_result['ria_to_head_straight_distance_px']:.6f}",
                "ria_to_head_skeleton_distance_px": f"{angle_result['ria_to_head_skeleton_distance_px']:.6f}",
                "tail_x": f"{tail[0]:.3f}",
                "tail_y": f"{tail[1]:.3f}",
                "skeleton_pixels": int(analysis["skeleton"].sum()),
                "centerline_pixels": len(path),
                "endpoint_count": len(analysis["endpoints"]),
                "branchpoint_count": len(analysis["branchpoints"]),
                "euler_number": int(props.euler_number),
                "solidity": f"{float(props.solidity):.6f}",
            })

            if WRITE_OVERLAYS and frame_idx % OVERLAY_INTERVAL == 0:
                out_path = os.path.join(overlay_dir, f"{frame_idx:06d}_skeleton_overlay.jpg")
                image_path = os.path.join(image_dir, f"{frame_idx:06d}.jpg")
                image = cv2.imread(image_path)
                if image is not None:
                    draw_overlay(image, analysis, path, angle_result, anchor_xy, out_path)
            progress.update(status=status, frame=frame_idx)
    finally:
        progress.close()

    fieldnames = [
        "frame", "status", "head_source",
        "ria_head_angle_deg", "ria_head_abs_angle_deg", "raw_three_point_angle_deg",
        "head_x", "head_y", "anchor_x", "anchor_y", "anchor_frame",
        "anchor_path_x", "anchor_path_y", "anchor_path_index",
        "body_ref_x", "body_ref_y", "body_path_index", "anchor_to_path_distance",
        "ria_to_head_straight_distance_px", "ria_to_head_skeleton_distance_px",
        "tail_x", "tail_y",
        "skeleton_pixels", "centerline_pixels", "endpoint_count", "branchpoint_count",
        "euler_number", "solidity",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    with open(complete_path, "w", encoding="utf-8") as f:
        f.write(f"{stack_name}\ncompleted={len(rows)} frame(s)\n")
    summary = ", ".join(f"{key}={value}" for key, value in sorted(status_counts.items()))
    if summary:
        print(f"[summary] {stack_name}: {summary}")
    print(f"Saved: {csv_path}")


def completed_worm_segmentation_stacks():
    if not os.path.isdir(worm_seg_dir):
        return []
    stacks = []
    for name in sorted(os.listdir(worm_seg_dir)):
        stack_dir = os.path.join(worm_seg_dir, name)
        if not os.path.isdir(stack_dir):
            continue
        if os.path.exists(os.path.join(stack_dir, ".complete")) and os.path.isdir(os.path.join(stack_dir, "masks")):
            stacks.append(name)
    return stacks


def main():
    stacks = completed_worm_segmentation_stacks()
    if not stacks:
        print("No completed worm segmentation stacks found.")
        return
    for stack_name in stacks:
        analyze_stack(stack_name)


if __name__ == "__main__":
    main()
