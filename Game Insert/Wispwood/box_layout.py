"""Box packing layout: component placement rectangles and fit/budget validators.

Pure Python (no FreeCAD). The single source of truth for *where* every component sits in
the box, consumed by :mod:`box_insert` (geometry) and :mod:`layout_svg` (the map). Box
coordinate frame: origin at the box front-left-bottom corner, X across the 185 width, Y
along the 265 length, Z up.

Public API
----------
``Rect``, ``bottom_regions``, ``top_regions``, ``rect_in_box``, ``rects_disjoint``,
``vertical_stack_height``, ``folded_alt_within_bound``.
"""

from collections import namedtuple

import config as cfg
import derived as d

Rect = namedtuple("Rect", "x y w h")

# Gaps between bays in the bottom layer.
_BAY_GAP = 2.0
_BOTTOM_Y0 = d.OUTER_WIDTH + _BAY_GAP  # below the Wispwood tray (which is OUTER_WIDTH deep)


def bottom_regions():
    """Return the bottom-layer placement rectangles, keyed by name.

    Returns
    -------
    dict of str to Rect
        ``wispwood`` (tray, long axis along X), ``alt_bay`` (folded stand), ``small_tray``
        (the new components tray), and its wells ``well_card``, ``well_cats``, ``well_round``.
    """
    wispwood = Rect(0.0, 0.0, d.OUTER_LENGTH, d.OUTER_WIDTH)

    alt_w = d.ALT_FOLDED_W + 2 * cfg.COMPONENT_CLEARANCE
    alt_l = d.ALT_FOLDED_L + 2 * cfg.COMPONENT_CLEARANCE
    alt_bay = Rect(0.0, _BOTTOM_Y0, alt_w, alt_l)

    tray_x0 = alt_bay.x + alt_bay.w + _BAY_GAP
    small_tray = Rect(tray_x0, _BOTTOM_Y0, cfg.BOX_W - tray_x0, cfg.BOX_L - _BOTTOM_Y0)

    c = cfg.COMPONENT_CLEARANCE
    ix0 = small_tray.x + cfg.INSERT_WALL
    iy0 = small_tray.y + cfg.INSERT_WALL
    well_card = Rect(ix0, iy0, cfg.CARD_W + 2 * c, cfg.CARD_H + 2 * c)
    cats_len = cfg.CAT_COUNT * cfg.CAT_THICKNESS + 2 * c
    well_cats = Rect(
        ix0, well_card.y + well_card.h + cfg.INSERT_WALL, cfg.CAT_SIZE + 2 * c, cats_len
    )
    round_side = cfg.ROUND_TOKEN_DIA + 2 * c
    well_round = Rect(
        ix0 + cfg.CAT_SIZE + 2 * c + cfg.INSERT_WALL,
        well_cats.y,
        round_side,
        round_side,
    )
    return {
        "wispwood": wispwood,
        "alt_bay": alt_bay,
        "small_tray": small_tray,
        "well_card": well_card,
        "well_cats": well_cats,
        "well_round": well_round,
    }


def top_regions():
    """Return the top-tray pocket CAVITY rectangles, keyed by name.

    Each rect is the cavity to cut directly (no further inset): inset from the tray
    perimeter by ``INSERT_WALL`` and separated from its neighbour by ``INSERT_WALL``.
    The paw, score pad and booklet lie loose on top and are not placed here.

    Both bays run the FULL interior length (Y) so the long bits (markers 214, score pad 218)
    drop in with room to spare.

    Returns
    -------
    dict of str to Rect
        ``board_pocket`` (loose stack of 5 board pieces) and ``marker_trough`` (4 markers),
        both spanning the full interior length.
    """
    w = cfg.INSERT_WALL
    full_h = cfg.BOX_L - 2 * w  # full interior length (both bays)
    board_w = cfg.BOARD_CENTER_PTP + cfg.BOARD_POCKET_SLACK  # widest piece + slack
    board_pocket = Rect(w, w, board_w, full_h)
    trough_x = board_pocket.x + board_pocket.w + w  # wall gap after the board pocket
    trough_w = cfg.BOX_W - w - trough_x  # remaining width inside the right wall
    marker_trough = Rect(trough_x, w, trough_w, full_h)
    return {"board_pocket": board_pocket, "marker_trough": marker_trough}


def rect_in_box(r):
    """Return True if rectangle ``r`` lies wholly within the box footprint.

    Returns
    -------
    bool
        ``True`` when all four sides of ``r`` are inside the box (0..BOX_W × 0..BOX_L).
    """
    return r.x >= 0 and r.y >= 0 and r.x + r.w <= cfg.BOX_W and r.y + r.h <= cfg.BOX_L


def rects_disjoint(a, b):
    """Return True if rectangles ``a`` and ``b`` do not overlap in plan.

    Returns
    -------
    bool
        ``True`` when ``a`` and ``b`` share no interior area (touching edges are allowed).
    """
    return a.x + a.w <= b.x or b.x + b.w <= a.x or a.y + a.h <= b.y or b.y + b.h <= a.y


def vertical_stack_height():
    """Return the tallest stacked column height from the box floor (mm).

    Floor up to the top-tray rim, the top tray itself, then the score pad and booklet
    resting loose on top.
    """
    return (
        cfg.SMALL_TRAY_RIM_Z + cfg.TOP_TRAY_DEPTH + cfg.SCOREPAD_THICKNESS + cfg.BOOKLET_THICKNESS
    )


def folded_alt_within_bound():
    """Return True if the folded alt-stand height is within ``ALT_STAND_MAX_FOLDED_H``."""
    return d.ALT_FOLDED_H <= cfg.ALT_STAND_MAX_FOLDED_H
