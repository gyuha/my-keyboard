"""Headless check that the case hugs the PCB with a stepped wall (ADR 261025-182809).

Run with the console binary (never the GUI — saving from freecadcmd drops the
GuiDocument and the part colours go with it):

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
        freecad/verify_pcb_fit.py

Exits 0 when every check passes, 1 otherwise. Everything is measured against the
`*_PCB_Reference` solid in the same document, so it checks the finished body, not
the parameters that built it:

  a. around the board's own height there is SEAT_GAP of air, then material
  b. the body outline is the PCB grown by SEAT_GAP + RING (RING_FRONT at the front)
  c. below the board the wall reaches under its edge: the ledge (left, right, rear;
     at the front the magnet backing blocks carry it)
  f. nothing in the body runs into the PCB
  g. a magnet in each front bore stays out of the PCB
  d. the ports and modules sit where they sat on the PCB before the outline moved
  e. what the host module slides under on the PCB's underside is short enough
"""

import os
import sys

import FreeCAD as App

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(BASE_DIR, "keyboard_parametric.FCStd")
sys.path.insert(0, os.path.join(BASE_DIR, "..", "tools"))
import pcb as pcb_source  # noqa: E402

SEAT_GAP = 0.5
RING = 1.2
RING_FRONT = 3.0   # plain wall at the front: the magnet bores need it
MAGNET_BORE_R = 5.15
MAGNET_DEPTH = 2.2
WALL = 3.0
PCB_BOTTOM = -2.6
MODULE_TOP = -4.9
# Bottom-side parts the host module may sit under, with their tallest body. The
# module already sat under diode D30 before the outline moved; what matters is Z.
SHORT_PARTS = {"SOD-323_L1.8-W1.3-LS2.5-RD": 1.1}
TOL = 0.05

# PCB-relative positions measured on the model before the outline moved (task 20
# baseline): distance from the PCB's inboard edge, or from its rear edge.
SPLIT_FROM_INBOARD = 15.90
HOST_MODULE_FROM_INBOARD = (24.65, 43.25)
WIRED_MODULE_FROM_REAR = (16.08, 40.18)

failures = []


def say(text):
    # freecadcmd exits without flushing a block-buffered stdout.
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def check(label, ok, detail):
    say("  %s %-58s %s" % ("PASS" if ok else "FAIL", label, detail))
    if not ok:
        failures.append(label)


def solid_at(shape, x, y, z):
    return shape.isInside(App.Vector(x, y, z), 1e-4, True)


def sketch_box(doc, name, dx):
    """A sketch's bound box in global X (sketches stay body-local)."""
    bb = doc.getObject(name).Shape.BoundBox
    return bb.XMin + dx, bb.XMax + dx, bb.YMin, bb.YMax


doc = App.openDocument(DOC)
project = pcb_source.load()

