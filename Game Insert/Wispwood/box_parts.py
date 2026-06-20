"""FreeCAD reference solids for the loose box components + the leftover-space block.

Models every remaining game component (the four outer map sections, the inner map section, the
card deck, the 1st-player paw, the solo tokens, the cat tokens, the markers, and the score pad)
as a reference solid at its real size, laid out in a palette beside the box. It also builds a
**leftover block** = the box interior minus the Wispwood tray, as the stock from which the new
organizer will be carved.

Fungible multiples (solo tokens, cats, markers) are modelled as a single **stack** (the storage
envelope) rather than separate pieces; the four outer map sections are separate objects. The
irregular parts (outer map sections, paw, ruler/markers) use **outlines traced from photos** on
Letter paper (see ``tools/trace_parts.py``); the rest come from sizes in :mod:`config`. Nothing
here is a printed part — these are design references.

Public API
----------
``build_perimeter_map``, ``build_center_map``, ``build_cards``, ``build_paw``,
``build_solo_tokens``, ``build_cats``, ``build_markers``, ``build_scorepad``,
``build_leftover_block``, ``build_all``.
"""

import math

import box_layout as bl
import config as cfg
import derived as d
import Part
from FreeCAD import Vector


def _box(x, y, z, dx, dy, dz):
    """Return an axis-aligned box solid with minimum corner ``(x, y, z)``."""
    return Part.makeBox(dx, dy, dz, Vector(x, y, z))


def _at_origin(shape):
    """Translate ``shape`` so its bounding-box minimum corner sits at the origin."""
    bb = shape.BoundBox
    shape.translate(Vector(-bb.XMin, -bb.YMin, -bb.ZMin))
    return shape


def _octagon_face(ptp):
    """Return a regular-octagon face (point-to-point ``ptp``), centred at the origin in Z = 0.

    Vertices sit at 22.5 deg + k*45 deg, so the octagon has the usual flat top/bottom/sides.
    """
    r = ptp / 2.0  # circumradius (point-to-point = 2 r)
    pts = [
        Vector(
            r * math.cos(math.radians(22.5 + 45 * k)),
            r * math.sin(math.radians(22.5 + 45 * k)),
            0.0,
        )
        for k in range(8)
    ]
    pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts))


def _profile_solid(points, thk):
    """Extrude a closed 2-D outline (list of ``(x, y)`` mm) by ``thk`` in Z, bbox min at origin."""
    pts = [Vector(x, y, 0.0) for x, y in points]
    pts.append(pts[0])
    return _at_origin(Part.Face(Part.makePolygon(pts)).extrude(Vector(0.0, 0.0, thk)))


# --- Measured outlines (mm), traced from photos on Letter paper by tools/trace_parts.py ------
# Each is a closed polygon with bbox minimum at the origin; the four outer map sections are
# identical, so one profile is reused. Re-run the tracer to refresh these from new photos.
_OUTER_MAP_PROFILE = [
    (0.0, 49.5),
    (13.0, 60.0),
    (17.0, 54.0),
    (37.8, 60.5),
    (47.0, 75.0),
    (42.8, 83.5),
    (51.5, 90.2),
    (96.2, 65.8),
    (145.8, 79.5),
    (153.0, 70.8),
    (160.8, 75.0),
    (176.5, 65.2),
    (182.5, 51.2),
    (182.0, 45.0),
    (176.8, 40.8),
    (186.2, 27.5),
    (89.8, 0.0),
]
_PAW_PROFILE = [
    (22.0, 1.2),
    (17.2, 4.8),
    (12.8, 13.5),
    (4.5, 19.0),
    (0.0, 28.8),
    (2.0, 38.0),
    (9.2, 46.5),
    (11.5, 56.2),
    (17.8, 63.0),
    (25.5, 65.2),
    (35.0, 64.0),
    (46.2, 65.8),
    (50.5, 64.5),
    (56.8, 60.0),
    (60.5, 53.5),
    (61.2, 48.5),
    (69.0, 40.2),
    (71.2, 32.5),
    (71.0, 27.5),
    (67.5, 21.2),
    (60.2, 16.2),
    (57.5, 7.8),
    (51.2, 1.8),
    (46.2, 0.8),
    (36.2, 3.0),
    (29.5, 0.0),
]
_RULER_PROFILE = [
    (0.0, 4.5),
    (1.8, 14.8),
    (17.0, 22.2),
    (19.2, 34.5),
    (195.8, 34.8),
    (198.0, 21.5),
    (210.2, 17.0),
    (214.0, 11.2),
    (213.0, 0.5),
    (1.2, 0.0),
]


def build_perimeter_map():
    """Return one outer map section, from the photo-traced quarter-octagon puzzle outline.

    Returns
    -------
    Part.Shape
        The board-section solid (bbox min at the origin), ~186 x 90 mm.
    """
    return _profile_solid(_OUTER_MAP_PROFILE, cfg.BOARD_THICKNESS)


