"""Parametric (Sketcher + PartDesign) rebuild of the keyboard model.

Source of truth after generation is the FCStd (edit dimensions in the GUI via the
`Parameters` spreadsheet). This script is a one-time generator: re-running it
rebuilds the parametric document from scratch and overwrites any GUI edits.

Increment 1: master spreadsheet + palm rest (Left/Right) as PartDesign bodies.
Plate and body parts are added in following increments.
"""

import math
import os

import FreeCAD as App
import Part

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOLERANCE = 0.001

# ---- master parameters: alias -> default value (mm / deg) ----------------------
PARAMS = {
    "PlateThickness": 4.0,
    "OuterMargin": 8.0,
    "CornerRadius": 5.0,
    "BodyWallThickness": 3.0,
    "BodyHeight": 18.0,
    "RestSideMargin": 6.0,
    "RestRearMargin": 6.0,
    "RestSlantWidth": 10.0,
    "RestSlantAngleDeg": 70.0,
    "RestRearCornerFillet": 3.0,
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
    "StabCutoutYOffset": 0.4,
    "KeyholeSize": 13.96,
    "PalmRestDepth": 80.0,
    "PalmRestRearHeight": 25.0,
    "PalmRestFrontHeight": 12.0,
    "PalmRestFlatDepth": 35.0,
    "PalmRestGap": 5.0,
    "PalmRestFilletRadius": 3.0,
    "PalmRestCrestRadius": 60.0,
    "PalmRestTaperAngleDeg": 10.0,
    # Round neodymium discs (10mm diameter, 2mm thick) hold the palm rest to the
    # body, glued into their pockets. The pocket is 2.2mm deep: ~0.1mm of glue
    # plus the 2mm disc leaves it 0.1mm shy of the mating surface, so the two
    # magnets sit 0.2mm apart once the faces close. A 2mm disc loses pull fast
    # with the gap, so err shallow — a pocket that prints under depth ends up
    # flush rather than standing the magnet proud and holding the faces open.
    "MagnetDiameter": 10.0,
    "MagnetHoleDepth": 2.2,
    "MagnetHoleClearance": 0.3,
    "MagnetCentreHeight": 9.0,
    "MagnetBossThickness": 3.0,
    "Rp2040ZeroLength": 25.0,
    "Rp2040ZeroWidth": 18.0,
    "Rp2040ZeroPcbThickness": 1.6,
    "Rp2040SeatSideClearance": 1.1,
    "Rp2040SeatEndClearance": -0.4,
    "Rp2040SeatDepth": 1.0,
    "Rp2040StopThickness": 3.0,
    "Rp2040StopHeight": 2.0,
    "UsbOpeningWidth": 10.0,
    "UsbOpeningHeight": 3.7,
    "UsbOpeningRadius": 1.5,
    "UsbBezelWidth": 14.0,
    "UsbBezelHeight": 7.7,
    "UsbBezelRadius": 5.0,
    "UsbBezelDepth": 1.0,
    "UsbEdgeOffset": 37.0,
    "TrsJackEdgeOffset": 17.5,
    "TrsJackHoleDiameter": 6.5,
    "TrsJackAxisHeight": 6.5,
    "TrsJackBodyLength": 15.0,
    "TrsJackBodyWidth": 9.0,
    "TrsJackBodyHeight": 7.0,
    "TrsJackNoseDiameter": 5.0,
    "TrsJackNoseLength": 2.0,
    "TrsJackStopWidth": 12.0,
    "TrsJackStopThickness": 3.0,
    "TrsJackStopHeight": 2.0,
    "TrsJackStopClearance": 0.2,
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
    values, so offset 0 is the spec position. +0.2 was printed and still bound
    slightly, so the approved +0.4 mm sits 0.4 mm above the spec position,
    putting the slot centre 0.25 mm below the switch centre.
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


def compute_layout(dxf_filename):
    """Plate/body footprint from the DXF key cutouts (first loop is the perimeter)."""
    loops = dxf_line_loops(os.path.join(BASE_DIR, dxf_filename))
    key_loops = loops[1:]
    # Outer footprint is derived from the original cutouts so the stab-height
    # tweak below cannot move the plate/body outline.
    xs = [p[0] for loop in key_loops for p in loop]
    ys = [p[1] for loop in key_loops for p in loop]
    margin = PARAMS["OuterMargin"]
    return {
        "x_min": min(xs) - margin,
        "y_min": min(ys) - margin,
        "x_max": max(xs) + margin,
        "y_max": max(ys) + margin,
        "key_loops": resize_keyholes(shrink_stab_slots(key_loops)),
    }


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
    offset = PARAMS["ScrewCornerOffset"]

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

    # M3 countersunk mounting holes at the four corners.
    screw_xy = [
        (x0 + offset, y0 + offset), (x1 - offset, y0 + offset),
        (x0 + offset, y1 - offset), (x1 - offset, y1 - offset),
    ]
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


# ---- Keyboard body (core: shell + cavity + insert bosses/pockets) --------------
def build_body(document, side, layout, color, include_controller=False,
               usb_center_x=None, jack_center_x=None):
    x0, y0 = layout["x_min"], layout["y_min"]
    x1, y1 = layout["x_max"], layout["y_max"]
    height = PARAMS["BodyHeight"]
    wall = PARAMS["BodyWallThickness"]
    radius = PARAMS["CornerRadius"]
    offset = PARAMS["ScrewCornerOffset"]
    cavity_h = height - wall
    z_base = -height
    r_inner = max(radius - wall, 0.5)
    screw_xy = [
        (x0 + offset, y0 + offset), (x1 - offset, y0 + offset),
        (x0 + offset, y1 - offset), (x1 - offset, y1 - offset),
    ]

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
    boss_pad = body.newObject("PartDesign::Pad", side + "_Body_Boss_Pad")
    boss_pad.Profile = boss_sk
    boss_pad.Length = cavity_h
    boss_pad.setExpression("Length", u"Parameters.BodyHeight - Parameters.BodyWallThickness")
    document.recompute()

    # 4. Insert pockets bored into the bosses from the top.
    ins_sk = body.newObject("Sketcher::SketchObject", side + "_Body_Insert_Holes")
    ins_sk.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    for x, y in screw_xy:
        ins_sk.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1),
                                       PARAMS["SpredsertM3LocatingDiameter"] / 2), False)
    ins = body.newObject("PartDesign::Pocket", side + "_Body_Insert_Pockets")
    ins.Profile = ins_sk
    ins.Length = PARAMS["SpredsertM3Length"] + PARAMS["M3ScrewTipRelief"]
    ins.setExpression("Length", u"Parameters.SpredsertM3Length + Parameters.M3ScrewTipRelief")
    document.recompute()

    # 5. Tilt-rest wedge fused under the body (triangular YZ profile, additive pad).
    side_margin = PARAMS["RestSideMargin"]
    rear_margin = PARAMS["RestRearMargin"]
    slant_w = PARAMS["RestSlantWidth"]
    slant = math.radians(PARAMS["RestSlantAngleDeg"])
    rx0 = x0 + side_margin
    rx1 = x1 - side_margin
    y_front = y0
    y_rear = y1 - rear_margin
    depth = y_rear - y_front
    tilt = rest_tilt(layout)
    bottom_length = depth * math.cos(tilt) - slant_w * math.cos(slant)
    rear_bottom_y = y_front + bottom_length * math.cos(tilt)
    rear_bottom_z = z_base - bottom_length * math.sin(tilt)
    x_center = (rx0 + rx1) / 2.0

    rest_sk = body.newObject("Sketcher::SketchObject", side + "_Body_Rest")
    rest_sk.Placement = App.Placement(App.Vector(x_center, 0, 0), YZ_ROTATION)
    add_polygon(rest_sk, [
        (y_front, z_base),
        (y_rear, z_base),
        (rear_bottom_y, rear_bottom_z),
    ])
    rest_pad = body.newObject("PartDesign::Pad", side + "_Body_Rest_Pad")
    rest_pad.Profile = rest_sk
    rest_pad.Length = rx1 - rx0
    rest_pad.Midplane = True
    document.recompute()

    # R3 round-over on the rear knife-edge ridge (the lowest X-running edge).
    try:
        ridge = ["Edge%d" % (index + 1) for index, edge in enumerate(rest_pad.Shape.Edges)
                 if edge.Vertexes
                 and all(abs(v.Point.z - rear_bottom_z) < 0.05 for v in edge.Vertexes)]
        if ridge:
            rest_fillet = body.newObject("PartDesign::Fillet", side + "_Body_Rest_Fillet")
            rest_fillet.Base = (rest_pad, ridge)
            rest_fillet.Radius = PARAMS["RestRearCornerFillet"]
            rest_fillet.setExpression("Radius", u"Parameters.RestRearCornerFillet")
            document.recompute()
    except Exception as rest_error:
        print("  rest fillet skipped (%s): %s" % (side, str(rest_error)[:40]))
        document.recompute()

    # 6. Magnet seats in the front wall, facing the palm rest. A 2.2mm pocket stops
    # short of breaching the BodyWallThickness wall, but only by 0.8mm — too thin to
    # survive the palm rest being pulled off — so pad a local backing block onto the
    # inside of the wall, leaving 3.8mm behind each magnet. It sits well forward of
    # the front switch row, so it never fouls the switch pins.
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

    # 7. Connectors. y_max (y1) is the rear wall; the cavity floor is at floor_z.
    floor_z = -cavity_h
    y_rear = y1

    if jack_center_x is not None:
        jack_z = z_base + PARAMS["TrsJackAxisHeight"]
        jh = body.newObject("Sketcher::SketchObject", side + "_Jack_Hole")
        jh.Placement = App.Placement(App.Vector(0, y_rear, 0), XZ_ROTATION)
        jh.addGeometry(Part.Circle(App.Vector(jack_center_x, jack_z, 0),
                                   App.Vector(0, 0, 1), PARAMS["TrsJackHoleDiameter"] / 2), False)
        jhp = body.newObject("PartDesign::Pocket", side + "_Jack_Hole_Pocket")
        jhp.Profile = jh
        jhp.Length = wall + 0.2
        jhp.Reversed = True
        document.recompute()

        jack_inner_y = y_rear - wall - (PARAMS["TrsJackBodyLength"] - PARAMS["TrsJackNoseLength"])
        sw, st = PARAMS["TrsJackStopWidth"], PARAMS["TrsJackStopThickness"]
        sy = jack_inner_y - PARAMS["TrsJackStopClearance"] - st
        js = body.newObject("Sketcher::SketchObject", side + "_Jack_Stop")
        js.Placement = App.Placement(App.Vector(0, 0, floor_z), App.Rotation())
        add_polygon(js, [(jack_center_x - sw / 2, sy), (jack_center_x + sw / 2, sy),
                         (jack_center_x + sw / 2, sy + st), (jack_center_x - sw / 2, sy + st)])
        jsp = body.newObject("PartDesign::Pad", side + "_Jack_Stop_Pad")
        jsp.Profile = js
        jsp.Length = PARAMS["TrsJackStopHeight"]
        document.recompute()

    if include_controller:
        seat_w = PARAMS["Rp2040ZeroWidth"] + 2 * PARAMS["Rp2040SeatSideClearance"]
        # EndClearance is negative: seat is shorter than the board so the USB end
        # protrudes through the wall opening and the board is held snugly.
        seat_l = PARAMS["Rp2040ZeroLength"] + 2 * PARAMS["Rp2040SeatEndClearance"]
        seat_x = usb_center_x - seat_w / 2
        seat_y = y_rear - wall - seat_l  # USB faces the front edge (usb_at_rear=False)

        cs = body.newObject("Sketcher::SketchObject", side + "_Ctrl_Seat")
        cs.Placement = App.Placement(App.Vector(0, 0, floor_z), App.Rotation())
        add_polygon(cs, [(seat_x, seat_y), (seat_x + seat_w, seat_y),
                         (seat_x + seat_w, seat_y + seat_l), (seat_x, seat_y + seat_l)])
        csp = body.newObject("PartDesign::Pocket", side + "_Ctrl_Seat_Pocket")
        csp.Profile = cs
        csp.Length = PARAMS["Rp2040SeatDepth"]
        document.recompute()

        # Opening center sits 0.8 below the TRS jack axis so both line up on the wall.
        uz0 = (z_base + PARAMS["TrsJackAxisHeight"] - 0.8
               - PARAMS["UsbOpeningHeight"] / 2)
        uo = body.newObject("Sketcher::SketchObject", side + "_Usb_Opening")
        uo.Placement = App.Placement(App.Vector(0, y_rear, 0), XZ_ROTATION)
        add_rounded_rect(uo, usb_center_x - PARAMS["UsbOpeningWidth"] / 2, uz0,
                         usb_center_x + PARAMS["UsbOpeningWidth"] / 2,
                         uz0 + PARAMS["UsbOpeningHeight"], PARAMS["UsbOpeningRadius"])
        uop = body.newObject("PartDesign::Pocket", side + "_Usb_Opening_Pocket")
        uop.Profile = uo
        uop.Length = wall + 0.2
        uop.Reversed = True
        document.recompute()

        # Bezel is concentric with the opening so the ring margin is uniform.
        bz0 = uz0 - (PARAMS["UsbBezelHeight"] - PARAMS["UsbOpeningHeight"]) / 2
        ub = body.newObject("Sketcher::SketchObject", side + "_Usb_Bezel")
        ub.Placement = App.Placement(App.Vector(0, y_rear, 0), XZ_ROTATION)
        add_rounded_rect(ub, usb_center_x - PARAMS["UsbBezelWidth"] / 2, bz0,
                         usb_center_x + PARAMS["UsbBezelWidth"] / 2,
                         bz0 + PARAMS["UsbBezelHeight"], PARAMS["UsbBezelRadius"])
        ubp = body.newObject("PartDesign::Pocket", side + "_Usb_Bezel_Pocket")
        ubp.Profile = ub
        ubp.Length = PARAMS["UsbBezelDepth"] + 0.1
        ubp.Reversed = True
        document.recompute()

        stop_w = PARAMS["Rp2040ZeroWidth"]
        stop_y = seat_y - PARAMS["Rp2040StopThickness"]
        cst = body.newObject("Sketcher::SketchObject", side + "_Ctrl_Stop")
        cst.Placement = App.Placement(App.Vector(0, 0, floor_z), App.Rotation())
        add_polygon(cst, [(usb_center_x - stop_w / 2, stop_y), (usb_center_x + stop_w / 2, stop_y),
                          (usb_center_x + stop_w / 2, stop_y + PARAMS["Rp2040StopThickness"]),
                          (usb_center_x - stop_w / 2, stop_y + PARAMS["Rp2040StopThickness"])])
        cstp = body.newObject("PartDesign::Pad", side + "_Ctrl_Stop_Pad")
        cstp.Profile = cst
        cstp.Length = PARAMS["Rp2040StopHeight"]
        document.recompute()

    if body.ViewObject:
        body.ViewObject.ShapeColor = color

    # Reference-only parts (not structural), placed in body-local coords.
    if include_controller:
        seat_z = floor_z - PARAMS["Rp2040SeatDepth"]
        board_y = seat_y + seat_l - PARAMS["Rp2040ZeroLength"]
        board = Part.makeBox(PARAMS["Rp2040ZeroWidth"], PARAMS["Rp2040ZeroLength"],
                             PARAMS["Rp2040ZeroPcbThickness"],
                             App.Vector(usb_center_x - PARAMS["Rp2040ZeroWidth"] / 2, board_y, seat_z))
        ref = document.addObject("Part::Feature", side + "_RP2040_Zero_Reference")
        ref.Shape = board
        if ref.ViewObject:
            ref.ViewObject.ShapeColor = (0.15, 0.60, 0.30)
    if jack_center_x is not None:
        jack_z = z_base + PARAMS["TrsJackAxisHeight"]
        jack_inner_y = y_rear - wall - (PARAMS["TrsJackBodyLength"] - PARAMS["TrsJackNoseLength"])
        jbody = Part.makeBox(PARAMS["TrsJackBodyWidth"],
                             PARAMS["TrsJackBodyLength"] - PARAMS["TrsJackNoseLength"],
                             PARAMS["TrsJackBodyHeight"],
                             App.Vector(jack_center_x - PARAMS["TrsJackBodyWidth"] / 2, jack_inner_y,
                                        jack_z - PARAMS["TrsJackBodyHeight"] / 2))
        jnose = Part.makeCylinder(PARAMS["TrsJackNoseDiameter"] / 2, PARAMS["TrsJackNoseLength"],
                                  App.Vector(jack_center_x, y_rear - wall, jack_z), App.Vector(0, 1, 0))
        ref2 = document.addObject("Part::Feature", side + "_PJ322_Jack_Reference")
        ref2.Shape = jbody.fuse(jnose)
        if ref2.ViewObject:
            ref2.ViewObject.ShapeColor = (0.75, 0.65, 0.15)
    document.recompute()
    return body


