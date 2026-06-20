"""Geometry builders for the Wispwood tile holder (custom design).

Builds the tray and the two-part sliding lid from the parameters in :mod:`config`,
using the FreeCAD ``Part`` workbench. Intended to be driven by ``Wispwood.FCMacro``
inside FreeCAD 1.0.2 (see the repository ``CLAUDE.md``).

Coordinate system
-----------------
- Origin at the front-left-bottom outer corner of the tray.
- ``X`` is width (across the two pockets), ``Y`` is length (along each tile stack; the
  front/dispensing end is at ``Y = 0``), ``Z`` is up.

Mechanism
---------
- The tray has two equal-height solid **end walls** (front and back), each rising to the
  lid underside, with a deep **finger scoop** per pocket for tile access from either end.
- The **lid** is a flat plate that slides in the side rails, inserted/removed at the **back**.
  The rails stop short of the front by ``LID_FRONT_STOP_GAP`` above the inside front surface,
  forming a stop that leaves a top-front **dispensing gap**. The large lid has a **reversible
  end cutout**: inserted cutout-end first it passes the stop and **closes the gap** (storage);
  reversed, it stops at the rail and **leaves the gap open**, so with the tray tilted/suspended
  by the folding stand the front tile slides up and out through that gap into the user's hand.
- A **folding stand** of two rounded-end legs (half the tray length) joined by a front
  base panel that covers them (chamfered gussets at the junction). Each leg's oval peg
  rides a slot in the tray side wall: along the horizontal **parallel arm** to the vertex
  (hinge, toward the front), a short **jog up**, then a short tilted **top arm** to the
  lock. Modelled folded.

Lid/slot fit (single source of truth)
-------------------------------------
The lid cross-section is defined once in :func:`_lid_xsection`. The tray's lid slot is
that *same* section grown by ``LID_SLIDE_CLEARANCE`` (:func:`build_lid_slot_cutter`) and
cut from the tray, so the fit is exact and lives in one place. The lid's top sliding
edges are chamfered over the full groove depth (45 deg), so the tray's retaining lip is a
clean 45 deg overhang that prints without support (no downward-pointing lip).

Public API
----------
``build_tray``, ``build_large_lid``, ``build_small_lid``, ``build_lid_slot_cutter``,
``build_stand``, ``build_stand_deployed``, ``build_all``.

All offsets are derived from named constants (never measured coordinates), per the
repository rules.
"""

import math

import config as cfg
import FreeCAD as App  # noqa: F401  (imported for parity with the macro environment)
import Part
from FreeCAD import Vector

# --- Derived outer envelope --------------------------------------------------
OUTER_WIDTH = 2 * cfg.WALL_LONG + 2 * cfg.POCKET_WIDTH + cfg.DIVIDER_THICKNESS
RAIL_Z0 = cfg.FLOOR_THICKNESS + cfg.POCKET_DEPTH  # lid underside (lid rests here)
LID_Z0 = RAIL_Z0
LID_Z1 = LID_Z0 + cfg.LID_THICKNESS
WALL_TOP = LID_Z1 + cfg.LID_SLIDE_CLEARANCE + cfg.LID_TOP_LIP  # outer (long) wall height
POCKET_Y0 = cfg.WALL_END  # front wall occupies Y[0..WALL_END]
POCKET_Y1 = POCKET_Y0 + cfg.POCKET_LENGTH  # inner face of the back wall
OUTER_LENGTH = cfg.POCKET_LENGTH + 2 * cfg.WALL_END

# --- Derived X positions -----------------------------------------------------
INNER_X0 = cfg.WALL_LONG
INNER_X1 = OUTER_WIDTH - cfg.WALL_LONG
LEFT_POCKET_X0 = INNER_X0
LEFT_POCKET_X1 = LEFT_POCKET_X0 + cfg.POCKET_WIDTH
DIVIDER_X0 = LEFT_POCKET_X1
DIVIDER_X1 = DIVIDER_X0 + cfg.DIVIDER_THICKNESS
RIGHT_POCKET_X0 = DIVIDER_X1
RIGHT_POCKET_X1 = RIGHT_POCKET_X0 + cfg.POCKET_WIDTH

