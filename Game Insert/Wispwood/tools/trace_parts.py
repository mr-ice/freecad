"""Trace game-part outlines from photos on Letter paper, in millimetres.

Run: uv run --with opencv-python-headless --with numpy python tools/trace_parts.py

For each photo it finds the sheet of paper (largest bright quad), perspective-corrects it to a
true US-Letter rectangle (279.4 x 215.9 mm), segments the part on the paper, and prints the
part's bounding box and a simplified outline polygon (mm). Debug overlays are written next to
the script.
"""

import os

import cv2
import numpy as np

LETTER_LONG = 279.4  # mm (11 in)
LETTER_SHORT = 215.9  # mm (8.5 in)
PXMM = 4.0  # warp resolution

SRC = "/Users/michael/Library/CloudStorage/OneDrive-Personal/Mobile Uploads"
IMAGES = {
    "ruler": "20260620_163756.jpg",
    "center_map": "20260620_163642.jpg",
    "paw": "20260620_163655.jpg",
    "outer_map": "20260620_163709.jpg",
}
OUT = os.path.dirname(os.path.abspath(__file__))


def order_quad(pts):
    """Order 4 points TL, TR, BR, BL."""
    pts = pts.reshape(4, 2).astype(np.float32)
    s = pts.sum(1)
    d = np.diff(pts, axis=1).ravel()
    return np.array(
        [pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]],
        dtype=np.float32,
    )


def find_paper(img):
    """Return the ordered 4 corners of the paper sheet (largest bright rectangle)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    for c in cnts[:5]:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4 and cv2.contourArea(approx) > 0.2 * img.shape[0] * img.shape[1]:
            return order_quad(approx)
    raise RuntimeError("paper not found")


def warp_to_letter(img, quad):
    """Warp so the paper fills a true Letter rectangle (landscape), PXMM px/mm."""
    w, h = int(LETTER_LONG * PXMM), int(LETTER_SHORT * PXMM)
    # If the paper quad is taller than wide, swap to keep landscape.
    (tl, tr, br, bl) = quad
    width = np.linalg.norm(tr - tl)
    height = np.linalg.norm(bl - tl)
    if height > width:
        quad = np.array([tr, br, bl, tl], dtype=np.float32)
    dst = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(quad, dst)
    return cv2.warpPerspective(img, M, (w, h))


def part_contour(warp):
    """Return the part contour via Canny edges (rim) closed into a filled mask.

    The parts are iridescent with bright centres that match the paper, so colour thresholding
    fails; their dark outline is reliable, so we Canny, dilate to close the rim into a loop,
    fill the largest external contour, then erode back to undo the dilation inflation.
    """
    h, w = warp.shape[:2]
    m = 24
    gray = cv2.cvtColor(warp, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray, 20, 70)
    grow = 4
    edges = cv2.dilate(edges, np.ones((grow, grow), np.uint8), iterations=2)
    edges[:m] = 0
    edges[-m:] = 0
    edges[:, :m] = 0
    edges[:, -m:] = 0
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        raise RuntimeError("no edges")
    cnt = max(cnts, key=cv2.contourArea)
    mask = np.zeros((h, w), np.uint8)
    cv2.drawContours(mask, [cnt], -1, 255, cv2.FILLED)
    mask = cv2.erode(mask, np.ones((grow, grow), np.uint8), iterations=2)  # undo dilation
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return max(cnts, key=cv2.contourArea), mask


for name, fn in IMAGES.items():
    path = os.path.join(SRC, fn)
    img = cv2.imread(path)
    quad = find_paper(img)
    warp = warp_to_letter(img, quad)
    cnt, mask = part_contour(warp)
    x, y, bw, bh = cv2.boundingRect(cnt)
    area_mm = cv2.contourArea(cnt) / (PXMM**2)
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.004 * peri, True).reshape(-1, 2) / PXMM
    print(f"\n=== {name} ({fn}) ===")
    print(f"  bbox: {bw / PXMM:.1f} x {bh / PXMM:.1f} mm   area: {area_mm:.0f} mm^2   verts: {len(approx)}")
    # polygon relative to bbox min, rounded
    poly = (approx - approx.min(0)).round(1)
    print(f"  polygon (mm, n={len(poly)}):")
    print("   " + "; ".join(f"({px:.1f},{py:.1f})" for px, py in poly))
    dbg = warp.copy()
    cv2.drawContours(dbg, [cnt], -1, (0, 0, 255), 3)
    cv2.imwrite(os.path.join(OUT, f"trace_{name}.png"), dbg)
