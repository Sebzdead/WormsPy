"""
Analyze nrv/nrD residual and PCA common signals against head angle.

Inputs:
- results/<RUN_ID>/08_roi_intensity/*_roi_intensity.csv

Outputs:
- results/<RUN_ID>/10_nrv_nrd_common_signal/*

Lag convention:
- lag > 0 means ROI intensity is shifted later:
  corr(head_angle[t], roi_intensity[t + lag])
"""
import argparse
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "20260529"
DEFAULT_FPS = 12.89

ROI_INPUT_SUBDIR = "08_roi_intensity"
OUTPUT_SUBDIR = "10_nrv_nrd_common_signal"

RAW_ANGLE_COLUMN = "ria_head_angle_deg"
ANGLE_COLUMN = "loop_normalized_head_angle_deg"
LOOP_LABEL_COLUMN = "template_loop_label"
LOOP_REFERENCE_LABEL = "loop_left"
LOOP_FLIPPED_LABEL = "loop_right"
ROI_LABELS = ("nrv_residual", "nrD_residual", "common_signal")
SOURCE_ROI_LABELS = ("nrv", "nrD")
ROI_INTENSITY_METRIC = "brightest5_mean_intensity"
ROI_COLUMN_RE = re.compile(
    rf"^{ROI_INTENSITY_METRIC}_(nrv|nrD)(?:_|$)"
)
BACKGROUND_COLUMN = "background_median_intensity"


def pearson_corr(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]
    if len(x) < 3:
        return np.nan, int(len(x))
    if np.nanstd(x) == 0 or np.nanstd(y) == 0:
        return np.nan, int(len(x))
    return float(np.corrcoef(x, y)[0, 1]), int(len(x))


def stack_name_from_intensity_csv(path):
    name = os.path.basename(path)
    suffix = "_roi_intensity.csv"
    return name[:-len(suffix)] if name.endswith(suffix) else os.path.splitext(name)[0]


def collect_intensity_csvs(input_dir):
    if not os.path.isdir(input_dir):
        return []
    return sorted(
        os.path.join(input_dir, name)
        for name in os.listdir(input_dir)
        if name.endswith("_roi_intensity.csv")
    )


def add_grouped_roi_columns(df):
    if BACKGROUND_COLUMN not in df.columns:
        return []
    background = pd.to_numeric(df[BACKGROUND_COLUMN], errors="coerce").replace(0, np.nan)
    grouped = {label: [] for label in SOURCE_ROI_LABELS}
    for col in df.columns:
        match = ROI_COLUMN_RE.match(col)
        if match:
            grouped[match.group(1)].append(col)

    found = []
    for label, cols in grouped.items():
        if not cols:
            continue
        out_col = f"roi_signal_{label}"
        brightest5 = df[cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)
        df[out_col] = (brightest5 - background) / background
        found.append(label)
    return found


def add_pca_common_and_residual_signals(df):
    required = ["roi_signal_nrv", "roi_signal_nrD"]
    if any(column not in df.columns for column in required):
        return None
    raw = df[required].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(raw).all(axis=1)
    if valid.sum() < 3:
        return None
    means = np.nanmean(raw[valid], axis=0)
    centered = raw - means
    fit = centered[valid]
    if not np.isfinite(fit).all():
        return None
    _u, singular_values, vt = np.linalg.svd(fit - fit.mean(axis=0), full_matrices=False)
    pc1 = vt[0].astype(float)
    if pc1.sum() < 0:
        pc1 *= -1
    scores = centered @ pc1
    common_projection = scores[:, None] * pc1[None, :]
    residual = centered - common_projection
    df["roi_signal_nrv_residual"] = residual[:, 0]
    df["roi_signal_nrD_residual"] = residual[:, 1]
    df["roi_signal_common_signal"] = scores
    explained = float(singular_values[0] ** 2 / np.sum(singular_values ** 2))
    return {
        "nrv_mean": float(means[0]),
        "nrd_mean": float(means[1]),
        "pc1_nrv_loading": float(pc1[0]),
        "pc1_nrd_loading": float(pc1[1]),
        "pc1_explained_variance_ratio": explained,
        "centered_nrv": centered[:, 0],
        "centered_nrd": centered[:, 1],
    }


