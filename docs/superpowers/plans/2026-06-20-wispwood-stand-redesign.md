# Wispwood Stand Redesign (tabletop base) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the rocking, front-tipping rod-frame stand with a tabletop-base design: a wide flat rod-frame base that reaches forward of the hinge and is the sole table contact, holding the tray at 75° with its bottom edge lifted 25 mm.

**Architecture:** The FreeCAD-free pure kinematics (lift→crossmember, lock distance, CG-vs-footprint stability, folded envelope) move into `derived.py` and are unit-tested with pytest. `stand.py` (FreeCAD `Part`) consumes those constants and builds the three flat parts; its geometry is verified by rendering `Stand.FCMacro` / `Wispwood.FCMacro` in FreeCAD 1.0.2.

**Tech Stack:** Python 3, FreeCAD 1.0.2 `Part` workbench, pytest, ruff (line-length 100, NumPy docstrings).

## Global Constraints

- FreeCAD 1.0.2 APIs only; geometry must be printable (flat-bed, self-supporting overhangs at 0.2 mm layers).
- All offsets derived from named constants in `config.py` — no measured/hard-coded coordinates (repo `CLAUDE.md`).
- Pure math lives in `derived.py` (no `import Part`/FreeCAD); only `stand.py`/`box_insert.py` import FreeCAD.
- Lint/format: `uv run ruff format` then `uv run ruff check` (line-length 100, NumPy docstrings) must pass.
- Run tests with: `uv run pytest "Game Insert/Wispwood/tests" -q` (cwd = repo root).
- Deploy angle `STAND_DEPLOY_ANGLE = 75°`; tray bottom-edge lift `TRAY_LIFT = 25 mm` (absolute, above table).
- Keep the shelf lip + side lips + locating pegs + tabs exactly as they are.
- Folded stand height must stay `<= ALT_STAND_MAX_FOLDED_H` (40 mm).

---

### Task 1: Pure stand kinematics + stability in `derived.py` (TDD)

Move the stand's pure math out of `stand.py` into `derived.py` so it is FreeCAD-free and unit-tested. Add config knobs; remove the old hard-coded crossmember.

**Files:**
- Modify: `Game Insert/Wispwood/config.py` (add `TRAY_LIFT`, `ALT_BASE_FWD`, `ALT_CG_LOW_OFFSET`; remove `ALT_CROSS_Y`)
- Modify: `Game Insert/Wispwood/derived.py` (add stand kinematics + stability + new folded envelope)
- Test: `Game Insert/Wispwood/tests/test_derived.py`

**Interfaces:**
- Produces (in `derived.py`), all FreeCAD-free:
  - `ALT_THETA: float` — `math.radians(cfg.STAND_DEPLOY_ANGLE)`
  - `ALT_HBY: float` = `cfg.ALT_ROD_R`; `ALT_ZC: float` = `cfg.ALT_PART_T / 2`
  - `ALT_CROSS_Y: float` = `ALT_HBY + (cfg.TRAY_LIFT - ALT_ZC) / sin(ALT_THETA)`
  - `ALT_S_HINGES: float` = `ALT_CROSS_Y - ALT_HBY`
  - `ALT_B_BASE: float` = `ALT_S_HINGES*cos(θ) + sqrt(L² − (ALT_S_HINGES*sin(θ) − cfg.ALT_CRADLE_OFFSET)²)` with `L = cfg.ALT_LEG_LENGTH`
  - `ALT_LIP_EDGE_H: float` = `cfg.ALT_LIP_EDGE_FRAC * WALL_TOP`
  - `cg_offset(l_cg, t_cg) -> float` — horizontal depth of CG behind the hinge: `l_cg*cos(θ) − t_cg*sin(θ)` (positive = behind/back)
  - `ALT_T_CG: float` = `WALL_TOP / 2` (tray half-thickness off the shelf face)
  - `ALT_CG_BACK_EMPTY: float` = `cg_offset(ALT_S_HINGES + OUTER_LENGTH/2, ALT_T_CG)`
  - `ALT_CG_FWD_LOW: float` = `cg_offset(ALT_S_HINGES + cfg.ALT_CG_LOW_OFFSET, ALT_T_CG)`
  - `stand_is_stable() -> bool` — `(-cfg.ALT_BASE_FWD) < ALT_CG_FWD_LOW and ALT_CG_BACK_EMPTY < ALT_B_BASE`
  - New folded envelope (replace the old `ALT_FOLDED_*`):
    - `ALT_FOLDED_W` = `ALT_SHELF_W`
    - `ALT_FOLDED_L` = `cfg.ALT_BASE_FWD + max(cfg.ALT_SHELF_HEIGHT, ALT_B_BASE + cfg.ALT_BASE_FOOT)`
    - `ALT_FOLDED_H` = `cfg.ALT_PART_T + cfg.ALT_PART_T + ALT_LIP_EDGE_H` (base + shelf + lip standing proud; the leg nests in the open shelf frame and adds no layer)

