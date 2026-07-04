# -*- coding: utf-8 -*-
"""
분할 키보드(add-function 레이아웃) 3D 프린팅용 풀 케이스 파라메트릭 생성 스크립트.

입력  : freecad/left-switch.dxf, freecad/right-switch.dxf
        (LINE 세그먼트로 이루어진 외곽선 + 스위치 컷아웃; 좌 148.2x129.2 / 우 195.8x129.2)
출력  : 좌/우 각 상판(plate)+케이스 바디(body)+하판(bottom) 3부품 → 총 6 STL + keyboard.FCStd

설계 근거: .forge ADR-0001(파라메트릭 스크립트 원천), ADR-0002(컷아웃 오프셋).
FreeCAD GUI(MCP RPC) 또는 freecadcmd 헤드리스 모두에서 실행 가능.
값만 바꿔 재생성 → 재출력하는 워크플로우를 전제로 스크립트 상단 변수로 파라미터 노출.
"""

import os
import math
import FreeCAD as App
import Part

# ─────────────────────────────────────────────────────────────────────────────
# 파라미터 (스크립트 상단 노출 — 프린터/조립 요구에 맞춰 값만 수정해 재생성)
# ─────────────────────────────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
    else "/Users/gyuha/workspace/my-keyboard/freecad"

DXF = {"left": os.path.join(HERE, "left-switch.dxf"),
       "right": os.path.join(HERE, "right-switch.dxf")}

PLATE_T  = 1.5      # 상판 두께 (mm)
WALL_T   = 3.0      # 케이스 바디 벽 두께 (mm)
BOTTOM_T = 3.0      # 하판 두께 (mm)

DXF_CUTOUT = 13.9           # DXF 원본 스위치 컷아웃 한 변 (mm)
SWITCH_CUTOUT_TARGET = 14.0 # 목표 개구부 (mm) — FDM 수축 보정; 빡빡하면 14.05~14.15
CUT_OFFSET = (SWITCH_CUTOUT_TARGET - DXF_CUTOUT) / 2.0  # 컷아웃 와이어 바깥 오프셋량

TILT_DEG    = 6.0   # 웨지 틸트 각(앞으로 6도)
FRONT_INT_H = 12.0  # 앞쪽 내부 여유 높이 (mm); 뒤쪽은 depth에 6도 적용해 파생

# 결합 파라미터 — 상판을 바디(tub)에 M3 접시나사로 체결
#   인서트: Spredsert M3x5 (devicemart no=1067969) — 바디 보스 상단에 압입, 파일럿 Ø4.0
#   나사  : 접시머리 십자 머신스크류 M3x10 (devicemart no=34782) — 상판 관통 후 인서트 체결
BOSS_OD            = 7.0   # 인서트 보스 외경
BOSS_WALL_OVERLAP  = 2.2   # 보스가 벽과 겹치는 양(mm). 클수록 보스가 코너(라운드 중심)쪽으로 이동. d=WALL_T+BOSS_OD/2-overlap=4.3 (실측 유효창 4.2~4.9, 라운드반경 ~3.45)
INSERT_HOLE_D      = 4.0   # Spredsert M3 압입 파일럿 홀 지름
INSERT_HOLE_DEPTH  = 7.0   # 인서트 홀 깊이 (인서트 5mm + 나사끝 여유)
SCREW_CLEAR_D      = 3.4   # 상판 M3 나사 관통 클리어런스 지름
CSK_TOP_D          = 6.0   # 접시머리 카운터싱크 상단 지름 (M3 접시머리 ~6mm)
CSK_DEPTH          = 1.3   # 90° 접시 카운터싱크 깊이 (Ø6→Ø3.4, plate 1.5 내)

# 포트/컨트롤러 (뒷벽; 좌/우 미러)
USBC_W, USBC_H    = 9.5, 4.0   # USB-C 컷아웃 (폭x높이)
TRRS_D            = 6.0        # TRRS(PJ-320A) 원형 컷아웃 지름
RP2040_W, RP2040_L = 18.0, 23.5  # RP2040-Zero 대략 치수(폭x길이)
REAR_SIDE_MARGIN  = 20.0       # 내측 벽 ~ 가장 가까운 부품(TRRS)까지 여유 (부품 놓을 공간)
PART_GAP          = 10.0       # RP2040 보드 ~ TRRS 사이 여유 (체결 간섭 방지)

