import os

import FreeCAD as App
import Part
import Mesh


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLATE_THICKNESS = 4.0
OUTER_MARGIN = 7.0
CORNER_RADIUS = 5.0
M3_CLEARANCE_DIAMETER = 3.2
M3_COUNTERSINK_DIAMETER = 6.0
M3_COUNTERSINK_DEPTH = 1.5
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


def rounded_plate(x_min, y_min, x_max, y_max):
    width = x_max - x_min
    height = y_max - y_min
    radius = CORNER_RADIUS
    horizontal = Part.makeBox(width - 2 * radius, height, PLATE_THICKNESS,
                              App.Vector(x_min + radius, y_min, 0))
    vertical = Part.makeBox(width, height - 2 * radius, PLATE_THICKNESS,
                            App.Vector(x_min, y_min + radius, 0))
    corners = [
        Part.makeCylinder(radius, PLATE_THICKNESS, App.Vector(x_min + radius, y_min + radius, 0)),
        Part.makeCylinder(radius, PLATE_THICKNESS, App.Vector(x_max - radius, y_min + radius, 0)),
        Part.makeCylinder(radius, PLATE_THICKNESS, App.Vector(x_min + radius, y_max - radius, 0)),
        Part.makeCylinder(radius, PLATE_THICKNESS, App.Vector(x_max - radius, y_max - radius, 0)),
    ]
    return horizontal.multiFuse([vertical] + corners).removeSplitter()


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
        "Central switch array only; original DXF perimeter excluded. 7 mm margin, R5 corners, "
        "four M3x10 countersunk mounting holes (3.2 mm clearance, 6.0 mm top countersink).")
    return plate_object, final_shape


document = App.newDocument("Keyboard_Switch_Plates")
document.addObject("App::FeaturePython", "Design_Parameters").Label = "Design parameters (mm)"
parameters = document.getObject("Design_Parameters")
for name, value in (("PlateThickness", PLATE_THICKNESS), ("Margin", OUTER_MARGIN),
                    ("CornerRadius", CORNER_RADIUS), ("M3ClearanceDiameter", M3_CLEARANCE_DIAMETER),
                    ("M3CountersinkDiameter", M3_COUNTERSINK_DIAMETER),
                    ("M3CountersinkDepth", M3_COUNTERSINK_DEPTH)):
    parameters.addProperty("App::PropertyLength", name, "Dimensions")
    setattr(parameters, name, value)

left_object, left_shape = build_plate(document, "Left", "left-switch.dxf", (0.86, 0.70, 0.20))
right_object, right_shape = build_plate(document, "Right", "right-switch.dxf", (0.25, 0.65, 0.85))

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
document.recompute()
document.saveAs(os.path.join(BASE_DIR, "keyboard_switch_plates.FCStd"))
print("Created keyboard_switch_plates.FCStd")
print("Left plate: %.2f x %.2f x %.2f mm" % (left_shape.BoundBox.XLength, left_shape.BoundBox.YLength, left_shape.BoundBox.ZLength))
print("Right plate: %.2f x %.2f x %.2f mm" % (right_shape.BoundBox.XLength, right_shape.BoundBox.YLength, right_shape.BoundBox.ZLength))