- [ ] **Step 1: Add config knobs and remove the old crossmember constant**

In `config.py`, in the alt-stand section, replace the line `ALT_CROSS_Y = 24.0  # ...` with nothing (delete it) and add near the lip/lift constants:

```python
TRAY_LIFT = 25.0  # tray bottom (dispensing) edge height above the table, deployed (absolute)
ALT_BASE_FWD = 25.0  # base forward-foot reach ahead of the shelf hinge (catches the loaded CG)
ALT_CG_LOW_OFFSET = 20.0  # assumed CG height above the lip when tiles pile low (worst forward case)
```

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_derived.py`:

```python
def test_stand_lift_sets_crossmember():
    """The crossmember Y derives from TRAY_LIFT so the tray bottom edge sits at that height."""
    theta = math.radians(cfg.STAND_DEPLOY_ANGLE)
    lip_z = d.ALT_ZC + (d.ALT_CROSS_Y - d.ALT_HBY) * math.sin(theta)
    assert math.isclose(lip_z, cfg.TRAY_LIFT, abs_tol=1e-9)


def test_stand_lock_distance_law_of_cosines():
    """B_BASE matches the law-of-cosines lock formula from the hinge spacing and leg length."""
    theta = math.radians(cfg.STAND_DEPLOY_ANGLE)
    s = d.ALT_S_HINGES
    expected = s * math.cos(theta) + math.sqrt(
        cfg.ALT_LEG_LENGTH**2 - (s * math.sin(theta) - cfg.ALT_CRADLE_OFFSET) ** 2
    )
    assert math.isclose(d.ALT_B_BASE, expected, abs_tol=1e-9)
    assert d.ALT_B_BASE < s + cfg.ALT_LEG_LENGTH  # non-degenerate triangle


def test_stand_cg_within_footprint():
    """Empty CG sits behind the hinge; loaded-low CG swings forward; both inside the base."""
    assert d.ALT_CG_BACK_EMPTY > 0  # empty: behind the hinge
    assert d.ALT_CG_FWD_LOW < 0  # loaded low: forward of the hinge
    assert d.ALT_CG_FWD_LOW > -cfg.ALT_BASE_FWD  # but not past the forward foot
    assert d.ALT_CG_BACK_EMPTY < d.ALT_B_BASE  # and not past the cradle
    assert d.stand_is_stable()


def test_folded_height_within_bound():
    """Folded stand height stays under the bay limit (overrides the prior assertion)."""
    assert d.ALT_FOLDED_H <= cfg.ALT_STAND_MAX_FOLDED_H
```

Delete the **old** `test_folded_height_within_bound` and `test_alt_stand_folded_envelope` bodies that reference the removed `ALT_CORNER_H`/`ALT_FOLDED_*` formulas (the new folded envelope no longer has corner posts). Keep `test_wispwood_outer_envelope`.

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest "Game Insert/Wispwood/tests/test_derived.py" -q`
Expected: FAIL — `AttributeError: module 'derived' has no attribute 'ALT_ZC'` (and friends).

- [ ] **Step 4: Implement the kinematics in `derived.py`**

Add `import math` at the top (after the module docstring). Replace the `# --- Alt stand folded envelope ---` block with:

```python
import math

# --- Stand kinematics (FreeCAD-free; consumed by stand.py) -------------------
ALT_THETA = math.radians(cfg.STAND_DEPLOY_ANGLE)
ALT_HBY = cfg.ALT_ROD_R  # bottom-rod (base hinge) axis Y
ALT_ZC = cfg.ALT_PART_T / 2.0  # hinge axis height = part mid-plane (base rests on the table)
ALT_SHELF_W = OUTER_WIDTH + 2 * cfg.ALT_SHELF_SIDE_LIP_W + 2 * cfg.ALT_SHELF_SIDE_CLEAR  # ~92.2

# Crossmember Y derived so the tray bottom edge lifts to TRAY_LIFT above the table.
ALT_CROSS_Y = ALT_HBY + (cfg.TRAY_LIFT - ALT_ZC) / math.sin(ALT_THETA)
ALT_S_HINGES = ALT_CROSS_Y - ALT_HBY  # hinge-to-hinge distance up the shelf

# Lock distance: deployed triangle, cradle seat ALT_CRADLE_OFFSET above the base centreline.
ALT_B_BASE = ALT_S_HINGES * math.cos(ALT_THETA) + math.sqrt(
    cfg.ALT_LEG_LENGTH**2 - (ALT_S_HINGES * math.sin(ALT_THETA) - cfg.ALT_CRADLE_OFFSET) ** 2
)

ALT_LIP_EDGE_H = cfg.ALT_LIP_EDGE_FRAC * WALL_TOP  # deep-lip height at the shelf edges


def cg_offset(l_cg, t_cg):
    """Return the horizontal depth of a slab CG behind the bottom hinge (mm; +behind/back).

    Parameters
    ----------
    l_cg : float
        CG height measured up the shelf from the hinge (mm).
    t_cg : float
        CG offset off the shelf front face (half the tray thickness) (mm).

    Returns
    -------
    float
        Horizontal (depth) position relative to the hinge; positive is back, negative forward.
    """
    return l_cg * math.cos(ALT_THETA) - t_cg * math.sin(ALT_THETA)


ALT_T_CG = WALL_TOP / 2.0  # tray half-thickness off the shelf face
ALT_CG_BACK_EMPTY = cg_offset(ALT_S_HINGES + OUTER_LENGTH / 2.0, ALT_T_CG)
ALT_CG_FWD_LOW = cg_offset(ALT_S_HINGES + cfg.ALT_CG_LOW_OFFSET, ALT_T_CG)


def stand_is_stable():
    """Return True if the loaded CG range stays inside the base footprint (no tip)."""
    return (-cfg.ALT_BASE_FWD) < ALT_CG_FWD_LOW and ALT_CG_BACK_EMPTY < ALT_B_BASE


# --- Folded envelope (tabletop-base design) ---------------------------------
ALT_FOLDED_W = ALT_SHELF_W
ALT_FOLDED_L = cfg.ALT_BASE_FWD + max(cfg.ALT_SHELF_HEIGHT, ALT_B_BASE + cfg.ALT_BASE_FOOT)
ALT_FOLDED_H = cfg.ALT_PART_T + cfg.ALT_PART_T + ALT_LIP_EDGE_H  # base + shelf + lip proud
```

Remove the now-dead `ALT_CORNER_H` line and update the module docstring's reference to `alt_stand.py` → `stand.py`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest "Game Insert/Wispwood/tests/test_derived.py" -q`
Expected: PASS (all tests).

- [ ] **Step 6: Lint, format, full test run**

Run: `cd "Game Insert/Wispwood" && uv run ruff format config.py derived.py tests/test_derived.py && uv run ruff check config.py derived.py tests/test_derived.py`
Then: `uv run pytest "Game Insert/Wispwood/tests" -q`
Expected: ruff clean; all tests pass.

- [ ] **Step 7: Commit**

```bash
git add "Game Insert/Wispwood/config.py" "Game Insert/Wispwood/derived.py" "Game Insert/Wispwood/tests/test_derived.py"
git commit -m "Wispwood stand: pure kinematics + stability in derived.py (TDD)"
```

---

### Task 2: Rebuild the base as an open rod rectangle in `stand.py`

Replace the H-base with a flat rod-frame rectangle: forward foot ahead of the hinge, a hinge cross-rod interleaving the shelf bottom rod, and a full-width snap cradle on the back. Delete `_base_leg` and the H-base 47/47 logic. Consume the Task-1 kinematics from `derived`.

**Files:**
- Modify: `Game Insert/Wispwood/stand.py` (module constants → use `d.*`; rewrite `build_base`; delete `_base_leg`; rewrite `_lock_cradle` as full-width; keep `build_shelf`/`build_leg` for Task 3)

