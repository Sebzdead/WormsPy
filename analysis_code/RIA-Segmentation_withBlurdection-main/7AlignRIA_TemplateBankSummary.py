"""Summarize progress and outputs from 7AlignRIA_TemplateBankManual_all.py."""
import csv
import os
import pickle
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260529"
HEAD_ANGLE_SUBDIR = "05_worm_head_angle"
ALIGN_SUBDIR = "07_ria_template_bank_all_aligned"


def read_csv(path):
    if not os.path.isfile(path):
        return []
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_checkpoint(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "rb") as f:
            return pickle.load(f).get("payload")
    except (EOFError, OSError, pickle.UnpicklingError) as error:
        print(f"[warn] Could not read checkpoint {path}: {error}")
        return None


def format_seconds(seconds):
    if seconds is None:
        return "n/a"
    seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def templates_for_coverage(counts, fraction=0.90):
    counts = sorted((int(value) for value in counts if int(value) > 0), reverse=True)
    total = sum(counts)
    if not counts or total <= 0:
        return 0, 0, 0.0
    target = total * fraction
    cumulative = 0
    for number, count in enumerate(counts, start=1):
        cumulative += count
        if cumulative >= target:
            return number, cumulative, cumulative / total
    return len(counts), cumulative, cumulative / total


def write_csv(path, rows):
    if not rows:
        return
    fields = list(rows[0])
    extras = sorted({key for row in rows for key in row} - set(fields))
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields + extras)
        writer.writeheader()
        writer.writerows(rows)


