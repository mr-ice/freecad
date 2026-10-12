"""Build the Dominion bit shapes (bulk metal, mats, player pieces) and the two bay spaces.

Public API: ``build_all()`` returns ``[(name, Part.Shape, is_bay, hidden)]`` with every shape
already moved to its grid position; ``PLACEMENTS`` holds those positions.
Override any position via ``config.PLACEMENTS``.
"""

import math

import config as cfg
import icons
import Part
from FreeCAD import Vector

# A bin is bay_1 wide less a wall each side (BIN_X); the bulk x is the bin less its own walls.
# y is the measured 60. Config volumes (35*60*h) are preserved, so z grows to compensate for
# the narrower x.
BULK_Y = cfg.BULK_Y
BIN_X = cfg.bay[1]["x"] - 2 * cfg.WALL_THICKNESS
# Each row is two bins side by side (BIN_Y_OUT wide each, BOX_TOLERANCE apart), together as wide
# as one bin around BULK_Y was.
BULK_HALF_Y = (BULK_Y - 2 * cfg.WALL_THICKNESS - cfg.BOX_TOLERANCE) / 2
BIN_Y_OUT = BULK_HALF_Y + 2 * cfg.WALL_THICKNESS
BULK_FOOTPRINT = (BIN_X - 2 * cfg.WALL_THICKNESS, BULK_HALF_Y)
STARS_VOLUME = 35 * 60 * 16

# Mat type -> (config key, how many types share that key's quantity)
MAT_TYPES = {
    "base": ("player_mat", 1),
    "exile": ("coffers_villagers_exile_mat", 2),
    "coffers_villagers": ("coffers_villagers_exile_mat", 2),
    "island": ("island_ship_sea_mat", 3),
    "ship": ("island_ship_sea_mat", 3),
    "sea": ("island_ship_sea_mat", 3),
    "favor": ("favors_mat", 1),
}


def _box(x, y, z):
    return Part.makeBox(x, y, z)


def _mat_dims(kind):
    """Return ``(x, y, t, quantity)`` for a mat type."""
    key, shared = MAT_TYPES[kind]
    m = cfg.Components[key]
    return m["x"], m["y"], m["t"], m["quantity"] // shared


def make_mat_stack(kind):
    """Stack of one mat type standing on edge: mat x is Y, mat y is Z, thickness stacks along X."""
    x, y, t, qty = _mat_dims(kind)
    return _box(t * qty, x, y)


def make_player_stack():
    """One of each mat type, corner-aligned, standing on edge (mat y along Z)."""
    parts, x0 = [], 0.0
    for kind in MAT_TYPES:
        x, y, t, _ = _mat_dims(kind)
        b = _box(t, x, y)
        b.translate(Vector(x0, 0, 0))
        parts.append(b)
        x0 += t
    return parts[0].multiFuse(parts[1:])


def make_player_pieces(player):
    """One player's parts as ``[(name, shape)]``: card stack, token stack, two cubes.

    Names are suffixed ``_<player>`` (1-based).
    """
    pp = cfg.Components["player_pieces"]
    card, tok, cube = pp["minus_card_gold"], pp["plus_tokens"], pp["cube"]
    r = tok["diameter"] / 2
    parts = [
        (f"PlayerCards_{player}", _box(card["x"], card["y"], card["quantity"] * card["t"])),
        (
            f"PlayerTokens_{player}",
            Part.makeCylinder(r, tok["quantity"] * tok["t"], Vector(r, r, 0)),
        ),
    ]
    parts += [
        (f"PlayerCube_{player}_{i + 1}", _box(cube["x"], cube["y"], cube["z"]))
        for i in range(cube["quantity"])
    ]
    return parts


BOX_MATS = ("base", "exile", "coffers_villagers", "favor")


def _make_box_wall(t, oy, height):
    """Solid min-x wall: ``height`` tall, finger hole near the top, rounded top corners."""
    wall = _box(t, oy, height)
    r = cfg.BOX_HOLE_D / 2
    wall = wall.cut(
        Part.makeCylinder(
            r, t, Vector(0, oy / 2, height - cfg.BOX_HOLE_MARGIN - r), Vector(1, 0, 0)
        )
    )
    tol = 1e-6
    wall = wall.makeFillet(
        cfg.BOX_WALL_FILLET,  # top corners: edges along X at the top
        [
            e
            for e in wall.Edges
            if abs(e.BoundBox.ZMin - height) < tol
            and e.BoundBox.XLength > tol
            and e.BoundBox.YLength < tol
        ],
    )
    rim = [e for e in wall.Edges if abs(getattr(e.Curve, "Radius", 0) - r) < tol]
    return wall.makeFillet(cfg.BOX_HOLE_FILLET, rim)


