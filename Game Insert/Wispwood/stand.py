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
BORE = PIN_R + cfg.ALT_HINGE_PIN_CLEAR
ACLR = cfg.ALT_HINGE_AXIAL_CLEAR
BASE_LEG_W = cfg.ALT_BASE_LEG_WIDTH
LEG_W = cfg.ALT_LEG_WIDTH
L_LEG = cfg.ALT_LEG_LENGTH
CROSS_W = cfg.ALT_BASE_CROSS_W
LEG_CX = W / 2.0

# Base-leg hinge centres: placed a clear ALT_LEG_BASE_GAP outboard of the prop leg, so the
# leg-hinge neck on the crossmember does not start inside the base's pass-under cutout.
_BL_OFFSET = LEG_W / 2.0 + cfg.ALT_LEG_BASE_GAP + BASE_LEG_W / 2.0
NECK_XS = (LEG_CX - _BL_OFFSET, LEG_CX + _BL_OFFSET)

# Base outer span (the leg end-cylinder matches this so it reaches both leg cradles).
BASE_X0 = NECK_XS[0] - BASE_LEG_W / 2.0
BASE_X1 = NECK_XS[1] + BASE_LEG_W / 2.0
D_LEG = CROSS_Y - HBY  # leg-hinge height up the shelf from the bottom hinge

# Finger-groove centres of the tray, mapped onto the (wider) shelf — the lip dips here.
_OFFSET = (W - d.OUTER_WIDTH) / 2.0
_PC_L = cfg.WALL_LONG + cfg.POCKET_WIDTH / 2.0
_PC_R = cfg.WALL_LONG + cfg.POCKET_WIDTH + cfg.DIVIDER_THICKNESS + cfg.POCKET_WIDTH / 2.0
FG_XS = (_OFFSET + _PC_L, _OFFSET + _PC_R)

# Shared-thickness (47/47) split planes for overlapping folded parts (base/shelf crossing and
# leg/base crossing both use these, so the two splits are identical: lower keeps Z[0,
# SPLIT_LOW], upper keeps Z[SPLIT_HIGH, T], with ALT_SPLIT_GAP between).
SPLIT_LOW = (T - cfg.ALT_SPLIT_GAP) / 2.0
SPLIT_HIGH = SPLIT_LOW + cfg.ALT_SPLIT_GAP

# Deployed triangle (centrelines): bottom hinge A, leg hinge H at distance S = D_LEG up the
# shelf, cradle C at distance B along the base; angle at A is the deploy angle. By the law of
# cosines (L the opposite side), with the cradle seat a height ALT_CRADLE_OFFSET above the base:
#   B = S·cosθ + √(L² − (S·sinθ − h_c)²)
# (the +cosθ root puts the foot forward under the leaning shelf). B < S + L by construction.
_THETA = math.radians(cfg.STAND_DEPLOY_ANGLE)
S_HINGES = D_LEG  # distance between the two hinges, along the shelf
_HC = cfg.ALT_CRADLE_OFFSET
B_BASE = S_HINGES * math.cos(_THETA) + math.sqrt(
    L_LEG**2 - (S_HINGES * math.sin(_THETA) - _HC) ** 2
)  # base hinge-to-cradle distance
X_LOCK = B_BASE  # kept name for downstream offsets
BASE_CROSS_Y = HBY + B_BASE  # cradle line (from the bottom hinge)
LIP_EDGE_H = cfg.ALT_LIP_EDGE_FRAC * d.WALL_TOP  # deep-lip height at the edges (~55% tray height)
BASE_LEN = B_BASE + cfg.ALT_BASE_FOOT  # +Y extent (hinge to cradle + a little)
FOOT_EXT = LIP_EDGE_H  # base legs extend this far forward (-Y) out the front of the shelf, as feet
NATIVE_Y_MIN = -FOOT_EXT  # the forward feet are the most-forward point
DISPLAY_X_OFFSET = W + 30.0

# Locating-peg X positions: near the outer (min/max X) edges of the shelf, shared with the tray
# divots so they register.
_TRAY_OFFSET = (W - d.OUTER_WIDTH) / 2.0
PEG_XS = (cfg.ALT_PEG_INSET, W - cfg.ALT_PEG_INSET)


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


def _yz_prism(pts_yz, x0, dx):
    """Extrude a closed Y-Z polygon (list of ``(y, z)``) ``dx`` along ``+X`` from ``x0``."""
    verts = [Vector(x0, y, z) for y, z in pts_yz]
    verts.append(verts[0])
    return Part.Face(Part.makePolygon(verts)).extrude(Vector(dx, 0.0, 0.0))


def _xz_prism(pts_xz, y0, dy):
    """Extrude a closed X-Z polygon (list of ``(x, z)``) ``dy`` along ``+Y`` from ``y0``."""
    verts = [Vector(x, y0, z) for x, z in pts_xz]
    verts.append(verts[0])
    return Part.Face(Part.makePolygon(verts)).extrude(Vector(0.0, dy, 0.0))


