import math
import os

import FreeCAD as App
import Part
import Mesh


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLATE_THICKNESS = 4.0
OUTER_MARGIN = 8.0
CORNER_RADIUS = 5.0
BODY_WALL_THICKNESS = 3.0
BODY_HEIGHT = 18.0
REST_SIDE_MARGIN = 6.0
REST_REAR_MARGIN = 6.0
REST_SLANT_WIDTH = 10.0
REST_SLANT_ANGLE_DEG = 70.0
M3_CLEARANCE_DIAMETER = 3.2
M3_COUNTERSINK_DIAMETER = 6.0
M3_COUNTERSINK_DEPTH = 1.5
SPREDSERT_M3_LOCATING_DIAMETER = 4.0
SPREDSERT_M3_LENGTH = 5.0
M3_SCREW_TIP_RELIEF = 2.0
INSERT_BOSS_DIAMETER = 8.0
RP2040_ZERO_LENGTH = 25.0
RP2040_ZERO_WIDTH = 18.0
RP2040_ZERO_PCB_THICKNESS = 1.6
RP2040_SEAT_CLEARANCE = 0.6
RP2040_SEAT_DEPTH = 1.0
RP2040_STOP_THICKNESS = 3.0
RP2040_STOP_HEIGHT = 2.0
USB_C_OPENING_WIDTH = 10.0
USB_C_OPENING_HEIGHT = 6.0
USB_C_OPENING_RADIUS = 1.5
USB_C_BEZEL_WIDTH = 14.0
USB_C_BEZEL_HEIGHT = 10.0
USB_C_BEZEL_RADIUS = 5.0
USB_C_BEZEL_DEPTH = 1.0
USB_C_EDGE_OFFSET = 37.0
TRS_JACK_EDGE_OFFSET = 17.5
TRS_JACK_HOLE_DIAMETER = 6.5
TRS_JACK_AXIS_HEIGHT = 6.5
TRS_JACK_BODY_LENGTH = 15.0
TRS_JACK_BODY_WIDTH = 9.0
TRS_JACK_BODY_HEIGHT = 7.0
TRS_JACK_NOSE_DIAMETER = 5.0
TRS_JACK_NOSE_LENGTH = 2.0
TRS_JACK_STOP_WIDTH = 12.0
TRS_JACK_STOP_THICKNESS = 3.0
TRS_JACK_STOP_HEIGHT = 2.0
TRS_JACK_STOP_CLEARANCE = 0.2
STAB_CLIP_PLATE_THICKNESS = 1.4
STAB_CLIP_LEDGE_WIDTH = 1.2
STAB_CUTOUT_MAX_WIDTH = 5.0
PALM_REST_DEPTH = 80.0
PALM_REST_REAR_HEIGHT = 25.0
PALM_REST_FRONT_HEIGHT = 12.0
PALM_REST_FLAT_DEPTH = 35.0
PALM_REST_GAP = 5.0
PALM_REST_FILLET_RADIUS = 3.0
DISPLAY_GAP = 25.0
MAIN_PCB_THICKNESS = 1.6
MX_PLATE_TO_PCB = 5.0
PCB_SEAT_CLEARANCE = 0.3
PCB_LEDGE_WIDTH = 1.5
BOARD_OUTLINE_LAYER = "Board-Outline-Layer"
MOUNTING_HOLE_MIN_DIAMETER = 3.0
MOUNTING_HOLE_CORNER_RADIUS = 15.0
MOUNTING_INSET = 3.0
PCB_SCREW_CLEARANCE_DIAMETER = 4.0
TOLERANCE = 0.001


def dxf_pairs(path):
    with open(path, "r", encoding="ascii", errors="ignore") as source:
        lines = [line.strip() for line in source]
    return [(int(lines[index]), lines[index + 1]) for index in range(0, len(lines) - 1, 2)]


def dxf_line_loops(path):
    """Read the R12 LINE-only DXF and join consecutive lines into closed loops."""
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


def wire_from_loop(points):
    vectors = [App.Vector(x, y, 0) for x, y in points]
    if vectors[0].distanceToPoint(vectors[-1]) > TOLERANCE:
        vectors.append(vectors[0])
    edges = [Part.makeLine(vectors[index], vectors[index + 1])
             for index in range(len(vectors) - 1)]
    return Part.Wire(edges)


def pcb_outline_wire(path, layer=BOARD_OUTLINE_LAYER):
    """Build a closed wire from the single board-outline LWPOLYLINE in a DXF.

    Honors per-vertex bulge (code 42; bulge = tan(theta/4), sagitta = bulge*chord/2)
    so 90-degree corner arcs become real Part.Arc edges rather than chords."""
    entity = None
    entity_layer = None
    collecting = []
    stream = None
    for code, value in dxf_pairs(path):
        if code == 0:
            if entity == "LWPOLYLINE" and entity_layer == layer:
                stream = collecting
                break
            entity = value
            entity_layer = None
            collecting = []
        else:
            if entity == "LWPOLYLINE":
                collecting.append((code, value))
            if code == 8:
                entity_layer = value
    if stream is None:
        raise RuntimeError("no board outline on layer %s in %s" % (layer, path))

    vertices = []  # (x, y, bulge)
    x = y = None
    bulge = 0.0
    for code, value in stream:
        if code == 10:
            if x is not None:
                vertices.append((x, y, bulge))
            x = float(value)
            y = None
            bulge = 0.0
        elif code == 20:
            y = float(value)
        elif code == 42:
            bulge = float(value)
    if x is not None:
        vertices.append((x, y, bulge))

    edges = []
    count = len(vertices)
    for index in range(count):
        x1, y1, b = vertices[index]
        x2, y2, _ = vertices[(index + 1) % count]
        start = App.Vector(x1, y1, 0)
        end = App.Vector(x2, y2, 0)
        # EasyEDA emits arcs as a pair of coincident vertices with the bulge on the
        # second; skip the zero-length segment between them (a degenerate edge would
        # break Part.Face).
        if start.distanceToPoint(end) < TOLERANCE:
            continue
        if abs(b) < TOLERANCE:
            edges.append(Part.makeLine(start, end))
        else:
            dx, dy = x2 - x1, y2 - y1
            mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            # EasyEDA's bulge sign with this outline's (clockwise) winding rounds
            # the corners inward (concave); negate the perpendicular offset so the
            # corner arcs bulge outward (convex), i.e. real rounded corners.
            apex = App.Vector(mx + (b / 2.0) * dy, my - (b / 2.0) * dx, 0)
            edges.append(Part.Arc(start, apex, end).toShape())
    return Part.Wire(Part.__sortEdges__(edges))