**Interfaces:**
- Consumes from `derived`: `ALT_CROSS_Y`, `ALT_S_HINGES`, `ALT_B_BASE`, `ALT_SHELF_W`, `ALT_LIP_EDGE_H`, `stand_is_stable`.
- Produces: `build_base() -> Part.Shape`; module constants `W`, `CROSS_Y`, `B_BASE`, `BASE_LEN`, `NATIVE_Y_MIN`, `DISPLAY_X_OFFSET`, `PEG_XS` (kept names for `box_insert`).

- [ ] **Step 1: Repoint stand.py module constants to `derived`**

In `stand.py`, replace the local kinematics derivations with the `derived` values:

```python
W = d.ALT_SHELF_W
ROD_R = cfg.ALT_ROD_R
T = cfg.ALT_PART_T
ZC = d.ALT_ZC
HBY = d.ALT_HBY
SHELF_H = cfg.ALT_SHELF_HEIGHT
CR = cfg.ALT_FRAME_CORNER_R
CROSS_Y = d.ALT_CROSS_Y
PIN_R = cfg.ALT_BARREL_NECK_R
BORE = PIN_R + cfg.ALT_HINGE_PIN_CLEAR
ACLR = cfg.ALT_HINGE_AXIAL_CLEAR
LEG_W = cfg.ALT_LEG_WIDTH
L_LEG = cfg.ALT_LEG_LENGTH
LEG_CX = W / 2.0
B_BASE = d.ALT_B_BASE
X_LOCK = B_BASE
BASE_CROSS_Y = HBY + B_BASE  # cradle line, from the bottom hinge
LIP_EDGE_H = d.ALT_LIP_EDGE_H
FWD = cfg.ALT_BASE_FWD  # forward-foot reach ahead of the hinge
BASE_FRONT_Y = HBY - FWD  # forward foot tip (-Y), out past the shelf bottom edge
BASE_BACK_Y = BASE_CROSS_Y + cfg.ALT_BASE_FOOT  # rear foot, past the cradle
BASE_LEN = BASE_BACK_Y - BASE_FRONT_Y
NATIVE_Y_MIN = BASE_FRONT_Y  # most-forward point of the folded stand
DISPLAY_X_OFFSET = W + 30.0
PEG_XS = (cfg.ALT_PEG_INSET, W - cfg.ALT_PEG_INSET)
```

Delete the now-unused `_BL_OFFSET`, `NECK_XS`, `BASE_X0/BASE_X1`, `D_LEG`, `_THETA`, `S_HINGES`, `_HC`, `FOOT_EXT`, `BASE_CROSS_W` (re-add any still needed by `build_leg` locally in Task 3), and the `_TRAY_OFFSET` dead line.

- [ ] **Step 2: Rewrite `_lock_cradle` as a single full-width seat**

```python
def _lock_cradle():
    """Return a full-width snap cradle on the base back: raised concave seat + ramp gusset.

    A boss spanning the base width with a concave seat (open toward the hinge) that the prop
    leg's base-width end cylinder clicks into, ramped on the foot side down to the base surface.
    """
    x0 = ROD_R
    span = W - 2 * ROD_R
    boss = _box(x0, BASE_CROSS_Y - ROD_R - 1.0, T, span, 2 * ROD_R + 2.0, ROD_R)
    seat = _xcyl(ROD_R + cfg.ALT_SNAP_CLEAR, span + 2.0, x0 - 1.0, BASE_CROSS_Y, T + ROD_R)
    cradle = boss.cut(seat)
    ramp_y0 = BASE_CROSS_Y + ROD_R + 1.0
    ramp = _yz_prism([(ramp_y0, T), (BASE_BACK_Y, T), (ramp_y0, T + ROD_R)], x0, span)
    return cradle.fuse(ramp)
```

- [ ] **Step 3: Rewrite `build_base` as an open rod rectangle**

