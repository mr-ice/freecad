"""FreeCAD reference solids for the loose box components + the leftover-space block.

Models the game components as reference solids at real size and builds the **bottom organizer**
by a subtractive method: start from a whole solid bottom box (:func:`_solid_lower_box`) and, for
each part placed at its recorded position (``offsets.txt``), **burn a fitted pocket down from the
top** (:func:`_pocket_cutter`) -- the leftover material forms the dividers. The markers + score
pad stay in the kept **top tray** (see :mod:`box_insert`); the folded stand gets its own burned
pocket. The old small tray is retired.

Fungible multiples (solo tokens, cats, markers) are modelled as a single **stack** (the storage
envelope) rather than separate pieces; the four outer map sections are separate objects. The
irregular parts (outer map sections, paw, ruler/markers) use **outlines traced from photos** on
Letter paper (see ``tools/trace_parts.py``); the rest come from sizes in :mod:`config`. Nothing
here is a printed part — these are design references.

Public API
----------
``build_perimeter_map``, ``build_center_map``, ``build_cards``, ``build_paw``,
``build_solo_tokens``, ``build_cats``, ``build_markers``, ``build_scorepad``,
``build_lower_space``, ``build_all``.
"""

import math

import box_layout as bl
import config as cfg
import derived as d
import Part
import stand as st
from FreeCAD import Vector

# Folded-stand placement in the box (from offsets.txt), shared with BoxParts.FCMacro.
STAND_OFFSET = (3.0, 110.5, 3.0)


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


def _zcyl(r, h, x, y, z):
    """Return a cylinder of radius ``r`` along ``+Z`` from ``(x, y, z)``."""
    return Part.makeCylinder(r, h, Vector(x, y, z), Vector(0.0, 0.0, 1.0))


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


