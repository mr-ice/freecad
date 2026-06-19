"""The Wispwood display stand — rod-frame design (see ``stand.md``).

Three print-in-place parts that hold the tray upright at ``STAND_DEPLOY_ANGLE``:

- **Shelf** — an empty rounded rectangle of Ø(2·rod) rod, filleted corners. A crossmember
  rod carries a lip the tray sits against; the bottom rod necks down to **pins** for the base
  hinge, and the crossmember rod necks down for the leg hinge.
- **Base** — an **H** (two legs + a crossmember) hinged on the shelf bottom-rod pins (each
  leg is a bored knuckle on a necked pin). It folds inside the shelf rectangle, **under** the
  shelf crossmember (shared 47/47 thickness: base lower, crossmember upper).
- **Leg** — hinged on the shelf crossmember; its far end is a rod-profile cross-cylinder that
  clicks into the base when deployed. Where it crosses the base crossmember they share 47/47
  (base lower, leg upper).

Modelled flat (print/folded orientation): parts lie in ``Z[0, 2·rod]`` with hinge axes along
``X``; the shelf extends ``+Y`` and hinges at ``Y = rod`` (bottom) and ``Y = ALT_CROSS_Y``
(crossmember). The base lock line is **computed** from the hinge positions and leg length so
the deployed shelf sits at ``STAND_DEPLOY_ANGLE``.

In-progress rebuild toward ``stand.md`` (base-focused); clearances and the snap lock still
need print tuning.

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
W = d.ALT_SHELF_W  # stand width (hinge-axis direction)
RR = cfg.ALT_ROD_R  # frame rod radius
T = 2.0 * RR  # part thickness (= rod diameter)
ZC = RR  # rod/centre Z (parts span Z[0, T])
SHELF_H = cfg.ALT_SHELF_HEIGHT
CROSS_Y = cfg.ALT_CROSS_Y  # shelf crossmember (tray rest + leg hinge)
PIN_R = cfg.ALT_BARREL_NECK_R  # necked-pin radius
NECK_XS = tuple(f * W for f in cfg.ALT_BARREL_NECK_FRACS)  # two base-hinge band centres
BORE = PIN_R + cfg.ALT_HINGE_PIN_CLEAR  # knuckle bore around a pin
ACLR = cfg.ALT_HINGE_AXIAL_CLEAR
BASE_LEG_W = cfg.ALT_BASE_LEG_WIDTH
LEG_W = cfg.ALT_LEG_WIDTH
L_LEG = cfg.ALT_LEG_LENGTH
CROSS_W = cfg.ALT_BASE_CROSS_W
LEG_CX = W / 2.0  # leg centred on the width

# Shared-thickness (47/47) split planes for overlapping folded parts.
SPLIT_LOW = (T - cfg.ALT_SPLIT_GAP) / 2.0  # a "lower" part keeps Z[0, SPLIT_LOW]
SPLIT_HIGH = SPLIT_LOW + cfg.ALT_SPLIT_GAP  # an "upper" part keeps Z[SPLIT_HIGH, T]

# Lock line: distance up the base (from the bottom hinge) where the leg end meets the base
# when the shelf is folded up to the deploy angle, derived from the leg-hinge height and length.
_THETA = math.radians(cfg.STAND_DEPLOY_ANGLE)
X_LOCK = math.sqrt(L_LEG**2 - (CROSS_Y * math.sin(_THETA)) ** 2) - CROSS_Y * math.cos(_THETA)
BASE_CROSS_Y = ZC + X_LOCK  # base crossmember on the lock line (from the bottom hinge)
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


def _necked_rod(y, x0, x1, necks):
    """Return an X rod (Ø = 2·RR) along ``Y = y`` from ``x0`` to ``x1``, necked to pins.

    ``necks`` is an iterable of ``(centre, width)``; over each band the rod radius drops to
    ``PIN_R`` so a moving knuckle can ride it as a hinge pin, with full-radius collars between
    bands to locate the knuckles axially.
    """
    rod = _xcyl(RR, x1 - x0, x0, y, ZC)
    for nc, nw in necks:
        nx = nc - nw / 2.0
        rod = rod.cut(_xcyl(RR + 0.5, nw, nx, y, ZC))
        rod = rod.fuse(_xcyl(PIN_R, nw, nx, y, ZC))
    return rod


def build_shelf():
    """Build the shelf: rounded-rectangle rod frame + necked hinge rods + tray crossmember.

    Returns
    -------
    Part.Shape
        The shelf solid (flat orientation).
    """
    base_necks = [(nc, BASE_LEG_W + 2 * ACLR) for nc in NECK_XS]
    bottom = _necked_rod(ZC, 0.0, W, base_necks)
    top = _xcyl(RR, W, 0.0, SHELF_H - RR, ZC)
    left = _ycyl(RR, SHELF_H, RR, 0.0, ZC)
    right = _ycyl(RR, SHELF_H, W - RR, 0.0, ZC)
    shelf = bottom.fuse(top).fuse(left).fuse(right)
    for cx, cy in ((RR, RR), (W - RR, RR), (RR, SHELF_H - RR), (W - RR, SHELF_H - RR)):
        shelf = shelf.fuse(Part.makeSphere(RR, Vector(cx, cy, ZC)))  # filleted corners

    # Crossmember rod, necked at the centre for the leg hinge.
    shelf = shelf.fuse(_necked_rod(CROSS_Y, RR, W - RR, [(LEG_CX, LEG_W + 2 * ACLR)]))

    # 47/47: the base folds under the crossmember, so remove the crossmember's lower half in
    # the two base-leg bands (the base keeps the lower there).
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

    # Tray lip: a narrow wall above the shelf face, in front of the crossmember (clears the
    # tray finger scoops), that the tray bottom edge rests against.
    shelf = shelf.fuse(_box(RR, CROSS_Y - 1.0, T, W - 2 * RR, 2.0, cfg.ALT_TRAY_LIP_H))
    return shelf


def _base_leg(nc):
    """Return one H leg: a knuckle on the bottom-rod pin + a bar up to the foot."""
    x0 = nc - BASE_LEG_W / 2.0
    # Bar starts clear of the bottom rod (above Y = rod top) so only the knuckle touches it.
    bar = _box(x0, ZC + RR, 0.0, BASE_LEG_W, BASE_LEN - RR, T)
    knuckle = _xcyl(RR, BASE_LEG_W, x0, ZC, ZC)
    leg = bar.fuse(knuckle)
    leg = leg.cut(_xcyl(BORE, BASE_LEG_W + 2.0, x0 - 1.0, ZC, ZC))  # bore for the pin
    # 47/47: keep only the lower part where the leg passes under the shelf crossmember.
    leg = leg.cut(_box(x0 - 1.0, CROSS_Y - RR - 1.0, SPLIT_LOW, BASE_LEG_W + 2.0, 2 * RR + 2.0, T))
    return leg


def build_base():
    """Build the base: an H (two hinged legs + crossmember) with a lock catch.

    Returns
    -------
    Part.Shape
        The base solid (flat orientation).
    """
    base = _base_leg(NECK_XS[0]).fuse(_base_leg(NECK_XS[1]))

    # Crossmember joining the two legs on the lock line.
    cross = _box(NECK_XS[0], BASE_CROSS_Y - CROSS_W / 2.0, 0.0, NECK_XS[1] - NECK_XS[0], CROSS_W, T)
    base = base.fuse(cross)

    # 47/47: the leg rests over the base crossmember, so remove the crossmember's upper half in
    # the leg band (the base keeps the lower there).
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

    # Lock catch: a raised boss with a concave cradle (radius RR + clearance) on the lower
    # band that the leg end-cylinder clicks into when deployed.
    boss = _box(
        LEG_CX - RR - 2.0, BASE_CROSS_Y - RR - 1.0, SPLIT_LOW, 2 * RR + 4.0, 2 * RR + 2.0, RR
    )
    boss = boss.cut(
        _xcyl(
            RR + cfg.ALT_SNAP_CLEAR, 2 * RR + 6.0, LEG_CX - RR - 3.0, BASE_CROSS_Y, SPLIT_LOW + RR
        )
    )
    base = base.fuse(boss)
    return base


def build_leg():
    """Build the prop leg: a bar hinged on the shelf crossmember, with an end-cylinder.

    Returns
    -------
    Part.Shape
        The leg solid (flat orientation).
    """
    x0 = LEG_CX - LEG_W / 2.0
    tip_y = CROSS_Y + L_LEG
    # Bar starts clear of the crossmember rod; the knuckle bridges down to the pin.
    bar = _box(x0, CROSS_Y + RR, 0.0, LEG_W, L_LEG - RR, T)
    knuckle = _xcyl(RR, LEG_W, x0, CROSS_Y, ZC)
    leg = bar.fuse(knuckle)
    leg = leg.cut(_xcyl(BORE, LEG_W + 2.0, x0 - 1.0, CROSS_Y, ZC))

    # End cross-cylinder (rod profile) that clicks into the base catch.
    leg = leg.fuse(_xcyl(RR, LEG_W, x0, tip_y, ZC))

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
