"""Parametric (Sketcher + PartDesign) rebuild of the keyboard model.

Source of truth after generation is the FCStd (edit dimensions in the GUI via the
`Parameters` spreadsheet). This script is a one-time generator: re-running it
rebuilds the parametric document from scratch and overwrites any GUI edits.

Increment 1: master spreadsheet + palm rest (Left/Right) as PartDesign bodies.
Plate and body parts are added in following increments.
"""

import math
import os
import sys

import FreeCAD as App
import Part

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(BASE_DIR), "tools"))
import pcb as pcb_source          # noqa: E402  -- epro parser, see ADR 260824-001947

TOLERANCE = 0.001

# ---- master parameters: alias -> default value (mm / deg) ----------------------
PCB = pcb_source.load()

PARAMS = {
    "PlateThickness": 4.0,
    "OuterMargin": 11.5,
    "CornerRadius": 5.0,
    "BodyWallThickness": 3.0,
    "BodyHeight": 13.2,
    "RestSideMargin": 6.0,
    "RestRearMargin": 6.0,
    "RestSlantWidth": 10.0,
    "RestSlantAngleDeg": 70.0,
    "RestRearCornerFillet": 3.0,
    "WedgeMinThickness": 1.5,
    "WedgeAlignPinDiameter": 4.0,
    "WedgeAlignPinHeight": 1.3,
    "WedgeAlignPinClearance": 0.3,
    "WedgeAlignPinHoleDepth": 1.5,
    "WedgeAlignPinInset": 15.0,
    "M3ClearanceDiameter": 3.2,
    "M3CountersinkDiameter": 6.0,
    "M3CountersinkDepth": 1.5,
    "SpredsertM3LocatingDiameter": 4.0,
    "SpredsertM3Length": 5.0,
    "M3ScrewTipRelief": 2.0,
    "InsertBossDiameter": 8.0,
    "ScrewCornerOffset": 4.3,
    "StabClipPlateThickness": 1.4,
    "StabClipLedgeWidth": 1.2,
    "StabCutoutMaxWidth": 5.0,
    "StabCutoutHeight": 14.1,
    "StabCutoutYOffset": 0.2,
    "KeyholeSize": 13.96,
    "PalmRestDepth": 80.0,
    "PalmRestRearHeight": 21.0,
    "PalmRestFrontHeight": 8.0,
    "PalmRestFlatDepth": 35.0,
    "PalmRestGap": 5.0,
    "PalmRestFilletRadius": 3.0,
    "PalmRestCrestRadius": 60.0,
    "PalmRestTaperAngleDeg": 10.0,
    # Round neodymium discs (10mm diameter, 2mm thick) hold the palm rest to the
    # body, glued into their pockets. The 10.3mm bore is centred at MagnetCentreHeight
    # in the 13.2mm front wall, which leaves 1.85mm of shell below it and 1.05mm above
    # — thin, and the reason an earlier revision used 8mm instead. It is tolerable
    # because the bore is only MagnetHoleDepth deep: the wall is solid behind it, and
    # the magnet's pull is along Y, taken by the backing block, not by these rims.
    # The palm rest side is unconstrained (its rear face is PalmRestRearHeight tall).
    # The pocket is 2.2mm deep: ~0.1mm of glue
    # plus the 2mm disc leaves it 0.1mm shy of the mating surface, so the two
    # magnets sit 0.2mm apart once the faces close. A 2mm disc loses pull fast
    # with the gap, so err shallow — a pocket that prints under depth ends up
    # flush rather than standing the magnet proud and holding the faces open.
    "MagnetDiameter": 10.0,
    "MagnetHoleDepth": 2.2,
    "MagnetHoleClearance": 0.3,
    "MagnetCentreHeight": 7.0,
    "MagnetBossThickness": 1.5,
    # --- PCB assembly stack -----------------------------------------------------
    # Two independent Z chains meet in the cavity, and neither is measured from the
    # other's end:
    #   from the plate down -- plate top +PlateThickness / plate bottom 0 /
    #     PCB top PlateThickness - PlateToPcb (MX standard, 5.0 below the plate top) /
    #     PCB bottom -2.6 / switch pin tips + solder -4.6
    #   from the cavity floor up -- floor -(BodyHeight - BodyWallThickness) = -10.2,
    #     and both loose boards stand on it in their own cradle.
    # The boards' seats are NOT constants: they are back-solved from PortAxisZ so the
    # RP2040-Zero (1.0mm PCB) and the USB-C breakout (1.6mm PCB) put their
    # receptacles on one axis and one rear-wall opening height serves both. See
    # .forge/adr/260824-224604-drop-aux-board-and-floor-mount-modules.md: the aux
    # board this replaces was 1.0mm short of clearing the switch pins.
    "PcbThickness": 1.6,
    "PlateToPcb": 5.0,
    "PcbSeatClearance": 0.3,
    "PlateCollarDiameter": 6.0,
    # --- rear-wall ports --------------------------------------------------------
    # PortAxisZ is the one number the whole port stack hangs off: -6.45 puts the
    # RP2040-Zero's top at -4.90, which clears the switch pin tips at -4.60 by
    # 0.30mm, and keeps its 1.2mm floor rail clear of its own 1.0mm bottom chip.
    # PortWallThickness == ConnectorOverhang is not a coincidence: the receptacle
    # shell stands only 1.0mm proud of its board, so the wall the plug crosses has
    # to be thinned to that, or the receptacle mouth sits recessed and the plug
    # bottoms out on the case before it seats.
    "PortAxisZ": -6.45,
    "PortWallThickness": 1.0,
    "ConnectorOverhang": 1.0,
    # The opening clears the receptacle SHELL, not the plug. The spec's 8.34 x 2.56
    # is the plug's metal shell -- the cavity inside the receptacle -- and sizing the
    # hole to it would leave the receptacle unable to pass at all. Because
    # ConnectorOverhang == PortWallThickness the receptacle's face sits flush with the
    # outer skin, so its own ~8.94 x 3.26 body occupies the hole; these are that plus
    # ~0.3mm a side. UsbOpeningRadius 1.9 is UsbOpeningHeight / 2 - 0.05, the most
    # add_rounded_rect allows, which makes the ends full semicircles like the
    # receptacle's own outline instead of a slot with square-ish corners.
    "UsbOpeningWidth": 9.5,
    "UsbOpeningHeight": 3.9,
    "UsbOpeningRadius": 1.9,
    # --- the two loose boards ---------------------------------------------------
    "ModuleWidth": 18.0,
    "ModuleDepth": 23.5,
    "ModulePcbThickness": 1.0,
    "ModuleUsbHeight": 3.1,
    "ModuleBottomChip": 1.0,
    "BreakoutWidth": 12.0,
    "BreakoutDepth": 13.5,
    "BreakoutThickness": 1.6,
    # --- cradles ----------------------------------------------------------------
    # CradleRailWidth is the module's two floor rails; the 1.0mm bottom chip hangs
    # between them. CradleWallThickness now applies only to the single end stop;
    # there are intentionally no side walls or retaining lips.
    "CradleWallThickness": 1.5,
    "CradleClearance": 0.3,
    "CradleRailWidth": 2.5,
    # --- where the ports and cradles sit ----------------------------------------
    # All measured from the *inboard* cavity wall's inner face -- the side that
    # faces the other half -- so shrinking OuterMargin later moves the whole port
    # group with the wall instead of stranding it. ADR 260824-224604: these are the
    # case's own choice now, not something read off a board that will never be made.
    # SplitPortInboardOffset is shared by both halves (the PCB's own jack positions
    # were not mirror-symmetric; that asymmetry is dropped).
    # The host-side module is rear-flush and only the right half has one. The other
    # half's module is wired, not plugged, so it hugs the inboard wall beside the
    # 16-pin header and needs a rear offset as well as an inboard one.
    "SplitPortInboardOffset": 17.83,
    "ModuleInboardOffset": 35.88,
    "ModuleInboardOffsetWired": 9.30,
    "ModuleRearOffset": 18.0,
    "DisplayGap": 25.0,
}