def build_outer_map_stack():
    """Return the four identical outer map sections as a single stacked solid (~186 x 90 mm)."""
    return _profile_solid(_OUTER_MAP_PROFILE, 4 * cfg.BOARD_THICKNESS)


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
    edge, cards, solo tokens) and the folded stand live here. The tray's whole front band is
    cut across the FULL box width, so no thin sliver is left beside the tray.
    """
    r = bl.bottom_regions()["wispwood"]
    c = cfg.COMPONENT_CLEARANCE
    block = _box(0.0, 0.0, 0.0, cfg.BOX_W, cfg.BOX_L, d.WALL_TOP)
    cut = _box(-1.0, r.y - c, -1.0, cfg.BOX_W + 2.0, r.h + 2 * c, d.WALL_TOP + 2.0)
    block = block.cut(cut)
    # Fillet the two back vertical corners (which sit in the box's rounded interior corners).
    rr = cfg.BOX_CORNER_R
    corners = []
    for e in block.Edges:
        bb = e.BoundBox
        vertical = abs(bb.ZLength - d.WALL_TOP) < 1e-6 and bb.XLength < 0.5 and bb.YLength < 0.5
        at_back = abs(bb.YMax - cfg.BOX_L) < 0.5
        at_side = abs(bb.XMin) < 0.5 or abs(bb.XMax - cfg.BOX_W) < 0.5
        if vertical and at_back and at_side:
            corners.append(e)
    if corners:
        block = block.makeFillet(rr, corners)
    return block


def _solid_lower_box():
    """Return the whole solid bottom box (back region, box-corner rounded) to carve pockets from."""
    r = bl.bottom_regions()["wispwood"]
    c = cfg.COMPONENT_CLEARANCE
    y0 = r.y + r.h + c  # front edge of the back region (facing the Wispwood tray)
    rr = cfg.BOX_CORNER_R
    h = d.WALL_TOP
    box = _box(0.0, y0, 0.0, cfg.BOX_W, cfg.BOX_L - y0, h)
    # Round the two back outer corners to the box's interior radius (cut the sharp bit).
    for cx in (0.0, cfg.BOX_W):
        ccx = cx + rr if cx == 0.0 else cx - rr
        sq_x = 0.0 if cx == 0.0 else cx - rr
        sq = _box(sq_x, cfg.BOX_L - rr, -1.0, rr, rr, h + 2.0)
        box = box.cut(sq.cut(_zcyl(rr, h + 2.0, ccx, cfg.BOX_L - rr, -1.0)))
    return box


def _pocket_cutter(solid, top_z, clr):
    """Return a 'router-from-the-top' cutter for ``solid``: its outer perimeter up to ``top_z``.

    Takes only the OUTER boundary of the part's footprint (inner holes are filled -- a router
    cutting from the top clears them, and any inner geometry would only occlude dropping the part
    in), grows it by ``clr``, and extrudes it up through the top -- so subtracting it from the box
    leaves a clean part-shaped pocket, open at the top and bottomed where the part rests.
    """
    bb = solid.BoundBox
    zmin = bb.ZMin
    up = Vector(0.0, 0.0, top_z - zmin + 1.0)
    faces = [f for f in solid.Faces if abs(f.CenterOfMass.z - zmin) < 0.1]
    cut = None
    for f in faces:
        try:
            face = Part.Face(f.OuterWire)  # outer perimeter only (fill inner holes)
        except Exception:
            face = f
        if clr:
            try:
                face = face.makeOffset2D(clr)
            except Exception:
                pass
        try:
            prism = face.extrude(up)
        except Exception:
            continue
        cut = prism if cut is None else cut.fuse(prism)
    if cut is None:  # fallback: bounding-box prism
        cut = _box(bb.XMin, bb.YMin, zmin, bb.XLength, bb.YLength, top_z - zmin + 1.0)
    return cut


def _stand_silhouette():
    """Return the combined outer-perimeter wire of the placed shelf + base, grown by the clearance.

    Both footprints (at the stand's resting Z) are filled to their outer perimeters and fused so
    the space between the two parts is enclosed, then the outer boundary of the union is offset
    outward by ``STAND_BAY_CLEAR`` -- one clean outline the folded stand drops into from the top.
    """
    ox, oy, oz = STAND_OFFSET
    foots = []
    for name, shape, *_rest in st.build_all():
        if name not in ("StandShelf", "StandBase"):
            continue
        shape.translate(Vector(ox - st.DISPLAY_X_OFFSET, oy, oz))
        zmin = shape.BoundBox.ZMin
        for f in shape.Faces:
            if abs(f.CenterOfMass.z - zmin) < 0.1:
                try:
                    foots.append(Part.Face(f.OuterWire))  # filled footprint (outer perimeter)
                except Exception:
                    pass
    if not foots:
        return None
    region = foots[0]
    for f in foots[1:]:
        region = region.fuse(f)
    outer = max(region.Faces, key=lambda f: f.Area).OuterWire  # combined outer boundary
    try:
        return outer.makeOffset2D(cfg.STAND_BAY_CLEAR)  # grow outward for a free fit
    except Exception:
        return outer


def build_bottom_tray(components, stand_sil):
    """Return the bottom box with a fitted pocket burned down from the top for every part.

    Starts from the whole solid bottom box and subtracts each part's outer-perimeter footprint
    (extruded from its resting Z up through the top) -- the parts drop in from above and the
    leftover material forms the dividers. The stand uses its combined shelf+base silhouette
    (``stand_sil``). Also cuts a deep front finger scoop to lift the Wispwood tray out.
    """
    box = _solid_lower_box()
    for _name, shape, _rgb in components:
        try:
            box = box.cut(_pocket_cutter(shape, d.WALL_TOP, cfg.COMPONENT_CLEARANCE))
        except Exception:
            pass
    if stand_sil is not None:
        try:
            zmin = stand_sil.BoundBox.ZMin
            box = box.cut(Part.Face(stand_sil).extrude(Vector(0.0, 0.0, d.WALL_TOP - zmin + 1.0)))
        except Exception:
            pass
    r = bl.bottom_regions()["wispwood"]
    y0 = r.y + r.h + cfg.COMPONENT_CLEARANCE
    box = box.cut(_zcyl(cfg.FINGER_GROOVE_R + 4.0, d.WALL_TOP + 1.0, r.x + r.w / 2.0, y0, -0.5))
    return box


def _placed(name, shape, x, y, z, rgb, rot=0.0):
    """Return a part tuple with ``shape`` rotated ``rot`` deg about Z, bbox min moved to (x,y,z)."""
    if rot:
        shape.rotate(Vector(0.0, 0.0, 0.0), Vector(0.0, 0.0, 1.0), rot)
    shape = _at_origin(shape)
    shape.translate(Vector(x, y, z))
    return (name, shape, rgb, True, 0)


def _shape_at(shape, x, y, z, r):
    """Return ``shape`` under a FreeCAD placement: rotate ``r`` deg about Z origin, then translate.

    Reproduces the recorded manual positions in ``offsets.txt`` (placement = Z rotation about the
    origin + base translation).
    """
    if r:
        shape.rotate(Vector(0.0, 0.0, 0.0), Vector(0.0, 0.0, 1.0), r)
    shape.translate(Vector(x, y, z))
    return shape


def _shape_centered(shape, cx, cy, z):
    """Return ``shape`` with its bbox centre in XY at ``(cx, cy)`` and its bottom at ``z``."""
    bb = shape.BoundBox
    shape.translate(Vector(cx - bb.Center.x, cy - bb.Center.y, z - bb.ZMin))
    return shape


def _bottom_components():
    """Return the bottom-layer parts as ``(name, placed_solid, rgb)`` at the recorded positions."""
    return [
        (
            "MapOuterStack",
            _shape_at(build_outer_map_stack(), 101.042, 282.206, 31.600, 232.0),
            (0.45, 0.65, 0.45),
        ),
        (
            "MapCenter",
            _shape_centered(build_center_map(), 120.162, 200.262, 40.532),
            (0.30, 0.55, 0.30),
        ),
        ("Cards", _shape_at(build_cards(), 119.800, 88.500, 33.000, 0.0), (0.85, 0.75, 0.45)),
        ("PawToken", _shape_at(build_paw(), 60.200, 176.500, 29.200, 0.0), (0.85, 0.55, 0.55)),
        ("CatTokensx6", _shape_at(build_cats(), 13.300, 223.200, 5.800, 0.0), (0.70, 0.50, 0.80)),
        (
            "SoloTokensx8",
            _shape_at(build_solo_tokens(), 151.400, 216.000, 23.300, 0.0),
            (0.55, 0.55, 0.85),
        ),
    ]


def build_all():
    """Build the bottom tray + every component at the recorded manual positions (offsets.txt).

    The bottom-layer contents (outer-map stack, center, cards, paw, cats, solo tokens) are placed
    at the positions recorded after manual arrangement; the markers + score pad stay in the kept
    top tray (not recorded). Each recorded position is a FreeCAD placement (Z rotation about the
    origin + base translation); the center octagon is placed by its centre.

    Returns
    -------
    list of tuple
        ``(name, shape, (r, g, b), visible, transparency)``.
    """
    comps = _bottom_components()
    stand_sil = _stand_silhouette()
    tray = build_bottom_tray(comps, stand_sil)
    parts = [("BottomTray", tray, (0.55, 0.6, 0.6), True, 30)]
    # Show the seated parts in their burned-down pockets.
    for name, shape, rgb in comps:
        parts.append((name, shape, rgb, True, 0))
    # Show the combined shelf+base outline (grown) as a wire for review.
    if stand_sil is not None:
        parts.append(("StandSilhouette", stand_sil, (1.0, 0.0, 0.0), True, 0))

    # --- Top tray: markers + score pad in the two bays (not in offsets.txt) --------------------
    tz = cfg.SMALL_TRAY_RIM_Z + cfg.INSERT_FLOOR  # top-tray pocket floor
    bp = bl.top_regions()["board_pocket"]
    mt = bl.top_regions()["marker_trough"]
    parts.append(
        _placed("ScorePad", build_scorepad(), bp.x + 2.0, bp.y + 2.0, tz, (0.80, 0.80, 0.60))
    )
    parts.append(
        _placed(
            "Markersx4", build_markers(), mt.x + 1.0, mt.y + 1.0, tz, (0.50, 0.75, 0.80), rot=90.0
        )
    )
    return parts
