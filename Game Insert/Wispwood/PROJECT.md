# Wispwood Tile Holder (custom)

A two-stack tile rack for **Wispwood**, derived from the community
*wispwood-tile-holder* by **gepesso** (reference STLs in `gepesso/`), redesigned with a
**two-part sliding/dispensing lid** and an **integrated folding stand**.

General FreeCAD coding rules live in the repository-root `CLAUDE.md`; this file captures
the design intent for this project.

## Source model (reverse-engineered from the reference STLs)

Measured from `gepesso/wispwood-tile-holder/*.stl` (binary STL bounding boxes + wall planes):

- **Outer tray:** 86 (X) × 182 (Y) × 42 (Z) mm.
- **Walls:** long sides **4 mm**, end walls **2 mm**, floor **~3 mm**, centre divider **2 mm**.
- **Two pockets:** **38.0 mm** wide × **~177 mm** long × **~39 mm** deep, split by the divider.
- **Lid:** ~80.5 × 180 × **2 mm**, slide-in.
- Original has finger scoops cut into the long walls.

## Tiles

- **160 square tiles** total, **80 per pocket** (two side-by-side stacks).
- **35 × 35 mm square, 2.133 mm thick** (measured). A stack of 80 is **~170.6 mm**.
- Fit **comfortably / low-friction** in the **38 mm** pocket (1.5 mm/side clearance),
  with ~8 mm of slack along the stack length.

## New design

### Tray
- Two side-by-side pockets, 80 tiles each, comfortable low-friction fit on the tile
  width and free sliding along the stack length.
- **Two equal-height end walls** (`END_WALL_HEIGHT`), front and back, both rising to the
  lid underside (full pocket depth).
- Lid rails, **beveled** (45° lip underside) so the tray prints without support; **rail
  friction** holds the lid in place during play and storage. The rails are open at the
  **back** (lid inserts/removes there) and **stop short of the front** by `LID_FRONT_STOP_GAP`
  (one tile thickness + 1 mm) above the inside front surface — the stop that leaves the
  dispensing gap.

### Two-part sliding / dispensing lid
- A **flat** plate (no walls closing off the columns), split into **two parts** that
  share the rails and have **beveled top sliding edges** for clean printing/entry:
  - **Large part (game use):** covers the front through **~tile 65**.
  - **Small part (storage):** seals the remaining **~65 → 80** region.
- **Reversible large lid (dispense vs. closed):** the rails stop `LID_FRONT_STOP_GAP` short
  of the inside front surface, so a full-tabbed lid always stops there, leaving a top-front
  gap. The large lid has a **cutout on one end** that strips the rail tabs over that same
  length, so inserted **cutout-end first** it passes the stop and reaches the inside front
  surface, **closing the gap** (storage). Inserted the **other way**, it stops at the rail,
  **leaving the gap open**: with the rack tilted/suspended the front tile **slides up and out
  through that gap into the operator's hand**.
- **Single-source fit:** the lid cross-section is defined once; the tray's lid slot is the
  *same* section grown by `LID_SLIDE_CLEARANCE` and cut from the tray, so the fit is exact
  and edited in one place. The slot cutter is emitted as a hidden `LidSlotCutter` object
  for inspection. The chamfer spans the full groove depth (45°) so the tray's retaining
  lip prints without support.
- **Friction tuning:** the printed lid slid well but did not stay put, so the **lid only**
  is widened in X by `LID_WIDTH_FRICTION` (0.4 mm total, 0.2 mm/side) — the slot is left
  unchanged, dropping the side clearance from 0.3 → 0.1 mm/side for a tighter friction grip
  while keeping the (good) vertical fit. Tune `LID_WIDTH_FRICTION` against the next print.

### Finger scoops
- On **both short ends** (front and back walls), one per pocket, **~80% of the pocket
  depth** (`SCOOP_DEPTH_FRACTION`) for easy tile access from either end.
- **Not on the long sides** — that area is reserved for the diagonal grip/lightening slots.

