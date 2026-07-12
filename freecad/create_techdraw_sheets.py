"""Generate TechDraw sheets (A4 landscape) with core dimensions for every
manufacturable part in keyboard_switch_plates.FCStd.

Per part: orthographic views + overall extent dimensions (makeExtentDim) +
a text-annotation block listing the core feature dimensions. Run inside the
FreeCAD GUI (document must be open)."""
import FreeCAD as App
import TechDraw
import os

_FCSTD = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "keyboard_switch_plates.FCStd")
doc = None
for _d in App.listDocuments().values():
    if _d.Name == "keyboard_switch_plates":
        doc = _d
        break
if doc is None:
    doc = App.openDocument(_FCSTD)
TMPL = os.path.join(App.getResourceDir(), "Mod", "TechDraw", "Templates",
                    "Default_Template_A4_Landscape.svg")

# --- clean up any previous drawing objects ------------------------------------
_order = ["TechDraw::DrawViewDimExtent", "TechDraw::DrawViewDimension",
          "TechDraw::DrawLeaderLine", "TechDraw::DrawViewAnnotation",
          "TechDraw::DrawViewPart", "TechDraw::DrawViewCollection",
          "TechDraw::DrawPage", "TechDraw::DrawSVGTemplate"]
# Remove strictly in dependency order (children first) so no live reference
# dangles onto a just-deleted view — deleting out of order segfaults headless.
for tid in _order:
    for o in [x for x in doc.Objects if x.TypeId == tid]:
        try:
            doc.removeObject(o.Name)
        except Exception:
            pass
doc.recompute()

P = doc.getObject("Design_Parameters")


def val(obj, attr, default=None):
    try:
        return float(getattr(obj, attr))
    except Exception:
        return default


# measure a switch (14x14) cutout and the key pitch from the left cutout refs
def key_metrics():
    cut = doc.getObject("Left_Switch_Cutouts")
    squares = []
    for w in cut.Shape.Wires:
        b = w.BoundBox
        if 13.0 < b.XLength < 15.0 and 13.0 < b.YLength < 15.0:
            squares.append(b)
    size_x = round(squares[0].XLength, 2) if squares else 14.0
    size_y = round(squares[0].YLength, 2) if squares else 14.0
    # horizontal pitch = smallest positive centre-to-centre distance
    cx = sorted({round(b.Center.x, 2) for b in squares})
    pitch = None
    for i in range(1, len(cx)):
        d = round(cx[i] - cx[i - 1], 2)
        if d > 5 and (pitch is None or d < pitch):
            pitch = d
    return size_x, size_y, pitch or 19.05


KX, KY, KP = key_metrics()

th = val(P, "PlateThickness", 4.0)
mg = val(P, "Margin", 8.0)
cr = val(P, "CornerRadius", 5.0)
m3c = val(P, "M3ClearanceDiameter", 3.2)
m3d = val(P, "M3CountersinkDiameter", 6.0)
m3t = val(P, "M3CountersinkDepth", 1.5)
stab_ledge = val(P, "StabClipPlateThickness", 1.4)
stab_w = val(P, "StabClipLedgeWidth", 1.2)
bh = val(P, "BodyHeight", 18.0)
wall = val(P, "BodyWallThickness", 3.0)
boss = 8.0
trs_d = val(P, "TRSJackHoleDiameter", 6.5)
trs_ax = val(P, "TRSJackAxisHeight", 6.5)
trs_off = val(P, "TRSJackEdgeOffset", 17.5)
usb_w = val(P, "USBOpeningWidth", 10.0)
usb_h = val(P, "USBOpeningHeight", 6.0)
usb_off = val(P, "USBEdgeOffset", 37.0)
pr_depth = val(P, "PalmRestDepth", 80.0)
pr_rear = val(P, "PalmRestRearHeight", 25.0)
pr_front = val(P, "PalmRestFrontHeight", 12.0)

lb_tilt = round(val(doc.getObject("Left_Keyboard_Body"), "RestTiltAngle", 4.32), 2)


def notes_plate():
    return [
        "CORE DIMENSIONS (mm)",
        "Plate thickness: %.1f" % th,
        "Outer margin: %.1f   Corner: R%.1f" % (mg, cr),
        "Key cutout: %.1f x %.1f" % (KX, KY),
        "Key pitch: %.2f" % KP,
        "M3 hole: dia %.1f clearance" % m3c,
        "  c'sink dia %.1f x %.1f deep" % (m3d, m3t),
        "Stab clip pocket (top/bottom edge):",
        "  %.1f wide, leaves %.1f ledge" % (stab_w, stab_ledge),
    ]