# ---- DXF helpers (unchanged from the original generator) -----------------------
def dxf_pairs(path):
    with open(path, "r", encoding="ascii", errors="ignore") as source:
        lines = [line.strip() for line in source]
    return [(int(lines[index]), lines[index + 1]) for index in range(0, len(lines) - 1, 2)]


def dxf_line_loops(path):
    segments = []
    entity = None
    values = {}
    for code, value in dxf_pairs(path):
        if code == 0:
            if entity == "LINE" and all(key in values for key in (10, 20, 11, 21)):
                segments.append(((float(values[10]), float(values[20])),
                                 (float(values[11]), float(values[21]))))
            entity = value
            values = {}
        elif entity == "LINE" and code in (10, 20, 11, 21):
            values[code] = value
    loops = []
    current = []
    last_end = None
    for start, end in segments:
        if last_end is not None and (abs(start[0] - last_end[0]) > TOLERANCE or
                                     abs(start[1] - last_end[1]) > TOLERANCE):
            loops.append(current)
            current = []
        if not current:
            current.append(start)
        current.append(end)
        last_end = end
    if current:
        loops.append(current)
    return loops


def shrink_stab_slots(key_loops):
    """Set each narrow stabilizer cutout's long dimension to StabCutoutHeight,
    keeping its centre fixed (the short dimension is left untouched), then shift
    it by StabCutoutYOffset. The DXF puts slots 0.65 mm below the switch centre
    (X +-11.900, DXF slot 3.30 x 14.201 -- the long dimension is then shrunk to
    StabCutoutHeight = 14.1), all within 0.3 mm of the commonly used Cherry
    values, so offset 0 is the spec position. Which offset actually clears
    depends on the switch and keycap fitted, so it is re-tuned per build from
    printed test coupons (see create_stab_test_coupon.py). The current +0.2 mm
    puts the slot centre 0.45 mm below the switch centre; it replaces an earlier
    +0.5 that had been chosen for a different switch.
    The offset is a fine adjustment, not a clearance fix: the stabilizer wire
    runs *under* the plate, and this plate has no wire passage between the two
    slots, so the housings are fitted first and the wire is hooked on from
    below -- see .forge/adr/260812-224138-stab-wire-under-plate-assembly-order.md.
    Stab slots never overlap a switch cutout in X, so moving them in Y cannot
    introduce a collision with one."""
    max_w = PARAMS["StabCutoutMaxWidth"]
    target = PARAMS["StabCutoutHeight"]
    dy = PARAMS["StabCutoutYOffset"]
    adjusted = []
    for loop in key_loops:
        xs = [p[0] for p in loop]
        ys = [p[1] for p in loop]
        bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
        if min(bx1 - bx0, by1 - by0) > max_w:
            adjusted.append(loop)
            continue
        if (by1 - by0) >= (bx1 - bx0):        # vertical slot: shrink Y
            c = (by0 + by1) / 2.0
            lo, hi = c - target / 2.0, c + target / 2.0
            loop = [(x, hi if abs(y - by1) < abs(y - by0) else lo) for x, y in loop]
        else:                                  # horizontal slot: shrink X
            c = (bx0 + bx1) / 2.0
            lo, hi = c - target / 2.0, c + target / 2.0
            loop = [(hi if abs(x - bx1) < abs(x - bx0) else lo, y) for x, y in loop]
        adjusted.append([(x, y + dy) for x, y in loop])
    return adjusted


def resize_keyholes(key_loops):
    """Set each key switch cutout (the wide ones) to KeyholeSize x KeyholeSize,
    keeping its centre fixed. Narrow stabilizer cutouts are left untouched."""
    max_w = PARAMS["StabCutoutMaxWidth"]
    size = PARAMS["KeyholeSize"]
    adjusted = []
    for loop in key_loops:
        xs = [p[0] for p in loop]
        ys = [p[1] for p in loop]
        bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
        if min(bx1 - bx0, by1 - by0) <= max_w:        # stab slot -> skip
            adjusted.append(loop)
            continue
        cx, cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
        xlo, xhi = cx - size / 2.0, cx + size / 2.0
        ylo, yhi = cy - size / 2.0, cy + size / 2.0
        loop = [(xhi if abs(x - bx1) < abs(x - bx0) else xlo,
                 yhi if abs(y - by1) < abs(y - by0) else ylo) for x, y in loop]
        adjusted.append(loop)
    return adjusted