def _peg(px, pz, py):
    """Return a locating peg protruding ``+Y`` from a lip face at ``(px, py, pz)``.

    A ridge: narrow in X with vertical (perpendicular) X sides, tapering only in Z from base to
    tip, so the downward Z face is angled and self-supports when printed flat.
    """
    xw = cfg.ALT_LIP_PEG_W / 2.0  # narrow half-width in X (vertical, perpendicular sides)
    zb = cfg.ALT_LIP_PEG_R  # base half-height in Z
    zt = cfg.ALT_LIP_PEG_TOP_R  # tip half-height in Z
    dep = cfg.ALT_LIP_PEG_H  # +Y protrusion

    def _rect(y, zh):
        pts = [
            Vector(px - xw, y, pz - zh),
            Vector(px + xw, y, pz - zh),
            Vector(px + xw, y, pz + zh),
            Vector(px - xw, y, pz + zh),
        ]
        pts.append(pts[0])
        return Part.makePolygon(pts)

    return Part.makeLoft([_rect(py, zb), _rect(py + dep, zt)], True)


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
    """Return the tray lip: deep at the shelf edges, filleted to the finger-groove dips.

    The edge posts extend ``ALT_LIP_DOWN`` below the shelf face to merge into the frame for a
    smoother transition, and each carries a cone locating peg (angled sides so it prints) on its
    top that seats in a matching tray divot.
    """
    h_edge = LIP_EDGE_H
    h_low = cfg.ALT_LIP_LOW_H
    lt = cfg.ALT_LIP_T
    ly = CROSS_Y - 1.0
    r_f = h_edge - h_low
    down = cfg.ALT_LIP_DOWN

    lip = _box(ROD_R, ly, T, W - 2 * ROD_R, lt, h_low)  # low lip across the whole width
    for edge_x, fg in ((0.0, FG_XS[0]), (W, FG_XS[1])):
        x_lo, x_hi = min(edge_x, fg), max(edge_x, fg)
        post = _box(x_lo, ly, T - down, x_hi - x_lo, lt, h_edge + down)  # extends down to the frame
        post = post.cut(_ycyl(r_f, lt + 2.0, fg, ly - 1.0, T + h_edge))  # fillet down to fg
        lip = lip.fuse(post)

    # Clearance so the lip does not fuse to the leg hinge passing under it: a narrow flat span
    # raised by ALT_LIP_LEG_GAP in the middle, with angled lead-ins running out to the leg edges
    # (so the lead-ins clear the leg at an angle and only ALT_LIP_LEG_FLAT needs bridging).
    g = cfg.ALT_LIP_LEG_GAP
    fh = cfg.ALT_LIP_LEG_FLAT / 2.0
    re_l, re_r = FG_XS  # lead-ins reach the lip bottom at the finger-groove dips (~0.2 over leg)
    cutter = _xz_prism(
        [
            (re_l, T - 1.0),
            (re_r, T - 1.0),
            (re_r, T),
            (LEG_CX + fh, T + g),
            (LEG_CX - fh, T + g),
            (re_l, T),
        ],
        ly - 1.0,
        lt + 2.0,
    )
    lip = lip.cut(cutter)

    # Locating pegs on the +Y face of each edge post (toward the tray), near the top (max Z).
    peg_pz = T + h_edge - cfg.ALT_LIP_PEG_R - 1.0
    for px in PEG_XS:
        lip = lip.fuse(_peg(px, peg_pz, ly + lt))
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
    """Return a lock cradle on one base leg: raised seat + a ramp gusset to the base end.

    A boss with a concave seat (open toward the hinge) that the leg end-cylinder clicks into,
    reinforced on the foot side by a solid wedge that ramps from the cradle top smoothly down
    to the base surface before the base end — strong, with a clean transition.
    """
    x0 = nc - BASE_LEG_W / 2.0
    ramp_end = BASE_CROSS_Y + cfg.ALT_BASE_FOOT  # reinforce a foot-length past the cradle
    boss = _box(x0, BASE_CROSS_Y - ROD_R - 1.0, T, BASE_LEG_W, 2 * ROD_R + 2.0, ROD_R)
    seat = _xcyl(ROD_R + cfg.ALT_SNAP_CLEAR, BASE_LEG_W + 2.0, x0 - 1.0, BASE_CROSS_Y, T + ROD_R)
    cradle = boss.cut(seat)
    ramp_y0 = BASE_CROSS_Y + ROD_R + 1.0  # foot edge of the boss
    ramp = _yz_prism([(ramp_y0, T), (ramp_end, T), (ramp_y0, T + ROD_R)], x0, BASE_LEG_W)
    return cradle.fuse(ramp)


def _base_leg(nc):
    """Return one H leg (raw, unflattened): a bar continued onto its bored hinge cylinder.

    The leg runs from the cradle end back through the hinge and **forward (-Y) out past the
    front of the shelf** by ``FOOT_EXT`` as a foot; the forward tip is rounded about X, like the
    rod ends.
    """
    x0 = nc - BASE_LEG_W / 2.0
    foot_y = HBY - FOOT_EXT  # forward (-Y) foot tip, out past the front of the shelf
    top_y = HBY + BASE_LEN  # +Y end (past the cradle)
    bar = _box(x0, foot_y, 0.0, BASE_LEG_W, top_y - foot_y, T)
    bar = bar.fuse(_xcyl(T / 2.0, BASE_LEG_W, x0, foot_y, ZC))  # foot rounded about X, like rods
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

    # 47/47: the leg rests over the base crossmember, so the base keeps only the lower band
    # (Z[0, SPLIT_LOW]) in the prop-leg band, leaving the split gap below the leg.
    base = base.cut(
        _box(
            LEG_CX - LEG_W / 2.0 - 1.0,
            BASE_CROSS_Y - CROSS_W / 2.0 - 1.0,
            SPLIT_LOW,
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

    # 47/47: keep only the upper band (Z[SPLIT_HIGH, T]) where the leg rests over the base
    # crossmember, so the leg underside leaves the split gap above the base and does not fuse.
    leg = leg.cut(
        _box(
            x0 - 1.0,
            BASE_CROSS_Y - CROSS_W / 2.0 - 1.0,
            -1.0,
            LEG_W + 2.0,
            CROSS_W + 2.0,
            SPLIT_HIGH + 1.0,
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
    assert B_BASE < S_HINGES + L_LEG, "base reach B must be < S + L (degenerate triangle)"
    # (the base foot intentionally extends past the shelf top now, so it is not bounded by SHELF_H)
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
