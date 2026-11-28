"""wormspy.analysis.catalog & pipelines: scanning, queue persistence, and execution."""

import numpy as np

from wormspy.acquisition.pairing import FramePair
from wormspy.acquisition.recorder import ChannelConfig, Recorder
from wormspy.acquisition.session import create_session
from wormspy.analysis.catalog import AnalysisQueue, scan_recordings
from wormspy.analysis.pipelines import PIPELINES, pipeline_by_id
from wormspy.calibration.math import CameraCalibration
from wormspy.calibration.routine import RigCalibration
from wormspy.core.frames import Frame

SHAPE = (32, 48)
GCAMP = ChannelConfig("gcamp", "fluorescence", SHAPE)
BF = ChannelConfig("brightfield", "behaviour", SHAPE)
MATRIX = np.array([[0.5, 0.0], [0.0, 0.5]])


def _make_session(data_root, animal_id, operator, condition, count=6, complete=True):
    cal = RigCalibration(reference="gcamp", cameras={
        "gcamp": CameraCalibration(MATRIX, 0.0, SHAPE),
        "brightfield": CameraCalibration(MATRIX, 0.0, SHAPE, origin_px=(24.0, 16.0)),
    })
    session = create_session(
        data_root,
        {"animal_id": animal_id, "operator": operator, "condition": condition, "notes": ""},
        {"fps": 10.0, "calibration": cal.to_json(),
         "channels": {"gcamp": {"role": "fluorescence"}, "brightfield": {"role": "behaviour"}}},
    )
    rec_dir = session / "rec-001"
    rec = Recorder(rec_dir, GCAMP, BF, fps=10.0, on_event=lambda _: None,
                   telemetry=lambda p: {"x_um": 1000.0, "y_um": 1000.0, "z_um": 0.0})
    rec.start()
    for i in range(count):
        fluo = np.full(SHAPE, 500, np.uint16)
        fluo[14:18, 22:26] = 4000
        bf = np.full(SHAPE, 200, np.uint8)
        bf[10:22, 18:30] = 60
        rec.submit(FramePair(
            i,
            Frame(fluo, i, 1.0 + i / 10, i * 100_000_000),
            Frame(bf, i, 1.0 + i / 10, i * 100_000_000),
            0,
        ))
    rec.stop()
    if not complete:
        (rec_dir / "recording.json").unlink()
    return rec_dir


def test_scan_recordings_reads_session_metadata_and_handles_incomplete(tmp_path):
    data_root = tmp_path / "data"
    _make_session(data_root, "N2 #1", "Alice", "on food", count=10, complete=True)
    _make_session(data_root, "ASH #2", "Bob", "off food", count=5, complete=False)

    entries = scan_recordings(data_root)
    assert len(entries) == 2
    by_animal = {e.animal_id: e for e in entries}
    assert by_animal["N2 #1"].operator == "Alice"
    assert by_animal["N2 #1"].condition == "on food"
    assert by_animal["N2 #1"].frames == 10
    assert by_animal["N2 #1"].complete is True
    assert set(by_animal["N2 #1"].roles) == {"fluorescence", "behaviour"}
    assert by_animal["ASH #2"].complete is False
    assert set(by_animal["ASH #2"].roles) == {"fluorescence", "behaviour"}


def test_analysis_queue_persists_selections_and_options(tmp_path):
    q_path = tmp_path / "analysis_queue.json"
    q = AnalysisQueue(q_path)
    q.set_selected("s1/rec-001", "ria_export", True)
    q.set_selected("s1/rec-001", "tierpsy_trajectory", True)
    q.set_options("ria_export", {"run_id": "20261128"})

    reloaded = AnalysisQueue(q_path)
    assert reloaded.selected_pipelines("s1/rec-001") == ["ria_export", "tierpsy_trajectory"]
    assert reloaded.options_for("ria_export") == {"run_id": "20261128"}
    reloaded.set_selected("s1/rec-001", "ria_export", False)
    assert reloaded.selected_pipelines("s1/rec-001") == ["tierpsy_trajectory"]


def test_builtin_pipelines_check_compatibility_execute_and_mark_done(tmp_path):
    data_root = tmp_path / "data"
    rec_dir = _make_session(data_root, "N2 #3", "SW", "fed", count=4)
    assert all(p.compatible(("fluorescence", "behaviour")) for p in PIPELINES)
    assert not pipeline_by_id("tierpsy_trajectory").compatible(("fluorescence",))

    for pid, opts in (
        ("ria_export", {"output_root": str(tmp_path / "ria"), "run_id": "r1", "copy_tiff": True}),
        ("tierpsy_trajectory", {"extract_skeletons": False}),
        ("classical_segmentation", {}),
    ):
        pipe = pipeline_by_id(pid)
        assert not pipe.is_done(rec_dir, opts)
        outputs = pipe.run(rec_dir, opts, None)
        assert outputs and pipe.is_done(rec_dir, opts)
