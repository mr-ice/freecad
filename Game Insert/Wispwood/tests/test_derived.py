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


def test_alt_stand_shelf_width():
    """Verify the shelf width is derived from the tray width plus the side lips/clearances."""
    assert math.isclose(
        d.ALT_SHELF_W,
        d.OUTER_WIDTH + 2 * cfg.ALT_SHELF_SIDE_LIP_W + 2 * cfg.ALT_SHELF_SIDE_CLEAR,
        abs_tol=1e-9,
    )


def test_stand_lift_sets_crossmember():
    """The crossmember Y derives from TRAY_LIFT so the tray bottom edge sits at that height."""
    theta = math.radians(cfg.STAND_DEPLOY_ANGLE)
    lip_z = d.ALT_ZC + (d.ALT_CROSS_Y - d.ALT_HBY) * math.sin(theta)
    assert math.isclose(lip_z, cfg.TRAY_LIFT, abs_tol=1e-9)


def test_stand_lock_distance_law_of_cosines():
    """B_BASE matches the law-of-cosines lock formula from the hinge spacing and leg length."""
    theta = math.radians(cfg.STAND_DEPLOY_ANGLE)
    s = d.ALT_S_HINGES
    expected = s * math.cos(theta) + math.sqrt(
        cfg.ALT_LEG_LENGTH**2 - (s * math.sin(theta) - cfg.ALT_CRADLE_OFFSET) ** 2
    )
    assert math.isclose(d.ALT_B_BASE, expected, abs_tol=1e-9)
    assert d.ALT_B_BASE < s + cfg.ALT_LEG_LENGTH  # non-degenerate triangle


def test_stand_cg_within_footprint():
    """Empty CG sits behind the hinge; loaded-low CG swings forward; both inside the base."""
    assert d.ALT_CG_BACK_EMPTY > 0  # empty: behind the hinge
    assert d.ALT_CG_FWD_LOW < 0  # loaded low: forward of the hinge
    assert d.ALT_CG_FWD_LOW > -cfg.ALT_BASE_FWD  # but not past the forward foot
    assert d.ALT_CG_BACK_EMPTY < d.ALT_B_BASE  # and not past the cradle
    assert d.stand_is_stable()


def test_folded_height_within_bound():
    """Verify folded stand height fits under the box-insert top tray."""
    assert d.ALT_FOLDED_H <= cfg.ALT_STAND_MAX_FOLDED_H
