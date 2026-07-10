# -*- coding: utf-8 -*-
"""
분할 키보드 스위치 플레이트(단독 상판) 3D 프린팅용 파라메트릭 생성 스크립트.

입력  : freecad/left-switch.dxf, freecad/right-switch.dxf
        - 각 DXF는 LINE 세그먼트로 구성됨(레이어 0). 가장 큰 폐곡선 하나가 외곽
          테두리이고(사용하지 않음), 나머지 폐곡선이 스위치 컷아웃이다.
        - 모든 폐곡선은 단순(자기교차 없음, maxdeg=2)임을 실측 확인. 인접 컷아웃이
          하나의 단순 루프로 이어진 병합형(예: 32.1x14.65)도 그대로 잘라낸다.
출력  : 좌/우 각 스위치 플레이트 → freecad/{left,right}-plate.FCStd + .stl

용도  : 케이스 없이 단독 출력하는 평판형 스위치 플레이트. 나사 보스/하단 케이스는 범위 밖.
실행  : freecadcmd make_plate.py  (헤드리스)  또는 FreeCAD MCP execute_code 로 본문 실행.
"""

import os
import FreeCAD as App
import Part
from FreeCAD import Vector

# ─────────────────────────────────────────────────────────────────────────────
# 파라미터 (값만 바꿔 재실행하면 재생성됨)
# ─────────────────────────────────────────────────────────────────────────────
PLATE_THICKNESS = 4.0    # 플레이트 두께 (mm)
CORNER_RADIUS   = 5.0    # 외곽 4개 모서리 필릿 반경 (mm)
EDGE_MARGIN     = 7.5    # 스위치 컷아웃 bbox 가장자리 ~ 외곽 거리 (mm)
CUTOUT_OFFSET   = 0.0    # 스위치 컷아웃 크기 보정 (mm; +면 구멍이 커짐, 프린터 오차 보정용)

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
    else "/Users/gyuha/workspace/my-keyboard/freecad"
SIDES = {"left": "left-switch.dxf", "right": "right-switch.dxf"}

TOL = 1e-6
Q = 3   # 좌표 일치 판정용 반올림 자리수


# ─────────────────────────────────────────────────────────────────────────────
# DXF ENTITIES 섹션의 LINE 세그먼트 파싱 → (x1,y1,x2,y2) 리스트
# ─────────────────────────────────────────────────────────────────────────────
def parse_line_segments(path):
    toks = [l.rstrip("\n") for l in open(path)]
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
# 세그먼트 → 순서 있는 폐곡선(폴리라인)들로 그룹화
#   모든 정점 차수가 2이므로(자기교차 없음) 각 루프를 결정적으로 추적할 수 있다.
# ─────────────────────────────────────────────────────────────────────────────
def rk(x, y):
    return (round(x, Q), round(y, Q))


def loops_from_segments(segs):
    from collections import defaultdict
    coord, adj = {}, defaultdict(list)
    for i, (x1, y1, x2, y2) in enumerate(segs):
        a, b = rk(x1, y1), rk(x2, y2)
        coord[a], coord[b] = (x1, y1), (x2, y2)
        adj[a].append((b, i))
        adj[b].append((a, i))
    used = [False] * len(segs)
    loops = []
    for s0 in range(len(segs)):
        if used[s0]:
            continue
        x1, y1, x2, y2 = segs[s0]
        used[s0] = True
        a, b = rk(x1, y1), rk(x2, y2)
        poly = [coord[a], coord[b]]
        cur = b
        while cur != a:
            step = None
            for (v, si) in adj[cur]:
                if not used[si]:
                    step = (v, si)
                    break
            if step is None:
                break            # 열린 체인(비정상) — 그대로 남겨둠
            used[step[1]] = True
            cur = step[0]
            poly.append(coord[cur])
        loops.append(poly)
    return loops


def bbox(polys):
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def area_of(poly):
    x0, y0, x1, y1 = bbox([poly])
    return (x1 - x0) * (y1 - y0)


# ─────────────────────────────────────────────────────────────────────────────
# 폴리라인 → FreeCAD 폐 와이어
# ─────────────────────────────────────────────────────────────────────────────
def wire_from_poly(poly, z):
    pts = [Vector(x, y, z) for (x, y) in poly]
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    return Part.makePolygon(pts)