def make_mat_box():
    """Open-top box for the ``BOX_MATS`` stacks, standing on edge side by side along X.

    Walls are 2*WALL (the whole stack is lifted by them). Solid: bottom and a min-x wall
    as tall as bay_1 with a finger hole and rounded edges.
    Skeleton: an L-shaped corner post (two overlapping t x ``POST_LEG`` rectangles,
    bay_1 z / 3 tall) at each max-x corner with a 45 degree brace rising from its top to
    the min-x wall (min-y / max-y sides), and on the max-x side two struts rising
    from the post tops to a point at the centre of the virtual wall.
    Overall X is bay_1 width less ``BOX_TOLERANCE``; Y and Z interiors add ``MAT_CLEARANCE``
    so the mats slide in and out.
    """
    t = 2 * cfg.WALL_THICKNESS
    dims = [_mat_dims(k) for k in BOX_MATS]
    stacks = sum(tt * q for _, _, tt, q in dims)
    iy = max(x for x, *_ in dims) + cfg.MAT_CLEARANCE
    iz = max(y for _, y, *_ in dims) + cfg.MAT_CLEARANCE
    ox = cfg.bay[1]["x"] - cfg.BOX_TOLERANCE  # fits the narrow bay; slack is mat clearance
    ix = ox - 2 * t
    assert ix >= stacks, "bay_1 is too narrow for the mat stacks"
    oy, oz = iy + 2 * t, iz + t
    xp = t + ix  # inner face of the max-x posts
    parts = [_box(ox, oy, t), _make_box_wall(t, oy, cfg.bay[1]["z"])]

    pz = cfg.bay[1]["z"] / 3  # corner post height; the brace starts at its top
    h = cfg.BRACE_T * math.sqrt(2)  # vertical thickness of a 45 degree bar BRACE_T wide
    brace = Part.Face(
        Part.makePolygon(
            [Vector(xp, 0, pz), Vector(t, 0, pz + ix), Vector(t, 0, pz + ix - h)]
            + [Vector(xp, 0, pz - h), Vector(xp, 0, pz)]
        )
    ).extrude(Vector(0, t, 0))
    for y in (0, oy - t):
        b = brace.copy()
        b.translate(Vector(0, y, 0))
        parts.append(b)
    # corner posts: two t x POST_LEG rectangles overlapping at each max-x corner
    leg = cfg.POST_LEG
    for y0, y1 in ((0, 0), (oy - leg, oy - t)):
        for w, d, py in ((t, leg, y0), (leg, t, y1)):
            post = _box(w, d, pz)
            post.translate(Vector(ox - w, py, 0))
            parts.append(post)

    # struts: BRACE_T-wide bars from the top of each corner post to the centre of the
    # max-x virtual wall
    bt = cfg.BRACE_T
    sy, sz = bt / 2, pz - bt / 2  # centreline starts inside the post, flush with its top
    dy, dz = oy / 2 - sy, oz / 2 - sz
    ln = math.hypot(dy, dz)
    ny, nz = -dz / ln * bt / 2, dy / ln * bt / 2  # half-thickness normal in the YZ plane
    for flip in (False, True):
        # Each bar is clipped at the wall's centre line (y = oy/2) instead of ending square,
        # so the mirrored pair meets in a solid peak with no gap.
        def at_mid(sign):
            y0, z0 = sy + sign * ny, sz + sign * nz
            return oy / 2, z0 + (oy / 2 - y0) * dz / dy

        pts = [(sy + ny, sz + nz), (sy - ny, sz - nz), at_mid(-1), at_mid(1)]
        pts = [(oy - y if flip else y, z) for y, z in pts]
        poly = [Vector(xp, y, z) for y, z in pts]
        parts.append(Part.Face(Part.makePolygon(poly + poly[:1])).extrude(Vector(t, 0, 0)))
    return parts[0].multiFuse(parts[1:]).removeSplitter()


def make_lift():
    """Lifting plate: a base under the mat stacks plus an upright with a finger hole.

    Base: bay_0 wide (X) by a Mat_sea stack long (Y) by ``LIFT_BASE_T`` tall. Upright
    stands on the base in the max-x, max-y corner: bay_0 tall, one Mat_small stack thick
    (X), (Mat_sea - Mat_small) long. The finger hole goes through X near the top,
    centered along the upright's length. All vertical and topmost edges are filleted.
    """
    bay = cfg.bay[0]
    sea = make_mat_stack("sea").BoundBox  # X = stack thickness, Y = mat width
    sm = cfg.Components["small_mat"]
    base = _box(bay["x"], sea.YLength, cfg.LIFT_BASE_T)
    up_w, up_l = sm["t"] * sm["quantity"], sea.YLength - sm["x"]
    up = _box(up_w, up_l, bay["z"])
    # upright in the max-x, max-y corner of the base
    ox, oy = bay["x"] - up_w, sea.YLength - up_l
    up.translate(Vector(ox, oy, cfg.LIFT_BASE_T))
    r = cfg.LIFT_HOLE_D / 2
    hole = Part.makeCylinder(
        r,
        up_w,
        Vector(ox, oy + up_l / 2, cfg.LIFT_BASE_T + bay["z"] - cfg.LIFT_HOLE_MARGIN - r),
        Vector(1, 0, 0),
    )
    lift = base.fuse(up).cut(hole).removeSplitter()
    top, tol = lift.BoundBox.ZMax, 1e-6

    def on_top(e):
        return abs(e.BoundBox.ZMin - top) < tol and abs(e.BoundBox.ZMax - top) < tol

    # Big round-over on the top edges along X, then small fillets on the vertical edges
    # and the remaining top edges (along Y).
    lift = lift.makeFillet(
        cfg.LIFT_TOP_FILLET, [e for e in lift.Edges if on_top(e) and e.BoundBox.XLength > tol]
    )
    edges = [
        e
        for e in lift.Edges
        if (e.BoundBox.XLength < tol and e.BoundBox.YLength < tol) or on_top(e)
    ]
    return lift.makeFillet(cfg.LIFT_FILLET, edges)


