"""The Wispwood display stand — rod-frame design (see ``stand.md``).

Three print-in-place parts that hold the tray upright at ``STAND_DEPLOY_ANGLE``:

- **Shelf** — an empty rounded rectangle drawn as a **continuous Ø(2·rod) rod path** (straight
  runs joined by quarter-torus fillets at the corners, no crossing cylinders). A crossmember
  rod carries a **tray lip** (deep at the edges, filleted down to clear the tray finger
  grooves). The bottom rod necks to **pins** for the base hinge; the crossmember rod necks for
  the leg hinge.
- **Base** — an **H** (two legs + a crossmember) hinged on the shelf bottom-rod pins. Each leg
  is a bar that **continues onto** its hinge cylinder, with the pin hole bored through both;
  each leg top carries the **lock cradle**. It folds under the shelf crossmember (47/47).
- **Leg** — hinged on the shelf crossmember (bar continued onto the cylinder, bored through).
  Its end cross-cylinder spans the **full base width** so its ends drop into the two base-leg
  cradles when deployed.

Modelled flat (print/folded orientation): parts lie in ``Z[0, 2·rod]`` with hinge axes along
``X``; the shelf extends ``+Y`` and hinges at ``Y = rod`` (bottom) and ``Y = ALT_CROSS_Y``
(crossmember). The base lock line is **computed** so the deployed shelf sits at
``STAND_DEPLOY_ANGLE``.

In-progress rebuild toward ``stand.md``; clearances and the snap lock still need print tuning.

Public API
----------
``X_LOCK``, ``BASE_LEN``, ``NATIVE_Y_MIN``, ``DISPLAY_X_OFFSET``,
``build_shelf``, ``build_base``, ``build_leg``, ``build_all``.
"""

import math

import config as cfg
import derived as d
import Part
from FreeCAD import Vector

# --- Frame / derived geometry ------------------------------------------------
W = d.ALT_SHELF_W
RR = cfg.ALT_ROD_R  # frame rod radius
T = 2.0 * RR  # part thickness (= rod diameter)
ZC = RR  # rod / part mid-plane Z
SHELF_H = cfg.ALT_SHELF_HEIGHT
CR = cfg.ALT_FRAME_CORNER_R  # frame corner fillet radius
CROSS_Y = cfg.ALT_CROSS_Y  # shelf crossmember (tray rest + leg hinge)
PIN_R = cfg.ALT_BARREL_NECK_R
NECK_XS = tuple(f * W for f in cfg.ALT_BARREL_NECK_FRACS)  # two base-hinge band centres
BORE = PIN_R + cfg.ALT_HINGE_PIN_CLEAR
ACLR = cfg.ALT_HINGE_AXIAL_CLEAR
BASE_LEG_W = cfg.ALT_BASE_LEG_WIDTH
LEG_W = cfg.ALT_LEG_WIDTH
L_LEG = cfg.ALT_LEG_LENGTH
CROSS_W = cfg.ALT_BASE_CROSS_W
LEG_CX = W / 2.0

# Base outer span (the leg end-cylinder matches this so it reaches both leg cradles).
BASE_X0 = NECK_XS[0] - BASE_LEG_W / 2.0
BASE_X1 = NECK_XS[1] + BASE_LEG_W / 2.0

# Finger-groove centres of the tray, mapped onto the (wider) shelf — the lip dips here.
_OFFSET = (W - d.OUTER_WIDTH) / 2.0
_PC_L = cfg.WALL_LONG + cfg.POCKET_WIDTH / 2.0
_PC_R = cfg.WALL_LONG + cfg.POCKET_WIDTH + cfg.DIVIDER_THICKNESS + cfg.POCKET_WIDTH / 2.0
FG_XS = (_OFFSET + _PC_L, _OFFSET + _PC_R)

# Shared-thickness (47/47) split planes for overlapping folded parts.
SPLIT_LOW = (T - cfg.ALT_SPLIT_GAP) / 2.0
SPLIT_HIGH = SPLIT_LOW + cfg.ALT_SPLIT_GAP

# Lock line (computed from the leg-hinge height and length so the shelf locks at the angle).
_THETA = math.radians(cfg.STAND_DEPLOY_ANGLE)
X_LOCK = math.sqrt(L_LEG**2 - (CROSS_Y * math.sin(_THETA)) ** 2) - CROSS_Y * math.cos(_THETA)
BASE_CROSS_Y = ZC + X_LOCK
BASE_LEN = X_LOCK + cfg.ALT_BASE_FOOT
NATIVE_Y_MIN = 0.0
DISPLAY_X_OFFSET = W + 30.0


def _box(x, y, z, dx, dy, dz):
    """Return an axis-aligned box solid with minimum corner ``(x, y, z)``."""
    return Part.makeBox(dx, dy, dz, Vector(x, y, z))


def _xcyl(r, length, x, y, z):
    """Return a cylinder of radius ``r`` along ``+X`` from ``(x, y, z)``."""
    return Part.makeCylinder(r, length, Vector(x, y, z), Vector(1.0, 0.0, 0.0))


