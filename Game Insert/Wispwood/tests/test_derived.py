"""Tests for the pure shared geometry in :mod:`derived`."""

import math

import config as cfg
import derived as d


def test_wispwood_outer_envelope():
    """Verify tray outer-envelope constants are derived consistently from config."""
    assert d.OUTER_WIDTH == 2 * cfg.WALL_LONG + 2 * cfg.POCKET_WIDTH + cfg.DIVIDER_THICKNESS
    assert math.isclose(d.OUTER_LENGTH, cfg.POCKET_LENGTH + 2 * cfg.WALL_END, abs_tol=1e-9)
    assert math.isclose(
        d.WALL_TOP,
        cfg.FLOOR_THICKNESS
        + cfg.POCKET_DEPTH
        + cfg.LID_THICKNESS
        + cfg.LID_SLIDE_CLEARANCE
        + cfg.LID_TOP_LIP,
        abs_tol=1e-9,
    )


def test_alt_stand_folded_envelope():
    """Verify alt-stand folded-envelope constants are derived consistently from config."""
    assert math.isclose(
        d.ALT_SHELF_W,
        d.OUTER_WIDTH + 2 * cfg.ALT_SHELF_SIDE_LIP_W + 2 * cfg.ALT_SHELF_SIDE_CLEAR,
        abs_tol=1e-9,
    )
    assert math.isclose(
        d.ALT_FOLDED_L, cfg.ALT_SHELF_HEIGHT + cfg.ALT_SHELF_BELOW_LIP, abs_tol=1e-9
    )
    # plate + raised corner posts
    assert math.isclose(d.ALT_FOLDED_H, cfg.ALT_SHELF_THICKNESS + d.ALT_CORNER_H, abs_tol=1e-9)


def test_folded_height_within_bound():
    """Verify folded alt-stand height fits under the box-insert top tray."""
    assert d.ALT_FOLDED_H <= cfg.ALT_STAND_MAX_FOLDED_H