def make_bin_box(bins, top):
    """Outer box with a separate pocket for each bin of a vertical stack of positioned bins.

    The box is as wide as ``bay_1``. The bins sit flush with its min-x face, and
    each pocket (its bin's footprint plus ``BOX_TOLERANCE``) is open only on that face, so
    bins slide in and out along X; the shelves between pockets stay solid. Floor and the
    min-y / max-y walls are ``SLEEVE_WALL`` (2*WALL), the max-x wall is whatever x is left.
    ``top`` is the box's top z (see :func:`build_all`), with a grab cut into it. The outer
    edges are filleted (``BOX_OUTER_FILLET``) and so are the pocket mouths at min-x
    (``BOX_MOUTH_FILLET``).

    Finger slots: in both the min-y and max-y walls, at x = min-x and centred on each bin,
    a half-cylinder (axis along Y, radius ``GROOVE_R``; trimmed to just inside the pocket if it
    would barely overshoot it) is cut
    through the wall, so a finger can reach in from the side to pull the bin out.
    """
    tol, w = cfg.BOX_TOLERANCE, cfg.SLEEVE_WALL
    bbs = [b.optimalBoundingBox() for b in bins]
    bx0 = min(b.XMin for b in bbs)  # bins sit at the box's min-x face, which is left open
    py0, py1 = min(b.YMin for b in bbs) - tol, max(b.YMax for b in bbs) + tol
    z0 = min(b.ZMin for b in bbs) - tol - w
    box = _box(cfg.bay[1]["x"] - cfg.BOX_TOLERANCE, py1 - py0 + 2 * w, top - z0)
    box.translate(Vector(bx0, py0 - w, z0))
    box = box.makeFillet(cfg.BOX_OUTER_FILLET, box.Edges)  # outer edges, before anything thins them
    cuts = []
    levels = {(round(b.ZMin, 3), round(b.ZMax, 3)): b for b in bbs}  # bins side by side share one
    for b in levels.values():
        zc = (b.ZMin + b.ZMax) / 2
        pocket = _box(b.XMax + tol - bx0 + 1, py1 - py0, b.ZLength + 2 * tol)
        pocket.translate(Vector(bx0 - 1, py0, b.ZMin - tol))  # overshoots the open face
        cuts.append(pocket)
        r = cfg.GROOVE_R
        half_pocket = b.ZLength / 2 + tol
        if 0 < r - half_pocket < cfg.WALL_THICKNESS:  # would only nick the shelf: pull it in
            r = half_pocket - tol
        for y in (py0 - w - 1, py1 - 1):  # through the min-y and max-y walls
            cuts.append(Part.makeCylinder(r, w + 2, Vector(bx0, y, zc), Vector(0, 1, 0)))
    cuts += _grab_cuts(bx0, (py0 + py1) / 2, top)
    box = box.cut(Part.makeCompound(cuts)).removeSplitter()
    # Edges at the open min-x face: the pocket mouths (edges inside the outer rim). The long
    # shelf/floor lips go first, then the short vertical ones; each pass is kept only if the
    # result is a valid solid. Edges shorter than 10 mm (around the finger slots) stay sharp.
    for long_edges in (True, False):
        box = _fillet_mouth(box, bx0, long_edges)
    return box


def _edge_indices(shape, edges):
    """Return indices into ``shape.Edges`` of ``edges`` (to find them again in a copy)."""
    return [i for i, e in enumerate(shape.Edges) if any(e.isSame(x) for x in edges)]


def _sound(shape):
    """Return True if ``shape`` passes the full BOP check with sane edge tolerances.

    ``isValid()`` alone misses fillets that leave open edges (tolerances in the mm range).
    """
    try:
        shape.check(True)
    except Exception:  # noqa: BLE001 -- Part raises a bare Exception with the BOP report
        return False
    return max(e.Tolerance for e in shape.Edges) < 1e-3


def _fillet_mouth(box, bx0, long_edges):
    """Fillet the min-x mouth edges that are long (>= 60 mm) or medium (10-60 mm).

    All at once if that gives a sound solid, otherwise one edge at a time, keeping only
    the fillets that stay sound.
    """

    def candidates(shape):
        tol, rim, bb = 1e-6, cfg.BOX_OUTER_FILLET, shape.BoundBox
        return [
            e
            for e in shape.Edges
            if abs(e.BoundBox.XMin - bx0) < tol
            and abs(e.BoundBox.XMax - bx0) < tol
            and e.BoundBox.YMin > bb.YMin + rim + tol
            and e.BoundBox.YMax < bb.YMax - rim - tol
            and e.BoundBox.ZMin > bb.ZMin + rim + tol
            and e.BoundBox.ZMax < bb.ZMax - rim - tol
            and ((e.Length >= 60) if long_edges else (10 < e.Length < 60))
        ]

    def try_fillet(shape, edges):
        try:
            # fillet a copy: a failed fillet corrupts the shape it was run on
            probe = shape.copy()
            keep = [probe.Edges[i] for i in _edge_indices(shape, edges)]
            result = probe.makeFillet(cfg.BOX_MOUTH_FILLET, keep)
        except Part.OCCError:
            return None
        return result if _sound(result) else None

    edges = candidates(box)
    # done = try_fillet(box, edges)
    return box
    if done is not None:
        return done
    for centre in [e.CenterOfMass for e in edges]:
        left = [e for e in candidates(box) if (e.CenterOfMass - centre).Length < 1e-3]
        if left:
            box = try_fillet(box, left[:1]) or box
    return box