def notes_body(side):
    n = [
        "CORE DIMENSIONS (mm)",
        "Body height: %.1f" % bh,
        "Wall / bottom: %.1f / %.1f" % (wall, wall),
        "Insert boss: dia %.1f" % boss,
        "Rest tilt: %.2f deg" % lb_tilt,
        "TRS jack: dia %.1f, axis h %.1f" % (trs_d, trs_ax),
        "  edge offset %.1f" % trs_off,
    ]
    if side == "Right":
        n += [
            "USB-C opening: %.1f x %.1f" % (usb_w, usb_h),
            "  edge offset %.1f" % usb_off,
            "RP2040-Zero seat: 25 x 18",
        ]
    return n


def notes_palm():
    return [
        "CORE DIMENSIONS (mm)",
        "Depth: %.1f" % pr_depth,
        "Rear height: %.1f" % pr_rear,
        "Front height: %.1f" % pr_front,
        "Flat shelf: 35.0",
        "Top fillet: R3.0",
        "Body gap: 5.0",
    ]


# view direction presets ->(Direction, XDirection). Top/Front/Right.
DIRS = {
    "Top":   (App.Vector(0, 0, 1),  App.Vector(1, 0, 0)),
    "Front": (App.Vector(0, -1, 0), App.Vector(1, 0, 0)),
    "Right": (App.Vector(1, 0, 0),  App.Vector(0, 1, 0)),
}


def add_view(page, src, kind, scale, x, y, label):
    v = doc.addObject("TechDraw::DrawViewPart", "TMP_V_" + label)
    page.addView(v)
    v.Source = [src]
    d, xd = DIRS[kind]
    v.Direction = d
    v.XDirection = xd
    v.ScaleType = "Custom"
    v.Scale = scale
    v.X = x
    v.Y = y
    v.Label = label
    v.recompute()
    return v


def add_extents(page, v):
    # Horizontal (0) + vertical (1) whole-view extent dims. Placement is left at
    # TechDraw's auto default: setting a custom X/Y on an extent dim and then
    # recomputing segfaults freecadcmd headless on macOS, so we don't.
    dh = TechDraw.makeExtentDim(v, [], 0)
    dv = TechDraw.makeExtentDim(v, [], 1)
    page.addView(dh)
    page.addView(dv)
    doc.recompute()
    return [dh, dv]


def add_note(page, lines, x, y, label):
    a = doc.addObject("TechDraw::DrawViewAnnotation", "TMP_Note_" + label)
    a.Text = lines
    a.TextSize = 2.6
    a.LineSpace = 90
    page.addView(a)
    a.X = x
    a.Y = y
    return a


def make_page(name, title):
    pg = doc.addObject("TechDraw::DrawPage", "TMP_Page_" + name)
    tp = doc.addObject("TechDraw::DrawSVGTemplate", "TMP_Tmpl_" + name)
    tp.Template = TMPL
    pg.Template = tp
    pg.Label = title
    return pg


# ---- part definitions --------------------------------------------------------
PARTS = [
    ("Left_Switch_Plate",  "Left switch plate",  "plate", notes_plate()),
    ("Right_Switch_Plate", "Right switch plate", "plate", notes_plate()),
    ("Left_Keyboard_Body", "Left keyboard body", "body",  notes_body("Left")),
    ("Right_Keyboard_Body", "Right keyboard body", "body", notes_body("Right")),
    ("Left_Palm_Rest",     "Left palm rest",     "palm",  notes_palm()),
    ("Right_Palm_Rest",    "Right palm rest",    "palm",  notes_palm()),
]

report = []
for obj_name, title, kind, notes in PARTS:
    src = doc.getObject(obj_name)
    bb = src.Shape.BoundBox
    pg = make_page(obj_name, title)
    if kind in ("plate", "body"):
        s = 0.55 if max(bb.XLength, bb.YLength) < 170 else 0.5
        vt = add_view(pg, src, "Top", s, 95, 140, obj_name + "_Top")
        vf = add_view(pg, src, "Front", s, 95, 55, obj_name + "_Front")
        views = [vt, vf]
        if kind == "body":
            views.append(add_view(pg, src, "Right", s, 215, 55, obj_name + "_Right"))
        nx, ny = 230, 165
    else:  # palm rest: side profile is primary
        vs = add_view(pg, src, "Right", 1.4, 90, 120, obj_name + "_Side")
        vt = add_view(pg, src, "Top", 0.7, 90, 45, obj_name + "_Top")
        views = [vs, vt]
        nx, ny = 225, 150
    doc.recompute()
    for v in views:
        add_extents(pg, v)
    add_note(pg, notes, nx, ny, obj_name)
    doc.recompute()
    report.append((title, pg.Name))

doc.recompute()
doc.saveAs(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "keyboard_switch_plates.FCStd"))

# ---- verification: list pages and measured extent values ---------------------
print("Pages created:")
for t, n in report:
    print("  %-22s -> %s" % (t, n))
print("Extent dimension values (mm):")
for d in doc.Objects:
    if d.TypeId == "TechDraw::DrawViewDimExtent":
        try:
            print("  %-40s %s = %.2f" % (d.Name, d.Type, d.getRawValue()))
        except Exception as e:
            print("  ", d.Name, "err", e)