# --- Derived lid extents -----------------------------------------------------
LID_X0 = cfg.WALL_LONG - cfg.RAIL_DEPTH  # lid edge reaches into the side grooves
LID_X1 = INNER_X1 + cfg.RAIL_DEPTH
# The lid slot is open at the BACK (lid inserts/removes there) but stops short of the front
# by LID_FRONT_STOP_GAP above the inside front surface; that stop leaves a top-front
# dispensing gap (which the large lid's reversible end cutout can pass to close).
LID_SLOT_Y0 = POCKET_Y0 + cfg.LID_FRONT_STOP_GAP  # front stop of the slot
LID_SLOT_Y1 = OUTER_LENGTH  # open back end
LARGE_LID_Y1 = POCKET_Y0 + cfg.LID_SPLIT_TILE * cfg.TILE_THICKNESS

# Pocket centres (X) used for the finger scoops.
POCKET_CENTRES_X = (
    (LEFT_POCKET_X0 + LEFT_POCKET_X1) / 2.0,
    (RIGHT_POCKET_X0 + RIGHT_POCKET_X1) / 2.0,
)

# Folding stand: leg geometry and the derived V-slot points (Y from front, Z from floor).
# The leg is centred between the box top and bottom; the oval rests at the back of the leg
# with equal top/bottom/back margins. The V vertex (hinge) points toward the FRONT, with
# one arm horizontal (folded peg rest) and the other tilted up by STAND_V_ANGLE_DEG (lock).
_STAND_VA = math.radians(cfg.STAND_V_ANGLE_DEG)
STAND_LEG_LEN = OUTER_LENGTH * cfg.STAND_LEG_LENGTH_FRAC
STAND_LEG_ZC = WALL_TOP / 2.0  # leg centred between the box top and bottom
_STAND_MARGIN = (cfg.STAND_LEG_WIDTH - cfg.STAND_PEG_WIDTH) / 2.0  # equal margin
# Folded rest at the back of the leg; horizontal arm runs forward to the vertex.
STAND_FOLDED = (
    STAND_LEG_LEN - _STAND_MARGIN - cfg.STAND_PEG_LENGTH / 2.0,
    STAND_LEG_ZC,
)
STAND_VERTEX = (STAND_FOLDED[0] - cfg.STAND_SLOT_ARM_LEN, STAND_FOLDED[1])
# Short vertical jog up (the lift), then the short tilted top arm to the lock.
STAND_JOG_TOP = (
    STAND_VERTEX[0],
    STAND_VERTEX[1] + cfg.STAND_JOG_FRAC * cfg.STAND_PEG_WIDTH,
)
_STAND_ARM2 = cfg.STAND_ARM2_FRAC * cfg.STAND_PEG_LENGTH
STAND_LOCK = (
    STAND_JOG_TOP[0] + _STAND_ARM2 * math.cos(_STAND_VA),
    STAND_JOG_TOP[1] + _STAND_ARM2 * math.sin(_STAND_VA),
)


def _box(x, y, z, dx, dy, dz):
    """Return an axis-aligned box solid with minimum corner ``(x, y, z)``."""
    return Part.makeBox(dx, dy, dz, Vector(x, y, z))


def _prism_xz(points_xz, y0, length):
    """Extrude a closed X-Z profile along ``+Y`` into a solid.

    Parameters
    ----------
    points_xz : list of tuple of float
        Profile vertices ``(x, z)`` in order; the polygon is auto-closed.
    y0 : float
        Y of the profile plane (mm).
    length : float
        Extrusion distance along ``+Y`` (mm).

    Returns
    -------
    Part.Shape
        The extruded solid.
    """
    pts = [Vector(x, y0, z) for x, z in points_xz]
    pts.append(pts[0])
    face = Part.Face(Part.makePolygon(pts))
    return face.extrude(Vector(0.0, length, 0.0))


