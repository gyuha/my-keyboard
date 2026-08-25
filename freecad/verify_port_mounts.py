"""Headless check that the floor-mounted port cradles and the rear-wall openings
match the stack derived in ADR 260824-224604.

Run with the console binary (never the GUI -- saving from a console run drops the
GuiDocument and the part colours go with it):

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd freecad/verify_port_mounts.py

`FreeCAD -c <script>` gives the same result, but that wrapper dumps the whole
process environment to stdout before it starts, so it is the wrong one to pipe into
a log or a CI transcript.

Exits 0 when all eight items pass, 1 otherwise. Runs in ~1s, so it sits outside the
~10min GUI regeneration and can be run on every edit.

Everything here measures the finished solid, never a feature property: a Pocket
whose Length reads 1.2 still leaves a 3mm wall if the relief patch behind it was
never cut, and a cradle whose sketch says 12.6 still pinches the board if a screw
boss grew into it.

  - openings come from the inner wires of the rear outer face, so the count is
    topological rather than clustered by guesswork (the left half's two ports are
    11.4mm apart, close enough that grouping their corner arcs by X mis-splits
    them; the wires cannot be mis-split);
  - the wall a plug has to cross is the Y extent of that opening's corner arcs,
    which is the material actually left after the relief patch;
  - cradle inner sizes come from rays fired at the walls through the void the
    board sits in.

Nothing is located by a hard-coded XY: each cradle is found by its seat faces (the
only upward-facing planes at that Z), so the script survives an OuterMargin change.

Two contract notes for the modeller. First, a cradle whose rear face lands within
5mm of the outer face is treated as bearing on the port seat, and then that face
must be exactly PortWallThickness (1.0) inside the outer face -- not 3.0. Referencing
the pocket to the cavity wall and cutting the relief patch as a separate cosmetic
feature passes every other item here and still leaves the plug bottoming out on the
case, which is the one failure the port seat exists to prevent.

Second, item 5 measures the module pocket in Y as well as
X, so the module cradle must be closed on all four sides. A three-sided pocket
leaves Y unmeasurable, and on the left half -- which has no rear wall to butt the
board against and no plug to push it home -- nothing else stops the board walking
out of the cradle under hand-wiring strain. The closing rib is 1.5mm of vertical
wall, so it costs no support.
"""

import os
import sys

import FreeCAD as App

DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keyboard_parametric.FCStd")

# --- expected values: all from the plan's derived stack, none re-derived here ---
PORT_AXIS_Z = -6.45            # both connectors' centre height, body-local
PORT_WALL = 1.0                # PortWallThickness: what is left of the 3mm rear
                               # wall after the local relief patch
MODULE_SEAT_Z = -9.00          # RP2040-Zero rail top (1.2mm rail clears the 1.0mm
                               # bottom chip)
BREAKOUT_SEAT_Z = -9.60        # USB-C breakout pad top (0.6mm pad)
MODULE_INNER = (18.6, 24.1)    # 18.0 x 23.5 board + 2 x CradleClearance 0.3
BREAKOUT_INNER = (12.6, 15.6)  # 12.0 x 15.0 board + 2 x CradleClearance 0.3
MIN_CRADLE_WEB = 1.5           # solid left between the two cradle pockets
OPENING_RADIUS = 1.5           # UsbOpeningRadius, the corner arcs we hunt for
OPENING_HEIGHT = 4.5           # UsbOpeningHeight; only used to place the ray probe

# Right carries the host port + the split-link port; left carries the split-link
# port only (its module sits inboard by the header and gets no opening at all).
BODIES = [("Left_Keyboard_Body", 1), ("Right_Keyboard_Body", 2)]

TOL = 0.05
# 0.15mm above the seat: inside the board slot for both boards (1.0t and 1.6t) and
# below the opening's lower edge (PORT_AXIS_Z - OPENING_HEIGHT/2 = -9.50), so a ray
# fired at the rear wall hits the port seat instead of escaping through the hole.
PROBE_LIFT = 0.15
# Wide enough to keep the module's two floor rails in one group (they sit at the
# two X extremes of an 18.6mm pocket) without reaching an unrelated feature.
SEAT_CLUSTER_GAP = 20.0

ITEMS = [
    "1. opening count (right 2, left 1)",
    "2. opening axis z == -7.25",
    "3. port seat wall == 1.0, flush with the outer face",
    "4. breakout cradle 12.6 x 15.6, bearing 1.0 inside the outer face",
    "5. module cradle 18.6 x 24.1, bearing 1.0 inside the outer face",
    "6. web between the two cradles >= 1.5",
    "7. seat heights: module -9.80, breakout -10.40",
    "8. no Aux_Guide objects left",
]
COUNT, AXIS, WALL, BREAKOUT, MODULE, WEB, SEATS, AUX = range(8)
failed_items = set()


