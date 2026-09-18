# Wispwood stand redesign — tabletop base (design B)

Date: 2026-06-20
Project: `Game Insert/Wispwood`
Supersedes the rod-frame stand currently in `stand.py` (free-floating shelf + H-base + leg).

## Problem

The current three-part rod-frame stand holds the tray at 75° but:

1. **It rocks** — the base is a narrow free-floating "H" (two legs + crossmember) that touches
   the table only on its rear legs and does not share a table plane with the shelf, so the
   contact points are not coplanar.
2. **It is front-heavy and tips forward** — the tray is a 183 mm-long, 43 mm-thick slab stood
   near-vertical. Near vertical, its centre of gravity falls at or *forward* of its bottom
   edge, so it rotates forward onto the small protruding base feet, which are the only thing
   catching it. The footprint does not straddle the CG.

The locating pegs + tabs + lip between the shelf and the tray work well and must be kept.

## Root-cause geometry

For a slab of length `L` and thickness `t` leaning at angle θ from horizontal, the CG sits, in
the horizontal (depth) direction relative to the bottom edge, at `L_cg·cosθ − t_cg·sinθ`
(`L_cg` = CG height up the slab, `t_cg` = half thickness). With this tray near vertical the
`t·sinθ` term dominates intermittently — and tiles piling toward the low (dispensing) end drop
`L_cg`, swinging the CG forward. So the CG **moves across the bottom edge depending on load**.
A stand that only braces one side of that edge is therefore unstable by construction.

**Conclusion:** the support footprint must straddle the full CG range — it must reach *forward*
of the tray face as well as back — and must be a single rigid plane on the table so it cannot
rock.

## Design

Three flat, print-in-place parts modelled in the existing flat convention (parts lie in
`Z[0, T]`, hinge axes along `X`, shelf extends `+Y`; deployed lean = `STAND_DEPLOY_ANGLE` = 75°).

### Part 1 — Base (redesigned)

An **open rounded rod rectangle** (same Ø`2·ALT_ROD_R` profile flattened to `ALT_PART_T` in Z
as the shelf), full shelf width `W`, lying flat on the table — the **sole table contact**.
Flattened rods give a flat bottom on all four sides, so the rectangle cannot rock.

- **Span (Y, deployed = forward→back):** from a **forward foot** `ALT_BASE_FWD` (~25 mm) ahead
  of the shelf hinge, back to past the **leg cradle** at `B_BASE` (~52 mm) behind the hinge,
  plus a short rear foot `ALT_BASE_FOOT`.
- **Hinge cross-rod** at the front (at the hinge axis `Y = HBY`): necked to pins / bored
  knuckles interleaving the shelf's bottom rod — the existing print-in-place pin hinge
  (`NECK_XS`, `ALT_HINGE_*`). The forward foot is the part of the base ahead of this rod.
- **Snap cradle** cross-rod at the lock line (`B_BASE` behind the hinge): a raised concave seat
  spanning the base width that the prop-leg end cylinder clicks into (reuse `_lock_cradle`
  concept, now a single full-width seat on the base back rod rather than per-H-leg seats).

This **replaces the old H base entirely**: `_base_leg`, the H crossmember, and the 47/47
base-under-shelf-crossmember split logic are deleted (the base is now a frame the shelf simply
folds on top of, so no thickness-sharing is needed there).

### Part 2 — Shelf (kept, one change)

The existing rod-frame shelf with **lip + side lips + locating pegs + tabs unchanged**
(`_tray_lip`, `_peg`, `PEG_XS`, the leg-clearance step, the deep-edge fillets). Only change:
the **crossmember moves up** so the tray bottom edge lifts to `TRAY_LIFT` = **25 mm above the
table** (absolute). Derivation:

```
CROSS_Y = HBY + (TRAY_LIFT − ZC) / sin(θ)
```

(`ZC` = hinge axis height = `ALT_PART_T/2`; the hinge axis sits at the mid-plane of the base
front rod, which rests on the table.) With current constants this gives `CROSS_Y ≈ 26.8 mm`.
The shelf hinges to the base at its bottom rod (`HBY`); the prop leg hinges on its crossmember.

### Part 3 — Prop leg (mechanism kept)

