"""Geometry builders for BombBusters components, from the parameters in :mod:`config`.

Builds one shape per token/card group (wire tokens, info tokens, equipment tokens,
info markers, the blue cut disc, mission/equipment cards) plus a translucent reference
box envelope, using the FreeCAD ``Part`` workbench. Intended to be driven by
``BombBusters.FCMacro`` inside FreeCAD 1.0.2 (see the repository ``CLAUDE.md``). This
module produces a simple non-overlapping grid for visual reference only -- it does not
attempt a real insert layout.

Coordinate convention
----------------------
Each config entry names a ``"Z"`` dimension -- the dimension that stands vertical in
world space. ``Thickness`` (or ``Diameter`` for ``BlueCutDisc``) is the stacking
dimension along which ``Quantity`` copies are fused into one shape: vertical when
``Z == "Thickness"`` (cards, stacked flat like a deck), horizontal otherwise (tokens
standing on edge, in a row). Items with no ``Thickness`` (``InfoMarker`` colors) have
no fuse axis; ``Quantity`` copies are placed side by side instead.

Public API
----------
``build_wire_tokens``, ``build_equipment_tokens``, ``build_info_tokens``,
``build_info_markers``, ``build_blue_cut_disc``, ``build_cards``, ``build_box``,
``build_token_tray``, ``build_token_tray_lid``, ``build_tray_contents``,
``build_tray_access_hole``, ``build_tray_joint_cuts``, ``build_all``.
"""

import math

import config as cfg
import Part
from FreeCAD import Vector

GAP = 10.0  # gap between top-level groups, mm
PAIR_GAP = 4.0  # gap between adjacent items within a group, mm -- wide enough that
# each InfoMarker hole can take its own top fillet without meeting its neighbor's
MARKER_FILLET = 2.0  # fillet radius on InfoMarker.Yellow's vertical edges, mm

# Per-part placement overrides, applied on top of build_all()'s automatic grid.
# name -> (offset: Vector, rotation: (axis: Vector, angle_degrees) or None).
# Add an entry here to move a specific part to its final spot; anything not listed
# keeps its automatic grid position.
PLACEMENTS = {
    # Red Tokens are rotated and fit inside the WALL_THICKNESS
    "WireToken_Red": (
        Vector(
            cfg.WireToken["Height"] + cfg.WALL_THICKNESS, cfg.WALL_THICKNESS, cfg.WALL_THICKNESS
        ),
        (Vector(0, 0, 1), 90),
    ),
    # Yellow Tokens are rotated and fit inside the WALL_THICKNESS
    "WireToken_Yellow": (
        Vector(
            cfg.WireToken["Height"] + cfg.WALL_THICKNESS,
            cfg.Box["Width"]
            - cfg.WireToken["Thickness"] * cfg.WireToken["Quantity"]["Yellow"]
            - cfg.WALL_THICKNESS,
            cfg.WALL_THICKNESS,
        ),
        (Vector(0, 0, 1), 90),
    ),
    "WireToken_Blue_00": (
        Vector(
            (cfg.WireToken["Height"] + cfg.WALL_THICKNESS) * 2,
            (cfg.Box["Width"] - (cfg.WireToken["Quantity"]["Blue_00"] * cfg.WireToken["Thickness"]))
            / 2,
            cfg.WALL_THICKNESS,
        ),
        (Vector(0, 0, 1), 90),
    ),
    "WireToken_Blue_01": (
        Vector(
            (cfg.WireToken["Height"] + cfg.WALL_THICKNESS) * 3,
            (cfg.Box["Width"] - (cfg.WireToken["Quantity"]["Blue_00"] * cfg.WireToken["Thickness"]))
            / 2,
            cfg.WALL_THICKNESS,
        ),
        (Vector(0, 0, 1), 90),
    ),
    "Card_Mission": (
        Vector(
            cfg.Card["Equipment"]["Width"] + cfg.WALL_THICKNESS * 6,
            cfg.WALL_THICKNESS,
            cfg.Box["Depth"]
            - cfg.WALL_THICKNESS
            - cfg.Card["Equipment"]["Thickness"] * cfg.Card["Equipment"]["Quantity"],
        ),
        (Vector(0, 0, 1), 0),
    ),
    "Card_Equipment": (
        Vector(
            cfg.Card["Equipment"]["Width"] + cfg.WALL_THICKNESS,
            cfg.WALL_THICKNESS,
            cfg.Box["Depth"]
            - cfg.WALL_THICKNESS
            - cfg.Card["Equipment"]["Thickness"] * cfg.Card["Equipment"]["Quantity"],
        ),
        (Vector(0, 0, 1), 90),
    ),
}

# Info-token / equipment-token grid, see infogrid.md: 5 columns x 3 rows, columns
# spanning the box's Width and rows stacked along its Height, the whole block pushed
# to the box's max-X (Height) side. Row 1 and row 3 of infogrid.md are swapped from
# the diagram, so the Equipment/Yellow row sits furthest from the edge instead of
# nearest it.
#
# Columns: one InfoToken-width (+TOLERANCE) each, with a 2mm divider between columns
# and the leftover width split evenly as the two edge margins.
_GRID_COL_WIDTH = cfg.InfoToken["Width"] + cfg.TOLERANCE
_GRID_COL_DIVIDER = 2.0
_GRID_COL_PITCH = _GRID_COL_WIDTH + _GRID_COL_DIVIDER
_GRID_COL_MARGIN = (cfg.Box["Width"] - _GRID_COL_WIDTH * 5 - _GRID_COL_DIVIDER * 4) / 2


def _grid_col_y(col):
    """Return the min-Y edge of grid column `col` (0-4)."""
    return _GRID_COL_MARGIN + col * _GRID_COL_PITCH