def _grab_cuts(bx0, y_mid, top):
    """BombBusters-style grab in the top surface.

    Two half-cylinders of radius ``GRAB_R``, axes parallel to X and centred on the top
    surface at ``y_mid``, split by a ``2*WALL`` tab at the middle of the box's x width.
    """
    w = cfg.WALL_THICKNESS
    xm, tab, ext = bx0 + cfg.bay[1]["x"] / 2, 2 * w, 1.0
    ends = ((bx0 - ext, xm - tab / 2), (xm + tab / 2, bx0 + cfg.bay[1]["x"] + ext))
    return [
        Part.makeCylinder(cfg.GRAB_R, b - a, Vector(a, y_mid, top), Vector(1, 0, 0))
        for a, b in ends
    ]


def _fillet_bottom_y_edges(shape, r):
    """Fillet the bottom edges that run along Y (the two lower short-side edges)."""
    zmin = shape.BoundBox.ZMin
    edges = [
        e
        for e in shape.Edges
        if abs(e.BoundBox.ZMin - zmin) < 1e-6
        and abs(e.BoundBox.ZMax - zmin) < 1e-6
        and e.BoundBox.YLength > 1e-6
    ]
    return shape.makeFillet(r, edges)


def make_player_box(horizontal=False):
    """Open-top box for one player's pieces: a pocket the card footprint plus clearance.

    The pocket is the ``minus_card_gold`` x/y plus ``PLAYER_BOX_CLEARANCE`` and as tall as
    the ``plus_tokens`` stack; walls and floor are ``WALL_THICKNESS``. The outside vertical
    and bottom edges are filleted (``BOX_OUTER_FILLET``) and so is the pocket's top rim
    (``BIN_FILLET``). The finished box is rotated -90 degrees about Y, then 90 about X
    (which swaps its y and z extents); ``horizontal`` skips the X turn, leaving it wide in Y.
    """
    pp = cfg.Components["player_pieces"]
    card, tok, w = pp["minus_card_gold"], pp["plus_tokens"], cfg.WALL_THICKNESS
    ix, iy = card["x"] + cfg.PLAYER_BOX_CLEARANCE, card["y"] + cfg.PLAYER_BOX_CLEARANCE
    iz = tok["quantity"] * tok["t"]
    outer = _box(ix + 2 * w, iy + 2 * w, iz + w)
    tol = 1e-6
    # outside corners: the 4 vertical edges and the 4 bottom edges (not the top rim)
    edges = [
        e
        for e in outer.Edges
        if (e.BoundBox.ZLength > tol) or (e.BoundBox.ZMax < tol)  # vertical or at z = 0
    ]
    outer = outer.makeFillet(cfg.BOX_OUTER_FILLET, edges)
    pocket = _box(ix, iy, iz + 1)
    pocket.translate(Vector(w, w, w))
    box = outer.cut(pocket)
    top = box.BoundBox.ZMax
    rim = [  # pocket rim: top-face edges away from the outer perimeter
        e
        for e in box.Edges
        if abs(e.BoundBox.ZMin - top) < tol
        and abs(e.BoundBox.ZMax - top) < tol
        and e.BoundBox.XMin > w - tol
        and e.BoundBox.XMax < ix + w + tol
        and e.BoundBox.YMin > w - tol
        and e.BoundBox.YMax < iy + w + tol
    ]
    box = box.makeFillet(cfg.BIN_FILLET, rim)
    box.rotate(Vector(0, 0, 0), Vector(0, 1, 0), -90)  # on its side, opening toward -x
    if not horizontal:
        box.rotate(Vector(0, 0, 0), Vector(1, 0, 0), 90)  # then about X (swaps y and z)
    bb = box.BoundBox
    box.translate(Vector(-bb.XMin, -bb.YMin, -bb.ZMin))  # keep the min corner at the origin
    return box


def _case_layout():
    """Dimensions of the player box case, all in the case's own frame (min corner at origin).

    The case fills bay_0 beside the lift in Y. Pocket 1 is three columns separated by
    ``WALL_THICKNESS`` walls. Columns 1 and 3 each hold two tall boxes (1/4, 3/6) stacked
    touching with no shelf, so a pair lifts out together. Column 2 holds the two wide boxes
    (2/5, ``make_player_box(True)``) stacked the same way, then a shelf, then a headroom
    pocket for incidentals above them. Pocket 2 takes the Y that is left. The hinge runs
    along Z past the max-y end; the lid is ``2*WALL`` thick on the open face.
    """
    w, tol, r, g = cfg.WALL_THICKNESS, cfg.BOX_TOLERANCE, cfg.HINGE_R, cfg.HINGE_GAP
    bay = cfg.bay[0]
    pb = make_player_box().BoundBox
    a, b = pb.YLength, pb.ZLength  # tall box: a wide in Y, b tall in Z (the wide box swaps them)
    widths, heights = (a, b, a), (b, a, b)  # box y and z per column
    px, inner = pb.XLength + tol, 2 * b + tol  # pocket depth (X); column height (Z)
    x_total = bay["x"] - tol  # the whole case, lid included, fills bay_0 x
    lid_t = x_total - (px + w)  # the lid takes the depth the body leaves
    assert lid_t >= 2 * w, "bay_0 is too shallow for the player box case"
    body_x = lid_t  # the body front touches the lid's inner face
    y0 = _lift_len() + tol  # case starts past the lift
    body_y = bay["y"] - y0 - r  # the body ends at the hinge axis; the knuckles add r beyond
    height = bay["z"] + cfg.LIFT_BASE_T  # same height as the lift
    fz = (height - inner) / 2  # floor and ceiling share what the columns leave
    ys, y = [], w  # column y
    for wd in widths:
        ys.append(y)
        y += wd + tol + w
    cw = [d + tol for d in widths]
    pocket2_y = body_y - (r + g + w) - y  # leaves wall for the lid-knuckle notch
    assert fz >= 1 and pocket2_y > 0, "bay_0 is too small for the player box case"
    stack = 2 * heights[1] + tol  # the wide boxes' stack; the shelf sits on it
    cells = [(ys[0], cw[0], fz, inner), (ys[1], cw[1], fz, stack), (ys[2], cw[2], fz, inner)]
    upper = (ys[1], cw[1], fz + stack + w, inner - stack - w)  # headroom over box 5
    slots = [  # boxes 1-3 low, 4-6 stacked on them; each centred in its column's y
        (body_x + tol / 2, ys[c] + tol / 2, fz + tol / 2 + k * heights[c])
        for k in range(2)
        for c in range(3)
    ]
    return {
        "w": w, "r": r, "g": g, "lid_t": lid_t, "x": x_total, "body_x": body_x,
        "px": px, "fz": fz, "inner": inner, "cells": cells, "upper": upper,
        "y0": y0, "body_y": body_y, "pocket2_y": pocket2_y, "pocket2_at": y,
        "height": height, "slots": slots,
    }  # fmt: skip


