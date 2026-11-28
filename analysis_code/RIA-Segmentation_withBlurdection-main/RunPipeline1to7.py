"""
Run pipeline steps 1-7 in order.

Default:
    python RunPipeline1to7.py

Useful options:
    python RunPipeline1to7.py --start 3 --end 7
    python RunPipeline1to7.py --only 4
    python RunPipeline1to7.py --dry-run

Each step writes a timestamped log under pipeline_logs/.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
LOG_DIR = SCRIPT_DIR / "pipeline_logs"
DEFAULT_PYTHON = r"C:\Users\34358\AppData\Local\Programs\Python\Python312\python.exe"

STEPS = [
    (1, "Convert TIFF folders to local stacks", "1ConvertTIFFtoStack.py"),
    (2, "Convert TIFF stacks to JPG frames", "2TIFF2JPG.py"),
    (3, "Segment whole worm", "3SegmentWorm.py"),
    (4, "Auto-crop RIA with SAM2", "4AutoCrop.py"),
    (5, "Skeletonize worm and compute head angle", "5WormSkeletonHeadAngle.py"),
    (6, "Convert RIA crop TIFFs to JPG", "6CropTIFF2JPG.py"),
    (7, "Align RIA crops with ECC", "7AlignRIA_ECC.py"),
]


def parse_step_list(text):
    steps = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            steps.update(range(int(lo), int(hi) + 1))
        else:
            steps.add(int(part))
    return steps


def selected_steps(args):
    valid = {step_num for step_num, _, _ in STEPS}
    if args.only:
        wanted = parse_step_list(args.only)
    else:
        wanted = {step for step in valid if args.start <= step <= args.end}
    unknown = sorted(wanted - valid)
    if unknown:
        raise ValueError(f"Unknown step number(s): {unknown}")
    return [step for step in STEPS if step[0] in wanted]


def log_name(step_num, script_name):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    stem = Path(script_name).stem
    return LOG_DIR / f"{timestamp}_step{step_num}_{stem}.log"


def run_step(step_num, description, script_name, python_exe, dry_run=False):
    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(script_path)

    command = [python_exe, str(script_path)]
    print(f"\n=== Step {step_num}: {description} ===")
    print("Command:", " ".join(command))

    if dry_run:
        return 0, None

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = log_name(step_num, script_name)
    start_time = time.time()

    env = os.environ.copy()
    env.setdefault("YOLO_CONFIG_DIR", str(SCRIPT_DIR / "Ultralytics"))
    env.setdefault("PYTHONUNBUFFERED", "1")

    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(f"Step {step_num}: {description}\n")
        log.write(f"Command: {' '.join(command)}\n")
        log.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        log.flush()

        process = subprocess.Popen(
            command,
            cwd=str(SCRIPT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
        )
        assert process.stdout is not None
        console_encoding = sys.stdout.encoding or "utf-8"
        for line in process.stdout:
            safe_line = line.encode(console_encoding, errors="replace").decode(console_encoding, errors="replace")
            print(safe_line, end="")
            log.write(line)
        return_code = process.wait()

        elapsed = time.time() - start_time
        log.write(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"Elapsed seconds: {elapsed:.1f}\n")
        log.write(f"Exit code: {return_code}\n")

    print(f"\n[step {step_num}] exit={return_code}, elapsed={elapsed:.1f}s")
    print(f"[step {step_num}] log: {log_path}")
    return return_code, log_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=7)
    parser.add_argument("--only", default="", help="Comma/range list, e.g. 3,4,7 or 3-5.")
    parser.add_argument("--python", default=DEFAULT_PYTHON if Path(DEFAULT_PYTHON).exists() else sys.executable, help="Python executable used to run each step.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--continue-on-fail", action="store_true")
    args = parser.parse_args()

    steps = selected_steps(args)
    print("Pipeline root:", SCRIPT_DIR)
    print("Python:", args.python)
    print("Selected steps:", ", ".join(str(step[0]) for step in steps))

    failures = []
    started = time.time()
    for step in steps:
        return_code, log_path = run_step(*step, python_exe=args.python, dry_run=args.dry_run)
        if return_code != 0:
            failures.append((step[0], step[2], return_code, log_path))
            if not args.continue_on_fail:
                print(f"\nStopping because step {step[0]} failed.")
                break

    elapsed = time.time() - started
    print("\n=== Pipeline Summary ===")
    print(f"Elapsed seconds: {elapsed:.1f}")
    if failures:
        print("Failures:")
        for step_num, script_name, return_code, log_path in failures:
            print(f"  step {step_num} {script_name}: exit={return_code}, log={log_path}")
        raise SystemExit(1)
    print("All selected steps finished successfully.")


if __name__ == "__main__":
    main()