def offset_wire_inward(wire, distance):
    """Offset a closed wire inward by `distance`, regardless of its winding.

    makeOffset2D shrinks or grows depending on the wire orientation, so try both
    signs and keep the result whose bounding box is smaller (the inward one).
    Returns None if neither sign produces a smaller closed wire."""
    reference = wire.BoundBox
    for signed in (-distance, distance):
        try:
            candidate = wire.makeOffset2D(signed)
        except Exception:
            continue
        box = candidate.BoundBox
        if box.XLength < reference.XLength - TOLERANCE and box.YLength < reference.YLength - TOLERANCE:
            return candidate
    return None


def offset_wire_outward(wire, distance):
    """Offset a closed wire outward by `distance`, regardless of its winding.

    Mirror of offset_wire_inward: keep the result whose bounding box is larger."""
    reference = wire.BoundBox
    for signed in (distance, -distance):
        try:
            candidate = wire.makeOffset2D(signed)
        except Exception:
            continue
        box = candidate.BoundBox
        if box.XLength > reference.XLength + TOLERANCE and box.YLength > reference.YLength + TOLERANCE:
            return candidate
    return None


def pcb_mounting_holes(path, bounds):
    """Detect the corner mounting holes on a PCB DXF.

    Reads circular pads/holes on the through-hole layers -- including the
    2-vertex "circle" polylines EasyEDA emits (a circle drawn as two semicircle
    arcs), which an earlier >= 3 vertex test silently discarded -- dedupes by
    position, and keeps the ones large enough to be a screw hole
    (>= MOUNTING_HOLE_MIN_DIAMETER). Of those, returns the one nearest each of
    the four board-outline corners within MOUNTING_HOLE_CORNER_RADIUS, so
    component through-holes elsewhere on the board are not mistaken for case
    screws. Returns [(x, y), ...] (up to four)."""
    layers = ("Hole-Layer", "Multi-Layer")
    entity = layer = None
    xs = []
    ys = []
    found = []

    def flush():
        if entity == "LWPOLYLINE" and layer in layers and len(xs) >= 2:
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            radius = sum(math.hypot(x - cx, y - cy) for x, y in zip(xs, ys)) / len(xs)
            found.append((cx, cy, radius))

    for code, value in dxf_pairs(path):
        if code == 0:
            flush()
            entity = value
            layer = None
            xs = []
            ys = []
        elif code == 8:
            layer = value
        elif code == 10:
            try:
                xs.append(float(value))
            except ValueError:
                pass
        elif code == 20:
            try:
                ys.append(float(value))
            except ValueError:
                pass
    flush()

    dedup = {}
    for cx, cy, radius in found:
        key = (round(cx, 1), round(cy, 1))
        if key not in dedup or radius > dedup[key]:
            dedup[key] = radius
    points = [(x, y) for (x, y), r in dedup.items() if 2 * r >= MOUNTING_HOLE_MIN_DIAMETER]

    corners = [(bounds.XMin, bounds.YMin), (bounds.XMax, bounds.YMin),
               (bounds.XMin, bounds.YMax), (bounds.XMax, bounds.YMax)]
    mounts = []
    seen = set()
    for corner_x, corner_y in corners:
        candidates = [(math.hypot(x - corner_x, y - corner_y), x, y) for x, y in points
                      if math.hypot(x - corner_x, y - corner_y) <= MOUNTING_HOLE_CORNER_RADIUS]
        if not candidates:
            continue
        _, x, y = min(candidates)
        key = (round(x, 1), round(y, 1))
        if key not in seen:
            seen.add(key)
            mounts.append((x, y))
    return mounts


def corner_mounting_holes(bounds):
    """Four screw positions at MOUNTING_INSET from each corner of a bounding box."""
    return [
        (bounds.XMin + MOUNTING_INSET, bounds.YMin + MOUNTING_INSET),
        (bounds.XMax - MOUNTING_INSET, bounds.YMin + MOUNTING_INSET),
        (bounds.XMin + MOUNTING_INSET, bounds.YMax - MOUNTING_INSET),
        (bounds.XMax - MOUNTING_INSET, bounds.YMax - MOUNTING_INSET),
    ]


def rounded_prism(x_min, y_min, x_max, y_max, radius, prism_height, z_base):
    width = x_max - x_min
    height = y_max - y_min
    horizontal = Part.makeBox(width - 2 * radius, height, prism_height,
                              App.Vector(x_min + radius, y_min, z_base))
    vertical = Part.makeBox(width, height - 2 * radius, prism_height,
                            App.Vector(x_min, y_min + radius, z_base))
    corners = [
        Part.makeCylinder(radius, prism_height, App.Vector(x_min + radius, y_min + radius, z_base)),
        Part.makeCylinder(radius, prism_height, App.Vector(x_max - radius, y_min + radius, z_base)),
        Part.makeCylinder(radius, prism_height, App.Vector(x_min + radius, y_max - radius, z_base)),
        Part.makeCylinder(radius, prism_height, App.Vector(x_max - radius, y_max - radius, z_base)),
    ]
    return horizontal.multiFuse([vertical] + corners).removeSplitter()


def rounded_plate(x_min, y_min, x_max, y_max):
    return rounded_prism(x_min, y_min, x_max, y_max, CORNER_RADIUS, PLATE_THICKNESS, 0)


def rounded_slot_xz(x_min, y_min, z_min, width, height, radius, depth):
    """Create a rounded rectangle in the XZ plane, extruded along positive Y."""
    parts = []
    if width - 2 * radius > TOLERANCE:
        parts.append(Part.makeBox(width - 2 * radius, depth, height,
                                  App.Vector(x_min + radius, y_min, z_min)))
    if height - 2 * radius > TOLERANCE:
        parts.append(Part.makeBox(width, depth, height - 2 * radius,
                                  App.Vector(x_min, y_min, z_min + radius)))
    centers = {
        (x_min + radius, z_min + radius),
        (x_min + width - radius, z_min + radius),
        (x_min + radius, z_min + height - radius),
        (x_min + width - radius, z_min + height - radius),
    }
    parts.extend(Part.makeCylinder(radius, depth, App.Vector(x, y_min, z), App.Vector(0, 1, 0))
                 for x, z in centers)
    return parts[0].multiFuse(parts[1:]).removeSplitter()


