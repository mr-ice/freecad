"""Configuration constants for the Wispwood tile holder (custom design).

All dimensions are in millimetres and all angles in degrees unless noted. Values
that are design assumptions pending confirmation are tagged ``ASSUMED``.

The public API of this module is the set of module-level constants below; downstream
modeling code imports them and must not hard-code measured coordinates (see the
repository ``CLAUDE.md``: always calculate offsets).
"""

# --- Tiles -------------------------------------------------------------------
TILE_COUNT_TOTAL = 160  # tiles in the game
STACKS = 2  # two side-by-side pockets
TILES_PER_STACK = TILE_COUNT_TOTAL // STACKS  # 80
TILE_SIZE = 35.0  # MEASURED square tile edge length
TILE_THICKNESS = 2.133  # MEASURED single-tile thickness

# --- Fit / clearances --------------------------------------------------------
TILE_SIDE_CLEARANCE = 1.5  # per side on tile width: keeps the 38 mm comfortable fit
STACK_LENGTH_SLACK = 8.0  # extra length so a full 80-tile stack slides freely
TILE_DEPTH_CLEARANCE = 1.0  # extra pocket depth above the tile height

# --- Pockets (derived) -------------------------------------------------------
POCKET_WIDTH = TILE_SIZE + 2 * TILE_SIDE_CLEARANCE  # ~38
POCKET_LENGTH = TILES_PER_STACK * TILE_THICKNESS + STACK_LENGTH_SLACK  # ~178.64
POCKET_DEPTH = TILE_SIZE + TILE_DEPTH_CLEARANCE  # ~37

# --- Walls / structure -------------------------------------------------------
WALL_LONG = 4.0  # SOURCE: long-side outer walls
WALL_END = 2.0  # SOURCE: end walls
FLOOR_THICKNESS = 3.0  # SOURCE
DIVIDER_THICKNESS = 2.0  # SOURCE: centre divider between the two pockets

# --- Lid ---------------------------------------------------------------------
LID_THICKNESS = 2.5
LID_SPLIT_TILE = 65  # large lid covers tiles 1..LID_SPLIT_TILE; small lid covers the rest
DISPENSE_GAP = TILE_THICKNESS + 0.6  # how far the lid slides back to release one tile
RAIL_DEPTH = 1.5  # how far the lid edge sits into the side rail groove
# The lid cross-section is defined once (in wispwood.py); the tray slot is that same
# section grown by LID_SLIDE_CLEARANCE and cut from the tray, so the fit is exact and
# defined in one place. LID_BEVEL spans the full groove depth (45 deg), making the tray's
# retaining lip a clean 45 deg overhang that prints without support. The lid's outer tip
# is then LID_THICKNESS - LID_BEVEL thick (~0.5 mm) -- raise LID_THICKNESS if too fragile.
LID_BEVEL = RAIL_DEPTH  # 45 deg chamfer on the lid's top sliding edges (== groove depth)
LID_SLIDE_CLEARANCE = 0.2  # tolerance grown around the lid to cut the tray slot (the fit)
# Extra lid width (total across both rail edges; half is added per side) that grows ONLY the
# lid, not the slot, so the side clearance shrinks from LID_SLIDE_CLEARANCE to a tighter
# friction fit. Raised because the lid slid well but did not stay put.
LID_WIDTH_FRICTION = 0.4
LID_TOP_LIP = 1.0  # wall lip above the lid that retains it from lifting
# The tray's lid slot stops short of the front by this distance above the inside surface of
# the front wall, forming a stop that leaves a top-front dispensing gap. The large lid has a
# reversible end cutout: inserted that end first, the lid passes the stop and closes the gap
# (storage); reversed, it stops here, leaving the gap open to dispense one tile.
LID_FRONT_STOP_GAP = TILE_THICKNESS + 1.0

# End walls (front and back) are identical: both rise to the lid underside (full pocket
# depth) so the flat lid can slide out either end and is held only by rail friction.
# Going higher would block the lid from sliding over them.
END_WALL_HEIGHT = POCKET_DEPTH  # top flush with the lid underside (~36 mm)

# --- Finger scoops (both end walls, one per pocket) -------------------------
SCOOP_WIDTH = 24.0  # width of the thumb scoop (pocket is POCKET_WIDTH wide)
SCOOP_DEPTH_FRACTION = 0.8  # scoop reaches ~80% of the pocket depth from the top down
SCOOP_CHAMFER = 1.0  # chamfer on the scoop's outer-face and top edges (finger comfort)

