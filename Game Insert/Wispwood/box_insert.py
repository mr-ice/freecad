"""FreeCAD builders for the Wispwood box insert (bottom small tray + printed top tray).

Builds the two printed trays from the placement rectangles in :mod:`box_layout` and the
sizes in :mod:`config`, in the box coordinate frame (origin box front-left-bottom; X width,
Y length, Z up). A non-printing box-reference shell is provided for fit checking.

All offsets derive from named constants (repo ``CLAUDE.md``); no measured coordinates.

``place_wispwood`` / ``place_stand`` position the parts built by the ``wispwood`` and
``stand`` modules (which are modelled in their own frames) into the box bays defined by
:func:`box_layout.bottom_regions`, so the whole packed box is viewable in one document.

Public API
----------
``build_top_tray``, ``build_box_reference``, ``build_all``,
``place_wispwood``, ``place_stand``.
"""

import box_layout as bl
import config as cfg
import derived as d
import Part
from FreeCAD import Vector


def _box(x, y, z, dx, dy, dz):
    """Return an axis-aligned box solid with minimum corner ``(x, y, z)``."""
    return Part.makeBox(dx, dy, dz, Vector(x, y, z))


def _assert_within_bed(shape, name):
    """Raise AssertionError if a printed part's XY bounding box exceeds the bed limit."""
    bb = shape.BoundBox
    limit = cfg.MAX_PRINTER_DIMENSION
    assert (
        bb.XLength <= limit and bb.YLength <= limit
    ), f"{name} {bb.XLength:.1f}x{bb.YLength:.1f} exceeds bed {limit}"


def build_top_tray():
    """Build the printed top tray: board pocket and marker trough.

    A ``TOP_TRAY_DEPTH``-tall plate over the box footprint with two pockets cut directly
    from the cavity rects returned by :func:`box_layout.top_regions` (no further inset).
    The board pocket holds the 5 loose board pieces; the marker trough holds 4 markers along
    Y. The 1st-player paw, score pad, and booklet lie loose on top (no pocket). No finger
    grooves — the board pieces and markers are flat and lift straight out.

    Returns
    -------
    Part.Shape
        The top-tray solid, in the box frame (local Z 0..TOP_TRAY_DEPTH; the macro lifts it
        to ``SMALL_TRAY_RIM_Z``).
    """
    t = bl.top_regions()
    depth = cfg.TOP_TRAY_DEPTH
    floor = cfg.INSERT_FLOOR
    # Oversize the plate by TOP_TRAY_FIT per side so it friction-fits and reaches the box ends.
    fit = cfg.TOP_TRAY_FIT
    block = _box(-fit, -fit, 0.0, cfg.BOX_W + 2 * fit, cfg.BOX_L + 2 * fit, depth)

    # Round all four vertical corners to the box's interior radius (so the oversized plate seats
    # concentric with the rounded box walls), matching the bottom box's filleted corners.
    rr = cfg.BOX_CORNER_R + fit
    corners = [
        e
        for e in block.Edges
        if abs(e.BoundBox.ZLength - depth) < 1e-6
        and e.BoundBox.XLength < 1e-6
        and e.BoundBox.YLength < 1e-6
    ]
    if corners:
        block = block.makeFillet(rr, corners)

    for key in ("board_pocket", "marker_trough"):
        r = t[key]
        block = block.cut(_box(r.x, r.y, floor, r.w, r.h, depth))

    _assert_within_bed(block, "TopTray")
    return block


def build_box_reference():
    """Return a non-printing transparent shell of the box interior for fit checking.

    Returns
    -------
    Part.Shape
        A thin-walled open box ``BOX_W x BOX_L x BOX_H``; do not export.
    """
    wall = 1.0
    outer = _box(-wall, -wall, -wall, cfg.BOX_W + 2 * wall, cfg.BOX_L + 2 * wall, cfg.BOX_H + wall)
    inner = _box(0.0, 0.0, 0.0, cfg.BOX_W, cfg.BOX_L, cfg.BOX_H + 1.0)
    return outer.cut(inner)


def place_wispwood(parts):
    """Position native Wispwood parts into the box's wispwood bay; drop the integrated stand.

    The Wispwood tray is modelled with its long axis along ``Y``; the box bay wants it along
    ``X`` (``bottom_regions()['wispwood']``), so each part is rotated 90 deg about ``Z`` and
    shifted back into ``+X``. The integrated folding stand (``Stand`` / ``StandDeployed``) is
    dropped — the separate alt stand is used instead.

    Parameters
    ----------
    parts : list of tuple
        The ``(name, shape, rgb, visible, transparency)`` tuples from ``wispwood.build_all``.

    Returns
    -------
    list of tuple
        The kept parts, transformed into the box frame.
    """
    rect = bl.bottom_regions()["wispwood"]
    out = []
    for name, shape, rgb, visible, transparency in parts:
        if name in ("Stand", "StandDeployed"):
            continue
        shape.rotate(Vector(0.0, 0.0, 0.0), Vector(0.0, 0.0, 1.0), 90.0)
        shape.translate(Vector(d.OUTER_LENGTH + rect.x, rect.y, 0.0))
        out.append((name, shape, rgb, visible, transparency))
    return out


def place_stand(parts):
    """Position the stand into the box's stand bay (front-left of the bottom layer).

    ``stand.build_all`` offsets its parts beside the tray for standalone review; this undoes
    that offset and shifts the stand (whose native ``Y`` starts at ``stand.NATIVE_Y_MIN``)
    into ``bottom_regions()['alt_bay']``.

    Parameters
    ----------
    parts : list of tuple
        The ``(name, shape, rgb, visible, transparency)`` tuples from ``stand.build_all``.

    Returns
    -------
    list of tuple
        The parts translated into the box frame.
    """
    import stand as s

    rect = bl.bottom_regions()["alt_bay"]
    dx = rect.x - s.DISPLAY_X_OFFSET
    dy = rect.y - s.NATIVE_Y_MIN
    out = []
    for name, shape, rgb, visible, transparency in parts:
        shape.translate(Vector(dx, dy, 0.0))
        out.append((name, shape, rgb, visible, transparency))
    return out


def build_all():
    """Build the box-insert parts in box position, as macro part tuples.

    Returns
    -------
    list of tuple
        ``(name, shape, (r, g, b), visible, transparency)``. The top tray is lifted to
        ``SMALL_TRAY_RIM_Z``. ``BoxReference`` is a hidden, transparent fit-check shell.
    """
    top = build_top_tray()
    top.translate(Vector(0.0, 0.0, cfg.SMALL_TRAY_RIM_Z))
    return [
        ("TopTray", top, (0.45, 0.65, 0.85), True, 40),
        ("BoxReference", build_box_reference(), (0.6, 0.6, 0.6), False, 80),
    ]