def pcb_offset(side, key_loops):
    """Rigid offset that maps PCB (epro) coordinates into this DXF's frame.

    Both describe the same physical switches, so the offset is read off the keys
    themselves rather than configured -- and because every key must agree on it,
    a bad read fails loudly instead of shifting the case by a few millimetres.
    Only the 14mm switch cutouts are matched; the narrow stabilizer slots have no
    counterpart in the switch list."""
    centres = []
    for loop in key_loops:
        xs = [p[0] for p in loop]
        ys = [p[1] for p in loop]
        if abs((max(xs) - min(xs)) - 14.0) < 0.1 and abs((max(ys) - min(ys)) - 14.0) < 0.1:
            centres.append(((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0))
    keys = PCB.matrix(side)
    if len(centres) != len(keys):
        raise ValueError("%s: DXF has %d switch cutouts, PCB has %d"
                         % (side, len(centres), len(keys)))
    dx = min(k.x for k in keys) - min(c[0] for c in centres)
    dy = min(k.y for k in keys) - min(c[1] for c in centres)
    worst = 0.0
    for cx, cy in centres:
        worst = max(worst, min(max(abs(cx + dx - k.x), abs(cy + dy - k.y)) for k in keys))
    if worst > 0.1:
        raise ValueError("%s: DXF and PCB switch positions differ by %.3fmm" % (side, worst))
    return -dx, -dy, worst


def compute_layout(dxf_filename, side):
    """Plate/body footprint from the DXF key cutouts (first loop is the perimeter).

    Also carries what the case needs from the PCB, mapped into this frame: the screw
    datum (the PCB's own mounting holes) and the PCB outline. ADR 260824-001947 makes
    the epro the source of those numbers, so nothing here is a literal.

    The rear-wall ports are *not* among them any more. They used to be read off the
    aux board's connectors, and reading coordinates off a board that will never be
    made is exactly the silently-drifting derivative 001947 warned about -- so they
    are the case's own parameters now (ADR 260824-224604), measured from the inboard
    cavity wall. `inboard_x`/`inboard_dir` are that datum: the half's inner face on
    the side that faces the other half, and the direction that runs away from it."""
    loops = dxf_line_loops(os.path.join(BASE_DIR, dxf_filename))
    key_loops = loops[1:]
    # Outer footprint is derived from the original cutouts so the stab-height
    # tweak below cannot move the plate/body outline.
    xs = [p[0] for loop in key_loops for p in loop]
    ys = [p[1] for loop in key_loops for p in loop]
    margin = PARAMS["OuterMargin"]
    wall = PARAMS["BodyWallThickness"]
    x_min, x_max = min(xs) - margin, max(xs) + margin
    ox, oy, worst = pcb_offset(side, key_loops)
    board = PCB.main(side)
    outline = board.outline
    print("  %s PCB offset (%.2f, %.2f), worst key deviation %.3fmm" % (side, ox, oy, worst))
    return {
        "x_min": x_min,
        "y_min": min(ys) - margin,
        "x_max": x_max,
        "y_max": max(ys) + margin,
        "key_loops": resize_keyholes(shrink_stab_slots(key_loops)),
        # The right half's inboard edge is its x minimum, the left half's its
        # maximum -- they meet in the middle of the desk.
        "inboard_x": (x_min + wall) if side == "right" else (x_max - wall),
        "inboard_dir": 1.0 if side == "right" else -1.0,
        # --- PCB-derived, already in this frame ---
        "screw_xy": [(h.x + ox, h.y + oy) for h in board.mounting_holes],
        "screw_diameter": board.mounting_holes[0].diameter,
        "pcb_rect": (outline.x_min + ox, outline.y_min + oy,
                     outline.x_max + ox, outline.y_max + oy, outline.radius),
    }


def stack_z():
    """The assembly Z levels.

    Two chains, meeting in the cavity. The plate chain runs down from
    PlateThickness; the port chain runs *outwards* from PortAxisZ, because the two
    receptacles have to share one height even though the boards under them are
    1.0mm and 1.6mm thick. Both receptacles sit directly on their board, so the
    board's top face is the connector's underside -- one level for both cradles --
    and each seat is that minus its own board thickness. Nothing here is a literal:
    change PortAxisZ and both cradles follow it."""
    plate = PARAMS["PlateThickness"]
    pcb_top = plate - PARAMS["PlateToPcb"]
    pcb_bottom = pcb_top - PARAMS["PcbThickness"]
    port_axis = PARAMS["PortAxisZ"]
    board_top = port_axis - PARAMS["ModuleUsbHeight"] / 2.0
    return {"pcb_top": pcb_top,
            "pcb_bottom": pcb_bottom,
            "floor_z": -(PARAMS["BodyHeight"] - PARAMS["BodyWallThickness"]),
            "port_axis": port_axis,
            "board_top": board_top,
            "module_seat": board_top - PARAMS["ModulePcbThickness"],
            "breakout_seat": board_top - PARAMS["BreakoutThickness"],
            "module_top": board_top + PARAMS["ModuleUsbHeight"]}


# ---- Sketcher helpers ----------------------------------------------------------
def add_rounded_rect(sketch, x0, y0, x1, y1, radius):
    """Add a closed rounded-rectangle wire (4 lines + 4 arcs) in the sketch plane."""
    radius = min(radius, (x1 - x0) / 2.0 - 0.05, (y1 - y0) / 2.0 - 0.05)
    normal = App.Vector(0, 0, 1)

    def line(ax, ay, bx, by):
        return Part.LineSegment(App.Vector(ax, ay, 0), App.Vector(bx, by, 0))

    def arc(cx, cy, deg0, deg1):
        circle = Part.Circle(App.Vector(cx, cy, 0), normal, radius)
        return Part.ArcOfCircle(circle, math.radians(deg0), math.radians(deg1))

    geometry = [
        line(x0 + radius, y0, x1 - radius, y0),
        arc(x1 - radius, y0 + radius, 270, 360),
        line(x1, y0 + radius, x1, y1 - radius),
        arc(x1 - radius, y1 - radius, 0, 90),
        line(x1 - radius, y1, x0 + radius, y1),
        arc(x0 + radius, y1 - radius, 90, 180),
        line(x0, y1 - radius, x0, y0 + radius),
        arc(x0 + radius, y0 + radius, 180, 270),
    ]
    for geo in geometry:
        sketch.addGeometry(geo, False)


def add_rounded_polygon(sketch, points, radius):
    """Add a closed wire through `points` (convex, counter-clockwise) with every
    corner rounded. `radius` is either one value for all corners or one value per
    point, where 0 leaves that corner sharp. Same output as add_rounded_rect for a
    rectangle, but also handles corners that are not right angles."""
    normal = App.Vector(0, 0, 1)
    radii = radius if isinstance(radius, (list, tuple)) else [radius] * len(points)
    corners = []
    for index in range(len(points)):
        cx, cy = points[index]
        corner = App.Vector(cx, cy, 0)
        if radii[index] <= 0:
            corners.append((corner, corner, None))
            continue
        px, py = points[index - 1]
        nx, ny = points[(index + 1) % len(points)]
        to_prev = (App.Vector(px, py, 0) - corner).normalize()
        to_next = (App.Vector(nx, ny, 0) - corner).normalize()
        half = math.acos(max(-1.0, min(1.0, to_prev.dot(to_next)))) / 2.0
        setback = radii[index] / math.tan(half)
        corners.append((corner + to_prev * setback, corner + to_next * setback,
                        corner + (to_prev + to_next).normalize() * (radii[index] / math.sin(half))))

    def angle(point, centre):
        return math.atan2(point.y - centre.y, point.x - centre.x)

    for index, (entry, leave, centre) in enumerate(corners):
        if centre is not None:
            circle = Part.Circle(centre, normal, radii[index])
            sketch.addGeometry(
                Part.ArcOfCircle(circle, angle(entry, centre), angle(leave, centre)), False)
        sketch.addGeometry(
            Part.LineSegment(leave, corners[(index + 1) % len(corners)][0]), False)


def add_polygon(sketch, points):
    for index in range(len(points)):
        ax, ay = points[index]
        bx, by = points[(index + 1) % len(points)]
        sketch.addGeometry(
            Part.LineSegment(App.Vector(ax, ay, 0), App.Vector(bx, by, 0)), False)


# Sketch placed on a plane whose normal is +X (local u -> global Y, v -> global Z).
YZ_ROTATION = App.Rotation(0.5, 0.5, 0.5, 0.5)

# Sketch on a plane whose normal is -Y (local u -> global X, v -> global Z).
XZ_ROTATION = App.Rotation(App.Vector(1, 0, 0), 90)


def rest_tilt(layout):
    """Nose-up angle (rad) the Body_Rest wedge props the case at once it is on the desk."""
    depth = (layout["y_max"] - PARAMS["RestRearMargin"]) - layout["y_min"]
    return math.asin(PARAMS["RestSlantWidth"]
                     * math.sin(math.radians(PARAMS["RestSlantAngleDeg"])) / depth)


def wedge_front_y(layout):
    """Y where the tilt wedge is cut off -- where it first reaches WedgeMinThickness.

    The wedge tapers to nothing at the case's front edge. Fused to the body that is
    just the line where it meets the bottom face, but as a separate part it would be
    a feather edge that curls off the bed, so everything thinner is dropped. The rest
    position is unaffected: the body's bottom plane extended forward still meets the
    desk at the front edge, so the case sits at the same angle and height."""
    return layout["y_min"] + PARAMS["WedgeMinThickness"] / math.tan(rest_tilt(layout))


def wedge_pin_centres(layout):
    """XY of the two alignment pins, on the wedge's top face.

    Read by both the wedge (which pads the pins) and the body (which pockets the
    matching holes), so the two cannot drift apart. Set well apart across the width:
    two pins constrain rotation, and the further apart they are the less angular
    error a given fit tolerance allows."""
    inset = PARAMS["WedgeAlignPinInset"]
    rx0 = layout["x_min"] + PARAMS["RestSideMargin"]
    rx1 = layout["x_max"] - PARAMS["RestSideMargin"]
    y = (wedge_front_y(layout) + (layout["y_max"] - PARAMS["RestRearMargin"])) / 2.0
    return [(rx0 + inset, y), (rx1 - inset, y)]


def magnet_centres_x(layout):
    """X positions of the magnet pair, at a quarter and three quarters of the width."""
    span = layout["x_max"] - layout["x_min"]
    return [layout["x_min"] + span * fraction for fraction in (0.25, 0.75)]


def add_magnet_pockets(document, body, name, placement, centres):
    """Bore the magnet pockets into `placement`'s plane, one per entry in `centres`."""
    sketch = body.newObject("Sketcher::SketchObject", name + "_Magnet_Holes")
    sketch.Placement = placement
    for u, v in centres:
        sketch.addGeometry(Part.Circle(
            App.Vector(u, v, 0), App.Vector(0, 0, 1),
            (PARAMS["MagnetDiameter"] + PARAMS["MagnetHoleClearance"]) / 2), False)
    pocket = body.newObject("PartDesign::Pocket", name + "_Magnet_Pockets")
    pocket.Profile = sketch
    pocket.Length = PARAMS["MagnetHoleDepth"]
    pocket.setExpression("Length", u"Parameters.MagnetHoleDepth")
    document.recompute()
    return pocket


def build_spreadsheet(document):
    sheet = document.addObject("Spreadsheet::Sheet", "Parameters")
    for row, (name, value) in enumerate(PARAMS.items(), start=1):
        sheet.set("A%d" % row, name)
        sheet.set("B%d" % row, repr(float(value)))
    document.recompute()
    for row, name in enumerate(PARAMS, start=1):
        sheet.setAlias("B%d" % row, name)
    document.recompute()
    return sheet


# ---- Palm rest -----------------------------------------------------------------
def build_palm_rest(document, side, layout):
    x0, x1 = layout["x_min"], layout["x_max"]
    y_rear = layout["y_min"] - PARAMS["PalmRestGap"]
    y_front = y_rear - PARAMS["PalmRestDepth"]
    z_base = -PARAMS["BodyHeight"]
    rear_h = PARAMS["PalmRestRearHeight"]
    front_h = PARAMS["PalmRestFrontHeight"]
    flat = PARAMS["PalmRestFlatDepth"]
    radius = PARAMS["CornerRadius"]
    # Both flanks lean inwards by PalmRestTaperAngleDeg, so the rear edge keeps the
    # plate width while the front edge (nearest the user) narrows.
    inset = PARAMS["PalmRestDepth"] * math.tan(math.radians(PARAMS["PalmRestTaperAngleDeg"]))

    body = document.addObject("PartDesign::Body", side + "_Palm_Rest")

    base = body.newObject("Sketcher::SketchObject", side + "_Palm_Base")
    base.Placement = App.Placement(App.Vector(0, 0, z_base), App.Rotation())
    # Front corners keep the CornerRadius rounding; the two rear corners stay sharp
    # so the rest butts squarely against the case.
    add_rounded_polygon(base, [
        (x0 + inset, y_front),
        (x1 - inset, y_front),
        (x1, y_rear),
        (x0, y_rear),
    ], [radius, radius, 0, 0])

    pad = body.newObject("PartDesign::Pad", side + "_Palm_Pad")
    pad.Profile = base
    pad.Length = rear_h
    pad.setExpression("Length", u"Parameters.PalmRestRearHeight")
    document.recompute()

    z_top = z_base + rear_h

    # The case stands nose-up on its Body_Rest wedge while the palm rest sits flat on
    # the desk, so in the desk frame the body's front face leans forward by the tilt
    # angle while a plain vertical rear face would not. Lean the rear face by the same
    # angle: the two faces then meet flush over their whole height instead of touching
    # along the bottom edge only, which is what lets the magnets pull face to face.
    tilt = rest_tilt(layout)
    lean = math.tan(tilt)

    def rear_at(z):
        return y_rear - (z - z_base) * lean

    lean_sk = body.newObject("Sketcher::SketchObject", side + "_Palm_LeanCut")
    lean_sk.Placement = App.Placement(App.Vector(0, 0, 0), YZ_ROTATION)
    z_lo, z_hi = z_base - 1.0, z_top + 1.0
    add_polygon(lean_sk, [
        (rear_at(z_lo), z_lo),
        (rear_at(z_hi), z_hi),
        (y_rear + 5.0, z_hi),
        (y_rear + 5.0, z_lo),
    ])
    lean_cut = body.newObject("PartDesign::Pocket", side + "_Palm_Lean")
    lean_cut.Profile = lean_sk
    lean_cut.Type = "ThroughAll"
    lean_cut.Midplane = True
    document.recompute()

    # Remove the wedge above the sloped top: quad on a YZ-normal plane, symmetric
    # through-all pocket so it cuts the full X width regardless of position.
    cut = body.newObject("Sketcher::SketchObject", side + "_Palm_WedgeCut")
    cut.Placement = App.Placement(App.Vector(0, 0, 0), YZ_ROTATION)
    add_polygon(cut, [
        (y_rear - flat, z_top),
        (y_front - 2.0, z_base + front_h),
        (y_front - 2.0, z_top + 2.0),
        (y_rear - flat, z_top + 2.0),
    ])
    pocket = body.newObject("PartDesign::Pocket", side + "_Palm_Wedge")
    pocket.Profile = cut
    pocket.Type = "ThroughAll"
    pocket.Midplane = True
    document.recompute()

    # The crest (where the flat deck meets the slope) is filleted separately: the two
    # faces meet at a very obtuse angle, so PalmRestFilletRadius would only round a
    # fraction of a millimetre there and the crest would still look sharp.
    def crest_edges(shape):
        return ["Edge%d" % (index + 1) for index, edge in enumerate(shape.Edges)
                if edge.Vertexes
                and all(abs(v.Point.y - (y_rear - flat)) < TOLERANCE
                        and abs(v.Point.z - z_top) < TOLERANCE for v in edge.Vertexes)]

    # The crest is filleted before the small edges: run the other way round and the
    # R3 fillet leaves 0.14mm slivers at both ends of the crest, which makes the
    # crest fillet fail at every radius.
    crest = body.newObject("PartDesign::Fillet", side + "_Palm_Crest")
    crest.Base = (pocket, crest_edges(pocket.Shape))
    crest.Radius = PARAMS["PalmRestCrestRadius"]
    crest.setExpression("Radius", u"Parameters.PalmRestCrestRadius")
    document.recompute()

    # Edges bounding the crest surface are already tangent continuous, so they must
    # not be filleted again.
    tip = crest.Shape
    smooth = [edge for face in tip.Faces
              if "Cylinder" in face.Surface.TypeId
              and abs(face.Surface.Radius - PARAMS["PalmRestCrestRadius"]) < TOLERANCE
              for edge in face.Edges]
    top_edges = ["Edge%d" % (index + 1) for index, edge in enumerate(tip.Edges)
                 if edge.Vertexes and min(v.Point.z for v in edge.Vertexes) > z_base + front_h / 2
                 and not any(edge.isSame(other) for other in smooth)]
    fillet = body.newObject("PartDesign::Fillet", side + "_Palm_Fillet")
    fillet.Base = (crest, top_edges)
    fillet.Radius = PARAMS["PalmRestFilletRadius"]
    fillet.setExpression("Radius", u"Parameters.PalmRestFilletRadius")
    document.recompute()

    # Magnet seats, bored perpendicular to the leaning rear face (not along Y) so the
    # magnet lies flat in its pocket. The sketch plane is tilted with the face, its
    # local +X follows global X and its origin sits on the face at the magnet height,
    # so each magnet centre is just (x, 0) in sketch coordinates.
    z_centre = z_base + PARAMS["MagnetCentreHeight"]
    add_magnet_pockets(
        document, body, side + "_Palm",
        App.Placement(App.Vector(0, rear_at(z_centre), z_centre),
                      App.Rotation(App.Vector(1, 0, 0), math.degrees(tilt) - 90)),
        [(x, 0.0) for x in magnet_centres_x(layout)])

    if body.ViewObject:
        body.ViewObject.ShapeColor = (0.13, 0.13, 0.13)
    return body


# ---- Switch plate --------------------------------------------------------------
def build_plate(document, side, layout, color):
    x0, y0 = layout["x_min"], layout["y_min"]
    x1, y1 = layout["x_max"], layout["y_max"]
    thickness = PARAMS["PlateThickness"]
    radius = PARAMS["CornerRadius"]
    stack = stack_z()

    body = document.addObject("PartDesign::Body", side + "_Switch_Plate")

    outline = body.newObject("Sketcher::SketchObject", side + "_Plate_Outline")
    outline.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    add_rounded_rect(outline, x0, y0, x1, y1, radius)
    pad = body.newObject("PartDesign::Pad", side + "_Plate_Pad")
    pad.Profile = outline
    pad.Length = thickness
    pad.setExpression("Length", u"Parameters.PlateThickness")
    document.recompute()

    # Key cutouts: the imported DXF polygons, one sketch, symmetric through pocket.
    keys = body.newObject("Sketcher::SketchObject", side + "_Key_Cutouts")
    keys.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    for loop in layout["key_loops"]:
        pts = list(loop)
        if (len(pts) > 1 and abs(pts[0][0] - pts[-1][0]) < TOLERANCE
                and abs(pts[0][1] - pts[-1][1]) < TOLERANCE):
            pts = pts[:-1]
        add_polygon(keys, pts)
    key_pocket = body.newObject("PartDesign::Pocket", side + "_Key_Pockets")
    key_pocket.Profile = keys
    key_pocket.Type = "ThroughAll"
    key_pocket.Midplane = True
    document.recompute()

    # M3 countersunk mounting holes. The datum is the PCB's own four mounting
    # holes, not an inset from the case corner: one screw has to pass through
    # plate, PCB and boss, so the three cannot each pick their own position.
    # (The old corner inset happened to land within 0.5mm of them, but only
    # because both were "just outside the key field" -- OuterMargin moved and
    # that coincidence went with it.)
    screw_xy = layout["screw_xy"]
    # Clamp collars on the underside. The plate bottom sits at z=0 and the PCB top
    # is PlateToPcb below the plate top, so with a 4mm plate there is a 1mm air gap
    # between them -- a screw pulled tight would clamp the plate against the wall
    # rim and leave the PCB loose. These collars bridge exactly that gap, so the
    # screw stack becomes plate -> collar -> PCB -> boss.
    collar_drop = -stack["pcb_top"]
    if collar_drop > TOLERANCE:
        collar = body.newObject("Sketcher::SketchObject", side + "_Plate_Collars")
        collar.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
        for x, y in screw_xy:
            collar.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1),
                                           PARAMS["PlateCollarDiameter"] / 2), False)
        collar_pad = body.newObject("PartDesign::Pad", side + "_Plate_Collar_Pad")
        collar_pad.Profile = collar
        collar_pad.Length = collar_drop
        collar_pad.Reversed = True
        document.recompute()

    holes = body.newObject("Sketcher::SketchObject", side + "_Screw_Holes")
    holes.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    for x, y in screw_xy:
        holes.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1),
                                      PARAMS["M3ClearanceDiameter"] / 2), False)
    hole_pocket = body.newObject("PartDesign::Pocket", side + "_Screw_Pockets")
    hole_pocket.Profile = holes
    hole_pocket.Type = "ThroughAll"
    hole_pocket.Midplane = True
    document.recompute()

    # Top-side countersink: chamfer the hole edges on the top face (guarded).
    try:
        widen = (PARAMS["M3CountersinkDiameter"] - PARAMS["M3ClearanceDiameter"]) / 2
        shape = hole_pocket.Shape
        edge_names = []
        for index, edge in enumerate(shape.Edges):
            if (type(edge.Curve).__name__ == "Circle"
                    and abs(edge.Curve.Radius - PARAMS["M3ClearanceDiameter"] / 2) < 0.05
                    and abs(edge.CenterOfMass.z - thickness) < 0.05):
                edge_names.append("Edge%d" % (index + 1))
        if edge_names:
            chamfer = body.newObject("PartDesign::Chamfer", side + "_Screw_Countersink")
            chamfer.Base = (hole_pocket, edge_names)
            chamfer.ChamferType = 1
            chamfer.Size = widen
            chamfer.Size2 = PARAMS["M3CountersinkDepth"]
            document.recompute()
    except Exception as chamfer_error:
        print("  countersink chamfer skipped (%s): %s" % (side, str(chamfer_error)[:40]))
        document.recompute()

    # Plate-mount stabilizer clip relief: on the two long edges of each narrow
    # stabilizer cutout, widen the slot by StabClipLedgeWidth from the underside up
    # to (thickness - StabClipPlateThickness), leaving a StabClipPlateThickness ledge
    # at the plate top so the clip can latch (the 1.4 mm ledge / 1.2 mm relief callouts).
    ledge = PARAMS["StabClipLedgeWidth"]
    max_w = PARAMS["StabCutoutMaxWidth"]
    stab = body.newObject("Sketcher::SketchObject", side + "_Stab_Relief")
    stab.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    stab_count = 0
    for loop in layout["key_loops"]:
        xs = [p[0] for p in loop]
        ys = [p[1] for p in loop]
        bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
        if min(bx1 - bx0, by1 - by0) > max_w:
            continue
        add_polygon(stab, [(bx0, by1), (bx1, by1), (bx1, by1 + ledge), (bx0, by1 + ledge)])
        add_polygon(stab, [(bx0, by0 - ledge), (bx1, by0 - ledge), (bx1, by0), (bx0, by0)])
        stab_count += 1
    if stab_count:
        stab_pocket = body.newObject("PartDesign::Pocket", side + "_Stab_Relief_Pocket")
        stab_pocket.Profile = stab
        stab_pocket.Length = thickness - PARAMS["StabClipPlateThickness"]
        stab_pocket.Reversed = True
        stab_pocket.setExpression(
            "Length", u"Parameters.PlateThickness - Parameters.StabClipPlateThickness")
        document.recompute()
    else:
        document.removeObject(stab.Name)
    print("  %s stab cutouts relieved: %d" % (side, stab_count))

    if body.ViewObject:
        body.ViewObject.ShapeColor = color
    return body