```python
def build_base():
    """Build the base: a flat open rod-frame rectangle + hinge cross-rod + full-width cradle.

    Lies flat on the table (the sole table contact). The front rod runs along the hinge axis
    and necks to a pin so the shelf bottom rod's knuckles ride it; the frame extends a forward
    foot ahead of the hinge and back past the cradle. The wide flat rectangle cannot rock.

    Returns
    -------
    Part.Shape
        The base solid (flat orientation).
    """
    run = (W - ROD_R - CR) - (ROD_R + CR)
    # Side rails span the full base length (front foot to back foot).
    left = _ycyl(ROD_R, BASE_BACK_Y - BASE_FRONT_Y, ROD_R, BASE_FRONT_Y, ZC)
    right = _ycyl(ROD_R, BASE_BACK_Y - BASE_FRONT_Y, W - ROD_R, BASE_FRONT_Y, ZC)
    front = _xcyl(ROD_R, run, ROD_R + CR, BASE_FRONT_Y + ROD_R, ZC)  # forward-foot rod
    back = _xcyl(ROD_R, run, ROD_R + CR, BASE_BACK_Y - ROD_R, ZC)  # rear-foot rod
    base = left.fuse(right).fuse(front).fuse(back)
    base = base.fuse(_corner(ROD_R + CR, BASE_FRONT_Y + ROD_R, 180.0))
    base = base.fuse(_corner(W - ROD_R - CR, BASE_FRONT_Y + ROD_R, 270.0))
    base = base.fuse(_corner(W - ROD_R - CR, BASE_BACK_Y - ROD_R, 0.0))
    base = base.fuse(_corner(ROD_R + CR, BASE_BACK_Y - ROD_R, 90.0))
    # Hinge cross-rod on the axis (Y = HBY): knuckles that ride the shelf bottom-rod pins.
    hinge = _necked_rod(HBY, ROD_R, W - ROD_R, [(LEG_CX, 0.0)])  # full rod, knuckles bored below
    hinge = hinge.cut(_xcyl(BORE, W + 2.0, -1.0, HBY, ZC))  # bored for the shelf pins
    base = base.fuse(hinge)
    base = _flat(base)
    base = base.fuse(_lock_cradle())
    return base
```

Note: the shelf bottom rod (Task 3) keeps full-radius collars where this base hinge rod is bored, and necks to `PIN_R` pins where the base knuckles sit — they interleave along the same axis `Y = HBY`. (If the single-knuckle interleave proves too coarse on a print, subdivide into multiple `_necked_rod` bands later; not needed for the first render.)

- [ ] **Step 4: Delete `_base_leg`**

Remove the entire `_base_leg` function.

- [ ] **Step 5: Lint & format**

Run: `cd "Game Insert/Wispwood" && uv run ruff format stand.py && uv run ruff check stand.py`
Expected: clean (note: `build_shelf`/`build_leg` still reference some constants fixed in Task 3; if ruff reports undefined names from the deletions in Step 1, that is expected and resolved in Task 3 — if so, do Task 3 before committing).

- [ ] **Step 6: Commit**

```bash
git add "Game Insert/Wispwood/stand.py"
git commit -m "Wispwood stand: rebuild base as a flat open rod rectangle (drop the H base)"
```

---

### Task 3: Update shelf + leg hinge to the new base; add stability assert

Point the shelf bottom rod at the new single-pin hinge, move the crossmember to the derived lift, fix the leg's base-overlap split for the new cradle, and assert stability at build time.

**Files:**
- Modify: `Game Insert/Wispwood/stand.py` (`build_shelf`, `build_leg`, `build_all`)

**Interfaces:**
- Consumes: Task-2 module constants; `derived.stand_is_stable`.
- Produces: `build_shelf()`, `build_leg()`, `build_all()` unchanged signatures.

- [ ] **Step 1: Shelf bottom rod necks to a center pin for the base knuckle**

In `build_shelf`, replace the `base_necks` / bottom-rod construction so the bottom rod necks to `PIN_R` at the center (where the base hinge knuckle rides) and keeps full collars elsewhere:

```python
    shelf = _necked_rod(HBY, ROD_R + CR, W - ROD_R - CR, [(LEG_CX, 0.0)])  # bottom rod → center pin
```

Delete the old per-`NECK_XS` 47/47 cut block in `build_shelf` (the base no longer folds under the crossmember — it is a frame the shelf lies on). Keep the top/left/right rods, the four `_corner` calls, the crossmember `_necked_rod(CROSS_Y, ...)` (with the single leg neck `(LEG_CX, LEG_W + 2*ACLR)`), the `_flat`, and the `_tray_lip()` fuse unchanged.

