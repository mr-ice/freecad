"""Tests for the box-insert constants in :mod:`config`."""

import config as cfg


def test_box_interior_dimensions():
    """Box interior dimensions match measured values."""
    assert (cfg.BOX_W, cfg.BOX_L, cfg.BOX_H) == (185.0, 265.0, 65.0)


def test_stock_matches_tile_thickness():
    """Flat cardboard stock thickness equals tile thickness."""
    assert cfg.STOCK_THICKNESS == cfg.TILE_THICKNESS


def test_cat_is_double_tile_thickness():
    """Cat token thickness is double tile thickness and count is 6."""
    assert cfg.CAT_THICKNESS == 2 * cfg.TILE_THICKNESS
    assert cfg.CAT_COUNT == 6


def test_printer_bumped_to_xl():
    """MAX_PRINTER_DIMENSION updated to XL bed size (350 mm)."""
    assert cfg.MAX_PRINTER_DIMENSION == 350.0


def test_alt_stand_max_folded_height():
    """Alt stand folded height cap matches design constraint."""
    assert cfg.ALT_STAND_MAX_FOLDED_H == 40.0


def test_component_sizes_present():
    """Component size constants are present and correct."""
    assert (cfg.CARD_W, cfg.CARD_H, cfg.CARD_DECK_THICKNESS) == (63.0, 88.0, 7.35)
    assert (cfg.MARKER_W, cfg.MARKER_H, cfg.MARKER_COUNT) == (34.0, 214.0, 4)
    assert (cfg.SCOREPAD_W, cfg.SCOREPAD_H, cfg.SCOREPAD_THICKNESS) == (103.0, 218.0, 5.5)
    assert (cfg.BOOKLET_W, cfg.BOOKLET_H, cfg.BOOKLET_THICKNESS) == (170.0, 244.0, 1.0)