# ---- Floor-mounted board cradles and the rear-wall ports ------------------------
def add_port_seat(document, body, name, centre_x, half_width, y_inner, y_outer,
                  floor_z, roof_low, roof_slope):
    """Thin the rear wall locally so a plug can reach the receptacle.

    The wall is BodyWallThickness; the receptacle shell stands only ConnectorOverhang
    (1.0mm) proud of its board. Drill straight through 3mm and the receptacle mouth
    ends up 2mm inside the case, where the plug's 6.5mm of exposed metal bottoms out
    on the case before it seats. So the inner face is cut back to PortWallThickness
    over the width the board needs -- that is the whole reason this feature exists,
    and it is why the cradle behind it is dimensioned to the seat face and not to
    the cavity wall.

    The roof is a ramp, not a ceiling. A flat roof would be a ~20mm-wide downward
    face with material within reach on only one of its four sides (the outer skin),
    which is precisely what verify_no_support.py fails: it cannot be bridged, only
    drooped. Climbing `roof_slope` mm for every mm it runs outward puts it at 51 deg
    off horizontal, inside the 45 deg a slicer carries unsupported, so the check
    never has to judge it at all. `roof_low` has to clear both the connector and the
    top of the opening -- if the roof dipped into the opening's height the plug would
    be crossing 3mm of wall again at its top corners."""
    run = y_outer - y_inner
    over = 0.6                     # start inside the cavity void, so the cut
                                   # overlaps the wall instead of meeting its face
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.Placement = App.Placement(App.Vector(centre_x + half_width, 0, 0),
                                     YZ_ROTATION)
    add_polygon(sketch, [(y_inner - over, floor_z),
                         (y_outer, floor_z),
                         (y_outer, roof_low + run * roof_slope),
                         (y_inner - over, roof_low - over * roof_slope)])
    pocket = body.newObject("PartDesign::Pocket", name + "_Pocket")
    pocket.Profile = sketch
    pocket.Length = 2 * half_width
    document.recompute()
    return pocket


