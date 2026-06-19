"""FreeCAD builders for the Wispwood box insert (bottom small tray + printed top tray).

Builds the two printed trays from the placement rectangles in :mod:`box_layout` and the
sizes in :mod:`config`, in the box coordinate frame (origin box front-left-bottom; X width,
Y length, Z up). A non-printing box-reference shell is provided for fit checking.

All offsets derive from named constants (repo ``CLAUDE.md``); no measured coordinates.

``place_wispwood`` / ``place_alt_stand`` position the parts built by the ``wispwood`` and
``alt_stand`` modules (which are modelled in their own frames) into the box bays defined by
:func:`box_layout.bottom_regions`, so the whole packed box is viewable in one document.

Public API
----------
``build_small_tray``, ``build_top_tray``, ``build_box_reference``, ``build_all``,
``place_wispwood``, ``place_alt_stand``.
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


def build_small_tray():
    """Build the bottom components tray: cats-on-edge slot, card well, round-token well.

    The tray outer walls rise to ``SMALL_TRAY_RIM_Z`` so the top tray rests flat across it
    and the Wispwood tray. Each well is cut to its component's depth and gets one vertical
    finger groove cut through a side wall, running the full height of the hole, so a finger
    can reach down beside the stack.

    Returns
    -------
    Part.Shape
        The small-tray solid, positioned in the box frame.
    """
    b = bl.bottom_regions()
    tray = b["small_tray"]
    rim = cfg.SMALL_TRAY_RIM_Z
    block = _box(tray.x, tray.y, 0.0, tray.w, tray.h, rim)

    # Card well: depth = deck thickness + access margin.
    card = b["well_card"]
    card_depth = cfg.CARD_DECK_THICKNESS + 3.0
    block = block.cut(_box(card.x, card.y, rim - card_depth, card.w, card.h, card_depth + 1.0))

    # Cats on edge: full-height slot (35 deep) so the 35 mm faces stand vertical.
    cats = b["well_cats"]
    cats_floor = rim - cfg.CAT_SIZE
    block = block.cut(_box(cats.x, cats.y, cats_floor - 1.0, cats.w, cats.h, cfg.CAT_SIZE + 2.0))

    # Round tokens: cylindrical well.
    rnd = b["well_round"]
    r = cfg.ROUND_TOKEN_DIA / 2.0 + cfg.COMPONENT_CLEARANCE
    rnd_depth = cfg.ROUND_TOKEN_COUNT * cfg.ROUND_TOKEN_THICKNESS + 3.0
    cx, cy = rnd.x + rnd.w / 2.0, rnd.y + rnd.h / 2.0
    block = block.cut(
        Part.makeCylinder(r, rnd_depth + 1.0, Vector(cx, cy, rim - rnd_depth), Vector(0, 0, 1))
    )

    # One vertical finger groove per well: a Z-axis cylinder centred on a well side wall (its
    # radius exceeds the wall, so it cuts through), spanning the full hole height. Each is
    # placed on a side that backs onto tray body (not a neighbouring well): card +X, cats +Y,
    # round +X.
    for groove_cx, groove_cy, floor_z in (
        (card.x + card.w, card.y + card.h / 2.0, rim - card_depth),  # card: right wall
        (cats.x + cats.w / 2.0, cats.y + cats.h, cats_floor),  # cats: back (+Y) wall
        (rnd.x + rnd.w, rnd.y + rnd.h / 2.0, rim - rnd_depth),  # round: right wall
    ):
        block = block.cut(
            Part.makeCylinder(
                cfg.FINGER_GROOVE_R,
                (rim + 1.0) - floor_z,
                Vector(groove_cx, groove_cy, floor_z),
                Vector(0, 0, 1),
            )
        )
    _assert_within_bed(block, "SmallTray")
    return block


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
    block = _box(0.0, 0.0, 0.0, cfg.BOX_W, cfg.BOX_L, depth)

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


def place_alt_stand(parts):
    """Position the folded alt stand into the box's alt-stand bay, lying flat on the floor.

    ``alt_stand.build_all`` offsets its parts beside the tray for standalone review; this
    undoes that offset and shifts the folded stand (whose native ``Y`` starts at
    ``-ALT_SHELF_BELOW_LIP``) into ``bottom_regions()['alt_bay']``.

    Parameters
    ----------
    parts : list of tuple
        The ``(name, shape, rgb, visible, transparency)`` tuples from ``alt_stand.build_all``.

    Returns
    -------
    list of tuple
        The parts translated into the box frame.
    """
    import alt_stand as a

    rect = bl.bottom_regions()["alt_bay"]
    dx = rect.x - a.DISPLAY_X_OFFSET
    dy = rect.y + cfg.ALT_SHELF_BELOW_LIP
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
        ("SmallTray", build_small_tray(), (0.85, 0.75, 0.45), True, 0),
        ("TopTray", top, (0.45, 0.65, 0.85), True, 40),
        ("BoxReference", build_box_reference(), (0.6, 0.6, 0.6), False, 80),
    ]