for side, host in (("Left", False), ("Right", True)):
    say("%s" % side)
    body = doc.getObject(side + "_Keyboard_Body")
    shape = body.Shape
    dx = body.Placement.Base.x
    p = doc.getObject(side + "_PCB_Reference").Shape.BoundBox
    mx, my = (p.XMin + p.XMax) / 2, (p.YMin + p.YMax) / 2

    # a. Air then ring, at mid-height of the board, on each side's midpoint.
    z = PCB_BOTTOM + 0.8
    for name, (x, y), (ux, uy) in (
            ("left", (p.XMin, my), (-1, 0)), ("right", (p.XMax, my), (1, 0)),
            ("front", (mx, p.YMin), (0, -1)), ("rear", (mx, p.YMax), (0, 1))):
        air = not solid_at(shape, x + ux * SEAT_GAP / 2, y + uy * SEAT_GAP / 2, z)
        t = RING_FRONT if name == "front" else RING
        ring = all(solid_at(shape, x + ux * (SEAT_GAP + f * t), y + uy * (SEAT_GAP + f * t), z)
                   for f in (0.1, 0.9))
        check("a. %s: %.1f air then %.1f ring" % (name, SEAT_GAP, t), air and ring,
              "air=%s ring=%s" % (air, ring))

    # b. Outline = PCB + gap + ring on every side.
    grow = SEAT_GAP + RING
    b = shape.BoundBox
    dev = max(abs(p.XMin - grow - b.XMin), abs(b.XMax - p.XMax - grow),
              abs(p.YMin - SEAT_GAP - RING_FRONT - b.YMin), abs(b.YMax - p.YMax - grow))
    check("b. outline == PCB + %.1f (front %.1f)" % (grow, SEAT_GAP + RING_FRONT), dev <= TOL,
          "%.2f x %.2f, worst deviation %.3f" % (b.XLength, b.YLength, dev))

    # c. Ledge: solid under the PCB's edge, air above it.
    under = WALL - grow - 0.1
    for name, (x, y), (ux, uy) in (
            ("left", (p.XMin, my), (1, 0)), ("right", (p.XMax, my), (-1, 0)),
            ("rear", (mx, p.YMax), (0, -1))):
        lx, ly = x + ux * under, y + uy * under
        ledge = solid_at(shape, lx, ly, PCB_BOTTOM - 0.2)
        above = not solid_at(shape, lx, ly, PCB_BOTTOM + 0.2)
        check("c. %s: ledge %.1f under the edge" % (name, under), ledge and above,
              "below=%s above-clear=%s" % (ledge, above))

    # f. Nothing of the body inside the board (the magnet backing blocks did).
    clash = shape.common(doc.getObject(side + "_PCB_Reference").Shape).Volume
    check("f. body does not run into the PCB", clash < 1e-3, "= %.3f mm^3" % clash)

    # g. A magnet seated in each front bore stays out of the board.
    import Part
    board_shape = doc.getObject(side + "_PCB_Reference").Shape
    bores = [f.Surface for f in shape.Faces
             if f.Surface.TypeId == "Part::GeomCylinder"
             and abs(f.Surface.Radius - MAGNET_BORE_R) < 1e-3]
    hit = sum(Part.makeCylinder(MAGNET_BORE_R, MAGNET_DEPTH,
                                App.Vector(c.Center.x, b.YMin, c.Center.z),
                                App.Vector(0, 1, 0)).common(board_shape).Volume
              for c in bores)
    check("g. %d front magnet bores clear of the PCB" % len(bores),
          len(bores) == 2 and hit < 1e-3, "= %.3f mm^3" % hit)

    # d. Ports and modules, relative to the PCB.
    inboard = p.XMax if side == "Left" else p.XMin
    sx0, sx1, _, _ = sketch_box(doc, side + "_Usb_Split", dx)
    split = abs((sx0 + sx1) / 2 - inboard)
    check("d. split port %.2f from inboard edge" % SPLIT_FROM_INBOARD,
          abs(split - SPLIT_FROM_INBOARD) <= TOL, "= %.3f" % split)
    mx0, mx1, my0, my1 = sketch_box(doc, side + "_Cradle_Module_Seat", dx)
    if host:
        near, far = mx0 - inboard, mx1 - inboard
        check("d. host module %.2f..%.2f from inboard edge" % HOST_MODULE_FROM_INBOARD,
              abs(near - HOST_MODULE_FROM_INBOARD[0]) <= TOL
              and abs(far - HOST_MODULE_FROM_INBOARD[1]) <= TOL,
              "= %.3f..%.3f" % (near, far))
    else:
        near, far = p.YMax - my1, p.YMax - my0
        check("d. wired module %.2f..%.2f from rear edge" % WIRED_MODULE_FROM_REAR,
              abs(near - WIRED_MODULE_FROM_REAR[0]) <= TOL
              and abs(far - WIRED_MODULE_FROM_REAR[1]) <= TOL,
              "= %.3f..%.3f" % (near, far))
        # It used to fill the old gap beside the board; now it hugs the wall that
        # reaches under the board's edge.
        hug = inboard - mx1
        check("d. wired module hugs the inboard wall (%.1f in)" % (WALL - grow),
              abs(hug - (WALL - grow)) <= TOL, "= %.3f" % hug)

    # e. Host module cradle vs the PCB's bottom-side parts (centre +- 2mm): anything
    # it slides under must be a known part whose top clears the module.
    if host:
        board = project.main(side.lower())
        ox, oy = p.XMin - board.outline.x_min, p.YMin - board.outline.y_min
        over = [c for c in board.components
                if c.layer == "bottom"
                and mx0 - 2 < c.x + ox < mx1 + 2 and my0 - 2 < c.y + oy < my1 + 2]
        bad = [c.designator for c in over
               if PCB_BOTTOM - SHORT_PARTS.get(c.footprint, 99.0) <= MODULE_TOP]
        check("e. host module clears the bottom-side parts above it", not bad,
              "under: %s; too tall: %s" % (", ".join(c.designator for c in over) or "none",
                                           ", ".join(bad) or "none"))

if failures:
    say("FAILED %d check(s)." % len(failures))
    sys.exit(1)
say("All PCB fit checks pass.")
sys.exit(0)