def cradle_pocket(centre_x, width, depth, y_far):
    """The hole a board drops into: board plus CradleClearance on every side.

    `y_far` is the pocket's rear face -- the port seat for a rear-flush cradle, so
    the board's own rear edge is what stops it and the receptacle lands in the
    opening."""
    clear = PARAMS["CradleClearance"]
    half = width / 2.0 + clear
    return (centre_x - half, centre_x + half, y_far - depth - 2 * clear, y_far)


def add_cradle(document, body, name, pocket, seat_z, open_axis, open_sign,
               rail_width=0.0):
    """One board support standing on the cavity floor: seat and end stop.

    `open_axis`/`open_sign` point toward the connector or wiring side. The opposite
    edge gets a stop, while both long side guides are deliberately left open for
    easier board insertion and wiring access. `rail_width` 0 lays a solid seat pad;
    anything else lays two rails, leaving the module's ModuleBottomChip hanging
    clear between them."""
    stack = stack_z()
    floor_z, board_top = stack["floor_z"], stack["board_top"]
    w = PARAMS["CradleWallThickness"]
    x0, x1, y0, y1 = pocket

    # 1. Seat. Solid pad, or two rails at the pocket's X extremes.
    seat_sk = body.newObject("Sketcher::SketchObject", name + "_Seat")
    seat_sk.Placement = App.Placement(App.Vector(0, 0, floor_z), App.Rotation())
    if rail_width > 0:
        add_polygon(seat_sk, [(x0, y0), (x0 + rail_width, y0),
                              (x0 + rail_width, y1), (x0, y1)])
        add_polygon(seat_sk, [(x1 - rail_width, y0), (x1, y0),
                              (x1, y1), (x1 - rail_width, y1)])
    else:
        add_polygon(seat_sk, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    seat_pad = body.newObject("PartDesign::Pad", name + "_Seat_Pad")
    seat_pad.Profile = seat_sk
    seat_pad.Length = seat_z - floor_z
    document.recompute()

    # 2. End stop only. The former long side walls and their retaining lips were
    # removed intentionally; these are the side guides visible beside both boards.
    if open_axis == "y":
        yb = y0 if open_sign > 0 else y1
        yo = yb - open_sign * w
        points = [(x0 - w, min(yb, yo)), (x1 + w, min(yb, yo)),
                  (x1 + w, max(yb, yo)), (x0 - w, max(yb, yo))]
    else:
        _, xb = (x1, x0) if open_sign > 0 else (x0, x1)
        xo = xb - open_sign * w
        points = [(min(xb, xo), y0 - w), (max(xb, xo), y0 - w),
                  (max(xb, xo), y1 + w), (min(xb, xo), y1 + w)]
    stop_sk = body.newObject("Sketcher::SketchObject", name + "_End_Stop")
    stop_sk.Placement = App.Placement(App.Vector(0, 0, floor_z), App.Rotation())
    add_polygon(stop_sk, points)
    stop_pad = body.newObject("PartDesign::Pad", name + "_End_Stop_Pad")
    stop_pad.Profile = stop_sk
    stop_pad.Length = board_top - floor_z
    document.recompute()
    return pocket


# ---- Keyboard body (core: shell + cavity + insert bosses/pockets) --------------
def build_body(document, side, layout, color, host_usb=False):
    """The case body. `host_usb` says this half carries the host port, which decides
    both openings and where its controller module sits: rear-flush behind a port seat
    when true, hugging the inboard wall beside the 16-pin header when false. It is a
    plain choice of half now -- with the module hand-wired instead of plugged into an
    aux board, nothing in the PCB constrains it (ADR 260824-224604 retires the
    260824-003937 reasoning that forced MASTER_LEFT)."""
    x0, y0 = layout["x_min"], layout["y_min"]
    x1, y1 = layout["x_max"], layout["y_max"]
    height = PARAMS["BodyHeight"]
    wall = PARAMS["BodyWallThickness"]
    radius = PARAMS["CornerRadius"]
    cavity_h = height - wall
    z_base = -height
    r_inner = max(radius - wall, 0.5)
    stack = stack_z()
    screw_xy = layout["screw_xy"]

    body = document.addObject("PartDesign::Body", side + "_Keyboard_Body")

    # 1. Outer shell.
    shell = body.newObject("Sketcher::SketchObject", side + "_Body_Outline")
    shell.Placement = App.Placement(App.Vector(0, 0, z_base), App.Rotation())
    add_rounded_rect(shell, x0, y0, x1, y1, radius)
    pad = body.newObject("PartDesign::Pad", side + "_Body_Pad")
    pad.Profile = shell
    pad.Length = height
    pad.setExpression("Length", u"Parameters.BodyHeight")
    document.recompute()

    # 2. Inner cavity: blind pocket from the top face, leaving a floor of `wall`.
    cav_sk = body.newObject("Sketcher::SketchObject", side + "_Body_Cavity")
    cav_sk.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    add_rounded_rect(cav_sk, x0 + wall, y0 + wall, x1 - wall, y1 - wall, r_inner)
    cav = body.newObject("PartDesign::Pocket", side + "_Body_Cavity_Pocket")
    cav.Profile = cav_sk
    cav.Length = cavity_h
    cav.setExpression("Length", u"Parameters.BodyHeight - Parameters.BodyWallThickness")
    document.recompute()

    # 3. Insert bosses: pillars rising from the cavity floor.
    boss_sk = body.newObject("Sketcher::SketchObject", side + "_Body_Bosses")
    boss_sk.Placement = App.Placement(App.Vector(0, 0, -cavity_h), App.Rotation())
    for x, y in screw_xy:
        boss_sk.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1),
                                        PARAMS["InsertBossDiameter"] / 2), False)
    # The boss stops at the PCB underside, not at the top rim: the PCB seats on it
    # and the plate lands on the wall rim above, so one screw clamps the sandwich.
    boss_top = stack["pcb_bottom"]
    boss_pad = body.newObject("PartDesign::Pad", side + "_Body_Boss_Pad")
    boss_pad.Profile = boss_sk
    boss_pad.Length = boss_top - (z_base + wall)
    document.recompute()

    # 4. Insert pockets bored into the bosses from the top.
    ins_sk = body.newObject("Sketcher::SketchObject", side + "_Body_Insert_Holes")
    ins_sk.Placement = App.Placement(App.Vector(0, 0, boss_top), App.Rotation())
    for x, y in screw_xy:
        ins_sk.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1),
                                       PARAMS["SpredsertM3LocatingDiameter"] / 2), False)
    ins = body.newObject("PartDesign::Pocket", side + "_Body_Insert_Pockets")
    ins.Profile = ins_sk
    ins.Length = PARAMS["SpredsertM3Length"] + PARAMS["M3ScrewTipRelief"]
    ins.setExpression("Length", u"Parameters.SpredsertM3Length + Parameters.M3ScrewTipRelief")
    document.recompute()

    # 5. Alignment holes for the tilt wedge, bored up into the bottom face. The
    # wedge is no longer fused here: inset from the body outline it left a 6 mm rim
    # of the bottom face floating, which is 91% of everything the printer had to
    # support. It is a separate glued part now -- see build_tilt_wedge and
    # .forge/adr/260819-204944-tilt-wedge-as-separate-glued-part.md. These holes take
    # its pins. They stop half way into the floor, so nothing opens into the cavity.
    pin_r = (PARAMS["WedgeAlignPinDiameter"] + PARAMS["WedgeAlignPinClearance"]) / 2
    pin_sk = body.newObject("Sketcher::SketchObject", side + "_Wedge_Pin_Holes")
    pin_sk.Placement = App.Placement(App.Vector(0, 0, z_base), App.Rotation())
    for x, y in wedge_pin_centres(layout):
        pin_sk.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1),
                                       pin_r), False)
    pin_pocket = body.newObject("PartDesign::Pocket", side + "_Wedge_Pin_Pockets")
    pin_pocket.Profile = pin_sk
    pin_pocket.Length = PARAMS["WedgeAlignPinHoleDepth"]
    pin_pocket.Reversed = True
    pin_pocket.setExpression("Length", u"Parameters.WedgeAlignPinHoleDepth")
    document.recompute()

    # 6. Magnet seats in the front wall, facing the palm rest. A 2.2mm pocket stops
    # short of breaching the BodyWallThickness wall, but only by 0.8mm — too thin to
    # survive the palm rest being pulled off — so pad a local backing block onto the
    # inside of the wall, leaving 2.3mm behind each magnet. Clearing the switch pins
    # is not what bounds the pad: the PCB outline reaches further forward than the
    # front switch row, and at MagnetBossThickness 3.0 the block ran 0.32mm into it.
    # 1.5 puts its inner face 1.18mm clear of the PCB's front edge.
    magnet_x = magnet_centres_x(layout)
    hole_r = (PARAMS["MagnetDiameter"] + PARAMS["MagnetHoleClearance"]) / 2
    pad_half = hole_r + 3.0
    back_sk = body.newObject("Sketcher::SketchObject", side + "_Magnet_Backing")
    back_sk.Placement = App.Placement(App.Vector(0, 0, -cavity_h), App.Rotation())
    for x in magnet_x:
        add_polygon(back_sk, [
            (x - pad_half, y0 + wall),
            (x + pad_half, y0 + wall),
            (x + pad_half, y0 + wall + PARAMS["MagnetBossThickness"]),
            (x - pad_half, y0 + wall + PARAMS["MagnetBossThickness"]),
        ])
    back_pad = body.newObject("PartDesign::Pad", side + "_Magnet_Backing_Pad")
    back_pad.Profile = back_sk
    back_pad.Length = cavity_h
    back_pad.setExpression("Length", u"Parameters.BodyHeight - Parameters.BodyWallThickness")
    document.recompute()

    # The front face is vertical here; it acquires the tilt when the case sits on its
    # wedge, and the palm rest's rear face is leaned to match (see build_palm_rest).
    add_magnet_pockets(
        document, body, side + "_Body",
        App.Placement(App.Vector(0, y0, 0), XZ_ROTATION),
        [(x, z_base + PARAMS["MagnetCentreHeight"]) for x in magnet_x])

    # 7. Rear-wall ports and the two floor-mounted board cradles. y_max (y1) is the
    # rear wall.
    #
    # There is no aux board any more: the RP2040-Zero and the USB-C breakout are
    # loose boards standing on the cavity floor, hand-wired to the main PCB's 16-pin
    # header pads (ADR 260824-224604). So this section builds, per half, the port
    # seats that thin the rear wall to PortWallThickness, the cradles that hold each
    # board at the height PortAxisZ demands, and the openings through the thinned
    # wall.
    floor_z = stack["floor_z"]
    y_rear = y1
    y_cav = y1 - wall                                # cavity's rear inner face
    y_seat = y1 - PARAMS["PortWallThickness"]         # what a rear-flush board bears on
    inboard = layout["inboard_x"]
    step = layout["inboard_dir"]
    seat_margin = 0.5          # port seat runs this far past each cradle wall face,
                               # so the board bears on 1.0mm of wall across its whole
                               # width -- a patch narrower than the board leaves its
                               # rear corners on the untouched 3.0mm and holds the
                               # receptacle 2mm short of the opening
    roof_slope = 1.25          # >1.0 is what makes the port seat roof self-supporting
    open_top = stack["port_axis"] + PARAMS["UsbOpeningHeight"] / 2.0
    roof_low = open_top + 0.3  # the roof must start above the opening, or the plug
                               # crosses 3mm of wall at the opening's top corners

    # The two things the stack silently gets wrong if a parameter drifts, both of
    # which look fine in the model and fail in the hand: a rail too short to keep
    # the module's bottom chip off the floor, and a port seat thicker than the
    # receptacle stands proud, which leaves the plug bottoming out on the case.
    rail_clear = (stack["module_seat"] - floor_z) - PARAMS["ModuleBottomChip"]
    if rail_clear <= 0:
        raise ValueError("module rail %.2f does not clear its %.2fmm bottom chip"
                         % (stack["module_seat"] - floor_z, PARAMS["ModuleBottomChip"]))
    if PARAMS["PortWallThickness"] > PARAMS["ConnectorOverhang"]:
        raise ValueError("port seat wall %.2f exceeds the %.2fmm the receptacle "
                         "stands proud of its board"
                         % (PARAMS["PortWallThickness"], PARAMS["ConnectorOverhang"]))

    # 7a. Split-link breakout: same inboard offset on both halves, rear-flush.
    split_x = inboard + step * PARAMS["SplitPortInboardOffset"]
    split_pocket = cradle_pocket(split_x, PARAMS["BreakoutWidth"],
                                 PARAMS["BreakoutDepth"], y_seat)
    add_port_seat(document, body, side + "_Port_Seat_Split", split_x,
                  (split_pocket[1] - split_pocket[0]) / 2.0 + seat_margin,
                  y_cav, y_seat, floor_z, roof_low, roof_slope)

    # 7b. The controller module. On the half that carries the host port it is
    # rear-flush like the breakout; on the other half nothing plugs into it, so it
    # hugs the inboard cavity wall next to the 16-pin header and gets no opening --
    # which is what lets the host port go back to the right half (ADR 260824-224604
    # retires 260824-003937).
    if host_usb:
        module_x = inboard + step * PARAMS["ModuleInboardOffset"]
        module_pocket = cradle_pocket(module_x, PARAMS["ModuleWidth"],
                                      PARAMS["ModuleDepth"], y_seat)
        add_port_seat(document, body, side + "_Port_Seat_Host", module_x,
                      (module_pocket[1] - module_pocket[0]) / 2.0 + seat_margin,
                      y_cav, y_seat, floor_z, roof_low, roof_slope)
    else:
        module_x = inboard + step * PARAMS["ModuleInboardOffsetWired"]
        module_pocket = cradle_pocket(module_x, PARAMS["ModuleWidth"],
                                      PARAMS["ModuleDepth"],
                                      y_cav - PARAMS["ModuleRearOffset"])

    add_cradle(document, body, side + "_Cradle_Split", split_pocket,
               stack["breakout_seat"], "y", 1.0)
    if host_usb:
        add_cradle(document, body, side + "_Cradle_Module", module_pocket,
                   stack["module_seat"], "y", 1.0,
                   rail_width=PARAMS["CradleRailWidth"])
    else:
        add_cradle(document, body, side + "_Cradle_Module", module_pocket,
                   stack["module_seat"], "x", -step,
                   rail_width=PARAMS["CradleRailWidth"])

    # 7c. USB-C openings through the thinned wall, on the shared port axis. Every
    # half gets the split-link port; only the host half gets the module's own,
    # centred on its cradle because the receptacle is centred on the board.
    usb_z = stack["port_axis"]
    ports = [("Split", split_x)]
    if host_usb:
        ports.append(("Host", module_x))
    for name, cx in ports:
        sk = body.newObject("Sketcher::SketchObject", side + "_Usb_" + name)
        sk.Placement = App.Placement(App.Vector(0, y_rear, 0), XZ_ROTATION)
        add_rounded_rect(sk, cx - PARAMS["UsbOpeningWidth"] / 2,
                         usb_z - PARAMS["UsbOpeningHeight"] / 2,
                         cx + PARAMS["UsbOpeningWidth"] / 2,
                         usb_z + PARAMS["UsbOpeningHeight"] / 2,
                         PARAMS["UsbOpeningRadius"])
        pk = body.newObject("PartDesign::Pocket", side + "_Usb_" + name + "_Pocket")
        pk.Profile = sk
        pk.Length = wall + 0.2
        pk.Reversed = True
        document.recompute()
    print("  %s cavity inner x %.2f..%.2f y %.2f..%.2f (inboard face x=%.2f)"
          % (side, x0 + wall, x1 - wall, y0 + wall, y_cav, inboard))
    print("  %s split cradle x %.2f..%.2f y %.2f..%.2f seat z=%.2f"
          % ((side,) + split_pocket + (stack["breakout_seat"],)))
    print("  %s module cradle x %.2f..%.2f y %.2f..%.2f seat z=%.2f%s"
          % ((side,) + module_pocket + (stack["module_seat"],
             " (rear-flush)" if host_usb else " (wired, inboard)")))
    print("  %s rear USB-C openings: %s (axis z=%.2f, port seat wall %.2f, "
          "module rail clears its bottom chip by %.2f)"
          % (side, ", ".join("%s@x=%.2f" % (n, cx) for n, cx in ports), usb_z,
             PARAMS["PortWallThickness"], rail_clear))

    if body.ViewObject:
        body.ViewObject.ShapeColor = color

    # Reference-only parts (not structural), placed in body-local coords.
    # The PCB itself, so the seat height and the connector axes can be checked
    # against real geometry instead of trusted. Not exported.
    px0, py0, px1, py1, prad = layout["pcb_rect"]
    board = Part.makeBox(px1 - px0, py1 - py0, PARAMS["PcbThickness"],
                         App.Vector(px0, py0, stack["pcb_bottom"]))
    if prad > TOLERANCE:
        vertical = [e for e in board.Edges
                    if abs(e.Vertexes[0].Point.x - e.Vertexes[-1].Point.x) < TOLERANCE
                    and abs(e.Vertexes[0].Point.y - e.Vertexes[-1].Point.y) < TOLERANCE]
        try:
            board = board.makeFillet(prad, vertical)
        except Exception as fillet_error:
            print("  %s PCB corner fillet skipped: %s" % (side, str(fillet_error)[:40]))
    ref = document.addObject("Part::Feature", side + "_PCB_Reference")
    ref.Shape = board
    if ref.ViewObject:
        ref.ViewObject.ShapeColor = (0.10, 0.45, 0.20)

    document.recompute()
    return body