Hinged on the shelf crossmember, swings down-back, end cross-cylinder (full base width) snaps
into the base cradle to lock 75°. Lock distance recomputed from the new `CROSS_Y` via the
existing law-of-cosines:

```
S = CROSS_Y − HBY                       # hinge-to-hinge distance up the shelf
B_BASE = S·cosθ + √(L_LEG² − (S·sinθ − ALT_CRADLE_OFFSET)²)
```

The leg keeps its 47/47 share only where it crosses the base cradle rod (leg upper, base
lower), if that overlap remains in the folded state; otherwise it too is dropped.

### Stability check (75°, current constants)

- Empty loaded CG ≈ **9 mm behind** the hinge.
- Tiles-piled-low CG ≈ **10 mm forward** of the hinge.
- Footprint: forward foot at **−25 mm**, cradle at **+52 mm**.
- Both CG extremes land inside the footprint with ≥14 mm margin → no tip; one rigid flat frame
  → no rock.

The build asserts (extended from the current ones):
- `L_LEG > S·sinθ` (leg reaches the table),
- `CROSS_Y + L_LEG < SHELF_H` (leg fits folded under the top),
- `B_BASE < S + L_LEG` (non-degenerate triangle),
- **new:** `−ALT_BASE_FWD < CG_fwd` and `CG_back < B_BASE` (CG range inside the footprint), so a
  bad parameter edit fails the build instead of printing an unstable stand.

### Folding / print

- Shelf folds flat down onto the base about the front hinge; leg folds onto the shelf.
- Folded stack ≈ base `T` + shelf `T` + leg `T` + upstanding lip ≈ **37 mm** (< `ALT_STAND_MAX_FOLDED_H` = 40 mm). Verify against the actual lip height; if over, fold the shelf lip-down.
- Forward foot protrudes past the shelf bottom edge when folded — **verify the folded envelope
  still drops into the box stand bay** (`box_layout`/`box_insert`); widen the bay if needed.

## Config changes (`config.py`)

- **Add** `TRAY_LIFT = 25.0` (tray bottom-edge height above the table, deployed).
- **Add** `ALT_BASE_FWD = 25.0` (base forward-foot reach ahead of the hinge).
- **Derive** `CROSS_Y` (currently `ALT_CROSS_Y = 24.0`) from `TRAY_LIFT` in `stand.py` (or keep
  the constant but document it as `≈` the derived value; prefer deriving so the lift is one knob).
- **Remove** the now-unused H-base constants if nothing else references them: revisit
  `ALT_BASE_LEG_WIDTH`, `ALT_BASE_LEG_CLEAR`, `ALT_BASE_T_GAP`, `ALT_BASE_CROSS_*`,
  `ALT_LOCK_NOTCH_*`, and the `ALT_LEG_BASE_GAP` (base-leg spacing) — delete or repurpose.
- Keep all lip/peg/tab/hinge/clearance constants.

## Code changes (`stand.py`)

- Rewrite `build_base` to emit the open rod-rectangle base + hinge cross-rod + full-width snap
  cradle; delete `_base_leg`.
- Update `build_shelf` crossmember Y to the derived `CROSS_Y`; everything lip/peg-related is
  reused unchanged.
- Recompute `B_BASE`, `BASE_LEN`, `NATIVE_Y_MIN`, `DISPLAY_X_OFFSET`, and the `place_stand`
  offsets in `box_insert.py` for the new base extents.
- Update `build_leg` 47/47 only if the leg still overlaps the base cradle rod when folded.

## Out of scope

- The tray itself (`wispwood.py`) — the divots already match the kept pegs; no change unless the
  peg X positions move.
- The two-layer box insert, lid, layout SVG.

## Testing

- Pure layer: extend `tests/test_derived.py` (or a new `test_stand.py` for the pure stand math)
  to assert the CG-range-inside-footprint inequality and the lift→`CROSS_Y` derivation from
  config, so the stability guarantee is unit-tested without FreeCAD.
- FreeCAD: render via `Stand.FCMacro`, confirm flat footprint, deployed 25 mm lift and 75°,
  snap lock, and fold; then `Wispwood.FCMacro` for the in-box placement and bay fit.

## Open tuning points (against a print)

- Snap interference (`ALT_SNAP_CLEAR`) for click strength.
- Forward-foot reach vs. how heavily the tray loads forward.
- Folded height / bay fit if the lip stands proud past 40 mm.
