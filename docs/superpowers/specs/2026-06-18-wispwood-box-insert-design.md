# Wispwood — full box insert + alt-stand completion (design)

Date: 2026-06-18
Project: `Game Insert/Wispwood`

Two deliverables:

1. **Complete the alternate stand** — add the upright lock (prop-leg T ↔ base legs) and
   verify the two print-in-place hinges; confirm it fits **folded** in the game box.
2. **Organize the rest of the game** into the retail box, alongside the existing Wispwood
   tray, with a new bottom tray and a new top tray.

General FreeCAD rules live in the repo `CLAUDE.md`; project intent in `Game
Insert/Wispwood/PROJECT.md`. This spec is the design of record for the box insert.

## Box and components

Box interior: **185 (X, width) × 265 (Y, length) × 65 (Z, height) mm.**

All flat cardboard is the **same stock, 2.133 mm** (= tree-tile thickness `TILE_THICKNESS`).

| Component | Size (mm) | Qty | Notes |
|---|---|---|---|
| Wispwood tray (existing) | 86 × 182.6 × ~42.7 | 1 | tiles + two-part lid; used as-is |
| Alt stand (existing) | ~92.2 × 105 × ~28 folded | 1 | corner posts rise ~21 mm; stored folded |
| Cat tokens | 35 × 35 × 4.27 | 6 | double tree-tile thickness; stored **on edge** |
| 1st-player token ("paw") | 70 × 64 × 2.133 | 1 | flat cardboard |
| Board — center octagon | ~135 × 135 × 2.133 | 1 | 135 point-to-point, concave sides |
| Board — perimeter pieces | ~86 × 190 × 2.133 | 4 | identical ¼-octagon (corner-centered, 2 full sides) |
| Card deck | 63 × 88 × 7.35 | 1 | unsleeved |
| Round tokens | Ø34 × 2.133 | 8 | stack ≈ 17 mm |
| Markers | 34 × 214 × 2.133 | 4 | tall flat standees (≈ 6× tree-token height) |
| Score pad | 103 × 218 × 5.5 | 1 | full pad |
| Rules booklet | 170 × 244 × 1 | 1 | lies flat |

Assembled board would be 268 mm across — **larger than the box** — so the board is stored
only as the 5 loose flat pieces.

## Architecture — two layers, split by component type

Long flat cardboard (markers 214, board 190, score pad 218, booklet 244) only fits along
the 265 axis. Rather than fight it into the bottom, **all flat cardboard goes up top**; the
chunky 3-D bits go in a bottom tray. This keeps every well a simple shape (no diagonal
troughs, no tight-packing the card deck).

### Bottom layer (on the box floor; rim height 42 to support the top tray)

```
X 0 ────────────────────────────────── 185
    ┌────────────────────────────────┐ Y=0
    │  Wispwood tray  86 × 182.6     │      (existing, long axis along X)
    ├────────────────┬───────────────┤ Y=86
    │ SMALL TRAY     │ ALT-STAND BAY │
    │ cats(on edge)  │ reserved      │
    │ cards · rounds │ ~92×105 spot  │ Y=265
    └────────────────┴───────────────┘
```

- **Wispwood tray** placed `X[0..182.6], Y[0..86]`, unchanged.
- **Small components tray** (`X[92..185]`-ish, `Y[86..265]`): three wells —
  - **Cats**: one slot, cats **on edge** (35 × 35 face vertical), 6 in a ~26 mm row;
    well ~35 (X) × ~30 (Y) × 35 deep, finger relief.
  - **Card deck**: well ~64 × 89 × ~10 deep, finger scoop.
  - **Round tokens**: Ø35 well, ~18 deep, finger scoop.
- **Alt-stand bay** (`X[0..92], Y[86..191]`): a reserved, lightly-bounded spot holding the
  folded alt stand (~92 × 105 × ~28). Clears under the top tray at z=42.
- Small-tray outer walls rise to **z=42** so the top tray rests flat across both trays.

### Top tray (printed, one part, rests at z=42, ~12 mm deep)

