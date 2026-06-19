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
- **Not on the long sides** — that area is reserved for the folding stand.

### Folding stand
- Two **legs** (length = `STAND_LEG_LENGTH_FRAC` × tray length, currently **0.6**) with
  **rounded free ends**, centred
  vertically on the box, joined by a **front base panel** made **a little wider than the
  box front so it covers the legs**, with **chamfered gussets** at the leg/base junctions.
- Each leg carries a **substantial oval peg** (`STAND_PEG_LENGTH`×`STAND_PEG_WIDTH`) at the
  **back of the leg, equal top/bottom/back margins**, riding a slot in the wall's outer
  face (blind — does not breach the pocket).
- Slot path (hinge toward the **front**, constant-width channels, **no keyhole**):
  - **parallel arm** — horizontal, the folded peg rest, length `STAND_SLOT_ARM_LEN`;
  - **jog** — a short vertical lift of `STAND_JOG_FRAC` × peg width (≈50%) at the vertex;
  - **top arm** — short tilted lock arm, `STAND_ARM2_FRAC` × peg length (≈150%), at
    `STAND_V_ANGLE_DEG`. The jog + short arm form the lock detent.
- Slot position **derived from the leg** (margins stay equal). Modelled **folded** —
  kinematics still to be tuned against a print.
- **Anti-fuse gap:** each leg's inner face is offset from the tray's outer wall by
  `STAND_BODY_GAP` (0.2 mm) so the folded-modelled legs do not print fused to the tray
  body; the oval pegs are lengthened to bridge the gap and still seat fully in the slot.