def clean_dataframe(path):
    df = pd.read_csv(path)
    if "frame" not in df.columns:
        raise ValueError(f"No frame column: {path}")
    if RAW_ANGLE_COLUMN not in df.columns:
        raise ValueError(f"No {RAW_ANGLE_COLUMN} column: {path}")

    input_rows = len(df)
    if "head_angle_status" in df.columns:
        df = df[df["head_angle_status"].astype(str).str.lower() == "ok"].copy()
    status_ok_rows = len(df)

    df["frame"] = pd.to_numeric(df["frame"], errors="coerce")
    raw_angle = pd.to_numeric(df[RAW_ANGLE_COLUMN], errors="coerce")
    if LOOP_LABEL_COLUMN in df.columns:
        loop_labels = df[LOOP_LABEL_COLUMN].astype(str).str.strip().str.lower()
        flip_mask = loop_labels == LOOP_FLIPPED_LABEL
        reference_mask = loop_labels == LOOP_REFERENCE_LABEL
        unknown_mask = ~(flip_mask | reference_mask)
    else:
        flip_mask = pd.Series(False, index=df.index)
        reference_mask = pd.Series(False, index=df.index)
        unknown_mask = pd.Series(True, index=df.index)
    df[ANGLE_COLUMN] = raw_angle.where(~flip_mask, -raw_angle)
    loop_stats = {
        "loop_left": int(reference_mask.sum()),
        "loop_right_flipped": int(flip_mask.sum()),
        "loop_label_unknown": int(unknown_mask.sum()),
    }
    source_labels = add_grouped_roi_columns(df)
    pca_info = add_pca_common_and_residual_signals(df)
    labels = list(ROI_LABELS) if pca_info is not None else []
    keep_cols = ["frame", ANGLE_COLUMN] + [f"roi_signal_{label}" for label in labels]
    df = df[keep_cols].dropna(subset=["frame", ANGLE_COLUMN]).copy()
    df = df.sort_values("frame").reset_index(drop=True)
    return df, labels, input_rows, status_ok_rows, loop_stats, pca_info, source_labels


def smooth_angles_for_cycles(angles, window_frames=9, polyorder=2):
    angles = np.asarray(angles, dtype=float)
    if len(angles) < 3 or window_frames <= 1:
        return angles.copy()
    window = min(int(window_frames), len(angles) if len(angles) % 2 == 1 else len(angles) - 1)
    if window % 2 == 0:
        window -= 1
    minimum = int(polyorder) + 2
    if minimum % 2 == 0:
        minimum += 1
    if window < minimum:
        return angles.copy()
    return savgol_filter(angles, window_length=window, polyorder=int(polyorder), mode="interp")


def smooth_finite_contiguous_runs(values, frames, window_frames=5, polyorder=2):
    values = np.asarray(values, dtype=float)
    frames = np.asarray(frames, dtype=float)
    smoothed = values.copy()
    if len(values) < 3 or window_frames <= 1:
        return smoothed

    valid = np.isfinite(values) & np.isfinite(frames)
    run_start = None
    for idx in range(len(values) + 1):
        continues = (
            idx < len(values)
            and valid[idx]
            and (
                run_start is None
                or idx == run_start
                or frames[idx] == frames[idx - 1] + 1
            )
        )
        if continues:
            if run_start is None:
                run_start = idx
            continue
        if run_start is not None:
            run_end = idx
            smoothed[run_start:run_end] = smooth_angles_for_cycles(
                values[run_start:run_end],
                window_frames,
                polyorder,
            )
            run_start = idx if idx < len(values) and valid[idx] else None
    return smoothed


def make_smoothed_analysis_dataframe(df, labels, window_frames=5, polyorder=2):
    smoothed = df.copy()
    frames = smoothed["frame"].to_numpy(dtype=float)
    columns = [ANGLE_COLUMN] + [f"roi_signal_{label}" for label in labels]
    for column in columns:
        smoothed[column] = smooth_finite_contiguous_runs(
            smoothed[column].to_numpy(dtype=float),
            frames,
            window_frames,
            polyorder,
        )
    return smoothed


def directional_zero_crossings(angles, zero_tolerance=0.0):
    angles = np.asarray(angles, dtype=float)
    crossing_rows = []
    previous_sign = 0

    for idx, value in enumerate(angles):
        if not np.isfinite(value):
            continue
        if abs(value) <= zero_tolerance:
            sign = 0
        else:
            sign = 1 if value > 0 else -1

        if idx > 0 and previous_sign != 0 and sign != 0 and sign != previous_sign:
            direction = "rising" if previous_sign < sign else "falling"
            crossing_rows.append((idx, direction, value))

        if sign != 0:
            previous_sign = sign

    return crossing_rows


