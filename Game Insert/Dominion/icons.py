"""Dominion icon inlays for the bins and boxes.

Icons come from ``dominion_symbols_v1_13/extras`` (SVG), the Dominion symbol font (debt
hex) and a generated 7-point star SVG. Each icon is split into separate parts (so they can be
printed in different colors) and each part is a thin solid that sits *inside* the host
surface, flush with it; the caller cuts a matching pocket in the host (``host_name``).

Public API: ``build_icons(shapes)`` takes ``{name: Part.Shape}`` of the positioned ``Bin_*``
and ``Box_*`` objects and returns ``[(name, Part.Shape, host_name)]`` for every icon part.
"""

import math
import os

import config as cfg
import FreeCAD as App
import importSVG
import Part
from FreeCAD import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
EXTRAS = os.path.join(_HERE, "dominion_symbols_v1_13", "extras")
SYMBOL_FONT = os.path.join(_HERE, "dominion_symbols_v1_13", "DominionSymbols.otf")

# Bin_<key> -> icon kind
BIN_ICONS = {
    "gold_coin": "coin",
    "copper_debt": "debt",
    "points": "shield",
    "stars": "star",
    "kingdom_markers": "logo",
}
# Box_<key> top surface layout: flank -> list of icon kinds (in a row along X)
BOX_TOPS = {
    "gold_coin": {"min_y": ["coin"], "max_y": ["debt"]},
    "stars": {"min_y": ["shield", "star"], "max_y": ["logo"]},
}


def _close(wire):
    """Return ``wire`` with its ends joined by a line if it is open."""
    if wire.isClosed():
        return wire
    edges = list(wire.Edges)
    edges.append(Part.makeLine(wire.Vertexes[-1].Point, wire.Vertexes[0].Point))
    return Part.Wire(edges)


def _faces(wires):
    """Return the faces of nested ``wires`` (even-odd, so inner wires become holes)."""
    wires = [_close(w) for w in wires]
    return list(Part.makeFace(wires, "Part::FaceMakerBullseye").Faces)


def _svg_shapes(path):
    """Return the shapes ``importSVG`` makes for ``path`` (in mm, y up).

    ``importSVG`` pops a 90/96 dpi dialog for any SVG not made by Inkscape whose width has no
    mm/in/cm unit (these are Xara ``pt`` files). It only asks when ``GuiUp``, and otherwise
    assumes 96 dpi, so ``GuiUp`` is switched off for the import to take that "Yes" answer.
    """
    previous = App.ActiveDocument
    gui_up = App.GuiUp
    doc = App.newDocument("_icon_svg")
    App.GuiUp = False
    try:
        importSVG.insert(path, doc.Name)
        return [o.Shape.copy() for o in doc.Objects if hasattr(o, "Shape") and o.Shape.Wires]
    finally:
        App.GuiUp = gui_up
        App.closeDocument(doc.Name)
        if previous is not None:
            App.setActiveDocument(previous.Name)


def _svg_faces(name, folder=EXTRAS):
    """Return faces for one ``<folder>/<name>.svg``, one set of faces per path."""
    faces = []
    for shape in _svg_shapes(os.path.join(folder, name + ".svg")):
        faces += _faces(shape.Wires)
    return faces


def _bbox(faces):
    box = App.BoundBox()
    for f in faces:
        box.add(f.BoundBox)
    return box


def _apply(faces, scale=1.0, dx=0.0, dy=0.0):
    out = []
    for f in faces:
        g = f.copy()
        g.transformShape(App.Matrix(scale, 0, 0, dx, 0, scale, 0, dy, 0, 0, scale, 0))
        out.append(g)
    return out


def _centre(faces, ref=None):
    """Move ``faces`` so the bounding-box centre of ``ref`` (default: themselves) is the origin."""
    b = _bbox(ref or faces)
    return _apply(faces, 1.0, -b.Center.x, -b.Center.y)


def _digit(text, height):
    """Return the faces of ``text`` in ``cfg.ICON_FONT``, ``height`` tall and centred."""
    faces = []
    for char_wires in Part.makeWireString(text, cfg.ICON_FONT, 10, 0):
        faces += _faces(char_wires)
    b = _bbox(faces)
    faces = _apply(faces, height / b.YLength, 0, 0)
    return _centre(faces)


def _glyph(char, height):
    """Return the faces of one ``DominionSymbols`` glyph, ``height`` tall and centred."""
    faces = []
    for char_wires in Part.makeWireString(char, SYMBOL_FONT, 10, 0):
        faces += _faces(char_wires)
    b = _bbox(faces)
    return _centre(_apply(faces, height / b.YLength, 0, 0))


