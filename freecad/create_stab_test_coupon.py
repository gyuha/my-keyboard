"""Stabilizer Y-offset test coupon.

Three 2u test stations on one bar, identical to the real switch plate except for
StabCutoutYOffset, so the wire-vs-keycap clearance can be compared in a single
short print instead of one full plate per candidate value.

Geometry constants are copied from create_keyboard_parametric.py (that script
runs main() on import, so it cannot be imported for them). Keep them in sync.

The bar is 2 mm thick rather than the plate's 4 mm: the 1.4 mm clip ledge is
preserved, so the stabilizer seats at the same height above the top face and the
Y clearance being measured is unchanged, but the slot walls are shallower and
the housing may sit looser than in the real plate.

Stations are ordered left to right by ascending offset; the notches on the front
edge repeat that order (1 notch = first station) so a cut-apart or flipped coupon
is still identifiable.
"""

import os

import FreeCAD as App
import Part
import Mesh

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# StabCutoutYOffset values under test — one station per value. Measured so far:
# +0.4 the keycap hits the wire and +0.6 the wire hits the switch, so between
# them the wire is trapped under the keycap skirt in a 0.2 mm window. Moving the
# switch 1 mm away instead worked, which is the same relative geometry as an
# offset around -0.8: far enough down that the wire clears the keycap footprint
# entirely, so the margin widens instead of pinching.
OFFSETS = [-0.6, -0.8, -1.0]

THICKNESS = 2.0                    # coupon bar (real plate is PlateThickness 4.0)
CLIP_LEDGE = 1.4                   # StabClipPlateThickness — kept at the real value
RELIEF_WIDEN = 1.2                 # StabClipLedgeWidth
KEYHOLE = 13.96                    # KeyholeSize
SLOT_W = 3.30                      # DXF stab slot short dimension
SLOT_H = 14.10                     # StabCutoutHeight
STAB_DX = 11.900                   # DXF stab slot X offset from the switch centre
DXF_DY = -0.650                    # DXF stab slot Y offset from the switch centre

PITCH = 32.0                       # station spacing: fits the slots, not a whole
                                   # 2u keycap -- stations are tested one at a
                                   # time, so the cap may overhang its neighbour
DEPTH = 22.0
INDEX_R = 1.5                      # index notch radius (cut into the front edge)


def box(dx, dy, dz, x, y, z):
    """Axis-aligned box centred on (x, y) in plan, with its base at z."""
    return Part.makeBox(dx, dy, dz, App.Vector(x - dx / 2.0, y - dy / 2.0, z))


def main():
    for name in list(App.listDocuments().keys()):
        if name.lower().startswith("stab_test_coupon"):
            App.closeDocument(name)
    document = App.newDocument("Stab_Test_Coupon")

    length = PITCH * len(OFFSETS)
    solid = Part.makeBox(length, DEPTH, THICKNESS, App.Vector(0, -DEPTH / 2.0, 0))

    cuts = []
    for index, offset in enumerate(OFFSETS):
        cx = PITCH * (index + 0.5)
        slot_cy = DXF_DY + offset

        cuts.append(box(KEYHOLE, KEYHOLE, THICKNESS, cx, 0.0, 0.0))
        for sign in (-1, 1):
            sx = cx + sign * STAB_DX
            # through slot
            cuts.append(box(SLOT_W, SLOT_H, THICKNESS, sx, slot_cy, 0.0))
            # underside clip relief: extends the slot ends, leaving CLIP_LEDGE on top
            cuts.append(box(SLOT_W, SLOT_H + 2 * RELIEF_WIDEN,
                            THICKNESS - CLIP_LEDGE, sx, slot_cy, 0.0))

        for notch in range(index + 1):
            nx = cx - 2.0 * index + 4.0 * notch
            cuts.append(Part.makeCylinder(
                INDEX_R, THICKNESS, App.Vector(nx, -DEPTH / 2.0, 0)))

    for cut in cuts:
        solid = solid.cut(cut)

    solid = solid.removeSplitter()
    obj = document.addObject("Part::Feature", "Stab_Test_Coupon")
    obj.Shape = solid
    document.recompute()
    # Name the output by the offsets it carries, so regenerating one variant
    # never overwrites another that is still queued for printing.
    tag = "_".join("%.2f" % offset for offset in OFFSETS)
    document.saveAs(os.path.join(BASE_DIR, "stab_test_coupon_%s.FCStd" % tag))

    out = os.path.join(BASE_DIR, "parametric_stl", "stab_test_coupon_%s.stl" % tag)
    Mesh.export([obj], out)

    bb = solid.BoundBox
    print("offsets: %s" % ", ".join("+%.1f" % o for o in OFFSETS))
    print("valid=%s solids=%d" % (solid.isValid(), len(solid.Solids)))
    print("bbox %.2f x %.2f x %.2f mm" % (bb.XLength, bb.YLength, bb.ZLength))
    for index, offset in enumerate(OFFSETS):
        print("  station %d (%d hole%s): offset +%.1f -> slot centre Y %+.3f from switch centre"
              % (index + 1, index + 1, "" if index == 0 else "s", offset, DXF_DY + offset))
    print("exported %s" % out)


main()