def half_cycle_slices(crossings, min_cycle_frames, max_cycle_frames):
    cycles = []
    rejected = []
    for start_row, end_row in zip(crossings, crossings[1:]):
        start, end = int(start_row[0]), int(end_row[0])
        length = end - start
        record = (len(cycles) + 1, start, end, f"{start_row[1]}_to_{end_row[1]}")
        if min_cycle_frames <= length <= max_cycle_frames:
            cycles.append(record)
        else:
            rejected.append({
                "start_row": start,
                "end_row": end,
                "cycle_n_frames": length,
                "reason": "too_short" if length < min_cycle_frames else "too_long",
            })
    return cycles, rejected


def mean_cycle_length(cycles):
    lengths = [end - start for _, start, end, _direction in cycles]
    if not lengths:
        return 0
    return int(round(float(np.mean(lengths))))


def corr_by_segments(stack_name, df, labels, cycles):
    rows = []
    for segment_id, start, end, cycle_direction in cycles:
        segment = df.iloc[start:end]
        angle = segment[ANGLE_COLUMN].to_numpy()
        finite_angle = angle[np.isfinite(angle)]
        max_head_angle = (
            float(finite_angle[np.argmax(np.abs(finite_angle))])
            if finite_angle.size
            else np.nan
        )
        max_abs_head_angle = float(np.nanmax(np.abs(angle)))
        for label in labels:
            roi_col = f"roi_signal_{label}"
            corr, n = pearson_corr(angle, segment[roi_col].to_numpy())
            rows.append({
                "stack": stack_name,
                "segment_id": segment_id,
                "segment_start_frame": int(segment["frame"].iloc[0]),
                "segment_end_frame": int(segment["frame"].iloc[-1]),
                "segment_n_frames": int(len(segment)),
                "half_cycle_direction": cycle_direction,
                "max_head_angle_deg": max_head_angle,
                "max_abs_head_angle_deg": max_abs_head_angle,
                "roi": label,
                "corr": corr,
                "n_valid": n,
            })
    return rows


def corr_by_segment_lag(stack_name, df, labels, cycles, lags, fps):
    rows = []
    for segment_id, start, end, cycle_direction in cycles:
        segment = df.iloc[start:end]
        angle = segment[ANGLE_COLUMN].to_numpy(dtype=float)
        for label in labels:
            roi = segment[f"roi_signal_{label}"].to_numpy(dtype=float)
            for lag in lags:
                if abs(lag) >= len(segment) - 2:
                    corr, n = np.nan, 0
                elif lag > 0:
                    x = angle[:-lag]
                    y = roi[lag:]
                    corr, n = pearson_corr(x, y)
                elif lag < 0:
                    x = angle[-lag:]
                    y = roi[:lag]
                    corr, n = pearson_corr(x, y)
                else:
                    corr, n = pearson_corr(angle, roi)
                rows.append({
                    "stack": stack_name,
                    "segment_id": segment_id,
                    "segment_start_frame": int(segment["frame"].iloc[0]),
                    "segment_end_frame": int(segment["frame"].iloc[-1]),
                    "segment_n_frames": int(len(segment)),
                    "half_cycle_direction": cycle_direction,
                    "roi": label,
                    "lag_frames": int(lag),
                    "lag_seconds": float(lag) / float(fps),
                    "corr": corr,
                    "n_valid": n,
                })
    return rows


def summarize_lag_rows(lag_rows):
    lag = pd.DataFrame(lag_rows)
    if lag.empty:
        return lag
    return (
        lag.groupby(["stack", "roi", "lag_frames"], as_index=False)
        .agg(
            lag_seconds=("lag_seconds", "first"),
            mean_corr=("corr", "mean"),
            sem_corr=("corr", lambda x: x.std(ddof=1) / np.sqrt(x.count()) if x.count() > 1 else np.nan),
            n_segments=("corr", "count"),
        )
    )


