"""PCB 기준 좌우 스위치 상판 파라메트릭 생성.

원천: freecad/left-pcb.dxf, freecad/right-pcb.dxf (전체 레이어 PCB export).
- 스위치 위치: Component-Shape-Layer 의 16mm 스위치 바디 courtyard (스위치당 1개)
- 나사 위치: 보드 외곽 bbox 네 모서리에서 안쪽으로 CORNER_INSET
외곽: 스위치 컷아웃 bbox 를 8mm 확장한 둥근 사각형(코너 R5).
상판: 1.5mm 평판, 접시머리 M3 상면 카운터싱크. 키 사이 중앙 나사홀 없음.

FreeCAD 없이도 추출부는 python3 로 실행되어 검증 리포트를 출력한다:
    python3 create_switch_plate.py --report
FreeCAD(freecadcmd/MCP) 안에서 build_all() 로 모델을 생성한다.
"""

import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 설계 파라미터 --------------------------------------------------------
KEY_PITCH = 19.05           # 1u (참고)
CUTOUT = 14.0               # 스위치 컷아웃 한 변 (목표 개구부)
CUTOUT_OFFSET = 0.0         # FDM 튜닝: 실개구부 = CUTOUT + 2*CUTOUT_OFFSET
OUTLINE_MARGIN = 8.0        # 컷아웃 bbox 에서 바깥으로
CORNER_R = 5.0              # 둥근 사각 코너 반경
PLATE_T = 4.0               # 상판 두께(두껍게 — 소음 저감)
BOARD_T = 2.0               # PCB 보드 두께(시각화용)
BOARD_GAP = 0.0             # 상판 바닥 ~ 보드 윗면 간격. 0 = 상판을 보드에 밀착
BOARD_CORNER_R = 3.0        # PCB 보드 모퉁이 라운드(실제 DXF bulge = R3)
SCREW_CLEAR = 3.4           # M3 normal clearance 관통경
CSK_DIA = 6.2               # 접시머리 카운터싱크 상단 지름 (Dk 6.0 + 0.2)
CSK_ANGLE = 90.0            # 접시머리 각
CORNER_INSET = 3.0          # 나사홀을 보드 bbox 모서리에서 안쪽으로 (좌측 PCB Ø5 홀과 일치)

# ---- body(하단 케이스) 파라미터 (ADR-0003) --------------------------------
BODY_H = 17.0               # body 외부 총 높이
WALL = 3.0                  # 벽 두께
FLOOR = 3.0                 # 바닥 두께
PLATE_GAP = 0.0             # 상판 바닥 ~ PCB 상면 간격. 0 = 상판이 PCB에 밀착
LIP_CLEAR = 0.3             # (미사용) 상판 recess 여유 — 현재 상판은 body 위에 얹힘
PCB_CLEAR = 0.4             # PCB 포켓 여유(반경 방향)
SHELF_W = 2.0               # PCB 선반 폭(내벽에서 안쪽)
POST_OD = 7.0               # 코너 인서트 포스트 지름
INSERT_HOLE_D = 4.0         # Spredsert M3X5 파일럿 홀 지름
INSERT_HOLE_DEPTH = 5.5     # 인서트 홀 깊이(블라인드)
BODY_CORNER_R = 5.0         # body 외곽 코너 반경

# 홀 지름 분류 (mm) — extract 리포트용
D_CORNER = 5.0
D_MID = 3.0
D_TOL = 0.35


# ---- DXF LWPOLYLINE 파서 --------------------------------------------------
def _iter_entities(path):
    with open(path, "r", errors="ignore") as f:
        lines = f.read().split("\n")
    n = len(lines)
    i = 0
    cur = None
    while i + 1 < n:
        code = lines[i].strip()
        val = lines[i + 1]
        if code == "0":
            if cur is not None:
                yield cur
            cur = {"type": val.strip(), "layer": None, "verts": []}
        elif cur is not None:
            if code == "8":
                cur["layer"] = val.strip()
            elif code == "10":
                try:
                    cur["verts"].append([float(val), None])
                except ValueError:
                    pass
            elif code == "20":
                try:
                    if cur["verts"] and cur["verts"][-1][1] is None:
                        cur["verts"][-1][1] = float(val)
                except ValueError:
                    pass
        i += 2
    if cur is not None:
        yield cur