```
X 0 ──────────────────────┬───── 185
┌──────────────────────┐  │ mark- │ Y=0
│  BOARD POCKET         │  │ ers   │  (4 × 34×214, stacked, 214 along Y)
│  140 × 195 (loose)    │  │ 45×218│
├──────────────┬───────┘  │       │
│ PAW 70 × 64  │          │       │ Y=265
└──────────────┴──────────┴───────┘
```

- **Board pocket**: one loose pocket ~140 × 195 (sized to the largest piece + slack); all 5
  pieces just stack in, contained — **no puzzle-shaped cutouts**. Finger scoop. Board stack
  ~10.7 mm is the tallest content → tray depth ~12 mm.
- **Marker trough**: ~45 (X) × 218 (Y) × ~10 deep, holds 4 markers stacked.
- **Paw recess**: 70 × 64 × shallow.

### Loose on top of the top tray

Score pad (103 × 218 × 5.5) then rules booklet (170 × 244 × 1) lie flat, contained by the
box walls — too large to need wells.

### Vertical budget (box = 65)

Tallest column: Wispwood/top-tray floor 42 → board 10.7 → score pad 5.5 → booklet 1 =
**≈ 59 mm < 65**, ~6 mm spare for lid clearance. Verify against the printed parts.

## Code structure

- **New `box_insert.py`** — builders for the new parts, in box coordinates:
  - `build_small_tray()` — cats-on-edge / card / round-token wells (bottom).
  - `build_top_tray()` — board pocket + marker trough + paw recess.
  - `build_box_reference()` — non-printing transparent 185×265×65 shell for fit checking
    (do not export).
  - `build_all()` — returns the macro part tuples, each translated to its box position
    (Wispwood tray at origin; small tray, alt-stand bay, top tray offset per layout).
- **`config.py`** — new section `--- Box insert ---`: box interior dims, `STOCK_THICKNESS`,
  every component size from the table above, and the derived well/tray parameters. Bump
  `MAX_PRINTER_DIMENSION` 240 → **350** (XL). No magic numbers in the builders.
- **`alt_stand.py`** — add the **upright lock**: the prop-leg T seats against the base (a
  notch/hook on the base crossbar or base-leg tops) to fix the deployed triangle angle;
  verify the prop-leg and base print-in-place hinges. Confirm the folded envelope fits the
  alt-stand bay. **This part is not finished** — expect iteration on the lock geometry and a
  re-print before it is signed off.
- **Folded-height bound:** add `ALT_STAND_MAX_FOLDED_H = 40` to `config.py` (≈2 mm under the
  42 mm top-tray underside). `alt_stand.py` computes the folded Z envelope (plate + corner
  posts) and `assert`s it `<= ALT_STAND_MAX_FOLDED_H`, so any change that would bust the box
  height fails loudly instead of silently overrunning. Current envelope ≈28 mm.
- **`Wispwood.FCMacro`** — reload + build `wispwood`, `alt_stand`, and `box_insert`; the new
  parts are positioned in the box frame so the whole packed box is viewable. Isometric +
  fit-all as today.
- **STL exports** for the two new printed parts (`SmallTray`, `TopTray`); the alt stand
  re-export after the lock. Board pieces, score pad, booklet, paw, markers are **cardboard —
  not printed**.
- **Layout SVG** (`box-layout.svg`) — a to-scale (1 mm = 1 user unit, `185 × 265`) top-down
  plan of the **bottom layer**, every region labeled, plus a note listing the top-layer
  items. Two jobs: design review, and **printing 1:1 into the box floor** as a pack-away map.
  Hand-authored now for review; in implementation, generated from `config.py` by
  `layout_svg.py` so it stays in sync with the dimensions.

## Out of scope / deliberately skipped

- No printed cradles for the board pieces, score pad, or booklet (box walls contain them).
- No puzzle-shaped board cutouts (loose pocket).
- No redesign of the Wispwood tray or the alt stand frame (only the alt stand's upright
  lock is added).

## Open verification items (confirm against a print)

- Top-tray rim resting flat on both bottom trays at z=42.
- Alt-stand folded envelope (esp. the ~21 mm corner posts) vs. the reserved bay and the
  z=42 top-tray underside — must stay `<= ALT_STAND_MAX_FOLDED_H` (40 mm).
- Cats-on-edge slot width vs. a 6-token row with finger access.
- All clearances reuse `GENERAL_CLEARANCE` unless a component needs its own.