- [ ] **Step 2: Update `build_leg` end cylinder + base-overlap split**

The leg end cross-cylinder must span the base width so it seats in the full-width cradle. Replace the end-cylinder and the 47/47 block:

```python
def build_leg():
    """Build the prop leg: a bar continued onto its hinge cylinder + a base-width end cylinder."""
    x0 = LEG_CX - LEG_W / 2.0
    tip_y = CROSS_Y + L_LEG
    bar = _box(x0, CROSS_Y, 0.0, LEG_W, L_LEG, T)
    leg = bar.fuse(_xcyl(ROD_R, LEG_W, x0, CROSS_Y, ZC))  # rounded hinge end
    leg = leg.cut(_xcyl(BORE, LEG_W + 2.0, x0 - 1.0, CROSS_Y, ZC))  # pin hole through both
    leg = leg.fuse(_xcyl(ROD_R, W - 2 * ROD_R, ROD_R, tip_y, ZC))  # base-width end cylinder
    return _flat(leg)
```

(The leg no longer crosses a base crossmember mid-span — it ends in the cradle — so the old leg 47/47 block is removed. The leg hinge pin is part of the shelf crossmember neck, as before.)

- [ ] **Step 3: Update `build_all` asserts**

Replace the assert block in `build_all` with:

```python
    assert L_LEG > ALT_S_HINGES * math.sin(d.ALT_THETA), "leg too short to reach the table"
    assert CROSS_Y + L_LEG < SHELF_H, "leg does not fit folded between the crossmember and top"
    assert B_BASE < ALT_S_HINGES + L_LEG, "base reach B must be < S + L (degenerate triangle)"
    assert d.stand_is_stable(), "loaded CG falls outside the base footprint (would tip)"
```

Add `ALT_S_HINGES = d.ALT_S_HINGES` to the module constants (Task 2 Step 1) if not already present, and ensure `import math` remains.

- [ ] **Step 4: Lint, format, full test run**