# Rows, furthest from the box edge (row 0) to nearest (row 3):
#   0: InfoMarkers + BlueCutDisc, each rotated 90 deg so its side-by-side spread
#      runs across the row (Y, the columns) instead of into its depth (X)
#   1: numbers 11-12 + Equipment (centered) + Yellow InfoToken
#   2: numbers 6-10   3: numbers 1-5
# A fused number/equipment pair's row is its stack length (2 items + TOLERANCE,
# once); rows are 15mm apart with a 7mm margin above/below the whole block.
_GRID_ROW_HEIGHT = cfg.InfoToken["Thickness"] * 2 + cfg.TOLERANCE
_GRID_ROW_GAP = 15.0
_GRID_ROW_MARGIN = 7.0

# Row 0's own depth is the largest of its (now rotated) items' cross sections.
_marker_red = cfg.InfoMarker["Red"]
_RED_DIAMETER_EFF = _marker_red["Diameter"] + cfg.TOLERANCE
_RED_RADIUS_EFF = _RED_DIAMETER_EFF / 2
_RED_PITCH = _marker_red["Diameter"] + PAIR_GAP
_RED_SPREAD = (_marker_red["Quantity"] - 1) * _RED_PITCH + _RED_DIAMETER_EFF

_marker_yellow = cfg.InfoMarker["Yellow"]
_MARKER_YELLOW_WIDTH_EFF = _marker_yellow["Width"] + cfg.TOLERANCE
_MARKER_YELLOW_PITCH = _marker_yellow["Width"] + PAIR_GAP
_MARKER_YELLOW_SPREAD = (
    _marker_yellow["Quantity"] - 1
) * _MARKER_YELLOW_PITCH + _MARKER_YELLOW_WIDTH_EFF

_DISC_DIAMETER_EFF = cfg.BlueCutDisc["Diameter"] + cfg.TOLERANCE
_DISC_RADIUS_EFF = _DISC_DIAMETER_EFF / 2
_DISC_SPREAD = cfg.BlueCutDisc["Thickness"] * cfg.BlueCutDisc["Quantity"] + cfg.TOLERANCE

_RED_HEIGHT_EFF = _marker_red["Height"] + cfg.TOLERANCE
_MARKER_YELLOW_HEIGHT_EFF = _marker_yellow["Height"] + cfg.TOLERANCE

# Row 0's items are raised so their tops (Z) land level with the InfoToken tops,
# rather than sitting on the floor themselves.
_ROW0_TOP_Z = cfg.WALL_THICKNESS + cfg.InfoToken["Height"] + cfg.TOLERANCE - 2.0

_ROW0_HEIGHT = max(_RED_DIAMETER_EFF, _MARKER_YELLOW_WIDTH_EFF, _DISC_DIAMETER_EFF)
_ROW_HEIGHTS = [_ROW0_HEIGHT] + [_GRID_ROW_HEIGHT] * 3

_GRID_BLOCK_LENGTH = (
    sum(_ROW_HEIGHTS) + _GRID_ROW_GAP * (len(_ROW_HEIGHTS) - 1) + _GRID_ROW_MARGIN * 2
)
_GRID_BLOCK_MIN_X = cfg.Box["Height"] - cfg.WALL_THICKNESS - _GRID_BLOCK_LENGTH


def _grid_row_x(row, block_min_x=_GRID_BLOCK_MIN_X):
    """Return the min-X edge of grid row `row` (0=furthest from the block's far edge)."""
    x = block_min_x + _GRID_ROW_MARGIN
    for height in _ROW_HEIGHTS[:row]:
        x += height + _GRID_ROW_GAP
    return x


# The box's grid and the Tray_ copy now share the same block_min_x (see below), so
# row 0's position and the BlueCutDisc's Y position are the same for both -- reused
# here to build the tray's coaxial access hole (build_tray_access_hole).
_ROW0_X = _grid_row_x(0)
_ROW0_TOP = _ROW0_X + _ROW0_HEIGHT
_DISC_Y = cfg.Box["Width"] - _GRID_COL_MARGIN - _DISC_SPREAD

# The TokenTrayLid rests directly on the tallest part in the tray: the info
# tokens, the Equipment token, or row 0 (markers/disc), whichever tops out
# highest above WALL_THICKNESS.
_TALLEST_PART_TOP_Z = max(
    cfg.WALL_THICKNESS + cfg.InfoToken["Height"] + cfg.TOLERANCE,
    cfg.WALL_THICKNESS + cfg.EquipmentToken["Height"] + cfg.TOLERANCE,
    _ROW0_TOP_Z,
)

# TokenTrayLid's legs: they extend _LEG_LENGTH past the tray's own ends (X) and
# run the full height down to the floor (Z=0), so each can carry an equilateral
# triangular key, spanning the tray's full width, that slides into a matching
# slot cut into the tray's end wall (build_tray_joint_cuts). The apex, at the
# tray's mid-height (_JOINT_Z), reaches _JOINT_DEPTH into the tray from its true
# end face.
_LEG_LENGTH = 2 * cfg.WALL_THICKNESS
_JOINT_DEPTH = cfg.WALL_THICKNESS
_JOINT_Z = cfg.TokenTray["Depth"] / 2
# The key's flush face is pushed this far past the tray's true end face, into
# the leg -- cutting a tool whose face sits exactly in the tray's own boundary
# plane produced an open (non-solid) result, so the tool needs genuine 3D
# overlap on both sides of that boundary. _JOINT_TOTAL_DEPTH (flush face to
# apex) grows by the same amount, so the apex position is unchanged; deriving
# _JOINT_HEIGHT from that total (rather than from _JOINT_DEPTH alone) keeps the
# triangle equilateral (side = altitude * 2 / sqrt(3)) despite the extra reach.
_JOINT_OVERLAP = 0.4
_JOINT_TOTAL_DEPTH = _JOINT_DEPTH + _JOINT_OVERLAP
_JOINT_HEIGHT = _JOINT_TOTAL_DEPTH * 2 / math.sqrt(3)

# A thin vertical access hole through the BlueCutDisc pocket, so a rod can reach
# in from above the tray to eject the disc stack.
_ACCESS_DIAMETER = cfg.BlueCutDisc["Diameter"] * 0.7
_ACCESS_RADIUS = _ACCESS_DIAMETER / 2