def countersunk_m3_hole(x, y):
    clearance = Part.makeCylinder(M3_CLEARANCE_DIAMETER / 2, PLATE_THICKNESS,
                                  App.Vector(x, y, 0))
    countersink = Part.makeCone(M3_CLEARANCE_DIAMETER / 2,
                                M3_COUNTERSINK_DIAMETER / 2,
                                M3_COUNTERSINK_DEPTH,
                                App.Vector(x, y, PLATE_THICKNESS - M3_COUNTERSINK_DEPTH))
    return clearance.fuse(countersink)


def build_tilt_rest(layout):
    """Wedge rest under the body: flush with the front face, inset by the margins elsewhere.

    Resting on the desk, the rear face tucks inward (under the body) at
    REST_SLANT_ANGLE_DEG from the desk and is REST_SLANT_WIDTH wide, its top corner
    sitting REST_REAR_MARGIN in front of the body rear face. The bottom tapers to
    zero at the front edge."""
    x_min = layout["x_min"] + REST_SIDE_MARGIN
    x_max = layout["x_max"] - REST_SIDE_MARGIN
    y_front = layout["y_min"]
    y_rear = layout["y_max"] - REST_REAR_MARGIN
    slant = math.radians(REST_SLANT_ANGLE_DEG)
    depth = y_rear - y_front
    # Typing tilt that lets the rear-face top corner meet the body bottom plane.
    tilt = math.asin(REST_SLANT_WIDTH * math.sin(slant) / depth)
    bottom_length = depth * math.cos(tilt) - REST_SLANT_WIDTH * math.cos(slant)
    rear_bottom_y = y_front + bottom_length * math.cos(tilt)
    rear_bottom_z = -BODY_HEIGHT - bottom_length * math.sin(tilt)
    thickness = bottom_length * math.sin(tilt) + 1.0
    slab = rounded_prism(x_min, y_front, x_max, y_rear, CORNER_RADIUS,
                         thickness, -BODY_HEIGHT - thickness)
    profile = [
        App.Vector(x_min - 1.0, y_front, -BODY_HEIGHT),
        App.Vector(x_min - 1.0, y_rear, -BODY_HEIGHT),
        App.Vector(x_min - 1.0, rear_bottom_y, rear_bottom_z),
    ]
    section = Part.Face(Part.makePolygon(profile + [profile[0]]))
    wedge = slab.common(section.extrude(App.Vector(x_max - x_min + 2.0, 0, 0)))
    return wedge, math.degrees(tilt)


def build_palm_rest(document, side, layout, color):
    """Free-standing wedge palm rest in front of the body (user side, past y_min).

    Flat bottom resting on the desk plane (z = -BODY_HEIGHT). A short flat shelf on
    the keyboard side slopes down toward the user; all top edges are rounded."""
    x_min = layout["x_min"]
    x_max = layout["x_max"]
    y_rear = layout["y_min"] - PALM_REST_GAP
    y_front = y_rear - PALM_REST_DEPTH
    z_base = -BODY_HEIGHT
    slab = rounded_prism(x_min, y_front, x_max, y_rear, CORNER_RADIUS,
                         PALM_REST_REAR_HEIGHT, z_base)
    profile = [
        App.Vector(x_min - 1.0, y_rear + 1.0, z_base),
        App.Vector(x_min - 1.0, y_rear + 1.0, z_base + PALM_REST_REAR_HEIGHT),
        App.Vector(x_min - 1.0, y_rear - PALM_REST_FLAT_DEPTH, z_base + PALM_REST_REAR_HEIGHT),
        App.Vector(x_min - 1.0, y_front - 1.0, z_base + PALM_REST_FRONT_HEIGHT),
        App.Vector(x_min - 1.0, y_front - 1.0, z_base),
    ]
    section = Part.Face(Part.makePolygon(profile + [profile[0]]))
    wedge = slab.common(section.extrude(App.Vector(x_max - x_min + 2.0, 0, 0)))
    top_edges = [edge for edge in wedge.Edges
                 if min(vertex.Point.z for vertex in edge.Vertexes) >
                 z_base + PALM_REST_FRONT_HEIGHT / 2]
    wedge = wedge.makeFillet(PALM_REST_FILLET_RADIUS, top_edges).removeSplitter()
    rest_object = add_feature(document, side + "_Palm_Rest", side + " palm rest wedge",
                              wedge, color, True)
    rest_object.addProperty("App::PropertyLength", "Depth", "Palm Rest").Depth = PALM_REST_DEPTH
    rest_object.addProperty("App::PropertyLength", "RearHeight", "Palm Rest").RearHeight = PALM_REST_REAR_HEIGHT
    rest_object.addProperty("App::PropertyLength", "FrontHeight", "Palm Rest").FrontHeight = PALM_REST_FRONT_HEIGHT
    rest_object.addProperty("App::PropertyLength", "FlatDepth", "Palm Rest").FlatDepth = PALM_REST_FLAT_DEPTH
    rest_object.addProperty("App::PropertyLength", "BodyGap", "Palm Rest").BodyGap = PALM_REST_GAP
    rest_object.addProperty("App::PropertyString", "PrintNote", "Palm Rest").PrintNote = (
        "Free-standing piece: place in front of the body with roughly a %.0f mm gap. "
        "Print flat side down; no supports needed." % PALM_REST_GAP)
    return rest_object, wedge


def add_feature(document, name, label, shape, color, visible=True):
    feature = document.addObject("Part::Feature", name)
    feature.Label = label
    feature.Shape = shape
    if feature.ViewObject:
        feature.ViewObject.ShapeColor = color
        feature.ViewObject.Visibility = visible
    return feature


