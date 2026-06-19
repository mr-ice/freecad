"""The Wispwood display stand (redesigned barrel-hinge stand).

A three-part, print-in-place triangular stand that holds the tray tilted for play:

- **Shelf** — a flat plate that the tray rests against (cross-lip + side lips grab it). Its
  bottom edge is a full-width **barrel** (Ø = plate thickness) with two narrowed **neck**
  bands that form the base hinge.
- **Base** — the foot. Two legs hinge on the barrel necks via knuckles; their shelf-facing
  edge is a **concave cylinder** matching the barrel so contact stays continuous as it
  rotates. An **unbroken crossbar** joins the legs and carries the lock socket.
- **Leg** — a prop hinged up the shelf; its tip **snaps** into the base crossbar socket. The
  socket position is **computed** so the shelf locks at ``STAND_DEPLOY_ANGLE`` above the table.

Modelled flat (the print orientation): the barrel axis is along ``X`` at ``Y = 0``; the shelf
extends ``+Y`` and the base extends ``-Y``; ``Z`` is the print height (sheets in ``Z[0, T]``,
lips above). Deployment folds the shelf up about the barrel.

All offsets derive from named constants (repo ``CLAUDE.md``); the lock is derived from the
hinge positions and leg length, never measured.

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
W = d.ALT_SHELF_W  # stand width (hinge axis), matches the tray + side lips
T = cfg.ALT_SHELF_THICKNESS  # plate / sheet thickness
R = T / 2.0  # barrel radius (full diameter = plate thickness)
SHELF_H = cfg.ALT_SHELF_HEIGHT  # shelf length above the barrel
NECK_R = cfg.ALT_BARREL_NECK_R
NECK_W = cfg.ALT_BARREL_NECK_W
NECK_XS = tuple(f * W for f in cfg.ALT_BARREL_NECK_FRACS)  # two base-knuckle band centres
D_LEG = cfg.ALT_LEG_HINGE_Y  # prop-leg hinge distance up the shelf
L_LEG = cfg.ALT_LEG_LENGTH
LEG_W = cfg.ALT_LEG_WIDTH
PIN_R = cfg.ALT_HINGE_PIN_R
CLR = cfg.ALT_HINGE_PIN_CLEAR
ACLR = cfg.ALT_HINGE_AXIAL_CLEAR

_THETA = math.radians(cfg.STAND_DEPLOY_ANGLE)
# Lock distance along the base from the barrel: where the prop-leg tip meets the table (Z=0)
# when the shelf is folded up to STAND_DEPLOY_ANGLE. Derived from the two hinge positions and
# the leg length (the leg hinge sits D_LEG up the shelf; its tip swings down to the base).
X_LOCK = math.sqrt(L_LEG**2 - (D_LEG * math.sin(_THETA)) ** 2) - D_LEG * math.cos(_THETA)
BASE_LEN = X_LOCK + 15.0  # base reaches a little past the lock line for a stable foot
NATIVE_Y_MIN = -BASE_LEN  # min Y of the flat model (used to place it in the box)
DISPLAY_X_OFFSET = W + 30.0  # offset for standalone review in the macro

# Prop leg centred between the two base legs.
LEG_X0 = W / 2.0 - LEG_W / 2.0
LEG_X1 = W / 2.0 + LEG_W / 2.0


def _box(x, y, z, dx, dy, dz):
    """Return an axis-aligned box solid with minimum corner ``(x, y, z)``."""
    return Part.makeBox(dx, dy, dz, Vector(x, y, z))


def _xcyl(r, length, x, y, z):
    """Return a cylinder of radius ``r`` along ``+X`` from ``(x, y, z)``."""
    return Part.makeCylinder(r, length, Vector(x, y, z), Vector(1.0, 0.0, 0.0))


def _leg_segments():
    """Return ``(x0, x1, is_plate)`` for the prop-leg hinge (plate / leg / plate)."""
    seg = LEG_W / 3.0
    return [(LEG_X0 + i * seg, LEG_X0 + (i + 1) * seg, i % 2 == 0) for i in range(3)]


def build_shelf():
    """Build the shelf: plate + barrel (with two necks) + tray lips + prop-leg hinge.

    Returns
    -------
    Part.Shape
        The shelf solid (flat print orientation).
    """
    plate = _box(0.0, 0.0, 0.0, W, SHELF_H, T)

    # Barrel along the bottom edge, full radius except the two neck bands.
    barrel = _xcyl(R, W, 0.0, 0.0, R)
    for nc in NECK_XS:
        x0 = nc - NECK_W / 2.0
        barrel = barrel.cut(_xcyl(R + 0.5, NECK_W, x0, 0.0, R))  # clear the band to the neck
        barrel = barrel.fuse(_xcyl(NECK_R, NECK_W, x0, 0.0, R))  # leave the thin neck rod
    shelf = plate.fuse(barrel)

    # Tray lips on the shelf top: a simple uniform cross-lip near the barrel, two side lips.
    cl_y0 = R + 1.0
    clt, clh = cfg.ALT_SHELF_CROSS_LIP_T, cfg.ALT_SHELF_CROSS_LIP_H
    slw, slh = cfg.ALT_SHELF_SIDE_LIP_W, cfg.ALT_SHELF_SIDE_LIP_H
    shelf = shelf.fuse(_box(0.0, cl_y0, T, W, clt, clh))  # cross-lip
    shelf = shelf.fuse(_box(0.0, cl_y0, T, slw, SHELF_H - cl_y0, slh))  # left side lip
    shelf = shelf.fuse(_box(W - slw, cl_y0, T, slw, SHELF_H - cl_y0, slh))  # right side lip

    # Prop-leg hinge: pin across the leg width + plate knuckles (outer segments).
    shelf = shelf.fuse(_xcyl(PIN_R, LEG_W, LEG_X0, D_LEG, R))
    for x0, x1, is_plate in _leg_segments():
        if is_plate:
            shelf = shelf.fuse(_xcyl(R, x1 - x0, x0, D_LEG, R))
            shelf = shelf.fuse(_box(x0, D_LEG, 0.0, x1 - x0, R + 1.0, T))  # neck back to plate
    return shelf


def _base_leg(nc):
    """Return one base leg (knuckle on the barrel neck + bar running ``-Y``)."""
    half = (NECK_W + 4.0) / 2.0
    x0, x1 = nc - half, nc + half
    # Knuckle ring around the neck (bored with clearance), axially inset from the collars.
    knuckle = _xcyl(R, NECK_W - 2.0 * ACLR, nc - NECK_W / 2.0 + ACLR, 0.0, R)
    knuckle = knuckle.cut(_xcyl(NECK_R + CLR, NECK_W, nc - NECK_W / 2.0 - 0.5, 0.0, R))
    # Bar from the hinge running -Y to the base end.
    bar = _box(x0, -BASE_LEN, 0.0, x1 - x0, BASE_LEN, T)
    return bar.fuse(knuckle)


def build_base():
    """Build the base: two legs on the barrel necks + concave mating edge + crossbar + socket.

    The crossbar is unbroken and sits on the computed lock line (``Y = -X_LOCK``); its centre
    carries the snap socket that the prop-leg tip clicks into.

    Returns
    -------
    Part.Shape
        The base solid (flat print orientation).
    """
    base = None
    for nc in NECK_XS:
        leg = _base_leg(nc)
        base = leg if base is None else base.fuse(leg)

    # Concave mating edge: clear the full-radius barrel so the base rides it as it rotates.
    base = base.cut(_xcyl(R + CLR, W, 0.0, 0.0, R))

    # Unbroken crossbar on the lock line, joining the two legs.
    cross_w = 10.0
    cy = -X_LOCK
    base = base.fuse(_box(NECK_XS[0], cy - cross_w / 2.0, 0.0, NECK_XS[1] - NECK_XS[0], cross_w, T))

    # Snap socket in the crossbar centre (the prop-leg tip seats here when deployed).
    sr = cfg.ALT_SNAP_R - cfg.ALT_SNAP_CLEAR
    base = base.cut(Part.makeSphere(sr, Vector(W / 2.0, cy, T)))
    return base


def build_leg():
    """Build the prop leg: bar + hinge knuckle + tip snap bump.

    The bar runs from the shelf hinge (``Y = D_LEG``) up the shelf and stops short of the top
    (no fuse). Its tip carries a snap bump that engages the base crossbar socket when deployed.

    Returns
    -------
    Part.Shape
        The leg solid (flat print orientation).
    """
    tip_y = D_LEG + L_LEG
    leg = _box(LEG_X0, D_LEG, 0.0, LEG_W, L_LEG, T)

    # Hinge: leg knuckle (middle segment) bored for the pin; notch clear of the plate knuckles.
    for x0, x1, is_plate in _leg_segments():
        if is_plate:
            leg = leg.cut(
                _box(x0 - ACLR, D_LEG - 1.0, -1.0, (x1 - x0) + 2 * ACLR, R + 1.0, T + 2.0)
            )
        else:
            leg = leg.fuse(_xcyl(R, (x1 - x0) - 2 * ACLR, x0 + ACLR, D_LEG, R))
    leg = leg.cut(_xcyl(PIN_R + CLR, LEG_W + 2.0, LEG_X0 - 1.0, D_LEG, R))

    # Tip snap bump (engages the base socket when deployed).
    sr = cfg.ALT_SNAP_R
    leg = leg.fuse(Part.makeSphere(sr, Vector(W / 2.0, tip_y, T)))
    return leg


def build_all():
    """Build the stand parts, offset beside the tray for standalone review.

    Returns
    -------
    list of tuple
        ``[(name, shape, (r, g, b), visible, transparency)]`` matching the macro's part
        tuple, or an empty list when ``SHOW_ALT_STAND`` is false. ``place_stand`` in
        :mod:`box_insert` repositions these into the box.
    """
    if not cfg.SHOW_ALT_STAND:
        return []
    assert L_LEG > D_LEG * math.sin(_THETA), "leg too short to reach the table at the lock angle"
    assert D_LEG + L_LEG < SHELF_H, "prop leg fuses into the shelf top; shorten ALT_LEG_LENGTH"
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