def save_stack_plots(stack_name, segment_rows, lag_rows, out_dir):
    segment_dir = os.path.join(out_dir, "segment_correlation")
    lag_dir = os.path.join(out_dir, "lag_correlation")
    os.makedirs(segment_dir, exist_ok=True)
    os.makedirs(lag_dir, exist_ok=True)
    seg = pd.DataFrame(segment_rows)
    lag = summarize_lag_rows(lag_rows)

    if not seg.empty:
        fig, ax_corr = plt.subplots(figsize=(10, 5))
        for label in ROI_LABELS:
            sub = seg[seg["roi"] == label]
            if sub.empty:
                continue
            ax_corr.plot(sub["segment_id"], sub["corr"], marker="o", label=label)
        ax_corr.axhline(0, color="black", linewidth=0.8)
        ax_corr.set_xlabel("Head-swing half-cycle")
        ax_corr.set_ylabel("Pearson r")
        ax_angle = ax_corr.twinx()
        angle_by_segment = seg.drop_duplicates("segment_id").sort_values("segment_id")
        ax_angle.plot(
            angle_by_segment["segment_id"],
            angle_by_segment["max_head_angle_deg"],
            color="black",
            linestyle="--",
            marker="x",
            label="Max head angle",
        )
        ax_angle.set_ylabel("Max head angle (deg)")
        ax_corr.set_title(
            f"{stack_name}: angle vs nrv/nrD residual and PCA common signals"
        )
        lines1, labels1 = ax_corr.get_legend_handles_labels()
        lines2, labels2 = ax_angle.get_legend_handles_labels()
        ax_corr.legend(lines1 + lines2, labels1 + labels2, loc="best")
        fig.tight_layout()
        fig.savefig(os.path.join(segment_dir, f"{stack_name}_segment_corr.png"), dpi=180)
        plt.close(fig)

    if not lag.empty:
        plt.figure(figsize=(10, 5))
        for label in ROI_LABELS:
            sub = lag[lag["roi"] == label]
            if sub.empty:
                continue
            x = sub["lag_seconds"].to_numpy(dtype=float)
            y = sub["mean_corr"].to_numpy(dtype=float)
            plt.plot(x, y, label=label)
            if sub["sem_corr"].notna().any():
                sem = sub["sem_corr"].to_numpy(dtype=float)
                plt.fill_between(x, y - sem, y + sem, alpha=0.15)
        plt.axhline(0, color="black", linewidth=0.8)
        plt.axvline(0, color="black", linewidth=0.8, linestyle="--")
        plt.xlabel("Lag (seconds): corr(loop-normalized angle[t], ROI[t + lag])")
        plt.ylabel("Mean Pearson r across half-cycles")
        plt.title(f"{stack_name}: half-cycle-averaged lag correlation")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(lag_dir, f"{stack_name}_lag_corr.png"), dpi=180)
        plt.close()


def save_cycle_segmentation_plot(stack_name, df, smoothed_angles, crossings, cycles, rejected, fps, out_dir):
    cycle_dir = os.path.join(out_dir, "cycle_segmentation")
    os.makedirs(cycle_dir, exist_ok=True)
    frames = df["frame"].to_numpy(dtype=float)
    times = frames / float(fps)
    angles = df[ANGLE_COLUMN].to_numpy(dtype=float)
    plt.figure(figsize=(14, 5))
    plt.plot(times, angles, color="gray", linewidth=0.8, alpha=0.55, label="Raw loop-normalized angle")
    plt.plot(times, smoothed_angles, color="black", linewidth=1.5, label="Smoothed angle used for cycles")
    plt.axhline(0, color="gray", linewidth=0.8, linestyle="--")

    for idx, (cycle_id, start, end, direction) in enumerate(cycles):
        color = "#d8ecff" if idx % 2 == 0 else "#e6f6df"
        plt.axvspan(times[start], times[min(end, len(times) - 1)], color=color, alpha=0.75)
        center = (times[start] + times[min(end, len(times) - 1)]) / 2
        plt.text(
            center,
            plt.ylim()[1] * 0.85,
            f"{cycle_id}\n{direction.replace('_to_', '→')}",
            ha="center",
            va="top",
            fontsize=7,
        )

    for item in rejected:
        start = item["start_row"]
        end = min(item["end_row"], len(times) - 1)
        plt.axvspan(times[start], times[end], color="red", alpha=0.14)

    for row_idx, direction, _angle in crossings:
        color = "green" if direction == "rising" else "purple"
        plt.axvline(times[row_idx], color=color, linewidth=0.7, alpha=0.45)

    plt.xlabel("Time (seconds)")
    plt.ylabel("Loop-normalized head angle (deg)")
    plt.title(
        f"{stack_name}: half-cycle segmentation "
        f"(accepted={len(cycles)}, rejected={len(rejected)})"
    )
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(os.path.join(cycle_dir, f"{stack_name}_cycle_segmentation.png"), dpi=180)
    plt.close()


def zscore(values):
    values = np.asarray(values, dtype=float)
    mean = float(np.nanmean(values))
    std = float(np.nanstd(values))
    if not np.isfinite(std) or std <= 0:
        return np.full(values.shape, np.nan, dtype=float)
    return (values - mean) / std