def build_plate(document, side, dxf_filename, pcb_filename, color):
    loops = dxf_line_loops(os.path.join(BASE_DIR, dxf_filename))
    # The first loop is the supplied perimeter. All following loops are key cutouts.
    all_key_wires = [wire_from_loop(loop) for loop in loops[1:]]
    # The plate outline is the PCB board outline; both DXFs share the same local
    # origin, so keep only the cutouts that fall inside the PCB (drops the top
    # function row that has no board underneath it).
    pcb_wire = pcb_outline_wire(os.path.join(BASE_DIR, pcb_filename))
    pcb_face = Part.Face(pcb_wire)
    key_wires = [wire for wire in all_key_wires
                 if pcb_face.isInside(wire.BoundBox.Center, TOLERANCE, True)]
    cutout_edges = Part.makeCompound(key_wires)
    # The case (plate + body) is a wall around the PCB: its outline is the PCB
    # outline grown outward by the wall thickness plus the seat clearance, so the
    # PCB sits inside the case rather than flush with its edge.
    outer_wire = offset_wire_outward(pcb_wire, BODY_WALL_THICKNESS + PCB_SEAT_CLEARANCE)
    outer_face = Part.Face(outer_wire)
    bounds = outer_wire.BoundBox
    x_min = bounds.XMin
    y_min = bounds.YMin
    x_max = bounds.XMax
    y_max = bounds.YMax

    outline = outer_face.extrude(App.Vector(0, 0, PLATE_THICKNESS))
    key_voids = [Part.Face(wire).extrude(App.Vector(0, 0, PLATE_THICKNESS)) for wire in key_wires]
    # Screw positions follow the PCB's own mounting holes so the plate, body and
    # board holes line up. If the board does not carry a clean set of four (e.g. an
    # incomplete export), fall back to four corners of the board at MOUNTING_INSET.
    mounting_holes = pcb_mounting_holes(os.path.join(BASE_DIR, pcb_filename), pcb_wire.BoundBox)
    if len(mounting_holes) == 4:
        screw_locations = mounting_holes
        screw_source = "PCB mounting holes"
    else:
        screw_locations = corner_mounting_holes(pcb_wire.BoundBox)
        screw_source = "board-corner fallback (%d holes detected)" % len(mounting_holes)
    screw_voids = [countersunk_m3_hole(x, y) for x, y in screw_locations]
    # Plate-mount stabilizer clips need a 1.4 mm plate; relieve the underside on the
    # top/bottom edges of each narrow stabilizer cutout so the clip can latch.
    stab_pocket_depth = PLATE_THICKNESS - STAB_CLIP_PLATE_THICKNESS
    stab_pockets = []
    for wire in key_wires:
        wire_bounds = wire.BoundBox
        if min(wire_bounds.XLength, wire_bounds.YLength) > STAB_CUTOUT_MAX_WIDTH:
            continue
        stab_pockets.append(Part.makeBox(wire_bounds.XLength, STAB_CLIP_LEDGE_WIDTH,
                                         stab_pocket_depth,
                                         App.Vector(wire_bounds.XMin, wire_bounds.YMax, 0)))
        stab_pockets.append(Part.makeBox(wire_bounds.XLength, STAB_CLIP_LEDGE_WIDTH,
                                         stab_pocket_depth,
                                         App.Vector(wire_bounds.XMin,
                                                    wire_bounds.YMin - STAB_CLIP_LEDGE_WIDTH, 0)))
    final_shape = outline.cut(
        Part.makeCompound(key_voids + screw_voids + stab_pockets)).removeSplitter()

    outline_object = add_feature(document, side + "_Plate_Outline", side + " plate outline (PCB)", outline,
                                 (0.75, 0.75, 0.75), False)
    outline_object.addProperty("App::PropertyLength", "Thickness", "Plate Parameters").Thickness = PLATE_THICKNESS
    outline_object.addProperty("App::PropertyString", "SourcePCB", "Plate Parameters").SourcePCB = pcb_filename
    cutout_object = add_feature(document, side + "_Switch_Cutouts", side + " switch cutout references",
                                cutout_edges, (0.90, 0.20, 0.20), False)
    cutout_object.addProperty("App::PropertyString", "SourceDXF", "Source").SourceDXF = dxf_filename
    holes_object = add_feature(document, side + "_M3_Screw_Holes", side + " M3 countersunk screw holes",
                               Part.makeCompound(screw_voids), (0.20, 0.45, 0.90), False)
    holes_object.addProperty("App::PropertyLength", "ClearanceDiameter", "M3 Countersink").ClearanceDiameter = M3_CLEARANCE_DIAMETER
    holes_object.addProperty("App::PropertyLength", "CountersinkDiameter", "M3 Countersink").CountersinkDiameter = M3_COUNTERSINK_DIAMETER
    holes_object.addProperty("App::PropertyLength", "CountersinkDepth", "M3 Countersink").CountersinkDepth = M3_COUNTERSINK_DEPTH
    holes_object.addProperty("App::PropertyString", "ScrewSource", "M3 Countersink").ScrewSource = screw_source
    if stab_pockets:
        stab_object = add_feature(document, side + "_Stab_Clip_Pockets",
                                  side + " stabilizer clip pockets",
                                  Part.makeCompound(stab_pockets), (0.90, 0.55, 0.20), False)
        stab_object.addProperty("App::PropertyLength", "LedgeThickness", "Stabilizer Clip").LedgeThickness = STAB_CLIP_PLATE_THICKNESS
        stab_object.addProperty("App::PropertyLength", "LedgeWidth", "Stabilizer Clip").LedgeWidth = STAB_CLIP_LEDGE_WIDTH
        stab_object.addProperty("App::PropertyLength", "PocketDepth", "Stabilizer Clip").PocketDepth = stab_pocket_depth
        stab_object.addProperty("App::PropertyString", "DesignNotes", "Stabilizer Clip").DesignNotes = (
            "Underside relief on the top/bottom edges of each stabilizer cutout: %.1f mm wide, "
            "leaving a %.1f mm ledge at the plate top so plate-mount stabilizer clips can latch."
            % (STAB_CLIP_LEDGE_WIDTH, STAB_CLIP_PLATE_THICKNESS))
    plate_object = add_feature(document, side + "_Switch_Plate", side + " finished 4 mm switch plate",
                               final_shape, color, True)
    plate_object.addProperty("App::PropertyString", "DesignNotes", "Documentation").DesignNotes = (
        "Outline is the PCB board outline (%s) grown outward by %.1f mm (wall + seat clearance) so " % (
            pcb_filename, BODY_WALL_THICKNESS + PCB_SEAT_CLEARANCE) +
        "the case surrounds the PCB; only cutouts inside the board are kept (top function row dropped). "
        "Four M3x10 countersunk mounting holes (3.2 mm clearance, 6.0 mm top countersink).")
    return plate_object, final_shape, {
        "x_min": x_min,
        "y_min": y_min,
        "x_max": x_max,
        "y_max": y_max,
        "screw_locations": screw_locations,
        "pcb_wire": pcb_wire,
        "pcb_face": pcb_face,
        "outer_wire": outer_wire,
    }


