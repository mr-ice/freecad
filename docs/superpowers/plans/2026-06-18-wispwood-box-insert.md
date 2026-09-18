# Wispwood Box Insert + Alt-Stand Completion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Organize the remaining Wispwood game components into the retail box alongside the existing tray, and finish the alternate stand's upright lock — keeping every part in print and box bounds.

**Architecture:** A pure-Python layer (`config.py`, `derived.py`, `box_layout.py`, `layout_svg.py`) holds all dimensions, packing math, validators, and the SVG map — unit-tested with pytest, no FreeCAD needed. A FreeCAD layer (`box_insert.py`, `alt_stand.py`) builds geometry from those numbers and self-checks bounding boxes at build time. The `.FCMacro` wires it all into one viewable packed box.

**Tech Stack:** Python 3.9+, FreeCAD 1.0.2 `Part` workbench, `uv` for env, `pytest` for the pure layer, `ruff` for lint/format.

## Global Constraints

- FreeCAD **1.0.2** APIs only.
- Box interior: **185 (X) × 265 (Y) × 65 (Z) mm**.
- All flat cardboard stock = **2.133 mm** (`TILE_THICKNESS`).
- `MAX_PRINTER_DIMENSION = 350` (XL); every printed part's bbox ≤ this.
- Folded alt stand height ≤ **`ALT_STAND_MAX_FOLDED_H = 40` mm**.
- No magic numbers in builders — derive every offset from named constants (repo `CLAUDE.md`).
- NumPy-style docstrings on every module/public function; `ruff format` + `ruff check` clean (line-length 100).
- Do **not** modify the existing Wispwood tray/lid geometry or the alt-stand frame; only the alt-stand **upright lock** is added.
- Board pieces, markers, paw, score pad, booklet are **cardboard — not printed**. Printed parts: `SmallTray`, `TopTray`, and the re-exported alt stand.
- Run tests with: `uv run pytest "Game Insert/Wispwood/tests" -v` (scope to this dir; the repo's `CampBedFrame/test_chevron.py` imports FreeCAD and must not be collected).
- All new modules live in `Game Insert/Wispwood/`.

---

## File Structure

| File | Responsibility | FreeCAD? |
|---|---|---|
| `config.py` (modify) | All constants incl. new `--- Box insert ---` section | no |
| `derived.py` (create) | Pure shared envelope math (Wispwood outer dims, alt-stand folded envelope) from config | no |
| `box_layout.py` (create) | Component placement rects in box coords + fit/budget validators | no |
| `layout_svg.py` (create) | Emit `box-layout.svg` from `box_layout`/`config` | no |
| `box_insert.py` (create) | FreeCAD builders: small tray, top tray, box reference, `build_all` | yes |
| `alt_stand.py` (modify) | Add upright lock + folded-height assert | yes |
| `Wispwood.FCMacro` (modify) | Reload + build `box_insert`; position parts in box frame | yes |
| `tests/conftest.py` (create) | Put the Wispwood dir on `sys.path` for imports | no |
| `tests/test_*.py` (create) | pytest for the pure layer | no |
| `PROJECT.md` (modify) | Document the box insert + alt-stand status | n/a |
| `box-layout.svg` (regenerate) | The packing map | n/a |

---

## Task 1: config.py — box-insert constants, printer bump, folded bound

**Files:**
- Modify: `Game Insert/Wispwood/config.py`
- Create: `Game Insert/Wispwood/tests/conftest.py`
- Test: `Game Insert/Wispwood/tests/test_config.py`

**Interfaces:**
- Produces (module constants): `BOX_W=185.0, BOX_L=265.0, BOX_H=65.0, STOCK_THICKNESS, CAT_COUNT=6, CAT_SIZE, CAT_THICKNESS, CARD_W=63.0, CARD_H=88.0, CARD_DECK_THICKNESS=7.35, ROUND_TOKEN_DIA=34.0, ROUND_TOKEN_COUNT=8, ROUND_TOKEN_THICKNESS, MARKER_W=34.0, MARKER_H=214.0, MARKER_COUNT=4, MARKER_THICKNESS, BOARD_CENTER_PTP=135.0, BOARD_PERIM_W=86.0, BOARD_PERIM_L=190.0, BOARD_PIECE_COUNT=5, BOARD_THICKNESS, PAW_W=70.0, PAW_H=64.0, PAW_THICKNESS, SCOREPAD_W=103.0, SCOREPAD_H=218.0, SCOREPAD_THICKNESS=5.5, BOOKLET_W=170.0, BOOKLET_H=244.0, BOOKLET_THICKNESS=1.0, INSERT_WALL=2.0, INSERT_FLOOR=1.5, TOP_TRAY_DEPTH=12.0, SMALL_TRAY_RIM_Z=42.0, COMPONENT_CLEARANCE, ALT_STAND_MAX_FOLDED_H=40.0`; and `MAX_PRINTER_DIMENSION` changed to `350.0`.

- [ ] **Step 1: Create the test conftest**

Create `Game Insert/Wispwood/tests/conftest.py`:

```python
"""Put the Wispwood project dir on sys.path so tests import its modules directly."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

- [ ] **Step 2: Write the failing test**

Create `Game Insert/Wispwood/tests/test_config.py`:

```python
"""Tests for the box-insert constants in :mod:`config`."""

import config as cfg


def test_box_interior_dimensions():
    assert (cfg.BOX_W, cfg.BOX_L, cfg.BOX_H) == (185.0, 265.0, 65.0)


def test_stock_matches_tile_thickness():
    assert cfg.STOCK_THICKNESS == cfg.TILE_THICKNESS


def test_cat_is_double_tile_thickness():
    assert cfg.CAT_THICKNESS == 2 * cfg.TILE_THICKNESS
    assert cfg.CAT_COUNT == 6


def test_printer_bumped_to_xl():
    assert cfg.MAX_PRINTER_DIMENSION == 350.0


def test_alt_stand_max_folded_height():
    assert cfg.ALT_STAND_MAX_FOLDED_H == 40.0


def test_component_sizes_present():
    assert (cfg.CARD_W, cfg.CARD_H, cfg.CARD_DECK_THICKNESS) == (63.0, 88.0, 7.35)
    assert (cfg.MARKER_W, cfg.MARKER_H, cfg.MARKER_COUNT) == (34.0, 214.0, 4)
    assert (cfg.SCOREPAD_W, cfg.SCOREPAD_H, cfg.SCOREPAD_THICKNESS) == (103.0, 218.0, 5.5)
    assert (cfg.BOOKLET_W, cfg.BOOKLET_H, cfg.BOOKLET_THICKNESS) == (170.0, 244.0, 1.0)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest "Game Insert/Wispwood/tests/test_config.py" -v`
Expected: FAIL — `AttributeError: module 'config' has no attribute 'BOX_W'`.

- [ ] **Step 4: Add the constants**

In `Game Insert/Wispwood/config.py`, change the printer line:

```python
MAX_PRINTER_DIMENSION = 350.0  # build-plate limit; XL bed (MK4 : 240, XL : 350)
```

Then append a new section at the end of the file:

```python
# --- Box insert --------------------------------------------------------------
# The retail box holds the Wispwood tray plus the rest of the game. Flat cardboard
# (board pieces, markers, paw, score pad, booklet) is the same stock as the tree tiles.
BOX_W = 185.0  # box interior width (X)
BOX_L = 265.0  # box interior length (Y)
BOX_H = 65.0  # box interior height (Z)
STOCK_THICKNESS = TILE_THICKNESS  # all flat cardboard stock (~2.133)

# Cat tokens: double tree-tile thickness, stored ON EDGE (35x35 face vertical).
CAT_COUNT = 6
CAT_SIZE = TILE_SIZE  # 35 square
CAT_THICKNESS = 2 * TILE_THICKNESS  # ~4.266

# Card deck (unsleeved).
CARD_W = 63.0
CARD_H = 88.0
CARD_DECK_THICKNESS = 7.35

# Round tokens.
ROUND_TOKEN_DIA = 34.0
ROUND_TOKEN_COUNT = 8
ROUND_TOKEN_THICKNESS = TILE_THICKNESS

# Markers: tall flat standees (~6x tree-token height).
MARKER_W = 34.0
MARKER_H = 214.0
MARKER_COUNT = 4
MARKER_THICKNESS = STOCK_THICKNESS

# Board: 5 loose pieces (assembled it is 268 across, larger than the box).
BOARD_CENTER_PTP = 135.0  # center octagon, point-to-point
BOARD_PERIM_W = 86.0  # perimeter-piece bounding box (1/4 octagon)
BOARD_PERIM_L = 190.0
BOARD_PIECE_COUNT = 5
BOARD_THICKNESS = STOCK_THICKNESS

# 1st-player "paw" token.
PAW_W = 70.0
PAW_H = 64.0
PAW_THICKNESS = STOCK_THICKNESS

# Score pad and rules booklet (loose on top of the top tray).
SCOREPAD_W = 103.0
SCOREPAD_H = 218.0
SCOREPAD_THICKNESS = 5.5
BOOKLET_W = 170.0
BOOKLET_H = 244.0
BOOKLET_THICKNESS = 1.0

# Insert tray construction.
INSERT_WALL = 2.0  # well/divider wall thickness
INSERT_FLOOR = 1.5  # tray floor thickness
TOP_TRAY_DEPTH = 12.0  # top-tray height (board stack is the tallest content)
SMALL_TRAY_RIM_Z = 42.0  # bottom-tray rim, matched to the Wispwood tray top
COMPONENT_CLEARANCE = GENERAL_CLEARANCE  # per-side fit clearance for component wells

# Folded alt stand must clear under the top tray (which rests at z = 42).
ALT_STAND_MAX_FOLDED_H = 40.0
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest "Game Insert/Wispwood/tests/test_config.py" -v`
Expected: PASS (6 tests).

- [ ] **Step 6: Lint + commit**

```bash
cd "/Users/michael/3dp/freeCAD"
uv run ruff format "Game Insert/Wispwood/config.py" "Game Insert/Wispwood/tests"
uv run ruff check "Game Insert/Wispwood/config.py" "Game Insert/Wispwood/tests"
git add "Game Insert/Wispwood/config.py" "Game Insert/Wispwood/tests/conftest.py" "Game Insert/Wispwood/tests/test_config.py"
git commit -m "Wispwood: add box-insert constants, XL printer bound, folded-stand cap"
```

---

## Task 2: derived.py — pure shared envelope + alt folded envelope

**Files:**
- Create: `Game Insert/Wispwood/derived.py`
- Test: `Game Insert/Wispwood/tests/test_derived.py`

**Interfaces:**
- Consumes: `config` constants from Task 1 and the existing tile/wall/lid/alt constants.
- Produces (module constants): `OUTER_WIDTH=86.0, OUTER_LENGTH≈182.64, RAIL_Z0=39.0, LID_Z1=41.5, WALL_TOP≈42.7, ALT_SHELF_W≈92.2, ALT_CORNER_H≈21.35, ALT_FOLDED_H≈28.35, ALT_FOLDED_W≈92.2, ALT_FOLDED_L=105.0`.
- Note: these mirror the derivations inside `wispwood.py`/`alt_stand.py` (whose module bodies import FreeCAD and cannot be imported under pytest). `derived.py` recomputes them from `config` only, so the pure layer is testable. The values are guarded by `test_derived.py` so drift is caught.

- [ ] **Step 1: Write the failing test**

Create `Game Insert/Wispwood/tests/test_derived.py`:

```python
"""Tests for the pure shared geometry in :mod:`derived`."""

import math

import config as cfg
import derived as d


def test_wispwood_outer_envelope():
    assert d.OUTER_WIDTH == 86.0
    assert math.isclose(d.OUTER_LENGTH, 182.64, abs_tol=0.01)
    assert math.isclose(d.WALL_TOP, 42.7, abs_tol=0.01)


def test_alt_stand_folded_envelope():
    assert math.isclose(d.ALT_SHELF_W, 92.2, abs_tol=0.01)
    assert math.isclose(d.ALT_FOLDED_L, 105.0, abs_tol=0.01)
    # plate + raised corner posts
    assert math.isclose(d.ALT_FOLDED_H, cfg.ALT_SHELF_THICKNESS + d.ALT_CORNER_H, abs_tol=1e-9)


def test_folded_height_within_bound():
    assert d.ALT_FOLDED_H <= cfg.ALT_STAND_MAX_FOLDED_H
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest "Game Insert/Wispwood/tests/test_derived.py" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'derived'`.

- [ ] **Step 3: Create derived.py**

Create `Game Insert/Wispwood/derived.py`:

```python
"""Pure derived geometry shared between the FreeCAD modules and the box-layout layer.

These values are recomputed from :mod:`config` alone (no FreeCAD import) so the packing
math and tests can run outside FreeCAD. They mirror the in-module derivations in
``wispwood.py`` (tray outer envelope) and ``alt_stand.py`` (folded stand envelope); the
single source of the *formulas* is here, and ``tests/test_derived.py`` pins the values.

Public API
----------
Module-level constants (see below).
"""

import config as cfg

# --- Wispwood tray outer envelope (mirrors wispwood.py) ----------------------
OUTER_WIDTH = 2 * cfg.WALL_LONG + 2 * cfg.POCKET_WIDTH + cfg.DIVIDER_THICKNESS  # 86
OUTER_LENGTH = cfg.POCKET_LENGTH + 2 * cfg.WALL_END  # ~182.64
RAIL_Z0 = cfg.FLOOR_THICKNESS + cfg.POCKET_DEPTH  # lid underside = 39
LID_Z1 = RAIL_Z0 + cfg.LID_THICKNESS  # 41.5
WALL_TOP = LID_Z1 + cfg.LID_SLIDE_CLEARANCE + cfg.LID_TOP_LIP  # outer wall top ~42.7

# --- Alt stand folded envelope (mirrors alt_stand.py) ------------------------
ALT_SHELF_W = OUTER_WIDTH + 2 * cfg.ALT_SHELF_SIDE_LIP_W + 2 * cfg.ALT_SHELF_SIDE_CLEAR  # ~92.2
ALT_CORNER_H = WALL_TOP * cfg.ALT_SHELF_CORNER_H_FRAC  # raised corner posts ~21.35
ALT_FOLDED_H = cfg.ALT_SHELF_THICKNESS + ALT_CORNER_H  # plate + posts ~28.35
ALT_FOLDED_W = ALT_SHELF_W  # ~92.2
ALT_FOLDED_L = cfg.ALT_SHELF_HEIGHT + cfg.ALT_SHELF_BELOW_LIP  # 105
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest "Game Insert/Wispwood/tests/test_derived.py" -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Lint + commit**

```bash
cd "/Users/michael/3dp/freeCAD"
uv run ruff format "Game Insert/Wispwood/derived.py" "Game Insert/Wispwood/tests/test_derived.py"
uv run ruff check "Game Insert/Wispwood/derived.py" "Game Insert/Wispwood/tests/test_derived.py"
git add "Game Insert/Wispwood/derived.py" "Game Insert/Wispwood/tests/test_derived.py"
git commit -m "Wispwood: pure derived envelope module (tray + folded alt stand)"
```

---

## Task 3: box_layout.py — placement rects + validators

**Files:**
- Create: `Game Insert/Wispwood/box_layout.py`
- Test: `Game Insert/Wispwood/tests/test_box_layout.py`

**Interfaces:**
- Consumes: `config` (Task 1), `derived` (Task 2).
- Produces:
  - `Rect = namedtuple("Rect", "x y w h")` (box coords, mm; origin box front-left).
  - `bottom_regions() -> dict[str, Rect]` keys: `wispwood, alt_bay, small_tray, well_card, well_cats, well_round`. (`well_round` is the bounding square of the round well; its inscribed circle is the well.)
  - `top_regions() -> dict[str, Rect]` keys: `board_pocket, marker_trough, paw`.
  - `rect_in_box(r: Rect) -> bool` — wholly inside `0..BOX_W` × `0..BOX_L`.
  - `rects_disjoint(a: Rect, b: Rect) -> bool`.
  - `vertical_stack_height() -> float` — tallest column from floor.
  - `folded_alt_within_bound() -> bool`.

- [ ] **Step 1: Write the failing test**

Create `Game Insert/Wispwood/tests/test_box_layout.py`:

```python
"""Tests for box component placement and fit validation in :mod:`box_layout`."""

import config as cfg
import box_layout as bl


def test_all_bottom_regions_fit_in_box():
    for name, r in bl.bottom_regions().items():
        assert bl.rect_in_box(r), f"{name} {r} out of box"


def test_all_top_regions_fit_in_box():
    for name, r in bl.top_regions().items():
        assert bl.rect_in_box(r), f"{name} {r} out of box"


def test_bottom_regions_do_not_overlap():
    b = bl.bottom_regions()
    keyed = [b["wispwood"], b["alt_bay"], b["small_tray"]]
    for i in range(len(keyed)):
        for j in range(i + 1, len(keyed)):
            assert bl.rects_disjoint(keyed[i], keyed[j]), f"{keyed[i]} overlaps {keyed[j]}"


def test_board_pocket_holds_largest_piece():
    p = bl.top_regions()["board_pocket"]
    # center octagon (135) and perimeter (86 x 190) must both fit in the pocket
    assert min(p.w, p.h) >= cfg.BOARD_CENTER_PTP
    assert max(p.w, p.h) >= cfg.BOARD_PERIM_L
    assert min(p.w, p.h) >= cfg.BOARD_PERIM_W


def test_marker_trough_holds_markers():
    t = bl.top_regions()["marker_trough"]
    assert max(t.w, t.h) >= cfg.MARKER_H  # 214 along the long axis
    assert min(t.w, t.h) >= cfg.MARKER_W


def test_vertical_budget_under_box_height():
    h = bl.vertical_stack_height()
    assert h <= cfg.BOX_H, f"stack {h} exceeds box {cfg.BOX_H}"


def test_folded_alt_within_bound():
    assert bl.folded_alt_within_bound()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest "Game Insert/Wispwood/tests/test_box_layout.py" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'box_layout'`.

- [ ] **Step 3: Create box_layout.py**

Create `Game Insert/Wispwood/box_layout.py`:

```python
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
    well_cats = Rect(ix0, well_card.y + well_card.h + cfg.INSERT_WALL, cfg.CAT_SIZE + 2 * c, cats_len)
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
    """Return the top-tray placement rectangles, keyed by name.

    Returns
    -------
    dict of str to Rect
        ``board_pocket`` (loose stack of 5 pieces), ``marker_trough`` (4 markers, 214 along
        Y), ``paw`` (1st-player token recess). The score pad and booklet lie loose on top
        and are not placed here.
    """
    c = cfg.COMPONENT_CLEARANCE
    pocket_w = cfg.BOARD_CENTER_PTP + 5.0  # widest piece + slack
    pocket_h = cfg.BOARD_PERIM_L + 5.0  # longest piece + slack
    board_pocket = Rect(0.0, 0.0, pocket_w, pocket_h)

    trough_w = cfg.BOX_W - board_pocket.w
    marker_trough = Rect(board_pocket.w, 0.0, trough_w, cfg.MARKER_H + 2 * c)

    paw = Rect(0.0, board_pocket.h + cfg.INSERT_WALL, cfg.PAW_W + 2 * c, cfg.PAW_H + 2 * c)
    return {"board_pocket": board_pocket, "marker_trough": marker_trough, "paw": paw}


def rect_in_box(r):
    """Return True if rectangle ``r`` lies wholly within the box footprint."""
    return r.x >= 0 and r.y >= 0 and r.x + r.w <= cfg.BOX_W and r.y + r.h <= cfg.BOX_L


def rects_disjoint(a, b):
    """Return True if rectangles ``a`` and ``b`` do not overlap in plan."""
    return (
        a.x + a.w <= b.x or b.x + b.w <= a.x or a.y + a.h <= b.y or b.y + b.h <= a.y
    )


def vertical_stack_height():
    """Return the tallest stacked column height from the box floor (mm).

    Floor up to the top-tray rim, the top tray itself, then the score pad and booklet
    resting loose on top.
    """
    return cfg.SMALL_TRAY_RIM_Z + cfg.TOP_TRAY_DEPTH + cfg.SCOREPAD_THICKNESS + cfg.BOOKLET_THICKNESS


def folded_alt_within_bound():
    """Return True if the folded alt-stand height is within ``ALT_STAND_MAX_FOLDED_H``."""
    return d.ALT_FOLDED_H <= cfg.ALT_STAND_MAX_FOLDED_H
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest "Game Insert/Wispwood/tests/test_box_layout.py" -v`
Expected: PASS (7 tests). If `test_all_bottom_regions_fit_in_box` fails on `small_tray`, the alt bay + tray exceeded 185 wide — reduce `_BAY_GAP` or confirm `ALT_FOLDED_W`; do not silently shrink a component.

- [ ] **Step 5: Lint + commit**

```bash
cd "/Users/michael/3dp/freeCAD"
uv run ruff format "Game Insert/Wispwood/box_layout.py" "Game Insert/Wispwood/tests/test_box_layout.py"
uv run ruff check "Game Insert/Wispwood/box_layout.py" "Game Insert/Wispwood/tests/test_box_layout.py"
git add "Game Insert/Wispwood/box_layout.py" "Game Insert/Wispwood/tests/test_box_layout.py"
git commit -m "Wispwood: box_layout placement rects + fit/budget validators"
```

---

## Task 4: layout_svg.py — generate the box map

**Files:**
- Create: `Game Insert/Wispwood/layout_svg.py`
- Test: `Game Insert/Wispwood/tests/test_layout_svg.py`
- Regenerate: `Game Insert/Wispwood/box-layout.svg`

**Interfaces:**
- Consumes: `config`, `box_layout` (Tasks 1, 3).
- Produces: `generate_svg() -> str`; `write_svg(path: str) -> None`.

- [ ] **Step 1: Write the failing test**

Create `Game Insert/Wispwood/tests/test_layout_svg.py`:

```python
"""Tests for the box-layout SVG generator in :mod:`layout_svg`."""

import config as cfg
import layout_svg


def test_svg_is_to_scale_and_labeled():
    svg = layout_svg.generate_svg()
    assert svg.lstrip().startswith("<svg")
    assert f'width="{cfg.BOX_W:g}mm"' in svg
    assert f'height="{cfg.BOX_L:g}mm"' in svg
    assert f'viewBox="0 0 {cfg.BOX_W:g} {cfg.BOX_L:g}"' in svg
    assert "Wispwood tray" in svg
    assert "Card deck" in svg
    assert "Folded alt stand" in svg
    assert svg.rstrip().endswith("</svg>")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest "Game Insert/Wispwood/tests/test_layout_svg.py" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'layout_svg'`.

- [ ] **Step 3: Create layout_svg.py**

Create `Game Insert/Wispwood/layout_svg.py`:

```python
"""Generate the box-layout SVG map from :mod:`config` and :mod:`box_layout`.

The map is to scale (1 user unit = 1 mm, ``185 x 265``) so it can be printed 1:1 into the
box floor as a pack-away guide, and reviewed as a design artifact. It draws the bottom-layer
regions with labels and lists the top-layer items in a corner note.

Public API
----------
``generate_svg``, ``write_svg``.
"""

import config as cfg
import box_layout as bl

_FILLS = {
    "wispwood": "#cfe3f7",
    "alt_bay": "#d6f0d8",
    "small_tray": "#f3eddb",
}


def _rect(r, fill, cls="region"):
    return (
        f'  <rect class="{cls}" x="{r.x:g}" y="{r.y:g}" '
        f'width="{r.w:g}" height="{r.h:g}" fill="{fill}"/>\n'
    )


def _text(x, y, s, cls="lbl"):
    return f'  <text class="{cls}" x="{x:g}" y="{y:g}">{s}</text>\n'


def generate_svg():
    """Return the box-layout SVG document as a string.

    Returns
    -------
    str
        A complete, to-scale SVG (``185 x 265`` mm) of the bottom layer plus a top-layer note.
    """
    b = bl.bottom_regions()
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{cfg.BOX_W:g}mm" '
        f'height="{cfg.BOX_L:g}mm" viewBox="0 0 {cfg.BOX_W:g} {cfg.BOX_L:g}" '
        f'font-family="Helvetica, Arial, sans-serif">\n',
        "  <style>\n"
        "    .region{stroke:#333;stroke-width:0.6}\n"
        "    .well{fill:none;stroke:#666;stroke-width:0.4;stroke-dasharray:2 1.5}\n"
        "    .lbl{font-size:5px;fill:#111;text-anchor:middle}\n"
        "    .sub{font-size:3.2px;fill:#444;text-anchor:middle}\n"
        "    .note{font-size:3.6px;fill:#222}\n"
        "  </style>\n",
        f'  <rect x="0" y="0" width="{cfg.BOX_W:g}" height="{cfg.BOX_L:g}" '
        'fill="#fff" stroke="#000" stroke-width="1"/>\n',
        _rect(b["wispwood"], _FILLS["wispwood"]),
        _rect(b["alt_bay"], _FILLS["alt_bay"]),
        _rect(b["small_tray"], _FILLS["small_tray"]),
    ]
    w = b["wispwood"]
    out.append(_text(w.x + w.w / 2, w.y + w.h / 2, "Wispwood tray"))
    a = b["alt_bay"]
    out.append(_text(a.x + a.w / 2, a.y + a.h / 2, "Folded alt stand"))
    for key, label in (("well_card", "Card deck"), ("well_cats", "Cats"), ("well_round", "Round")):
        r = b[key]
        out.append(_rect(r, "none", cls="well"))
        out.append(_text(r.x + r.w / 2, r.y + r.h / 2, label, cls="sub"))
    note = [
        "ON TOP (top tray + loose):",
        "board pieces x5  |  markers x4",
        "1P paw  |  score pad  |  booklet",
    ]
    for i, line in enumerate(note):
        out.append(_text(4, cfg.BOX_L - 16 + i * 6, line, cls="note"))
    out.append("</svg>\n")
    return "".join(out)


def write_svg(path):
    """Write the generated SVG to ``path``."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(generate_svg())
```

Note: the `.note` text uses `text-anchor:start` by default (left-aligned at x=4); that is intentional for the corner block.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest "Game Insert/Wispwood/tests/test_layout_svg.py" -v`
Expected: PASS (1 test).

- [ ] **Step 5: Regenerate the committed SVG and eyeball it**

```bash
cd "/Users/michael/3dp/freeCAD/Game Insert/Wispwood"
uv run python -c "import layout_svg; layout_svg.write_svg('box-layout.svg')"
qlmanage -t -s 900 -o /tmp box-layout.svg >/dev/null 2>&1 && echo "rendered /tmp/box-layout.svg.png"
```

Open `/tmp/box-layout.svg.png` (or the SVG) and confirm the regions are to scale and labeled.

- [ ] **Step 6: Lint + commit**

```bash
cd "/Users/michael/3dp/freeCAD"
uv run ruff format "Game Insert/Wispwood/layout_svg.py" "Game Insert/Wispwood/tests/test_layout_svg.py"
uv run ruff check "Game Insert/Wispwood/layout_svg.py" "Game Insert/Wispwood/tests/test_layout_svg.py"
git add "Game Insert/Wispwood/layout_svg.py" "Game Insert/Wispwood/tests/test_layout_svg.py" "Game Insert/Wispwood/box-layout.svg"
git commit -m "Wispwood: parametric box-layout SVG generator + regenerated map"
```

---

## Task 5: box_insert.py — FreeCAD tray builders

**Files:**
- Create: `Game Insert/Wispwood/box_insert.py`

**Interfaces:**
- Consumes: `config`, `derived`, `box_layout` (Tasks 1–3); FreeCAD `Part`, `Vector`.
- Produces: `build_small_tray() -> Part.Shape`, `build_top_tray() -> Part.Shape`, `build_box_reference() -> Part.Shape`, `build_all() -> list[tuple]` (macro part tuples `(name, shape, rgb, visible, transparency)`).

**Verification note:** this module imports `Part`, so it cannot be imported under pytest. Its runnable check is `_assert_within_bed()` (raises at build time if a printed part exceeds `MAX_PRINTER_DIMENSION`) plus the macro run in Task 7. No pytest steps here.

- [ ] **Step 1: Create box_insert.py with the small tray**

Create `Game Insert/Wispwood/box_insert.py`:

```python
"""FreeCAD builders for the Wispwood box insert (bottom small tray + printed top tray).

Builds the two printed trays from the placement rectangles in :mod:`box_layout` and the
sizes in :mod:`config`, in the box coordinate frame (origin box front-left-bottom; X width,
Y length, Z up). A non-printing box-reference shell is provided for fit checking.

All offsets derive from named constants (repo ``CLAUDE.md``); no measured coordinates.

Public API
----------
``build_small_tray``, ``build_top_tray``, ``build_box_reference``, ``build_all``.
"""

import box_layout as bl
import config as cfg
import Part
from FreeCAD import Vector


def _box(x, y, z, dx, dy, dz):
    """Return an axis-aligned box solid with minimum corner ``(x, y, z)``."""
    return Part.makeBox(dx, dy, dz, Vector(x, y, z))


def _assert_within_bed(shape, name):
    """Raise AssertionError if a printed part's XY bounding box exceeds the bed limit."""
    bb = shape.BoundBox
    limit = cfg.MAX_PRINTER_DIMENSION
    assert bb.XLength <= limit and bb.YLength <= limit, (
        f"{name} {bb.XLength:.1f}x{bb.YLength:.1f} exceeds bed {limit}"
    )


def build_small_tray():
    """Build the bottom components tray: cats-on-edge slot, card well, round-token well.

    The tray outer walls rise to ``SMALL_TRAY_RIM_Z`` so the top tray rests flat across it
    and the Wispwood tray. Wells are cut to each component's depth; a finger scoop notches
    the card and round wells for access.

    Returns
    -------
    Part.Shape
        The small-tray solid, positioned in the box frame.
    """
    b = bl.bottom_regions()
    tray = b["small_tray"]
    rim = cfg.SMALL_TRAY_RIM_Z
    block = _box(tray.x, tray.y, 0.0, tray.w, tray.h, rim)

    # Card well: depth = deck thickness + access margin.
    card = b["well_card"]
    card_depth = cfg.CARD_DECK_THICKNESS + 3.0
    block = block.cut(_box(card.x, card.y, rim - card_depth, card.w, card.h, card_depth + 1.0))

    # Cats on edge: full-height slot (35 deep) so the 35 mm faces stand vertical.
    cats = b["well_cats"]
    block = block.cut(
        _box(cats.x, cats.y, rim - cfg.CAT_SIZE - 1.0, cats.w, cats.h, cfg.CAT_SIZE + 2.0)
    )

    # Round tokens: cylindrical well.
    rnd = b["well_round"]
    r = cfg.ROUND_TOKEN_DIA / 2.0 + cfg.COMPONENT_CLEARANCE
    rnd_depth = cfg.ROUND_TOKEN_COUNT * cfg.ROUND_TOKEN_THICKNESS + 3.0
    cx, cy = rnd.x + rnd.w / 2.0, rnd.y + rnd.h / 2.0
    block = block.cut(
        Part.makeCylinder(r, rnd_depth + 1.0, Vector(cx, cy, rim - rnd_depth), Vector(0, 0, 1))
    )

    # Finger scoop on the card well (a half-cylinder notch in the near wall).
    scoop_r = 12.0
    block = block.cut(
        Part.makeCylinder(
            scoop_r, card.w, Vector(card.x, card.y + card.h / 2.0, rim), Vector(1, 0, 0)
        )
    )
    _assert_within_bed(block, "SmallTray")
    return block
```

- [ ] **Step 2: Add the top tray and box reference**

Append to `Game Insert/Wispwood/box_insert.py`:

```python
def build_top_tray():
    """Build the printed top tray: board pocket, marker trough, paw recess.

    A ``TOP_TRAY_DEPTH``-tall plate over the box footprint with three pockets. The board
    pocket holds the 5 loose pieces; the marker trough holds 4 markers along Y; the paw
    recess holds the 1st-player token. Score pad and booklet lie loose on top (no pocket).

    Returns
    -------
    Part.Shape
        The top-tray solid, in the box frame (local Z 0..TOP_TRAY_DEPTH; the macro lifts it
        to ``SMALL_TRAY_RIM_Z``).
    """
    t = bl.top_regions()
    depth = cfg.TOP_TRAY_DEPTH
    floor = cfg.INSERT_FLOOR
    block = _box(0.0, 0.0, 0.0, cfg.BOX_W, cfg.BOX_L, depth)

    for key in ("board_pocket", "marker_trough", "paw"):
        r = t[key]
        block = block.cut(_box(r.x + cfg.INSERT_WALL, r.y + cfg.INSERT_WALL, floor,
                               r.w - 2 * cfg.INSERT_WALL, r.h - 2 * cfg.INSERT_WALL, depth))

    # Finger scoop into the board pocket (half-cylinder through the near long wall).
    p = t["board_pocket"]
    block = block.cut(
        Part.makeCylinder(12.0, p.w, Vector(p.x + p.w / 2.0, p.y + cfg.INSERT_WALL, depth),
                          Vector(0, -1, 0))
    )
    _assert_within_bed(block, "TopTray")
    return block


def build_box_reference():
    """Return a non-printing transparent shell of the box interior for fit checking.

    Returns
    -------
    Part.Shape
        A thin-walled open box ``BOX_W x BOX_L x BOX_H``; do not export.
    """
    wall = 1.0
    outer = _box(-wall, -wall, -wall, cfg.BOX_W + 2 * wall, cfg.BOX_L + 2 * wall, cfg.BOX_H + wall)
    inner = _box(0.0, 0.0, 0.0, cfg.BOX_W, cfg.BOX_L, cfg.BOX_H + 1.0)
    return outer.cut(inner)


def build_all():
    """Build the box-insert parts in box position, as macro part tuples.

    Returns
    -------
    list of tuple
        ``(name, shape, (r, g, b), visible, transparency)``. The top tray is lifted to
        ``SMALL_TRAY_RIM_Z``. ``BoxReference`` is a hidden, transparent fit-check shell.
    """
    top = build_top_tray()
    top.translate(Vector(0.0, 0.0, cfg.SMALL_TRAY_RIM_Z))
    return [
        ("SmallTray", build_small_tray(), (0.85, 0.75, 0.45), True, 0),
        ("TopTray", top, (0.45, 0.65, 0.85), True, 40),
        ("BoxReference", build_box_reference(), (0.6, 0.6, 0.6), True, 80),
    ]
```

- [ ] **Step 3: Lint**

```bash
cd "/Users/michael/3dp/freeCAD"
uv run ruff format "Game Insert/Wispwood/box_insert.py"
uv run ruff check "Game Insert/Wispwood/box_insert.py"
```

Expected: clean (ruff does not import FreeCAD, so it lints fine).

- [ ] **Step 4: Commit**

```bash
git add "Game Insert/Wispwood/box_insert.py"
git commit -m "Wispwood: box_insert FreeCAD builders (small tray, top tray, box ref)"
```

(Geometry is verified when the macro runs in Task 7.)

---

## Task 6: alt_stand.py — upright lock + folded-height assert

**Files:**
- Modify: `Game Insert/Wispwood/alt_stand.py`

**Interfaces:**
- Consumes: existing `alt_stand` helpers (`build_leg`, `build_base`, `_flat_cylinder`, `_box`, `BASE_CROSS_Y0/Y1`, `BASE_TOP_Y`, `LEG_LT`), `config`, and `derived` (Task 2).
- Produces: a notch in the base + a matching catch on the prop-leg T so the deployed triangle locks; `build_all()` asserts the folded height bound.

**Status:** the alt stand is **not finished** — the lock geometry below is a concrete first pass and is expected to need tuning against a print. Its check is visual-in-FreeCAD plus the folded-height assert.

- [ ] **Step 1: Add the folded-height assertion to build_all**

In `Game Insert/Wispwood/alt_stand.py`, add to the imports near the top (after `from wispwood import OUTER_WIDTH, WALL_TOP`):

```python
import derived as d
```

Then at the start of `build_all()` (right after the `if not cfg.SHOW_ALT_STAND: return []` guard), insert:

```python
    assert d.ALT_FOLDED_H <= cfg.ALT_STAND_MAX_FOLDED_H, (
        f"folded stand {d.ALT_FOLDED_H:.1f} mm exceeds box bound {cfg.ALT_STAND_MAX_FOLDED_H} mm"
    )
```

- [ ] **Step 2: Add the upright-lock notch on the base crossbar**

Add a config constant. In `config.py` (alt-stand section), append:

```python
ALT_LOCK_NOTCH_W = 9.0  # width of the T-catch notch in the base crossbar (>= ALT_LEG_T_DIA)
ALT_LOCK_NOTCH_DEPTH = 3.0  # how deep the prop-leg T seats into the base crossbar
```

Then in `alt_stand.py`, at the end of `build_base()` (just before `return base.fuse(cross)`), cut a central notch in the crossbar that the prop-leg T drops into when the triangle is deployed:

```python
    # Upright lock: a central notch in the crossbar top edge that the prop-leg T seats into,
    # fixing the deployed triangle angle. Centred on the shelf width, sized to the T.
    nx = SHELF_W / 2.0 - cfg.ALT_LOCK_NOTCH_W / 2.0
    notch = _box(
        nx,
        BASE_CROSS_Y1 - cfg.ALT_LOCK_NOTCH_DEPTH,
        -1.0,
        cfg.ALT_LOCK_NOTCH_W,
        cfg.ALT_LOCK_NOTCH_DEPTH + 1.0,
        LEG_LT + 2.0,
    )
    cross = cross.cut(notch)
```

- [ ] **Step 3: Add the matching catch on the prop-leg T**

In `alt_stand.py` `build_leg()`, after the `tcross = _flat_cylinder(...)` / `leg = leg.fuse(tcross)` lines, add a small tongue under the T centre that engages the crossbar notch:

```python
    # Upright-lock tongue: a stub under the T centre that drops into the base-crossbar notch.
    tongue_w = cfg.ALT_LOCK_NOTCH_W - cfg.ALT_HINGE_AXIAL_CLEAR
    tongue = _box(
        SHELF_W / 2.0 - tongue_w / 2.0,
        HINGE_Y + length - cfg.ALT_LEG_T_DIA / 2.0,
        SPLIT_FRONT0,
        tongue_w,
        cfg.ALT_LEG_T_DIA,
        LEG_LT - SPLIT_FRONT0,
    )
    leg = leg.fuse(tongue)
```

- [ ] **Step 4: Verify in FreeCAD**

Run `Wispwood.FCMacro` inside FreeCAD 1.0.2. Confirm:
- No exceptions (the folded-height assert passes — console shows the doc built).
- `AltBase` has a notch in the crossbar; `AltLeg`'s T has the tongue.
- With `SHOW_STAND_DEPLOYED`/the deployed ghost, the T tongue aligns with the crossbar notch (the lock seats). Note any misalignment for a tuning pass — **this is expected to iterate**.

In the FreeCAD Python console, confirm the folded envelope:

```python
import derived, config
print(derived.ALT_FOLDED_H, "<=", config.ALT_STAND_MAX_FOLDED_H)
```

Expected: `~28.35 <= 40.0`.

- [ ] **Step 5: Lint + commit**

```bash
cd "/Users/michael/3dp/freeCAD"
uv run ruff format "Game Insert/Wispwood/alt_stand.py" "Game Insert/Wispwood/config.py"
uv run ruff check "Game Insert/Wispwood/alt_stand.py" "Game Insert/Wispwood/config.py"
git add "Game Insert/Wispwood/alt_stand.py" "Game Insert/Wispwood/config.py"
git commit -m "Wispwood: alt-stand upright lock (T tongue + crossbar notch) + folded bound assert"
```

---

## Task 7: Wispwood.FCMacro — wire in box_insert

**Files:**
- Modify: `Game Insert/Wispwood/Wispwood.FCMacro`

**Interfaces:**
- Consumes: `box_insert.build_all` (Task 5), existing `wispwood.build_all`, `alt_stand.build_all`.

- [ ] **Step 1: Reload + build box_insert**

In `Wispwood.FCMacro`, after the `alt_stand` reload block, add:

```python
import box_insert  # noqa: E402

importlib.reload(box_insert)
```

And change the parts assembly line:

```python
parts = list(wispwood.build_all()) + list(alt_stand.build_all())
```

to:

```python
parts = (
    list(wispwood.build_all())
    + list(alt_stand.build_all())
    + list(box_insert.build_all())
)
```

Also reload `derived` (so its constants refresh) by adding, near the other reloads after `import config`:

```python
import derived  # noqa: E402

importlib.reload(derived)
```

- [ ] **Step 2: Run the full macro in FreeCAD and verify the packed box**

Run `Wispwood.FCMacro` in FreeCAD 1.0.2. Confirm:
- Document rebuilds with no exceptions (all build-time asserts pass).
- `SmallTray`, `TopTray`, `BoxReference` appear positioned in the box; the trays sit inside the `BoxReference` shell.
- Isometric + fit-all shows the whole packed box.

In the FreeCAD Python console, confirm everything is in bounds:

```python
import box_layout
print("vertical stack:", box_layout.vertical_stack_height(), "<=", 65)
for name, r in box_layout.bottom_regions().items():
    assert box_layout.rect_in_box(r), name
print("layout OK")
```

Expected: `vertical stack: 60.5 <= 65` and `layout OK`.

- [ ] **Step 3: Commit**

```bash
cd "/Users/michael/3dp/freeCAD"
git add "Game Insert/Wispwood/Wispwood.FCMacro"
git commit -m "Wispwood: macro builds the box insert (small + top tray, box reference)"
```

---

## Task 8: Export STLs, update PROJECT.md, final tidy

**Files:**
- Modify: `Game Insert/Wispwood/PROJECT.md`
- Create (export from FreeCAD): `Wispwood-SmallTray.stl`, `Wispwood-TopTray.stl`; re-export the alt-stand STLs.

- [ ] **Step 1: Export the printed parts**

In FreeCAD, after the macro runs, select `SmallTray` then File → Export → STL → `Game Insert/Wispwood/Wispwood-SmallTray.stl`; repeat for `TopTray` → `Wispwood-TopTray.stl`; re-export the changed alt-stand parts. Do **not** export `BoxReference`, the board/marker/paw/pad/booklet (cardboard), or the deployed ghost.

- [ ] **Step 2: Update PROJECT.md**

In `Game Insert/Wispwood/PROJECT.md`, add a `### Box insert` subsection under "New design" summarizing: two-layer packing (flat cardboard up top, chunky bits below), the small tray (cats on edge, card, round wells), the top tray (board pocket, marker trough, paw), loose score pad + booklet, the `box-layout.svg` map, and the `MAX_PRINTER_DIMENSION = 350` (XL) requirement. Update the alt-stand section to record the **upright lock** (T tongue + crossbar notch) and the **`ALT_STAND_MAX_FOLDED_H = 40` mm** folded bound. Update the Build status checklist:

```markdown
- [x] Alternate stand: upright lock (T tongue + base-crossbar notch) — first pass, needs print tuning
- [x] Box insert: config + pure layout/validators + SVG map (box_layout, layout_svg, derived)
- [x] Box insert: small tray (cats on edge, card, round-token wells) + printed top tray
- [ ] Print + verify: trays fit the box, alt-stand lock seats, folded stand ≤ 40 mm
```

- [ ] **Step 3: Run the whole pure test suite + lint**

```bash
cd "/Users/michael/3dp/freeCAD"
uv run pytest "Game Insert/Wispwood/tests" -v
uv run ruff format "Game Insert/Wispwood"
uv run ruff check "Game Insert/Wispwood"
```

Expected: all tests PASS; ruff clean.

- [ ] **Step 4: Commit**

```bash
git add "Game Insert/Wispwood/PROJECT.md" "Game Insert/Wispwood/"*.stl
git commit -m "Wispwood: export tray STLs, document box insert + alt-stand lock"
```

---

## Self-Review

**Spec coverage:**
- Two-layer architecture → Tasks 3 (layout), 5 (trays), 7 (macro). ✓
- Bottom small tray (cats on edge, card, round) → Task 5 `build_small_tray`. ✓
- Top tray (board pocket, marker trough, paw) → Task 5 `build_top_tray`. ✓
- Loose score pad + booklet → modeled as vertical-budget contributors (Task 3 `vertical_stack_height`); not printed (Global Constraints). ✓
- Alt-stand upright lock + hinge verify → Task 6. ✓
- Folded-height bound `ALT_STAND_MAX_FOLDED_H = 40` → Tasks 1 (const), 2/3 (validator), 6 (assert). ✓
- `MAX_PRINTER_DIMENSION = 350` + per-part bed check → Tasks 1, 5 (`_assert_within_bed`). ✓
- Layout SVG, generated from config → Task 4. ✓
- box reference for fit-checking → Task 5. ✓
- STL exports → Task 8. ✓
- PROJECT.md update → Task 8. ✓

**Placeholder scan:** No TBD/TODO; all code blocks complete; FreeCAD geometry is concrete (tunable, flagged where iteration is expected). ✓

**Type consistency:** `Rect(x,y,w,h)` used identically across `box_layout`, `layout_svg`, `box_insert`. `bottom_regions`/`top_regions` key names match between producer (Task 3) and consumers (Tasks 4, 5). `build_all` returns the 5-tuple the macro already iterates. `derived.ALT_FOLDED_H` referenced consistently in Tasks 2, 3, 6. ✓
