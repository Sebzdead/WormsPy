"""
Generate frame-status timeline heatmaps from existing 07_ria_aligned alignment CSVs.

This script does not rerun ECC and does not modify aligned TIFF stacks.
It only reads:
- results/<RUN_ID>/07_ria_aligned/*_alignment.csv

Outputs:
- results/<RUN_ID>/07_ria_aligned/status_timelines/<stack>_status_timeline.png
- results/<RUN_ID>/07_ria_aligned/status_timelines/all_stacks_status_timeline.png
"""
import argparse
import csv
import os

import cv2
import numpy as np


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260529"
ALIGNED_SUBDIR = "07_ria_aligned"


def status_color(status):
    colors = {
        "ok": (80, 220, 80),
        "classifier_bad": (60, 60, 230),
        "no_ria_mask": (230, 180, 40),
        "ecc_failed": (190, 60, 190),
        "unstable_warp": (60, 140, 230),
    }
    return colors.get(status, (150, 150, 150))


def read_rows(csv_path):
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_status_timeline(rows, out_path, title=None, width=1400, row_height=24):
    if not rows:
        return
    n = len(rows)
    width = max(200, int(width))
    bar = np.zeros((row_height, width, 3), dtype=np.uint8)
    for x in range(width):
        idx = min(n - 1, int(x * n / width))
        bar[:, x, :] = status_color(rows[idx].get("status", ""))

    seen = []
    for row in rows:
        status = row.get("status", "")
        if status and status not in seen:
            seen.append(status)

    legend_h = 24 * max(1, int(np.ceil(len(seen) / 3)))
    title_h = 30 if title else 0
    canvas = np.zeros((title_h + row_height + legend_h + 8, width, 3), dtype=np.uint8)
    y = 0
    if title:
        cv2.putText(canvas, title, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        y += title_h
    canvas[y:y + row_height, :, :] = bar
    y += row_height + 8
    for i, status in enumerate(seen):
        col = i % 3
        row = i // 3
        x = col * (width // 3) + 8
        yy = y + row * 24
        cv2.rectangle(canvas, (x, yy), (x + 16, yy + 16), status_color(status), -1)
        cv2.putText(canvas, status, (x + 22, yy + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (230, 230, 230), 1, cv2.LINE_AA)
    cv2.imwrite(out_path, canvas)


def save_all_status_timeline(items, out_path, width=1400, row_height=14):
    if not items:
        return
    left = 330
    header = 30
    legend_h = 80
    height = header + len(items) * row_height + legend_h
    canvas = np.zeros((height, left + width, 3), dtype=np.uint8)
    cv2.putText(canvas, "Alignment frame status by stack", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    y = header
    for stack_name, rows in items:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=RUN_ID)
    parser.add_argument("--width", type=int, default=1400)
    args = parser.parse_args()

    aligned_dir = os.path.join(RESULTS_ROOT, args.run_id, ALIGNED_SUBDIR)
    status_dir = os.path.join(aligned_dir, "status_timelines")
    os.makedirs(status_dir, exist_ok=True)

    csv_paths = sorted(
        os.path.join(aligned_dir, name)
        for name in os.listdir(aligned_dir)
        if name.endswith("_alignment.csv")
    ) if os.path.isdir(aligned_dir) else []
    if not csv_paths:
        print(f"No alignment CSV files found in: {aligned_dir}")
        return

    items = []
    for csv_path in csv_paths:
        stack_name = os.path.basename(csv_path)[:-len("_alignment.csv")]
        rows = read_rows(csv_path)
        if not rows:
            continue
        ok = sum(1 for row in rows if row.get("status") == "ok")
        dropped = len(rows) - ok
        out_path = os.path.join(status_dir, f"{stack_name}_status_timeline.png")
        save_status_timeline(
            rows,
            out_path,
            title=f"{stack_name}: ok={ok}/{len(rows)}, dropped={dropped}/{len(rows)}",
            width=args.width,
        )
        items.append((stack_name, rows))
        print(f"Saved: {out_path}")

    overview_path = os.path.join(status_dir, "all_stacks_status_timeline.png")
    save_all_status_timeline(items, overview_path, width=args.width)
    print(f"Saved all-stack status timeline: {overview_path}")


if __name__ == "__main__":
    main()