def build_body(document, side, layout, color, include_controller=False, usb_center_x=None,
               usb_at_rear=True, jack_center_x=None):
    x_min = layout["x_min"]
    y_min = layout["y_min"]
    x_max = layout["x_max"]
    y_max = layout["y_max"]
    pcb_wire = layout["pcb_wire"]
    cavity_height = BODY_HEIGHT - BODY_WALL_THICKNESS
    outer_wire = layout["outer_wire"]
    z_pcb_top = PLATE_THICKNESS - MX_PLATE_TO_PCB
    z_pcb_bottom = z_pcb_top - MAIN_PCB_THICKNESS
    # Outer wall follows the widened case outline (PCB grown outward), so the plate
    # edge and body edge match and both surround the PCB.
    outer_body = Part.Face(outer_wire).extrude(App.Vector(0, 0, -BODY_HEIGHT))
    # Two-step cavity: the PCB drops into the upper pocket (PCB + seat clearance) and
    # rests on a perimeter ledge at its underside; the lower cavity (PCB - ledge) is
    # the electronics space down to the floor. Insert bosses rise only to the PCB
    # underside and double as standoffs; the M3 screw passes through the PCB's own
    # mounting hole into the insert (screw positions come from the PCB mounting holes).
    drop_wire = offset_wire_outward(pcb_wire, PCB_SEAT_CLEARANCE)
    lower_wire = offset_wire_inward(pcb_wire, PCB_LEDGE_WIDTH)
    if drop_wire is not None and lower_wire is not None:
        drop_face = Part.Face(drop_wire)
        drop_face.translate(App.Vector(0, 0, 0.01))
        upper_cavity = drop_face.extrude(App.Vector(0, 0, z_pcb_bottom - 0.01))
        lower_face = Part.Face(lower_wire)
        lower_face.translate(App.Vector(0, 0, z_pcb_bottom))
        lower_cavity = lower_face.extrude(App.Vector(0, 0, -cavity_height - z_pcb_bottom))
        case_shell = outer_body.cut(upper_cavity).cut(lower_cavity)
    else:
        # Fallback: single cavity inset from the outer wall by the wall thickness.
        cavity_wire = offset_wire_inward(outer_wire, BODY_WALL_THICKNESS)
        cavity_face = Part.Face(cavity_wire)
        cavity_face.translate(App.Vector(0, 0, 0.01))
        inner_cavity = cavity_face.extrude(App.Vector(0, 0, -(cavity_height + 0.01)))
        case_shell = outer_body.cut(inner_cavity)
    # Bosses rise from the cavity floor to the PCB underside (they support the board).
    boss_height = z_pcb_bottom + cavity_height
    bosses = [Part.makeCylinder(INSERT_BOSS_DIAMETER / 2, boss_height,
                                App.Vector(x, y, -cavity_height)).common(outer_body)
              for x, y in layout["screw_locations"]]
    insert_length = SPREDSERT_M3_LENGTH + M3_SCREW_TIP_RELIEF
    insert_pockets = [Part.makeCylinder(SPREDSERT_M3_LOCATING_DIAMETER / 2, insert_length,
                                        App.Vector(x, y, z_pcb_bottom - insert_length))
                      for x, y in layout["screw_locations"]]
    body_cuts = list(insert_pockets)
    body_fuses = []

    if include_controller:
        if usb_center_x is None:
            usb_center_x = (x_min + x_max) / 2
        seat_width = RP2040_ZERO_WIDTH + 2 * RP2040_SEAT_CLEARANCE
        seat_length = RP2040_ZERO_LENGTH + 2 * RP2040_SEAT_CLEARANCE
        seat_x = usb_center_x - seat_width / 2
        if usb_at_rear:
            seat_y = y_min + BODY_WALL_THICKNESS
            usb_y = y_min - 0.1
            board_y = seat_y
            orientation = "USB-C faces the rear edge"
        else:
            seat_y = y_max - BODY_WALL_THICKNESS - seat_length
            usb_y = y_max - BODY_WALL_THICKNESS - 0.1
            board_y = seat_y + seat_length - RP2040_ZERO_LENGTH
            orientation = "USB-C faces the front edge"
        seat_z = -cavity_height - RP2040_SEAT_DEPTH
        controller_seat = Part.makeBox(seat_width, seat_length, RP2040_SEAT_DEPTH,
                                       App.Vector(seat_x, seat_y, seat_z))
        # USB-C sits at the back edge of the controller and is reached through the rear wall.
        usb_opening = rounded_slot_xz(usb_center_x - USB_C_OPENING_WIDTH / 2, usb_y,
                                      -BODY_HEIGHT + 2.0, USB_C_OPENING_WIDTH,
                                      USB_C_OPENING_HEIGHT, USB_C_OPENING_RADIUS,
                                      BODY_WALL_THICKNESS + 0.2)
        bezel_y = usb_y if usb_at_rear else y_max - USB_C_BEZEL_DEPTH
        usb_bezel = rounded_slot_xz(usb_center_x - USB_C_BEZEL_WIDTH / 2, bezel_y,
                                    -BODY_HEIGHT,
                                    USB_C_BEZEL_WIDTH, USB_C_BEZEL_HEIGHT,
                                    USB_C_BEZEL_RADIUS, USB_C_BEZEL_DEPTH + 0.1)
        body_cuts.extend((controller_seat, usb_opening, usb_bezel))
        board_reference = Part.makeBox(RP2040_ZERO_WIDTH, RP2040_ZERO_LENGTH,
                                       RP2040_ZERO_PCB_THICKNESS,
                                       App.Vector(usb_center_x - RP2040_ZERO_WIDTH / 2,
                                                  board_y,
                                                  seat_z))
        controller_object = add_feature(document, side + "_RP2040_Zero_Reference",
                                        side + " RP2040-Zero board reference",
                                        board_reference, (0.15, 0.60, 0.30), True)
        controller_object.addProperty("App::PropertyLength", "BoardLength", "RP2040-Zero").BoardLength = RP2040_ZERO_LENGTH
        controller_object.addProperty("App::PropertyLength", "BoardWidth", "RP2040-Zero").BoardWidth = RP2040_ZERO_WIDTH
        controller_object.addProperty("App::PropertyLength", "SeatDepth", "RP2040-Zero").SeatDepth = RP2040_SEAT_DEPTH
        controller_object.addProperty("App::PropertyString", "Orientation", "RP2040-Zero").Orientation = orientation
        # Floor backstop behind the board's non-USB end, mirroring the PJ-322 jack
        # stop: a rib fused to the cavity floor that backs the controller's rear edge
        # (same 2 mm height as the audio jack backstop).
        stop_width = RP2040_ZERO_WIDTH
        stop_y = (seat_y + seat_length if usb_at_rear
                  else seat_y - RP2040_STOP_THICKNESS)
        controller_stop = Part.makeBox(stop_width, RP2040_STOP_THICKNESS, RP2040_STOP_HEIGHT,
                                       App.Vector(usb_center_x - stop_width / 2, stop_y,
                                                  -cavity_height))
        body_fuses.append(controller_stop)
        controller_object.addProperty("App::PropertyLength", "StopThickness", "RP2040-Zero").StopThickness = RP2040_STOP_THICKNESS
        controller_object.addProperty("App::PropertyLength", "StopHeight", "RP2040-Zero").StopHeight = RP2040_STOP_HEIGHT

    if jack_center_x is not None:
        # PJ-322 plug axis: jack body resting on the cavity floor, entry through the rear wall.
        jack_z = -BODY_HEIGHT + TRS_JACK_AXIS_HEIGHT
        jack_hole = Part.makeCylinder(TRS_JACK_HOLE_DIAMETER / 2, BODY_WALL_THICKNESS + 0.2,
                                      App.Vector(jack_center_x, y_max - BODY_WALL_THICKNESS - 0.1, jack_z),
                                      App.Vector(0, 1, 0))
        body_cuts.append(jack_hole)
        jack_inner_y = y_max - BODY_WALL_THICKNESS - (TRS_JACK_BODY_LENGTH - TRS_JACK_NOSE_LENGTH)
        jack_body = Part.makeBox(TRS_JACK_BODY_WIDTH,
                                 TRS_JACK_BODY_LENGTH - TRS_JACK_NOSE_LENGTH,
                                 TRS_JACK_BODY_HEIGHT,
                                 App.Vector(jack_center_x - TRS_JACK_BODY_WIDTH / 2,
                                            jack_inner_y,
                                            jack_z - TRS_JACK_BODY_HEIGHT / 2))
        # Floor backstop behind the jack body: takes the plug-insertion push toward the cavity.
        jack_stop = Part.makeBox(TRS_JACK_STOP_WIDTH, TRS_JACK_STOP_THICKNESS, TRS_JACK_STOP_HEIGHT,
                                 App.Vector(jack_center_x - TRS_JACK_STOP_WIDTH / 2,
                                            jack_inner_y - TRS_JACK_STOP_CLEARANCE - TRS_JACK_STOP_THICKNESS,
                                            -cavity_height))
        body_fuses.append(jack_stop)
        jack_nose = Part.makeCylinder(TRS_JACK_NOSE_DIAMETER / 2, TRS_JACK_NOSE_LENGTH,
                                      App.Vector(jack_center_x, y_max - BODY_WALL_THICKNESS, jack_z),
                                      App.Vector(0, 1, 0))
        jack_object = add_feature(document, side + "_PJ322_Jack_Reference",
                                  side + " PJ-322 3.5 mm TRS jack reference",
                                  jack_body.fuse(jack_nose), (0.75, 0.65, 0.15), True)
        jack_object.addProperty("App::PropertyString", "Part", "PJ-322").Part = (
            "PJ-322 3.5 mm stereo jack, 5-pin DIP (Devicemart 1067728)")
        jack_object.addProperty("App::PropertyLength", "HoleDiameter", "PJ-322").HoleDiameter = TRS_JACK_HOLE_DIAMETER
        jack_object.addProperty("App::PropertyLength", "EdgeOffset", "PJ-322").EdgeOffset = TRS_JACK_EDGE_OFFSET
        jack_object.addProperty("App::PropertyLength", "AxisHeight", "PJ-322").AxisHeight = TRS_JACK_AXIS_HEIGHT
        jack_object.addProperty("App::PropertyLength", "StopThickness", "PJ-322").StopThickness = TRS_JACK_STOP_THICKNESS
        jack_object.addProperty("App::PropertyLength", "StopHeight", "PJ-322").StopHeight = TRS_JACK_STOP_HEIGHT
        jack_object.addProperty("App::PropertyLength", "StopClearance", "PJ-322").StopClearance = TRS_JACK_STOP_CLEARANCE
        jack_object.addProperty("App::PropertyString", "MountingNote", "PJ-322").MountingNote = (
            "Rest the jack on the cavity floor with the DIP pins facing up, nose tucked into the "
            "rear-wall hole; the floor backstop behind the body takes the plug-insertion push. "
            "Solder the link wires, then tack the body with adhesive.")

    rest_wedge, rest_tilt = build_tilt_rest(layout)
    final_body = case_shell.multiFuse(bosses + body_fuses + [rest_wedge]).cut(
        Part.makeCompound(body_cuts)).removeSplitter()

    pocket_object = add_feature(document, side + "_M3_Insert_Pockets",
                                side + " SPREDSERT M3x5 insert pockets",
                                Part.makeCompound(insert_pockets), (0.35, 0.80, 0.35), False)
    pocket_object.addProperty("App::PropertyLength", "LocatingHoleDiameter", "SPREDSERT M3x5").LocatingHoleDiameter = SPREDSERT_M3_LOCATING_DIAMETER
    pocket_object.addProperty("App::PropertyLength", "InsertDepth", "SPREDSERT M3x5").InsertDepth = SPREDSERT_M3_LENGTH
    pocket_object.addProperty("App::PropertyLength", "TipRelief", "SPREDSERT M3x5").TipRelief = M3_SCREW_TIP_RELIEF
    pocket_object.addProperty("App::PropertyLength", "PocketDepth", "SPREDSERT M3x5").PocketDepth = SPREDSERT_M3_LENGTH + M3_SCREW_TIP_RELIEF
    pocket_object.addProperty("App::PropertyString", "Insert", "SPREDSERT M3x5").Insert = "AMTEC SPREDSERT M3x5 brass insert"
    body_object = add_feature(document, side + "_Keyboard_Body", side + " 18 mm keyboard body",
                              final_body, color, True)
    body_object.addProperty("App::PropertyLength", "WallThickness", "Body Parameters").WallThickness = BODY_WALL_THICKNESS
    body_object.addProperty("App::PropertyLength", "BodyHeight", "Body Parameters").BodyHeight = BODY_HEIGHT
    body_object.addProperty("App::PropertyLength", "BottomThickness", "Body Parameters").BottomThickness = BODY_WALL_THICKNESS
    body_object.addProperty("App::PropertyLength", "InsertBossDiameter", "Body Parameters").InsertBossDiameter = INSERT_BOSS_DIAMETER
    body_object.addProperty("App::PropertyLength", "RestSlantWidth", "Tilt Rest").RestSlantWidth = REST_SLANT_WIDTH
    body_object.addProperty("App::PropertyAngle", "RestSlantAngle", "Tilt Rest").RestSlantAngle = REST_SLANT_ANGLE_DEG
    body_object.addProperty("App::PropertyLength", "RestSideMargin", "Tilt Rest").RestSideMargin = REST_SIDE_MARGIN
    body_object.addProperty("App::PropertyLength", "RestRearMargin", "Tilt Rest").RestRearMargin = REST_REAR_MARGIN
    body_object.addProperty("App::PropertyAngle", "RestTiltAngle", "Tilt Rest").RestTiltAngle = rest_tilt
    body_object.addProperty("App::PropertyLength", "PCBSeatTopZ", "PCB Seat").PCBSeatTopZ = z_pcb_top
    body_object.addProperty("App::PropertyLength", "PCBSeatBottomZ", "PCB Seat").PCBSeatBottomZ = z_pcb_bottom
    body_object.addProperty("App::PropertyLength", "PCBSeatClearance", "PCB Seat").PCBSeatClearance = PCB_SEAT_CLEARANCE
    body_object.addProperty("App::PropertyLength", "PCBLedgeWidth", "PCB Seat").PCBLedgeWidth = PCB_LEDGE_WIDTH
    body_object.addProperty("App::PropertyString", "AssemblyNotes", "Documentation").AssemblyNotes = (
        "Open-top body whose wall surrounds the PCB (outline grown outward by %.1f mm). The insert bosses "
        "sit at the PCB's own mounting-hole positions and rise to the board underside as standoffs. Install "
        "four SPREDSERT M3x5 inserts into the bosses from the top, drop the PCB in (it rests on the %.1f mm "
        "perimeter ledge and the boss tops at z=%.1f mm), then fasten the 4 mm plate: the M3 screws pass "
        "through the plate and the PCB mounting holes into the inserts." % (
            BODY_WALL_THICKNESS + PCB_SEAT_CLEARANCE, PCB_LEDGE_WIDTH, z_pcb_bottom))
    return body_object, final_body