def _lid_xsection(clearance, width_inflate=0.0):
    """Return the lid's X-Z cross-section, optionally grown outward.

    This is the single source of truth for the lid profile. ``clearance == 0`` gives the
    lid itself; a positive ``clearance`` gives the tray slot section (the lid grown by the
    fit tolerance). The top sliding edges are chamfered by ``LID_BEVEL`` so the tray's
    retaining lip is a 45 deg, support-free overhang.

    ``width_inflate`` grows the profile only in X (each rail edge outward by this amount),
    leaving Z unchanged. The lid uses it to widen into the rail grooves for a tighter
    friction fit; the slot does not, so the side clearance shrinks while the Z fit is kept.

    Parameters
    ----------
    clearance : float
        Amount to grow the section outward on every side (mm).
    width_inflate : float, optional
        Extra growth applied per side in X only (mm). Default ``0.0``.

    Returns
    -------
    list of tuple of float
        ``(x, z)`` profile vertices, ordered, ready for :func:`_prism_xz`.
    """
    x0 = LID_X0 - clearance - width_inflate
    x1 = LID_X1 + clearance + width_inflate
    zb = LID_Z0 - clearance
    zt = LID_Z1 + clearance
    b = cfg.LID_BEVEL
    return [
        (x0, zb),
        (x1, zb),
        (x1, zt - b),
        (x1 - b, zt),
        (x0 + b, zt),
        (x0, zt - b),
    ]


def build_lid_slot_cutter():
    """Return the tool that cuts the lid slot in the tray (lid section + clearance).

    It is the lid cross-section grown by ``LID_SLIDE_CLEARANCE`` and swept from the front
    stop (``LID_SLOT_Y0``) to the open back (``LID_SLOT_Y1``), so subtracting it from the tray
    yields a slot that fits the lid exactly and stops short of the front. Also exposed on its
    own (hidden) so it can be inspected in FreeCAD.

    Returns
    -------
    Part.Shape
        The slot cutter solid.
    """
    return _prism_xz(_lid_xsection(cfg.LID_SLIDE_CLEARANCE), LID_SLOT_Y0, LID_SLOT_Y1 - LID_SLOT_Y0)


def _finger_scoop(cx, wall_y0):
    """Return a deep, round-bottomed finger-scoop cutter for an end wall.

    Parameters
    ----------
    cx : float
        Pocket centre X (mm).
    wall_y0 : float
        Y of the end wall's minimum-Y face; the cutter spans the wall thickness with a
        1 mm margin on each side.

    Returns
    -------
    Part.Shape
        The scoop cutter solid.
    """
    r = cfg.SCOOP_WIDTH / 2.0
    bottom_z = cfg.FLOOR_THICKNESS + (1.0 - cfg.SCOOP_DEPTH_FRACTION) * cfg.POCKET_DEPTH
    centre_z = bottom_z + r
    y0 = wall_y0 - 1.0
    ylen = cfg.WALL_END + 2.0
    slot = _box(cx - r, y0, centre_z, 2.0 * r, ylen, (WALL_TOP + 1.0) - centre_z)
    round_bottom = Part.makeCylinder(r, ylen, Vector(cx, y0, centre_z), Vector(0.0, 1.0, 0.0))
    return slot.fuse(round_bottom)


def _chamfer_scoop_edges(tray):
    """Chamfer each scoop's outer-face and top edges (best-effort; returns tray if it fails).

    Selects edges in the scoop X-region that lie wholly on an end wall's top (Z = end-wall
    top) or outer face (Y = 0 or Y = OUTER_LENGTH) and chamfers them so fingers clear the
    edges. Edge selection is geometric, so it is wrapped defensively.
    """
    top_z = cfg.FLOOR_THICKNESS + cfg.END_WALL_HEIGHT
    r = cfg.SCOOP_WIDTH / 2.0
    outer_ys = (0.0, OUTER_LENGTH)
    tol = 0.3

    def near_scoop_x(bb):
        mid = 0.5 * (bb.XMin + bb.XMax)
        return any(abs(mid - cx) <= r + 0.5 for cx in POCKET_CENTRES_X)

    selected = []
    for e in tray.Edges:
        bb = e.BoundBox
        if not near_scoop_x(bb):
            continue
        at_top = abs(bb.ZMin - top_z) < tol and abs(bb.ZMax - top_z) < tol
        at_outer = any(abs(bb.YMin - y) < tol and abs(bb.YMax - y) < tol for y in outer_ys)
        if at_top or at_outer:
            selected.append(e)
    if not selected:
        return tray
    try:
        return tray.makeChamfer(cfg.SCOOP_CHAMFER, selected)
    except Exception:
        return tray