> The original **integrated folding stand** (oval pegs riding V-slots in the tray walls) is
> **retired**; it lives in `archive/folding_stand.py`. The tray is now held by the separate
> rod-frame **display stand** (`stand.py`), described below.

### Box insert — `box_insert.py`, `box_layout.py`, `derived.py`, `layout_svg.py`
The retail box (185 × 265 × 65 mm interior) holds the Wispwood tray plus the rest of the game
components. A two-layer packing keeps the chunky pieces below and the flat cardboard on top:

**Bottom layer (floor → z = 42 mm):**
- The **Wispwood tray** (86 × 183 mm, long axis along X) occupies the front-left bay.
- A **folded alt-stand bay** (left of the tray in Y) stores the triangular stand flat.
- A **small printed tray** fills the remaining bay with:
  - **Cats on edge** — 6 cat tokens (double tile thickness, 35 × 35 face) stored on edge in a
    full-height slot so the 35 mm faces stand vertical.
  - **Card well** — unsleeved card deck (63 × 88 mm) in a recess with a finger-scoop notch.
  - **Round-token well** — 8 round tokens (Ø34 mm) in a cylindrical well.

**Top layer (z = ~42.7 → ~54.7 mm):**
- A **printed top tray** (full box footprint, `TOP_TRAY_DEPTH` = 12 mm) with two pockets:
  - **Board pocket** — holds the 5 loose board pieces (widest piece `BOARD_CENTER_PTP` = 135 mm,
    longest `BOARD_PERIM_L` = 190 mm); a finger scoop across the pocket mouth aids extraction.
  - **Marker trough** — 4 flat marker standees (214 mm tall, stored along Y).
- **1st-player paw, score pad + rules booklet** lie loose on top of the top tray; no pocket needed.

**Bed size:** the trays are checked against `MAX_PRINTER_DIMENSION = 350` mm (XL bed required)
at build time via `_assert_within_bed`.

**Layout map:** `box-layout.svg` is generated from config by `layout_svg.py` and shows
every component rectangle in the box frame at scale; re-run whenever dimensions change.

### Display stand (tabletop base) — `stand.py`
A **standalone** rod-frame stand, stored folded off the tray, that holds the tray upright at
`STAND_DEPLOY_ANGLE` (75°) with its bottom (dispensing) edge lifted `TRAY_LIFT` (25 mm) above
the table. Three flat **print-in-place** parts (Ø9 rod flattened to `ALT_PART_T` = 7 mm in Z so
they print flat-bed). The FreeCAD-free **kinematics and stability live in `derived.py`**;
`stand.py` builds the geometry; `tests/test_derived.py` pins the math.

**Why this shape:** the tray is a 183 mm-long, 43 mm-thick slab. Stood near-vertical, its CG
crosses its bottom edge as tiles pile low, so it tips **forward**, not back. The fix is a wide
flat base that reaches **forward of the hinge** and is the sole table contact (see
`stand-design.svg` / `stand-options.svg`).

- **Shelf (`build_shelf`):** a continuous **rounded rod rectangle** (straight runs + quarter-
  torus corners). The bottom rod necks to **pins** at `NECK_XS` for the base hinge; a
  crossmember rod (at the derived `ALT_CROSS_Y`, set by `TRAY_LIFT`) necks for the leg hinge
  and carries the **tray lip** — deep at the shelf edges, filleted down to clear the finger
  grooves, with **locating pegs** on the lip faces (`ALT_LIP_PEG_*`, `PEG_XS`) that seat in the
  tray's front-face **divots**. *(Lip + side lips + pegs + tabs are unchanged — they work.)*
- **Base (`build_base`):** a flat **open rod rectangle** lying on the table — the **sole
  contact, so it cannot rock**. Side rails sit at `NECK_XS`; two bored **knuckles** at the
  hinge axis interleave the shelf pins (print-in-place hinge along X). It reaches a **forward
  foot** `ALT_BASE_FWD` (25 mm) ahead of the hinge — catching the loaded CG — and back to a
  **snap cradle** (`_lock_cradle`, seat clearance `ALT_SNAP_CLEAR`) past the lock line.