def build_pcb_reference(document, side, layout, color):
    """1.6 mm PCB reference solid at the MX switch stack height, under the plate.

    Cuts the M3 screw mounting holes at the screw positions so the reference shows
    where the board bolts to the case (matching the PCB's own mounting holes)."""
    z_pcb_top = PLATE_THICKNESS - MX_PLATE_TO_PCB
    board = layout["pcb_face"].extrude(App.Vector(0, 0, -MAIN_PCB_THICKNESS))
    board.translate(App.Vector(0, 0, z_pcb_top))
    screw_holes = [Part.makeCylinder(PCB_SCREW_CLEARANCE_DIAMETER / 2, MAIN_PCB_THICKNESS + 1.0,
                                     App.Vector(x, y, z_pcb_top - MAIN_PCB_THICKNESS - 0.5))
                   for x, y in layout["screw_locations"]]
    board = board.cut(Part.makeCompound(screw_holes)).removeSplitter()
    pcb_object = add_feature(document, side + "_PCB_Reference", side + " PCB board reference",
                             board, color, True)
    pcb_object.addProperty("App::PropertyLength", "Thickness", "PCB").Thickness = MAIN_PCB_THICKNESS
    pcb_object.addProperty("App::PropertyLength", "PlateTopToPCB", "PCB").PlateTopToPCB = MX_PLATE_TO_PCB
    pcb_object.addProperty("App::PropertyLength", "TopZ", "PCB").TopZ = z_pcb_top
    pcb_object.addProperty("App::PropertyLength", "ScrewHoleDiameter", "PCB").ScrewHoleDiameter = PCB_SCREW_CLEARANCE_DIAMETER
    pcb_object.addProperty("App::PropertyString", "MountingNote", "PCB").MountingNote = (
        "Reference at the MX stack height (PCB top %.1f mm below the plate top). Screw holes (dia %.1f mm) "
        "sit at the plate/body screw positions; on the real board these must match the case screw axes." % (
            MX_PLATE_TO_PCB, PCB_SCREW_CLEARANCE_DIAMETER))
    return pcb_object, board


