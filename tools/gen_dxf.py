#!/usr/bin/env python3
"""좌/우 KLE 분할본에서 스위치 플레이트 DXF 를 생성한다.

배열 원천은 keylayout-left.json / keylayout-right.json 뿐이며, 이 스크립트가 내는
freecad/*-switch.dxf 는 생성물이다 — 손으로 편집하지 않는다.
근거: adr/260821-202939-kle-is-the-only-layout-source-dxf-generated.md

create_keyboard_parametric.py 가 DXF 에서 실제로 쓰는 정보는
  · 스위치 컷아웃의 **중심** (크기는 KeyholeSize 로 덮어써진다)
  · 슬롯의 **중심과 짧은 변** (긴 변은 StabCutoutHeight 로 덮어써진다)
뿐이고, 첫 루프(외곽선)는 loops[1:] 로 버려진다. 그럼에도 원본과 같은 치수를 쓰는
이유는 기준 픽스처 대조(tools/test_gen_dxf.py)가 성립하게 하기 위해서다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dxf
import kle

UNIT = 19.05             # 1u — 0.75인치 표준 키 피치
OFFSET_X = 0.094         # 원본 DXF 의 원점 관례. 형상에는 무관(바운딩박스만 쓰임)
OFFSET_Y = 0.434
SWITCH_SIZE = 14.0       # 원본 DXF 의 스위치 컷아웃 한 변
SLOT_SHORT = 3.3         # 슬롯 짧은 변 — 최종 형상에 그대로 남는다
SLOT_LONG = 14.201       # 슬롯 긴 변 — StabCutoutHeight(14.1) 로 덮어써진다
SLOT_DX = 11.9           # 2u 이상 키 중심에서 좌우 슬롯까지의 X 거리
SLOT_DY = -0.65          # 슬롯 중심은 스위치 중심보다 아래
STAB_MIN_WIDTH = 2.0     # 스테빌라이저를 쓰는 최소 키 폭(u)
PERIMETER_MARGIN = 2.5   # 첫 루프 여유 — 버려지는 값이나 원본 관례를 따른다

ROOT = Path(__file__).resolve().parent.parent


def key_centres(kle_path):
    """KLE 에서 (중심x_u, 중심y_u, 폭_u) 목록과 총 높이(u)를 뽑는다.

    KLE 는 y 가 아래로 증가하고 행 앞의 y 속성은 추가 간격이다. 폭은 직전 속성
    객체의 w 가 그 다음 키 하나에만 적용된다.
    """
    rows = kle.parse(kle_path)
    centres = []
    y = 0.0
    for row in rows:
        if row and isinstance(row[0], dict):
            y += row[0].get("y", 0)
        x, width = 0.0, 1.0
        for item in row:
            if isinstance(item, dict):
                x += item.get("x", 0)
                if "w" in item:
                    width = item["w"]
            else:
                centres.append((x + width / 2.0, y + 0.5, width))
                x += width
                width = 1.0
        y += 1.0
    return centres, y


def rect(cx, cy, w, h):
    """중심과 크기로 닫힌 사각 루프를 만든다 (5점 4선, 마지막 점 = 첫 점)."""
    x0, x1 = cx - w / 2.0, cx + w / 2.0
    y0, y1 = cy - h / 2.0, cy + h / 2.0
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def build_loops(kle_path):
    """스위치 컷아웃과 스테빌라이저 슬롯 루프를 DXF 좌표계로 만든다."""
    centres, total_h = key_centres(kle_path)
    switches, slots = [], []
    for cx_u, cy_u, width_u in centres:
        cx = cx_u * UNIT + OFFSET_X
        cy = (total_h - cy_u) * UNIT + OFFSET_Y      # DXF 는 y 가 위로 증가
        switches.append(rect(cx, cy, SWITCH_SIZE, SWITCH_SIZE))
        if width_u >= STAB_MIN_WIDTH:
            for dx in (-SLOT_DX, SLOT_DX):
                slots.append(rect(cx + dx, cy + SLOT_DY, SLOT_SHORT, SLOT_LONG))
    return switches, slots


def generate(kle_path, out_path):
    """KLE 하나에서 DXF 하나를 쓴다. 첫 루프는 버려지는 외곽선이다."""
    switches, slots = build_loops(kle_path)
    xs = [p[0] for loop in switches for p in loop]
    ys = [p[1] for loop in switches for p in loop]
    m = PERIMETER_MARGIN
    perimeter = [(min(xs) - m, min(ys) - m), (max(xs) + m, min(ys) - m),
                 (max(xs) + m, max(ys) + m), (min(xs) - m, max(ys) + m),
                 (min(xs) - m, min(ys) - m)]
    dxf.write_loops(out_path, [perimeter] + switches + slots)
    return len(switches), len(slots)


if __name__ == "__main__":
    for side in ("left", "right"):
        src = ROOT / f"keylayout-{side}.json"
        dst = ROOT / "freecad" / f"{side}-switch.dxf"
        n_sw, n_sl = generate(src, dst)
        print(f"{dst.name}: 스위치 {n_sw} + 슬롯 {n_sl} = 키 컷아웃 {n_sw + n_sl}개")