# --- Grip / lightening slots (long side walls) -------------------------------
# Diagonal rounded (stadium) slots cut through each long wall to save plastic and give grip.
GRIP_SLOT_COUNT = 4  # slots per long wall, spaced along the length
GRIP_SLOT_WIDTH = 6.0  # stadium width (across the slot)
GRIP_SLOT_LENGTH = 22.0  # stadium length end-to-end (along the diagonal)
GRIP_SLOT_ANGLE = 60.0  # slot tilt above horizontal (deg)

# --- Folding stand -----------------------------------------------------------
# Two legs (rounded free ends) joined by a front base panel a little wider than the box
# front so it covers the legs; the leg/base junction is chamfered. Each leg carries a
# substantial oval peg that rides a complex slot in the tray's outer side wall. Modelled
# FOLDED; the path/lock still need tuning vs a print.
STAND_THICKNESS = 3.0  # leg and base-panel thickness
# Single knob for the deployed tilt / balance: longer legs reach further back and lift the
# raised end higher, moving the assembly's centre of gravity UP and BACK. The whole stand
# slot (folded peg rest, vertex/hinge, jog, lock) is derived from STAND_LEG_LEN in
# wispwood.py, so changing this fraction moves the leg AND the slot together and they stay
# aligned (the peg's back margin stays constant). Stays in-bounds through ~0.7; tune to taste.
STAND_LEG_LENGTH_FRAC = 0.6  # fraction of the tray length spanned by each leg
STAND_LEG_WIDTH = 16.0  # leg width (Z extent), centred on the peg
STAND_BASE_DEPTH = 8.0  # base-panel thickness along Y (the foot)
STAND_CHAMFER = 5.0  # chamfer/gusset at the leg-to-base junction

# Oval / bar peg on each leg (rides the slot) -- substantial, centred on the leg:
STAND_PEG_LENGTH = 10.0  # oval major axis, along the leg
STAND_PEG_WIDTH = 5.0  # oval minor axis (sets the slot channel width)
STAND_PEG_DEPTH = 2.5  # how far the peg projects into the wall slot (< WALL_LONG)
STAND_SLOT_CLEARANCE = 0.4  # slot-vs-peg running clearance
# Gap between each leg's inner face and the tray outer wall, so the folded-modelled stand
# does not print fused to the tray body. The peg still bridges this gap into the wall slot.
STAND_BODY_GAP = 0.2

# Slot path in the outer wall face, DERIVED from the leg so the oval sits at the back of
# the leg with equal margins. The hinge is toward the FRONT. Path: along the horizontal
# "parallel" arm to its end, a short vertical jog up (so the peg lifts before locking),
# then a short tilted "top" arm to the lock. This jog+short-arm is the lock detent.
STAND_SLOT_ARM_LEN = 24.0  # length of the horizontal (parallel) arm
STAND_V_ANGLE_DEG = 15.0  # tilt of the top arm above horizontal
STAND_JOG_FRAC = 0.5  # vertical jog at the vertex = this * peg width (the lift)
STAND_ARM2_FRAC = 1.5  # top (lock) arm length = this * peg length (significantly shorter)