def _circle_of(ent):
    """LWPOLYLINE 이 원이면 (cx, cy, dia) 반환, 아니면 None."""
    vs = [(x, y) for x, y in ent["verts"] if y is not None]
    if len(vs) == 2:
        (x0, y0), (x1, y1) = vs
        dia = math.hypot(x1 - x0, y1 - y0)
        return ((x0 + x1) / 2, (y0 + y1) / 2, dia)
    if len(vs) >= 6:
        xs = [v[0] for v in vs]
        ys = [v[1] for v in vs]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        if w > 0 and h > 0 and abs(w - h) / max(w, h) < 0.2:
            return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (w + h) / 2)
    return None


def _dedup(centers, tol=0.6):
    out = []
    for x, y in centers:
        if not any(abs(x - a) < tol and abs(y - b) < tol for a, b in out):
            out.append((round(x, 3), round(y, 3)))
    return out


def _corner_holes(board, circles):
    """보드 네 모퉁이에 가장 가까운 원홀(하단 body 고정용)을 (cx,cy,dia)로 반환.

    Ø3 스태빌라이저 홀 등 내부 홀은 제외되고, 모퉁이의 고정 홀만 위치로 잡는다.
    좌 PCB는 Ø5, 우 PCB는 Ø3.55 등 지름이 달라도 위치 기준이라 모두 잡힌다.
    """
    if not board:
        return []
    bx = [v[0] for v in board]
    by = [v[1] for v in board]
    out = []
    for cx0 in (min(bx), max(bx)):
        for cy0 in (min(by), max(by)):
            near = [(x, y, d) for x, y, d in circles if math.hypot(x - cx0, y - cy0) < 10]
            if not near:
                continue
            x, y, d = max(near, key=lambda t: t[2])   # 동심원이면 바깥(hole) 지름
            if not any(abs(x - a) < 0.6 and abs(y - b) < 0.6 for a, b, _ in out):
                out.append((round(x, 3), round(y, 3), round(d, 3)))
    return out


def extract(path):
    """PCB DXF 에서 스위치 중심·보드외곽·코너 고정홀을 추출.

    스위치 위치는 Component-Shape-Layer 의 16mm 스위치 바디 courtyard 로 잡는다
    (Multi-Layer Ø4 홀은 절반만 검출되는 문제가 있음).
    코너 고정홀은 보드 모퉁이 근접 위치로 잡는다(Ø3 스태빌라이저 홀은 제외).
    """
    ents = list(_iter_entities(path))
    sw, corner, mid, circles = [], [], [], []
    board = None
    for e in ents:
        lay = e["layer"]
        if lay == "Board-Outline-Layer":
            vs = [(x, y) for x, y in e["verts"] if y is not None]
            if len(vs) >= 3 and (board is None or len(vs) > len(board)):
                board = vs
            continue
        if lay == "Component-Shape-Layer":
            vs = [(x, y) for x, y in e["verts"] if y is not None]
            if len(vs) < 3:
                continue
            xs = [v[0] for v in vs]
            ys = [v[1] for v in vs]
            w = max(xs) - min(xs)
            h = max(ys) - min(ys)
            if 15.0 <= w <= 17.0 and 15.0 <= h <= 17.0:
                sw.append(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2))
            continue
        if lay in ("Multi-Layer", "Hole-Layer"):
            c = _circle_of(e)
            if not c:
                continue
            cx, cy, d = c
            circles.append((cx, cy, d))
            if lay == "Multi-Layer":
                if abs(d - D_CORNER) < D_TOL:
                    corner.append((cx, cy))
                elif abs(d - D_MID) < D_TOL:
                    mid.append((cx, cy))
    return {
        "switch": _dedup(sw, tol=2.0),
        "corner": _dedup(corner),
        "mid": _dedup(mid),                       # Ø3 스태빌라이저 홀(참고용)
        "corner_holes": _corner_holes(board, circles),  # 하단 body 고정용 코너 홀
        "board": board,
    }


