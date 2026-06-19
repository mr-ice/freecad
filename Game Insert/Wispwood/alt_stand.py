"""Alternate stand for the Wispwood tray (separate, stored off the tray).

A triangular frame of three parts -- the **shelf** (holds the tray), the **base** (sits on
the table), and the **leg** (props them apart in a triangle). It is stored separately because
the integrated stand is too big to fit in the box on the tray. This module defines all three
parts; each leg/base joins the shelf by its own print-in-place hinge.

Base
----
The foot: two legs on print-in-place hinges **centred in the shelf's bottom border** (knuckles
subdivided to match the prop-leg hinge). The legs run up through the shelf flanking the prop
leg and stop short of its T; a **crossbar high up** (just below the leg tops) joins them. Where
a leg crosses the shelf's lip-band cross, and where the crossbar passes under the prop leg, the
7 mm is shared **~47/47** (one part keeps the back, the other the front, with ``ALT_SPLIT_GAP``
between) so the cross-lip support and both parts stay full-strength and print free.

Leg
---
A bar that nests **fully inside** the shelf plate's central opening (recessed within the 7 mm,
free of all other structure) and is joined to the plate by a **print-in-place hinge** just
above the cross-lip -- interleaved knuckles on a single pin, with the gaps as print
clearances. It swings out to prop the stand; its free end carries a flattened-cylinder **T**
(perpendicular to the bar) that will lock the stand upright.

Shelf
-----
A rounded-rectangle plate, ``ALT_SHELF_THICKNESS`` thick and ``ALT_SHELF_HEIGHT`` tall, wide
enough that the tray clears between the side lips (width = tray + 2 side lips + 2 side
clearances). On the top surface:

- a **cross-lip** across the bottom edge that the tray rests against, and
- two short **side lips** above it on the outer edges that steady the tray laterally (each
  ``ALT_SHELF_SIDE_LIP_W`` wide, clearing the tray by ``ALT_SHELF_SIDE_CLEAR`` per side), and
- the two bottom **corners raised** to ``ALT_SHELF_CORNER_H_FRAC`` of the tray height and
  **filleted** back down to the cross-lip and side-lips, forming a deeper corner cup.

The frame extends ``ALT_SHELF_BELOW_LIP`` below the lip toward the base; the centre of both
the tray region and that extension is cut away, leaving a border frame (plus the lip support
band) that holds the tray's perimeter and carries the load to the base.

All offsets are derived from named constants (never measured), per the repository rules.

Public API
----------
``build_shelf``, ``build_leg``, ``build_base``, ``build_all``.
"""

import config as cfg
import Part
from FreeCAD import Vector
from wispwood import OUTER_WIDTH, WALL_TOP

# --- Derived geometry --------------------------------------------------------
# Width = tray + a side lip each side + a running clearance each side, so the tray clears
# between the side lips regardless of the lip width.
SHELF_W = OUTER_WIDTH + 2 * cfg.ALT_SHELF_SIDE_LIP_W + 2 * cfg.ALT_SHELF_SIDE_CLEAR
CORNER_H = WALL_TOP * cfg.ALT_SHELF_CORNER_H_FRAC  # raised corner height (~1/2 tray height)
DISPLAY_X_OFFSET = OUTER_WIDTH + 30.0  # set the part beside the tray in the view

# --- Leg / print-in-place hinge (shared by shelf and leg) --------------------
LEG_LT = cfg.ALT_LEG_THICK
LEG_W = cfg.ALT_LEG_WIDTH
LEG_X0 = SHELF_W / 2.0 - LEG_W / 2.0  # leg/hinge X range, centred on the width
LEG_X1 = SHELF_W / 2.0 + LEG_W / 2.0
HINGE_Y = cfg.ALT_SHELF_CROSS_LIP_T + cfg.ALT_LEG_HINGE_GAP  # just above the cross-lip
HINGE_Z = LEG_LT / 2.0  # hinge axis centred in the leg thickness
HINGE_RK = cfg.ALT_HINGE_R  # knuckle outer radius
HINGE_RP = cfg.ALT_HINGE_PIN_R  # pin radius
# The leg lives in the plate's central opening; it starts just past the leg-knuckle protrusion
# so the knuckles have room, and the leg (thinner than the plate) sits recessed inside the 7 mm.
OPENING_Y0 = HINGE_Y - HINGE_RK - cfg.ALT_LEG_POCKET_CLEAR