BED = 220.0         # 프린터 베드 한 변 (풋프린트 검증 기준)

Z_FLOOR = BOTTOM_T          # 바디 내부 바닥 = 하판 상면
def z_top_at(y, y_front):    # 벽체 상단(lip) 높이 — 앞에서 뒤로 6도 상승
    return Z_FLOOR + FRONT_INT_H + (y - y_front) * math.tan(math.radians(TILT_DEG))

TOL = 1e-6

# ─────────────────────────────────────────────────────────────────────────────
# DXF 파싱 → LINE 세그먼트
# ─────────────────────────────────────────────────────────────────────────────
def parse_line_segments(path):
    """DXF ENTITIES 섹션의 LINE 엔티티를 (x1,y1,x2,y2) 리스트로 반환."""
    with open(path) as f:
        toks = [l.rstrip("\n") for l in f]
    pairs = [(toks[i].strip(), toks[i + 1].strip()) for i in range(0, len(toks) - 1, 2)]
    idx = None
    for n in range(len(pairs) - 1):
        if pairs[n] == ("0", "SECTION") and pairs[n + 1] == ("2", "ENTITIES"):
            idx = n + 2
            break
    if idx is None:
        raise RuntimeError("ENTITIES 섹션을 찾지 못함: %s" % path)
    segs, cur, d = [], None, {}
    def flush():
        if cur == "LINE" and all(k in d for k in ("10", "20", "11", "21")):
            segs.append((float(d["10"]), float(d["20"]), float(d["11"]), float(d["21"])))
    n = idx
    while n < len(pairs):
        code, val = pairs[n]
        if code == "0":
            flush()
            if val == "ENDSEC":
                break
            cur, d = val, {}
        elif code in ("10", "20", "11", "21"):
            d[code] = val
        n += 1
    return segs


# ─────────────────────────────────────────────────────────────────────────────
# 자기접촉(figure-8) 폐다각형 → 단순 루프들로 분리
#   sortEdges가 인접 노치 스위치 2개를 하나의 figure-8 와이어로 이어붙이는 경우가 있어
#   (Part.Face가 유효하지 않음), 스택 방식으로 단순 폐곡선들로 분해한다.
# ─────────────────────────────────────────────────────────────────────────────
def ordered_points_of(wire):
    """와이어의 정점을 연결 순서대로 반환."""
    pts = []
    for e in wire.Edges:
        vs = e.Vertexes
        p = (vs[0].X, vs[0].Y)
        if not pts or (abs(pts[-1][0] - p[0]) > 1e-4 or abs(pts[-1][1] - p[1]) > 1e-4):
            pts.append(p)
        pts.append((vs[1].X, vs[1].Y))
    return pts


def split_simple_loops(pts, q=3):
    """닫힌 점열 pts를 단순 폐곡선들로 분리(자기접촉 지점에서 스택 팝)."""
    def key(p):
        return (round(p[0], q), round(p[1], q))
    loops, stack, seen = [], [], {}
    for p in pts:
        k = key(p)
        if k in seen:
            i = seen[k]
            loop = stack[i:]
            if len(loop) >= 3:
                loops.append(loop)
            for qq in stack[i:]:
                seen.pop(key(qq), None)
            stack = stack[:i + 1]  # 접촉점은 남겨 이후 경로가 이어지게
        else:
            seen[k] = len(stack)
            stack.append(p)
    if len(stack) >= 3:
        loops.append(stack)
    return loops


def face_from_loop(loop):
    """단순 점열 → 닫힌 planar Part.Face."""
    vecs = [App.Vector(x, y, 0) for x, y in loop]
    if vecs[0].distanceToPoint(vecs[-1]) > 1e-4:
        vecs.append(vecs[0])
    edges = []
    for a, b in zip(vecs[:-1], vecs[1:]):
        if a.distanceToPoint(b) > TOL:
            edges.append(Part.LineSegment(a, b).toShape())
    return Part.Face(Part.Wire(edges))