def _diag_slot(yc, zc, x0, depth, length, width, angle_deg):
    """Return a diagonal stadium (round-ended) slot, extruded ``depth`` along ``+X``.

    A capsule in the Y-Z plane: two end caps of diameter ``width`` separated along a line at
    ``angle_deg`` above horizontal and centred on ``(yc, zc)``, swept ``depth`` through the
    wall. Used to lighten and add grip to the long side walls.

    Parameters
    ----------
    yc, zc : float
        Slot centre in the Y-Z plane (mm).
    x0 : float
        Start X of the through-cut (mm).
    depth : float
        Cut distance along ``+X`` (mm).
    length, width : float
        Stadium overall length (along the diagonal) and width (across) (mm).
    angle_deg : float
        Tilt of the slot above horizontal (deg).

    Returns
    -------
    Part.Shape
        The slot cutter solid.
    """
    cap = length - width  # cap-centre separation so the overall length includes the caps
    a = math.radians(angle_deg)
    dy, dz = math.cos(a), math.sin(a)
    c1 = Vector(x0, yc - dy * cap / 2.0, zc - dz * cap / 2.0)
    c2 = Vector(x0, yc + dy * cap / 2.0, zc + dz * cap / 2.0)
    slot = Part.makeCylinder(width / 2.0, depth, c1, Vector(1.0, 0.0, 0.0))
    slot = slot.fuse(Part.makeCylinder(width / 2.0, depth, c2, Vector(1.0, 0.0, 0.0)))
    bar = Part.makeBox(depth, cap, width, Vector(0.0, -cap / 2.0, -width / 2.0))
    bar.rotate(Vector(0.0, 0.0, 0.0), Vector(1.0, 0.0, 0.0), angle_deg)
    bar.translate(Vector(x0, yc, zc))
    return slot.fuse(bar)


# Divot X positions on the tray's min-Y front face, derived from the stand peg inset so the
# tray registers onto the stand pegs. The stand is wider than the tray by the side lips, so the
# tray (centred on it) maps the stand pegs inward by that half-difference.
_STAND_HALF_EXTRA = cfg.ALT_SHELF_SIDE_LIP_W + cfg.ALT_SHELF_SIDE_CLEAR
DIVOT_XS = (
    cfg.ALT_PEG_INSET - _STAND_HALF_EXTRA,
    OUTER_WIDTH + _STAND_HALF_EXTRA - cfg.ALT_PEG_INSET,
)


def _stand_divot(dx, dz):
    """Return a cutter for one stand-peg divot in the tray's min-Y front face (enters ``+Y``).

    A lofted negative of the stand locating peg (matching dimensions grown by
    ``ALT_PEG_CLEAR``): narrow in X, tapering in Z, mouth at the ``Y = 0`` front face and
    narrowing inward, so the tray snaps onto the peg.

    Parameters
    ----------
    dx, dz : float
        Divot centre on the front face (X across the tray, Z up the wall).

    Returns
    -------
    Part.Shape
        The divot cutter solid.
    """
    clr = cfg.ALT_PEG_CLEAR
    xw = cfg.ALT_LIP_PEG_W / 2.0 + clr  # narrow half-width in X
    zb = cfg.ALT_LIP_PEG_R + clr  # mouth half-height in Z
    zt = cfg.ALT_LIP_PEG_TOP_R + clr  # tip half-height in Z
    dep = cfg.ALT_LIP_PEG_H

    def _rect(y, zh):
        pts = [
            Vector(dx - xw, y, dz - zh),
            Vector(dx + xw, y, dz - zh),
            Vector(dx + xw, y, dz + zh),
            Vector(dx - xw, y, dz + zh),
        ]
        pts.append(pts[0])
        return Part.makePolygon(pts)

    mouth = _rect(-0.5, zb)  # slightly proud of the front face (Y = 0)
    tip = _rect(dep, zt)  # deepest point inside the wall
    return Part.makeLoft([mouth, tip], True)