def _hinge_segments():
    """Return ``(x_start, x_end, is_plate)`` for each knuckle segment across the hinge."""
    n = cfg.ALT_HINGE_SEGMENTS
    seg = (LEG_X1 - LEG_X0) / n
    return [(LEG_X0 + i * seg, LEG_X0 + (i + 1) * seg, i % 2 == 0) for i in range(n)]


# --- 47/47 thickness split (shared by overlapping parts) ---------------------
SPLIT_BACK = (LEG_LT - cfg.ALT_SPLIT_GAP) / 2.0  # a "back" part keeps Z[0, SPLIT_BACK]
SPLIT_FRONT0 = SPLIT_BACK + cfg.ALT_SPLIT_GAP  # a "front" part keeps Z[SPLIT_FRONT0, LEG_LT]
PROP_SEG_W = (LEG_X1 - LEG_X0) / cfg.ALT_HINGE_SEGMENTS  # prop-leg knuckle width, to match

# --- Base (foot): hinge centred in the bottom border + two flanking legs ------
BASE_HINGE_Y = -cfg.ALT_SHELF_BELOW_LIP + cfg.ALT_SHELF_BORDER / 2.0  # centred in the bottom border
# Base legs stop short of the prop leg's T (T centre is at HINGE_Y + leg length).
BASE_TOP_Y = HINGE_Y + cfg.ALT_LEG_LENGTH - cfg.ALT_LEG_T_DIA / 2.0 - cfg.ALT_BASE_T_GAP
BASE_L_X1 = LEG_X0 - cfg.ALT_BASE_LEG_CLEAR  # left base leg, just left of the prop leg
BASE_L_X0 = BASE_L_X1 - cfg.ALT_BASE_LEG_WIDTH
BASE_R_X0 = LEG_X1 + cfg.ALT_BASE_LEG_CLEAR  # right base leg, just right of the prop leg
BASE_R_X1 = BASE_R_X0 + cfg.ALT_BASE_LEG_WIDTH
BASE_LEGS_X = ((BASE_L_X0, BASE_L_X1), (BASE_R_X0, BASE_R_X1))
# Crossbar high up, just below the leg tops, where it passes under the prop leg.
BASE_CROSS_Y1 = BASE_TOP_Y - cfg.ALT_BASE_CROSS_INSET
BASE_CROSS_Y0 = BASE_CROSS_Y1 - cfg.ALT_BASE_CROSS_WIDTH


def _base_leg_hinge_segments(x0, x1):
    """Return ``(x_start, x_end, is_plate)`` segments for one base leg's hinge.

    Subdivided to the prop-leg knuckle width (so the two hinges match), odd count so the ends
    are plate knuckles and a single moving (leg) knuckle sits in the middle.
    """
    n = max(3, int(round((x1 - x0) / PROP_SEG_W)))
    if n % 2 == 0:
        n += 1
    seg = (x1 - x0) / n
    return [(x0 + i * seg, x0 + (i + 1) * seg, i % 2 == 0) for i in range(n)]


def _box(x, y, z, dx, dy, dz):
    """Return an axis-aligned box solid with minimum corner ``(x, y, z)``."""
    return Part.makeBox(dx, dy, dz, Vector(x, y, z))


def _rounded_rect_prism(x0, y0, w, h, r, z0, dz):
    """Return a rounded-rectangle solid (corner radius ``r``) extruded along ``+Z``.

    Parameters
    ----------
    x0, y0 : float
        Minimum-corner position of the bounding rectangle (mm).
    w, h : float
        Rectangle width (X) and height (Y) (mm).
    r : float
        Corner radius (mm).
    z0 : float
        Base Z of the prism (mm).
    dz : float
        Extrusion height along ``+Z`` (mm).

    Returns
    -------
    Part.Shape
        The extruded rounded-rectangle solid.
    """
    solid = _box(x0 + r, y0, z0, w - 2 * r, h, dz).fuse(_box(x0, y0 + r, z0, w, h - 2 * r, dz))
    for cx, cy in (
        (x0 + r, y0 + r),
        (x0 + w - r, y0 + r),
        (x0 + r, y0 + h - r),
        (x0 + w - r, y0 + h - r),
    ):
        solid = solid.fuse(Part.makeCylinder(r, dz, Vector(cx, cy, z0), Vector(0.0, 0.0, 1.0)))
    return solid