def _lift_len():
    """Y length of the lift (one Mat_sea stack's width)."""
    return cfg.Components["island_ship_sea_mat"]["x"]


def make_player_case():
    """Return ``(body, lid)``: two pockets open at min-x, and a print-in-place hinged lid.

    Body: five sides around pocket 1 (the six player boxes) and pocket 2 (the leftover Y),
    ``WALL_THICKNESS`` walls, floor and ceiling split from what the boxes leave of the height.
    The lid is a plate on the open face as thick as the case's x (``bay_0`` x less
    ``BOX_TOLERANCE``) leaves, touching the body. Its inner face is pocketed (``WALL_THICKNESS``
    outer panel and rim) for incidentals between the player boxes and the lid.

    The hinge axis runs along Z at the body's max-y end face, midway in x. Open 180 degrees the
    lid's outer face (min-x) lands in the plane of the body's back face (max-x), so both lie flat
    on the bed with the axis horizontal (print the lid rotated into that pose); since both end at
    the axis, they don't overlap. Knuckles of radius ``HINGE_R`` alternate along the axis.
    Case knuckles sit on the body's end face with a wedge toward the back face that thins to the
    body's end there, and a 45 degree gusset on the other side. Lid knuckles hang off a wedge
    that continues the lid plate past the axis and thins to the plate's end at the outer face,
    with a 45 degree gusset under the knuckle; the body is notched at those bands for the
    knuckle, gusset and the wedge's flipped position. There is no pin: each case knuckle has
    a truncated cone (``HINGE_CONE_R``/``HINGE_CONE_TIP``) on its faces toward the lid knuckles,
    which carry sockets with ``HINGE_CONE_CLEARANCE`` all round, so the lid is captive yet free.
    """
    lay = _case_layout()
    w, r, g, lt, h = lay["w"], lay["r"], lay["g"], lay["lid_t"], lay["height"]
    xb, xt = lay["body_x"], lay["x"]
    xa = xt / 2  # hinge axis x: midway between the lid's outer face and the body's back face
    ya = lay["body_y"]  # hinge axis y: the body's end face
    ty = ya + r  # the case's y with the knuckles
    k = r / math.sqrt(2)  # 45 degree tangent offset on a knuckle
    body = _box(lay["px"] + w, ya, h)
    body.translate(Vector(xb, 0, 0))
    px, fz = lay["px"], lay["fz"]
    uy, ucw, uz, uh = lay["upper"]
    pockets = [_pocket(xb, y, z, px, cw, ch) for y, cw, z, ch in lay["cells"] + [lay["upper"]]]
    pockets.append(_pocket(xb, lay["pocket2_at"], fz, px, lay["pocket2_y"], lay["inner"]))
    body = body.cut(Part.makeCompound(pockets))
    # Grab in the top, centred on the case, over the headroom pocket. It is as deep as the
    # ceiling plus that pocket less a wall (and no wider than the column and its walls), and
    # a solid block fills the pocket under its footprint to leave that wall.
    yc = ya / 2
    assert uy <= yc <= uy + ucw, "the headroom pocket must sit under the case's centre"
    rg = min(cfg.GRAB_R, fz + uh - w, yc - uy + w, uy + ucw + w - yc)
    y_a, y_b = max(uy, yc - rg - w), min(uy + ucw, yc + rg + w)
    block = _box(px, y_b - y_a, uh)
    block.translate(Vector(xb, y_a, uz))
    body = body.fuse(block)
    xe = xb + px + w  # == xt, the case's back face
    # The grab runs the whole case, lid and body, centred on x; a 2*WALL tab at the middle
    # (in the lid) splits it in two.
    xm = xe / 2
    grab = Part.makeCompound(
        [
            Part.makeCylinder(rg, q - p, Vector(p, yc, h), Vector(1, 0, 0))
            for p, q in ((-1, xm - w), (xm + w, xe + 1))
        ]
    )
    body = body.cut(grab)
    lid = _box(lt, ya, h)  # the plate ends at the body's end face; the wedges add the knuckles
    hw = r * lt / (xt - xa)  # the case wedge's height at the lid plate's inner face, flipped
    inner = _box(lt - w + 1, ya - g - hw - 2 * w, h - 2 * w)  # lid pocket, open at its inner face
    inner.translate(Vector(w, w, w))
    lid = lid.cut(inner)
    # a solid block fills the lid pocket under the grab, leaving a wall below its cut
    fill = _box(lt - w, 2 * (rg + w), rg)
    fill.translate(Vector(w, yc - rg - w, h - w - fill.BoundBox.ZLength))
    lid = lid.fuse(fill).cut(grab)
    n = cfg.HINGE_KNUCKLES
    bands = [(i * h / n, (i + 1) * h / n) for i in range(n)]
    # Cone-and-socket pivots instead of a pin: each case knuckle has a 45 degree truncated cone
    # on its faces toward a lid knuckle; the lid knuckle's socket is that cone offset by the
    # clearance (normal to its surface), so nothing fuses.
    rb, rt, c = cfg.HINGE_CONE_R, cfg.HINGE_CONE_TIP, cfg.HINGE_CONE_CLEARANCE
    hc = rb - rt
    s_open, s_tip, s_depth = rb - g + c * math.sqrt(2), rt - c + c * math.sqrt(2), hc + c - g
    assert s_depth > 0 and s_open < r - 1, "hinge cone does not fit the knuckle"
    body_parts, body_cuts, lid_cuts, lid_parts, sockets, cones = [body], [], [], [], [], []
    for i, (a, b) in enumerate(bands):
        a, b = a + g / 2, b - g / 2
        dz = b - a
        knuckle = Part.makeCylinder(r, dz, Vector(xa, ya, a))
        if i % 2:
            # lid knuckle on a wedge continuing the plate past the axis: it thins to the plate's
            # end at the outer face (min-x). A 45 degree gusset under the knuckle (toward -x)
            # supports it; the body gives way (notch) for the knuckle, gussets and flipped wedge.
            wedge = _prism([(0, ya - 1), (xa, ya - 1), (xa, ty), (0, ya)], a, dz)
            gusset = _prism(
                [(xa, ya + 1), (xa - 2 * k, ya + 1), (xa - 2 * k, ya), (xa - k, ya - k)], a, dz
            )
            lid_parts += [knuckle, wedge, gusset]
            sockets += [
                Part.makeCone(s_open, s_tip, s_depth, Vector(xa, ya, a), Vector(0, 0, 1)),
                Part.makeCone(s_open, s_tip, s_depth, Vector(xa, ya, b), Vector(0, 0, -1)),
            ]
            notch = _box(xt - xb + 2, r + g + 1, dz + 2 * g)
            notch.translate(Vector(xb - 1, ya - r - g, a - g))
            body_cuts.append(notch)
            continue
        # case knuckle on the end face: a 45 degree gusset on its -x side and a wedge on its +x
        # side that thins to the body's end at the back face (max-x), both 1 mm into the body
        body_parts += [
            knuckle,
            _prism([(xa, ya - 1), (xt, ya - 1), (xt, ya), (xa, ty)], a, dz),
            _prism([(xa, ya - 1), (xa - 2 * k, ya - 1), (xa - 2 * k, ya), (xa - k, ya + k)], a, dz),
        ]
        if i + 1 < n:
            cones.append(Part.makeCone(rb, rt, hc, Vector(xa, ya, b), Vector(0, 0, 1)))
        if i:
            cones.append(Part.makeCone(rb, rt, hc, Vector(xa, ya, a), Vector(0, 0, -1)))
        # the lid plate stops short of where the case wedge will stand once the lid is flipped:
        # a gap at its outer face, growing along the wedge's slope toward the inner face
        cut = _prism(
            [(-1, ya - g), (0, ya - g), (lt, ya - g - hw), (lt + 1, ya - g - hw)]
            + [(lt + 1, ty + 1), (-1, ty + 1)],
            a - g,
            dz + 2 * g,
        )
        lid_cuts.append(cut)
    # the cones stand in the notches' z range, so they go on after the notches are cut
    body = _fuse([_fuse(body_parts).cut(Part.makeCompound(body_cuts))] + cones)
    lid = _fuse([lid.cut(Part.makeCompound(lid_cuts))] + lid_parts).cut(Part.makeCompound(sockets))
    return body, lid


