import pytest
from core.stage import Stage, NullStage, FakeStage, clamp_native


def test_clamp_within_bounds_is_unchanged():
    value, hit = clamp_native(50.0, 0.0, 100.0)
    assert value == 50.0
    assert hit is False


def test_clamp_above_max_pins_to_max_and_flags():
    value, hit = clamp_native(150.0, 0.0, 100.0)
    assert value == 100.0
    assert hit is True


def test_clamp_below_min_pins_to_min_and_flags():
    value, hit = clamp_native(-5.0, 0.0, 100.0)
    assert value == 0.0
    assert hit is True


def test_null_stage_is_not_connected():
    stage = NullStage()
    assert stage.is_connected() is False


def test_null_stage_moves_are_noops():
    stage = NullStage()
    stage.move_relative("x", 100.0)
    assert stage.get_position("x") == 0.0


def test_fake_stage_tracks_relative_moves_and_clamps():
    stage = FakeStage(limits={"x": (0.0, 100.0)}, positions={"x": 90.0})
    hit = stage.move_relative("x", 50.0)  # 90 + 50 = 140 -> clamp to 100
    assert stage.get_position("x") == 100.0
    assert hit is True


def test_fake_stage_relative_move_within_bounds_does_not_flag():
    stage = FakeStage(limits={"x": (0.0, 100.0)}, positions={"x": 10.0})
    hit = stage.move_relative("x", 5.0)
    assert stage.get_position("x") == 15.0
    assert hit is False


def test_fake_stage_satisfies_stage_interface():
    assert issubclass(FakeStage, Stage)
    assert issubclass(NullStage, Stage)