# ---- switch_hole DXF (스테빌라이저 슬롯) ----------------------------------
def _iter_lines(path):
    """switch_hole DXF 의 LINE 세그먼트 [((x1,y1),(x2,y2)), ...] 반환."""
    with open(path, "r", errors="ignore") as f:
        L = f.read().split("\n")
    segs = []
    ent = None
    cur = {}
    n = len(L)
    i = 0
    keymap = {"10": "x1", "20": "y1", "11": "x2", "21": "y2"}
    while i + 1 < n:
        code = L[i].strip()
        val = L[i + 1].strip()
        if code == "0":
            if ent == "LINE" and len(cur) == 4:
                segs.append(((cur["x1"], cur["y1"]), (cur["x2"], cur["y2"])))
            ent = val
            cur = {}
        elif ent == "LINE" and code in keymap:
            try:
                cur[keymap[code]] = float(val)
            except ValueError:
                pass
        i += 2
    if ent == "LINE" and len(cur) == 4:
        segs.append(((cur["x1"], cur["y1"]), (cur["x2"], cur["y2"])))
    return segs


def _loops(segs, tol=1e-3):
    """연결된 세그먼트를 닫힌 루프로 묶는다(각 사각형/외곽 = 한 루프)."""
    if not segs:
        return []
    out = []
    cur = [segs[0]]
    for s in segs[1:]:
        pe = cur[-1][1]
        if abs(s[0][0] - pe[0]) < tol and abs(s[0][1] - pe[1]) < tol:
            cur.append(s)
        else:
            out.append(cur)
            cur = [s]
    out.append(cur)
    return out


def stab_slots(name, centers):
    """switch_hole DXF 의 스테빌라이저 슬롯을 PCB/plate 좌표계로 정렬해 반환.

    반환: [(x0, y0, x1, y1), ...] 축 정렬 사각형.
    정렬: switch_hole 의 14mm 키홀 중심 집합을 plate 스위치 중심(centers)에
    centroid 로 맞춰 순수 평행이동한다(회전/스케일 없음, 잔차 <0.1mm 확인됨).
    """
    path = os.path.join(HERE, "%s_switch_hole.dxf" % name)
    keys, stabs = [], []
    for lp in _loops(_iter_lines(path)):
        xs = [p[0] for s in lp for p in s]
        ys = [p[1] for s in lp for p in s]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        w, h = x1 - x0, y1 - y0
        if 12 <= w <= 16 and 12 <= h <= 16:
            keys.append(((x0 + x1) / 2, (y0 + y1) / 2))
        elif (w < 6 and h <= 20) or (h < 6 and w <= 20):
            stabs.append((x0, y0, x1, y1))
    if not keys or not stabs or not centers:
        return []
    kx = sum(k[0] for k in keys) / len(keys)
    ky = sum(k[1] for k in keys) / len(keys)
    sx = sum(c[0] for c in centers) / len(centers)
    sy = sum(c[1] for c in centers) / len(centers)
    ox, oy = sx - kx, sy - ky
    return [(x0 + ox, y0 + oy, x1 + ox, y1 + oy) for x0, y0, x1, y1 in stabs]


# ---- FreeCAD 지오메트리 빌드 (FreeCAD 안에서만 동작) ---------------------
def _square_face(cx, cy, size):
    import FreeCAD as App
    import Part
    h = size / 2.0
    pts = [App.Vector(cx - h, cy - h, 0), App.Vector(cx + h, cy - h, 0),
           App.Vector(cx + h, cy + h, 0), App.Vector(cx - h, cy + h, 0),
           App.Vector(cx - h, cy - h, 0)]
    return Part.Face(Part.makePolygon(pts))


def _rounded_rect(x0, y0, x1, y1, r, t):
    """모서리 R 인 둥근 사각 프리즘 솔리드."""
    import FreeCAD as App
    import Part
    box = Part.makeBox(x1 - x0, y1 - y0, t, App.Vector(x0, y0, 0))
    vedges = [e for e in box.Edges
              if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6]
    return box.makeFillet(r, vedges)