def _star_svg(path, points=7, inner=0.5, radius=50.0):
    """Write a regular ``points``-pointed star SVG (point up) to ``path`` if missing."""
    if os.path.exists(path):
        return
    pts = []
    for i in range(points * 2):
        r = radius if i % 2 == 0 else radius * inner
        a = math.pi * i / points
        pts.append(f"{radius + r * math.sin(a):.3f},{radius - r * math.cos(a):.3f}")
    size = 2 * radius
    with open(path, "w") as f:
        f.write(
            '<?xml version="1.0" standalone="no"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{size}mm" '
            f'height="{size}mm" viewBox="0 0 {size} {size}">\n'
            f'  <path d="M {" L ".join(pts)} Z" fill="#000000" stroke="none"/>\n</svg>\n'
        )


def _ellipse_ring(a, b, line):
    """Return the face of an elliptical outline (semi-axes ``a`` x ``b``, ``line`` wide)."""
    outer = Part.Ellipse(Vector(0, 0, 0), a, b).toShape()
    inner = Part.Ellipse(Vector(0, 0, 0), a - line, b - line).toShape()
    return _faces([Part.Wire(outer), Part.Wire(inner)])


def make_icon(kind):
    """Return ``(parts, (w, h))`` for an icon kind: ``{part: [Face]}`` centred at the origin.

    Parameters
    ----------
    kind : str
        One of ``coin``, ``debt``, ``shield``, ``star``, ``logo``.

    Returns
    -------
    parts : dict
        Part name -> faces in the XY plane, all sharing one centred frame.
    size : tuple of float
        Width and height of the whole icon.
    """
    if kind == "coin":
        # the SVG is far too detailed to print: keep the outer ring, the shield outline and a
        # digit. The four biggest outlines nest (ring out/in, shield out/in).
        big = sorted(_svg_faces("coin"), key=lambda f: -f.Area)[:4]
        ring, shield = _even_odd(big[:2]), _even_odd(big[2:])
        ib = _bbox(shield)
        parts = {
            "ring": ring,
            "shield": shield,
            "digit": _apply(_digit("1", ib.YLength * 0.4), 1.0, ib.Center.x, ib.Center.y),
        }
        ref = ring
    elif kind == "debt":
        hexes = _glyph(".", 10)
        hb = _bbox(hexes)
        digit = _apply(_digit("1", hb.YLength * 0.4), 1.0, hb.Center.x, hb.Center.y)
        parts = {"debt": hexes, "digit": digit}
        ref = hexes
    elif kind == "shield":
        # just the outline (the inner shield is left hollow, so no red/green halves) and a digit
        outline = _svg_faces("shield outline")
        ib = min(outline, key=lambda f: f.Area).BoundBox  # the inner path is the shield area
        outline = _even_odd(outline)
        digit = _apply(_digit("8", ib.YLength * 0.45), 1.0, ib.Center.x, ib.Center.y)
        parts = {"outline": outline, "digit": digit}
        ref = outline
    elif kind == "star":
        path = os.path.join(EXTRAS, "star7.svg")
        _star_svg(path)
        star = _svg_faces("star7")
        parts, ref = {"star": star}, star
    elif kind == "logo":
        logo = _svg_faces("dominion logo")
        lb = _bbox(logo)
        long_, short = cfg.KINGDOM_MARKER_OVAL
        a, b = long_ / 2, short / 2
        line = cfg.ICON_LINE
        # largest logo (aspect lb) whose corners stay inside the oval's inner edge
        ai, bi = a - line - cfg.ICON_MARGIN, b - line - cfg.ICON_MARGIN
        aspect = lb.XLength / lb.YLength
        half_w = 1 / math.sqrt(1 / ai**2 + 1 / (aspect * bi) ** 2)
        scale = 2 * half_w / lb.XLength
        logo = _apply(_centre(logo), scale, 0, 0)
        parts = {"oval": _ellipse_ring(a, b, line), "logo": logo}
        ref = parts["oval"]
    b = _bbox(ref)
    shift = (-b.Center.x, -b.Center.y)
    if kind in ("coin", "debt", "shield"):
        parts = {k: _apply(v, 1.0, *shift) for k, v in parts.items()}
    elif kind == "star":
        parts = {k: _centre(v) for k, v in parts.items()}
    return parts, (b.XLength, b.YLength)


def _place(parts, size, centre, axes, fit, depth):
    """Scale an icon to ``fit`` (w, h), extrude it inward and move it onto a surface.

    ``axes`` is ``(ex, ey, ez)``: the surface directions for icon x, icon y and the outward
    normal. Parts extend from the surface ``depth`` along ``-ez`` (inside the host).
    """
    scale = min(fit[0] / size[0], fit[1] / size[1])
    ex, ey, ez = axes
    m = App.Matrix(
        ex.x, ey.x, ez.x, centre.x, ex.y, ey.y, ez.y, centre.y, ex.z, ey.z, ez.z, centre.z
    )
    out = {}
    for name, faces in parts.items():
        solids = [f.extrude(Vector(0, 0, -depth)) for f in _apply(faces, scale, 0, 0)]
        solid = solids[0].multiFuse(solids[1:]) if len(solids) > 1 else solids[0]
        solid.transformShape(m)
        out[name] = solid
    return out


