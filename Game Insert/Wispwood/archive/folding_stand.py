"""Archived: the integrated folding stand (oval pegs riding V-slots in the tray walls).

Retired from ``wispwood.py``/``config.py`` in favour of the separate rod-frame ``stand.py``.
Kept verbatim for reference; NOT imported by any macro. The folding-stand constants that used
to live in ``config.py`` are reproduced here so this snapshot is self-contained.

A one-piece springy U: two rounded-end legs joined by a front base panel, each leg carrying an
oval peg that rides a parallel-arm / jog / top-arm slot cut in the tray's outer side wall
(folded peg rest → hinge vertex → lock detent). Modelled folded.
"""

import math

import config as cfg
import Part
from FreeCAD import Vector

# --- Folding-stand constants (formerly in config.py) -------------------------
STAND_THICKNESS = 3.0  # leg and base-panel thickness
STAND_LEG_LENGTH_FRAC = 0.6  # fraction of the tray length spanned by each leg
STAND_LEG_WIDTH = 16.0  # leg width (Z extent), centred on the peg
STAND_BASE_DEPTH = 8.0  # base-panel thickness along Y (the foot)
STAND_CHAMFER = 5.0  # chamfer/gusset at the leg-to-base junction
STAND_PEG_LENGTH = 10.0  # oval major axis, along the leg
STAND_PEG_WIDTH = 5.0  # oval minor axis (sets the slot channel width)
STAND_PEG_DEPTH = 2.5  # how far the peg projects into the wall slot (< WALL_LONG)
STAND_SLOT_CLEARANCE = 0.4  # slot-vs-peg running clearance
STAND_BODY_GAP = 0.2  # leg-inner-face to tray-wall gap so the folded model prints free
STAND_SLOT_ARM_LEN = 24.0  # length of the horizontal (parallel) arm
STAND_V_ANGLE_DEG = 15.0  # tilt of the top arm above horizontal
STAND_JOG_FRAC = 0.5  # vertical jog at the vertex = this * peg width (the lift)
STAND_ARM2_FRAC = 1.5  # top (lock) arm length = this * peg length

# --- Derived tray envelope (formerly imported from wispwood.py) --------------
OUTER_WIDTH = 2 * cfg.WALL_LONG + 2 * cfg.POCKET_WIDTH + cfg.DIVIDER_THICKNESS
RAIL_Z0 = cfg.FLOOR_THICKNESS + cfg.POCKET_DEPTH
WALL_TOP = RAIL_Z0 + cfg.LID_THICKNESS + cfg.LID_SLIDE_CLEARANCE + cfg.LID_TOP_LIP
OUTER_LENGTH = cfg.POCKET_LENGTH + 2 * cfg.WALL_END

# --- Folding-stand slot path (Y from front, Z from floor) --------------------
_STAND_VA = math.radians(STAND_V_ANGLE_DEG)
STAND_LEG_LEN = OUTER_LENGTH * STAND_LEG_LENGTH_FRAC
STAND_LEG_ZC = WALL_TOP / 2.0
_STAND_MARGIN = (STAND_LEG_WIDTH - STAND_PEG_WIDTH) / 2.0
STAND_FOLDED = (STAND_LEG_LEN - _STAND_MARGIN - STAND_PEG_LENGTH / 2.0, STAND_LEG_ZC)
STAND_VERTEX = (STAND_FOLDED[0] - STAND_SLOT_ARM_LEN, STAND_FOLDED[1])
STAND_JOG_TOP = (STAND_VERTEX[0], STAND_VERTEX[1] + STAND_JOG_FRAC * STAND_PEG_WIDTH)
_STAND_ARM2 = STAND_ARM2_FRAC * STAND_PEG_LENGTH
STAND_LOCK = (
    STAND_JOG_TOP[0] + _STAND_ARM2 * math.cos(_STAND_VA),
    STAND_JOG_TOP[1] + _STAND_ARM2 * math.sin(_STAND_VA),
)


def _box(x, y, z, dx, dy, dz):
    """Return an axis-aligned box solid with minimum corner ``(x, y, z)``."""
    return Part.makeBox(dx, dy, dz, Vector(x, y, z))


def _prism_yz(points_yz, x0, depth):
    """Extrude a closed Y-Z profile (list of ``(y, z)``) ``depth`` along ``+X`` from ``x0``."""
    pts = [Vector(x0, y, z) for y, z in points_yz]
    pts.append(pts[0])
    face = Part.Face(Part.makePolygon(pts))
    return face.extrude(Vector(depth, 0.0, 0.0))


def _channel(p1, p2, width, x0, depth):
    """Return a round-ended channel between two Y-Z points, extruded ``depth`` along X."""
    (y1, z1), (y2, z2) = p1, p2
    length = math.hypot(y2 - y1, z2 - z1)
    uy, uz = (y2 - y1) / length, (z2 - z1) / length
    ny, nz = -uz, uy
    hw = width / 2.0
    rect = _prism_yz(
        [
            (y1 + ny * hw, z1 + nz * hw),
            (y2 + ny * hw, z2 + nz * hw),
            (y2 - ny * hw, z2 - nz * hw),
            (y1 - ny * hw, z1 - nz * hw),
        ],
        x0,
        depth,
    )
    cap1 = Part.makeCylinder(hw, depth, Vector(x0, y1, z1), Vector(1.0, 0.0, 0.0))
    cap2 = Part.makeCylinder(hw, depth, Vector(x0, y2, z2), Vector(1.0, 0.0, 0.0))
    return rect.fuse(cap1).fuse(cap2)


