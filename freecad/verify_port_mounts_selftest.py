"""Synthetic proof that verify_port_mounts.py can actually go green, and that its
one non-obvious requirement bites.

A check that has never passed is not a check -- it may be measuring something the
geometry can never satisfy, and you only find that out after a 10-minute GUI
regeneration. So this builds two throwaway solids that are correct by construction
and asserts all eight items PASS, then re-runs case B with the module cradle
referenced to the cavity wall instead of the port seat, and asserts that item 5
alone FAILS.

Case B is the counter-example worth keeping. The pocket is the right size, the
opening is at the right height, the wall at the opening is a correct 1.0mm and the
seats are at the right Z -- every other item reads perfect. But the board's rear
edge bears 3.0mm inside the outer face instead of 1.0mm, so the host USB-C, whose
shell stands only 1.0mm proud of the board, ends up 2mm back from the opening and
the plug bottoms out on the case. That is the failure the port seat exists to
prevent, and it is invisible to any check that only measures the pocket's size.

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
        freecad/verify_port_mounts_selftest.py
"""

import os
import sys

os.environ["VERIFY_PORT_MOUNTS_IMPORT"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import FreeCAD as App
import Part

import verify_port_mounts as V

WALL = 3.0
FLOOR_Z = -11.0
BODY_Z = -14.0
Y_REAR = 104.66
PATCH_DEPTH = 2.0            # leaves PortWallThickness 1.0 of the 3.0 rear wall
SEAT_Y = Y_REAR - WALL + PATCH_DEPTH   # 103.66: the port seat's inner face


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, App.Vector(x0, y0, z0))


def opening(cx):
    """Rounded-rect prism through the port seat, r=1.5, axis Y."""
    w, h, r = V.OPENING_RADIUS * 0 + 10.0, V.OPENING_HEIGHT, V.OPENING_RADIUS
    z = V.PORT_AXIS_Z
    prism = box(cx - w / 2, cx + w / 2, SEAT_Y - 0.66, Y_REAR + 0.2, z - h / 2, z + h / 2)
    along_y = [e for e in prism.Edges
               if abs(e.Vertexes[0].Point.x - e.Vertexes[-1].Point.x) < 1e-7
               and abs(e.Vertexes[0].Point.z - e.Vertexes[-1].Point.z) < 1e-7]
    return prism.makeFillet(r, along_y)


def cradle(shape, cx, inner_w, inner_d, seat_z, board_t, rear_y, rails):
    """Three walls (or four when `rear_y` is not the port seat) + seat + top lips."""
    x0, x1 = cx - inner_w / 2.0, cx + inner_w / 2.0
    y1 = rear_y
    y0 = y1 - inner_d
    top = seat_z + board_t
    cw, lip = 1.5, 0.8
    closed_rear = abs(rear_y - SEAT_Y) > 1e-6
    outer_y1 = y1 + cw if closed_rear else y1
    shape = shape.fuse(box(x0 - cw, x1 + cw, y0 - cw, outer_y1, FLOOR_Z, top))
    # Bounded at y1 exactly: overshooting here would cut straight through the rear
    # wall and merge the pocket with the opening.
    shape = shape.cut(box(x0, x1, y0, y1, FLOOR_Z, top + 1.0))
    if rails:
        for rx in (x0, x1 - cw):
            shape = shape.fuse(box(rx, rx + cw, y0, y1, FLOOR_Z, seat_z))
    else:
        shape = shape.fuse(box(x0, x1, y0, y1, FLOOR_Z, seat_z))
    for lx in (x0, x1 - lip):
        shape = shape.fuse(box(lx, lx + lip, y0, y1, top, top + 0.8))
    return shape


def half(x_hi, ports, module):
    """`ports` are (x, patch_width) for the rear openings; `module` is (x, rear_y)."""
    shape = box(-8.88, x_hi, 50.0, Y_REAR, BODY_Z, 0.0)
    shape = shape.cut(box(-8.88 + WALL, x_hi - WALL, 50.0 + WALL, Y_REAR - WALL,
                          FLOOR_Z, 0.5))
    for px, patch_w in ports:
        shape = shape.cut(box(px - patch_w / 2, px + patch_w / 2,
                              Y_REAR - WALL, SEAT_Y,
                              V.PORT_AXIS_Z - 4.0, V.PORT_AXIS_Z + 4.0))
        shape = shape.cut(opening(px))
    shape = cradle(shape, ports[0][0], V.BREAKOUT_INNER[0], V.BREAKOUT_INNER[1],
                   V.BREAKOUT_SEAT_Z, 1.6, SEAT_Y, rails=False)
    mx, m_rear = module
    shape = cradle(shape, mx, V.MODULE_INNER[0], V.MODULE_INNER[1],
                   V.MODULE_SEAT_Z, 1.0, m_rear, rails=True)
    return shape


def build(module_rear_y):
    doc = App.newDocument("PortMountSelfTest")
    left = doc.addObject("Part::Feature", "Left_Keyboard_Body")
    left.Shape = half(70.0, [(11.95, 16.0)], (45.0, 94.1))
    right = doc.addObject("Part::Feature", "Right_Keyboard_Body")
    right.Shape = half(70.0, [(11.95, 16.0), (30.5, 20.0)], (30.5, module_rear_y))
    right.Placement.Base = App.Vector(181.06, 0, 0)   # display offset, as the real doc
    doc.recompute()
    return doc


def run(label, module_rear_y):
    V.failed_items.clear()
    V.say("\n" + "#" * 74)
    V.say("# %s" % label)
    V.say("#   module cradle rear face at y=%.2f, %.2fmm inside the outer face"
          % (module_rear_y, Y_REAR - module_rear_y))
    V.say("#" * 74)
    code = V.report(build(module_rear_y))
    return code, set(V.failed_items)


code_a, failed_a = run("case A: geometry built to the derived stack", SEAT_Y)
code_b, failed_b = run("case B: module cradle referenced to the cavity wall "
                       "instead of the port seat", Y_REAR - WALL)

V.say("\n" + "=" * 74)
problems = []
if failed_a:
    problems.append("case A should pass all 8, failed: %s" % sorted(failed_a))
if code_a != 0:
    problems.append("case A exit code %d, expected 0" % code_a)
if failed_b != {V.MODULE}:
    problems.append("case B should fail item 5 only, failed: %s"
                    % sorted(i + 1 for i in failed_b))
if code_b == 0:
    problems.append("case B exit code 0, expected non-zero")
for line in problems:
    V.say("  SELFTEST FAIL %s" % line)
if problems:
    V.say("self-test FAILED")
    sys.exit(1)
V.say("  case A: all 8 items PASS, exit 0")
V.say("  case B: item 5 (module cradle) FAILS on the rear bearing plane, exit %d"
      % code_b)
V.say("self-test passed")
sys.exit(0)
