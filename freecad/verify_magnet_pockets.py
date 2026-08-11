"""Headless check that the magnet pockets are sized for glue-mounted 10x2mm discs.

Run with the console binary (never the GUI — saving from freecadcmd drops the
GuiDocument and the part colours go with it):

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
        freecad/verify_magnet_pockets.py

Exits 0 when every check passes, 1 otherwise. The point of checks 3 and 4 is that
they measure the finished solid rather than trusting the feature properties: a
Pocket whose Length reads 2.2 can still cut a different depth if its sketch plane
does not sit on the mating face.
"""

import os
import sys

import FreeCAD as App
import Part

DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keyboard_parametric.FCStd")

# Glue (~0.1mm) + magnet (2.0mm) + 0.1mm recess, so the disc never stands proud.
EXPECTED_DEPTH = 2.2
# Front wall 3.0 + backing pad 3.0 - pocket 2.2.
EXPECTED_BACKING = 3.8
# (MagnetDiameter 10.0 + MagnetHoleClearance 0.3) / 2, unchanged by this task.
HOLE_RADIUS = 5.15

POCKETS = [
    "Left_Palm_Magnet_Pockets",
    "Right_Palm_Magnet_Pockets",
    "Left_Body_Magnet_Pockets",
    "Right_Body_Magnet_Pockets",
]

TOL = 1e-3

failures = []


def say(text):
    # freecadcmd exits without flushing a block-buffered stdout, so every line is
    # flushed as it is written or the whole report is lost on sys.exit().
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def check(label, ok, detail):
    say("  %s %-58s %s" % ("PASS" if ok else "FAIL", label, detail))
    if not ok:
        failures.append(label)


def magnet_cylinders(shape):
    """Cylindrical faces of the magnet pockets, as (axis, low point, high point)."""
    found = []
    for face in shape.Faces:
        surface = face.Surface
        if surface.TypeId != "Part::GeomCylinder":
            continue
        if abs(surface.Radius - HOLE_RADIUS) > TOL:
            continue
        axis = App.Vector(surface.Axis).normalize()
        base = surface.Center
        offsets = [(vertex.Point - base).dot(axis) for vertex in face.Vertexes]
        found.append((axis, base + axis * min(offsets), base + axis * max(offsets)))
    return found


def material_run(shape, start, direction):
    """Thickness of solid material from `start` along `direction`, by bisection."""
    step, limit = 0.1, 40.0
    outside = None
    probe = step
    while probe <= limit:
        if not shape.isInside(start + direction * probe, 1e-7, True):
            outside = probe
            break
        probe += step
    if outside is None:
        return None
    lo, hi = outside - step, outside
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if shape.isInside(start + direction * mid, 1e-7, True):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


doc = App.openDocument(DOC)

say("\n=== 1. Parameters spreadsheet ===")
sheet = doc.getObject("Parameters")
depth_cell = None
for row in range(1, 200):
    try:
        if sheet.getAlias("B%d" % row) == "MagnetHoleDepth":
            depth_cell = "B%d" % row
            break
    except Exception:
        continue
if depth_cell is None:
    check("MagnetHoleDepth alias exists", False, "no aliased cell found")
else:
    value = float(sheet.get(depth_cell))
    check("%s (MagnetHoleDepth) == %s" % (depth_cell, EXPECTED_DEPTH),
          abs(value - EXPECTED_DEPTH) < TOL, "= %s" % value)

say("\n=== 2. Pocket feature Length ===")
for name in POCKETS:
    pocket = doc.getObject(name)
    if pocket is None:
        check("%s exists" % name, False, "object missing")
        continue
    length = float(pocket.Length)
    check("%s.Length == %s" % (name, EXPECTED_DEPTH),
          abs(length - EXPECTED_DEPTH) < TOL, "= %s mm" % length)

say("\n=== 3. Measured pocket depth in the finished solid ===")
say("    (cylinder height along its own axis, so the leaned palm rest face is")
say("     measured along the bore, not along Y)")
bodies = [o for o in doc.Objects if o.TypeId == "PartDesign::Body" and o.Shape.Faces]
measured = {}
for body in bodies:
    cylinders = magnet_cylinders(body.Shape)
    if not cylinders:
        continue
    measured[body.Name] = cylinders
    check("%s: 2 magnet bores present" % body.Name, len(cylinders) == 2,
          "found %d" % len(cylinders))
    for index, (axis, low, high) in enumerate(cylinders):
        depth = (high - low).Length
        check("%s bore %d depth == %s" % (body.Name, index + 1, EXPECTED_DEPTH),
              abs(depth - EXPECTED_DEPTH) < TOL, "= %.4f mm" % depth)
check("bodies carrying magnet bores == 4 (2 palm rests + 2 bodies)",
      len(measured) == 4, "found %d: %s" % (len(measured), sorted(measured)))

say("\n=== 4. Material behind the body-side pocket floor ===")
for body in bodies:
    if body.Name not in measured or "Palm" in body.Name:
        continue
    for index, (axis, low, high) in enumerate(measured[body.Name]):
        # The pocket floor is whichever end has solid material just beyond it.
        if body.Shape.isInside(high + axis * 0.3, 1e-7, True):
            floor, direction = high, axis
        elif body.Shape.isInside(low - axis * 0.3, 1e-7, True):
            floor, direction = low, App.Vector(axis).multiply(-1)
        else:
            check("%s bore %d has a floor" % (body.Name, index + 1), False,
                  "no material beyond either end — pocket broke through")
            continue
        run = material_run(body.Shape, floor, direction)
        check("%s bore %d backing == %s" % (body.Name, index + 1, EXPECTED_BACKING),
              run is not None and abs(run - EXPECTED_BACKING) < TOL,
              "= %s mm" % ("none" if run is None else "%.4f" % run))

say("\n" + "=" * 66)
if failures:
    say("FAILED %d check(s):" % len(failures))
    for label in failures:
        say("  - %s" % label)
    sys.exit(1)
say("All checks passed.")
sys.exit(0)