Run: `cd "Game Insert/Wispwood" && uv run ruff format stand.py && uv run ruff check stand.py`
Then: `uv run pytest "Game Insert/Wispwood/tests" -q`
Expected: ruff clean; tests pass (tests don't import `stand`, but confirm nothing regressed).

- [ ] **Step 5: FreeCAD render verification (manual)**

In FreeCAD 1.0.2, run `Stand.FCMacro`. Confirm: base is a flat rectangle resting on Z=0; shelf hinges at the front and leans; tray lip/pegs/tabs intact; prop leg end cylinder lines up with the cradle at 75°; parts do not interpenetrate; folded fold is plausible. (User reviews and adjusts constants as needed.)

- [ ] **Step 6: Commit**

```bash
git add "Game Insert/Wispwood/stand.py"
git commit -m "Wispwood stand: shelf 25mm lift + single-pin hinge + base-width leg lock; stability assert"
```

---

### Task 4: Box placement, folded bay, and docs

Update the in-box placement for the new base extents, confirm the folded bay still fits, and refresh the docs that describe the stand.

**Files:**
- Modify: `Game Insert/Wispwood/box_insert.py` (`place_stand` — already uses `s.NATIVE_Y_MIN`/`s.DISPLAY_X_OFFSET`, verify)
- Modify: `Game Insert/Wispwood/PROJECT.md` (replace the "Folding stand" section with the tabletop-base description)
- Test: `Game Insert/Wispwood/tests/test_box_layout.py` (folded bay fit)

**Interfaces:**
- Consumes: `stand.NATIVE_Y_MIN`, `stand.DISPLAY_X_OFFSET`; `derived.ALT_FOLDED_W/L/H`.

- [ ] **Step 1: Verify the folded bay still fits (failing test first if it doesn't)**

Add to `tests/test_box_layout.py`:

```python
def test_folded_stand_bay_fits():
    """The folded stand bay lies within the box and clears the height bound."""
    bay = bl.bottom_regions()["alt_bay"]
    assert bl.rect_in_box(bay)
    assert bl.folded_alt_within_bound()
```

Run: `uv run pytest "Game Insert/Wispwood/tests/test_box_layout.py" -q`
Expected: PASS if the new `ALT_FOLDED_L`/`ALT_FOLDED_H` fit; if FAIL, the bay or `ALT_BASE_*` need adjustment — surface to the user before forcing it.

- [ ] **Step 2: Confirm `place_stand` needs no code change**

`box_insert.place_stand` already shifts by `rect.y - s.NATIVE_Y_MIN` and `rect.x - s.DISPLAY_X_OFFSET`; since `NATIVE_Y_MIN` now equals `BASE_FRONT_Y` (Task 2), the offset is automatically correct. No edit unless the render shows the stand outside the bay. (Read it, confirm, leave as-is.)

- [ ] **Step 3: Update PROJECT.md**

Replace the entire "### Folding stand" section with a "### Display stand (`stand.py`)" section describing the tabletop-base design: three flat print-in-place parts (open rod-frame base = sole flat table contact reaching `ALT_BASE_FWD` forward of the hinge; shelf with kept lip/pegs/tabs, tray bottom lifted `TRAY_LIFT`=25 mm; prop leg snapping into a full-width base cradle at `STAND_DEPLOY_ANGLE`=75°). Note the stability guarantee (CG range inside the footprint, unit-tested via `derived.stand_is_stable`) and that the old folding stand lives in `archive/folding_stand.py`. Also fix the "Finger scoops … reserved for the folding stand" line to "reserved for the diagonal grip slots".

- [ ] **Step 4: Lint, format, full test run**

Run: `cd "Game Insert/Wispwood" && uv run ruff format box_insert.py tests/test_box_layout.py && uv run ruff check box_insert.py tests/test_box_layout.py`
Then: `uv run pytest "Game Insert/Wispwood/tests" -q`
Expected: ruff clean; all tests pass.

- [ ] **Step 5: FreeCAD render verification (manual)**

Run `Wispwood.FCMacro`; confirm the stand drops into its bay without overlapping the tray/small tray, and the folded stack clears the top tray. (User reviews.)

- [ ] **Step 6: Commit**

```bash
git add "Game Insert/Wispwood/box_insert.py" "Game Insert/Wispwood/PROJECT.md" "Game Insert/Wispwood/tests/test_box_layout.py"
git commit -m "Wispwood stand: folded-bay fit test + box placement + PROJECT.md for the tabletop base"
```

---

## Self-Review

**Spec coverage:**
- Wide flat forward-reaching base (no rock, no tip) → Task 2 (`build_base`), stability in Task 1.
- 25 mm tray lift / crossmember derivation → Task 1 (`ALT_CROSS_Y`) + Task 3 (shelf).
- Keep lip/pegs/tabs → Task 3 reuses `_tray_lip`/`_peg`/`PEG_XS` unchanged.
- Prop-leg snap lock recomputed → Task 1 (`ALT_B_BASE`) + Task 3 (leg).
- Delete old H base + 47/47 → Task 2 (delete `_base_leg`) + Task 3 (drop leg/shelf splits).
- Stability assertions fail the build → Task 3 Step 3.
- Folded envelope / bay fit → Task 1 (`ALT_FOLDED_*`) + Task 4.
- Config knobs (`TRAY_LIFT`, `ALT_BASE_FWD`) + remove H constants → Task 1; the spec's "revisit `ALT_BASE_LEG_*`/`ALT_LOCK_NOTCH_*`/`ALT_LEG_BASE_GAP`" cleanup is folded into Task 2 Step 1 deletions and Task 4 (remove any left unreferenced — check with `grep`).

**Placeholder scan:** none — every code step shows full code; FreeCAD geometry steps are explicit; manual-render steps are verification, not placeholders.

**Type consistency:** `ALT_CROSS_Y`/`ALT_S_HINGES`/`ALT_B_BASE`/`ALT_LIP_EDGE_H`/`stand_is_stable`/`cg_offset` defined in Task 1 and consumed by name in Tasks 2–3. `NATIVE_Y_MIN`/`DISPLAY_X_OFFSET`/`PEG_XS`/`BASE_LEN` kept as the names `box_insert` already imports. `W`/`CROSS_Y`/`B_BASE`/`BASE_CROSS_Y`/`BASE_FRONT_Y`/`BASE_BACK_Y` consistent across Tasks 2–3.

**Note for executor:** geometry Tasks 2–4 cannot run pytest for the FreeCAD parts (no headless FreeCAD here); they rely on ruff + the user's in-FreeCAD render review. Only Task 1 is fully TDD.
