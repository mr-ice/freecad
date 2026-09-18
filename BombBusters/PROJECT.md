# BombBusters

Reference geometry for the **BombBusters** board game's components: wire tokens, info
tokens, equipment tokens, info markers, blue cut discs, and mission/equipment cards,
plus the game box's usable interior volume. General FreeCAD coding rules live in the
repository-root `CLAUDE.md`; this file captures the design intent for this project.

`tokens.py` builds one shape per component group (fused stacks where items nest, or
side-by-side copies where they don't) and lays them out in a simple non-overlapping
grid next to a translucent box envelope, purely so the true-scale shapes can be
inspected before designing the real insert layout -- see
`docs/superpowers/specs/2026-09-05-bombbusters-tokens-design.md` for the geometry
design. `BombBusters.FCMacro` builds it.

## Current design parameters

Defined in `config.py` (millimeters), see that file for the authoritative values:

- **WireToken:** `45 x 14 x 3.15`, quantities Red 11 / Yellow 11 / Blue 48
- **InfoToken:** `21.25 x 14 x 3.15`, quantities Number 24 / Yellow 2
- **EquipmentToken:** `21.15 x 29.75 x 3.15`, quantity 2
- **InfoMarker:** Red cylinder diameter 6 x height 12 (qty 3); Yellow square rod
  width 6 x height 12 (qty 4)
- **BlueCutDisc:** diameter 19.1 x thickness 1.6, quantity 12
- **Card:** Mission `110.3 x 75 x 0.325` (qty 10); Equipment `88 x 63 x 7.1/22` (qty 35)
- **Box:** interior space `260 x 91.4 x 40`

This is a reference-geometry project, not an insert design -- no layout, walls, or
lid geometry is built here.
