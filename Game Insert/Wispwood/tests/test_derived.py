"""Tests for the pure shared geometry in :mod:`derived`."""

import math

import config as cfg
import derived as d


def test_wispwood_outer_envelope():
    """Verify tray outer-envelope constants match expected millimetre values."""
    assert d.OUTER_WIDTH == 86.0
    assert math.isclose(d.OUTER_LENGTH, 182.64, abs_tol=0.01)
    assert math.isclose(d.WALL_TOP, 42.7, abs_tol=0.01)


def test_alt_stand_folded_envelope():
    """Verify alt-stand folded-envelope constants match expected millimetre values."""
    assert math.isclose(d.ALT_SHELF_W, 92.2, abs_tol=0.01)
    assert math.isclose(d.ALT_FOLDED_L, 105.0, abs_tol=0.01)
    # plate + raised corner posts
    assert math.isclose(d.ALT_FOLDED_H, cfg.ALT_SHELF_THICKNESS + d.ALT_CORNER_H, abs_tol=1e-9)


def test_folded_height_within_bound():
    """Verify folded alt-stand height fits under the box-insert top tray."""
    assert d.ALT_FOLDED_H <= cfg.ALT_STAND_MAX_FOLDED_H