# Master switch: off while debugging the joint cuts, to see whether the cuts
# alone (with no fillet involved) produce a valid solid.
_ENABLE_TRAY_FILLETS = True
_ENABLE_OUTER_EDGE_FILLETS = True

# TokenTray fillets: its 12 outer edges (top, bottom, and the 4 vertical corners),
# then the rim of every pocket cut into its top face, rolled out one part category
# at a time -- flip these on as each is reviewed (see _tray_tool_category).
_TRAY_OUTER_FILLET = 2.0
_TRAY_TOP_FILLET = 1.5

# Smaller than _TRAY_TOP_FILLET: even spread out (see PAIR_GAP), adjacent marker
# holes are only ~3.25mm apart, too tight for the full 1.5mm on each side.
_MARKER_TOP_FILLET = 1.0
_ENABLE_DISC_TOP_FILLET = True
_ENABLE_MARKER_TOP_FILLET = True
_ENABLE_TOKEN_TOP_FILLET = True

# category -> (enabled, fillet radius). Info tokens only fillet their Y-direction
# edges (see _fillet_tray_top_rims) -- the X-direction ones facing an adjacent column
# across the 2mm _GRID_COL_DIVIDER are left sharp rather than risk the conflict.
_TOP_FILLET_CATEGORIES = (
    ("disc", _ENABLE_DISC_TOP_FILLET, _TRAY_TOP_FILLET),
    ("marker", _ENABLE_MARKER_TOP_FILLET, _MARKER_TOP_FILLET),
    ("token", _ENABLE_TOKEN_TOP_FILLET, _TRAY_TOP_FILLET),
)


def _populate_info_grid_placements(prefix, block_min_x):
    """Add PLACEMENTS entries for one copy of the info/equipment/marker/disc grid.

    Parameters
    ----------
    prefix : str
        Prepended to each part's base name, e.g. ``"Tray_"`` for the copy that
        sits on the TokenTray instead of in the box.
    block_min_x : float
        Min-X edge of this copy's whole grid block, in world coordinates.
    """

    def row_x(row):
        return _grid_row_x(row, block_min_x)

    # Row 1: numbers 11-12 (columns 0-1), Equipment (columns 2-3, centered), Yellow
    # InfoToken (column 4).
    for i, num in enumerate((11, 12)):
        PLACEMENTS[f"{prefix}InfoToken_Number_Pair_{num - 1:02d}"] = (
            Vector(row_x(1), _grid_col_y(i), cfg.WALL_THICKNESS),
            None,
        )

    equipment_col_span = _GRID_COL_WIDTH * 2 + _GRID_COL_DIVIDER
    equipment_width = cfg.EquipmentToken["Width"] + cfg.TOLERANCE
    PLACEMENTS[f"{prefix}EquipmentToken_Pair"] = (
        Vector(
            row_x(1),
            _grid_col_y(2) + (equipment_col_span - equipment_width) / 2,
            cfg.WALL_THICKNESS,
        ),
        None,
    )

    PLACEMENTS[f"{prefix}InfoToken_Yellow_Pair"] = (
        Vector(row_x(1), _grid_col_y(4), cfg.WALL_THICKNESS),
        None,
    )

    # Row 2: numbers 6-10, columns 0-4.
    # Row 3 (nearest the edge): numbers 1-5, columns 0-4.
    for num in range(1, 11):
        r, col = divmod(num - 1, 5)
        PLACEMENTS[f"{prefix}InfoToken_Number_Pair_{num - 1:02d}"] = (
            Vector(row_x(3 - r), _grid_col_y(col), cfg.WALL_THICKNESS),
            None,
        )

    # Row 0 (furthest from the edge): InfoMarker Yellow and Red placed alongside
    # each other -- different X lanes within the row's depth, not end to end along
    # Y. Yellow sits at the row's near (bottom) edge in X, starting at the row's
    # left margin in Y; Red sits at the row's far (top) edge in X (level with the
    # discs), its Y span centered on Yellow's since Yellow's is wider. Both rotated
    # 90 deg about Z so their side-by-side spread runs along Y instead of into the
    # row's depth (X). BlueCutDisc is pushed to the row's far end in Y, well clear
    # of the markers for room to reach in.
    row0_x = row_x(0)
    row0_top = row0_x + _ROW0_HEIGHT

    yellow_y = _GRID_COL_MARGIN
    PLACEMENTS[f"{prefix}InfoMarker_Yellow"] = (
        Vector(
            row0_x + _MARKER_YELLOW_WIDTH_EFF, yellow_y, _ROW0_TOP_Z - _MARKER_YELLOW_HEIGHT_EFF
        ),
        (Vector(0, 0, 1), 90),
    )

    red_y = yellow_y + (_MARKER_YELLOW_SPREAD - _RED_SPREAD) / 2
    PLACEMENTS[f"{prefix}InfoMarker_Red"] = (
        Vector(row0_top - _RED_RADIUS_EFF, red_y + _RED_RADIUS_EFF, _ROW0_TOP_Z - _RED_HEIGHT_EFF),
        (Vector(0, 0, 1), 90),
    )

    disc_y = cfg.Box["Width"] - _GRID_COL_MARGIN - _DISC_SPREAD
    PLACEMENTS[f"{prefix}BlueCutDisc_Stack"] = (
        Vector(row0_top - _DISC_RADIUS_EFF, disc_y, _ROW0_TOP_Z - _DISC_RADIUS_EFF),
        (Vector(0, 0, 1), 90),
    )


_populate_info_grid_placements("", _GRID_BLOCK_MIN_X)
# The Tray_ copy is a set of cutting tools for build_all()'s TokenTray pocket cut
# (see _cut_tray_contents), so it's placed at the exact same coordinates as the
# box's own grid -- which line up with the tray once its +X edge is aligned to
# the box's, below.
_populate_info_grid_placements("Tray_", _GRID_BLOCK_MIN_X)