document = App.newDocument("Keyboard_Switch_Plates")
document.addObject("App::FeaturePython", "Design_Parameters").Label = "Design parameters (mm)"
parameters = document.getObject("Design_Parameters")
for name, value in (("PlateThickness", PLATE_THICKNESS), ("Margin", OUTER_MARGIN),
                    ("CornerRadius", CORNER_RADIUS), ("BodyWallThickness", BODY_WALL_THICKNESS),
                    ("BodyHeight", BODY_HEIGHT), ("M3ClearanceDiameter", M3_CLEARANCE_DIAMETER),
                    ("M3CountersinkDiameter", M3_COUNTERSINK_DIAMETER),
                    ("M3CountersinkDepth", M3_COUNTERSINK_DEPTH),
                    ("SPREDSERTLocatingDiameter", SPREDSERT_M3_LOCATING_DIAMETER),
                    ("SPREDSERTLength", SPREDSERT_M3_LENGTH), ("M3ScrewTipRelief", M3_SCREW_TIP_RELIEF),
                    ("RP2040SeatDepth", RP2040_SEAT_DEPTH), ("USBOpeningWidth", USB_C_OPENING_WIDTH),
                    ("USBOpeningHeight", USB_C_OPENING_HEIGHT), ("USBBezelWidth", USB_C_BEZEL_WIDTH),
                    ("USBBezelHeight", USB_C_BEZEL_HEIGHT), ("USBBezelDepth", USB_C_BEZEL_DEPTH),
                    ("USBEdgeOffset", USB_C_EDGE_OFFSET), ("RestSideMargin", REST_SIDE_MARGIN),
                    ("RestRearMargin", REST_REAR_MARGIN), ("RestSlantWidth", REST_SLANT_WIDTH),
                    ("TRSJackEdgeOffset", TRS_JACK_EDGE_OFFSET),
                    ("TRSJackHoleDiameter", TRS_JACK_HOLE_DIAMETER),
                    ("TRSJackAxisHeight", TRS_JACK_AXIS_HEIGHT),
                    ("PalmRestDepth", PALM_REST_DEPTH),
                    ("PalmRestRearHeight", PALM_REST_REAR_HEIGHT),
                    ("PalmRestFrontHeight", PALM_REST_FRONT_HEIGHT),
                    ("StabClipPlateThickness", STAB_CLIP_PLATE_THICKNESS),
                    ("StabClipLedgeWidth", STAB_CLIP_LEDGE_WIDTH)):
    parameters.addProperty("App::PropertyLength", name, "Dimensions")
    setattr(parameters, name, value)