# ─────────────────────────────────────────────────────────────────────────────
# DXF → (외곽 face, 컷아웃 face 리스트) — 모두 단순 폐곡선 기반
# ─────────────────────────────────────────────────────────────────────────────
def load_geometry(path):
    segs = parse_line_segments(path)
    edges = [Part.LineSegment(App.Vector(a, b, 0), App.Vector(c, d, 0)).toShape()
             for a, b, c, d in segs
             if App.Vector(a, b, 0).distanceToPoint(App.Vector(c, d, 0)) > TOL]
    wires = [Part.Wire(ch) for ch in Part.sortEdges(edges)]

    # 외곽 = 최대 면적 와이어
    def wire_area(w):
        try:
            return Part.Face(w).Area
        except Exception:
            return w.BoundBox.XLength * w.BoundBox.YLength
    wires.sort(key=wire_area, reverse=True)
    outer_wire, hole_wires = wires[0], wires[1:]

    outer_face = Part.Face(outer_wire)

    # 각 컷아웃을 단순 루프로 분해 → face
    cut_faces = []
    for w in hole_wires:
        try:
            f = Part.Face(w)
            if f.isValid():
                cut_faces.append(f)
                continue
        except Exception:
            pass
        # figure-8 등 → 단순 루프 분리
        for loop in split_simple_loops(ordered_points_of(w)):
            f = face_from_loop(loop)
            if f.isValid() and f.Area > 1.0:
                cut_faces.append(f)
    return outer_face, cut_faces, outer_wire, hole_wires


def plate_face(path):
    """상판 평면 face (외곽 - 전 컷아웃). S1 산출물."""
    outer_face, cut_faces, _, _ = load_geometry(path)
    face = outer_face
    for cf in cut_faces:
        face = face.cut(cf)
    return face, len(cut_faces)


# ─────────────────────────────────────────────────────────────────────────────
# S2: 컷아웃 오프셋 + 상판 솔리드
# ─────────────────────────────────────────────────────────────────────────────
def offset_cut_face(face, dist):
    """컷아웃 face를 바깥으로 dist만큼 확장. makeOffset2D 실패 시 중심 스케일 폴백(ADR-0002)."""
    try:
        off = face.makeOffset2D(dist)
        if off.isValid() and off.Area > face.Area:
            return off
    except Exception:
        pass
    # 폴백: 중심 기준 스케일 (target/원본 비율)
    c = face.CenterOfMass
    factor = SWITCH_CUTOUT_TARGET / DXF_CUTOUT
    m = App.Matrix()
    m.move(App.Vector(-c.x, -c.y, 0))
    s = App.Matrix(); s.scale(factor, factor, 1.0)
    m2 = App.Matrix(); m2.move(App.Vector(c.x, c.y, 0))
    f2 = face.copy()
    f2.transformShape(m2.multiply(s).multiply(m), True)
    return f2


def plate_solid(path):
    """상판 솔리드: (외곽 - 오프셋 컷아웃) 을 PLATE_T로 압출. S2 산출물."""
    outer_face, cut_faces, _, _ = load_geometry(path)
    face = outer_face
    sample_w = None
    for cf in cut_faces:
        ocf = offset_cut_face(cf, CUT_OFFSET)
        # 표본: 정사각 컷아웃 하나의 오프셋 후 개구부 폭
        if sample_w is None and abs(cf.BoundBox.XLength - DXF_CUTOUT) < 0.2 \
                and abs(cf.BoundBox.YLength - DXF_CUTOUT) < 0.2:
            sample_w = ocf.BoundBox.XLength
        face = face.cut(ocf)
    solid = face.extrude(App.Vector(0, 0, PLATE_T))
    return solid, sample_w


def export_stl(shape, path):
    shape.exportStl(path)


def build_s2(doc, export=True):
    for o in list(doc.Objects):
        doc.removeObject(o.Name)
    report = {}
    for side in ("left", "right"):
        solid, sample_w = plate_solid(DXF[side])
        obj = doc.addObject("Part::Feature", "%sPlate" % side.capitalize())
        obj.Shape = solid
        bb = solid.BoundBox
        report[side] = dict(valid=solid.isValid(), thick=round(bb.ZLength, 3),
                            sample=round(sample_w, 3) if sample_w else None,
                            solids=len(solid.Solids))
        if export:
            export_stl(solid, os.path.join(HERE, "%s-plate.stl" % side))
    doc.recompute()
    return report