def _corner_cup(at_right):
    """Return one raised, filleted corner cup (cross-lip ∩ side-lip), for the left or right.

    A post is raised at the corner to ``CORNER_H`` (~1/2 the tray height), then a concave
    fillet (a subtracted cylinder) sweeps it back down to the cross-lip height along the
    cross-lip (X) and to the side-lip height along the side-lip (Y), so the tray's bottom
    corner sits in a deeper cup.

    Parameters
    ----------
    at_right : bool
        ``False`` for the left corner (near X = 0), ``True`` for the right (near X = W).

    Returns
    -------
    Part.Shape
        The corner-cup solid.
    """
    t = cfg.ALT_SHELF_THICKNESS
    clt, clh = cfg.ALT_SHELF_CROSS_LIP_T, cfg.ALT_SHELF_CROSS_LIP_H
    slw, slh = cfg.ALT_SHELF_SIDE_LIP_W, cfg.ALT_SHELF_SIDE_LIP_H
    rx, ry = CORNER_H - clh, CORNER_H - slh  # fillet radii = rise from lip to corner height
    top = t + CORNER_H

    if not at_right:
        x_arm, x_post = 0.0, 0.0  # cross-lip arm runs +X from the left edge
        cyl_x_c, cyl_y_base = slw + rx, -1.0
    else:
        x_arm, x_post = SHELF_W - slw - rx, SHELF_W - slw
        cyl_x_c, cyl_y_base = SHELF_W - slw - rx, SHELF_W - slw - 1.0

    block = _box(x_arm, 0.0, t, slw + rx, clt, CORNER_H)  # cross-lip arm
    block = block.fuse(_box(x_post, 0.0, t, slw, clt + ry, CORNER_H))  # side-lip arm
    cyl_x = Part.makeCylinder(rx, clt + 2.0, Vector(cyl_x_c, -1.0, top), Vector(0.0, 1.0, 0.0))
    cyl_y = Part.makeCylinder(
        ry, slw + 2.0, Vector(cyl_y_base, clt + ry, top), Vector(1.0, 0.0, 0.0)
    )
    return block.cut(cyl_x).cut(cyl_y)


def build_shelf():
    """Build the shelf: a rounded-rectangle border frame with the tray lips on top.

    The plate lies in the X-Y plane (X is the width, Y the height the tray lies along) with
    its top surface at ``Z = ALT_SHELF_THICKNESS``. The cross-lip and side lips stand off that
    surface; the unused centre is cut away to leave a border frame.

    Returns
    -------
    Part.Shape
        The shelf solid.
    """
    w, h = SHELF_W, cfg.ALT_SHELF_HEIGHT
    below = cfg.ALT_SHELF_BELOW_LIP
    t = cfg.ALT_SHELF_THICKNESS
    r, b = cfg.ALT_SHELF_CORNER_R, cfg.ALT_SHELF_BORDER
    clh, clt = cfg.ALT_SHELF_CROSS_LIP_H, cfg.ALT_SHELF_CROSS_LIP_T
    slw, slh = cfg.ALT_SHELF_SIDE_LIP_W, cfg.ALT_SHELF_SIDE_LIP_H

    # The lip line is Y = 0: the tray lies against Y[0, h]; the frame extends `below` past the
    # lip (Y < 0) down toward the base. Deployed, this whole plate sits 15 deg off vertical.
    plate = _rounded_rect_prism(0.0, -below, w, h + below, r, 0.0, t)

    # Central opening: houses the leg AND lightens the tray region. Through the plate, from just
    # past the hinge-knuckle protrusion up to the top border. The plate hinge is added back.
    shelf = plate.cut(_box(b, OPENING_Y0, -1.0, w - 2 * b, (h - b) - OPENING_Y0, t + 2.0))

    # Hollow out the extension below the lip too, leaving a bottom border and side rails.
    if below > b:
        shelf = shelf.cut(_box(b, -below + b, -1.0, w - 2 * b, below - b, t + 2.0))

    # Tray-retaining lips on the top surface, plus the raised, filleted corner cups; all
    # clipped to the plate footprint so they never overhang the rounded edges.
    foot = _rounded_rect_prism(0.0, -below, w, h + below, r, 0.0, t + CORNER_H)
    cross = _box(0.0, 0.0, t, w, clt, clh)  # across the bottom edge
    left = _box(0.0, clt, t, slw, h - clt, slh)  # outer-edge side lips, above the cross-lip
    right = _box(w - slw, clt, t, slw, h - clt, slh)
    lips = cross.fuse(left).fuse(right).fuse(_corner_cup(False)).fuse(_corner_cup(True))
    lips = lips.common(foot)
    shelf = shelf.fuse(lips)

    # Plate side of the print-in-place hinge (the leg side is built with the leg).
    shelf = shelf.fuse(_plate_hinge())

    # Base: clear so its legs pass/swing (47/47 at the lip band), then the base plate hinges.
    shelf = shelf.cut(_base_leg_clearances())
    shelf = shelf.fuse(_base_plate_hinge())
    return shelf


