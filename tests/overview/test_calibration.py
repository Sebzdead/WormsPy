"""OverviewCalibration: homography fitting, round-trips, FOV box, and legacy YAML import."""

from pathlib import Path

import numpy as np
import pytest

from wormspy.overview.calibration import OverviewCalibration


def test_fit_four_and_more_points_round_trips_and_computes_fov_polygon(tmp_path):
    px = [(100.0, 100.0), (500.0, 100.0), (500.0, 500.0), (100.0, 500.0)]
    um = [(5000.0, 5000.0), (45000.0, 5000.0), (45000.0, 45000.0), (5000.0, 45000.0)]
    calib = OverviewCalibration.fit(px, um)
    assert calib.residual_um == pytest.approx(0.0, abs=1e-2)
    assert calib.pixel_to_stage_um(300.0, 300.0) == pytest.approx((25000.0, 25000.0), abs=1e-2)
    assert calib.stage_um_to_pixel(25000.0, 25000.0) == pytest.approx((300.0, 300.0), abs=1e-2)

    poly = calib.fov_polygon_px((25000.0, 25000.0), fov_um=(2000.0, 1000.0))
    assert poly.shape == (5, 2)
    assert tuple(poly[0]) == pytest.approx(tuple(poly[-1]))

    path = tmp_path / "overview_calibration.json"
    calib.save(path)
    loaded = OverviewCalibration.load(path)
    assert loaded.pixel_to_stage_um(200.0, 400.0) == pytest.approx(
        calib.pixel_to_stage_um(200.0, 400.0))

    # 5-point fit also works
    calib5 = OverviewCalibration.fit([*px, (300.0, 300.0)], [*um, (25000.0, 25000.0)])
    assert calib5.residual_um == pytest.approx(0.0, abs=1e-2)


def test_fit_rejects_fewer_than_four_points_or_collinear_points():
    with pytest.raises(ValueError):
        OverviewCalibration.fit([(0, 0), (1, 0), (0, 1)], [(0, 0), (1, 0), (0, 1)])
    with pytest.raises(ValueError):
        OverviewCalibration.fit([(0, 0), (1, 0), (2, 0), (3, 0)],
                                [(0, 0), (1, 0), (2, 0), (3, 0)])


def test_from_legacy_yaml_imports_tracker_calibration_in_micrometres():
    yaml_path = Path(__file__).parents[2] / "Tracker" / "src" / "camera_stage_calibration.yaml"
    if not yaml_path.exists():
        pytest.skip("Tracker legacy calibration file not present")
    calib = OverviewCalibration.from_legacy_yaml(yaml_path)
    # In camera_stage_calibration.yaml, center pixel (1045, 1225) maps to (15, 15) mm = 15000 µm
    x_um, y_um = calib.pixel_to_stage_um(1045.0, 1225.0)
    assert (x_um, y_um) == pytest.approx((15_000.0, 15_000.0), abs=500.0)
    assert len(calib.pixel_points) == 4
    assert np.isfinite(calib.residual_um)