# ---- Tilt wedge (separate glued part) ------------------------------------------
def build_tilt_wedge(document, side, layout, color):
    """The wedge that props the case nose-up, printed on its own and glued under the
    body (ADR 260819-204944). Same profile as when it was fused, minus the feather
    edge at the front (wedge_front_y), plus two alignment pins on its top face.

    Printed on its slanted underside it has no overhang at all; the body, freed of
    it, lies flat on its bottom face. Together that is what removes the ~2.6k mm^2
    of support the fused shape needed."""
    side_margin = PARAMS["RestSideMargin"]
    slant_w = PARAMS["RestSlantWidth"]
    slant = math.radians(PARAMS["RestSlantAngleDeg"])
    z_base = -PARAMS["BodyHeight"]
    rx0 = layout["x_min"] + side_margin
    rx1 = layout["x_max"] - side_margin
    y_front = layout["y_min"]
    y_rear = layout["y_max"] - PARAMS["RestRearMargin"]
    tilt = rest_tilt(layout)
    bottom_length = (y_rear - y_front) * math.cos(tilt) - slant_w * math.cos(slant)
    rear_bottom_y = y_front + bottom_length * math.cos(tilt)
    rear_bottom_z = z_base - bottom_length * math.sin(tilt)
    y_cut = wedge_front_y(layout)

    body = document.addObject("PartDesign::Body", side + "_Tilt_Wedge")

    profile = body.newObject("Sketcher::SketchObject", side + "_Wedge_Profile")
    profile.Placement = App.Placement(App.Vector((rx0 + rx1) / 2.0, 0, 0), YZ_ROTATION)
    add_polygon(profile, [
        (y_cut, z_base),
        (y_rear, z_base),
        (rear_bottom_y, rear_bottom_z),
        (y_cut, z_base - PARAMS["WedgeMinThickness"]),
    ])
    pad = body.newObject("PartDesign::Pad", side + "_Wedge_Pad")
    pad.Profile = profile
    pad.Length = rx1 - rx0
    pad.Midplane = True
    document.recompute()

    # R3 round-over on the rear knife-edge ridge (the lowest X-running edge).
    try:
        ridge = ["Edge%d" % (index + 1) for index, edge in enumerate(pad.Shape.Edges)
                 if edge.Vertexes
                 and all(abs(v.Point.z - rear_bottom_z) < 0.05 for v in edge.Vertexes)]
        if ridge:
            fillet = body.newObject("PartDesign::Fillet", side + "_Wedge_Fillet")
            fillet.Base = (pad, ridge)
            fillet.Radius = PARAMS["RestRearCornerFillet"]
            fillet.setExpression("Radius", u"Parameters.RestRearCornerFillet")
            document.recompute()
    except Exception as fillet_error:
        print("  wedge fillet skipped (%s): %s" % (side, str(fillet_error)[:40]))
        document.recompute()

    # Alignment pins standing on the top (mating) face, into the body's holes.
    pins = body.newObject("Sketcher::SketchObject", side + "_Wedge_Pins")
    pins.Placement = App.Placement(App.Vector(0, 0, z_base), App.Rotation())
    for x, y in wedge_pin_centres(layout):
        pins.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1),
                                     PARAMS["WedgeAlignPinDiameter"] / 2), False)
    pin_pad = body.newObject("PartDesign::Pad", side + "_Wedge_Pin_Pad")
    pin_pad.Profile = pins
    pin_pad.Length = PARAMS["WedgeAlignPinHeight"]
    pin_pad.setExpression("Length", u"Parameters.WedgeAlignPinHeight")
    document.recompute()

    if body.ViewObject:
        body.ViewObject.ShapeColor = color
    return body