def _plate_hinge():
    """Return the plate side of the hinge: the pin plus the plate knuckles and their necks.

    The pin spans the whole hinge and anchors to the plate knuckles (the segment ends); each
    plate knuckle is tied back to the solid lip-band plate by a full-height neck across the
    opening. The leg knuckles (built with the leg) ride the pin between them.
    """
    t = cfg.ALT_SHELF_THICKNESS
    pin = Part.makeCylinder(
        HINGE_RP, LEG_X1 - LEG_X0, Vector(LEG_X0, HINGE_Y, HINGE_Z), Vector(1.0, 0.0, 0.0)
    )
    out = pin
    for xa, xb, is_plate in _hinge_segments():
        if not is_plate:
            continue
        knuckle = Part.makeCylinder(
            HINGE_RK, xb - xa, Vector(xa, HINGE_Y, HINGE_Z), Vector(1.0, 0.0, 0.0)
        )
        neck = _box(xa, OPENING_Y0 - 1.0, 0.0, xb - xa, HINGE_Y - (OPENING_Y0 - 1.0), t)
        out = out.fuse(knuckle).fuse(neck)
    return out


def _flat_cylinder(x0, yc, zc, length, dia, thick):
    """Return a flattened cylinder (axis ``+X``): full diameter in Y, flattened in Z.

    A cylinder of diameter ``dia`` swept ``length`` along ``+X`` from ``x0`` (circle centred at
    ``(yc, zc)`` in Y-Z), with its top and bottom trimmed to an overall ``thick`` in Z -- a
    stadium cross-section. Used for the leg's T-shaped locking end.

    Parameters
    ----------
    x0 : float
        Start X of the axis (mm).
    yc, zc : float
        Axis position in the Y-Z plane (mm).
    length : float
        Length along ``+X`` (mm).
    dia : float
        Cylinder diameter before flattening (mm).
    thick : float
        Flattened overall thickness in Z (mm).

    Returns
    -------
    Part.Shape
        The flattened-cylinder solid.
    """
    cyl = Part.makeCylinder(dia / 2.0, length, Vector(x0, yc, zc), Vector(1.0, 0.0, 0.0))
    htop = _box(x0 - 1.0, yc - dia, zc + thick / 2.0, length + 2.0, 2.0 * dia, dia)
    hbot = _box(x0 - 1.0, yc - dia, zc - thick / 2.0 - dia, length + 2.0, 2.0 * dia, dia)
    return cyl.cut(htop).cut(hbot)