def build_tray():
    """Build the tray: floor, walls, end walls, divider, lid slot, scoops, grip slots.

    Returns
    -------
    Part.Shape
        The tray solid.
    """
    wall_h = WALL_TOP - cfg.FLOOR_THICKNESS
    inner_w = INNER_X1 - INNER_X0

    floor = _box(0, 0, 0, OUTER_WIDTH, OUTER_LENGTH, cfg.FLOOR_THICKNESS)
    left_wall = _box(0, 0, cfg.FLOOR_THICKNESS, cfg.WALL_LONG, OUTER_LENGTH, wall_h)
    right_wall = _box(INNER_X1, 0, cfg.FLOOR_THICKNESS, cfg.WALL_LONG, OUTER_LENGTH, wall_h)
    # Front and back end walls are identical, both rising to the lid underside so the
    # lid can slide out either end (held by rail friction).
    front_wall = _box(INNER_X0, 0, cfg.FLOOR_THICKNESS, inner_w, cfg.WALL_END, cfg.END_WALL_HEIGHT)
    back_wall = _box(
        INNER_X0,
        POCKET_Y1,
        cfg.FLOOR_THICKNESS,
        inner_w,
        cfg.WALL_END,
        cfg.END_WALL_HEIGHT,
    )
    # Divider stops below the lid so the single lid spans both pockets.
    divider = _box(
        DIVIDER_X0,
        0,
        cfg.FLOOR_THICKNESS,
        cfg.DIVIDER_THICKNESS,
        POCKET_Y1,
        RAIL_Z0 - cfg.FLOOR_THICKNESS,
    )

    tray = floor.fuse(left_wall).fuse(right_wall).fuse(front_wall).fuse(back_wall).fuse(divider)

    # Lid slot: the lid grown by the fit tolerance, cut once from the tray. This forms the
    # beveled side rails and gives the lid clearance over the end walls and divider.
    tray = tray.cut(build_lid_slot_cutter())

    # Deep finger scoops in both end walls, one per pocket, then chamfer their edges.
    for cx in POCKET_CENTRES_X:
        tray = tray.cut(_finger_scoop(cx, 0.0))  # front wall (min-Y face at 0)
        tray = tray.cut(_finger_scoop(cx, POCKET_Y1))  # back wall
    tray = _chamfer_scoop_edges(tray)

    # Diagonal rounded grip/lightening slots cut through both long side walls, in the pocket
    # zone below the lid rails, to save plastic and improve grip.
    z_mid = (cfg.FLOOR_THICKNESS + RAIL_Z0) / 2.0
    y0 = cfg.WALL_END + cfg.GRIP_SLOT_LENGTH / 2.0 + 2.0
    y1 = OUTER_LENGTH - cfg.WALL_END - cfg.GRIP_SLOT_LENGTH / 2.0 - 2.0
    for i in range(cfg.GRIP_SLOT_COUNT):
        yc = y0 + (y1 - y0) * (i + 0.5) / cfg.GRIP_SLOT_COUNT
        for x0 in (-1.0, INNER_X1 - 1.0):  # left and right long walls (through-cut, overcut)
            tray = tray.cut(
                _diag_slot(
                    yc,
                    z_mid,
                    x0,
                    cfg.WALL_LONG + 2.0,
                    cfg.GRIP_SLOT_LENGTH,
                    cfg.GRIP_SLOT_WIDTH,
                    cfg.GRIP_SLOT_ANGLE,
                )
            )

    # Stand-peg divots in the min-Y front face, so the tray snaps onto the stand's locating pegs.
    for dx in DIVOT_XS:
        tray = tray.cut(_stand_divot(dx, cfg.ALT_DIVOT_Z))

    return tray