def build_center_map():
    """Return the inner map section: a regular octagon plate, ``BOARD_CENTER_PTP`` point-to-point.

    Returns
    -------
    Part.Shape
        The center-octagon solid (bbox min at the origin).
    """
    return _at_origin(
        _octagon_face(cfg.BOARD_CENTER_PTP).extrude(Vector(0.0, 0.0, cfg.BOARD_THICKNESS))
    )


def build_cards():
    """Return the card deck (unsleeved) as a solid block."""
    return _box(0.0, 0.0, 0.0, cfg.CARD_W, cfg.CARD_H, cfg.CARD_DECK_THICKNESS)


def build_paw():
    """Return the 1st-player paw token, from the photo-traced cat-paw outline (~71 x 66 mm)."""
    return _profile_solid(_PAW_PROFILE, cfg.PAW_THICKNESS)


def build_solo_tokens():
    """Return the 8 solo tokens as a single stacked cylinder (the storage envelope)."""
    h = cfg.ROUND_TOKEN_COUNT * cfg.ROUND_TOKEN_THICKNESS
    return Part.makeCylinder(cfg.ROUND_TOKEN_DIA / 2.0, h, Vector(0.0, 0.0, 0.0), Vector(0, 0, 1))


def build_cats():
    """Return the 6 cat tokens as a single stacked block (35x35 face, double-tile thickness)."""
    h = cfg.CAT_COUNT * cfg.CAT_THICKNESS
    return _box(0.0, 0.0, 0.0, cfg.CAT_SIZE, cfg.CAT_SIZE, h)


def build_markers():
    """Return the 4 markers (rulers/solo board) as a stack, using the photo-traced ruler outline.

    The markers are the ~214 x 35 mm number-track standees; modelled as one ruler profile
    extruded to the 4-piece stack thickness (the storage envelope).
    """
    return _profile_solid(_RULER_PROFILE, cfg.MARKER_COUNT * cfg.MARKER_THICKNESS)


def build_scorepad():
    """Return the score pad as a solid block."""
    return _box(0.0, 0.0, 0.0, cfg.SCOREPAD_W, cfg.SCOREPAD_H, cfg.SCOREPAD_THICKNESS)


def build_leftover_block():
    """Return the leftover space: the box interior minus the Wispwood tray volume.

    The Wispwood tray occupies ``bottom_regions()['wispwood']`` up to its wall top; everything
    else in the ``BOX_W x BOX_L x BOX_H`` interior (including the space above the tray) is the
    stock this block represents, for carving the new organizer.

    Returns
    -------
    Part.Shape
        The leftover-block solid, in the box frame.
    """
    r = bl.bottom_regions()["wispwood"]
    c = cfg.COMPONENT_CLEARANCE
    block = _box(0.0, 0.0, 0.0, cfg.BOX_W, cfg.BOX_L, cfg.BOX_H)
    tray = _box(r.x - c, r.y - c, 0.0, r.w + 2 * c, r.h + 2 * c, d.WALL_TOP + c)
    return block.cut(tray)


# Component palette: each entry is (name, builder, (r, g, b)). The four outer map sections are
# separate objects; fungible multiples are single stacks.
_PALETTE = [
    ("MapOuter1", build_perimeter_map, (0.45, 0.65, 0.45)),
    ("MapOuter2", build_perimeter_map, (0.45, 0.65, 0.45)),
    ("MapOuter3", build_perimeter_map, (0.45, 0.65, 0.45)),
    ("MapOuter4", build_perimeter_map, (0.45, 0.65, 0.45)),
    ("MapCenter", build_center_map, (0.30, 0.55, 0.30)),
    ("Cards", build_cards, (0.85, 0.75, 0.45)),
    ("PawToken", build_paw, (0.85, 0.55, 0.55)),
    ("SoloTokensx8", build_solo_tokens, (0.55, 0.55, 0.85)),
    ("CatTokensx6", build_cats, (0.70, 0.50, 0.80)),
    ("Markersx4", build_markers, (0.50, 0.75, 0.80)),
    ("ScorePad", build_scorepad, (0.80, 0.80, 0.60)),
]


def build_all():
    """Build every component (laid out in a palette beside the box) + the leftover block.

    Returns
    -------
    list of tuple
        ``(name, shape, (r, g, b), visible, transparency)``. The leftover block is shown
        transparent in the box; the components flow in columns to the right of the box (X >
        ``BOX_W``) so they are all visible and can be dragged into place to design the organizer.
    """
    gap = 10.0
    parts = [("LeftoverBlock", build_leftover_block(), (0.6, 0.6, 0.6), True, 70)]

    cx = cfg.BOX_W + 30.0
    cy = 0.0
    col_w = 0.0
    for name, builder, rgb in _PALETTE:
        shape = _at_origin(builder())
        bb = shape.BoundBox
        if cy > 0.0 and cy + bb.YLength > cfg.BOX_L:  # wrap to a new column
            cx += col_w + gap
            cy = 0.0
            col_w = 0.0
        shape.translate(Vector(cx, cy, 0.0))
        parts.append((name, shape, rgb, True, 0))
        cy += bb.YLength + gap
        col_w = max(col_w, bb.XLength)
    return parts
