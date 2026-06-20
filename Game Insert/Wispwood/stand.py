"""The Wispwood display stand — rod-frame design (see ``stand.md``).

Three print-in-place parts that hold the tray upright at ``STAND_DEPLOY_ANGLE``:

- **Shelf** — an empty rounded rectangle drawn as a **continuous rod path** (straight runs
  joined by quarter-torus corner fillets, no crossing cylinders). A crossmember rod carries a
  **tray lip** (deep at the edges, filleted down to clear the tray finger grooves). The bottom
  rod necks to **pins** for the base hinge; the crossmember rod necks for the leg hinge.
- **Base** — a flat **open rod rectangle** lying on the table (the sole contact, so it cannot
  rock), hinged on the shelf bottom-rod pins via two bored knuckles. It reaches a **forward
  foot** ``ALT_BASE_FWD`` ahead of the hinge (catching the loaded CG) and back to a **snap
  cradle**. The shelf folds flat on top of it.
- **Leg** — hinged on the shelf crossmember (bar continued onto the cylinder, bored through).
  Its end cross-cylinder spans the base width and snaps into the base cradle to lock the angle.

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

# --- Frame / derived geometry (kinematics live in derived.py) ----------------
W = d.ALT_SHELF_W
ROD_R = cfg.ALT_ROD_R  # rod in-plane radius (Ø9)
T = cfg.ALT_PART_T  # part thickness in Z (7 mm cross-section of the Ø9 rod)
ZC = d.ALT_ZC  # part mid-plane Z (hinge axis height; base rests on the table)
HBY = d.ALT_HBY  # bottom-rod (base hinge) axis Y, so the outer face sits at Y = 0
SHELF_H = cfg.ALT_SHELF_HEIGHT
CR = cfg.ALT_FRAME_CORNER_R  # frame corner fillet radius
CROSS_Y = d.ALT_CROSS_Y  # shelf crossmember (tray rest + leg hinge), derived from TRAY_LIFT
PIN_R = cfg.ALT_BARREL_NECK_R
BORE = PIN_R + cfg.ALT_HINGE_PIN_CLEAR
ACLR = cfg.ALT_HINGE_AXIAL_CLEAR
LEG_W = cfg.ALT_LEG_WIDTH
L_LEG = cfg.ALT_LEG_LENGTH
LEG_CX = W / 2.0
ALT_S_HINGES = d.ALT_S_HINGES  # hinge-to-hinge distance up the shelf

# Base hinge knuckles: two bands flanking the prop leg (inboard of the shelf side rails) so the
# base interleaves with the shelf bottom rod's pins without the two frames' rails colliding on
# the shared hinge axis. The base side rails sit at these knuckle centres.
BASE_KNUCKLE_W = cfg.ALT_BASE_LEG_WIDTH  # base hinge-knuckle axial width
_BL_OFFSET = LEG_W / 2.0 + cfg.ALT_LEG_BASE_GAP + BASE_KNUCKLE_W / 2.0
NECK_XS = (LEG_CX - _BL_OFFSET, LEG_CX + _BL_OFFSET)  # knuckle / base-rail centres
BASE_X0 = NECK_XS[0] - ROD_R  # base outer X extent
BASE_X1 = NECK_XS[1] + ROD_R

# Deployed lock geometry (computed in derived.py): cradle line behind the bottom hinge.
B_BASE = d.ALT_B_BASE
X_LOCK = B_BASE  # kept name for downstream offsets
BASE_CROSS_Y = HBY + B_BASE  # cradle line (from the bottom hinge)
LIP_EDGE_H = d.ALT_LIP_EDGE_H  # deep-lip height at the edges (~55% tray height)

# Base extents: a flat rod rectangle from a forward foot (ahead of the hinge) back past the
# cradle. The wide flat rectangle is the sole table contact, so it cannot rock.
FWD = cfg.ALT_BASE_FWD  # forward-foot reach ahead of the hinge
BASE_FRONT_Y = HBY - FWD  # forward foot tip (-Y), out past the shelf bottom edge
BASE_BACK_Y = BASE_CROSS_Y + cfg.ALT_BASE_FOOT  # rear foot, past the cradle
BASE_LEN = BASE_BACK_Y - BASE_FRONT_Y
NATIVE_Y_MIN = BASE_FRONT_Y  # most-forward point of the folded stand
DISPLAY_X_OFFSET = W + 30.0

# Finger-groove centres of the tray, mapped onto the (wider) shelf — the lip dips here.
_OFFSET = (W - d.OUTER_WIDTH) / 2.0
_PC_L = cfg.WALL_LONG + cfg.POCKET_WIDTH / 2.0
_PC_R = cfg.WALL_LONG + cfg.POCKET_WIDTH + cfg.DIVIDER_THICKNESS + cfg.POCKET_WIDTH / 2.0
FG_XS = (_OFFSET + _PC_L, _OFFSET + _PC_R)

# Locating-peg X positions: near the outer (min/max X) edges of the shelf, shared with the tray
# divots so they register.
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
    base_necks = [(nc, BASE_KNUCKLE_W + 2 * ACLR) for nc in NECK_XS]
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

    shelf = _flat(shelf)  # flatten the rods to the 7 mm cross-section
    shelf = shelf.fuse(_tray_lip())  # the lip rises above the part plane (not flattened)
    return shelf


def _lock_cradle():
    """Return a snap cradle spanning the base inner width: raised concave seat + ramp gusset.

    A boss across the base (between the side rails) with a concave seat (open toward the hinge)
    that the prop leg's wide end cylinder clicks into, ramped on the foot side down to the base
    surface before the rear rod.
    """
    x0 = NECK_XS[0]
    span = NECK_XS[1] - NECK_XS[0]
    boss = _box(x0, BASE_CROSS_Y - ROD_R - 1.0, T, span, 2 * ROD_R + 2.0, ROD_R)
    seat = _xcyl(ROD_R + cfg.ALT_SNAP_CLEAR, span + 2.0, x0 - 1.0, BASE_CROSS_Y, T + ROD_R)
    cradle = boss.cut(seat)
    ramp_y0 = BASE_CROSS_Y + ROD_R + 1.0
    ramp = _yz_prism([(ramp_y0, T), (BASE_BACK_Y, T), (ramp_y0, T + ROD_R)], x0, span)
    return cradle.fuse(ramp)


def _base_knuckle(nc):
    """Return one base hinge knuckle: an X-cylinder at the hinge axis, bored for the shelf pin.

    Centred on a side rail at ``x = nc``, ``Y = HBY``; the rail merges into it. Bored to
    ``BORE`` so it rides the shelf bottom-rod pin (a print-in-place hinge along ``X``).
    """
    x0 = nc - BASE_KNUCKLE_W / 2.0
    knuckle = _xcyl(ROD_R, BASE_KNUCKLE_W, x0, HBY, ZC)
    return knuckle.cut(_xcyl(BORE, BASE_KNUCKLE_W + 2.0, x0 - 1.0, HBY, ZC))


def build_base():
    """Build the base: a flat open rod rectangle on the hinge knuckles + a snap cradle.

    A rounded rod rectangle (rails at ``NECK_XS``) lying flat on the table — the sole table
    contact, so it cannot rock. It reaches a forward foot ``ALT_BASE_FWD`` ahead of the hinge
    and back past the cradle. Two bored knuckles at the hinge axis interleave the shelf bottom
    rod's pins.

    Returns
    -------
    Part.Shape
        The base solid (flat orientation).
    """
    xl, xr = NECK_XS  # side-rail centrelines
    yf = BASE_FRONT_Y + ROD_R  # front-rod centreline
    yb = BASE_BACK_Y - ROD_R  # rear-rod centreline
    run = (xr - CR) - (xl + CR)
    rise = (yb - CR) - (yf + CR)
    base = _xcyl(ROD_R, run, xl + CR, yf, ZC)  # forward-foot rod
    base = base.fuse(_xcyl(ROD_R, run, xl + CR, yb, ZC))  # rear-foot rod
    base = base.fuse(_ycyl(ROD_R, rise, xl, yf + CR, ZC))  # left rail
    base = base.fuse(_ycyl(ROD_R, rise, xr, yf + CR, ZC))  # right rail
    base = base.fuse(_corner(xl + CR, yf + CR, 180.0))  # front-left
    base = base.fuse(_corner(xr - CR, yf + CR, 270.0))  # front-right
    base = base.fuse(_corner(xr - CR, yb - CR, 0.0))  # back-right
    base = base.fuse(_corner(xl + CR, yb - CR, 90.0))  # back-left

    # Print-in-place hinge knuckles at the axis (Y = HBY), between the foot and the frame.
    base = base.fuse(_base_knuckle(NECK_XS[0])).fuse(_base_knuckle(NECK_XS[1]))

    base = _flat(base)
    base = base.fuse(_lock_cradle())
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
    # The end cylinder snaps into the base cradle; no 47/47 split — the leg ends in the cradle
    # rather than crossing a base crossmember.
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
    assert L_LEG > ALT_S_HINGES * math.sin(d.ALT_THETA), "leg too short to reach the table"
    assert CROSS_Y + L_LEG < SHELF_H, "leg does not fit folded between the crossmember and top"
    assert B_BASE < ALT_S_HINGES + L_LEG, "base reach B must be < S + L (degenerate triangle)"
    assert d.stand_is_stable(), "loaded CG falls outside the base footprint (would tip)"
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