def say(text):
    # freecadcmd exits without flushing a block-buffered stdout, so every line is
    # flushed as it is written or the whole report is lost on sys.exit().
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def check(item, label, ok, detail):
    say("  %s %-54s %s" % ("PASS" if ok else "FAIL", label, detail))
    if not ok:
        failed_items.add(item)


def fmt(value):
    return "none" if value is None else "%.3f" % value


def is_axis(surface, letter):
    return abs(abs(getattr(App.Vector(surface.Axis).normalize(), letter)) - 1.0) < 1e-6


def void_run(shape, start, direction, limit=45.0, step=0.1):
    """Distance from `start` (which must be in void) to the first solid along
    `direction`, by march-then-bisect. None if nothing is hit inside `limit`."""
    probe = step
    hit = None
    while probe <= limit:
        if shape.isInside(start + direction * probe, 1e-7, True):
            hit = probe
            break
        probe += step
    if hit is None:
        return None
    lo, hi = hit - step, hit
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if shape.isInside(start + direction * mid, 1e-7, True):
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def rear_outer_face(shape, y_rear):
    """The single planar face at y == y_rear. Its inner wires are the openings."""
    best = None
    for face in shape.Faces:
        if face.Surface.TypeId != "Part::GeomPlane" or not is_axis(face.Surface, "y"):
            continue
        box = face.BoundBox
        if abs(box.YMin - y_rear) > 1e-4 or abs(box.YMax - y_rear) > 1e-4:
            continue
        if best is None or face.Area > best.Area:
            best = face
    return best


def openings(shape, face):
    """One entry per hole in the rear face: (x centre, z centre, arc faces). The
    outer wire is the one with the largest bounding box, so it drops out."""
    wires = sorted(face.Wires, key=lambda w: w.BoundBox.DiagonalLength)[:-1]
    arcs = [f for f in shape.Faces
            if f.Surface.TypeId == "Part::GeomCylinder"
            and abs(f.Surface.Radius - OPENING_RADIUS) <= 0.02
            and is_axis(f.Surface, "y")
            and f.BoundBox.YMax > face.BoundBox.YMax - 4.0]
    result = []
    for wire in wires:
        box = wire.BoundBox
        mine = [f for f in arcs
                if box.XMin - 0.1 <= f.BoundBox.Center.x <= box.XMax + 0.1
                and box.ZMin - 0.1 <= f.BoundBox.Center.z <= box.ZMax + 0.1]
        result.append(((box.XMin + box.XMax) / 2.0, (box.ZMin + box.ZMax) / 2.0, mine))
    return sorted(result)


def seat_clusters(shape, z_target):
    """Groups of upward-facing horizontal faces at z_target -- one group per cradle
    seat. More than one group means the seat cannot be identified, and the cradle
    measurement below has to be reported as unmeasurable rather than guessed."""
    faces = []
    for face in shape.Faces:
        if face.Surface.TypeId != "Part::GeomPlane" or not is_axis(face.Surface, "z"):
            continue
        box = face.BoundBox
        z = (box.ZMin + box.ZMax) / 2.0
        if abs(z - z_target) > TOL:
            continue
        # CenterOfMass rather than the bbox centre: a bbox centre can fall in a
        # hole and then the material probe below would read the wrong side.
        centre = face.CenterOfMass
        if not shape.isInside(App.Vector(centre.x, centre.y, z - 0.2), 1e-7, True):
            continue
        if shape.isInside(App.Vector(centre.x, centre.y, z + 0.2), 1e-7, True):
            continue
        faces.append(face)
    clusters = []
    for face in faces:
        box = face.BoundBox
        entry = [box.XMin, box.XMax, box.YMin, box.YMax, [face]]
        for other in list(clusters):
            if (entry[0] - SEAT_CLUSTER_GAP <= other[1]
                    and entry[1] + SEAT_CLUSTER_GAP >= other[0]
                    and entry[2] - SEAT_CLUSTER_GAP <= other[3]
                    and entry[3] + SEAT_CLUSTER_GAP >= other[2]):
                entry[0] = min(entry[0], other[0])
                entry[1] = max(entry[1], other[1])
                entry[2] = min(entry[2], other[2])
                entry[3] = max(entry[3], other[3])
                entry[4] += other[4]
                clusters.remove(other)
        clusters.append(entry)
    return clusters