def save_normalized_signal_angle_plot(stack_name, df, labels, fps, out_dir):
    signal_dir = os.path.join(out_dir, "normalized_signal_angle")
    os.makedirs(signal_dir, exist_ok=True)
    times = df["frame"].to_numpy(dtype=float) / float(fps)
    plt.figure(figsize=(14, 5))
    plt.plot(
        times,
        zscore(df[ANGLE_COLUMN].to_numpy(dtype=float)),
        color="black",
        linewidth=1.4,
        label="Head angle z-score",
    )
    for label in labels:
        plt.plot(
            times,
            zscore(df[f"roi_signal_{label}"].to_numpy(dtype=float)),
            linewidth=1,
            alpha=0.85,
            label=f"{label} brightest-5 deltaF/Fbg z-score",
        )
    plt.axhline(0, color="gray", linewidth=0.7, linestyle="--")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Z-score")
    plt.title(f"{stack_name}: normalized angle, residuals, and PCA common signal")
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(os.path.join(signal_dir, f"{stack_name}_normalized_signal_angle.png"), dpi=180)
    plt.close()


def save_pca_common_signal_plot(stack_name, pca_info, out_dir):
    pca_dir = os.path.join(out_dir, "pca_common_signal")
    os.makedirs(pca_dir, exist_ok=True)
    x = np.asarray(pca_info["centered_nrv"], dtype=float)
    y = np.asarray(pca_info["centered_nrd"], dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    loading = np.array(
        [pca_info["pc1_nrv_loading"], pca_info["pc1_nrd_loading"]],
        dtype=float,
    )
    extent = max(1.0, float(np.nanpercentile(np.abs(np.concatenate([x[valid], y[valid]])), 98)))
    line = np.array([-extent, extent])
    plt.figure(figsize=(7, 7))
    plt.scatter(x[valid], y[valid], s=8, alpha=0.35, color="gray", label="Frames")
    plt.plot(
        line * loading[0],
        line * loading[1],
        color="red",
        linewidth=2,
        label=(
            f"PC1 common direction\n"
            f"loading=({loading[0]:.3f}, {loading[1]:.3f}), "
            f"variance={pca_info['pc1_explained_variance_ratio']:.1%}"
        ),
    )
    plt.axhline(0, color="black", linewidth=0.6)
    plt.axvline(0, color="black", linewidth=0.6)
    plt.xlabel("Centered nrv brightest-5 deltaF/Fbg")
    plt.ylabel("Centered nrD brightest-5 deltaF/Fbg")
    plt.title(f"{stack_name}: nrv/nrD PCA common-signal direction")
    plt.axis("equal")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(pca_dir, f"{stack_name}_pca_common_signal.png"), dpi=180)
    plt.close()


def save_derived_signals(stack_name, df, output_dir):
    signal_dir = os.path.join(output_dir, "signals")
    os.makedirs(signal_dir, exist_ok=True)
    columns = [
        "frame",
        ANGLE_COLUMN,
        "roi_signal_nrv_residual",
        "roi_signal_nrD_residual",
        "roi_signal_common_signal",
    ]
    df[columns].to_csv(
        os.path.join(signal_dir, f"{stack_name}_pca_residual_common_signals.csv"),
        index=False,
    )