# TokenTray's +X edge is aligned with the box's +X edge, so it sits directly under
# the box's own info-token/equipment/marker/disc grid; its own bottom is at Z=0
# (not raised onto WALL_THICKNESS like the box parts).
PLACEMENTS["TokenTray"] = (Vector(cfg.Box["Height"] - cfg.TokenTray["Height"], 0, 0), None)

# TokenTrayLid is built directly in world coordinates (see build_token_tray_lid),
# since its legs and joint keys need to line up with the tray's own world
# position -- no PLACEMENTS entry needed.


def place(shape, offset=None, rotation=None):
    """Return a positioned copy of `shape`; `shape` itself is left untouched.

    `Part.Shape.translate`/`.rotate` mutate the shape in place and return `None` --
    this wraps them so placement reads as an expression instead.

    Parameters
    ----------
    shape : Part.Shape
        Shape to reposition.
    offset : FreeCAD.Vector, optional
        Translation to apply, in mm, after any rotation. Defaults to none.
    rotation : tuple of (FreeCAD.Vector, float), optional
        ``(axis, angle_degrees)`` rotated about the shape's local origin, applied
        before the offset. Defaults to none.

    Returns
    -------
    Part.Shape
        A new, positioned shape.
    """
    moved = shape.copy()
    if rotation is not None:
        axis, angle = rotation
        moved.rotate(Vector(0, 0, 0), axis, angle)
    if offset is not None:
        moved.translate(offset)
    return moved


def make_box_stack(height, width, thickness, quantity, z_dim):
    """Build one fused box representing `quantity` items stacked along Thickness.

    Parameters
    ----------
    height, width, thickness : float
        Named dimensions of a single item, in mm.
    quantity : int
        Number of items fused into the stack.
    z_dim : str
        Which of ``"Height"``, ``"Width"``, ``"Thickness"`` is vertical (world Z).

    Returns
    -------
    Part.Shape
        The fused stack, with its own min corner at the origin. Every dimension is
        grown by ``config.TOLERANCE`` for clearance as a hole cut for the physical
        part; the stacking dimension only gets it once, not once per item.
    """
    stack_length = thickness * quantity + cfg.TOLERANCE
    height += cfg.TOLERANCE
    width += cfg.TOLERANCE
    if z_dim == "Thickness":
        return Part.makeBox(height, width, stack_length)
    if z_dim == "Height":
        return Part.makeBox(stack_length, width, height)
    if z_dim == "Width":
        return Part.makeBox(stack_length, height, width)
    raise ValueError(f"unsupported z_dim: {z_dim!r}")


def make_cylinder_stack(diameter, axial_length, quantity, z_dim):
    """Build one fused cylinder representing `quantity` items stacked along its axis.

    Parameters
    ----------
    diameter : float
        Item diameter, in mm.
    axial_length : float
        Per-item length along the stacking axis (``Thickness`` for ``BlueCutDisc``,
        or the item's own axial dimension for a single unstacked cylinder), in mm.
    quantity : int
        Number of items fused into the stack.
    z_dim : str
        ``"Diameter"`` puts the axis horizontal (the circular cross-section spans Z);
        anything else puts the axis vertical along Z.

    Returns
    -------
    Part.Shape
        Cylinder of radius ``(diameter + config.TOLERANCE) / 2`` and length
        ``axial_length * quantity + config.TOLERANCE`` -- the stacking dimension
        (length) only gets the tolerance once, not once per item.
    """
    radius = (diameter + cfg.TOLERANCE) / 2
    length = axial_length * quantity + cfg.TOLERANCE
    direction = Vector(1, 0, 0) if z_dim == "Diameter" else Vector(0, 0, 1)
    return Part.makeCylinder(radius, length, Vector(0, 0, 0), direction)


def build_wire_tokens():
    """Build one fused stack per WireToken color key.

    Blue is split into two to fit based on keys Blue_00 an Blue_01

    Returns
    -------
    list of (str, Part.Shape)
        ``[("WireToken_Red", shape), ("WireToken_Yellow", shape),
        ("WireToken_Blue_00", shape), ..., ("WireToken_Blue_05", shape)]``
    """
    wt = cfg.WireToken
    height, width, thickness, z = wt["Height"], wt["Width"], wt["Thickness"], wt["Z"]
    result = []
    for color, qty in wt["Quantity"].items():
        result.append((f"WireToken_{color}", make_box_stack(height, width, thickness, qty, z)))
    return result


def build_equipment_tokens():
    """Build the fused pair of EquipmentTokens.

    Returns
    -------
    list of (str, Part.Shape)
        ``[("EquipmentToken_Pair", shape)]``
    """
    et = cfg.EquipmentToken
    shape = make_box_stack(et["Height"], et["Width"], et["Thickness"], et["Quantity"], et["Z"])
    return [("EquipmentToken_Pair", shape)]


def build_info_tokens():
    """Build the Yellow InfoToken pair and the twelve Number InfoToken pairs.

    Returns
    -------
    list of (str, Part.Shape)
        ``[("InfoToken_Yellow_Pair", shape), ("InfoToken_Number_Pair_00", shape), ...]``
        -- the Yellow pair first, so callers can keep it adjacent to the equipment pair.
    """
    it = cfg.InfoToken
    height, width, thickness, z = it["Height"], it["Width"], it["Thickness"], it["Z"]
    result = [
        (
            "InfoToken_Yellow_Pair",
            make_box_stack(height, width, thickness, it["Quantity"]["Yellow"], z),
        )
    ]
    pair_count = it["Quantity"]["Number"] // 2
    for i in range(pair_count):
        result.append(
            (f"InfoToken_Number_Pair_{i:02d}", make_box_stack(height, width, thickness, 2, z))
        )
    return result


def make_side_by_side(build_one, quantity, pitch):
    """Fuse `quantity` copies of a shape, offset by `pitch` along X.

    Parameters
    ----------
    build_one : callable
        Zero-argument callable returning a fresh shape for one item.
    quantity : int
        Number of copies to place.
    pitch : float
        Center-to-center offset between copies, in mm.

    Returns
    -------
    Part.Shape
        Fused compound of all copies.
    """
    shapes = []
    for i in range(quantity):
        shape = build_one()
        shape.translate(Vector(pitch * i, 0, 0))
        shapes.append(shape)
    result = shapes[0]
    for shape in shapes[1:]:
        result = result.fuse(shape)
    return result


