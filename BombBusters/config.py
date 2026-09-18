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

# EquipmentTokens (!=, ==)
EquipmentToken = {"Height": 21.15, "Width": 29.75, "Thickness": 3.15, "Quantity": 2, "Z": "Height"}

# Markers
InfoMarker = {
    "Red": {"Diameter": 8, "Height": 12, "Quantity": 3},
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