def build_leg():
    """Build the prop leg, nested inside the shelf-plate pocket, free except for the hinge.

    A flat bar (``Z`` in ``[0, ALT_LEG_THICK]``, on the back of the plate) running from the
    hinge up the shelf, ending in a flattened-cylinder **T** for locking upright. Its end of
    the print-in-place hinge is a set of knuckles bored to ride the plate's pin; the bar is
    notched clear of the plate knuckles. Built in the assembled (folded-in) position with all
    the hinge/pocket clearances, so it prints in place without fusing to the shelf.

    Returns
    -------
    Part.Shape
        The leg solid.
    """
    length = cfg.ALT_LEG_LENGTH
    ca = cfg.ALT_HINGE_AXIAL_CLEAR
    bore = cfg.ALT_HINGE_PIN_R + cfg.ALT_HINGE_PIN_CLEAR
    bar = _box(LEG_X0, HINGE_Y, 0.0, LEG_W, length, LEG_LT)

    leg = bar
    pin_hole = Part.makeCylinder(
        bore, LEG_W + 2.0, Vector(LEG_X0 - 1.0, HINGE_Y, HINGE_Z), Vector(1.0, 0.0, 0.0)
    )
    for xa, xb, is_plate in _hinge_segments():
        if is_plate:
            # Notch the bar clear of the plate knuckle (X and Y axial/running clearance).
            notch = _box(
                xa - ca, HINGE_Y - 1.0, -1.0, (xb - xa) + 2 * ca, HINGE_RK + ca + 1.0, LEG_LT + 2.0
            )
            leg = leg.cut(notch)
        else:
            # Leg knuckle: a cylinder on the hinge axis, bored for the pin, axial clearance.
            knuckle = Part.makeCylinder(
                HINGE_RK,
                (xb - xa) - 2 * ca,
                Vector(xa + ca, HINGE_Y, HINGE_Z),
                Vector(1.0, 0.0, 0.0),
            )
            leg = leg.fuse(knuckle)
    leg = leg.cut(pin_hole)  # bore all knuckles to clear the pin

    tx0 = SHELF_W / 2.0 - cfg.ALT_LEG_T_LEN / 2.0
    tcross = _flat_cylinder(
        tx0, HINGE_Y + length, HINGE_Z, cfg.ALT_LEG_T_LEN, cfg.ALT_LEG_T_DIA, cfg.ALT_LEG_T_THICK
    )
    leg = leg.fuse(tcross)

    # Keep only the front ~47% where the base crossbar passes under the prop leg (the crossbar
    # takes the back ~47%, with the split gap between, so they don't fuse).
    clr = cfg.ALT_BASE_LEG_CLEAR
    leg = leg.cut(
        _box(
            LEG_X0 - 1.0,
            BASE_CROSS_Y0 - clr,
            -1.0,
            LEG_W + 2.0,
            (BASE_CROSS_Y1 - BASE_CROSS_Y0) + 2 * clr,
            SPLIT_FRONT0 + 1.0,
        )
    )
    return leg


def _base_plate_hinge():
    """Return the shelf side of the base's two hinges: a pin per base leg plus plate knuckles.

    Each base leg has its own hinge (subdivided to the prop-leg knuckle width); the plate
    knuckles are fused into the bottom border on either side of the moving (leg) knuckle.
    """
    out = None
    for x0, x1 in BASE_LEGS_X:
        pin = Part.makeCylinder(
            HINGE_RP, x1 - x0, Vector(x0, BASE_HINGE_Y, HINGE_Z), Vector(1.0, 0.0, 0.0)
        )
        out = pin if out is None else out.fuse(pin)
        for xa, xb, is_plate in _base_leg_hinge_segments(x0, x1):
            if is_plate:
                out = out.fuse(
                    Part.makeCylinder(
                        HINGE_RK, xb - xa, Vector(xa, BASE_HINGE_Y, HINGE_Z), Vector(1.0, 0.0, 0.0)
                    )
                )
    return out


def _base_leg_clearances():
    """Return the material to remove from the shelf so the base legs are free and swing.

    Below the lip band each leg gets a full-depth slot (clearing the bottom border / hinge
    region); at the lip band the cut is only the **back** of the shelf, so the front ~47% stays
    as the cross-lip support (the leg keeps the back ~47% there) -- the shared-thickness cut.
    """
    clr = cfg.ALT_BASE_LEG_CLEAR
    t = cfg.ALT_SHELF_THICKNESS
    out = None
    for x0, x1 in BASE_LEGS_X:
        # full-depth slot from the hinge up to the lip band
        below = _box(
            x0 - clr,
            BASE_HINGE_Y - 1.0,
            -1.0,
            (x1 - x0) + 2 * clr,
            (1.0) - (BASE_HINGE_Y - 1.0),
            t + 2.0,
        )
        # back-only cut across the lip band (keep the front as cross-lip support)
        band = _box(x0 - clr, 0.0, -1.0, (x1 - x0) + 2 * clr, OPENING_Y0, SPLIT_FRONT0 + 1.0)
        out = below.fuse(band) if out is None else out.fuse(below).fuse(band)
    return out