def build_info_markers():
    """Build the InfoMarker Red cylinders and Yellow filleted square rods.

    Each color's `Quantity` markers stand side by side along X (not stacked).

    Returns
    -------
    list of (str, Part.Shape)
        ``[("InfoMarker_Red", shape), ("InfoMarker_Yellow", shape)]``
    """
    im = cfg.InfoMarker
    z = im["Z"]

    red = im["Red"]
    red_shape = make_side_by_side(
        lambda: make_cylinder_stack(red["Diameter"], red["Height"], 1, z),
        red["Quantity"],
        red["Diameter"] + PAIR_GAP,
    )

    yellow = im["Yellow"]

    def build_yellow_one():
        width = yellow["Width"] + cfg.TOLERANCE
        box = Part.makeBox(width, width, yellow["Height"] + cfg.TOLERANCE)
        vertical_edges = [
            e
            for e in box.Edges
            if abs(e.Vertexes[0].X - e.Vertexes[1].X) < 1e-6
            and abs(e.Vertexes[0].Y - e.Vertexes[1].Y) < 1e-6
        ]
        return box.makeFillet(MARKER_FILLET, vertical_edges)

    yellow_shape = make_side_by_side(
        build_yellow_one, yellow["Quantity"], yellow["Width"] + PAIR_GAP
    )

    return [("InfoMarker_Red", red_shape), ("InfoMarker_Yellow", yellow_shape)]


def build_blue_cut_disc():
    """Build the single fused BlueCutDisc stack.

    Returns
    -------
    list of (str, Part.Shape)
        ``[("BlueCutDisc_Stack", shape)]``
    """
    bcd = cfg.BlueCutDisc
    shape = make_cylinder_stack(bcd["Diameter"], bcd["Thickness"], bcd["Quantity"], bcd["Z"])
    return [("BlueCutDisc_Stack", shape)]


def build_cards():
    """Build the Mission and Equipment card stacks.

    Returns
    -------
    list of (str, Part.Shape)
        ``[("Card_Mission", shape), ("Card_Equipment", shape)]``
    """
    card = cfg.Card
    z = card["Z"]
    return [
        (
            f"Card_{key}",
            make_box_stack(
                card[key]["Height"],
                card[key]["Width"],
                card[key]["Thickness"],
                card[key]["Quantity"],
                z,
            ),
        )
        for key in ("Mission", "Equipment")
    ]


def build_box():
    """Build the config.Box envelope as a reference volume.

    Returns
    -------
    Part.Shape
        Box sized ``Height x Width x Depth``, ``Depth`` vertical.
    """
    box = cfg.Box
    return Part.makeBox(box["Height"], box["Width"], box["Depth"])


def build_token_tray():
    """Build the config.TokenTray envelope as a plain box -- no clearance tolerance.

    Returns
    -------
    list of (str, Part.Shape)
        ``[("TokenTray", shape)]``
    """
    tray = cfg.TokenTray
    return [("TokenTray", Part.makeBox(tray["Height"], tray["Width"], tray["Depth"]))]


def _triangle_prism(x_start, depth, z_center, height):
    """Build an equilateral-triangle prism, spanning the tray's full width (Y).

    The cross-section (in the X-Z plane) has one side flush with the leg's own
    vertical face (X=x_start, of length `height`, centered on `z_center`); the
    apex -- the key's actual working point -- sits at `z_center` too, protruding
    `depth` away from that face.

    Parameters
    ----------
    x_start : float
        X coordinate of the leg's face, in world coordinates -- where the
        triangle's flush side sits.
    depth : float
        Distance from the flush side to the apex, along X; negative points
        toward -X. For an equilateral triangle this is `height` * sqrt(3) / 2.
    z_center : float
        Z coordinate of both the flush side's midpoint and the apex.
    height : float
        Length of the side flush with the leg's face.

    Returns
    -------
    Part.Shape
        The prism, spanning Y from 0 to ``config.TokenTray["Width"]``.
    """
    p1 = Vector(x_start, 0, z_center - height / 2)
    p2 = Vector(x_start, 0, z_center + height / 2)
    p3 = Vector(x_start + depth, 0, z_center)
    face = Part.Face(Part.makePolygon([p1, p2, p3, p1]))
    return face.extrude(Vector(0, cfg.TokenTray["Width"], 0))


def _lid_joint_prisms():
    """Build the two equilateral-triangle keys joining TokenTrayLid's legs to TokenTray.

    One per end, at the tray's own end faces, spanning its full width (Y),
    flush side (length _JOINT_HEIGHT) against the leg, apex at the tray's
    mid-height (_JOINT_Z) protruding _JOINT_DEPTH into the tray. The flush face
    is pushed _JOINT_OVERLAP past the tray's true end face, into the leg, so
    both the fuse onto the lid and the cut into the tray have genuine 3D
    overlap rather than a coincident face -- the apex stays put, so the key's
    reach into the tray is unaffected. Fused onto the lid's legs (see
    build_token_tray_lid) and cut into the tray's end walls (see
    build_tray_joint_cuts) at the exact same position, so they slide together
    with no clearance.

    Returns
    -------
    tuple of (Part.Shape, Part.Shape)
        ``(left, right)``, pointing +X and -X into the tray respectively.
    """
    x_min = cfg.Box["Height"] - cfg.TokenTray["Height"] - cfg.TOLERANCE
    x_max = cfg.Box["Height"]
    left = _triangle_prism(x_min - _JOINT_OVERLAP, _JOINT_TOTAL_DEPTH, _JOINT_Z, _JOINT_HEIGHT)
    right = _triangle_prism(x_max + _JOINT_OVERLAP, -_JOINT_TOTAL_DEPTH, _JOINT_Z, _JOINT_HEIGHT)
    return left, right