def summarize():
    run_id = RUN_ID
    for index, arg in enumerate(sys.argv[1:]):
        if arg.startswith("--run-id="):
            run_id = arg.split("=", 1)[1].strip()
        elif arg == "--run-id" and index + 2 <= len(sys.argv[1:]):
            run_id = sys.argv[1:][index + 1].strip()
    run_dir = os.path.join(RESULTS_ROOT, run_id)
    head_dir = os.path.join(run_dir, HEAD_ANGLE_SUBDIR)
    align_dir = os.path.join(run_dir, ALIGN_SUBDIR)
    checkpoint_dir = os.path.join(align_dir, "checkpoints")
    report_dir = os.path.join(align_dir, "statistics")
    os.makedirs(report_dir, exist_ok=True)

    local = read_checkpoint(os.path.join(checkpoint_dir, "local_banks.pkl")) or {}
    global_bank = read_checkpoint(os.path.join(checkpoint_dir, "global_bank.pkl")) or {}
    manual = read_checkpoint(os.path.join(checkpoint_dir, "manual_template_transforms.pkl")) or {}
    completed_outputs = read_checkpoint(os.path.join(checkpoint_dir, "completed_aligned_stacks.pkl")) or {}

    local_templates = local.get("local_templates", [])
    frame_assignments = local.get("frame_assignments", {})
    completed_local = set(local.get("completed_stacks", []))
    global_templates = global_bank.get("global_templates", [])
    transforms = manual.get("transforms", {})
    completed_aligned = set(completed_outputs.get("completed_stacks", []))

    templates_by_stack = defaultdict(list)
    assignments_by_stack = defaultdict(list)
    for template in local_templates:
        templates_by_stack[template["stack"]].append(template)
    for assignment in frame_assignments.values():
        assignments_by_stack[assignment["stack"]].append(assignment)

    stack_names = set()
    if os.path.isdir(head_dir):
        stack_names.update(
            name for name in os.listdir(head_dir)
            if os.path.isdir(os.path.join(head_dir, name))
        )
    stack_names.update(templates_by_stack)

    rows = []
    total_statuses = Counter()
    for stack_name in sorted(stack_names):
        head_rows = read_csv(os.path.join(head_dir, stack_name, "head_angles.csv"))
        statuses = Counter(str(row.get("status", "")).strip() or "missing_status" for row in head_rows)
        total_statuses.update(statuses)
        templates = templates_by_stack.get(stack_name, [])
        assignments = assignments_by_stack.get(stack_name, [])
        counts = [int(template["count"]) for template in templates]
        n90, frames90, fraction90 = templates_for_coverage(counts)
        forced = sum(int(float(row.get("local_forced_low_cc", 0) or 0)) for row in assignments)
        dropped_singletons = sum(
            int(float(row.get("dropped_local_singleton", 0) or 0))
            for row in assignments
        )
        cc_values = [
            float(row["local_match_cc"])
            for row in assignments
            if str(row.get("local_match_cc", "")).strip()
        ]
        rows.append({
            "stack": stack_name,
            "total_frames": len(head_rows),
            "ok_frames": statuses.get("ok", 0),
            "non_ok_frames": len(head_rows) - statuses.get("ok", 0),
            "local_bank_complete": int(stack_name in completed_local),
            "local_templates": len(templates),
            "templates_for_90pct_frames": n90,
            "frames_covered_by_90pct_templates": frames90,
            "actual_coverage_fraction": round(fraction90, 6),
            "local_assignments": len(assignments),
            "local_forced_low_cc": forced,
            "dropped_local_singletons": dropped_singletons,
            "mean_local_cc": round(sum(cc_values) / len(cc_values), 6) if cc_values else "",
            "aligned_output_complete": int(stack_name in completed_aligned),
        })

    state_counts = Counter(
        transform.get("state_label", "unknown")
        for transform in transforms.values()
    )
    loop_counts = Counter(
        transform.get("loop_label", "unknown")
        for transform in transforms.values()
    )

    checkpoint_files = [
        os.path.join(checkpoint_dir, name)
        for name in os.listdir(checkpoint_dir)
        if name.endswith(".pkl")
    ] if os.path.isdir(checkpoint_dir) else []
    start_time = min((os.path.getctime(path) for path in checkpoint_files), default=None)
    latest_time = max((os.path.getmtime(path) for path in checkpoint_files), default=None)
    elapsed = latest_time - start_time if start_time is not None and latest_time is not None else None

    total_frames = sum(int(row["total_frames"]) for row in rows)
    ok_frames = sum(int(row["ok_frames"]) for row in rows)
    local_count = len(local_templates)
    global_count = len(global_templates)
    local_n90, local_frames90, local_fraction90 = templates_for_coverage(
        template["count"] for template in local_templates
    )
    global_n90, global_frames90, global_fraction90 = templates_for_coverage(
        template["count"] for template in global_templates
    )
    per_stack_n90 = [
        int(row["templates_for_90pct_frames"])
        for row in rows
        if int(row["local_bank_complete"])
    ]
    independent_n90_total = sum(per_stack_n90)
    mean_n90 = statistics.mean(per_stack_n90) if per_stack_n90 else 0
    median_n90 = statistics.median(per_stack_n90) if per_stack_n90 else 0
    min_n90 = min(per_stack_n90, default=0)
    max_n90 = max(per_stack_n90, default=0)

    lines = [
        f"RIA template-bank summary: RUN_ID={run_id}",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"Stacks: {len(rows)} total, {len(completed_local)} local-bank complete, "
        f"{len(completed_aligned)} aligned-output complete",
        f"Frames: {total_frames} total, {ok_frames} status=ok, {total_frames - ok_frames} excluded",
        f"Local templates: {local_count}; top {local_n90} cover "
        f"{local_frames90} frames ({local_fraction90:.2%})",
        f"Per-stack 90% templates: sum={independent_n90_total}, mean={mean_n90:.2f}, "
        f"median={median_n90:g}, range={min_n90}-{max_n90}",
        f"Pooled local templates for whole-group 90% coverage: {local_n90}",
        (
            f"Global templates: {global_count}; top {global_n90} cover "
            f"{global_frames90} frames ({global_fraction90:.2%})"
            if global_templates
            else "Global templates: not built yet; cross-video deduplicated 90% count unavailable"
        ),
        f"Manual template labels completed: {len(transforms)}/{global_count}",
        f"Observed checkpoint wall time: {format_seconds(elapsed)} "
        f"(estimated from first creation to latest checkpoint update)",
        "",
        "Head-angle statuses: " + ", ".join(f"{key}={value}" for key, value in total_statuses.most_common()),
        "State labels: " + (", ".join(f"{key}={value}" for key, value in state_counts.most_common()) or "none"),
        "Loop labels: " + (", ".join(f"{key}={value}" for key, value in loop_counts.most_common()) or "none"),
        "",
        "Per-stack:",
    ]
    for row in rows:
        lines.append(
            f"- {row['stack']}: frames={row['total_frames']}, ok={row['ok_frames']}, "
            f"local_templates={row['local_templates']}, templates_for_90pct={row['templates_for_90pct_frames']}, "
            f"local_complete={row['local_bank_complete']}, aligned_complete={row['aligned_output_complete']}"
        )

    report_path = os.path.join(report_dir, "template_bank_summary.txt")
    csv_path = os.path.join(report_dir, "template_bank_per_stack.csv")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    write_csv(csv_path, rows)
    print("\n".join(lines[:14]))
    print(f"\nSaved: {report_path}")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    summarize()
