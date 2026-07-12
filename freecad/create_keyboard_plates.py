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
SCREW_CORNER_OFFSET = 4.3
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


def build_plate(document, side, dxf_filename, color):
    loops = dxf_line_loops(os.path.join(BASE_DIR, dxf_filename))
    # The first loop is the supplied perimeter. All following loops are key cutouts.
    key_wires = [wire_from_loop(loop) for loop in loops[1:]]
    cutout_edges = Part.makeCompound(key_wires)
    bounds = cutout_edges.BoundBox
    x_min = bounds.XMin - OUTER_MARGIN
    y_min = bounds.YMin - OUTER_MARGIN
    x_max = bounds.XMax + OUTER_MARGIN
    y_max = bounds.YMax + OUTER_MARGIN

    outline = rounded_plate(x_min, y_min, x_max, y_max)
    key_voids = [Part.Face(wire).extrude(App.Vector(0, 0, PLATE_THICKNESS)) for wire in key_wires]
    screw_locations = [
        (x_min + SCREW_CORNER_OFFSET, y_min + SCREW_CORNER_OFFSET),
        (x_max - SCREW_CORNER_OFFSET, y_min + SCREW_CORNER_OFFSET),
        (x_min + SCREW_CORNER_OFFSET, y_max - SCREW_CORNER_OFFSET),
        (x_max - SCREW_CORNER_OFFSET, y_max - SCREW_CORNER_OFFSET),
    ]
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

    outline_object = add_feature(document, side + "_Plate_Outline", side + " plate outline (R5)", outline,
                                 (0.75, 0.75, 0.75), False)
    outline_object.addProperty("App::PropertyLength", "Thickness", "Plate Parameters").Thickness = PLATE_THICKNESS
    outline_object.addProperty("App::PropertyLength", "Margin", "Plate Parameters").Margin = OUTER_MARGIN
    outline_object.addProperty("App::PropertyLength", "CornerRadius", "Plate Parameters").CornerRadius = CORNER_RADIUS
    cutout_object = add_feature(document, side + "_Switch_Cutouts", side + " switch cutout references",
                                cutout_edges, (0.90, 0.20, 0.20), False)
    cutout_object.addProperty("App::PropertyString", "SourceDXF", "Source").SourceDXF = dxf_filename
    holes_object = add_feature(document, side + "_M3_Screw_Holes", side + " M3 countersunk screw holes",
                               Part.makeCompound(screw_voids), (0.20, 0.45, 0.90), False)
    holes_object.addProperty("App::PropertyLength", "ClearanceDiameter", "M3 Countersink").ClearanceDiameter = M3_CLEARANCE_DIAMETER
    holes_object.addProperty("App::PropertyLength", "CountersinkDiameter", "M3 Countersink").CountersinkDiameter = M3_COUNTERSINK_DIAMETER
    holes_object.addProperty("App::PropertyLength", "CountersinkDepth", "M3 Countersink").CountersinkDepth = M3_COUNTERSINK_DEPTH
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
        "Central switch array only; original DXF perimeter excluded. %.1f mm margin, R5 corners, " % OUTER_MARGIN +
        "four M3x10 countersunk mounting holes (3.2 mm clearance, 6.0 mm top countersink).")
    return plate_object, final_shape, {
        "x_min": x_min,
        "y_min": y_min,
        "x_max": x_max,
        "y_max": y_max,
        "screw_locations": screw_locations,
    }


def build_body(document, side, layout, color, include_controller=False, usb_center_x=None,
               usb_at_rear=True, jack_center_x=None):
    x_min = layout["x_min"]
    y_min = layout["y_min"]
    x_max = layout["x_max"]
    y_max = layout["y_max"]
    cavity_height = BODY_HEIGHT - BODY_WALL_THICKNESS
    outer_body = rounded_prism(x_min, y_min, x_max, y_max, CORNER_RADIUS, BODY_HEIGHT, -BODY_HEIGHT)
    inner_cavity = rounded_prism(x_min + BODY_WALL_THICKNESS, y_min + BODY_WALL_THICKNESS,
                                 x_max - BODY_WALL_THICKNESS, y_max - BODY_WALL_THICKNESS,
                                 CORNER_RADIUS - BODY_WALL_THICKNESS, cavity_height + 0.01,
                                 -cavity_height)
    case_shell = outer_body.cut(inner_cavity)
    boss_height = cavity_height
    bosses = [Part.makeCylinder(INSERT_BOSS_DIAMETER / 2, boss_height,
                                App.Vector(x, y, -cavity_height)).common(outer_body)
              for x, y in layout["screw_locations"]]
    insert_pockets = [Part.makeCylinder(SPREDSERT_M3_LOCATING_DIAMETER / 2,
                                        SPREDSERT_M3_LENGTH + M3_SCREW_TIP_RELIEF,
                                        App.Vector(x, y, -(SPREDSERT_M3_LENGTH + M3_SCREW_TIP_RELIEF)))
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
    body_object.addProperty("App::PropertyString", "AssemblyNotes", "Documentation").AssemblyNotes = (
        "Open-top body: install four SPREDSERT M3x5 inserts from the top, then fasten the 4 mm plate "
        "with the matching M3x10 countersunk screws. A 2 mm relief below each insert prevents screw bottoming.")
    return body_object, final_body


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

left_object, left_shape, left_layout = build_plate(document, "Left", "left-switch.dxf", (0.86, 0.70, 0.20))
right_object, right_shape, right_layout = build_plate(document, "Right", "right-switch.dxf", (0.25, 0.65, 0.85))
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
