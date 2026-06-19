"""Tests for box component placement and fit validation in :mod:`box_layout`."""

import box_layout as bl
import config as cfg


def test_all_bottom_regions_fit_in_box():
    """Assert every bottom region lies wholly within the box footprint."""
    for name, r in bl.bottom_regions().items():
        assert bl.rect_in_box(r), f"{name} {r} out of box"


def test_all_top_regions_fit_in_box():
    """Assert every top region lies wholly within the box footprint."""
    for name, r in bl.top_regions().items():
        assert bl.rect_in_box(r), f"{name} {r} out of box"


def test_bottom_regions_do_not_overlap():
    """Assert the three main bottom bays are mutually non-overlapping."""
    b = bl.bottom_regions()
    keyed = [b["wispwood"], b["alt_bay"], b["small_tray"]]
    for i in range(len(keyed)):
        for j in range(i + 1, len(keyed)):
            assert bl.rects_disjoint(keyed[i], keyed[j]), f"{keyed[i]} overlaps {keyed[j]}"


def test_board_pocket_holds_largest_piece():
    """Assert the board pocket accommodates the largest board piece."""
    p = bl.top_regions()["board_pocket"]
    # center octagon (135) and perimeter (86 x 190) must both fit in the pocket
    assert min(p.w, p.h) >= cfg.BOARD_CENTER_PTP
    assert max(p.w, p.h) >= cfg.BOARD_PERIM_L
    assert min(p.w, p.h) >= cfg.BOARD_PERIM_W


def test_marker_trough_holds_markers():
    """Assert the marker trough is wide/tall enough for the markers."""
    t = bl.top_regions()["marker_trough"]
    assert max(t.w, t.h) >= cfg.MARKER_H  # 214 along the long axis
    assert min(t.w, t.h) >= cfg.MARKER_W


def test_vertical_budget_under_box_height():
    """Assert the tallest stacked column does not exceed the box interior height."""
    h = bl.vertical_stack_height()
    assert h <= cfg.BOX_H, f"stack {h} exceeds box {cfg.BOX_H}"


def test_folded_alt_within_bound():
    """Assert the folded alt-stand height fits under the top tray."""
    assert bl.folded_alt_within_bound()


def _within(inner, outer):
    """Return True if rect ``inner`` lies wholly within rect ``outer``."""
    return (
        inner.x >= outer.x
        and inner.y >= outer.y
        and inner.x + inner.w <= outer.x + outer.w
        and inner.y + inner.h <= outer.y + outer.h
    )


def test_wells_inside_small_tray():
    """Each component well is contained within the small-tray footprint."""
    b = bl.bottom_regions()
    tray = b["small_tray"]
    for key in ("well_card", "well_cats", "well_round"):
        assert _within(b[key], tray), f"{key} {b[key]} not inside small_tray {tray}"
