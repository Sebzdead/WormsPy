"""wormspy.analysis.ria_bridge: export for RIA-Segmentation and join results back."""

import csv

import numpy as np
import pandas as pd
import pytest

from wormspy.acquisition.pairing import FramePair
from wormspy.acquisition.recorder import ChannelConfig, Recorder
from wormspy.acquisition.session import create_session
from wormspy.analysis.ria_bridge import export_for_ria_pipeline, join_ria_results, main
from wormspy.calibration.math import CameraCalibration
from wormspy.calibration.routine import RigCalibration
from wormspy.core.frames import Frame
from wormspy.reader import open_recording

SHAPE = (40, 60)
GCAMP = ChannelConfig("gcamp", "fluorescence", SHAPE)
BF = ChannelConfig("brightfield", "behaviour", SHAPE)
MATRIX = np.array([[0.5, 0.0], [0.0, 0.5]])


def _record(tmp_path, first=20, count=5, drop=(2,)):
    cal = RigCalibration(reference="gcamp", cameras={
        "gcamp": CameraCalibration(MATRIX, 0.0, SHAPE)})
    session = create_session(tmp_path / "data", {"animal_id": "RIA-bridge"},
                             {"fps": 10.0, "calibration": cal.to_json(),
                              "channels": {"gcamp": {"role": "fluorescence"},
                                           "brightfield": {"role": "behaviour"}}})
    rec = Recorder(session / "rec-001", GCAMP, BF, fps=10.0, on_event=lambda _: None,
                   telemetry=lambda pair: {"x_um": 1000.0 + pair.frame_index,
                                           "y_um": 2000.0, "z_um": 0.0})
    rec.start()
    for i in range(count):
        fid = first + i
        if i == 3:
            rec.mark_event("odor")
        img = np.full(SHAPE, 200 + i * 50, np.uint16)
        img[10:20, 20:30] = 5000
        clock = None if i in drop else Frame(img, fid, 10.0 + i / 10, i * 100_000_000)
        follower = Frame(np.full(SHAPE, 120, np.uint8), fid, 10.0 + i / 10, i * 100_000_000)
        rec.submit(FramePair(fid, clock, follower, 0 if clock else None))
    rec.stop()
    return session / "rec-001"


def test_export_and_join_round_trip_with_frame_offset_and_world_coords(tmp_path):
    rec_path = _record(tmp_path, first=20, count=5, drop=(2,))
    out_root = tmp_path / "ria_results"
    with open_recording(rec_path) as rec:
        exported = export_for_ria_pipeline(rec, out_root, run_id="run1", copy_tiff=True)
        assert exported["stack"].exists()
        jpgs = sorted(exported["jpg_dir"].glob("*.jpg"))
        assert [p.name for p in jpgs] == [f"{i:06d}.jpg" for i in range(5)]
        assert (exported["jpg_dir"] / "conversion_info.txt").exists()
        fmap = pd.read_csv(exported["frame_map"])
        assert list(fmap["frame"]) == [0, 1, 2, 3, 4]
        assert list(fmap["frame_index"]) == [20, 21, 22, 23, 24]
        assert list(fmap["valid"]) == [1, 1, 0, 1, 1]

        # Simulate RIA-Segmentation Step 5 & Step 8 outputs (0-based frame column)
        angles_csv = tmp_path / "head_angles.csv"
        with angles_csv.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["frame", "status", "ria_head_angle_deg",
                                               "head_x", "head_y", "anchor_x", "anchor_y"])
            w.writeheader()
            w.writerow({"frame": 0, "status": "ok", "ria_head_angle_deg": 12.5,
                        "head_x": 30.0, "head_y": 20.0, "anchor_x": 40.0, "anchor_y": 25.0})
            w.writerow({"frame": 3, "status": "ok", "ria_head_angle_deg": -8.0,
                        "head_x": 32.0, "head_y": 22.0, "anchor_x": "", "anchor_y": ""})

        roi_csv = tmp_path / "roi_intensity.csv"
        with roi_csv.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["frame", "status",
                                               "background_corrected_mean_intensity_nrD"])
            w.writeheader()
            w.writerow({"frame": 0, "status": "ok",
                        "background_corrected_mean_intensity_nrD": 412.0})
            w.writerow({"frame": 3, "status": "ok",
                        "background_corrected_mean_intensity_nrD": 890.0})

        joined = join_ria_results(rec, head_angles_csv=angles_csv, roi_intensity_csv=roi_csv)
        assert list(joined.index) == [20, 21, 22, 23, 24]
        # frame 0 -> frame_index 20, stage=(1020, 2000), centre=(30, 20), 2 µm/px
        assert joined.loc[20, "head_x_um"] == pytest.approx(1020.0)
        assert joined.loc[20, "anchor_x_um"] == pytest.approx(1040.0)
        assert joined.loc[20, "anchor_y_um"] == pytest.approx(2010.0)
        assert joined.loc[23, "event"] == "odor"
        assert joined.loc[23, "background_corrected_mean_intensity_nrD"] == pytest.approx(890.0)
        assert np.isnan(joined.loc[22, "ria_head_angle_deg"])

    # CLI smoke check
    assert main(["export", str(rec_path), "--out", str(out_root), "--run-id", "run2"]) == 0
    out_csv = tmp_path / "joined.csv"
    assert main(["join", str(rec_path), "--head-angles", str(angles_csv),
                 "--roi-intensity", str(roi_csv), "--out", str(out_csv)]) == 0
    assert out_csv.exists()