- **Balance knob:** `STAND_LEG_LENGTH_FRAC` is the single parameter for the deployed
  balance — longer legs move the centre of gravity **up and back**. The entire slot path is
  derived from the leg length, so the leg and slot move together and stay aligned (the
  peg's back margin is constant); it stays in-bounds through ~0.7.
- **Deployed ghost (display-only):** with `SHOW_STAND_DEPLOYED`, a **non-printing**
  `StandDeployed` copy is shown at the lock (second) position for visual comparison. Because
  the oval peg's major axis follows the slot-channel direction, the lock pose is the stand
  rotated by `STAND_V_ANGLE_DEG` about the peg axis and carried to the seated lock position
  — one detent radius past `STAND_LOCK` (the arm's centreline end) so the peg sits at the
  rounded top of the slot. Do not export it.

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

**Top layer (z = 42 → ~54 mm):**
- A **printed top tray** (full box footprint, `TOP_TRAY_DEPTH` = 12 mm) with three pockets:
  - **Board pocket** — holds the 5 loose board pieces (widest piece `BOARD_CENTER_PTP` = 135 mm,
    longest `BOARD_PERIM_L` = 190 mm); a finger scoop aids extraction.
  - **Marker trough** — 4 flat marker standees (214 mm tall, stored along Y).
  - **Paw recess** — 1st-player paw token (70 × 64 mm).
- **Score pad + rules booklet** lie loose on top of the top tray; no pocket needed.

**Bed size:** the trays are checked against `MAX_PRINTER_DIMENSION = 350` mm (XL bed required)
at build time via `_assert_within_bed`.

**Layout map:** `box-layout.svg` is generated from config by `layout_svg.py` and shows
every component rectangle in the box frame at scale; re-run whenever dimensions change.

### Alternate stand (separate, triangular frame) — `alt_stand.py`
The integrated stand is too big to fit in the box on the tray, so this is a **standalone**
stand stored off the tray. It is a **triangular frame** of three parts — the **shelf** (holds
the tray), the **base** (on the table), and the **leg** (props them apart) — built up one part
at a time.
- **Shelf:** a **rounded-rectangle** plate, `ALT_SHELF_THICKNESS` (2 mm) thick,
  `ALT_SHELF_WIDTH_OVER_TRAY` (3 mm) wider than the tray, `ALT_SHELF_HEIGHT` (~80 mm) tall. On
  the top surface: a **cross-lip** across the bottom that the tray rests against, and two
  **side lips** above it on the outer edges (`ALT_SHELF_SIDE_LIP_W` 1.4 mm × `…_H` 3 mm) that
  steady the tray — their inner gap clears the 86 mm tray by 0.1 mm/side. The two bottom
  **corners are raised** to `ALT_SHELF_CORNER_H_FRAC` (~½ the tray height, ≈21 mm) and
  **filleted** (r ≈ 18 mm) back down to the cross-lip and side-lips, making a deeper cup that
  cradles the tray's bottom corners. The unused centre — of both the tray region and the
  below-lip extension — is cut out, leaving a **border frame** (`ALT_SHELF_BORDER`).
- **Below-lip extension:** the frame extends `ALT_SHELF_BELOW_LIP` (~15 mm, slant) below the
  lip toward the base. Deployed at 15° off vertical that lifts the top of the lip ~17 mm so
  the tray's front-top edge lands ~28 mm off the table (`front_edge = lip_vert + H_tray·sin15`).
- **Stocky frame:** plate `ALT_SHELF_THICKNESS` 4 mm, border `ALT_SHELF_BORDER` 10 mm; side
  lips widened to 3 mm (matched to the cross-lip), so the shelf width is now derived as
  tray + 2 side lips + 2 `ALT_SHELF_SIDE_CLEAR` = 92.2 mm (86.2 mm inner gap for the tray).
- **Stocky base:** plate `ALT_SHELF_THICKNESS` now **7 mm** (not counting lips), so the leg
  nests fully inside it.
- **Leg (`build_leg`):** a prop bar that nests **fully inside the 7 mm** plate's central
  opening (recessed, free of all structure) and joins the plate by a **print-in-place hinge**
  just above the cross-lip — interleaved knuckles (`ALT_HINGE_SEGMENTS`, plate at the ends) on
  a single pin. The knuckle body is **Ø7 mm** (`ALT_HINGE_R`, fills the full plate thickness)
  on a **Ø3 mm** pin (`ALT_HINGE_PIN_R`, part of the plate); leg knuckles bored
  `ALT_HINGE_PIN_CLEAR` (0.4 mm) over it → ~1.6 mm walls, with `ALT_HINGE_AXIAL_CLEAR` between
  knuckles — all gaps are the print clearances that keep it free. The far end is a **flattened cylinder forming a T** (`ALT_LEG_T_*`) for
  locking upright. Shown as `AltLeg`.
- **Base (`build_base`):** the foot — **two legs** on print-in-place hinges **centred in the
  shelf's bottom border** (knuckles subdivided to match the prop-leg hinge width), running up
  through the shelf flanking the prop leg (`ALT_BASE_LEG_WIDTH`, `ALT_BASE_LEG_CLEAR`),
  **stopping short of the T** (`ALT_BASE_T_GAP`), joined by a **high crossbar**
  (`ALT_BASE_CROSS_INSET` below the leg tops). **Shared-thickness (~47/47) cuts** (`ALT_SPLIT_GAP`
  0.4 mm): where a leg crosses the lip-band cross it keeps the back ~47% and the shelf keeps the
  front (cross-lip support); where the crossbar passes under the prop leg it takes the back ~47%
  and the prop leg the front. Shown as `AltBase`. The **upright lock** (T ↔ base) is next.
- **Upright lock:** when the triangle is deployed, the prop-leg's **T tongue** (a stub under
  the T crossbar centre, width = `ALT_LOCK_NOTCH_W` − clearance) drops into a matching
  **notch in the base crossbar** (`ALT_LOCK_NOTCH_W` × `ALT_LOCK_NOTCH_DEPTH`), fixing the
  deployed angle. The 47/47 split at the crossbar/leg overlap keeps both parts print-free. Lock
  geometry is first-pass; print tuning expected.
- **Folded envelope:** `ALT_STAND_MAX_FOLDED_H = 40` mm constrains the folded stand height so
  it clears under the top tray (which rests at z = 42 mm with a 2 mm margin). Checked at build
  time; current computed folded height (`ALT_FOLDED_H`) is well within the bound.

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
