def build_secret_mission_tray(name="SecretMissionTray",
                              pockets=None):
    """Build the SecretMissionTray shell: hollow box with a grab-bit notch.

    Outer footprint is ``config.SecretMissionTray`` (sized to fit inside the
    Small SecretMissionBox), walls and floor ``WALL_THICKNESS`` thick, open
    top, raised to the box's own interior depth.  One short edge (X=0) has two
    semicircular notches cut into it, stacked along Z with
    ``2 * WALL_THICKNESS`` of wall between them as a grab tab (see
    :func:`_secret_mission_grab_cut`).  The notch cut still leaves a
    plain WALL_THICKNESS of material behind it. 

    Fillet order matches TokenTray/WireTray (see :func:`_fillet_tray_outer_edges`):
    the 12 outer box edges are rounded on the plain, uncut box first, before
    any pocket or notch nearby could thin out the material a fillet needs --
    then the hollow and notch are cut, then the cavity's own rim
    (:func:`_fillet_secret_mission_inner_rim`) is filleted. The grab region's
    own fillet (:func:`_fillet_secret_mission_grab`) is left off for now --
    not every one of its edges fillets cleanly yet.

    Parameters
    ----------
    name : str, optional
        Name for the returned part -- :func:`build_secret_mission_token_tray`
        reuses this same shell under its own name for a second copy.

    pockets : list of (str, x, depth), optional
        List of pocket placements to include in the tray.

    Returns
    -------
    list of (str, Part.Shape)
        ``[(name, shape)]``
    """
    tray = cfg.SecretMissionTray
    outer = Part.makeBox(tray["Height"], tray["Width"], tray["Depth"])
    outer_edges = _box_corner_edges(outer, 0, tray["Height"], 0, tray["Width"], 0, tray["Depth"])
    outer = _fillet_edges_best_effort(outer, _SECRET_TRAY_OUTER_FILLET, outer_edges)


    outer = outer.cut(_secret_mission_grab_cut(tray))

    return outer

    # pockets are cut after the outer fillet, so the fillet doesn't get thinned out
    if not pockets:
        # Default is one pocket the size of the tray
        pockets = [ ("SecretMissionTrayPocket", tray["Depth"] - cfg.WALL_THICKNESS, 
                     tray["Height"] - cfg.WALL_THICKNESS* 2 ) ]
    if pockets:
        for pocket in pockets:
            outer = _cut_pocket(outer, pocket)

    overshoot = 1.0
    inner = Part.makeBox(
        tray["Height"] - 2 * cfg.WALL_THICKNESS,
        tray["Width"] - 2 * cfg.WALL_THICKNESS,
        tray["Depth"] - cfg.WALL_THICKNESS + overshoot,
        Vector(cfg.WALL_THICKNESS, cfg.WALL_THICKNESS, cfg.WALL_THICKNESS),
    )
    inner = inner.cut(_secret_mission_grab_wall_bump(tray))
    shape = outer.cut(inner)
    shape = shape.cut(_secret_mission_grab_cut(tray))
    shape = _fillet_secret_mission_inner_rim(shape, tray)

    return [(name, shape)]

