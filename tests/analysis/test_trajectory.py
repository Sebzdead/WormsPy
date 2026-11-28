"""wormspy.analysis.trajectory: skeleton extraction, world trajectories, and Tierpsy export."""

import json
import sys

import cv2
import numpy as np
import pandas as pd
import pytest

from wormspy.acquisition.pairing import FramePair
from wormspy.acquisition.recorder import ChannelConfig, Recorder
from wormspy.acquisition.session import create_session
from wormspy.analysis.trajectory import (
    export_tierpsy,
    extract_skeleton,
    main,
    reconstruct_trajectory,
    write_tierpsy_hdf5,
)
from wormspy.calibration.math import CameraCalibration
from wormspy.calibration.routine import RigCalibration
from wormspy.core.frames import Frame
from wormspy.reader import open_recording
from wormspy.sim.render import ImageGeometry, render_behaviour, render_fluorescence
from wormspy.sim.worm import SyntheticWorm
from wormspy.tracking.estimators import DarkObject

GEOM = ImageGeometry(width_px=240, height_px=160, um_per_px=5.0)
SHAPE = (GEOM.height_px, GEOM.width_px)
GCAMP = ChannelConfig("gcamp", "fluorescence", SHAPE)
BF = ChannelConfig("brightfield", "behaviour", SHAPE)


def test_extract_skeleton_returns_equidistant_centerline_and_handles_empty():
    assert extract_skeleton(np.zeros((40, 40), bool)) is None
    mask = np.zeros((100, 140), np.uint8)
    ts = np.linspace(0.0, np.pi, 40)
    pts = np.column_stack([20.0 + 95.0 * (ts / np.pi), 50.0 + 18.0 * np.sin(ts)])
    cv2.polylines(mask, [np.rint(pts).astype(np.int32).reshape(-1, 1, 2)],
                  isClosed=False, color=255, thickness=9)
    skel = extract_skeleton(mask > 0, n_points=49)
    assert skel is not None and skel.shape == (49, 2)
    # endpoints lie near the ends of the drawn curve (either orientation)
    ends = {tuple(np.round(skel[0])), tuple(np.round(skel[-1]))}
    assert any(np.hypot(e[0] - 20.0, e[1] - 50.0) < 6.0 for e in ends)
    assert any(np.hypot(e[0] - 115.0, e[1] - 50.0) < 6.0 for e in ends)


def _record_crawling_worm(tmp_path, count=8, drop=(3,)):
    cal = RigCalibration(reference="brightfield", cameras={
        "brightfield": CameraCalibration(GEOM.matrix, 0.0, SHAPE),
        "gcamp": CameraCalibration(GEOM.matrix, 0.0, SHAPE, origin_px=tuple(GEOM.origin_px)),
    })
    session = create_session(tmp_path / "data", {"animal_id": "N2-traj"},
                             {"fps": 10.0, "calibration": cal.to_json(),
                              "channels": {"gcamp": {"role": "fluorescence"},
                                           "brightfield": {"role": "behaviour"}}})
    worm = SyntheticWorm(seed=1, start_um=(1000.0, 1000.0), speed_um_s=200.0, length_um=600.0)
    rec = Recorder(session / "rec-001", GCAMP, BF, fps=10.0, on_event=lambda _: None,
                   telemetry=lambda pair: {"x_um": 1000.0 + pair.frame_index * 15.0,
                                           "y_um": 1000.0, "z_um": 0.0})
    rec.start()
    true_centroids = []
    for i in range(count):
        stage_um = (1000.0 + i * 15.0, 1000.0)
        true_centroids.append(worm.centroid)
        fluo = render_fluorescence(worm, stage_um, GEOM)
        bf = render_behaviour(worm, stage_um, GEOM)
        clock = Frame(fluo, i, 10.0 + i / 10, i * 100_000_000)
        follower = None if i in drop else Frame(bf, i, 10.0 + i / 10, i * 100_000_000)
        rec.submit(FramePair(i, clock, follower, 0 if follower else None))
        worm.step(0.1)
    rec.stop()
    return session / "rec-001", true_centroids