# --- Alternate stand (separate, triangular frame: shelf + base + leg) --------
# Fresh design. A triangular frame of three parts: the SHELF (holds the
# tray on LIPs), the BASE (sits on the table), and the LEG (props them
# apart in a triangle).  Built up part by part; this section defines the
# SHELF.
#
# Shelf: a rounded-rectangle plate, ALT_SHELF_THICKNESS thick, ALT_SHELF_HEIGHT tall and wide
# enough to clear the tray between the side lips (width = tray + 2*side-lip + 2*side-clear). A
# cross-lip across the bottom of the top surface holds the tray; two side lips on the outer
# edges steady it; the two bottom corners are raised and filleted into a cup. The unused centre
# of the plate is cut away, leaving a border frame.
# --- Stand mechanism (redesigned barrel hinge + computed snap lock) ----------
# The shelf bottom is a full-width barrel (Ø = plate thickness) with two narrowed neck bands;
# the base hinges on it via two knuckles and a concave mating edge. The prop leg hinges up the
# shelf and its tip snaps into a socket on the base; the socket position is COMPUTED so the
# shelf locks at STAND_DEPLOY_ANGLE above the table.
STAND_DEPLOY_ANGLE = 75.0  # locked shelf angle above the table (deg)
ALT_BARREL_NECK_R = 2.0  # reduced barrel radius at the two base-knuckle bands
ALT_BARREL_NECK_W = 12.0  # axial width of each base-knuckle band
ALT_BARREL_NECK_FRACS = (0.28, 0.72)  # neck-band centres as a fraction of the shelf width
ALT_LEG_HINGE_Y = 18.0  # prop-leg hinge distance up the shelf from the barrel axis
ALT_SNAP_R = 2.0  # radius of the leg-tip snap bump and the base socket
ALT_SNAP_CLEAR = 0.15  # snap interference (smaller = stronger click)
# Rod-frame stand (per stand.md): shelf is a rounded rectangle of rod; base is an H hinged on
# the shelf's bottom rod (necked to a pin); the leg hinges on the shelf crossmember and its
# end-cylinder clicks into the base.
ALT_ROD_R = 4.5  # frame rod in-plane radius (Ø9), flattened to ALT_PART_T in Z for printing
ALT_PART_T = 7.0  # part thickness in Z (a 7 mm cross-section trimmed from the Ø9 rod)
ALT_CROSS_Y = 24.0  # shelf crossmember Y (tray sits here; the leg hinges on it)
ALT_TRAY_LIP_H = 3.0  # lip height above the shelf face that catches the tray bottom edge
ALT_BASE_FOOT = 12.0  # base length past the lock line (foot)
ALT_BASE_CROSS_W = 9.0  # base/leg crossmember width along the part
ALT_FRAME_CORNER_R = 8.0  # shelf frame corner radius (continuous rounded rod path)
ALT_LIP_EDGE_FRAC = 0.55  # tray lip height at the shelf edges, as a fraction of tray height
ALT_LIP_LOW_H = 3.0  # tray lip height at the finger-groove centres (low, to clear scoops)
ALT_LIP_T = 3.0  # tray lip thickness (along Y)
ALT_LIP_LEG_GAP = 0.4  # clearance under the lip over the leg hinge (so they don't fuse); 2 layers
ALT_LIP_LEG_RAMP = 3.0  # run of the angled lead-in up to that gap (gentle, prints at 0.2 mm)

SHOW_ALT_STAND = True
ALT_SHELF_THICKNESS = 7.0  # shelf plate thickness (the leg nests fully inside this, not the lips)
ALT_SHELF_SIDE_CLEAR = 0.1  # per-side gap between the tray and the side lips
ALT_SHELF_HEIGHT = 89.0  # shelf length; raised one rod-diameter above the leg so it clears the top
# Frame extension below the cross-lip, down toward the base. Deployed, the shelf sits 15 deg
# off vertical, so this is the SLANT length along the angled frame (vertical drop = x*cos15).
# ~15 mm puts the top of the lip ~18 mm (slant) above the table so the tray's front-top edge
# lands ~28 mm off the table. See ALT_SHELF_HEIGHT for the above-lip part.
ALT_SHELF_BELOW_LIP = 25.0  # slant length of frame below the lip (toward the base)
ALT_SHELF_CORNER_R = 5.0  # rounded-rectangle corner radius
ALT_SHELF_BORDER = 10.0  # frame border left after cutting the unused centre out (stocky)
ALT_SHELF_CROSS_LIP_H = 3.0  # bottom cross-lip height above the surface (holds the tray)
ALT_SHELF_CROSS_LIP_T = 7.0  # bottom cross-lip thickness (along the height)
ALT_SHELF_SIDE_LIP_W = 3.0  # side steadying-lip width (matched to the cross-lip thickness)
ALT_SHELF_SIDE_LIP_H = 3.0  # side steadying-lip height above the surface
# The two bottom corners (cross-lip meets side-lip) are raised to this fraction of the tray
# height, then filleted back down to the cross-lip and the side-lip on each side, making a
# deeper cup that cradles the tray's bottom corners.
ALT_SHELF_CORNER_H_FRAC = 0.5  # corner-post height as a fraction of the tray height (~1/2)

# Leg (the prop): nests FULLY INSIDE the shelf plate, in a pocket cut in the back, free of all
# other structure except a print-in-place hinge just above the cross-lip. It swings out to
# prop the stand; its free end is a flattened cylinder forming a T, for locking upright later.
ALT_LEG_LENGTH = 50.0  # leg hinge to its end-cylinder; fits folded between crossmember and top
ALT_LEG_WIDTH = 24.0  # leg-bar width (across) = hinge span
ALT_LEG_THICK = 7.0  # leg-bar thickness (<= plate thickness so it sits recessed inside)
ALT_LEG_HINGE_GAP = 2.0  # gap above the cross-lip to the hinge axis
ALT_LEG_POCKET_CLEAR = 0.4  # clearance around the leg in its opening (so it stays free)
ALT_LEG_T_LEN = 60.0  # T crossbar length (across)
ALT_LEG_T_DIA = 8.0  # T crossbar cylinder diameter before flattening
ALT_LEG_T_THICK = 7.0  # T crossbar flattened thickness (fits the leg thickness)