def build_plate(name, centers, board):
    """한쪽 상판 솔리드를 만들어 (solid, info) 반환."""
    import FreeCAD as App
    import Part

    # 1) 외곽 = body 외곽과 동일(단차 없음): PCB bbox ± (PCB_CLEAR + WALL), R = BODY_CORNER_R
    bxs = [v[0] for v in board]
    bys = [v[1] for v in board]
    x0, x1 = min(bxs) - PCB_CLEAR - WALL, max(bxs) + PCB_CLEAR + WALL
    y0, y1 = min(bys) - PCB_CLEAR - WALL, max(bys) + PCB_CLEAR + WALL
    solid = _rounded_rect(x0, y0, x1, y1, BODY_CORNER_R, PLATE_T)

    # 2) 스위치 컷아웃 (14 + 2*offset)
    cut = CUTOUT + 2 * CUTOUT_OFFSET
    tools = []
    for cx, cy in centers:
        t = _square_face(cx, cy, cut).extrude(App.Vector(0, 0, PLATE_T + 2))
        t.translate(App.Vector(0, 0, -1))
        tools.append(t)
    solid = solid.cut(tools[0].multiFuse(tools[1:]) if len(tools) > 1 else tools[0])

    # 2b) 스테빌라이저 슬롯 (switch_hole DXF, PCB 좌표 정렬 후 관통 컷)
    slots = stab_slots(name, centers)
    if slots:
        stools = []
        for x0, y0, x1, y1 in slots:
            stools.append(Part.makeBox(x1 - x0, y1 - y0, PLATE_T + 2,
                                       App.Vector(x0, y0, -1)))
        solid = solid.cut(stools[0].multiFuse(stools[1:]) if len(stools) > 1 else stools[0])

    # 3) 나사홀(코너 4개) + 상면 카운터싱크 — 보드 bbox 모서리에서 CORNER_INSET
    bx = [v[0] for v in board]
    by = [v[1] for v in board]
    bx0, bx1 = min(bx) + CORNER_INSET, max(bx) - CORNER_INSET
    by0, by1 = min(by) + CORNER_INSET, max(by) - CORNER_INSET
    screws = [(bx0, by0), (bx1, by0), (bx0, by1), (bx1, by1)]
    csk_depth = (CSK_DIA - SCREW_CLEAR) / 2.0 / math.tan(math.radians(CSK_ANGLE / 2.0))
    st = []
    for cx, cy in screws:
        st.append(Part.makeCylinder(SCREW_CLEAR / 2.0, PLATE_T + 2,
                                    App.Vector(cx, cy, -1)))
        st.append(Part.makeCone(SCREW_CLEAR / 2.0, CSK_DIA / 2.0, csk_depth,
                                App.Vector(cx, cy, PLATE_T - csk_depth)))
        st.append(Part.makeCylinder(CSK_DIA / 2.0, 0.6, App.Vector(cx, cy, PLATE_T - 0.01)))
    solid = solid.cut(st[0].multiFuse(st[1:]))

    bb = solid.BoundBox
    info = dict(name=name, switches=len(centers), stabs=len(slots), screws=len(screws),
                csk_depth=round(csk_depth, 2), valid=solid.isValid(),
                solids=len(solid.Solids),
                bbox=(round(bb.XLength, 1), round(bb.YLength, 1), round(bb.ZLength, 2)),
                screw_pos=[(round(a, 1), round(b, 1)) for a, b in screws])
    return solid, info


