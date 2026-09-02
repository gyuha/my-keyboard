#!/usr/bin/env python3
"""Verify the tilt-wedge centre hollow (task 18) straight from the exported STLs.

FreeCAD-free on purpose (retro 260819: keep verifiers outside the heavy
regeneration pipeline) -- reads the binary STLs in freecad/parametric_stl/.

Per wedge, four checks:
  1. outer silhouette unchanged  -- bbox dims match the pre-hollow baseline +-0.1mm
     (the pocket is interior only; any bbox drift means the outside moved)
  2. both alignment pins present -- vertices above the top face cluster into
     exactly 2 islands (pin height 1.3mm over the mating face)
  3. bottom skin ~2mm            -- a vertical ray through the hollow centre finds
     one material interval of WedgeHollowSkin (2.0 +-0.3mm; measured vertically,
     the ~5deg tilt inflates the normal thickness by <1%)
  4. volume cut by >=25%         -- total volume <= 0.75 x the solid baseline
"""

import os
import struct
import sys

STL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parametric_stl")

PIN_HEIGHT = 1.3          # WedgeAlignPinHeight
SKIN = 2.0                # WedgeHollowSkin (normal thickness; ray measures vertical)
SKIN_TOL = 0.3
BBOX_TOL = 0.1
VOLUME_MAX_RATIO = 0.75

# Pre-hollow baselines measured 2026-09-02 (solid wedges, plan "원천" section).
BASELINE = {
    "left_tilt_wedge.stl": {"volume": 68538.0, "bbox": (144.0625, 90.7841, 10.1919)},
    "right_tilt_wedge.stl": {"volume": 93449.6, "bbox": (196.4500, 90.7841, 10.1919)},
}

failures = []


def say(text):
    print(text)


def fail(name, text):
    failures.append("%s: %s" % (name, text))
    say("  FAIL %s" % text)


def load(path):
    with open(path, "rb") as f:
        f.read(80)
        count = struct.unpack("<I", f.read(4))[0]
        tris = []
        for _ in range(count):
            d = struct.unpack("<12fH", f.read(50))
            tris.append((d[3:6], d[6:9], d[9:12]))
        return tris


def volume_of(tris):
    total = 0.0
    for (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) in tris:
        total += (x1 * (y2 * z3 - y3 * z2)
                  - y1 * (x2 * z3 - x3 * z2)
                  + z1 * (x2 * y3 - x3 * y2)) / 6.0
    return total


def bbox_of(tris):
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for tri in tris:
        for p in tri:
            for k in range(3):
                lo[k] = min(lo[k], p[k])
                hi[k] = max(hi[k], p[k])
    return lo, hi


def pin_islands(tris, top_z):
    """Cluster vertices above the mating face into XY islands (should be 2 pins)."""
    pts = set()
    for tri in tris:
        for x, y, z in tri:
            if z > top_z + 0.2:
                pts.add((round(x, 3), round(y, 3)))
    islands = []
    for x, y in sorted(pts):
        for isle in islands:
            ix, iy = isle[0]
            if abs(x - ix) < 6.0 and abs(y - iy) < 6.0:
                isle.append((x, y))
                break
        else:
            islands.append([(x, y)])
    return islands


def material_intervals(tris, x0, y0):
    """Crossing z's of a vertical ray at (x0, y0), paired even-odd into material."""
    zs = []
    for (ax, ay, az), (bx, by, bz), (cx, cy, cz) in tris:
        d1 = (bx - ax) * (y0 - ay) - (by - ay) * (x0 - ax)
        d2 = (cx - bx) * (y0 - by) - (cy - by) * (x0 - bx)
        d3 = (ax - cx) * (y0 - cy) - (ay - cy) * (x0 - cx)
        has_neg = d1 < 0 or d2 < 0 or d3 < 0
        has_pos = d1 > 0 or d2 > 0 or d3 > 0
        if has_neg and has_pos:
            continue  # (x0, y0) outside this triangle's XY projection
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        if abs(nz) < 1e-9:
            continue  # vertical wall, grazing hit
        z = az - (nx * (x0 - ax) + ny * (y0 - ay)) / nz
        zs.append(z)
    zs.sort()
    # Merge duplicate crossings from shared edges.
    dedup = []
    for z in zs:
        if not dedup or z - dedup[-1] > 1e-4:
            dedup.append(z)
    return [(dedup[i], dedup[i + 1]) for i in range(0, len(dedup) - 1, 2)]


def check(name):
    say(name)
    base = BASELINE[name]
    tris = load(os.path.join(STL_DIR, name))

    lo, hi = bbox_of(tris)
    dims = tuple(hi[k] - lo[k] for k in range(3))
    if all(abs(dims[k] - base["bbox"][k]) <= BBOX_TOL for k in range(3)):
        say("  PASS bbox unchanged            %.4f x %.4f x %.4f" % dims)
    else:
        fail(name, "bbox %.4f x %.4f x %.4f != baseline %.4f x %.4f x %.4f"
             % (dims + base["bbox"]))

    top_z = hi[2] - PIN_HEIGHT
    islands = pin_islands(tris, top_z)
    if len(islands) == 2:
        say("  PASS alignment pins            2 islands above top face z=%.2f" % top_z)
    else:
        fail(name, "expected 2 pin islands above z=%.2f, found %d" % (top_z, len(islands)))

    x0 = (lo[0] + hi[0]) / 2.0
    y0 = (lo[1] + hi[1]) / 2.0
    intervals = material_intervals(tris, x0, y0)
    thickness = sum(b - a for a, b in intervals)
    if abs(thickness - SKIN) <= SKIN_TOL and len(intervals) == 1:
        say("  PASS skin at hollow centre     %.3f mm (1 interval) at (%.1f, %.1f)"
            % (thickness, x0, y0))
    else:
        fail(name, "material at (%.1f, %.1f) is %.3f mm in %d interval(s), want %.1f +-%.1f in 1"
             % (x0, y0, thickness, len(intervals), SKIN, SKIN_TOL))

    volume = volume_of(tris)
    limit = base["volume"] * VOLUME_MAX_RATIO
    if volume <= limit:
        say("  PASS volume reduced            %.0f mm^3 <= %.0f (baseline %.0f, -%.0f%%)"
            % (volume, limit, base["volume"], (1 - volume / base["volume"]) * 100))
    else:
        fail(name, "volume %.0f mm^3 > limit %.0f (baseline %.0f)"
             % (volume, limit, base["volume"]))


def main():
    say("Tilt-wedge hollow check -- skin %.1f +-%.1f mm, volume <= %.0f%% of solid baseline"
        % (SKIN, SKIN_TOL, VOLUME_MAX_RATIO * 100))
    say("=" * 100)
    for name in BASELINE:
        check(name)
    say("=" * 100)
    if failures:
        say("%d check(s) failed." % len(failures))
        return 1
    say("All wedge hollow checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
