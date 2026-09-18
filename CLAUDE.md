# FreeCAD Project Rules

These rules apply to every project in this repository. They were consolidated from
the per-project Cursor rule files (`.cursor/rules/*`) and are the single source of
truth for how the FreeCAD modeling code should be written.

**Keep this file general.** It covers *how* to build any project. Project-specific
details — dimensions, sizes, tolerances, bin/token layouts, and the description of what
each model is — belong in that subproject's own `PROJECT.md`, **not here**, so the
general rules never have to be repeated per project. See [Projects](#projects) below.

## Target environment

- Generate Python code for **FreeCAD 1.0.2**. Do not use APIs or behavior that only
  work on earlier, incompatible FreeCAD versions.
- The Python scripts drive FreeCAD to generate 3D models that are most likely going to
  be **fabricated** (3D printed), so geometry must be printable and dimensionally correct.

## Project structure

- Put most constants in a project-level **`config.py`**, imported by the rest of the
  Python. Avoid scattering magic numbers through the modeling code.
- Provide a **`.FCMacro`** for each project that, when run inside FreeCAD:
  - reloads all of the project's Python modules (so edits take effect without
    restarting FreeCAD), and
  - re-creates the FreeCAD document from scratch.
- Keep the document creation **in the `.FCMacro` itself**. After building the model,
  the macro should switch the new document to **isometric view** and **fit all** models
  to the view.

## Modeling conventions

- **Always calculate offsets in code**, even when given offsets that were directly
  measured or pre-calculated within the model. Derive positions from named constants and
  computed values rather than hard-coding measured coordinates.

## Tooling

- Lint and format all Python with **`ruff check`** and **`ruff format`**.

## Git / commits

- **Don't repeatedly prompt to commit.** After finishing a change, do not end with a
  "want me to commit?" question. Commit (or push) only when the user explicitly asks; until
  then, just leave the changes pending without asking each turn.

## Projects

Each subproject keeps its own design intent and specific parameters (sizes, tolerances,
descriptions) in a local `PROJECT.md`. When working in a subproject, read its `PROJECT.md`
together with this file. Add new projects to this list as they gain a `PROJECT.md`.

- [BookBindingTemplates](BookBindingTemplates/PROJECT.md) — 3D-printable bookbinding
  layout templates at several configurable book sizes.
- [DimSumOrganizer](DimSumOrganizer/PROJECT.md) — insert for a bamboo steamer basket that
  holds stacks of circular and oval game tokens.
- [ToolOrganizer](ToolOrganizer/PROJECT.md) — drawer organizer bin inserts with locking
  clips and labels.
- [Game Insert/Wispwood](Game%20Insert/Wispwood/PROJECT.md) — two-stack Wispwood tile rack
  with a two-part sliding/dispensing lid and an integrated folding stand.
- [BombBusters](BombBusters/PROJECT.md) — reference geometry for BombBusters game
  components (tokens, markers, discs, cards) and the box envelope, for layout planning.