def _oval_peg(y, z, x0, xlen):
    """Return an oval/bar peg (stadium in Y-Z, major along Y) extruded ``xlen`` along X."""
    hw = STAND_PEG_WIDTH / 2.0
    half = STAND_PEG_LENGTH / 2.0 - hw
    box = _prism_yz(
        [(y - half, z - hw), (y + half, z - hw), (y + half, z + hw), (y - half, z + hw)],
        x0,
        xlen,
    )
    c1 = Part.makeCylinder(hw, xlen, Vector(x0, y - half, z), Vector(1.0, 0.0, 0.0))
    c2 = Part.makeCylinder(hw, xlen, Vector(x0, y + half, z), Vector(1.0, 0.0, 0.0))
    return box.fuse(c1).fuse(c2)


def _stand_slot_cutter(x0, depth):
    """Return the stand slot cutter for one long wall: parallel arm + jog + top arm."""
    width = STAND_PEG_WIDTH + STAND_SLOT_CLEARANCE
    peg_half = STAND_PEG_LENGTH / 2.0
    folded_end = (STAND_FOLDED[0] + peg_half, STAND_FOLDED[1])
    arm1 = _channel(STAND_VERTEX, folded_end, width, x0, depth)
    jog = _channel(STAND_VERTEX, STAND_JOG_TOP, width, x0, depth)
    arm2 = _channel(STAND_JOG_TOP, STAND_LOCK, width, x0, depth)
    return arm1.fuse(jog).fuse(arm2)


def _leg(x0):
    """Return one leg (flush at ``x0``) with its free (back) end rounded to a half-circle."""
    t, w, base_d = STAND_THICKNESS, STAND_LEG_WIDTH, STAND_BASE_DEPTH
    zc = STAND_LEG_ZC
    r = w / 2.0
    back_y = STAND_LEG_LEN
    straight = _box(x0, -base_d, zc - r, t, (back_y - r) - (-base_d), w)
    cap = Part.makeCylinder(r, t, Vector(x0, back_y - r, zc), Vector(1.0, 0.0, 0.0))
    return straight.fuse(cap)


def _leg_base_gussets(x0):
    """Return 45-degree chamfer gussets reinforcing one leg's junction with the base."""
    t, w, ch = STAND_THICKNESS, STAND_LEG_WIDTH, STAND_CHAMFER
    z_top, z_bot = STAND_LEG_ZC + w / 2.0, STAND_LEG_ZC - w / 2.0
    top = _prism_yz([(0.0, z_top), (ch, z_top), (0.0, z_top + ch)], x0, t)
    bottom = _prism_yz([(0.0, z_bot), (ch, z_bot), (0.0, z_bot - ch)], x0, t)
    return top.fuse(bottom)


def build_stand():
    """Build the folding stand: two rounded-end legs + a base panel that covers them."""
    t, base_d = STAND_THICKNESS, STAND_BASE_DEPTH
    g = STAND_BODY_GAP
    yf, zf = STAND_FOLDED

    left_leg_x0 = -t - g
    right_leg_x0 = OUTER_WIDTH + g
    left_leg = _leg(left_leg_x0)
    right_leg = _leg(right_leg_x0)
    base = _box(left_leg_x0, -base_d, 0.0, (right_leg_x0 + t) - left_leg_x0, base_d, WALL_TOP)
    gussets = _leg_base_gussets(left_leg_x0).fuse(_leg_base_gussets(right_leg_x0))
    left_peg = _oval_peg(yf, zf, -g, STAND_PEG_DEPTH + g)
    right_peg = _oval_peg(yf, zf, OUTER_WIDTH - STAND_PEG_DEPTH, STAND_PEG_DEPTH + g)

    return left_leg.fuse(right_leg).fuse(base).fuse(gussets).fuse(left_peg).fuse(right_peg)


def build_stand_deployed():
    """Return a NON-PRINTING copy of the stand posed at the slot's lock (deployed) position."""
    shape = build_stand()
    fy, fz = STAND_FOLDED
    arm_y, arm_z = math.cos(_STAND_VA), math.sin(_STAND_VA)
    detent_r = (STAND_PEG_WIDTH + STAND_SLOT_CLEARANCE) / 2.0
    ly = STAND_LOCK[0] + detent_r * arm_y
    lz = STAND_LOCK[1] + detent_r * arm_z
    shape.rotate(Vector(0.0, fy, fz), Vector(1.0, 0.0, 0.0), STAND_V_ANGLE_DEG)
    shape.translate(Vector(0.0, ly - fy, lz - fz))
    return shape
