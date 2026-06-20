"""Pure derived geometry shared between the FreeCAD modules and the box-layout layer.

These values are recomputed from :mod:`config` alone (no FreeCAD import) so the packing
math and tests can run outside FreeCAD. They mirror the tray outer envelope in
``wispwood.py`` and own the stand kinematics consumed by ``stand.py``; the single source of
the *formulas* is here, and ``tests/test_derived.py`` pins the values.

Public API
----------
Module-level constants and :func:`cg_offset`, :func:`stand_is_stable` (see below).
"""

import math

import config as cfg

# --- Wispwood tray outer envelope (mirrors wispwood.py) ----------------------
OUTER_WIDTH = 2 * cfg.WALL_LONG + 2 * cfg.POCKET_WIDTH + cfg.DIVIDER_THICKNESS  # 86
OUTER_LENGTH = cfg.POCKET_LENGTH + 2 * cfg.WALL_END  # ~182.64
RAIL_Z0 = cfg.FLOOR_THICKNESS + cfg.POCKET_DEPTH  # lid underside = 39
LID_Z1 = RAIL_Z0 + cfg.LID_THICKNESS  # 41.5
WALL_TOP = LID_Z1 + cfg.LID_SLIDE_CLEARANCE + cfg.LID_TOP_LIP  # outer wall top ~42.7

# --- Stand kinematics (FreeCAD-free; consumed by stand.py) -------------------
ALT_THETA = math.radians(cfg.STAND_DEPLOY_ANGLE)
ALT_HBY = cfg.ALT_ROD_R  # bottom-rod (base hinge) axis Y
ALT_ZC = cfg.ALT_PART_T / 2.0  # hinge axis height = part mid-plane (base rests on the table)
ALT_SHELF_W = OUTER_WIDTH + 2 * cfg.ALT_SHELF_SIDE_LIP_W + 2 * cfg.ALT_SHELF_SIDE_CLEAR  # ~92.2

# Crossmember Y derived so the tray bottom edge lifts to TRAY_LIFT above the table.
ALT_CROSS_Y = ALT_HBY + (cfg.TRAY_LIFT - ALT_ZC) / math.sin(ALT_THETA)
ALT_S_HINGES = ALT_CROSS_Y - ALT_HBY  # hinge-to-hinge distance up the shelf

# Lock distance: deployed triangle, cradle seat ALT_CRADLE_OFFSET above the base centreline.
ALT_B_BASE = ALT_S_HINGES * math.cos(ALT_THETA) + math.sqrt(
    cfg.ALT_LEG_LENGTH**2 - (ALT_S_HINGES * math.sin(ALT_THETA) - cfg.ALT_CRADLE_OFFSET) ** 2
)

ALT_LIP_EDGE_H = cfg.ALT_LIP_EDGE_FRAC * WALL_TOP  # deep-lip height at the shelf edges


def cg_offset(l_cg, t_cg):
    """Return the horizontal depth of a slab CG behind the bottom hinge (mm; +behind/back).

    Parameters
    ----------
    l_cg : float
        CG height measured up the shelf from the hinge (mm).
    t_cg : float
        CG offset off the shelf front face (half the tray thickness) (mm).

    Returns
    -------
    float
        Horizontal (depth) position relative to the hinge; positive is back, negative forward.
    """
    return l_cg * math.cos(ALT_THETA) - t_cg * math.sin(ALT_THETA)


ALT_T_CG = WALL_TOP / 2.0  # tray half-thickness off the shelf face
ALT_CG_BACK_EMPTY = cg_offset(ALT_S_HINGES + OUTER_LENGTH / 2.0, ALT_T_CG)
ALT_CG_FWD_LOW = cg_offset(ALT_S_HINGES + cfg.ALT_CG_LOW_OFFSET, ALT_T_CG)


def stand_is_stable():
    """Return True if the loaded CG range stays inside the base footprint (no tip)."""
    return (-cfg.ALT_BASE_FWD) < ALT_CG_FWD_LOW and ALT_CG_BACK_EMPTY < ALT_B_BASE


# --- Folded envelope (tabletop-base design) ---------------------------------
ALT_FOLDED_W = ALT_SHELF_W
ALT_FOLDED_L = cfg.ALT_BASE_FWD + max(cfg.ALT_SHELF_HEIGHT, ALT_B_BASE + cfg.ALT_BASE_FOOT)
ALT_FOLDED_H = cfg.ALT_PART_T + cfg.ALT_PART_T + ALT_LIP_EDGE_H  # base + shelf + lip proud
