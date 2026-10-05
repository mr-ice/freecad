# WireTokens
WireToken = {
    "Height": 45,
    "Width": 14,
    "Thickness": 3.15,
    "Quantity": {
        "Red": 11,
        "Yellow": 11,
        "Blue_00": 24,
        "Blue_01": 24,
    },
    "Z": "Width",
}

# InfoTokens
InfoToken = {
    "Height": 21.25,
    "Width": 14,
    "Thickness": 3.15,
    "Quantity": {
        "Number": 24,
        "Yellow": 2,
    },
    "Z": "Height",
}

# Tokens from SecretMission Boxes
SecretMissionTokens = {
    "Height": 21.25,
    "Width": 14,
    "Thickness": 3.15,
    "Quantity": {"X": 5, "x1": 8, "x2": 8, "x3": 5, "even": 11, "odd": 11},
    "Z": "Width",
}

# EquipmentTokens (!=, ==)
EquipmentToken = {"Height": 21.15, "Width": 29.75, "Thickness": 3.15, "Quantity": 2, "Z": "Height"}

# Markers
InfoMarker = {
    "Red": {"Diameter": 8, "Height": 12, "Quantity": 4},
    "Yellow": {"Width": 8, "Height": 12, "Quantity": 4},
    "Z": "Height",
}

# BlueCutDiscs
BlueCutDisc = {"Diameter": 19.1, "Thickness": 1.6, "Quantity": 12, "Z": "Diameter"}

# Cards
Card = {
    "Mission": {
        "Height": 110.3,
        "Width": 75,
        "Thickness": 0.325,
        "Quantity": 10,  # more in boxes
    },
    "Equipment": {
        "Height": 88,
        "Width": 63,
        "Thickness": 7.1 / 22,  # 13 equipment, 9 roles, 12 numbers, 1 direction
        "Quantity": 35,  # more in boxes
    },
    "Z": "Thickness",
}


# Space left in the box (original loose insert)
Box = {
    "Height": 260,
    "Width": 91.4,
    "Depth": 40,
    "Z": "Depth",
}

# Secret Mission boxes come in large and smal
SecretMissionBox = {"Height": 129.0, "Width": 86.0, "Depth": 19.0, "Z": "Depth"}

SecretMissionBoxL = SecretMissionBox.copy()
SecretMissionBoxL["Width"] = SecretMissionBox["Width"] * 3 / 2

# TokenTray holds the cut discs, infomarkers, and all info tokens
TokenTray = {
    "Height": 111,
    "Width": 91.4,
    "Depth": 15,
    "Z": "Depth",
}

# Overall
WALL_THICKNESS = 1.5
TOLERANCE = 0.75

# WireStand: rack holding up to 14 WireTokens standing on edge, each with an
# optional InfoToken slot in front. Cross section is a hexagon -- full-width
# vertical base, angled sides, narrow top around the slots. The angled sides
# are hollowed from behind down to a WALL_THICKNESS shell, to save material.
# Positions labeled A-N, engraved into the angled sides near the top; a
# matching letter insert (build_wire_stand_letters) can be printed in a second
# color.
WireStand = {
    "Positions": 14,
    "Letters": "ABCDEFGHIJKLMN",
    "Floor": 1,  # solid material left under each slot
    "SlotCutDepth": 7,  # Z depth of the slot cut, above the floor
    "MiddleWall": 2 * WALL_THICKNESS,  # wall between the front and back slot rows
    "TopMargin": WALL_THICKNESS,  # solid strip on each side of the narrow top, outside the slots
    "PocketGap": 2 * WALL_THICKNESS,  # gap between the slot cut and the pocket cut behind it
    "LabelPocketDepth": 1,
    "LabelHeight": 5,  # font height of the engraved letter
    "LabelTopGap": 1,  # gap between the top edge and the top of the engraved letter
    "Width": 30,  # fixed base width (front-to-back)
    "VerticalHeight": 2,  # height of the vertical base before the sides angle in
}
WireStand["Height"] = WireStand["Floor"] + WireStand["SlotCutDepth"]
# WireToken and InfoToken share the same Width and Thickness. Width now runs along
# the stand's length (X): width, divider, width, divider, ... Thickness is the
# slot's front-to-back depth (Y) -- the token stands on its thin edge.
WireStand["SlotWidth"] = WireToken["Width"] + TOLERANCE/3 # X extent of one token slot
WireStand["SlotDepth"] = WireToken["Thickness"] + TOLERANCE/3
# The narrow top only needs to fit the two thin slots, their middle wall, and a
# margin on each outer edge -- the base stays the fixed Width above regardless.
WireStand["TopWidth"] = (
    2 * WireStand["TopMargin"] + 2 * WireStand["SlotDepth"] + WireStand["MiddleWall"]
)
WireStand["TopMin"] = (WireStand["Width"] - WireStand["TopWidth"]) / 2
WireStand["TopMax"] = WireStand["Width"] - WireStand["TopMin"]
WireStand["Length"] = (
    WireStand["Positions"] * WireStand["SlotWidth"]
    + (WireStand["Positions"] + 1) * WireStand["PocketGap"]
)

# SecretMissionTray: fits inside the (Small) SecretMissionBox, walls raised to
# that box's own interior depth.
SecretMissionTray = {
    "Height": SecretMissionBox["Height"] - TOLERANCE,
    "Width": SecretMissionBox["Width"] - TOLERANCE,
    "Depth": SecretMissionBox["Depth"],
    "Z": "Depth",
}
