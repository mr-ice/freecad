"""Dominion dimensions (mm), bay spaces, components, and bit placement overrides."""
# Extra space in my big dominion boxes
bay = [
    {"x": 28.8, "y": 296, "z": 100},
    {"x": 43, "y": 296, "z": 100},
]

# The wooden bitbox which we no longer have room for.
# This is the orientation with the lid up
current_bit_box = {"x": 90, "y": 215, "z": 49}


# All the extra components that I need to fit
Components = {
    "stars": {
        "diameter": 16,
        "points": 7,
        "thickness": 6,
        "quantity": 13,
    },
    "player_pieces": {
        "minus_card_gold": {
            "quantity": 2,
            "x": 34.5,
            "y": 44.5,
            "t": 2.05,
        },
        "plus_tokens": {"quantity": 8, "diameter": 24, "t": 16.5 / 8},
        "cube": {"quantity": 2, "x": 10.21, "y": 10.21, "z": 10.21},
    },
    "metal": {
        "kingdom_markers": {
            "description": (
                "20 10x15mm white oval with dominion on one side and a ",
                "water scene on the other",
            ),
            "volume": 35 * 60 * 10,
        },
        "gold_coin": {"description": "gold color round metal coins", "volume": 35 * 60 * 46},
        "copper_debt": {"description": "hex copper with a 1 in the center", "volume": 35 * 60 * 30},
        "points": {
            "description": "shield victory point metal tokens in 1,2,5 denominations",
            "volume": 35 * 60 * 40,
        },
    },
    "dice": {"x": 32, "y": 20, "z": 16},
    "small_mat": {"x": 80, "y": 80, "t": 1.2, "quantity": 9},
    "favors_mat": {
        "x": 127.5,
        "y": 84,
        "t": 1.15,
        "quantity": 6,
    },
    "island_ship_sea_mat": {"x": 126.2, "y": 83, "t": 1.0, "quantity": 18},
    "coffers_villagers_exile_mat": {"x": 127.43, "y": 83.8, "t": 1.15, "quantity": 12},
    "player_mat": {
        "x": 125,
        "y": 82,
        "t": 12.5 / 6,
        "quantity": 6,
    },
}

# BULK_Y = two boxes need to fit beside the mat tray
# 296 - 134.5 = 161.5 remaining in bay_1
# half of that is 80.75
# minus 6 WALL_THICKNESSES = 9mm = 71.75
# possibly minus a bit less as we need some BOX_TOLERANCES


WALL_THICKNESS = 1.5  # same as ../BombBusters
BULK_FILLET = 8  # radius on the bulk items' bottom y-aligned edges (the x-end ones)
BIN_FILLET = 1  # radius on the bins' inner top rim
BULK_Y = 70.75  # y width of a bulk row; each row is split into two bins side by side
LIFT_BASE_T = 3.125  # lifting apparatus base thickness
LIFT_HOLE_D = 20  # finger hole diameter (guess -- adjust to your finger)
LIFT_HOLE_MARGIN = 4  # from the upright's top edge to the finger hole
LIFT_FILLET = 2  # radius on the lift's vertical and topmost edges
LIFT_TOP_FILLET = 9  # radius on the lift's topmost edges along X
BOX_TOLERANCE = 0.5  # mat box total width is bay_1 x less this
POST_LEG = 8  # mat box corner post leg length
BRACE_T = 8  # mat box 45 degree brace width (in the XZ plane)
BOX_HOLE_D = 20  # mat box wall finger hole diameter
BOX_HOLE_MARGIN = 4  # from the wall top to the hole
BOX_WALL_FILLET = 9  # radius on the wall's top corners
BOX_HOLE_FILLET = 1  # radius on the finger hole rims
MAT_CLEARANCE = 1  # extra mat box interior in Y and Z so mats slide freely
SLEEVE_WALL = 2 * WALL_THICKNESS  # outer box floor/side wall around each bin stack
BOX_OUTER_FILLET = 1.5  # outer edges of the bin boxes
BOX_MOUTH_FILLET = 1  # pocket mouth edges at the boxes' open min-x face
GRAB_R = 14  # top-surface grab cut radius (diameter 28, about twice the earlier grab)
GROOVE_R = 9  # finger slot radius in the outer box side walls
RENDER_ICONS = True  # False skips building the icon inlays and their pockets (much faster)
ICON_DEPTH = 0.8  # icon inlay thickness: the pocket sunk into the host (must be >= 0.6 to print)
LID_LOGO = "dominion_logo_v1_0/dl_flat.svg"  # logo on the PlayerCase_Lid outer face
LID_LOGO_SCALE = 0.8  # lid logo size as a fraction of the lid face it fits
ICON_MARGIN = 1.0  # clear space around an icon on its face
ICON_LINE = 1.0  # outline width of the kingdom marker oval
KINGDOM_MARKER_OVAL = (15, 10)  # the real marker is a 10 x 15 oval; keep its axis ratio
ICON_FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"  # digits on coin/debt/shield
ICON_COLORS = {"left_red": (0.8, 0.1, 0.1), "right_green": (0.1, 0.6, 0.2)}  # by part suffix
PLAYER_BOX_CLEARANCE = 1  # player box pocket vs the card footprint (total, x and y)
RENDER_PLAYER_ITEMS = False  # False skips PlayerMats_ and the Player{Cards,Tokens,Cube}_ parts
RENDER_DICE = False  # False skips the Dice reference box
LID_OPEN = True  # PlayerCase_Lid swung 180 degrees about its hinge (the print pose)
PLAYERS = 6  # max players; player_pieces quantities are per player
GAP = 10  # spacing between bits in the default grid
TRANSPARENCY = 70  # bay envelopes, percent

# Edit me: {name: (x, y, z)} overrides the default grid position of any bit.
# Names are the FreeCAD object names, e.g. "Bay_0", "Mat_island", "PlayerMats_3".
BIN_GAP = SLEEVE_WALL + 2 * BOX_TOLERANCE  # bin-to-bin: shelf + pocket gaps
# Bulk items and MatBox are placed from Bay_1 by bits.stack_placements(); entries here
# override any bit.
PLACEMENTS = {
    "Mat_base": (41.8, 3, 3),
    "Mat_exile": (54.6, 3, 3),
    "Mat_coffers_villagers": (61.8, 3, 3),
    "Mat_favor": (71.8, 3, 3),
    "Mat_island": (0, 0, 3.2),
    "Mat_ship": (6, 0, 3.2),
    "Mat_sea": (12, 0, 3.2),
    "Mat_small": (18, 0, 3.2),
    "Lift": (0, 0, 0),
}

# Player box case (bay_0 beside the lift): hinged lid on the pockets' open (min-x) face.
HINGE_R = 3  # knuckle radius
HINGE_CONE_R = 2  # base radius of the 45 degree truncated cones on the case knuckles
HINGE_CONE_TIP = 0.8  # tip radius of those cones
HINGE_CONE_CLEARANCE = 0.2  # gap between each cone and its socket in the lid knuckle
HINGE_GAP = 0.4  # clearance between interleaved knuckles and to the case end
HINGE_KNUCKLES = 5  # odd: the case gets the outer ones, the lid the inner ones