def build_plate(side, dxf_name):
    segs = parse_line_segments(os.path.join(HERE, dxf_name))
    loops = loops_from_segments(segs)

    # 가장 넓은 bbox 폐곡선 = 외곽 테두리 → 제외
    border_i = max(range(len(loops)), key=lambda i: area_of(loops[i]))
    cutouts = [poly for i, poly in enumerate(loops) if i != border_i]

    # 스위치 컷아웃 전체 bbox + 여유 → 외곽 사각형
    x0, y0, x1, y1 = bbox(cutouts)
    X0, Y0 = x0 - EDGE_MARGIN, y0 - EDGE_MARGIN
    X1, Y1 = x1 + EDGE_MARGIN, y1 + EDGE_MARGIN

    outer = Part.makePolygon([
        Vector(X0, Y0, 0), Vector(X1, Y0, 0),
        Vector(X1, Y1, 0), Vector(X0, Y1, 0), Vector(X0, Y0, 0)])
    box = Part.Face(outer).extrude(Vector(0, 0, PLATE_THICKNESS))

    # 수직(Z방향) 4개 모서리 에지만 골라 필릿
    if CORNER_RADIUS > TOL:
        verticals = [e for e in box.Edges
                     if abs(e.Vertexes[0].X - e.Vertexes[1].X) < TOL
                     and abs(e.Vertexes[0].Y - e.Vertexes[1].Y) < TOL]
        box = box.makeFillet(CORNER_RADIUS, verticals)

    # 컷아웃 → 관통 프리즘 (플레이트 상하로 여유롭게 관통)
    prisms = []
    for poly in cutouts:
        w = wire_from_poly(poly, -1.0)
        if abs(CUTOUT_OFFSET) > TOL:
            try:
                w = w.makeOffset2D(CUTOUT_OFFSET)
            except Exception as ex:
                App.Console.PrintWarning("offset 실패(원형 유지): %s\n" % ex)
        prisms.append(Part.Face(w).extrude(Vector(0, 0, PLATE_THICKNESS + 2.0)))

    tool = prisms[0] if len(prisms) == 1 else prisms[0].multiFuse(prisms[1:])
    plate = box.cut(tool)

    # 측정/검증 출력
    bb = plate.BoundBox
    print("[%s] loops=%d  border(bbox area max) 제외 → cutouts=%d"
          % (side, len(loops), len(cutouts)))
    print("[%s] 외곽 %.2f x %.2f mm, 두께(Z) %.3f mm, solids=%d, valid=%s"
          % (side, bb.XLength, bb.YLength, bb.ZLength, len(plate.Solids), plate.isValid()))
    return plate


SIDE_GAP = 20.0   # 통합 FCStd에서 좌/우 플레이트 사이 간격 (mm)


def main():
    # 좌/우 각각 형상 생성 + STL 저장(각자 DXF 원점 위치 — 프린트 시 개별 출력)
    shapes = {}
    for side, dxf_name in SIDES.items():
        plate = build_plate(side, dxf_name)
        shapes[side] = plate
        stl = os.path.join(HERE, "%s-plate.stl" % side)
        plate.exportStl(stl)
        print("[%s] STL 저장: %s" % (side, os.path.basename(stl)))

    # 두 플레이트를 하나의 FCStd에 나란히 배치 — 한 화면에서 함께 확인
    doc = App.newDocument("keyboard-plate")
    x_cursor = 0.0
    for side in ("left", "right"):
        plate = shapes[side]
        placed = plate.copy()
        placed.translate(Vector(x_cursor, 0.0, 0.0))
        feat = doc.addObject("Part::Feature", "%sPlate" % side.capitalize())
        feat.Shape = placed
        x_cursor += plate.BoundBox.XLength + SIDE_GAP
    doc.recompute()
    fcstd = os.path.join(HERE, "keyboard-plate.FCStd")
    doc.saveAs(fcstd)
    print("통합 문서 저장: %s (LeftPlate + RightPlate)" % os.path.basename(fcstd))
    App.closeDocument(doc.Name)


main()