def cradle_box(shape, cluster, seat_z):
    """Inner footprint of the pocket above a seat, measured by firing rays at the
    cradle walls from PROBE_LIFT above the seat centre.

    The Y rays are fired at three X positions (centre and 0.5mm inside each side
    wall) instead of one, because a single centre ray cannot tell a full-width port
    seat from a relief patch narrower than the board. That distinction is the whole
    point of the port seat: if the patch is 16mm wide but the module pocket is
    18.6mm, the board's rear corners land on the untouched 3mm wall, the board stops
    2mm short, and the receptacle -- which only protrudes 1.0mm -- stays recessed.
    The plug then bottoms out on the case instead of the connector.

    Returns a dict with width, depth, the bounds, and the spread of the front/rear
    bearing planes across the sampled width."""
    cx = (cluster[0] + cluster[1]) / 2.0
    cy = (cluster[2] + cluster[3]) / 2.0
    z = seat_z + PROBE_LIFT
    result = {"width": None, "depth": None, "x0": None, "x1": None,
              "y0": None, "y1": None, "front_spread": None, "rear_spread": None,
              "note": ""}
    if shape.isInside(App.Vector(cx, cy, z), 1e-7, True):
        result["note"] = "probe point sits in material"
        return result
    xn = void_run(shape, App.Vector(cx, cy, z), App.Vector(-1, 0, 0))
    xp = void_run(shape, App.Vector(cx, cy, z), App.Vector(1, 0, 0))
    missing = []
    if xn is None:
        missing.append("-x")
    if xp is None:
        missing.append("+x")
    if xn is not None and xp is not None:
        result["x0"], result["x1"] = cx - xn, cx + xp
        result["width"] = xp + xn
        inset = max(0.0, result["width"] / 2.0 - 0.5)
        samples = [cx - inset, cx, cx + inset]
    else:
        samples = [cx]
    fronts, rears = [], []
    for px in samples:
        start = App.Vector(px, cy, z)
        yn = void_run(shape, start, App.Vector(0, -1, 0))
        yp = void_run(shape, start, App.Vector(0, 1, 0))
        if yn is None or yp is None:
            missing.append("%s%s" % ("-y" if yn is None else "+y",
                                     "" if px == cx else "@%.2f" % px))
            continue
        fronts.append(cy - yn)
        rears.append(cy + yp)
    if len(fronts) == len(samples) and fronts:
        result["y0"], result["y1"] = fronts[len(fronts) // 2], rears[len(rears) // 2]
        result["depth"] = result["y1"] - result["y0"]
        result["front_spread"] = max(fronts) - min(fronts)
        result["rear_spread"] = max(rears) - min(rears)
    if missing:
        result["note"] = "no wall found: " + ",".join(missing)
    return result


def separation(a_low, a_high, b_low, b_high):
    """Gap between two 1-D intervals; negative means they overlap."""
    if None in (a_low, a_high, b_low, b_high):
        return None
    return max(a_low, b_low) - min(a_high, b_high)


def report(doc):

    say("\n=== item 8: objects left over from the aux board ===")
    stale = [o.Name for o in doc.Objects if "Aux_Guide" in o.Name or "Aux_Guide" in o.Label]
    check(AUX, "no object named *Aux_Guide*", not stale,
          "found %d%s" % (len(stale), ": " + ", ".join(stale) if stale else ""))

    for body_name, expected_openings in BODIES:
        body = doc.getObject(body_name)
        say("\n=== %s ===" % body_name)
        if body is None or not body.Shape.Faces:
            for item in (COUNT, AXIS, WALL, BREAKOUT, MODULE, WEB, SEATS):
                check(item, "%s: solid available" % body_name, False, "body missing or empty")
            continue
        shape = body.Shape
        x_off = body.Placement.Base.x   # the right half is shifted +X for display only
        y_rear = shape.BoundBox.YMax

        # --- items 1-3: rear-wall openings ---------------------------------------
        face = rear_outer_face(shape, y_rear)
        if face is None:
            for item in (COUNT, AXIS, WALL):
                check(item, "rear outer face at y=%.2f" % y_rear, False, "not found")
            found = []
        else:
            found = openings(shape, face)
        check(COUNT, "openings found == %d" % expected_openings,
              face is not None and len(found) == expected_openings, "found %d" % len(found))
        if face is not None and not found:
            check(AXIS, "opening axis z == %s" % PORT_AXIS_Z, False, "no opening to measure")
            check(WALL, "port seat wall == %s" % PORT_WALL, False, "no opening to measure")
        for index, (cx, cz, arc_faces) in enumerate(found):
            check(AXIS, "opening %d (x=%.2f) axis z == %s" % (index + 1, cx - x_off, PORT_AXIS_Z),
                  abs(cz - PORT_AXIS_Z) <= TOL, "= %.3f" % cz)
            if not arc_faces:
                check(WALL, "opening %d wall == %s" % (index + 1, PORT_WALL), False,
                      "no r=%s corner arc found" % OPENING_RADIUS)
                continue
            thickness = max(f.BoundBox.YLength for f in arc_faces)
            outer = max(f.BoundBox.YMax for f in arc_faces)
            check(WALL, "opening %d wall == %s, flush with outer face" % (index + 1, PORT_WALL),
                  abs(thickness - PORT_WALL) <= TOL and abs(outer - y_rear) <= TOL,
                  "= %.3f mm, outer face offset %+.3f (%d arcs)"
                  % (thickness, outer - y_rear, len(arc_faces)))

        # --- item 7 + items 4-6: cradle seats and pockets -------------------------
        boxes = {}
        for item, name, seat_z, expected in ((BREAKOUT, "breakout", BREAKOUT_SEAT_Z, BREAKOUT_INNER),
                                             (MODULE, "module", MODULE_SEAT_Z, MODULE_INNER)):
            clusters = seat_clusters(shape, seat_z)
            check(SEATS, "%s seat at z == %s" % (name, seat_z), len(clusters) == 1,
                  "%d seat group(s)%s" % (len(clusters), "" if len(clusters) != 1 else
                                          " spanning %.2f x %.2f (%d face(s))"
                                          % (clusters[0][1] - clusters[0][0],
                                             clusters[0][3] - clusters[0][2],
                                             len(clusters[0][4]))))
            if len(clusters) != 1:
                check(item, "%s cradle inner == %s x %s" % ((name,) + expected), False,
                      "no single seat at z=%s to measure from" % seat_z)
                continue
            m = cradle_box(shape, clusters[0], seat_z)
            boxes[name] = (m["x0"], m["x1"], m["y0"], m["y1"])
            ok = (m["width"] is not None and m["depth"] is not None
                  and abs(m["width"] - expected[0]) <= TOL
                  and abs(m["depth"] - expected[1]) <= TOL
                  and m["front_spread"] <= TOL and m["rear_spread"] <= TOL)
            # A cradle against the rear wall must bear on the port seat, not on the
            # untouched 3mm cavity wall: the receptacle shell stands only 1.0mm proud
            # of the board, so 2mm too far out leaves the plug bottoming on the case.
            rear_gap = None if m["y1"] is None else y_rear - m["y1"]
            seated = rear_gap is not None and rear_gap < 5.0
            if seated:
                ok = ok and abs(rear_gap - PORT_WALL) <= TOL
            check(item, "%s cradle inner == %s x %s%s"
                  % ((name,) + expected + (" on the port seat" if seated else "",)), ok,
                  "= %s x %s, rear face %s inside the outer face, spread f %s / r %s %s"
                  % (fmt(m["width"]), fmt(m["depth"]), fmt(rear_gap),
                     fmt(m["front_spread"]), fmt(m["rear_spread"]), m["note"]))
        if len(boxes) == 2:
            b, m = boxes["breakout"], boxes["module"]
            gaps = [separation(b[0], b[1], m[0], m[1]), separation(b[2], b[3], m[2], m[3])]
            usable = [g for g in gaps if g is not None]
            web = max(usable) if usable else None
            check(WEB, "web between cradles >= %s" % MIN_CRADLE_WEB,
                  web is not None and web >= MIN_CRADLE_WEB - 1e-6,
                  "= %s (x %s / y %s)" % (fmt(web), fmt(gaps[0]), fmt(gaps[1])))
        else:
            check(WEB, "web between cradles >= %s" % MIN_CRADLE_WEB, False,
                  "both cradles must be measurable first")

    say("\n" + "=" * 74)
    for index, label in enumerate(ITEMS):
        say("  %s %s" % ("FAIL" if index in failed_items else "PASS", label))
    say("=" * 74)
    if failed_items:
        say("FAILED %d of %d items." % (len(failed_items), len(ITEMS)))
        return 1
    say("All 8 items passed.")
    return 0


# The self-test imports this file to run `report` against synthetic geometry, so the
# real document is only opened when the script is executed as a check.
if os.environ.get("VERIFY_PORT_MOUNTS_IMPORT") != "1":
    sys.exit(report(App.openDocument(DOC)))