def _ycyl(r, length, x, y, z):
    """Return a cylinder of radius ``r`` along ``+Y`` from ``(x, y, z)``."""
    return Part.makeCylinder(r, length, Vector(x, y, z), Vector(0.0, 1.0, 0.0))


def _corner(cx, cy, start_deg):
    """Return a quarter-torus frame fillet (path radius ``CR``, tube ``RR``) at a corner."""
    elbow = Part.makeTorus(CR, RR, Vector(cx, cy, ZC), Vector(0.0, 0.0, 1.0), -180.0, 180.0, 90.0)
    elbow.rotate(Vector(cx, cy, ZC), Vector(0.0, 0.0, 1.0), start_deg)
    return elbow


def _necked_rod(y, x0, x1, necks):
    """Return an X rod (Ø = 2·RR) along ``Y = y`` from ``x0`` to ``x1``, necked to pins.

    ``necks`` is an iterable of ``(centre, width)``; over each band the radius drops to
    ``PIN_R`` so a knuckle rides it as a hinge pin, with full collars between bands.
    """
    rod = _xcyl(RR, x1 - x0, x0, y, ZC)
    for nc, nw in necks:
        nx = nc - nw / 2.0
        rod = rod.cut(_xcyl(RR + 0.5, nw, nx, y, ZC))
        rod = rod.fuse(_xcyl(PIN_R, nw, nx, y, ZC))
    return rod


def _tray_lip():
    """Return the tray lip: deep at the shelf edges, filleted down to the finger-groove dips.

    A low full-width lip wall, plus a tall block from each outer edge in to the adjacent
    finger-groove centre, with a concave fillet sweeping the tall edge down to the low height
    exactly at the finger groove (so the lip cradles the tray sides but clears its scoops).
    """
    h_edge = cfg.ALT_LIP_EDGE_FRAC * d.WALL_TOP
    h_low = cfg.ALT_LIP_LOW_H
    lt = cfg.ALT_LIP_T
    ly = CROSS_Y - 1.0
    r_f = h_edge - h_low

    lip = _box(RR, ly, T, W - 2 * RR, lt, h_low)  # low lip across the whole width
    for edge_x, fg in ((0.0, FG_XS[0]), (W, FG_XS[1])):
        x_lo, x_hi = min(edge_x, fg), max(edge_x, fg)
        post = _box(x_lo, ly, T, x_hi - x_lo, lt, h_edge)
        # Concave fillet: subtract a Y-axis cylinder so the post top drops to h_low at fg.
        post = post.cut(_ycyl(r_f, lt + 2.0, fg, ly - 1.0, T + h_edge))
        lip = lip.fuse(post)
    return lip


def build_shelf():
    """Build the shelf: continuous rounded-rod frame + necked hinge rods + tray lip.

    Returns
    -------
    Part.Shape
        The shelf solid (flat orientation).
    """
    base_necks = [(nc, BASE_LEG_W + 2 * ACLR) for nc in NECK_XS]
    # Continuous rounded path: straight runs (tangent point to tangent point) + corner fillets.
    shelf = _necked_rod(RR, RR + CR, W - RR - CR, base_necks)  # bottom (base hinge pins)
    shelf = shelf.fuse(_xcyl(RR, (W - RR - CR) - (RR + CR), RR + CR, SHELF_H - RR, ZC))  # top
    shelf = shelf.fuse(_ycyl(RR, (SHELF_H - RR - CR) - (RR + CR), RR, RR + CR, ZC))  # left
    shelf = shelf.fuse(_ycyl(RR, (SHELF_H - RR - CR) - (RR + CR), W - RR, RR + CR, ZC))  # right
    shelf = shelf.fuse(_corner(RR + CR, RR + CR, 180.0))  # bottom-left
    shelf = shelf.fuse(_corner(W - RR - CR, RR + CR, 270.0))  # bottom-right
    shelf = shelf.fuse(_corner(W - RR - CR, SHELF_H - RR - CR, 0.0))  # top-right
    shelf = shelf.fuse(_corner(RR + CR, SHELF_H - RR - CR, 90.0))  # top-left

    # Crossmember rod (necked at centre for the leg hinge).
    shelf = shelf.fuse(_necked_rod(CROSS_Y, RR, W - RR, [(LEG_CX, LEG_W + 2 * ACLR)]))

    # 47/47: base folds under the crossmember, so remove the crossmember lower half in the two
    # base-leg bands (the base keeps the lower there).
    for nc in NECK_XS:
        shelf = shelf.cut(
            _box(
                nc - BASE_LEG_W / 2.0 - 1.0,
                CROSS_Y - RR - 1.0,
                -1.0,
                BASE_LEG_W + 2.0,
                2 * RR + 2.0,
                SPLIT_HIGH + 1.0,
            )
        )

    shelf = shelf.fuse(_tray_lip())
    return shelf