def build_board(r):
    """Board-Outline 폴리곤을 BOARD_T 두께로, 상판 아래로 내려 배치한 PCB 솔리드.

    하단 body 고정용 코너 홀만 관통으로 뚫는다(Ø3 스태빌라이저 홀은 제외).
    """
    import FreeCAD as App
    import Part
    z_bottom = -(BOARD_GAP + BOARD_T)
    # 실제 보드는 R3 둥근 사각형(DXF bulge). bbox + R3 로 재현.
    bx = [v[0] for v in r["board"]]
    by = [v[1] for v in r["board"]]
    solid = _rounded_rect(min(bx), min(by), max(bx), max(by), BOARD_CORNER_R, BOARD_T)
    solid.translate(App.Vector(0, 0, z_bottom))

    # 코너 고정홀만 관통
    holes = r["corner_holes"]
    tools = [Part.makeCylinder(d / 2.0, BOARD_T + 2, App.Vector(cx, cy, z_bottom - 1))
             for cx, cy, d in holes]
    if tools:
        solid = solid.cut(tools[0].multiFuse(tools[1:]) if len(tools) > 1 else tools[0])
    return solid, holes


def build_body(name, r):
    """하단 케이스(body) 솔리드를 만들어 (solid, info) 반환.

    외곽 = PCB 외곽 기준(ADR-0003), 외부높이 BODY_H, 벽/바닥 WALL/FLOOR.
    상단 lip 단턱(상판 recess) + 둘레 PCB 선반 + 4 코너 인서트 포스트.
    좌표: 바닥 밑면 z=0.
    """
    import FreeCAD as App
    import Part

    # PCB 외곽 bbox
    b = r["board"]
    bx0, bx1 = min(v[0] for v in b), max(v[0] for v in b)
    by0, by1 = min(v[1] for v in b), max(v[1] for v in b)

    # 파생 Z (상판이 body 위에 얹힘 — 리세스 없음. PCB 는 최상단 선반에 안착)
    floor_top = FLOOR                       # 3
    pcb_top = BODY_H                        # 17 (PCB 상면 = body 상단 rim = 상판 바닥)
    shelf_top = pcb_top - BOARD_T           # 15 (PCB 바닥 = 선반/포스트 top)

    # 개구 경계
    cav_x0, cav_x1 = bx0 - PCB_CLEAR, bx1 + PCB_CLEAR       # 캐비티 내벽(PCB+여유)
    cav_y0, cav_y1 = by0 - PCB_CLEAR, by1 + PCB_CLEAR
    out_x0, out_x1 = cav_x0 - WALL, cav_x1 + WALL           # 외벽 외곽
    out_y0, out_y1 = cav_y0 - WALL, cav_y1 + WALL
    sh_x0, sh_x1 = cav_x0 + SHELF_W, cav_x1 - SHELF_W       # 선반 내측(하부 캐비티)
    sh_y0, sh_y1 = cav_y0 + SHELF_W, cav_y1 - SHELF_W

    cav_r = max(BODY_CORNER_R - WALL, 0.5)
    OV = 2.0

    # 1) 외곽 솔리드
    solid = _rounded_rect(out_x0, out_y0, out_x1, out_y1, BODY_CORNER_R, BODY_H)

    # 2) 계단형 캐비티 (하부→상부, 상부가 넓어 z=shelf_top 선반 생성). 리세스 없음(상판이 위에 얹힘)
    lo = _rounded_rect(sh_x0, sh_y0, sh_x1, sh_y1, max(cav_r - SHELF_W, 0.5), BODY_H - floor_top + OV)
    lo.translate(App.Vector(0, 0, floor_top))
    up = _rounded_rect(cav_x0, cav_y0, cav_x1, cav_y1, cav_r, BODY_H - shelf_top + OV)
    up.translate(App.Vector(0, 0, shelf_top))
    solid = solid.cut(lo.fuse(up))

    # 3) 코너 인서트 포스트(바닥 top → 선반 top) + 인서트 홀(블라인드)
    holes = r["corner_holes"]
    posts = [Part.makeCylinder(POST_OD / 2.0, shelf_top - floor_top, App.Vector(cx, cy, floor_top))
             for cx, cy, _ in holes]
    if posts:
        solid = solid.fuse(posts[0].multiFuse(posts[1:]) if len(posts) > 1 else posts[0])
        tools = [Part.makeCylinder(INSERT_HOLE_D / 2.0, INSERT_HOLE_DEPTH,
                                   App.Vector(cx, cy, shelf_top - INSERT_HOLE_DEPTH))
                 for cx, cy, _ in holes]
        solid = solid.cut(tools[0].multiFuse(tools[1:]) if len(tools) > 1 else tools[0])

    bb = solid.BoundBox
    info = dict(name=name + "_body", body_h=round(bb.ZLength, 2), wall=WALL, floor=FLOOR,
                posts=len(holes), insert_d=INSERT_HOLE_D, insert_depth=INSERT_HOLE_DEPTH,
                shelf_top=shelf_top, plate_seat=pcb_top,
                valid=solid.isValid(), solids=len(solid.Solids),
                bbox=(round(bb.XLength, 1), round(bb.YLength, 1), round(bb.ZLength, 2)),
                post_pos=[(round(cx, 1), round(cy, 1)) for cx, cy, _ in holes])
    return solid, info