def _lid_prism(y0, y1):
    """Return a flat lid plate (single-source section) spanning ``Y[y0..y1]``.

    The section is widened in X by half of ``LID_WIDTH_FRICTION`` per side (the slot is
    not), tightening the rail-groove fit so the lid stays put while still sliding.
    """
    return _prism_xz(_lid_xsection(0.0, cfg.LID_WIDTH_FRICTION / 2.0), y0, y1 - y0)


def _lid_end_cutout(y_front):
    """Return the cutter that strips the rail tabs from one end of the large lid.

    Removing the groove-engaging tabs over ``LID_FRONT_STOP_GAP`` of length on this end lets
    it pass the tray's lid-slot stop, so the lid reaches the inside front surface and closes
    the dispensing gap. Inserted the other way (plain end forward), the full tabs meet the
    stop and the gap stays open. The cut also clears ``LID_SLIDE_CLEARANCE`` into the plate so
    the stripped end slides between the (solid, ungrooved) long walls of the stop region.

    Parameters
    ----------
    y_front : float
        Y of the lid's cutout end face (mm).

    Returns
    -------
    Part.Shape
        The cutout tool (the two side strips).
    """
    clr = cfg.LID_SLIDE_CLEARANCE
    m = 1.0  # over-cut margin so the end and top/bottom faces are cleanly removed
    y0 = y_front - m
    ylen = cfg.LID_FRONT_STOP_GAP + m  # back face lands exactly at the slot stop
    z0 = LID_Z0 - m
    zlen = (LID_Z1 + m) - z0
    left = _box(LID_X0 - m, y0, z0, (cfg.WALL_LONG + clr) - (LID_X0 - m), ylen, zlen)
    right_x0 = INNER_X1 - clr
    right = _box(right_x0, y0, z0, (LID_X1 + m) - right_x0, ylen, zlen)
    return left.fuse(right)


def build_large_lid():
    """Build the large (game-use) flat lid: pocket front through tile ``LID_SPLIT_TILE``.

    Spans the pocket interior from the inside front surface (``POCKET_Y0``) back to the lid
    split, with a reversible end cutout (:func:`_lid_end_cutout`). Inserted cutout-end first,
    the lid passes the tray's slot stop and closes the dispensing gap (storage); reversed, it
    stops at the slot, leaving the gap open. Built in the closed (gap-closed) position.

    Returns
    -------
    Part.Shape
        The large lid solid.
    """
    lid = _lid_prism(POCKET_Y0, LARGE_LID_Y1)
    return lid.cut(_lid_end_cutout(POCKET_Y0))


def build_small_lid():
    """Build the small (storage) flat lid that seals the back region.

    Returns
    -------
    Part.Shape
        The small lid solid.
    """
    return _lid_prism(LARGE_LID_Y1, POCKET_Y1)


# --- Folding stand -----------------------------------------------------------


def _prism_yz(points_yz, x0, depth):
    """Extrude a closed Y-Z profile along ``+X`` into a solid.

    Parameters
    ----------
    points_yz : list of tuple of float
        Profile vertices ``(y, z)`` in order; the polygon is auto-closed.
    x0 : float
        X of the profile plane (mm).
    depth : float
        Extrusion distance along ``+X`` (mm).

    Returns
    -------
    Part.Shape
        The extruded solid.
    """
    pts = [Vector(x0, y, z) for y, z in points_yz]
    pts.append(pts[0])
    face = Part.Face(Part.makePolygon(pts))
    return face.extrude(Vector(depth, 0.0, 0.0))


def _channel(p1, p2, width, x0, depth):
    """Return a round-ended channel between two Y-Z points, extruded ``depth`` along X."""
    (y1, z1), (y2, z2) = p1, p2
    length = math.hypot(y2 - y1, z2 - z1)
    uy, uz = (y2 - y1) / length, (z2 - z1) / length
    ny, nz = -uz, uy  # unit normal in the Y-Z plane
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
    hw = cfg.STAND_PEG_WIDTH / 2.0
    half = cfg.STAND_PEG_LENGTH / 2.0 - hw
    box = _prism_yz(
        [
            (y - half, z - hw),
            (y + half, z - hw),
            (y + half, z + hw),
            (y - half, z + hw),
        ],
        x0,
        xlen,
    )
    c1 = Part.makeCylinder(hw, xlen, Vector(x0, y - half, z), Vector(1.0, 0.0, 0.0))
    c2 = Part.makeCylinder(hw, xlen, Vector(x0, y + half, z), Vector(1.0, 0.0, 0.0))
    return box.fuse(c1).fuse(c2)