def build_token_tray_lid():
    """Build the TokenTray's lid: a slab on legs that key into the tray.

    A WALL_THICKNESS-thick slab, no clearance tolerance, sharing the tray's
    Height x Width footprint, resting on the tallest part in the tray
    (_TALLEST_PART_TOP_Z). At each end, a leg extends _LEG_LENGTH past the
    tray and drops the full height down to the floor (Z=0), carrying a
    triangular key (see _lid_joint_prisms) that slides into a matching slot
    in the tray's end wall.

    Returns
    -------
    list of (str, Part.Shape)
        ``[("TokenTrayLid", shape)]``, already in world coordinates.
    """
    tray = cfg.TokenTray
    x_min = cfg.Box["Height"] - cfg.TokenTray["Height"] - cfg.TOLERANCE
    x_max = cfg.Box["Height"]
    lid_top = _TALLEST_PART_TOP_Z + cfg.WALL_THICKNESS

    slab = Part.makeBox(
        tray["Height"] + cfg.TOLERANCE,
        tray["Width"],
        cfg.WALL_THICKNESS,
        Vector(x_min, 0, _TALLEST_PART_TOP_Z),
    )
    left_leg = Part.makeBox(_LEG_LENGTH, tray["Width"], lid_top, Vector(x_min - _LEG_LENGTH, 0, 0))
    right_leg = Part.makeBox(_LEG_LENGTH, tray["Width"], lid_top, Vector(x_max, 0, 0))
    left_key, right_key = _lid_joint_prisms()

    shape = slab.fuse(left_leg).fuse(right_leg).fuse(left_key).fuse(right_key)
    return _fillet_tray_outer_edges([("TokenTrayLid", shape)])


def build_tray_joint_cuts():
    """Build the two triangular slots cut into TokenTray's end walls.

    Same shape and position as the lid's leg keys (see _lid_joint_prisms),
    named like the other Tray_ cutting tools so build_all()'s
    _cut_tray_contents subtracts them from TokenTray -- but listed in
    _CUT_TARGETS as excluded from TokenTrayLid, which gets this shape fused on
    as a protrusion instead of cut.

    Returns
    -------
    list of (str, Part.Shape)
        ``[("Tray_JointLeft", shape), ("Tray_JointRight", shape)]``
    """
    left, right = _lid_joint_prisms()
    return [("Tray_JointLeft", left), ("Tray_JointRight", right)]


def build_tray_contents():
    """Build a second copy of every info/equipment/marker/disc part, for the tray.

    Each part is renamed ``Tray_<name>`` so :func:`build_all` can place it on the
    TokenTray, in the same orientation as its counterpart in the box (see
    :func:`_populate_info_grid_placements`).

    Returns
    -------
    list of (str, Part.Shape)
        A fresh copy of every part built by :func:`build_info_tokens`,
        :func:`build_equipment_tokens`, :func:`build_info_markers`, and
        :func:`build_blue_cut_disc`, renamed with a ``Tray_`` prefix.
    """
    parts = (
        build_info_tokens()
        + build_equipment_tokens()
        + build_info_markers()
        + build_blue_cut_disc()
    )
    return [(f"Tray_{name}", shape) for name, shape in parts]


def build_tray_access_hole():
    """Build the access hole through the TokenTray's BlueCutDisc pocket.

    A cylinder (``_ACCESS_DIAMETER``, 0.7x the BlueCutDisc diameter), 2x the
    BlueCutDisc stack's own height (thickness x quantity, plus tolerance) long,
    running horizontally along Y -- parallel to the disc stack itself -- but
    raised so its central axis sits exactly on the tray's top surface: that top
    face passes straight through the cylinder's center, letting half poke out
    above the tray while the rest stays embedded, guaranteeing a clean cut
    regardless of exact tray thickness. Not coaxial with the BlueCutDisc stack
    (different Z), even though it runs parallel to it. Capped with a sphere at
    its near (-Y) end for a smooth, print-friendly transition into the (much
    wider) disc pocket instead of a flat step.

    Returns
    -------
    list of (str, Part.Shape)
        ``[("Tray_AccessHole", shape)]`` -- built directly in world coordinates
        (no separate PLACEMENTS entry) and named like the other ``Tray_`` cutting
        tools, so BombBusters.FCMacro hides it once the pocket cut is made.
    """
    length = 2 * _DISC_SPREAD
    x = _ROW0_TOP - _DISC_RADIUS_EFF
    y_start = _DISC_Y - _DISC_RADIUS_EFF / 2
    z = cfg.TokenTray["Depth"]

    cylinder = Part.makeCylinder(_ACCESS_RADIUS, length, Vector(x, y_start, z), Vector(0, 1, 0))
    cap = Part.makeSphere(_ACCESS_RADIUS, Vector(x, y_start, z))
    return [("Tray_AccessHole", cylinder.fuse(cap))]


def _pack_row(shapes, gap):
    """Translate a list of shapes into a left-to-right row with a fixed gap.

    Parameters
    ----------
    shapes : list of Part.Shape
        Shapes to place, assumed already at their own origin.
    gap : float
        Gap between adjacent shapes, in mm.

    Returns
    -------
    tuple of (list of Part.Shape, float)
        The translated shapes (copies), and the total row width.
    """
    placed = []
    cursor = 0.0
    for shape in shapes:
        moved = shape.copy()
        moved.translate(Vector(cursor, 0, 0))
        placed.append(moved)
        cursor += shape.BoundBox.XLength + gap
    return placed, (cursor - gap if placed else 0.0)


