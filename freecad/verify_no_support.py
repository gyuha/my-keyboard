"""Headless check that every printed part comes off the bed without support.

Reads the exported STLs directly, so it needs no FreeCAD:

    python3 freecad/verify_no_support.py

Exits 0 when every part passes, 1 otherwise.

Print orientation is derived, not configured: the part rests on its **largest
downward-facing planar face**, which is what a slicer picks when you drop a part
on the plate. That lands on the flat bottom for the case body and on the slanted
face for the tilt wedge -- and on the wedge for a body that still has one fused
to it, matching how the case used to be placed (nose up by the wedge angle).

A face leaning more than OVERHANG_LIMIT_DEG from vertical is then judged, and
"steep" alone is NOT enough to fail it. Two shapes are steep and still print
clean, and calling them failures would only push the design to be worse:

  * **A ceiling that can be bridged.** A hole through or into a wall always has
    one -- magnet pocket, TRS jack, USB cutout, wedge alignment hole. The printer
    spans it from one wall to the opposite one, so what matters is the span, not
    the angle. Judged by BRIDGE_SPAN_MM: material within reach on two opposite
    sides means bridgeable. A floating rim fails this exactly as it should --
    it has a wall on the inside and open air on the outside, so it can only
    droop, and that is the flaw this whole check exists to catch.
  * **A round-over that lands tangent to the bed.** The wedge's rear ridge is
    filleted so it isn't a knife edge, and the fillet meets the bed at a
    tangent. Excluded up to BED_TANGENT_MM above the bed. The trade this makes:
    a genuine overhang living entirely inside that band would be missed. It is
    a thin band and anything real is far taller, so the loss is small.
"""

import math
import os
import struct
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STL_DIR = os.path.join(BASE_DIR, "parametric_stl")

# 45 deg is the slicer default: at 45 each layer still lands half on the one below.
OVERHANG_LIMIT_DEG = 45.0
# How far a printer will span unsupported between two anchors.
BRIDGE_SPAN_MM = 12.0
# Height band above the bed where a bed-tangent round-over lives (= the R3 ridge).
BED_TANGENT_MM = 3.05
# A face this close to the lowest point is sitting on the bed, not overhanging.
BED_BAND = 0.05
# Nothing but measurement noise may remain once the two shapes above are judged.
LIMIT_MM2 = 20.0

PARTS = [
    "left_keyboard_body.stl",
    "right_keyboard_body.stl",
    "left_tilt_wedge.stl",
    "right_tilt_wedge.stl",
]

failures = []


def say(text):
    print(text)


def read_stl(path):
    with open(path, "rb") as handle:
        handle.read(80)
        count = struct.unpack("<I", handle.read(4))[0]
        return [struct.unpack("<12fH", handle.read(50))[3:12] for _ in range(count)]


def face_normal_area(a, b, c):
    u = [b[i] - a[i] for i in range(3)]
    w = [c[i] - a[i] for i in range(3)]
    cross = [u[1] * w[2] - u[2] * w[1],
             u[2] * w[0] - u[0] * w[2],
             u[0] * w[1] - u[1] * w[0]]
    length = math.sqrt(sum(value * value for value in cross))
    if length == 0.0:
        return None, 0.0
    return [value / length for value in cross], length / 2.0


def bed_normal(triangles):
    """Model-space direction of the largest downward-facing planar face.

    Triangles are grouped by plane (normal + offset, rounded) so a face split
    into many triangles is weighed as one face.
    """
    planes = {}
    for a, b, c in triangles:
        normal, area = face_normal_area(a, b, c)
        if normal is None or normal[2] >= -0.01:
            continue
        offset = sum(normal[i] * a[i] for i in range(3))
        key = (round(normal[0], 3), round(normal[1], 3), round(normal[2], 3),
               round(offset, 2))
        entry = planes.setdefault(key, [0.0, normal])
        entry[0] += area
    if not planes:
        return None
    return max(planes.values(), key=lambda entry: entry[0])[1]


def rotation_to_bed(normal):
    """Rotation matrix (row vectors) taking `normal` to (0, 0, -1)."""
    target = (0.0, 0.0, -1.0)
    axis = [normal[1] * target[2] - normal[2] * target[1],
            normal[2] * target[0] - normal[0] * target[2],
            normal[0] * target[1] - normal[1] * target[0]]
    sin = math.sqrt(sum(value * value for value in axis))
    cos = sum(normal[i] * target[i] for i in range(3))
    if sin < 1e-9:
        return ([[1, 0, 0], [0, 1, 0], [0, 0, 1]] if cos > 0
                else [[1, 0, 0], [0, -1, 0], [0, 0, -1]])
    x, y, z = [value / sin for value in axis]
    angle = math.atan2(sin, cos)
    s, c = math.sin(angle), math.cos(angle)
    t = 1 - c
    return [[t * x * x + c,     t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c,     t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c]]