# ─────────────────────────────────────────────────────────────────────────────
# 실행 진입점 (S1 검증)
# ─────────────────────────────────────────────────────────────────────────────
def build_s1(doc):
    for o in list(doc.Objects):
        doc.removeObject(o.Name)
    report = {}
    xoff = {"left": 0.0, "right": 210.0}
    for side in ("left", "right"):
        face, ncut = plate_face(DXF[side])
        shp = face.copy()
        shp.translate(App.Vector(xoff[side], 0, 0))
        obj = doc.addObject("Part::Feature", "%sPlateFace" % side.capitalize())
        obj.Shape = shp
        bb = face.BoundBox
        report[side] = dict(valid=face.isValid(), ncut=ncut,
                            w=round(bb.XLength, 2), h=round(bb.YLength, 2),
                            area=round(face.Area, 1))
    doc.recompute()
    return report


# ─────────────────────────────────────────────────────────────────────────────
# S3: 케이스 바디 (6° 웨지 벽체 + 상단 lip + 인서트 보스)
# ─────────────────────────────────────────────────────────────────────────────
def boss_centers(bb):
    """인서트 보스 중심 좌표: 좌우 각 4개(코너)만. 벽에 겹치도록 모서리 안쪽으로 최대한 인셋해 스위치 컷아웃을 피함."""
    d = WALL_T + BOSS_OD / 2.0 - BOSS_WALL_OVERLAP
    xs = (bb.XMin + d, bb.XMax - d)
    ys = (bb.YMin + d, bb.YMax - d)
    return [(x, y) for x in xs for y in ys]


def body_solid(path):
    """바디+하판 일체형 tub 솔리드 (바닥 통합 + 상단 인서트 보스 + RP2040 마운트). (body, info) 반환."""
    outer_face, _, _, _ = load_geometry(path)
    bb = outer_face.BoundBox
    y_front = bb.YMin
    tall = 90.0

    # 1) 바닥판(Z 0..BOTTOM_T) + 전높이 벽(Z BOTTOM_T..) — 틸트 전
    floor = outer_face.extrude(App.Vector(0, 0, BOTTOM_T))
    walls_full = outer_face.extrude(App.Vector(0, 0, tall))
    walls_full.translate(App.Vector(0, 0, Z_FLOOR))
    inner_face = outer_face.makeOffset2D(-WALL_T)
    cav = inner_face.extrude(App.Vector(0, 0, tall + 20))
    cav.translate(App.Vector(0, 0, Z_FLOOR))
    walls = walls_full.cut(cav)
    body = floor.fuse(walls)  # tub (바닥 + 벽)

    # 2) 인서트 보스(전높이, 나중에 틸트로 상단 정리) — 벽에 융합
    centers = boss_centers(bb)
    for cx, cy in centers:
        boss = Part.makeCylinder(BOSS_OD / 2.0, tall, App.Vector(cx, cy, Z_FLOOR), App.Vector(0, 0, 1))
        body = body.fuse(boss)

    # 3) RP2040 정렬 포스트 (일체 바닥 위)
    rx, ry = rp2040_center(bb, path)
    for dx in (-RP2040_W / 2, RP2040_W / 2):
        for dy in (-RP2040_L / 2, RP2040_L / 2):
            post = Part.makeCylinder(1.5, 5.0, App.Vector(rx + dx, ry + dy, Z_FLOOR), App.Vector(0, 0, 1))
            body = body.fuse(post)
    body = body.removeSplitter()

    # 4) 틸트 평면으로 상단 절단 (벽·보스 상단이 6° rim이 됨)
    zf = Z_FLOOR + FRONT_INT_H
    cutter = Part.makeBox(bb.XLength + 40, bb.YLength + 80, 140)
    cutter.translate(App.Vector(bb.XMin - 20, y_front - 20, zf))
    cutter.rotate(App.Vector(0, y_front, zf), App.Vector(1, 0, 0), TILT_DEG)
    body = body.cut(cutter)
    body = body.removeSplitter()

    # 5) 인서트 홀(Spredsert M3x5): rim에서 아래로 (상판 나사가 위에서 체결)
    #    보스 상단은 6° 경사면이므로, 수직 커터의 평평한 상단이 경사 rim 최고점
    #    (보스 반경만큼 상승)보다 위에서 시작해야 개구부가 깔끔한 원형으로 뚫린다.
    #    rim 범위 안에서 시작하면 평평한 캡이 경사면을 가로질러 나선형 립이 생긴다.
    rim_clear = BOSS_OD / 2.0 * math.tan(math.radians(TILT_DEG)) + 0.5
    for cx, cy in centers:
        top = z_top_at(cy, y_front)
        hole = Part.makeCylinder(INSERT_HOLE_D / 2.0, INSERT_HOLE_DEPTH + rim_clear,
                                 App.Vector(cx, cy, top + rim_clear), App.Vector(0, 0, -1))
        body = body.cut(hole)

    # 6) 뒷벽 포트 컷아웃(USB-C + TRRS, 좌/우 미러)
    body = cut_rear_ports(body, bb, path)
    body = body.removeSplitter()
    info = dict(nboss=len(centers), zf=zf, zback=z_top_at(bb.YMax, y_front),
                y_front=y_front, bb=bb, centers=centers)
    return body, info


