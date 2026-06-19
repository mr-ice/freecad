"""FreeCAD builders for the Wispwood box insert (bottom small tray + printed top tray).

Builds the two printed trays from the placement rectangles in :mod:`box_layout` and the
sizes in :mod:`config`, in the box coordinate frame (origin box front-left-bottom; X width,
Y length, Z up). A non-printing box-reference shell is provided for fit checking.

All offsets derive from named constants (repo ``CLAUDE.md``); no measured coordinates.

Public API
----------
``build_small_tray``, ``build_top_tray``, ``build_box_reference``, ``build_all``.
"""

import box_layout as bl
import config as cfg
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
    and the Wispwood tray. Wells are cut to each component's depth; a finger scoop notches
    the card and round wells for access.

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
    block = block.cut(
        _box(cats.x, cats.y, rim - cfg.CAT_SIZE - 1.0, cats.w, cats.h, cfg.CAT_SIZE + 2.0)
    )

    # Round tokens: cylindrical well.
    rnd = b["well_round"]
    r = cfg.ROUND_TOKEN_DIA / 2.0 + cfg.COMPONENT_CLEARANCE
    rnd_depth = cfg.ROUND_TOKEN_COUNT * cfg.ROUND_TOKEN_THICKNESS + 3.0
    cx, cy = rnd.x + rnd.w / 2.0, rnd.y + rnd.h / 2.0
    block = block.cut(
        Part.makeCylinder(r, rnd_depth + 1.0, Vector(cx, cy, rim - rnd_depth), Vector(0, 0, 1))
    )

    # Finger scoop on the card well (a half-cylinder notch in the near wall).
    scoop_r = 12.0
    block = block.cut(
        Part.makeCylinder(
            scoop_r, card.w, Vector(card.x, card.y + card.h / 2.0, rim), Vector(1, 0, 0)
        )
    )
    _assert_within_bed(block, "SmallTray")
    return block


def build_top_tray():
    """Build the printed top tray: board pocket, marker trough, paw recess.

    A ``TOP_TRAY_DEPTH``-tall plate over the box footprint with three pockets. The board
    pocket holds the 5 loose pieces; the marker trough holds 4 markers along Y; the paw
    recess holds the 1st-player token. Score pad and booklet lie loose on top (no pocket).

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

    for key in ("board_pocket", "marker_trough", "paw"):
        r = t[key]
        block = block.cut(
            _box(
                r.x + cfg.INSERT_WALL,
                r.y + cfg.INSERT_WALL,
                floor,
                r.w - 2 * cfg.INSERT_WALL,
                r.h - 2 * cfg.INSERT_WALL,
                depth,
            )
        )

    # Finger scoop into the board pocket (half-cylinder through the near long wall).
    p = t["board_pocket"]
    block = block.cut(
        Part.makeCylinder(
            12.0, p.w, Vector(p.x + p.w / 2.0, p.y + cfg.INSERT_WALL, depth), Vector(0, -1, 0)
        )
    )
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
        ("BoxReference", build_box_reference(), (0.6, 0.6, 0.6), True, 80),
    ]