def _inside(f, g):
    """Return True if face ``f`` lies wholly within face ``g``."""
    return g.BoundBox.isInside(f.BoundBox) and f.cut(g).Area < 1e-3 * f.Area


def _even_odd(faces):
    """Return ``faces`` (each one closed outline, filled) with nested outlines as holes.

    The SVG logo's paths arrive as separate filled outlines, so the rings, counters and window
    cut-outs have to be recovered: an outline inside an odd number of others is a hole in the
    outline that directly encloses it.
    """
    depth = [
        sum(i != j and _inside(f, g) for j, g in enumerate(faces)) for i, f in enumerate(faces)
    ]
    out = []
    for i, f in enumerate(faces):
        if depth[i] % 2:
            continue
        for j, h in enumerate(faces):
            if depth[j] == depth[i] + 1 and _inside(h, f):
                f = f.cut(h)
        out += f.Faces
    return out


def lid_logo(centre, axes, fit, depth=None):
    """Return ``{part: Part.Shape}`` of the ``cfg.LID_LOGO`` SVG inlay on a surface.

    The SVG repeats its paths (a stroke and a fill copy, plus masked copies), has gradient-mask
    rectangles and stray marker dots, and splits ring holes into their own outlines; identical
    faces are kept once, the rectangles and dots are dropped and the holes are cut back in.
    ``centre``, ``axes`` and ``fit`` are as for :func:`_place`.
    """
    path = os.path.join(_HERE, cfg.LID_LOGO)
    seen, faces = set(), []
    for f in _svg_faces(os.path.splitext(os.path.basename(path))[0], os.path.dirname(path)):
        b = f.BoundBox
        key = tuple(round(v, 2) for v in (f.Area, b.XMin, b.YMin, b.XMax, b.YMax))
        mask = len(f.Edges) == 4 and abs(f.Area - b.XLength * b.YLength) < 0.01 * f.Area
        if key not in seen and not mask and f.Area > 1:
            seen.add(key)
            faces.append(f)
    faces = _centre(_even_odd(faces))
    b = _bbox(faces)
    return _place(
        {"logo": faces}, (b.XLength, b.YLength), centre, axes, fit, depth or cfg.ICON_DEPTH
    )


def build_icons(shapes):
    """Return ``[(name, Part.Shape, host_name)]`` icon parts for the positioned bins and boxes.

    Each of a row's two bins (``Bin_<key>_<n>``) gets its icon on both the min-x and the max-x
    face; the boxes get theirs on the
    top surface, either side of the grab cut. Part names are
    ``Icon_<target>_<face>_<icon>_<part>``.
    """
    out = []
    depth, margin = cfg.ICON_DEPTH, cfg.ICON_MARGIN
    bins = [(k, n, kind) for k, kind in BIN_ICONS.items() for n in (1, 2)]
    for key, n, kind in bins:
        shape = shapes.get(f"Bin_{key}_{n}")
        if shape is None:
            continue
        b = shape.optimalBoundingBox()
        parts, size = make_icon(kind)
        fit = (b.YLength - 2 * margin, b.ZLength - 2 * margin)
        yc, zc = (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2
        faces = (
            ("minx", b.XMin, (Vector(0, -1, 0), Vector(0, 0, 1), Vector(-1, 0, 0))),
            ("maxx", b.XMax, (Vector(0, 1, 0), Vector(0, 0, 1), Vector(1, 0, 0))),
        )
        for face, x, axes in faces:
            placed = _place(parts, size, Vector(x, yc, zc), axes, fit, depth)
            out += [
                (f"Icon_Bin_{key}_{n}_{face}_{kind}_{p}", s, f"Bin_{key}_{n}")
                for p, s in placed.items()
            ]
    rim = margin + cfg.BOX_OUTER_FILLET
    for key, flanks in BOX_TOPS.items():
        shape = shapes.get(f"Box_{key}")
        if shape is None:
            continue
        b = shape.optimalBoundingBox()
        ymid = (b.YMin + b.YMax) / 2
        spans = {
            "min_y": (b.YMin + rim, ymid - cfg.GRAB_R - margin),
            "max_y": (ymid + cfg.GRAB_R + margin, b.YMax - rim),
        }
        for flank, kinds in flanks.items():
            y0, y1 = spans[flank]
            cell_w = (b.XLength - 2 * rim - margin * (len(kinds) - 1)) / len(kinds)
            for i, kind in enumerate(kinds):
                parts, size = make_icon(kind)
                xc = b.XMin + rim + cell_w * (i + 0.5) + margin * i
                axes = (Vector(1, 0, 0), Vector(0, 1, 0), Vector(0, 0, 1))
                centre = Vector(xc, (y0 + y1) / 2, b.ZMax)
                placed = _place(parts, size, centre, axes, (cell_w, y1 - y0), depth)
                out += [
                    (f"Icon_Box_{key}_top_{kind}_{p}", s, f"Box_{key}") for p, s in placed.items()
                ]
    return out