def build_all(export=True):
    """FreeCAD 문서에 좌·우 상판 + 그 아래 PCB 보드를 생성하고 (원하면) STL/STEP export."""
    import FreeCAD as App

    doc = App.ActiveDocument or App.newDocument("switch_plates")
    infos = []
    for name in ("left", "right"):
        path = os.path.join(HERE, "%s-pcb.dxf" % name)
        r = extract(path)
        x_off = 230 if name == "right" else 0

        # 상판
        solid, info = build_plate(name, r["switch"], r["board"])
        plate = doc.addObject("Part::Feature", "%s_switch_plate" % name)
        plate.Shape = solid
        # PCB 보드
        board = doc.addObject("Part::Feature", "%s_pcb_board" % name)
        board_solid, corner_holes = build_board(r)
        board.Shape = board_solid
        info["corner_fix_holes"] = [(x, y, d) for x, y, d in corner_holes]
        # 하단 body
        body = doc.addObject("Part::Feature", "%s_body" % name)
        body_solid, binfo = build_body(name, r)
        body.Shape = body_solid

        # 조립 배치 (body 좌표: 바닥 밑면 z=0). body[0,17] · PCB[15,17] · 상판[17,21](위에 얹힘)
        pcb_top = BODY_H                          # 17 (PCB 상면 = body 상단)
        plate_bottom = pcb_top                    # 17 (상판이 PCB 위에 맞닿아 얹힘)
        body.Placement.Base = App.Vector(x_off, 0, 0)
        board.Placement.Base = App.Vector(x_off, 0, pcb_top - board_solid.BoundBox.ZMax)
        plate.Placement.Base = App.Vector(x_off, 0, plate_bottom)

        infos.append(binfo)
        infos.append(info)
        if export:
            solid.exportStl(os.path.join(HERE, "%s_switch_plate.stl" % name))
            solid.exportStep(os.path.join(HERE, "%s_switch_plate.step" % name))
            body_solid.exportStl(os.path.join(HERE, "%s_body.stl" % name))
            body_solid.exportStep(os.path.join(HERE, "%s_body.step" % name))
    doc.recompute()
    doc.saveAs(os.path.join(HERE, "switch_plates.FCStd"))
    for i in infos:
        print(i)
    return infos


def report():
    for name in ("left", "right"):
        path = os.path.join(HERE, "%s-pcb.dxf" % name)
        r = extract(path)
        b = r["board"]
        bx = [v[0] for v in b]
        by = [v[1] for v in b]
        print("===== %s-pcb.dxf =====" % name)
        print("  switch(16mm body): %d" % len(r["switch"]))
        print("  board bbox: %.1f x %.1f" % (max(bx) - min(bx), max(by) - min(by)))
        print("  corner screws: %s" % [
            (round(min(bx) + CORNER_INSET, 1), round(min(by) + CORNER_INSET, 1)),
            (round(max(bx) - CORNER_INSET, 1), round(min(by) + CORNER_INSET, 1)),
            (round(min(bx) + CORNER_INSET, 1), round(max(by) - CORNER_INSET, 1)),
            (round(max(bx) - CORNER_INSET, 1), round(max(by) - CORNER_INSET, 1))])


if __name__ == "__main__":
    import sys
    if "--report" in sys.argv or len(sys.argv) == 1:
        report()