def build_base():
    """Build the base (foot): two legs up from the bottom-border hinge, joined by a high crossbar.

    The legs flank the prop leg in the central opening, stop short of its T, and keep only
    their back ~47% where they cross the lip band. The crossbar sits high (just below the leg
    tops) and is thinned to its back ~47% where it passes under the prop leg. The leg knuckles
    ride the shelf's pins. Free of the shelf except via the hinges.

    Returns
    -------
    Part.Shape
        The base solid.
    """
    ca = cfg.ALT_HINGE_AXIAL_CLEAR
    bore = HINGE_RP + cfg.ALT_HINGE_PIN_CLEAR
    clr = cfg.ALT_BASE_LEG_CLEAR

    base = None
    for x0, x1 in BASE_LEGS_X:
        leg = _box(x0, BASE_HINGE_Y, 0.0, x1 - x0, BASE_TOP_Y - BASE_HINGE_Y, LEG_LT)
        # keep only the back ~47% where this leg crosses the lip band (shelf keeps the front)
        leg = leg.cut(_box(x0 - 1.0, 0.0, SPLIT_BACK, (x1 - x0) + 2.0, OPENING_Y0, LEG_LT))
        base = leg if base is None else base.fuse(leg)
        # moving (leg) knuckle on the hinge axis
        for xa, xb, is_plate in _base_leg_hinge_segments(x0, x1):
            if not is_plate:
                base = base.fuse(
                    Part.makeCylinder(
                        HINGE_RK,
                        (xb - xa) - 2 * ca,
                        Vector(xa + ca, BASE_HINGE_Y, HINGE_Z),
                        Vector(1.0, 0.0, 0.0),
                    )
                )
        # bar notch so the leg clears the plate knuckles at the hinge
        for xa, xb, is_plate in _base_leg_hinge_segments(x0, x1):
            if is_plate:
                base = base.cut(
                    _box(
                        xa - ca,
                        BASE_HINGE_Y - 1.0,
                        -1.0,
                        (xb - xa) + 2 * ca,
                        HINGE_RK + ca + 1.0,
                        LEG_LT + 2.0,
                    )
                )
        # bore the knuckles to ride the pin
        base = base.cut(
            Part.makeCylinder(
                bore,
                (x1 - x0) + 2.0,
                Vector(x0 - 1.0, BASE_HINGE_Y, HINGE_Z),
                Vector(1.0, 0.0, 0.0),
            )
        )

    # Crossbar joining the legs, high up; back ~47% where it passes under the prop leg.
    cross = _box(
        BASE_L_X0, BASE_CROSS_Y0, 0.0, BASE_R_X1 - BASE_L_X0, BASE_CROSS_Y1 - BASE_CROSS_Y0, LEG_LT
    )
    cross = cross.cut(
        _box(
            LEG_X0 - clr,
            BASE_CROSS_Y0 - 1.0,
            SPLIT_BACK,
            (LEG_X1 - LEG_X0) + 2 * clr,
            (BASE_CROSS_Y1 - BASE_CROSS_Y0) + 2.0,
            LEG_LT,
        )
    )
    return base.fuse(cross)


def build_all():
    """Build the alternate-stand parts for the document, offset beside the tray for review.

    Returns
    -------
    list of tuple
        ``[(name, shape, (r, g, b), visible, transparency)]`` matching the macro's part
        tuple, or an empty list when ``SHOW_ALT_STAND`` is false.
    """
    if not cfg.SHOW_ALT_STAND:
        return []
    tr = cfg.ALT_STAND_TRANSPARENCY
    parts = []
    for name, shape, rgb in (
        ("AltShelf", build_shelf(), (0.55, 0.40, 0.80)),
        ("AltLeg", build_leg(), (0.85, 0.55, 0.20)),
        ("AltBase", build_base(), (0.25, 0.65, 0.55)),
    ):
        shape.translate(Vector(DISPLAY_X_OFFSET, 0.0, 0.0))
        parts.append((name, shape, rgb, True, tr))
    return parts