def _prism(points, z, dz):
    """Polygon of ``(x, y)`` points extruded ``dz`` along Z from ``z``."""
    poly = Part.makePolygon([Vector(x, y, z) for x, y in points + points[:1]])
    return Part.Face(poly).extrude(Vector(0, 0, dz))


def _pocket(x, y, z, dx, dy, dz):
    """Pocket cut: starts 1 mm before ``x`` so it breaks through the open min-x face."""
    p = _box(dx + 1, dy, dz)
    p.translate(Vector(x - 1, y, z))
    return p


def case_placements(origin):
    """Positions of the player case, its lid, and the six player boxes inside it.

    ``origin`` is where ``Bay_0`` sits. The case abuts the lift's far end (plus tolerance).
    """
    ox, oy, oz = origin
    lay = _case_layout()
    base = (ox, oy + lay["y0"], oz)
    out = {"PlayerCase": base, "PlayerCase_Lid": base}
    for n, (x, y, z) in enumerate(lay["slots"], 1):
        out[f"PlayerBox_{n}"] = (base[0] + x, base[1] + y, base[2] + z)
    return out


def make_bin(bulk):
    """Open-top bin around a positioned bulk shape, with the bulk volume cut out.

    Bin is 2*WALL bigger in x/y and WALL bigger in z, centered on the bulk in x/y and
    flush with its top (max z), so the extra WALL is the floor.
    """
    w, bb = cfg.WALL_THICKNESS, bulk.BoundBox
    box = _box(bb.XLength + 2 * w, bb.YLength + 2 * w, bb.ZLength + w)
    box.translate(Vector(bb.XMin - w, bb.YMin - w, bb.ZMax - box.BoundBox.ZLength))
    bin_ = box.cut(bulk)
    top, tol = bin_.BoundBox.ZMax, 1e-6
    inner = [  # top-face edges not on the outer perimeter = the cavity rim
        e
        for e in bin_.Edges
        if abs(e.BoundBox.ZMin - top) < tol
        and abs(e.BoundBox.ZMax - top) < tol
        and e.BoundBox.XMin > bb.XMin - w + tol
        and e.BoundBox.XMax < bb.XMax + w - tol
        and e.BoundBox.YMin > bb.YMin - w + tol
        and e.BoundBox.YMax < bb.YMax + w - tol
    ]
    return bin_.makeFillet(cfg.BIN_FILLET, inner)