def build_all():
    """Lay out one of every component group, left to right, for scale reference.

    Groups: wire tokens, the equipment pair with the info-token pairs right next to
    it, info markers, the blue cut disc stack, the card stacks, the TokenTray, and
    a second copy of the info/equipment/marker/disc parts placed on that tray.
    Placement is a simple non-overlapping grid, not a real layout -- combine with
    :func:`build_box` to check fit.

    Returns
    -------
    list of (str, Part.Shape)
        Every named shape, translated into its grid position.
    """
    groups = [
        build_wire_tokens(),
        build_equipment_tokens() + build_info_tokens(),
        build_info_markers(),
        build_blue_cut_disc(),
        build_cards(),
        build_token_tray(),
        build_token_tray_lid(),
        build_tray_contents(),
        build_tray_access_hole(),
        build_tray_joint_cuts(),
    ]

    result = []
    for named_shapes in groups:
        for name, shape in named_shapes:
            offset, rotation = PLACEMENTS.get(name, (None, None))
            if offset is not None or rotation is not None:
                shape = place(shape, offset, rotation)
            result.append((name, shape))

    return _fillet_tray_top_rims(_cut_tray_contents(_fillet_tray_outer_edges(result)))


# Which Tray_-prefixed cutting tools to skip, per target part. TokenTrayLid
# skips the access hole -- it's meant to poke out through the tray's own top,
# not the lid sitting above it.
_CUT_TARGETS = {
    "TokenTray": frozenset(),
    "TokenTrayLid": frozenset({"Tray_AccessHole", "Tray_JointLeft", "Tray_JointRight"}),
}


def _cut_tray_contents(named_shapes):
    """Carve a pocket for every Tray_-prefixed part out of each :data:`_CUT_TARGETS` entry.

    The Tray_* parts are cutting tools, not visible geometry: BombBusters.FCMacro
    hides them once this cut is made.

    Parameters
    ----------
    named_shapes : list of (str, Part.Shape)
        Every part from :func:`build_all`, already placed in world coordinates.

    Returns
    -------
    list of (str, Part.Shape)
        `named_shapes` with each target in :data:`_CUT_TARGETS` replaced by
        itself minus every ``Tray_*`` tool not excluded for that target;
        unchanged if there are no ``Tray_*`` tools.
    """
    shapes_by_name = dict(named_shapes)
    tools = {name: shape for name, shape in named_shapes if name.startswith("Tray_")}
    if not tools:
        return named_shapes

    cut_shapes = {}
    for target, excluded in _CUT_TARGETS.items():
        base = shapes_by_name.get(target)
        if base is None:
            continue
        cut = base
        for tool_name, tool_shape in tools.items():
            if tool_name not in excluded:
                cut = cut.cut(tool_shape)
        cut_shapes[target] = cut

    return [(name, cut_shapes.get(name, shape)) for name, shape in named_shapes]


def _near(value, target, tol):
    """Return whether `value` is within `tol` of `target`."""
    return abs(value - target) < tol


def _box_corner_edges(shape, x_min, x_max, y_min, y_max, z_min, z_max, tol=1e-6):
    """Return `shape`'s edges running along one of the given box's 12 edge lines.

    A box edge line fixes two of the three axes at boundary values and lets the
    third vary. This matches full corner-to-corner edges as well as any
    fragment of one -- e.g. the piece left when a cut splits an edge partway
    along its length (an access hole exiting through a wall, a joint slot at a
    corner, ...), which a stricter "both ends are a true 3D corner" check would
    miss.

    Parameters
    ----------
    shape : Part.Shape
        Shape to search.
    x_min, x_max, y_min, y_max, z_min, z_max : float
        The box's extent, in world coordinates.
    tol : float, optional
        Coordinate-matching tolerance, in mm.

    Returns
    -------
    list of Part.Edge
        Every straight edge (or edge fragment) lying on one of the box's 12
        edge lines. Curved edges are excluded even when their endpoints land
        on a corner -- e.g. a fillet's rounded arc, whose two ends sit at
        adjacent corners but which doesn't itself run along the edge line.
    """
    axis_bounds = {"x": (x_min, x_max), "y": (y_min, y_max), "z": (z_min, z_max)}
    axis_pairs = (("x", "y"), ("x", "z"), ("y", "z"))

    def on_a_shared_edge_line(v0, v1):
        return any(
            _near(getattr(v0, a1), b1, tol)
            and _near(getattr(v1, a1), b1, tol)
            and _near(getattr(v0, a2), b2, tol)
            and _near(getattr(v1, a2), b2, tol)
            for a1, a2 in axis_pairs
            for b1 in axis_bounds[a1]
            for b2 in axis_bounds[a2]
        )

    def is_straight(edge):
        p0, p1 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
        return _near(edge.Length, (p1 - p0).Length, tol)

    return [
        edge
        for edge in shape.Edges
        if len(edge.Vertexes) == 2
        and is_straight(edge)
        and on_a_shared_edge_line(edge.Vertexes[0].Point, edge.Vertexes[1].Point)
    ]


def _fillet_edges_best_effort(shape, radius, edges):
    """Fillet `edges` on `shape` at `radius`, skipping any that can't be done.

    OCC's fillet can fail outright for the whole batch when two of the requested
    edges are too close together for the given radius -- e.g. facing walls of two
    pockets separated by less than 2x the radius (adjacent info-token columns are
    only ``_GRID_COL_DIVIDER`` mm apart), or an edge tangent to another part's own
    pre-existing fillet (the Yellow InfoMarker's vertical edges are already
    rounded at ``MARKER_FILLET`` when built). Rather than losing every fillet in
    the batch, retry one edge at a time and leave whichever individually still
    fail unfilleted.

    Parameters
    ----------
    shape : Part.Shape
        Shape to fillet.
    radius : float
        Fillet radius, in mm.
    edges : list of Part.Edge
        Candidate edges, from `shape`.

    Returns
    -------
    Part.Shape
        `shape` with every edge that could be filleted, filleted; `shape`
        unchanged if `edges` is empty.
    """
    if not edges:
        return shape

    try:
        return shape.makeFillet(radius, edges)
    except Part.OCCError:
        pass

    for target in [edge.CenterOfMass for edge in edges]:
        # Edges recomputed fresh each pass, since a prior fillet invalidates the
        # old references -- find this edge's current counterpart by position.
        matches = [e for e in shape.Edges if (e.CenterOfMass - target).Length < 1e-6]
        if not matches:
            continue
        try:
            shape = shape.makeFillet(radius, matches)
        except Part.OCCError:
            continue
    return shape