# ---- main ----------------------------------------------------------------------
def main():
    for name in list(App.listDocuments().keys()):
        if name == "Keyboard_Parametric":
            App.closeDocument(name)
    document = App.newDocument("Keyboard_Parametric")

    build_spreadsheet(document)
    left_layout = compute_layout("left-switch.dxf", "left")
    right_layout = compute_layout("right-switch.dxf", "right")

    build_plate(document, "Left", left_layout, (0.86, 0.70, 0.20))
    build_plate(document, "Right", right_layout, (0.25, 0.65, 0.85))
    # The right half is the host: its module sits rear-flush behind a port seat and
    # gets the second opening. The left half's module is hand-wired and inboard, so
    # it gets no opening at all and the left half is flashed with the case open
    # (ADR 260824-224604, which also puts the firmware back to MASTER_RIGHT).
    for side, layout, color in (("Left", left_layout, (0.60, 0.35, 0.12)),
                                ("Right", right_layout, (0.12, 0.38, 0.60))):
        build_body(document, side, layout, color, host_usb=(side == "Right"))
    build_tilt_wedge(document, "Left", left_layout, (0.50, 0.30, 0.55))
    build_tilt_wedge(document, "Right", right_layout, (0.30, 0.35, 0.55))
    build_palm_rest(document, "Left", left_layout)
    build_palm_rest(document, "Right", right_layout)

    # Separate the two halves for display (right side shifted in +X), as the
    # original generator did with DISPLAY_GAP. Shift bodies and reference parts,
    # not the sketches/features nested inside the bodies.
    display_offset = (left_layout["x_max"] - left_layout["x_min"]) + PARAMS["DisplayGap"]
    for obj in document.Objects:
        if obj.Name.startswith("Right_") and obj.TypeId in ("PartDesign::Body", "Part::Feature"):
            obj.Placement.Base = App.Vector(display_offset, 0, 0)

    document.recompute()
    document.saveAs(os.path.join(BASE_DIR, "keyboard_parametric.FCStd"))

    stl_dir = os.path.join(BASE_DIR, "parametric_stl")
    if not os.path.isdir(stl_dir):
        os.makedirs(stl_dir)
    import Mesh
    for obj in document.Objects:
        if obj.TypeId == "PartDesign::Body" and hasattr(obj, "Shape") and obj.Shape.Solids:
            shape = obj.Shape
            print("%s: valid=%s solids=%d vol=%.0f" % (
                obj.Name, shape.isValid(), len(shape.Solids), shape.Volume))
            # Export at the origin: the display offset applied above is for looking
            # at the two halves side by side, not something a slicer should inherit.
            placed = shape.copy()
            placed.Placement = App.Placement()
            Mesh.Mesh(placed.tessellate(0.05)).write(
                os.path.join(stl_dir, obj.Name.lower() + ".stl"))
    print("STL exported to %s" % stl_dir)


main()