# ---- main ----------------------------------------------------------------------
def main():
    for name in list(App.listDocuments().keys()):
        if name == "Keyboard_Parametric":
            App.closeDocument(name)
    document = App.newDocument("Keyboard_Parametric")

    build_spreadsheet(document)
    left_layout = compute_layout("left-switch.dxf")
    right_layout = compute_layout("right-switch.dxf")

    build_plate(document, "Left", left_layout, (0.86, 0.70, 0.20))
    build_plate(document, "Right", right_layout, (0.25, 0.65, 0.85))
    build_body(document, "Left", left_layout, (0.60, 0.35, 0.12),
               jack_center_x=left_layout["x_max"] - PARAMS["TrsJackEdgeOffset"])
    build_body(document, "Right", right_layout, (0.12, 0.38, 0.60),
               include_controller=True,
               usb_center_x=right_layout["x_min"] + PARAMS["UsbEdgeOffset"],
               jack_center_x=right_layout["x_min"] + PARAMS["TrsJackEdgeOffset"])
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

    for obj in document.Objects:
        if obj.TypeId == "PartDesign::Body" and hasattr(obj, "Shape") and obj.Shape.Solids:
            shape = obj.Shape
            print("%s: valid=%s solids=%d vol=%.0f" % (
                obj.Name, shape.isValid(), len(shape.Solids), shape.Volume))


main()