# Print-in-place hinge: interleaved knuckles on a single pin. Odd segment count so the ends
# are PLATE knuckles (the pin anchors to the plate there); LEG knuckles ride the pin between
# them. Gaps are the print clearances that keep the leg free.
ALT_HINGE_SEGMENTS = 5  # knuckle segments across the hinge (plate at the ends, alternating)
ALT_HINGE_R = 3.5  # knuckle outer radius (Ø7 mm = the full plate thickness)
ALT_HINGE_PIN_R = 1.5  # pin radius (Ø3 mm; the pin is part of the plate)
ALT_HINGE_PIN_CLEAR = 0.4  # radial clearance of the leg-knuckle bore around the pin (comfortable)
ALT_HINGE_AXIAL_CLEAR = 0.3  # axial gap between leg and plate knuckles
# Where two parts overlap in plan (base leg ↔ shelf cross, base crossbar ↔ prop leg) they
# share the thickness ~47/47: one keeps the back ~47%, the other the front ~47%, with this gap
# between so they print free. Each part = (thickness - gap) / 2.
ALT_SPLIT_GAP = 0.4
ALT_CRADLE_OFFSET = 3.5  # height of the lock-cradle seat above the base centreline (the leg
# end-cylinder locks here, on TOP of the base, so the deployed lock geometry is offset up by this
ALT_LEG_BASE_GAP = 4.0  # in-plane gap between the prop leg and each base leg, so the leg-hinge
# neck on the crossmember clears the base's pass-under cutout (was ~1.3 mm, too tight)

# Base (the foot): a second print-in-place hinge centred in the shelf's bottom border (same
# Ø7 knuckles / Ø3 pin, knuckles subdivided to match the prop-leg hinge). Two legs run up
# through the shelf flanking the prop leg, stopping short of its T; a crossbar high up (under
# the prop leg, via the 47/47 split) joins them into one part.
ALT_BASE_LEG_WIDTH = 14.0  # each base-leg width (across)
ALT_BASE_LEG_CLEAR = 3.0  # clearance from the prop leg and the slot walls
ALT_BASE_T_GAP = 3.0  # base legs stop this far short of the prop T
ALT_BASE_CROSS_WIDTH = 8.0  # crossbar length along the leg
ALT_BASE_CROSS_INSET = 6.0  # crossbar pulled back from the base-leg tops (toward the hinge)
ALT_LOCK_NOTCH_W = 9.0  # width of the T-catch notch in the base crossbar (>= ALT_LEG_T_DIA)
ALT_LOCK_NOTCH_DEPTH = 3.0  # how deep the prop-leg T seats into the base crossbar
ALT_STAND_TRANSPARENCY = 0  # FreeCAD view only

# --- Tolerances / print ------------------------------------------------------
GENERAL_CLEARANCE = 0.2  # default fit clearance for mating printed parts
MAX_PRINTER_DIMENSION = 350.0  # build-plate limit; XL bed (MK4 : 240, XL : 350)

# --- Display (FreeCAD view only; no effect on geometry or the print) ---------
# Percent transparency (0 opaque .. 100 invisible) applied to the tray and lid parts so the
# tiles, fit, and stand slot can be seen through them; other parts stay opaque.
TRAY_LID_TRANSPARENCY = 80
# A second, NON-PRINTING ghost copy of the stand posed at the slot's lock (deployed)
# position, for visual comparison against the folded stand. Display-only -- do not export it.
SHOW_STAND_DEPLOYED = True
STAND_DEPLOYED_TRANSPARENCY = 55  # ghost transparency so it reads as a reference, not a part

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
BOARD_POCKET_SLACK = 5.0  # loose slack around the board-piece stack in the top-tray pocket
INSERT_WALL = 2.0  # well/divider wall thickness
INSERT_FLOOR = 1.5  # tray floor thickness
TOP_TRAY_DEPTH = 12.0  # top-tray height (board stack is the tallest content)
TOP_TRAY_FIT = 0.4  # per-side oversize of the top tray so it friction-fits and covers the box ends
FINGER_GROOVE_R = 8.0  # radius of the vertical finger grooves cut through the small-tray well walls
SMALL_TRAY_RIM_Z = (
    FLOOR_THICKNESS + POCKET_DEPTH + LID_THICKNESS + LID_SLIDE_CLEARANCE + LID_TOP_LIP
)  # = Wispwood WALL_TOP (~42.7); top tray rests flush on the Wispwood + small trays
COMPONENT_CLEARANCE = GENERAL_CLEARANCE  # per-side fit clearance for component wells

# Folded alt stand must clear under the top tray (which rests at z = 42).
ALT_STAND_MAX_FOLDED_H = 40.0