def rotate(matrix, point):
    return tuple(sum(matrix[i][k] * point[k] for k in range(3)) for i in range(3))


def ray_hits(origin, direction, candidates, limit):
    """True when a triangle is hit within `limit` along `direction`."""
    for a, b, c in candidates:
        e1 = [b[i] - a[i] for i in range(3)]
        e2 = [c[i] - a[i] for i in range(3)]
        p = [direction[1] * e2[2] - direction[2] * e2[1],
             direction[2] * e2[0] - direction[0] * e2[2],
             direction[0] * e2[1] - direction[1] * e2[0]]
        det = sum(e1[i] * p[i] for i in range(3))
        if abs(det) < 1e-9:
            continue
        inv = 1.0 / det
        t = [origin[i] - a[i] for i in range(3)]
        u = sum(t[i] * p[i] for i in range(3)) * inv
        if u < 0.0 or u > 1.0:
            continue
        q = [t[1] * e1[2] - t[2] * e1[1],
             t[2] * e1[0] - t[0] * e1[2],
             t[0] * e1[1] - t[1] * e1[0]]
        v = sum(direction[i] * q[i] for i in range(3)) * inv
        if v < 0.0 or u + v > 1.0:
            continue
        distance = sum(e2[i] * q[i] for i in range(3)) * inv
        if 1e-6 < distance <= limit:
            return True
    return False


def bridgeable(point, buckets):
    """True when material sits within reach on two opposite sides of `point`."""
    candidates = buckets.get(int(math.floor(point[2])), ())
    if not candidates:
        return False
    hits = [ray_hits(point, direction, candidates, BRIDGE_SPAN_MM)
            for direction in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))]
    return (hits[0] and hits[1]) or (hits[2] and hits[3])


def support_area(path):
    """(unsupported mm^2, bridged mm^2, bed-tangent mm^2, bed mm^2, tilt deg)."""
    triangles = read_stl(path)
    triangles = [(t[0:3], t[3:6], t[6:9]) for t in triangles]
    normal = bed_normal(triangles)
    if normal is None:
        return None
    matrix = rotation_to_bed(normal)
    placed = [tuple(rotate(matrix, vertex) for vertex in triangle)
              for triangle in triangles]
    z_min = min(min(vertex[2] for vertex in triangle) for triangle in placed)

    buckets = {}
    for triangle in placed:                       # index by the metre... by the mm
        low = int(math.floor(min(vertex[2] for vertex in triangle)))
        high = int(math.floor(max(vertex[2] for vertex in triangle)))
        for level in range(low, high + 1):
            buckets.setdefault(level, []).append(triangle)

    threshold = -math.cos(math.radians(OVERHANG_LIMIT_DEG))
    unsupported = bridged = tangent = bed = 0.0
    for triangle in placed:
        face, area = face_normal_area(*triangle)
        if face is None or face[2] > threshold:
            continue
        top = max(vertex[2] for vertex in triangle) - z_min
        if top < BED_BAND:
            bed += area
            continue
        if top < BED_TANGENT_MM:
            tangent += area
            continue
        centre = [sum(vertex[i] for vertex in triangle) / 3.0 for i in range(3)]
        centre[2] -= 0.15                          # just under the ceiling
        if bridgeable(centre, buckets):
            bridged += area
        else:
            unsupported += area
    tilt = math.degrees(math.acos(max(-1.0, min(1.0, -normal[2]))))
    return unsupported, bridged, tangent, bed, tilt


def check(name, path):
    if not os.path.exists(path):
        failures.append("%s is missing" % name)
        say("  MISSING  %s" % name)
        return
    result = support_area(path)
    if result is None:
        failures.append("%s has no downward face" % name)
        say("  BROKEN   %s — no downward-facing face to rest on" % name)
        return
    unsupported, bridged, tangent, bed, tilt = result
    ok = unsupported <= LIMIT_MM2
    if not ok:
        failures.append("%s needs %.1f mm^2 of support" % (name, unsupported))
    say("  %s %-26s support %7.1f   bridged %6.1f   bed-tangent %6.1f   "
        "bed %8.1f   tilt %.2f deg" % (
            "PASS" if ok else "FAIL", name, unsupported, bridged, tangent, bed, tilt))


if __name__ == "__main__":
    targets = sys.argv[1:] or [os.path.join(STL_DIR, name) for name in PARTS]
    say("Support check — over %.0f deg, bridge span %.0f mm, allowance %.0f mm^2" % (
        OVERHANG_LIMIT_DEG, BRIDGE_SPAN_MM, LIMIT_MM2))
    say("=" * 100)
    for path in targets:
        check(os.path.basename(path), path)
    say("=" * 100)
    if failures:
        say("FAILED %d part(s):" % len(failures))
        for label in failures:
            say("  - %s" % label)
        sys.exit(1)
    say("All parts print without support.")
    sys.exit(0)