def _stand_slot_cutter(x0, depth):
    """Return the stand slot cutter for one long wall: parallel arm + jog + top arm.

    Constant-width round-ended channels (no keyhole pockets): a horizontal "parallel" arm
    (the folded peg rest, hinge end toward the front), a short vertical jog up at the
    vertex (the peg lifts before locking), and a short tilted "top" arm to the lock.

    Parameters
    ----------
    x0 : float
        Inner X where the blind slot starts; it is cut ``depth`` further along ``+X``.
    depth : float
        Slot depth into the wall (mm).

    Returns
    -------
    Part.Shape
        The slot cutter solid.
    """
    width = cfg.STAND_PEG_WIDTH + cfg.STAND_SLOT_CLEARANCE
    peg_half = cfg.STAND_PEG_LENGTH / 2.0
    # Extend the horizontal arm past the folded rest (toward the back) so the oval is
    # fully captured at rest.
    folded_end = (STAND_FOLDED[0] + peg_half, STAND_FOLDED[1])
    arm1 = _channel(STAND_VERTEX, folded_end, width, x0, depth)  # horizontal "parallel" arm
    jog = _channel(STAND_VERTEX, STAND_JOG_TOP, width, x0, depth)  # short vertical lift
    arm2 = _channel(STAND_JOG_TOP, STAND_LOCK, width, x0, depth)  # short tilted top arm
    return arm1.fuse(jog).fuse(arm2)


def _leg(x0):
    """Return one leg (flush at ``x0``) with its free (back) end rounded to a half-circle."""
    t, w, base_d = cfg.STAND_THICKNESS, cfg.STAND_LEG_WIDTH, cfg.STAND_BASE_DEPTH
    zc = STAND_LEG_ZC
    r = w / 2.0
    back_y = STAND_LEG_LEN  # free end
    straight = _box(x0, -base_d, zc - r, t, (back_y - r) - (-base_d), w)
    cap = Part.makeCylinder(r, t, Vector(x0, back_y - r, zc), Vector(1.0, 0.0, 0.0))
    return straight.fuse(cap)


def _leg_base_gussets(x0):
    """Return 45-degree chamfer gussets reinforcing one leg's junction with the base."""
    t, w, ch = cfg.STAND_THICKNESS, cfg.STAND_LEG_WIDTH, cfg.STAND_CHAMFER
    z_top, z_bot = STAND_LEG_ZC + w / 2.0, STAND_LEG_ZC - w / 2.0
    top = _prism_yz([(0.0, z_top), (ch, z_top), (0.0, z_top + ch)], x0, t)
    bottom = _prism_yz([(0.0, z_bot), (ch, z_bot), (0.0, z_bot - ch)], x0, t)
    return top.fuse(bottom)