# Bulk items grouped into stacks (bottom first); each stack gets one outer box.
STACKS = (("gold_coin", "copper_debt"), ("stars", "points", "kingdom_markers"))


BINS = (1, 2)  # the two bins side by side in each row, min-y first
# box wall + gap + bin wall (y, z): bulk inset from the box's edge
INSET = cfg.SLEEVE_WALL + cfg.BOX_TOLERANCE + cfg.WALL_THICKNESS


def bulk_height(key):
    """Height (z) of one bin's bulk cavity: the stack's free depth shared out by volume.

    Each stack's bins fill the bay's height from its floor up to the grab cut (less the walls and
    gaps between bins), split in proportion to the config volumes. That is more than the volume
    needs, so every bin has room to spare.
    """
    keys = next(k for k in STACKS if key in k)
    volume = lambda k: STARS_VOLUME if k == "stars" else cfg.Components["metal"][k]["volume"]  # noqa: E731
    free = (
        cfg.bay[1]["z"]
        - INSET
        - (cfg.WALL_THICKNESS + cfg.BOX_TOLERANCE + cfg.GRAB_R)
        - (len(keys) - 1) * (cfg.WALL_THICKNESS + cfg.BIN_GAP)
    )
    return free * volume(key) / sum(volume(k) for k in keys)


def stack_placements(origin):
    """Return positions derived from where ``Bay_1`` sits (``origin``): bulk items and MatBox.

    Each stack's outer box spans bay_1 in x, floor on the bay floor, and the first box ends
    flush with the bay's max-y; the next box abuts it. Within a box each bin's floor
    (WALL) sits ``BIN_GAP`` above the bin below, so spacing follows the computed bulk
    heights; the topmost bin must stay under the box top (bay_1 z).
    """
    bay = cfg.bay[1]
    ox, oy, oz = origin
    inset = INSET
    box_len = BULK_Y + 2 * cfg.WALL_THICKNESS + 2 * cfg.BOX_TOLERANCE + 2 * cfg.SLEEVE_WALL
    x = ox + cfg.WALL_THICKNESS  # bin flush with the box min-x face, bulk inside its wall
    out = {"MatBox": origin}
    for i, keys in enumerate(STACKS):
        y = oy + bay["y"] - i * box_len - inset - BULK_Y
        z = oz + inset
        for key in keys:
            for n in BINS:  # the second bin sits past the first, a tolerance apart
                out[f"Bulk_{key}_{n}"] = (x, y + (n - 1) * (BIN_Y_OUT + cfg.BOX_TOLERANCE), z)
            top = z + bulk_height(key)
            z = top + cfg.WALL_THICKNESS + cfg.BIN_GAP
        assert top - oz <= bay["z"], f"stack {keys} is {top - oz:.1f} tall, bay_1 is shorter"
    return out


def _shapes():
    """Return ``[(row, name, shape, is_bay)]`` -- row picks the grid row."""
    out = [(0, f"Bay_{i}", _box(b["x"], b["y"], b["z"]), True) for i, b in enumerate(cfg.bay)]
    for key in (*cfg.Components["metal"], "stars"):
        out += [
            (1, f"Bulk_{key}_{n}", _box(*BULK_FOOTPRINT, bulk_height(key)), False) for n in BINS
        ]
    if cfg.RENDER_DICE:
        d = cfg.Components["dice"]
        out.append((1, "Dice", _box(d["x"], d["y"], d["z"]), False))
    if cfg.RENDER_PLAYER_ITEMS:
        out += [
            (1, n, sh, False) for p in range(1, cfg.PLAYERS + 1) for n, sh in make_player_pieces(p)
        ]
    out += [
        (1, f"PlayerBox_{p}", make_player_box(p in (2, 5)), False)
        for p in range(1, cfg.PLAYERS + 1)
    ]
    out = [
        (r, n, _fillet_bottom_y_edges(sh, cfg.BULK_FILLET) if n.startswith("Bulk_") else sh, b)
        for r, n, sh, b in out
    ]
    out += [(2, f"Mat_{k}", make_mat_stack(k), False) for k in MAT_TYPES]
    sm = cfg.Components["small_mat"]
    out.append((2, "Mat_small", _box(sm["t"] * sm["quantity"], sm["x"], sm["y"]), False))
    out.append((2, "Lift", make_lift(), False))
    out.append((4, "MatBox", make_mat_box(), False))
    case, lid = make_player_case()
    out += [(4, "PlayerCase", case, False), (4, "PlayerCase_Lid", lid, False)]
    if cfg.RENDER_PLAYER_ITEMS:
        out += [(3, f"PlayerMats_{i + 1}", make_player_stack(), False) for i in range(cfg.PLAYERS)]
    return out


