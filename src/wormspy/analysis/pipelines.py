"""Pluggable offline analysis pipeline registry for the `wormspy-review` UI."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from wormspy.analysis.ria_bridge import export_for_ria_pipeline
from wormspy.analysis.segmentation import default_channel, segment
from wormspy.analysis.trajectory import export_tierpsy, reconstruct_trajectory
from wormspy.reader import open_recording

ProgressFn = Callable[[str], None]


@dataclass(frozen=True)
class PipelineOption:
    """Declarative option schema rendered generically by SessionBrowser."""

    key: str
    label: str
    kind: Literal["str", "dir", "bool"]
    default: Any
    help: str = ""


@dataclass(frozen=True)
class AnalysisPipeline:
    id: str
    name: str
    short_name: str
    description: str
    required_roles: tuple[str, ...]
    is_done: Callable[[Path, dict], bool]
    run: Callable[[Path, dict, ProgressFn | None], dict[str, Path]]
    options: tuple[PipelineOption, ...] = ()

    def compatible(self, roles: Iterable[str]) -> bool:
        role_set = set(roles)
        if not role_set:
            return True
        return set(self.required_roles) <= role_set


# --- built-in pipelines -------------------------------------------------------------------

def _ria_target(rec_dir: Path, options: dict) -> tuple[Path, str, str]:
    out_raw = options.get("output_root")
    output_root = Path(out_raw) if out_raw else (rec_dir.parents[1] / "ria_exports")
    run_id = str(options.get("run_id") or "wormspy")
    stack_name = f"{rec_dir.parent.name}_{rec_dir.name}"
    return output_root, run_id, stack_name


def _ria_is_done(rec_dir: Path, options: dict) -> bool:
    output_root, run_id, stack_name = _ria_target(rec_dir, options)
    return (output_root / run_id / f"{stack_name}_frame_index_map.csv").exists()


def _ria_run(rec_dir: Path, options: dict, progress: ProgressFn | None = None) -> dict[str, Path]:
    output_root, run_id, stack_name = _ria_target(rec_dir, options)
    if progress:
        progress(f"Exporting {rec_dir.name} for RIA-Segmentation…")
    with open_recording(rec_dir) as rec:
        return export_for_ria_pipeline(
            rec,
            output_root=output_root,
            run_id=run_id,
            stack_name=stack_name,
            normalization=str(options.get("normalization", "minmax")),
            copy_tiff=bool(options.get("copy_tiff", False)),
        )


def _tierpsy_is_done(rec_dir: Path, _options: dict) -> bool:
    return (rec_dir / "analysis" / "tierpsy" / "trajectory.csv").exists()


def _tierpsy_run(rec_dir: Path, options: dict,
                 progress: ProgressFn | None = None) -> dict[str, Path]:
    if progress:
        progress(f"Reconstructing world trajectory for {rec_dir.name}…")
    with open_recording(rec_dir) as rec:
        result = reconstruct_trajectory(
            rec,
            extract_skeletons=bool(options.get("extract_skeletons", True)),
        )
        out_dir = rec_dir / "analysis" / "tierpsy"
        return export_tierpsy(
            rec,
            result,
            out_dir,
            write_hdf5=bool(options.get("write_hdf5", False)),
        )


def _classical_is_done(rec_dir: Path, _options: dict) -> bool:
    analysis_dir = rec_dir / "analysis"
    return analysis_dir.is_dir() and any(analysis_dir.glob("*_segmentation.csv"))


def _classical_run(rec_dir: Path, options: dict,
                   progress: ProgressFn | None = None) -> dict[str, Path]:
    with open_recording(rec_dir) as rec:
        channel = options.get("channel") or default_channel(rec)
        out_dir = rec_dir / "analysis"
        out_dir.mkdir(parents=True, exist_ok=True)
        csv_path = out_dir / f"{channel}_segmentation.csv"
        overlay_path = (out_dir / f"{channel}_segmentation.mp4"
                        if options.get("overlay") else None)

        def _cb(done: int, total: int) -> None:
            if progress:
                progress(f"Segmenting {rec_dir.name}: {done}/{total}")

        table = segment(rec, channel=channel, overlay=overlay_path, progress=_cb)
        table.to_csv(csv_path)
        outputs = {"csv": csv_path}
        if overlay_path is not None and overlay_path.exists():
            outputs["overlay"] = overlay_path
        return outputs


PIPELINES: tuple[AnalysisPipeline, ...] = (
    AnalysisPipeline(
        id="ria_export",
        name="RIA-Segmentation export",
        short_name="RIA",
        description="Export BigTIFF stack, 8-bit JPGs, and frame map for YOLO/SAM2 RIA pipeline",
        required_roles=("fluorescence",),
        is_done=_ria_is_done,
        run=_ria_run,
        options=(
            PipelineOption(
                "output_root",
                "Export folder",
                "dir",
                "",
                "Parent directory for RIA export folders (default: <data_root>/ria_exports)",
            ),
            PipelineOption(
                "run_id",
                "Run subfolder",
                "str",
                "wormspy",
                "Subfolder name inside the export root for this batch",
            ),
            PipelineOption(
                "copy_tiff",
                "Also copy BigTIFF",
                "bool",
                False,
                "Write a full 16-bit BigTIFF stack alongside the 8-bit JPG frames",
            ),
        ),
    ),
    AnalysisPipeline(
        id="tierpsy_trajectory",
        name="World trajectory / Tierpsy",
        short_name="Tierpsy",
        description="Reconstruct world µm trajectory + 49-pt skeletons and Tierpsy files",
        required_roles=("behaviour",),
        is_done=_tierpsy_is_done,
        run=_tierpsy_run,
        options=(
            PipelineOption(
                "extract_skeletons",
                "Extract 49-pt skeletons",
                "bool",
                True,
                "Compute midlines alongside world centroid trajectories",
            ),
            PipelineOption(
                "write_hdf5",
                "Write Tierpsy HDF5",
                "bool",
                False,
                "Also export featuresN-compatible HDF5 if h5py is installed",
            ),
        ),
    ),
    AnalysisPipeline(
        id="classical_segmentation",
        name="Classical neuron segmentation",
        short_name="Neuron",
        description="Track single bright neuron and export raw 16-bit calcium intensity CSV",
        required_roles=("fluorescence",),
        is_done=_classical_is_done,
        run=_classical_run,
        options=(
            PipelineOption(
                "overlay",
                "Render debug MP4",
                "bool",
                False,
                "Save an annotated tracking video next to the CSV",
            ),
        ),
    ),
)


def pipeline_by_id(pipeline_id: str) -> AnalysisPipeline:
    for pipeline in PIPELINES:
        if pipeline.id == pipeline_id:
            return pipeline
    raise KeyError(f"unknown pipeline {pipeline_id!r}")
