"""FreeCAD reference solids for the loose box components + the leftover-space block.

Models every remaining game component (the four outer map sections, the inner map section, the
card deck, the 1st-player paw, the solo tokens, the cat tokens, the markers, and the score pad)
as a reference solid at its real size, arranged inside the box. It splits the space not used by
the Wispwood tray into a **lower** layer (beside the tray, for the chunky bits + folded stand)
and an **upper** layer (over the whole footprint, for the flat large bits), then places each
component into them -- the basis for the reworked organizer (the old small tray is retired).

Fungible multiples (solo tokens, cats, markers) are modelled as a single **stack** (the storage
envelope) rather than separate pieces; the four outer map sections are separate objects. The
irregular parts (outer map sections, paw, ruler/markers) use **outlines traced from photos** on
Letter paper (see ``tools/trace_parts.py``); the rest come from sizes in :mod:`config`. Nothing
here is a printed part — these are design references.

Public API
----------
``build_perimeter_map``, ``build_center_map``, ``build_cards``, ``build_paw``,
``build_solo_tokens``, ``build_cats``, ``build_markers``, ``build_scorepad``,
``build_lower_space``, ``build_upper_space``, ``build_all``.
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
    """Return the inner map section: an octagon (``BOARD_CENTER_PTP`` ptp) with scalloped edges.

    Each of the 8 sides bows inward by ``BOARD_CENTER_WAVE`` (a circular arc through the side
    midpoint pulled toward the centre), matching the wavy printed edge so an insert can hug it.

    Returns
    -------
    Part.Shape
        The center-octagon solid (bbox min at the origin).
    """
    r = cfg.BOARD_CENTER_PTP / 2.0
    s = cfg.BOARD_CENTER_WAVE
    verts = [
        Vector(
            r * math.cos(math.radians(22.5 + 45 * k)),
            r * math.sin(math.radians(22.5 + 45 * k)),
            0.0,
        )
        for k in range(8)
    ]
    edges = []
    for k in range(8):
        a, b = verts[k], verts[(k + 1) % 8]
        mid = (a + b) * 0.5
        midp = mid * ((mid.Length - s) / mid.Length)  # pull the side midpoint inward
        edges.append(Part.Arc(a, midp, b).toShape())
    face = Part.Face(Part.Wire(edges))
    return _at_origin(face.extrude(Vector(0.0, 0.0, cfg.BOARD_THICKNESS)))


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
    """Return the 6 cat tokens stored ON EDGE: 35x35 faces vertical, rowed along the thickness."""
    row = cfg.CAT_COUNT * cfg.CAT_THICKNESS  # row length (along the stacked thickness)
    return _box(0.0, 0.0, 0.0, cfg.CAT_SIZE, row, cfg.CAT_SIZE)


def build_markers():
    """Return the 4 markers (rulers/solo board) as a stack, using the photo-traced ruler outline.

    The markers are the ~214 x 35 mm number-track standees; modelled as one ruler profile
    extruded to the 4-piece stack thickness (the storage envelope).
    """
    return _profile_solid(_RULER_PROFILE, cfg.MARKER_COUNT * cfg.MARKER_THICKNESS)


def build_scorepad():
    """Return the score pad as a solid block."""
    return _box(0.0, 0.0, 0.0, cfg.SCOREPAD_W, cfg.SCOREPAD_H, cfg.SCOREPAD_THICKNESS)


def build_lower_space():
    """Return the LOWER space: the bottom layer (Z 0..tray top) beside the Wispwood tray.

    The box footprint minus the tray, up to the tray's wall top -- the chunky bits (cats on
    edge, cards, solo tokens, paw) and the folded stand live here.
    """
    r = bl.bottom_regions()["wispwood"]
    c = cfg.COMPONENT_CLEARANCE
    block = _box(0.0, 0.0, 0.0, cfg.BOX_W, cfg.BOX_L, d.WALL_TOP)
    tray = _box(r.x - c, r.y - c, -1.0, r.w + 2 * c, r.h + 2 * c, d.WALL_TOP + 2.0)
    return block.cut(tray)


def build_upper_space():
    """Return the UPPER space: the top layer (Z tray top..box top) over the whole footprint.

    The flat large bits (board sections, markers, score pad) rest here, on top of the tray and
    the lower layer.
    """
    return _box(0.0, 0.0, d.WALL_TOP, cfg.BOX_W, cfg.BOX_L, cfg.BOX_H - d.WALL_TOP)


def _placed(name, shape, x, y, z, rgb, rot=0.0):
    """Return a part tuple with ``shape`` rotated ``rot`` deg about Z, bbox min moved to (x,y,z)."""
    if rot:
        shape.rotate(Vector(0.0, 0.0, 0.0), Vector(0.0, 0.0, 1.0), rot)
    shape = _at_origin(shape)
    shape.translate(Vector(x, y, z))
    return (name, shape, rgb, True, 0)


def build_all():
    """Build the two spaces + every component arranged inside them (the small tray is retired).

    Lower layer (beside the tray): cards, paw, cats on edge, solo tokens. Upper layer (over the
    whole box): the 5 board sections (stacked), the markers, the score pad. The folded stand is
    placed separately by ``box_insert.place_stand``; these positions avoid its bay. A first-pass
    arrangement -- drag/adjust in FreeCAD.

    Returns
    -------
    list of tuple
        ``(name, shape, (r, g, b), visible, transparency)``.
    """
    uz = d.WALL_TOP + cfg.COMPONENT_CLEARANCE  # upper-layer floor
    bt = cfg.BOARD_THICKNESS
    parts = [
        ("LowerSpace", build_lower_space(), (0.55, 0.6, 0.6), True, 82),
        ("UpperSpace", build_upper_space(), (0.5, 0.6, 0.72), True, 86),
    ]
    # --- Lower layer (Z 0), clear of the stand bay (X < ~93, Y 88..202) -----------------------
    parts.append(_placed("Cards", build_cards(), 96.0, 90.0, 0.0, (0.85, 0.75, 0.45), rot=90.0))
    parts.append(_placed("PawToken", build_paw(), 96.0, 157.0, 0.0, (0.85, 0.55, 0.55)))
    parts.append(_placed("CatTokensx6", build_cats(), 10.0, 210.0, 0.0, (0.70, 0.50, 0.80)))
    parts.append(_placed("SoloTokensx8", build_solo_tokens(), 56.0, 210.0, 0.0, (0.55, 0.55, 0.85)))
    # --- Upper layer (Z = uz): board sections stacked, markers, score pad ----------------------
    for i in range(4):  # four identical outer sections, stacked
        parts.append(
            _placed(
                f"MapOuter{i + 1}",
                build_perimeter_map(),
                3.0,
                5.0,
                uz + i * bt,
                (0.45, 0.65, 0.45),
                rot=90.0,
            )
        )
    parts.append(
        _placed("MapCenter", build_center_map(), 3.0, 5.0, uz + 4 * bt, (0.30, 0.55, 0.30))
    )
    parts.append(
        _placed("Markersx4", build_markers(), 97.0, 25.0, uz, (0.50, 0.75, 0.80), rot=90.0)
    )
    parts.append(
        _placed("ScorePad", build_scorepad(), 3.0, 25.0, uz + 5 * bt + 2.0, (0.80, 0.80, 0.60))
    )
    return parts