def _tray_tool_category(name):
    """Return which top-fillet toggle governs the Tray_-prefixed tool `name`.

    Groups the pocket-cutting tools into the three-part rollout: cut discs (plus
    their coaxial access hole) first, then info markers, then info tokens (which
    also covers the Equipment token, sharing its row).

    Parameters
    ----------
    name : str
        A part name from :func:`build_all`, e.g. ``"Tray_BlueCutDisc_Stack"``.

    Returns
    -------
    str or None
        ``"disc"``, ``"marker"``, or ``"token"``; ``None`` if `name` isn't a
        ``Tray_``-prefixed pocket/cut tool.
    """
    if not name.startswith("Tray_"):
        return None
    base = name[len("Tray_") :]
    if base in ("BlueCutDisc_Stack", "AccessHole"):
        return "disc"
    if base.startswith("InfoMarker_"):
        return "marker"
    if base == "EquipmentToken_Pair" or base.startswith("InfoToken_"):
        return "token"
    return None


# Every piece that gets the tray's outer fillet plus (where cut) its pockets'
# top-face fillet -- currently the tray itself and its lid.
_FILLET_TARGETS = ("TokenTray", "TokenTrayLid")


def _fillet_tray_outer_edges(named_shapes):
    """Round each :data:`_FILLET_TARGETS` entry's 12 outer box edges.

    Run before :func:`_cut_tray_contents`, on each piece's plain, uncut box --
    so there's no pocket, access hole, or joint slot anywhere near an outer
    edge yet to thin out the material a fillet needs.

    Parameters
    ----------
    named_shapes : list of (str, Part.Shape)
        Every part from :func:`build_all`, not yet cut.

    Returns
    -------
    list of (str, Part.Shape)
        `named_shapes` with each target's 12 outer edges (top, bottom, and
        vertical) filleted at ``_TRAY_OUTER_FILLET``. A target is left
        unchanged if it isn't present in `named_shapes`, or if
        ``_ENABLE_TRAY_FILLETS``/``_ENABLE_OUTER_EDGE_FILLETS`` is off.
    """
    if not _ENABLE_TRAY_FILLETS or not _ENABLE_OUTER_EDGE_FILLETS:
        return named_shapes

    shapes_by_name = dict(named_shapes)

    filleted = {}
    for target in _FILLET_TARGETS:
        piece = shapes_by_name.get(target)
        if piece is None:
            continue

        # Each piece's own bounding box, not a shared one: TokenTrayLid's legs
        # extend _LEG_LENGTH past TokenTray's X range, so its true outer corners
        # sit further out than the tray's.
        x_min = piece.BoundBox.XMin
        x_max = piece.BoundBox.XMax
        y_min = piece.BoundBox.YMin
        y_max = piece.BoundBox.YMax
        z_min = piece.BoundBox.ZMin
        z_max = piece.BoundBox.ZMax

        outer_edges = _box_corner_edges(piece, x_min, x_max, y_min, y_max, z_min, z_max)
        filleted[target] = _fillet_edges_best_effort(piece, _TRAY_OUTER_FILLET, outer_edges)

    return [(name, filleted.get(name, shape)) for name, shape in named_shapes]


def _fillet_tray_top_rims(named_shapes):
    """Round the top-face rim of every pocket cut into a :data:`_FILLET_TARGETS` entry.

    Parameters
    ----------
    named_shapes : list of (str, Part.Shape)
        Every part from :func:`build_all`, already cut (see
        :func:`_cut_tray_contents`) and outer-edge filleted (see
        :func:`_fillet_tray_outer_edges`).

    Returns
    -------
    list of (str, Part.Shape)
        `named_shapes` with the top-face rim of every pocket whose category is
        enabled (see :data:`_TOP_FILLET_CATEGORIES` and
        :func:`_tray_tool_category`) filleted at that category's own radius. A
        target is left unchanged if it isn't present in `named_shapes`, or if
        ``_ENABLE_TRAY_FILLETS`` is off.
    """
    if not _ENABLE_TRAY_FILLETS:
        return named_shapes

    shapes_by_name = dict(named_shapes)

    filleted = {}
    for target in _FILLET_TARGETS:
        piece = shapes_by_name.get(target)
        if piece is None:
            continue

        z_max = piece.BoundBox.ZMax

        for category, enabled, radius in _TOP_FILLET_CATEGORIES:
            if not enabled:
                continue

            tool_boxes = [
                shape.BoundBox
                for name, shape in named_shapes
                if _tray_tool_category(name) == category
            ]

            def in_a_tool(edge, tool_boxes=tool_boxes):
                com = edge.CenterOfMass
                return any(
                    box.XMin - 1e-3 <= com.x <= box.XMax + 1e-3
                    and box.YMin - 1e-3 <= com.y <= box.YMax + 1e-3
                    for box in tool_boxes
                )

            # No vertex-count filter here (unlike _box_corner_edges): a round
            # pocket's top rim is a single closed-loop edge (1 vertex, not 2),
            # and that's a perfectly fillet-able edge -- it must stay eligible.
            top_edges = [
                edge
                for edge in piece.Edges
                if all(_near(v.Point.z, z_max, 1e-6) for v in edge.Vertexes) and in_a_tool(edge)
            ]

            if category == "token":
                # Adjacent info-token columns are only _GRID_COL_DIVIDER mm
                # apart, and the edges facing each other across that gap run in
                # the X direction (constant Y). Edges running in the Y
                # direction (constant X) only ever face the next row,
                # _GRID_ROW_GAP mm away, so they're always safe.
                top_edges = [
                    edge
                    for edge in top_edges
                    if _near(edge.Vertexes[0].Point.x, edge.Vertexes[-1].Point.x, 1e-6)
                ]

            piece = _fillet_edges_best_effort(piece, radius, top_edges)

        filleted[target] = piece

    return [(name, filleted.get(name, shape)) for name, shape in named_shapes]
