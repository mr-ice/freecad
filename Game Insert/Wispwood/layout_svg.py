"""Generate the box-layout SVG map from :mod:`config` and :mod:`box_layout`.

The map is to scale (1 user unit = 1 mm, ``185 x 265``) so it can be printed 1:1 into the
box floor as a pack-away guide, and reviewed as a design artifact. It draws the bottom-layer
regions with labels and lists the top-layer items in a corner note.

Public API
----------
``generate_svg``, ``write_svg``.
"""

import box_layout as bl
import config as cfg

_FILLS = {
    "wispwood": "#cfe3f7",
    "alt_bay": "#d6f0d8",
    "small_tray": "#f3eddb",
}


def _rect(r, fill, cls="region"):
    return (
        f'  <rect class="{cls}" x="{r.x:g}" y="{r.y:g}" '
        f'width="{r.w:g}" height="{r.h:g}" fill="{fill}"/>\n'
    )


def _text(x, y, s, cls="lbl"):
    return f'  <text class="{cls}" x="{x:g}" y="{y:g}">{s}</text>\n'


def generate_svg():
    """Return the box-layout SVG document as a string.

    Returns
    -------
    str
        A complete, to-scale SVG (``185 x 265`` mm) of the bottom layer plus a top-layer note.
    """
    b = bl.bottom_regions()
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{cfg.BOX_W:g}mm" '
        f'height="{cfg.BOX_L:g}mm" viewBox="0 0 {cfg.BOX_W:g} {cfg.BOX_L:g}" '
        f'font-family="Helvetica, Arial, sans-serif">\n',
        "  <style>\n"
        "    .region{stroke:#333;stroke-width:0.6}\n"
        "    .well{fill:none;stroke:#666;stroke-width:0.4;stroke-dasharray:2 1.5}\n"
        "    .lbl{font-size:5px;fill:#111;text-anchor:middle}\n"
        "    .sub{font-size:3.2px;fill:#444;text-anchor:middle}\n"
        "    .note{font-size:3.6px;fill:#222}\n"
        "  </style>\n",
        f'  <rect x="0" y="0" width="{cfg.BOX_W:g}" height="{cfg.BOX_L:g}" '
        'fill="#fff" stroke="#000" stroke-width="1"/>\n',
        _rect(b["wispwood"], _FILLS["wispwood"]),
        _rect(b["alt_bay"], _FILLS["alt_bay"]),
        _rect(b["small_tray"], _FILLS["small_tray"]),
    ]
    w = b["wispwood"]
    out.append(_text(w.x + w.w / 2, w.y + w.h / 2, "Wispwood tray"))
    a = b["alt_bay"]
    out.append(_text(a.x + a.w / 2, a.y + a.h / 2, "Folded alt stand"))
    for key, label in (("well_card", "Card deck"), ("well_cats", "Cats"), ("well_round", "Round")):
        r = b[key]
        out.append(_rect(r, "none", cls="well"))
        out.append(_text(r.x + r.w / 2, r.y + r.h / 2, label, cls="sub"))
    note = [
        "ON TOP (top tray + loose):",
        "board pieces x5  |  markers x4",
        "1P paw  |  score pad  |  booklet",
    ]
    for i, line in enumerate(note):
        out.append(_text(4, cfg.BOX_L - 24 + i * 6, line, cls="note"))
    out.append("</svg>\n")
    return "".join(out)


def write_svg(path: str) -> None:
    """Write the generated SVG to a file.

    Parameters
    ----------
    path : str
        Destination file path; created or overwritten.
    """
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(generate_svg())