left_object, left_shape, left_layout = build_plate(document, "Left", "left-switch.dxf", "left-pcb.dxf", (0.86, 0.70, 0.20))
right_object, right_shape, right_layout = build_plate(document, "Right", "right-switch.dxf", "right-pcb.dxf", (0.25, 0.65, 0.85))
# Left half is the TRRS slave (MASTER_RIGHT firmware): no controller seat or
# USB opening; the RP2040-Zero is placed freely and flashing needs the case
# open anyway (BOOTSEL button access).
left_body_object, left_body_shape = build_body(
    document, "Left", left_layout, (0.60, 0.35, 0.12),
    jack_center_x=left_layout["x_max"] - TRS_JACK_EDGE_OFFSET)
right_body_object, right_body_shape = build_body(
    document, "Right", right_layout, (0.12, 0.38, 0.60), True,
    right_layout["x_min"] + USB_C_EDGE_OFFSET, False,
    right_layout["x_min"] + TRS_JACK_EDGE_OFFSET)
left_palm_object, left_palm_shape = build_palm_rest(document, "Left", left_layout, (0.13, 0.13, 0.13))
right_palm_object, right_palm_shape = build_palm_rest(document, "Right", right_layout, (0.13, 0.13, 0.13))
left_pcb_object, left_pcb_shape = build_pcb_reference(document, "Left", left_layout, (0.10, 0.45, 0.20))
right_pcb_object, right_pcb_shape = build_pcb_reference(document, "Right", right_layout, (0.10, 0.45, 0.20))

# Both DXFs use a local origin. Move every right-side document object so the
# two halves are visibly separate in FreeCAD while retaining their local STL geometry.
right_display_offset = left_shape.BoundBox.XMax + DISPLAY_GAP - right_shape.BoundBox.XMin
for object in document.Objects:
    if object.Name.startswith("Right_"):
        object.Placement.Base = App.Vector(right_display_offset, 0, 0)

document.recompute()

document.saveAs(os.path.join(BASE_DIR, "keyboard_switch_plates.FCStd"))
Mesh.export([left_object], os.path.join(BASE_DIR, "left_switch_plate.stl"))
# Export an unshifted copy of the right plate for a predictable slicer origin.
right_object.Placement.Base = App.Vector(0, 0, 0)
Mesh.export([right_object], os.path.join(BASE_DIR, "right_switch_plate.stl"))
right_object.Placement.Base = App.Vector(right_display_offset, 0, 0)
Mesh.export([left_body_object], os.path.join(BASE_DIR, "left_keyboard_body.stl"))
right_body_object.Placement.Base = App.Vector(0, 0, 0)
Mesh.export([right_body_object], os.path.join(BASE_DIR, "right_keyboard_body.stl"))
right_body_object.Placement.Base = App.Vector(right_display_offset, 0, 0)
Mesh.export([left_palm_object], os.path.join(BASE_DIR, "left_palm_rest.stl"))
right_palm_object.Placement.Base = App.Vector(0, 0, 0)
Mesh.export([right_palm_object], os.path.join(BASE_DIR, "right_palm_rest.stl"))
right_palm_object.Placement.Base = App.Vector(right_display_offset, 0, 0)
document.recompute()
document.saveAs(os.path.join(BASE_DIR, "keyboard_switch_plates.FCStd"))
print("Created keyboard_switch_plates.FCStd")
print("Left plate: %.2f x %.2f x %.2f mm" % (left_shape.BoundBox.XLength, left_shape.BoundBox.YLength, left_shape.BoundBox.ZLength))
print("Right plate: %.2f x %.2f x %.2f mm" % (right_shape.BoundBox.XLength, right_shape.BoundBox.YLength, right_shape.BoundBox.ZLength))
print("Left body: %.2f x %.2f x %.2f mm" % (left_body_shape.BoundBox.XLength, left_body_shape.BoundBox.YLength, left_body_shape.BoundBox.ZLength))
print("Right body: %.2f x %.2f x %.2f mm" % (right_body_shape.BoundBox.XLength, right_body_shape.BoundBox.YLength, right_body_shape.BoundBox.ZLength))
print("Rest tilt: left %.2f deg, right %.2f deg" % (
    float(left_body_object.RestTiltAngle), float(right_body_object.RestTiltAngle)))
print("PJ-322 jack hole: dia %.2f mm, center z %.2f, left x=%.2f, right x=%.2f (local coords)" % (
    TRS_JACK_HOLE_DIAMETER, -BODY_HEIGHT + TRS_JACK_AXIS_HEIGHT,
    left_layout["x_max"] - TRS_JACK_EDGE_OFFSET,
    right_layout["x_min"] + TRS_JACK_EDGE_OFFSET))
print("Left palm rest: %.2f x %.2f x %.2f mm" % (
    left_palm_shape.BoundBox.XLength, left_palm_shape.BoundBox.YLength, left_palm_shape.BoundBox.ZLength))
print("Right palm rest: %.2f x %.2f x %.2f mm" % (
    right_palm_shape.BoundBox.XLength, right_palm_shape.BoundBox.YLength, right_palm_shape.BoundBox.ZLength))
print("Left PCB ref: %.2f x %.2f x %.2f mm, top z=%.2f" % (
    left_pcb_shape.BoundBox.XLength, left_pcb_shape.BoundBox.YLength,
    left_pcb_shape.BoundBox.ZLength, left_pcb_shape.BoundBox.ZMax))
print("Right PCB ref: %.2f x %.2f x %.2f mm, top z=%.2f" % (
    right_pcb_shape.BoundBox.XLength, right_pcb_shape.BoundBox.YLength,
    right_pcb_shape.BoundBox.ZLength, right_pcb_shape.BoundBox.ZMax))
print("Kept switch cutouts (solids in plate) — inspect Left_Switch_Cutouts / Right_Switch_Cutouts counts in tree")
