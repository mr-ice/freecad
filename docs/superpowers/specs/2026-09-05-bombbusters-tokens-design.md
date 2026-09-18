# BombBusters token/card/marker geometry — design

Date: 2026-09-05

## Goal

Generate FreeCAD 1.0.2 `Part` shapes for every physical component listed in
`BombBusters/config.py` (wire tokens, info tokens, equipment tokens, info
markers, blue cut discs, mission/equipment cards) plus a translucent
reference volume for the box envelope (`config.Box`), so the user can see
everything at true scale before designing the real insert layout. This
module does not attempt a final layout — placement here is a simple
non-overlapping grid for visual reference only.

## Coordinate convention

Each config entry names its dimensions (`Height`, `Width`, `Thickness`, or
`Diameter`) and a `Z` field naming which of those dimensions is vertical in
world space. `Thickness` (or `Diameter` for `BlueCutDisc`) is always the
"stacking" dimension along which `Quantity` copies are fused into one
extruded/cylindrical shape:

- If `Z == "Thickness"` (Cards): the stack axis is vertical — a deck sitting
  flat, height = `Thickness * Quantity`.
- Otherwise (WireToken, InfoToken, EquipmentToken, BlueCutDisc): the stack
  axis is horizontal — tokens standing on edge in a row, row length =
  `Thickness * Quantity`.
- Items with no `Thickness` (`InfoMarker.Red`, `InfoMarker.Yellow`) have no
  fuse axis; `Quantity` becomes separate identical shapes placed side by
  side with a small gap instead of one fused solid.

## Module: `tokens.py`

### Generic builders

- `make_box_stack(height, width, thickness, quantity, z_dim) -> Part.Shape`
  One fused box. `z_dim` is `"Height"`, `"Width"`, or `"Thickness"` — the
  dimension placed along world Z; the stack axis is `Thickness` unless
  `z_dim == "Thickness"`, in which case the stack axis is Z itself.
- `make_cylinder_stack(diameter, thickness, quantity, z_dim) -> Part.Shape`
  One fused cylinder, same axis rule using `Diameter` in place of `Width`/
  `Height` for the cross-section.
- `make_side_by_side(build_one, quantity, pitch, axis="x") -> Part.Shape`
  Fuses `quantity` copies of a single shape (from `build_one()`), offset by
  `pitch` along `axis`. Used where there is no `Thickness` to stack along.

### Per-config builders (each returns `[(name, shape), ...]`)

- `build_wire_tokens()` — one `make_box_stack` per `WireToken.Quantity` key
  (`Red`, `Yellow`, `Blue`).
- `build_equipment_tokens()` — one `make_box_stack`, quantity 2 (the pair).
- `build_info_tokens()` — `Yellow`: one `make_box_stack` quantity 2 (a
  pair); `Number`: twelve `make_box_stack` calls of quantity 2 each (12
  discrete pairs, not one stack of 24), arranged in a small sub-grid.
- `build_info_markers()` — `Red`: `make_cylinder_stack`-style single
  cylinders via `make_side_by_side` (quantity 3, no fuse axis); `Yellow`:
  square box (`Width x Width x Height`) with a 2mm fillet on the 4 vertical
  edges, via `make_side_by_side` (quantity 4).
- `build_blue_cut_disc()` — one `make_cylinder_stack`, axis horizontal
  (`Z == "Diameter"`), length `Thickness * Quantity`.
- `build_cards()` — one `make_box_stack` each for `Mission` and
  `Equipment` (`Z == "Thickness"`, vertical deck).
- `build_box()` — a translucent box solid from `config.Box`
  (`Height x Width x Depth`, `Depth` vertical), for scale reference only —
  not part of the layout grid.

### Layout: `build_all()`

Lays out these groups left to right along X with a fixed `GAP`, each
group's internals packed with a smaller internal gap:

1. Wire token stacks (Red, Yellow, Blue side by side)
2. Equipment/Info cluster: equipment pair-stack, the Yellow info-token pair
   immediately next to it, then the 12 Number info-token pairs in a sub-grid
   — keeping info tokens visually grouped near the equipment pair
3. Info markers: Red cylinders, then Yellow filleted rods
4. Blue cut disc (single cylinder)
5. Card stacks: Mission, Equipment

Returns `[(name, shape), ...]` for everything above. `build_box()` is
returned separately (not part of the row) so the macro can render it with
transparency.

## Macro: `BombBusters.FCMacro`

Follows the existing `Wispwood.FCMacro` pattern: adds the project directory
to `sys.path`, reloads `config` and `tokens`, recreates the `BombBusters`
document from scratch, adds every shape from `tokens.build_all()` plus
`tokens.build_box()` as `Part::Feature` objects (box gets
`Transparency = 80`), recomputes, switches to isometric view, and fits all.

## Out of scope

- Real insert layout / nesting inside the box — the user will design that
  separately using these reference shapes.
- Any lid, wall, or divider geometry — this module only produces the loose
  component shapes and the box envelope for scale reference.