def _is_left(path):
    return "left" in os.path.basename(path)


def rear_cluster(bb, path):
    """뒷벽 부품(RP2040 USB-C, TRRS) x 배치.
    내측 벽에서 REAR_SIDE_MARGIN만큼 안쪽에 TRRS를 두고, RP2040 보드는 PART_GAP만큼 더 안쪽에 분리.
    USB-C는 보드 중심에 정렬. 반환: (usb_x, trrs_x, rp_cx)."""
    if _is_left(path):
        inner_x, sgn = bb.XMax, -1.0
    else:
        inner_x, sgn = bb.XMin, +1.0
    trrs_x = inner_x + sgn * REAR_SIDE_MARGIN
    rp_cx = trrs_x + sgn * (TRRS_D / 2.0 + PART_GAP + RP2040_W / 2.0)
    return rp_cx, trrs_x, rp_cx  # usb_x = rp_cx


def cut_rear_ports(body, bb, path):
    """뒷벽(y_max)에 USB-C·TRRS 컷아웃. 좌/우 미러, 서로 떨어뜨려 배치."""
    yb = bb.YMax
    # 포트 중심 높이: 바닥에서 약간 위 (내부 여유 안)
    zc = Z_FLOOR + 5.0
    x_usb, x_trrs, _ = rear_cluster(bb, path)
    # USB-C: 사각 컷 (뒷벽 관통)
    usb = Part.makeBox(USBC_W, WALL_T + 4, USBC_H,
                       App.Vector(x_usb - USBC_W / 2, yb - WALL_T - 2, zc - USBC_H / 2))
    body = body.cut(usb)
    # TRRS: 원형 컷 (뒷벽 관통, y방향)
    trrs = Part.makeCylinder(TRRS_D / 2.0, WALL_T + 4,
                             App.Vector(x_trrs, yb - WALL_T - 2, zc + 1.0), App.Vector(0, 1, 0))
    body = body.cut(trrs)
    return body


def build_s3(doc, export=True):
    for o in list(doc.Objects):
        doc.removeObject(o.Name)
    report = {}
    for side in ("left", "right"):
        body, info = body_solid(DXF[side])
        obj = doc.addObject("Part::Feature", "%sBody" % side.capitalize())
        obj.Shape = body
        bb = body.BoundBox
        # 최저면 평면성: 최저 Z의 face가 평면인지
        zmin = bb.ZMin
        flat_bottom = any(abs(f.BoundBox.ZMax - zmin) < 1e-3 and abs(f.BoundBox.ZLength) < 1e-3
                          for f in body.Faces)
        report[side] = dict(valid=body.isValid(), solids=len(body.Solids),
                            nboss=info["nboss"], zmin=round(zmin, 2),
                            zback=round(info["zback"], 2), flat_bottom=flat_bottom)
        if export:
            export_stl(body, os.path.join(HERE, "%s-body.stl" % side))
    doc.recompute()
    return report