def save_summary_lag_plot(lag_df, out_dir):
    if lag_df.empty:
        return pd.DataFrame()
    summary = (
        lag_df.groupby(["roi", "lag_frames"], as_index=False)
        .agg(
            lag_seconds=("lag_seconds", "first"),
            mean_corr=("corr", "mean"),
            sem_corr=("corr", lambda x: x.std(ddof=1) / np.sqrt(x.count()) if x.count() > 1 else np.nan),
            n_segments=("corr", "count"),
        )
    )
    plt.figure(figsize=(10, 5))
    for label in ROI_LABELS:
        sub = summary[summary["roi"] == label]
        if sub.empty:
            continue
        plt.plot(sub["lag_seconds"], sub["mean_corr"], label=label)
        if sub["sem_corr"].notna().any():
            x = sub["lag_seconds"].to_numpy(dtype=float)
            y = sub["mean_corr"].to_numpy(dtype=float)
            sem = sub["sem_corr"].to_numpy(dtype=float)
            plt.fill_between(x, y - sem, y + sem, alpha=0.15)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.axvline(0, color="black", linewidth=0.8, linestyle="--")
    plt.xlabel("Lag (seconds): corr(angle[t], ROI[t + lag])")
    plt.ylabel("Mean Pearson r across half-cycles")
    plt.title("Summary half-cycle-averaged lag correlation")
    plt.legend()
    plt.tight_layout()
    summary_plot_dir = os.path.join(out_dir, "plots", "summary")
    os.makedirs(summary_plot_dir, exist_ok=True)
    plt.savefig(os.path.join(summary_plot_dir, "summary_lag_corr.png"), dpi=180)
    plt.savefig(os.path.join(summary_plot_dir, "overall_lag_corr.png"), dpi=180)
    plt.close()
    summary.to_csv(os.path.join(out_dir, "lag_correlations_summary.csv"), index=False)
    summary.to_csv(os.path.join(out_dir, "overall_lag_correlations.csv"), index=False)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=RUN_ID)
    parser.add_argument("--input-dir", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--fps", type=float, default=DEFAULT_FPS, help="Acquisition frame rate used to convert lag frames to seconds.")
    parser.add_argument(
        "--max-lag",
        type=int,
        default=0,
        help="Maximum lag in frames. Use 0 to auto-set from the mean accepted cycle length.",
    )
    parser.add_argument("--min-cycle-frames", type=int, default=10)
    parser.add_argument("--max-cycle-frames", type=int, default=300)
    parser.add_argument("--cycle-smooth-window", type=int, default=9)
    parser.add_argument("--cycle-smooth-polyorder", type=int, default=2)
    parser.add_argument("--signal-smooth-window", type=int, default=5)
    parser.add_argument("--signal-smooth-polyorder", type=int, default=2)
    parser.add_argument("--zero-tolerance", type=float, default=0.0)
    args = parser.parse_args()
    if args.fps <= 0:
        raise ValueError("--fps must be > 0")
    if args.min_cycle_frames < 3 or args.max_cycle_frames < args.min_cycle_frames:
        raise ValueError("Require 3 <= --min-cycle-frames <= --max-cycle-frames")
    if args.cycle_smooth_window < 1 or args.cycle_smooth_polyorder < 0:
        raise ValueError("Cycle smoothing window must be >= 1 and polyorder must be >= 0")
    if args.signal_smooth_window < 1 or args.signal_smooth_polyorder < 0:
        raise ValueError("Signal smoothing window must be >= 1 and polyorder must be >= 0")

    input_dir = args.input_dir or os.path.join(RESULTS_ROOT, args.run_id, ROI_INPUT_SUBDIR)
    output_dir = args.output_dir or os.path.join(RESULTS_ROOT, args.run_id, OUTPUT_SUBDIR)
    plot_dir = os.path.join(output_dir, "plots")
    smoothed_output_dir = os.path.join(output_dir, f"smoothed_window_{args.signal_smooth_window}")
    smoothed_plot_dir = os.path.join(smoothed_output_dir, "plots")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(plot_dir, exist_ok=True)
    os.makedirs(smoothed_output_dir, exist_ok=True)
    os.makedirs(smoothed_plot_dir, exist_ok=True)
    print(f"Using FPS={args.fps:g}; lag_seconds = lag_frames / FPS")
    print(
        "ROI signal metric: "
        f"({ROI_INTENSITY_METRIC} - {BACKGROUND_COLUMN}) / {BACKGROUND_COLUMN}"
    )
    print(
        "Half cycles: each adjacent zero-crossing pair; "
        f"accepted length={args.min_cycle_frames}-{args.max_cycle_frames} frames"
    )
    print(
        f"Cycle detection smoothing: Savitzky-Golay window={args.cycle_smooth_window}, "
        f"polyorder={args.cycle_smooth_polyorder}; correlations use raw angles"
    )
    print(
        f"Separate smoothed analysis: Savitzky-Golay window={args.signal_smooth_window}, "
        f"polyorder={args.signal_smooth_polyorder}; output={smoothed_output_dir}"
    )

    csv_paths = collect_intensity_csvs(input_dir)
    if not csv_paths:
        raise FileNotFoundError(f"No *_roi_intensity.csv files found in {input_dir}")

    all_segment_rows = []
    all_lag_rows = []
    all_crossing_rows = []
    all_cycle_rows = []
    all_pca_rows = []
    prepared = []
    smoothed_prepared = []

    for path in csv_paths:
        stack_name = stack_name_from_intensity_csv(path)
        print(f"Analyzing {stack_name}")
        df, labels, input_rows, status_ok_rows, loop_stats, pca_info, source_labels = clean_dataframe(path)
        print(f"  frames: input={input_rows}, head_angle_status_ok={status_ok_rows}, usable={len(df)}")
        print(
            "  loop normalization: "
            f"loop_left={loop_stats['loop_left']}, "
            f"loop_right flipped={loop_stats['loop_right_flipped']}, "
            f"unknown={loop_stats['loop_label_unknown']}"
        )
        if not labels:
            print(
                f"[skip] {stack_name}: PCA requires both nrv and nrD "
                f"{ROI_INTENSITY_METRIC} signals; found={source_labels}"
            )
            continue
        if df.empty:
            print(f"[skip] {stack_name}: no usable frames after filtering head_angle_status == ok")
            continue
        print(
            "  PCA common direction: "
            f"nrv loading={pca_info['pc1_nrv_loading']:.4f}, "
            f"nrD loading={pca_info['pc1_nrd_loading']:.4f}, "
            f"explained variance={pca_info['pc1_explained_variance_ratio']:.1%}"
        )
        all_pca_rows.append({
            "stack": stack_name,
            **{
                key: value
                for key, value in pca_info.items()
                if not isinstance(value, np.ndarray)
            },
        })
        save_pca_common_signal_plot(stack_name, pca_info, plot_dir)
        save_derived_signals(stack_name, df, output_dir)

        smoothed_angles = smooth_angles_for_cycles(
            df[ANGLE_COLUMN].to_numpy(),
            args.cycle_smooth_window,
            args.cycle_smooth_polyorder,
        )
        crossings = directional_zero_crossings(smoothed_angles, args.zero_tolerance)
        cycles, rejected = half_cycle_slices(
            crossings,
            args.min_cycle_frames,
            args.max_cycle_frames,
        )
        auto_lag = mean_cycle_length(cycles)
        print(
            f"  cycles: accepted={len(cycles)}, rejected={len(rejected)}, "
            f"mean accepted length={auto_lag} frame(s)"
        )
        save_cycle_segmentation_plot(
            stack_name,
            df,
            smoothed_angles,
            crossings,
            cycles,
            rejected,
            args.fps,
            plot_dir,
        )
        save_normalized_signal_angle_plot(stack_name, df, labels, args.fps, plot_dir)
        prepared.append((stack_name, df, labels, cycles, crossings, rejected, auto_lag))
        smoothed_df = make_smoothed_analysis_dataframe(
            df,
            labels,
            args.signal_smooth_window,
            args.signal_smooth_polyorder,
        )
        save_derived_signals(stack_name, smoothed_df, smoothed_output_dir)
        save_normalized_signal_angle_plot(
            stack_name,
            smoothed_df,
            labels,
            args.fps,
            smoothed_plot_dir,
        )
        smoothed_prepared.append(
            (stack_name, smoothed_df, labels, cycles, crossings, rejected, auto_lag)
        )

    auto_lags = [item[6] for item in prepared if item[6] > 0]
    if args.max_lag > 0:
        max_lag = args.max_lag
        print(f"Using user max lag: {max_lag} frame(s)")
    elif auto_lags:
        max_lag = max(1, int(round(float(np.mean(auto_lags)))))
        print(f"Auto max lag from mean accepted cycle length: {max_lag} frame(s)")
    else:
        max_lag = 1
        print("Could not estimate segment length; using max lag = 1 frame")
    lags = list(range(-max_lag, max_lag + 1))

    for stack_name, df, labels, cycles, crossings, rejected, auto_lag in prepared:
        print(f"Computing correlations for {stack_name} (mean cycle length={auto_lag} frame(s))")
        for row_idx, crossing_type, angle_value in crossings:
            all_crossing_rows.append({
                "stack": stack_name,
                "row_index": int(row_idx),
                "frame": int(df["frame"].iloc[row_idx]),
                "crossing_type": crossing_type,
                "angle_deg": float(angle_value),
            })
        for cycle_id, start, end, cycle_direction in cycles:
            all_cycle_rows.append({
                "stack": stack_name,
                "cycle_id": cycle_id,
                "accepted": 1,
                "reason": "",
                "start_frame": int(df["frame"].iloc[start]),
                "end_frame": int(df["frame"].iloc[min(end, len(df) - 1)]),
                "cycle_n_rows": int(end - start),
                "half_cycle_direction": cycle_direction,
            })
        for item in rejected:
            all_cycle_rows.append({
                "stack": stack_name,
                "cycle_id": "",
                "accepted": 0,
                "reason": item["reason"],
                "start_frame": int(df["frame"].iloc[item["start_row"]]),
                "end_frame": int(df["frame"].iloc[min(item["end_row"], len(df) - 1)]),
                "cycle_n_rows": int(item["cycle_n_frames"]),
                "half_cycle_direction": "",
            })

        segment_rows = corr_by_segments(stack_name, df, labels, cycles)
        lag_rows = corr_by_segment_lag(stack_name, df, labels, cycles, lags, args.fps)
        save_stack_plots(stack_name, segment_rows, lag_rows, plot_dir)

        all_segment_rows.extend(segment_rows)
        all_lag_rows.extend(lag_rows)

    smoothed_segment_rows = []
    smoothed_lag_rows = []
    for stack_name, df, labels, cycles, _crossings, _rejected, auto_lag in smoothed_prepared:
        print(f"Computing smoothed correlations for {stack_name} (mean cycle length={auto_lag} frame(s))")
        segment_rows = corr_by_segments(stack_name, df, labels, cycles)
        lag_rows = corr_by_segment_lag(stack_name, df, labels, cycles, lags, args.fps)
        save_stack_plots(stack_name, segment_rows, lag_rows, smoothed_plot_dir)
        smoothed_segment_rows.extend(segment_rows)
        smoothed_lag_rows.extend(lag_rows)

    segment_df = pd.DataFrame(all_segment_rows)
    lag_df = pd.DataFrame(all_lag_rows)
    crossing_df = pd.DataFrame(all_crossing_rows)
    cycle_df = pd.DataFrame(all_cycle_rows)
    pca_df = pd.DataFrame(all_pca_rows)

    segment_path = os.path.join(output_dir, "segment_correlations.csv")
    lag_path = os.path.join(output_dir, "lag_correlations_by_segment.csv")
    lag_summary_path = os.path.join(output_dir, "lag_correlations.csv")
    crossing_path = os.path.join(output_dir, "zero_crossings.csv")
    cycle_path = os.path.join(output_dir, "cycle_segments.csv")
    pca_path = os.path.join(output_dir, "pca_common_signal_summary.csv")
    overall_lag_path = os.path.join(output_dir, "overall_lag_correlations.csv")
    overall_plot_path = os.path.join(output_dir, "overall_lag_corr.png")
    segment_df.to_csv(segment_path, index=False)
    lag_df.to_csv(lag_path, index=False)
    summarize_lag_rows(all_lag_rows).to_csv(lag_summary_path, index=False)
    crossing_df.to_csv(crossing_path, index=False)
    cycle_df.to_csv(cycle_path, index=False)
    pca_df.to_csv(pca_path, index=False)
    save_summary_lag_plot(lag_df, output_dir)

    smoothed_segment_df = pd.DataFrame(smoothed_segment_rows)
    smoothed_lag_df = pd.DataFrame(smoothed_lag_rows)
    smoothed_segment_df.to_csv(
        os.path.join(smoothed_output_dir, "segment_correlations.csv"),
        index=False,
    )
    smoothed_lag_df.to_csv(
        os.path.join(smoothed_output_dir, "lag_correlations_by_segment.csv"),
        index=False,
    )
    summarize_lag_rows(smoothed_lag_rows).to_csv(
        os.path.join(smoothed_output_dir, "lag_correlations.csv"),
        index=False,
    )
    save_summary_lag_plot(smoothed_lag_df, smoothed_output_dir)

    print(f"Saved segment correlations: {segment_path}")
    print(f"Saved segment lag correlations: {lag_path}")
    print(f"Saved stack-averaged lag correlations: {lag_summary_path}")
    print(f"Saved overall lag correlations: {overall_lag_path}")
    print(f"Saved overall lag plot: {overall_plot_path}")
    print(f"Saved zero crossings: {crossing_path}")
    print(f"Saved cycle segmentation table: {cycle_path}")
    print(f"Saved PCA common-signal summary: {pca_path}")
    print(f"Saved cycle segmentation plots: {os.path.join(plot_dir, 'cycle_segmentation')}")
    print(f"Saved normalized signal-angle plots: {os.path.join(plot_dir, 'normalized_signal_angle')}")
    print(f"Saved PCA common-signal plots: {os.path.join(plot_dir, 'pca_common_signal')}")
    print(f"Saved segment correlation plots: {os.path.join(plot_dir, 'segment_correlation')}")
    print(f"Saved lag correlation plots: {os.path.join(plot_dir, 'lag_correlation')}")
    print(f"Saved summary plots: {os.path.join(plot_dir, 'summary')}")
    print(f"Saved separate smoothed analysis: {smoothed_output_dir}")


if __name__ == "__main__":
    main()
