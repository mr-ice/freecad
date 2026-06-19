"""Pure derived geometry shared between the FreeCAD modules and the box-layout layer.

These values are recomputed from :mod:`config` alone (no FreeCAD import) so the packing
math and tests can run outside FreeCAD. They mirror the in-module derivations in
``wispwood.py`` (tray outer envelope) and ``alt_stand.py`` (folded stand envelope); the
single source of the *formulas* is here, and ``tests/test_derived.py`` pins the values.

Public API
----------
Module-level constants (see below).
"""

import config as cfg

# --- Wispwood tray outer envelope (mirrors wispwood.py) ----------------------
OUTER_WIDTH = 2 * cfg.WALL_LONG + 2 * cfg.POCKET_WIDTH + cfg.DIVIDER_THICKNESS  # 86
OUTER_LENGTH = cfg.POCKET_LENGTH + 2 * cfg.WALL_END  # ~182.64
RAIL_Z0 = cfg.FLOOR_THICKNESS + cfg.POCKET_DEPTH  # lid underside = 39
LID_Z1 = RAIL_Z0 + cfg.LID_THICKNESS  # 41.5
WALL_TOP = LID_Z1 + cfg.LID_SLIDE_CLEARANCE + cfg.LID_TOP_LIP  # outer wall top ~42.7

# --- Alt stand folded envelope (mirrors alt_stand.py) ------------------------
ALT_SHELF_W = OUTER_WIDTH + 2 * cfg.ALT_SHELF_SIDE_LIP_W + 2 * cfg.ALT_SHELF_SIDE_CLEAR  # ~92.2
ALT_CORNER_H = WALL_TOP * cfg.ALT_SHELF_CORNER_H_FRAC  # raised corner posts ~21.35
ALT_FOLDED_H = cfg.ALT_SHELF_THICKNESS + ALT_CORNER_H  # plate + posts ~28.35
ALT_FOLDED_W = ALT_SHELF_W  # ~92.2
ALT_FOLDED_L = cfg.ALT_SHELF_HEIGHT + cfg.ALT_SHELF_BELOW_LIP  # 105