def test_reconstruct_trajectory_and_export_tierpsy(tmp_path):
    rec_path, true_centroids = _record_crawling_worm(tmp_path, count=8, drop=(3,))
    est = DarkObject(background_sigma_px=30.0, min_area_px=100.0, downsample=1)
    with open_recording(rec_path) as rec:
        result = reconstruct_trajectory(rec, estimator=est)
        assert result.skeletons_px is not None and result.skeletons_um is not None
        assert result.skeletons_um.shape == (8, 49, 2)
        assert np.isnan(result.table.loc[3, "worm_x_um"])
        assert np.isnan(result.skeletons_um[3]).all()
        for i in (0, 1, 2, 4, 5, 6, 7):
            assert (result.table.loc[i, "worm_x_um"], result.table.loc[i, "worm_y_um"]) == (
                pytest.approx(true_centroids[i], abs=25.0))
        assert result.table.loc[5, "speed_um_s"] > 0.0

        out_dir = tmp_path / "tierpsy_out"
        outputs = export_tierpsy(rec, result, out_dir)
        assert set(outputs) == {"trajectory_csv", "stage_csv", "metadata", "skeletons_npz"}
        meta = json.loads(outputs["metadata"].read_text())
        assert meta["coordinate_units"] == "microns" and meta["skeleton_points"] == 49
        stage_df = pd.read_csv(outputs["stage_csv"])
        assert len(stage_df) == 8

    assert main([str(rec_path), "--no-skeleton"]) == 0
    assert (rec_path / "analysis" / "tierpsy" / "trajectory.csv").exists()


def test_reconstruct_trajectory_accepts_external_masks_directory(tmp_path):
    rec_path, true_centroids = _record_crawling_worm(tmp_path, count=4, drop=())
    mask_dir = tmp_path / "masks"
    mask_dir.mkdir()
    with open_recording(rec_path) as rec:
        for pos, frame_index in enumerate(rec.index):
            img = rec["brightfield"][frame_index]
            cv2.imwrite(str(mask_dir / f"{pos:06d}_worm_mask.png"),
                        ((img < 140).astype(np.uint8) * 255))
        res = reconstruct_trajectory(rec, mask_dir=mask_dir)
    assert res.table.loc[0, "worm_x_um"] == pytest.approx(true_centroids[0][0], abs=25.0)


def test_write_tierpsy_hdf5_requires_h5py_and_writes_expected_schema(monkeypatch, tmp_path):
    rec_path, _ = _record_crawling_worm(tmp_path, count=4, drop=())
    est = DarkObject(background_sigma_px=30.0, min_area_px=100.0, downsample=1)
    with open_recording(rec_path) as rec:
        res = reconstruct_trajectory(rec, estimator=est)

    monkeypatch.setitem(sys.modules, "h5py", None)
    with pytest.raises(ImportError, match="tierpsy"):
        write_tierpsy_hdf5(res, tmp_path / "out.hdf5")

    written = {}

    class FakeDataset:
        def __init__(self, data):
            self.data = data
            self.attrs = {}

    class FakeGroup:
        def __init__(self, prefix=""):
            self.prefix = prefix
            self.attrs = {}

        def create_dataset(self, name, data):
            ds = FakeDataset(data)
            written[f"{self.prefix}{name}"] = ds
            return ds

        def create_group(self, name):
            return FakeGroup(f"{self.prefix}{name}/")

    class FakeH5File(FakeGroup):
        def __init__(self, path, mode):
            super().__init__()
            written["_path"] = path

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            pass

    fake_h5py = type(sys)("h5py")
    fake_h5py.File = FakeH5File
    monkeypatch.setitem(sys.modules, "h5py", fake_h5py)

    h5_path = write_tierpsy_hdf5(res, tmp_path / "rec_skeletons.hdf5")
    assert h5_path.name == "rec_skeletons.hdf5"
    assert written["skeleton"].data.shape == (4, 49, 2)
    assert written["stage_position_pix"].data.shape == (4, 2)
    assert written["timestamp/time"].data.shape == (4,)
    assert written["trajectories_data"].data.shape == (4,)