def _lock_cradle(nc):
    """Return a lock cradle on one base leg: a raised boss with a concave seat for the leg rod."""
    x0 = nc - BASE_LEG_W / 2.0
    boss = _box(x0, BASE_CROSS_Y - RR - 1.0, T, BASE_LEG_W, 2 * RR + 2.0, RR + 1.0)
    seat = _xcyl(RR + cfg.ALT_SNAP_CLEAR, BASE_LEG_W + 2.0, x0 - 1.0, BASE_CROSS_Y, T + RR + 1.0)
    return boss.cut(seat)


def _base_leg(nc):
    """Return one H leg: a bar continued onto its hinge cylinder, bored for the pin."""
    x0 = nc - BASE_LEG_W / 2.0
    bar = _box(x0, ZC, 0.0, BASE_LEG_W, BASE_LEN, T)  # from the hinge axis up
    leg = bar.fuse(_xcyl(RR, BASE_LEG_W, x0, ZC, ZC))  # rounded hinge end
    leg = leg.cut(_xcyl(BORE, BASE_LEG_W + 2.0, x0 - 1.0, ZC, ZC))  # pin hole through both
    # 47/47: keep only the lower part where the leg passes under the shelf crossmember.
    leg = leg.cut(_box(x0 - 1.0, CROSS_Y - RR - 1.0, SPLIT_LOW, BASE_LEG_W + 2.0, 2 * RR + 2.0, T))
    leg = leg.fuse(_lock_cradle(nc))
    return leg


def build_base():
    """Build the base: an H (two hinged legs + crossmember), with a lock cradle on each leg.

    Returns
    -------
    Part.Shape
        The base solid (flat orientation).
    """
    base = _base_leg(NECK_XS[0]).fuse(_base_leg(NECK_XS[1]))

    # Unbroken crossmember joining the two legs on the lock line.
    cross = _box(NECK_XS[0], BASE_CROSS_Y - CROSS_W / 2.0, 0.0, NECK_XS[1] - NECK_XS[0], CROSS_W, T)
    base = base.fuse(cross)

    # 47/47: the leg rests over the base crossmember, so remove the crossmember upper half in
    # the prop-leg band (the base keeps the lower there).
    base = base.cut(
        _box(
            LEG_CX - LEG_W / 2.0 - 1.0,
            BASE_CROSS_Y - CROSS_W / 2.0 - 1.0,
            SPLIT_HIGH,
            LEG_W + 2.0,
            CROSS_W + 2.0,
            T,
        )
    )
    return base


def build_leg():
    """Build the prop leg: a bar continued onto its hinge cylinder + a base-width end cylinder.

    Returns
    -------
    Part.Shape
        The leg solid (flat orientation).
    """
    x0 = LEG_CX - LEG_W / 2.0
    tip_y = CROSS_Y + L_LEG
    bar = _box(x0, CROSS_Y, 0.0, LEG_W, L_LEG, T)  # from the hinge axis up
    leg = bar.fuse(_xcyl(RR, LEG_W, x0, CROSS_Y, ZC))  # rounded hinge end
    leg = leg.cut(_xcyl(BORE, LEG_W + 2.0, x0 - 1.0, CROSS_Y, ZC))  # pin hole through both

    # End cross-cylinder spanning the full base width (its ends seat in the base-leg cradles).
    leg = leg.fuse(_xcyl(RR, BASE_X1 - BASE_X0, BASE_X0, tip_y, ZC))

    # 47/47: keep only the upper part where the leg rests over the base crossmember.
    leg = leg.cut(
        _box(
            x0 - 1.0,
            BASE_CROSS_Y - CROSS_W / 2.0 - 1.0,
            -1.0,
            LEG_W + 2.0,
            CROSS_W + 2.0,
            SPLIT_LOW + 1.0,
        )
    )
    return leg


def build_all():
    """Build the stand parts, offset beside the tray for standalone review.

    Returns
    -------
    list of tuple
        ``[(name, shape, (r, g, b), visible, transparency)]``; empty when ``SHOW_ALT_STAND``
        is false. ``place_stand`` in :mod:`box_insert` repositions these into the box.
    """
    if not cfg.SHOW_ALT_STAND:
        return []
    assert L_LEG > CROSS_Y * math.sin(_THETA), "leg too short to reach the table at the lock angle"
    assert CROSS_Y + L_LEG < SHELF_H, "leg does not fit folded between the crossmember and top"
    tr = cfg.ALT_STAND_TRANSPARENCY
    parts = []
    for name, shape, rgb in (
        ("StandShelf", build_shelf(), (0.55, 0.40, 0.80)),
        ("StandBase", build_base(), (0.25, 0.65, 0.55)),
        ("StandLeg", build_leg(), (0.85, 0.55, 0.20)),
    ):
        shape.translate(Vector(DISPLAY_X_OFFSET, 0.0, 0.0))
        parts.append((name, shape, rgb, True, tr))
    return parts