# ─────────────────────────────────────────────────────────────────────────────
# S4: 하판 + 나사 클리어런스 홀 + RP2040 컨트롤러 마운트
# ─────────────────────────────────────────────────────────────────────────────
def rp2040_center(bb, path):
    """RP2040-Zero 포켓 중심 (뒷벽 인접, USB-C 포트 x와 정렬)."""
    _, _, cx = rear_cluster(bb, path)
    cy = bb.YMax - WALL_T - 2.0 - RP2040_L / 2.0
    return cx, cy


# ─────────────────────────────────────────────────────────────────────────────
# 상판 나사홀 + 접시 카운터싱크 (조립 위치에서 뚫고, 내보내기용은 역-틸트)
# ─────────────────────────────────────────────────────────────────────────────
def cut_plate_screws(assembled_plate, bb, y_front):
    """조립(틸트)된 상판에 수직 M3 관통홀 + 90° 접시 카운터싱크 (바디 인서트와 정렬)."""
    # 상판 윗면도 6° 경사면이므로, 수직 카운터싱크 콘의 평평한 상단이 경사면 최고점
    # (카운터싱크 반경만큼 상승)보다 위에서 시작해야 개구부가 깔끔한 원형으로 뚫린다.
    # 콘을 위로 csk_clear만큼 연장하되 90°(45°) 콘면은 그대로 유지 → 접시 시트는 불변,
    # 평평한 상단만 경사면 위로 떠서 나선형 립이 사라진다.
    csk_clear = CSK_TOP_D / 2.0 * math.tan(math.radians(TILT_DEG)) + 0.5
    for cx, cy in boss_centers(bb):
        top = z_top_at(cy, y_front)          # rim = 상판 밑면 근사 높이
        plate_top = top + PLATE_T            # 상판 윗면 근사
        thru = Part.makeCylinder(SCREW_CLEAR_D / 2.0, PLATE_T + 10,
                                 App.Vector(cx, cy, plate_top + 1), App.Vector(0, 0, -1))
        csk = Part.makeCone(CSK_TOP_D / 2.0 + csk_clear, SCREW_CLEAR_D / 2.0,
                            CSK_DEPTH + csk_clear,
                            App.Vector(cx, cy, plate_top + 0.01 + csk_clear), App.Vector(0, 0, -1))
        assembled_plate = assembled_plate.cut(thru).cut(csk)
    return assembled_plate


def unplace_plate(shape, y_front):
    """조립 배치의 역변환 — 상판을 다시 평평하게(프린트/내보내기용)."""
    zf = Z_FLOOR + FRONT_INT_H
    p = shape.copy()
    p.rotate(App.Vector(0, y_front, zf), App.Vector(1, 0, 0), -TILT_DEG)
    p.translate(App.Vector(0, 0, -zf))
    return p


# ─────────────────────────────────────────────────────────────────────────────
# 조립 · 검증 · STL · FCStd
# ─────────────────────────────────────────────────────────────────────────────
def prestretch_plate_y(plate, y_front):
    """6° 틸트 시 Y가 cos6°만큼 단축돼 바디 수직벽보다 안쪽으로 들어가는 것을 보상.
    틸트 전 평판을 y_front 기준 Y로 1/cos6° 늘리면 틸트 후 투영이 footprint와 일치 → 벽과 밀착.
    (스위치 컷아웃은 판에 수직 유지, 스위치 안착 불변)"""
    k = 1.0 / math.cos(math.radians(TILT_DEG))
    p = plate.copy()
    p.translate(App.Vector(0, -y_front, 0))
    m = App.Matrix(); m.A22 = k              # Y축만 스케일
    p = p.transformGeometry(m)
    p.translate(App.Vector(0, y_front, 0))
    return p


def place_plate_on_rim(plate, y_front):
    """평평한 상판을 6° 틸트시켜 바디 rim(z_top) 위에 안착."""
    zf = Z_FLOOR + FRONT_INT_H
    p = plate.copy()
    p.translate(App.Vector(0, 0, zf))                       # 앞 rim 높이로
    p.rotate(App.Vector(0, y_front, zf), App.Vector(1, 0, 0), TILT_DEG)  # 6° 틸트
    return p


def plate_2d_face(path):
    """상판 2D face (외곽 - 컷아웃) — 나사 위치 재료 검사용."""
    of, cfs, _, _ = load_geometry(path)
    f = of
    for c in cfs:
        f = f.cut(c)
    return f


