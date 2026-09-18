"""Tests for the box-layout SVG generator in :mod:`layout_svg`."""

import config as cfg
import layout_svg


def test_svg_is_to_scale_and_labeled():
    """Assert the SVG has correct dimensions, viewBox, and required region labels."""
    svg = layout_svg.generate_svg()
    assert svg.lstrip().startswith("<svg")
    assert f'width="{cfg.BOX_W:g}mm"' in svg
    assert f'height="{cfg.BOX_L:g}mm"' in svg
    assert f'viewBox="0 0 {cfg.BOX_W:g} {cfg.BOX_L:g}"' in svg
    assert "Wispwood tray" in svg
    assert "Card deck" in svg
    assert "Folded alt stand" in svg
    assert svg.rstrip().endswith("</svg>")