def build_stand():
    """Build the folding stand: two rounded-end legs + a base panel that covers them.

    One springy U-shaped part. The base panel is a little wider than the box front so it
    covers the legs, the leg/base junctions are chamfered with gussets, and each leg's free
    end is rounded. Modelled folded (pegs at ``STAND_FOLDED``).

    Returns
    -------
    Part.Shape
        The stand solid.
    """
    t, base_d = cfg.STAND_THICKNESS, cfg.STAND_BASE_DEPTH
    g = cfg.STAND_BODY_GAP
    yf, zf = STAND_FOLDED

    # Each leg is offset outward by the body gap so its inner face does not touch (and
    # print fused to) the tray's outer wall. Inner faces land at x = -g and x = OUTER_WIDTH+g.
    left_leg_x0 = -t - g
    right_leg_x0 = OUTER_WIDTH + g
    left_leg = _leg(left_leg_x0)
    right_leg = _leg(right_leg_x0)
    # Base panel: a little wider than the box front so it covers both (gapped) legs.
    base = _box(left_leg_x0, -base_d, 0.0, (right_leg_x0 + t) - left_leg_x0, base_d, WALL_TOP)
    gussets = _leg_base_gussets(left_leg_x0).fuse(_leg_base_gussets(right_leg_x0))
    # Pegs project inward from each leg, bridging the gap and reaching STAND_PEG_DEPTH into
    # the wall slot (which is cut from the wall outer face at x = 0 / x = OUTER_WIDTH).
    left_peg = _oval_peg(yf, zf, -g, cfg.STAND_PEG_DEPTH + g)
    right_peg = _oval_peg(yf, zf, OUTER_WIDTH - cfg.STAND_PEG_DEPTH, cfg.STAND_PEG_DEPTH + g)

    return left_leg.fuse(right_leg).fuse(base).fuse(gussets).fuse(left_peg).fuse(right_peg)


def build_stand_deployed():
    """Return a NON-PRINTING copy of the stand posed at the slot's lock (second) position.

    The oval peg's major axis is constrained to the slot-channel direction, so between the
    folded rest (horizontal "parallel" arm) and the lock detent (tilted "top" arm) the rigid
    body rotates by ``STAND_V_ANGLE_DEG`` about the peg axis (parallel to ``X``). This builds
    the stand, rotates it by that angle about the peg axis through the folded peg centre,
    then carries the peg centre to the seated lock position. It is a view-only reference for
    comparing the folded and deployed poses -- not a part to print.

    ``STAND_LOCK`` is the top arm's *centreline* end; the slot's rounded top (the end cap)
    extends one detent radius further along the arm, so the seated peg centre is advanced by
    that radius to sit at the true top of the detent.

    Returns
    -------
    Part.Shape
        The stand solid transformed to the lock position.
    """
    shape = build_stand()
    fy, fz = STAND_FOLDED
    # Advance the lock target by one detent radius along the top-arm direction so the peg
    # seats at the rounded top of the slot (STAND_LOCK is the arm's centreline end).
    arm_y, arm_z = math.cos(_STAND_VA), math.sin(_STAND_VA)  # top-arm unit dir in (Y, Z)
    detent_r = (cfg.STAND_PEG_WIDTH + cfg.STAND_SLOT_CLEARANCE) / 2.0
    ly = STAND_LOCK[0] + detent_r * arm_y
    lz = STAND_LOCK[1] + detent_r * arm_z
    # Rotate about the peg axis (parallel to X) through the folded peg centre, so the oval
    # aligns with the top arm, then carry the peg centre to the seated lock position.
    shape.rotate(Vector(0.0, fy, fz), Vector(1.0, 0.0, 0.0), cfg.STAND_V_ANGLE_DEG)
    shape.translate(Vector(0.0, ly - fy, lz - fz))
    return shape


def build_all():
    """Build every part in assembled position, ready to add to a document.

    Returns
    -------
    list of tuple
        ``(name, shape, (r, g, b), visible, transparency)`` for each part, where
        ``transparency`` is a view-only percent (0 opaque .. 100 invisible). The tray and
        lids are made ``TRAY_LID_TRANSPARENCY`` so the tiles/fit show through; the rest are
        opaque. ``LidSlotCutter`` is the (hidden) tool used to cut the tray's lid slot,
        exposed for inspection. The integrated folding stand has been retired in favour of
        the separate stand (see ``alt_stand``); its builders remain below but are unused.
    """
    tlt = cfg.TRAY_LID_TRANSPARENCY
    parts = [
        ("Tray", build_tray(), (0.80, 0.80, 0.82), True, tlt),
        ("LidLarge", build_large_lid(), (0.20, 0.45, 0.85), True, tlt),
        ("LidSmall", build_small_lid(), (0.25, 0.70, 0.40), True, tlt),
        ("LidSlotCutter", build_lid_slot_cutter(), (0.90, 0.25, 0.25), False, 0),
    ]
    return parts