- **Leg (`build_leg`):** a bar continued onto its **bored hinge cylinder** (on the shelf
  crossmember pin) plus a base-width **end cylinder** that snaps into the base cradle to lock
  the angle. `ALT_LEG_LENGTH` sets the prop length (fits folded between the crossmember and the
  shelf top).
- **Computed lock:** the cradle distance `ALT_B_BASE` is solved by law of cosines from the
  hinge spacing `ALT_S_HINGES`, leg length, and `ALT_CRADLE_OFFSET` so the deployed shelf sits
  at exactly 75°.
- **Stability guarantee:** `derived.stand_is_stable()` checks the loaded CG range (empty ≈ 9 mm
  behind the hinge, tiles-low ≈ 10 mm forward) stays inside the footprint (forward foot at
  −`ALT_BASE_FWD`, cradle at +`ALT_B_BASE`). `build_all` asserts it, so a bad parameter edit
  fails the build instead of printing an unstable stand.
- **Folded envelope:** `ALT_STAND_MAX_FOLDED_H = 40` mm bounds the folded height (`ALT_FOLDED_H`
  ≈ 37.5 mm: base + shelf + upstanding lip). The forward foot protrudes past the shelf bottom
  edge when folded (intentional). Checked at build time and in `tests/test_derived.py`.

### Finger-scoop chamfers
- The scoops' **outer-face and top edges** are chamfered (`SCOOP_CHAMFER`) for finger
  comfort. Applied by geometric edge selection (best-effort) — verify in FreeCAD.

## Decisions

- Tiles **35 × 35 × 2.133 mm** (measured); pocket **38 mm** wide (1.5 mm/side clearance).
- Dispense at the **front** short end: lid slides back, the front tile slides up and out
  through the **top-front gap** (over the tall front wall) into the operator's hand, with
  the tray tilted/suspended.
- Folding stand uses **oval pegs riding V-slots** in the long side walls (not a pin
  hinge): down → swing → up to lock.
- Lid split at **tile 65**.

## Assumptions (to confirm by printing)

- Stand deployed tilt angle **~15°**; suspension height ≈ one-tile drop clearance.
- Dispensing clearances: `DISPENSE_GAP`, `LID_SLIDE_CLEARANCE`, `GATE_FLOOR_GAP`,
  `STAND_HINGE_CLEARANCE` — empirical, tune after a test print.

## Print-tuning log

- **Print 1:** lid slid freely but would not hold position; legs printed fused to the tray
  body. **Fixes:** `LID_WIDTH_FRICTION = 0.4` (tighter lid friction, slot unchanged) and
  `STAND_BODY_GAP = 0.2` (leg-to-wall clearance). Re-print to confirm both.

## Build status

- [x] Reverse-engineer reference dimensions
- [x] `PROJECT.md` spec + `config.py` parameters
- [x] Core parametric tray (pockets, walls, divider, lid rails) — `.FCMacro` + Python
- [x] Two-part sliding/dispensing lid + short-end finger scoops
- [x] Folding stand: V-slot + oval-peg legs + base bar (folded; kinematics need tuning)
- [x] Print 1 fit fixes: lid friction width + leg anti-fuse gap (config-driven)
- [ ] Re-print to confirm lid holds position and legs separate cleanly
- [x] Alternate stand (restart): triangular frame — shelf (lips, corner cups, below-lip ext)
- [x] Alternate stand: leg part (print-in-place hinge above lip + flattened-cylinder T end)
- [x] Alternate stand: base part (two legs on a bottom-edge hinge, flanking the leg)
- [x] Alternate stand: upright lock (T tongue + base-crossbar notch) — first pass, needs print tuning
- [x] Box insert: config + pure layout/validators + SVG map (box_layout, layout_svg, derived)
- [x] Box insert: small tray (cats on edge, card, round-token wells) + printed top tray
- [ ] Print + verify: trays fit the box, alt-stand lock seats, folded stand ≤ 40 mm
- [ ] Alternate stand: confirm dims against a print