def default_placements(items):
    """Lay items out in rows (by row number) along X, rows stacked along Y, none overlapping."""
    pos, y = {}, 0.0
    for row in sorted({r for r, *_ in items}):
        x, depth = 0.0, 0.0
        for r, name, shape, _ in items:
            if r != row:
                continue
            bb = shape.BoundBox
            pos[name] = (x - bb.XMin, y - bb.YMin, -bb.ZMin)
            x += bb.XLength + cfg.GAP
            depth = max(depth, bb.YLength)
        y += depth + cfg.GAP
    return pos


def _lid_logo():
    """Return the lid logo inlay ``[(name, shape, host)]`` on the lid's outer (min-x) face.

    Built on the closed lid, then swung open with it when ``LID_OPEN``. The face is the lid
    plate less the hinge gap at its max-y end, and the logo reads upright from the front.
    """
    lay = _case_layout()
    bx, by, bz = PLACEMENTS["PlayerCase_Lid"]
    span, m = lay["body_y"] - lay["g"], cfg.ICON_MARGIN
    centre = Vector(bx, by + span / 2, bz + lay["height"] / 2)
    axes = (Vector(0, -1, 0), Vector(0, 0, 1), Vector(-1, 0, 0))
    fit = (cfg.LID_LOGO_SCALE * (span - 2 * m), cfg.LID_LOGO_SCALE * (lay["height"] - 2 * m))
    out = []
    for part, solid in icons.lid_logo(centre, axes, fit).items():
        if cfg.LID_OPEN:
            solid.rotate(Vector(bx + lay["x"] / 2, by + lay["body_y"], 0), Vector(0, 0, 1), 180)
        out.append((f"Icon_PlayerCase_Lid_{part}", solid, "PlayerCase_Lid"))
    return out


def _fuse(shapes):
    """Return ``shapes`` fused into one solid (touching parts can't be cut as a compound)."""
    return shapes[0].multiFuse(shapes[1:]).removeSplitter() if len(shapes) > 1 else shapes[0]


def build_all():
    """Return ``[(name, Part.Shape, is_bay, hidden)]`` positioned per ``PLACEMENTS``.

    Each ``Bulk_*`` item is hidden and followed by a ``Bin_*`` with its volume cut out; the
    ``Icon_*`` inlay parts (see :mod:`icons`) come last, with a matching pocket cut in each
    host ``Bin_*`` / ``Box_*``.
    """
    global PLACEMENTS
    items = _shapes()
    grid = default_placements(items)
    origin = {**grid, **cfg.PLACEMENTS}["Bay_1"]
    bay0 = {**grid, **cfg.PLACEMENTS}["Bay_0"]
    PLACEMENTS = {**grid, **stack_placements(origin), **case_placements(bay0), **cfg.PLACEMENTS}
    out = []
    for _, name, shape, is_bay in items:
        shape.translate(Vector(*PLACEMENTS[name]))
        if name == "PlayerCase_Lid" and cfg.LID_OPEN:  # swing it open about the hinge axis
            lay = _case_layout()
            px, py, _ = PLACEMENTS[name]
            shape.rotate(Vector(px + lay["x"] / 2, py + lay["body_y"], 0), Vector(0, 0, 1), 180)
        bulk = name.startswith("Bulk_")
        out.append((name, shape, is_bay, bulk))
        if bulk:
            out.append((name.replace("Bulk_", "Bin_", 1), make_bin(shape), False, False))
    stacks = {  # each STACKS entry is one outer box, named for its lowest bin
        keys[0]: [(n, sh) for n, sh, *_ in out for k in keys if n.startswith(f"Bin_{k}_")]
        for keys in STACKS
    }
    # All boxes are pinned to the top of Bay_1. The grab cuts (radius GRAB_R) bottom out WALL
    # above the highest pocket ceiling, which belongs to the tallest bin, so that must fit.
    bins_top = max(sh.optimalBoundingBox().ZMax for g in stacks.values() for _, sh in g)
    top = PLACEMENTS["Bay_1"][2] + cfg.bay[1]["z"]
    need = bins_top + cfg.BOX_TOLERANCE + cfg.WALL_THICKNESS + cfg.GRAB_R
    assert need <= top + 1e-6, f"boxes need {need:.1f} for the grab cut, bay_1 top is {top:.1f}"
    for key, group in stacks.items():
        out.append((f"Box_{key}", make_bin_box([sh for _, sh in group], top), False, False))
    placed = []
    if cfg.RENDER_ICONS:
        placed = icons.build_icons({n: s for n, s, *_ in out}) + _lid_logo()
    pockets = {}
    for _, shape, host in placed:
        pockets.setdefault(host, []).append(shape)
    # pocket every host where its icon parts sit, so the (separate) inlays drop in flush
    out = [(n, s.cut(_fuse(pockets[n])) if n in pockets else s, bay, hid) for n, s, bay, hid in out]
    return out + [(n, s, False, False) for n, s, _ in placed]


PLACEMENTS = {}
