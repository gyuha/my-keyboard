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
M3_CLEARANCE_DIAMETER = 3.2
M3_COUNTERSINK_DIAMETER = 6.0
M3_COUNTERSINK_DEPTH = 1.5
SPREDSERT_M3_LOCATING_DIAMETER = 4.0
SPREDSERT_M3_LENGTH = 5.0
M3_SCREW_TIP_RELIEF = 2.0
INSERT_BOSS_DIAMETER = 8.0
SCREW_CORNER_OFFSET = 4.3
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


def countersunk_m3_hole(x, y):
    clearance = Part.makeCylinder(M3_CLEARANCE_DIAMETER / 2, PLATE_THICKNESS,
                                  App.Vector(x, y, 0))
    countersink = Part.makeCone(M3_CLEARANCE_DIAMETER / 2,
                                M3_COUNTERSINK_DIAMETER / 2,
                                M3_COUNTERSINK_DEPTH,
                                App.Vector(x, y, PLATE_THICKNESS - M3_COUNTERSINK_DEPTH))
    return clearance.fuse(countersink)


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
    final_shape = outline.cut(Part.makeCompound(key_voids + screw_voids)).removeSplitter()

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


def build_body(document, side, layout, color):
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
    final_body = case_shell.multiFuse(bosses).cut(Part.makeCompound(insert_pockets)).removeSplitter()

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
                    ("SPREDSERTLength", SPREDSERT_M3_LENGTH), ("M3ScrewTipRelief", M3_SCREW_TIP_RELIEF)):
    parameters.addProperty("App::PropertyLength", name, "Dimensions")
    setattr(parameters, name, value)

left_object, left_shape, left_layout = build_plate(document, "Left", "left-switch.dxf", (0.86, 0.70, 0.20))
right_object, right_shape, right_layout = build_plate(document, "Right", "right-switch.dxf", (0.25, 0.65, 0.85))
left_body_object, left_body_shape = build_body(document, "Left", left_layout, (0.60, 0.35, 0.12))
right_body_object, right_body_shape = build_body(document, "Right", right_layout, (0.12, 0.38, 0.60))

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
document.recompute()
document.saveAs(os.path.join(BASE_DIR, "keyboard_switch_plates.FCStd"))
print("Created keyboard_switch_plates.FCStd")
print("Left plate: %.2f x %.2f x %.2f mm" % (left_shape.BoundBox.XLength, left_shape.BoundBox.YLength, left_shape.BoundBox.ZLength))
print("Right plate: %.2f x %.2f x %.2f mm" % (right_shape.BoundBox.XLength, right_shape.BoundBox.YLength, right_shape.BoundBox.ZLength))
