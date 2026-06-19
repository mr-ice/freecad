"""The Wispwood display stand — rod-frame design (see ``stand.md``).

Three print-in-place parts that hold the tray upright at ``STAND_DEPLOY_ANGLE``:

- **Shelf** — an empty rounded rectangle drawn as a **continuous rod path** (straight runs
  joined by quarter-torus corner fillets, no crossing cylinders). A crossmember rod carries a
  **tray lip** (deep at the edges, filleted down to clear the tray finger grooves). The bottom
  rod necks to **pins** for the base hinge; the crossmember rod necks for the leg hinge.
- **Base** — an **H** (two legs + crossmember) hinged on the shelf bottom-rod pins. Each leg is
  a bar that **continues onto** its hinge cylinder, pin hole bored through both; each leg top
  carries a **lock cradle**. It folds under the shelf crossmember (47/47).
- **Leg** — hinged on the shelf crossmember (bar continued onto the cylinder, bored through).
  Its end cross-cylinder spans the **full base width** so its ends seat in the leg cradles.

Rods are a Ø(2·``ALT_ROD_R``) profile **flattened to ``ALT_PART_T`` in Z** (flat top/bottom
print without support). Modelled flat: parts lie in ``Z[0, T]`` with hinge axes along ``X``;
the shelf extends ``+Y`` and hinges at ``Y = HBY`` (bottom) and ``Y = ALT_CROSS_Y``
(crossmember). The base lock line is computed so the deployed shelf sits at the deploy angle.

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
ROD_R = cfg.ALT_ROD_R  # rod in-plane radius (Ø9)
T = cfg.ALT_PART_T  # part thickness in Z (7 mm cross-section of the Ø9 rod)
ZC = T / 2.0  # part mid-plane Z
HBY = ROD_R  # bottom-rod (base hinge) axis Y, so the outer face sits at Y = 0
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
D_LEG = CROSS_Y - HBY  # leg-hinge height up the shelf from the bottom hinge

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
X_LOCK = math.sqrt(L_LEG**2 - (D_LEG * math.sin(_THETA)) ** 2) - D_LEG * math.cos(_THETA)
BASE_CROSS_Y = HBY + X_LOCK
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


def _flat(shape):
    """Trim a rod assembly to the printable ``Z[0, T]`` cross-section (flat top and bottom)."""
    return shape.common(_box(-1000.0, -1000.0, 0.0, 2000.0, 2000.0, T))


def _corner(cx, cy, start_deg):
    """Return a quarter-torus frame fillet (path radius ``CR``, tube ``ROD_R``) at a corner."""
    elbow = Part.makeTorus(
        CR, ROD_R, Vector(cx, cy, ZC), Vector(0.0, 0.0, 1.0), -180.0, 180.0, 90.0
    )
    elbow.rotate(Vector(cx, cy, ZC), Vector(0.0, 0.0, 1.0), start_deg)
    return elbow


def _necked_rod(y, x0, x1, necks):
    """Return an X rod (radius ``ROD_R``) along ``Y = y`` from ``x0`` to ``x1``, necked to pins.

    ``necks`` is an iterable of ``(centre, width)``; over each band the radius drops to
    ``PIN_R`` so a knuckle rides it as a hinge pin, with full collars between bands.
    """
    rod = _xcyl(ROD_R, x1 - x0, x0, y, ZC)
    for nc, nw in necks:
        nx = nc - nw / 2.0
        rod = rod.cut(_xcyl(ROD_R + 0.5, nw, nx, y, ZC))
        rod = rod.fuse(_xcyl(PIN_R, nw, nx, y, ZC))
    return rod


def _tray_lip():
    """Return the tray lip: deep at the shelf edges, filleted down to the finger-groove dips."""
    h_edge = cfg.ALT_LIP_EDGE_FRAC * d.WALL_TOP
    h_low = cfg.ALT_LIP_LOW_H
    lt = cfg.ALT_LIP_T
    ly = CROSS_Y - 1.0
    r_f = h_edge - h_low

    lip = _box(ROD_R, ly, T, W - 2 * ROD_R, lt, h_low)  # low lip across the whole width
    for edge_x, fg in ((0.0, FG_XS[0]), (W, FG_XS[1])):
        x_lo, x_hi = min(edge_x, fg), max(edge_x, fg)
        post = _box(x_lo, ly, T, x_hi - x_lo, lt, h_edge)
        post = post.cut(_ycyl(r_f, lt + 2.0, fg, ly - 1.0, T + h_edge))  # fillet down to fg
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
    run = (W - ROD_R - CR) - (ROD_R + CR)
    rise = (SHELF_H - ROD_R - CR) - (ROD_R + CR)
    shelf = _necked_rod(HBY, ROD_R + CR, W - ROD_R - CR, base_necks)  # bottom (hinge pins)
    shelf = shelf.fuse(_xcyl(ROD_R, run, ROD_R + CR, SHELF_H - ROD_R, ZC))  # top
    shelf = shelf.fuse(_ycyl(ROD_R, rise, ROD_R, ROD_R + CR, ZC))  # left
    shelf = shelf.fuse(_ycyl(ROD_R, rise, W - ROD_R, ROD_R + CR, ZC))  # right
    shelf = shelf.fuse(_corner(ROD_R + CR, ROD_R + CR, 180.0))  # bottom-left
    shelf = shelf.fuse(_corner(W - ROD_R - CR, ROD_R + CR, 270.0))  # bottom-right
    shelf = shelf.fuse(_corner(W - ROD_R - CR, SHELF_H - ROD_R - CR, 0.0))  # top-right
    shelf = shelf.fuse(_corner(ROD_R + CR, SHELF_H - ROD_R - CR, 90.0))  # top-left

    shelf = shelf.fuse(_necked_rod(CROSS_Y, ROD_R, W - ROD_R, [(LEG_CX, LEG_W + 2 * ACLR)]))

    # 47/47: base folds under the crossmember, so remove the crossmember lower half in the two
    # base-leg bands (the base keeps the lower there).
    for nc in NECK_XS:
        shelf = shelf.cut(
            _box(
                nc - BASE_LEG_W / 2.0 - 1.0,
                CROSS_Y - ROD_R - 1.0,
                -1.0,
                BASE_LEG_W + 2.0,
                2 * ROD_R + 2.0,
                SPLIT_HIGH + 1.0,
            )
        )

    shelf = _flat(shelf)  # flatten the rods to the 7 mm cross-section
    shelf = shelf.fuse(_tray_lip())  # the lip rises above the part plane (not flattened)
    return shelf


def _lock_cradle(nc):
    """Return a lock cradle on one base leg: a raised boss with a concave seat for the leg rod."""
    x0 = nc - BASE_LEG_W / 2.0
    boss = _box(x0, BASE_CROSS_Y - ROD_R - 1.0, T, BASE_LEG_W, 2 * ROD_R + 2.0, ROD_R)
    seat = _xcyl(ROD_R + cfg.ALT_SNAP_CLEAR, BASE_LEG_W + 2.0, x0 - 1.0, BASE_CROSS_Y, T + ROD_R)
    return boss.cut(seat)


def _base_leg(nc):
    """Return one H leg (raw, unflattened): a bar continued onto its bored hinge cylinder."""
    x0 = nc - BASE_LEG_W / 2.0
    bar = _box(x0, HBY, 0.0, BASE_LEG_W, BASE_LEN, T)  # from the hinge axis up
    leg = bar.fuse(_xcyl(ROD_R, BASE_LEG_W, x0, HBY, ZC))  # rounded hinge end
    leg = leg.cut(_xcyl(BORE, BASE_LEG_W + 2.0, x0 - 1.0, HBY, ZC))  # pin hole through both
    # 47/47: keep only the lower part where the leg passes under the shelf crossmember.
    leg = leg.cut(
        _box(x0 - 1.0, CROSS_Y - ROD_R - 1.0, SPLIT_LOW, BASE_LEG_W + 2.0, 2 * ROD_R + 2.0, T)
    )
    return leg


def build_base():
    """Build the base: an H (two hinged legs + crossmember), with a lock cradle on each leg.

    Returns
    -------
    Part.Shape
        The base solid (flat orientation).
    """
    base = _base_leg(NECK_XS[0]).fuse(_base_leg(NECK_XS[1]))

    cross = _box(NECK_XS[0], BASE_CROSS_Y - CROSS_W / 2.0, 0.0, NECK_XS[1] - NECK_XS[0], CROSS_W, T)
    base = base.fuse(cross)

    # 47/47: the leg rests over the base crossmember (base keeps the lower in the prop-leg band).
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

    base = _flat(base)
    base = base.fuse(_lock_cradle(NECK_XS[0])).fuse(_lock_cradle(NECK_XS[1]))
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
    bar = _box(x0, CROSS_Y, 0.0, LEG_W, L_LEG, T)
    leg = bar.fuse(_xcyl(ROD_R, LEG_W, x0, CROSS_Y, ZC))  # rounded hinge end
    leg = leg.cut(_xcyl(BORE, LEG_W + 2.0, x0 - 1.0, CROSS_Y, ZC))  # pin hole through both
    leg = leg.fuse(_xcyl(ROD_R, BASE_X1 - BASE_X0, BASE_X0, tip_y, ZC))  # base-width end cylinder

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
    return _flat(leg)


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
    assert L_LEG > D_LEG * math.sin(_THETA), "leg too short to reach the table at the lock angle"
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