def screw_positions_ok(path):
    """각 보스 나사 위치가 상판 재료 안(카운터싱크 Ø6 반경까지)인지 검사."""
    f = plate_2d_face(path)
    r = CSK_TOP_D / 2.0
    res = []
    for cx, cy in boss_centers(f.BoundBox):
        pts = [(cx, cy)] + [(cx + r * math.cos(a), cy + r * math.sin(a))
                            for a in [i * math.pi / 4 for i in range(8)]]
        ok = all(f.isInside(App.Vector(px, py, 0), 0.1, True) for px, py in pts)
        res.append((round(cx, 1), round(cy, 1), ok))
    return res


def build_half(side):
    """한 반쪽의 2부품(상판 틸트배치+나사홀, 바디 tub)과 검증값 반환."""
    path = DXF[side]
    outer_face, _, _, _ = load_geometry(path)
    y_front = outer_face.BoundBox.YMin
    bb0 = outer_face.BoundBox
    plate_flat = plate_solid(path)[0]                     # 스위치 컷아웃만
    plate_flat = prestretch_plate_y(plate_flat, y_front)  # 틸트 Y단축 보상 → 벽과 밀착
    body, info = body_solid(path)
    plate_asm = place_plate_on_rim(plate_flat, y_front)   # rim 위 틸트 배치
    plate_asm = cut_plate_screws(plate_asm, bb0, y_front)  # 나사홀 + 카운터싱크
    plate_export = unplace_plate(plate_asm, y_front)       # 내보내기용 평판

    def vol(a, b):
        try:
            return a.common(b).Volume
        except Exception:
            return -1.0
    inter = dict(body_plate=vol(body, plate_asm))
    comp = Part.makeCompound([plate_asm, body])
    bb = comp.BoundBox
    valid = plate_export.isValid() and body.isValid()
    return dict(parts={"plate": plate_export, "body": body, "plate_asm": plate_asm},
                inter=inter, footprint=(round(bb.XLength, 1), round(bb.YLength, 1)),
                valid=valid, zmax=round(bb.ZMax, 2), nboss=info["nboss"],
                body_solids=len(body.Solids), plate_solids=len(plate_export.Solids),
                screws=screw_positions_ok(path))


def build_assembly(doc, export=True, save=True):
    for o in list(doc.Objects):
        doc.removeObject(o.Name)
    xgap = {"left": 0.0, "right": 210.0}
    report = {}
    for side in ("left", "right"):
        h = build_half(side)
        report[side] = {k: h[k] for k in
                        ("inter", "footprint", "valid", "zmax", "nboss",
                         "body_solids", "plate_solids", "screws")}
        # STL 내보내기 (2부품: 상판 평판 + 바디 tub)
        if export:
            export_stl(h["parts"]["plate"], os.path.join(HERE, "%s-plate.stl" % side))
            export_stl(h["parts"]["body"], os.path.join(HERE, "%s-body.stl" % side))
        # 조립 배치(시각화용): 우측 반쪽은 +X 이동
        dx = xgap[side]
        for name, shp in (("Plate", h["parts"]["plate_asm"]),
                          ("Body", h["parts"]["body"])):
            s = shp.copy()
            if dx:
                s.translate(App.Vector(dx, 0, 0))
            obj = doc.addObject("Part::Feature", "%s%s" % (side.capitalize(), name))
            obj.Shape = s
    doc.recompute()
    if save:
        doc.saveAs(os.path.join(HERE, "keyboard.FCStd"))
    return report


if __name__ == "__main__":
    _doc = App.ActiveDocument or App.newDocument("keyboard")
    rep = build_assembly(_doc, export=True, save=True)
    for side, r in rep.items():
        nbad = sum(1 for _, _, ok in r["screws"] if not ok)
        print("[%-5s] valid=%s footprint=%s zmax=%.1f body_solids=%d plate_solids=%d "
              "boss=%d screw_bad=%d body∩plate=%.3f"
              % (side, r["valid"], r["footprint"], r["zmax"], r["body_solids"],
                 r["plate_solids"], r["nboss"], nbad, r["inter"]["body_plate"]))
