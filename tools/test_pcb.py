#!/usr/bin/env python3
"""pcb.py 검사 — epro 에서 읽은 값이 실측치와 맞는가.

기대값은 전부 `pcb/split-keyboard.epro` 를 손으로 파싱해 확인한 실측치다. 파서가
"자기가 읽은 것과 자기가 계산한 것"만 대조하면 규칙이 틀렸는지는 못 잡으므로,
바깥에서 재 온 숫자를 박아 둔다. test_gen_dxf.py 와 같은 이유의 픽스처다.
근거: adr/260824-001947-epro-is-the-source-of-pcb-geometry.md

실행: python3 tools/test_pcb.py   (통과 시 exit 0)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pcb                          # S1 에서 구현된다 — 없으면 여기서 실패한다

TOL = 0.01

failures = []


def check(label, ok, detail=""):
    if not ok:
        failures.append(f"{label}{': ' + detail if detail else ''}")


def near(a, b, tol=TOL):
    return abs(a - b) <= tol


project = pcb.load()

# ---- S1. 보드 4장을 이름으로 식별한다 -----------------------------------------
# project.json 의 이름과 컴포넌트 수는 바깥에서 센 값이다.
check("보드 수", len(project.boards) == 4, str(len(project.boards)))
for name, count in (("PCB2_1", 63), ("PCB13", 90), ("PCB8_1", 3), ("PCB8_2", 3)):
    board = project.boards.get(name)
    check(f"{name} 존재", board is not None)
    if board is not None:
        check(f"{name} 컴포넌트 수", len(board.components) == count,
              f"{len(board.components)} (기대 {count})")

# 의미 기반 접근자 — 이름이 아니라 디자이너 접두어(LEFT*/RIGHT*)로 판정한다.
for side in ("left", "right"):
    check(f"main({side})", project.main(side) is not None)
    check(f"aux({side})", project.aux(side) is not None)
check("main/aux 구분", project.main("left") is not project.aux("left"))

# ---- S2. 외곽과 마운팅 홀 -----------------------------------------------------
# 실측: 좌 146.21 x 103.35, 우 198.60 x 103.35, 코너 R3.0
for side, w, h in (("left", 146.21, 103.35), ("right", 198.60, 103.35)):
    o = project.main(side).outline
    check(f"{side} 외곽 폭", near(o.width, w), f"{o.width:.2f} (기대 {w})")
    check(f"{side} 외곽 깊이", near(o.height, h), f"{o.height:.2f} (기대 {h})")
    check(f"{side} 코너 R", near(o.radius, 3.0), f"{o.radius:.2f}")
    # y 는 위로 증가한다 — 최상단 행(ROW0)이 y_max 쪽에 있어야 한다.
    check(f"{side} y 방향", o.y_max > o.y_min)

# aux 보드는 40 x 55
for side in ("left", "right"):
    o = project.aux(side).outline
    check(f"{side} aux 폭", near(o.width, 40.0), f"{o.width:.2f}")
    check(f"{side} aux 깊이", near(o.height, 55.0), f"{o.height:.2f}")

# 마운팅 홀 — 양쪽 메인 PCB 에 ⌀3.55 가 4개, 가장자리에서 약 3mm 안쪽.
# .worktree/pcb 의 스펙 문서는 "좌 1개, 우 없음"이라고 적었고 그것이 틀렸다.
for side in ("left", "right"):
    board = project.main(side)
    holes = board.mounting_holes
    check(f"{side} 마운팅 홀 수", len(holes) == 4, str(len(holes)))
    for i, hole in enumerate(holes):
        check(f"{side} 홀{i} 지름", near(hole.diameter, 3.55), f"{hole.diameter:.2f}")
        o = board.outline
        inset_x = min(hole.x - o.x_min, o.x_max - hole.x)
        inset_y = min(hole.y - o.y_min, o.y_max - hole.y)
        check(f"{side} 홀{i} 인셋", near(inset_x, 3.0, 0.1) and near(inset_y, 3.0, 0.1),
              f"x {inset_x:.2f} / y {inset_y:.2f}")

# ---- S3. 핀맵 -----------------------------------------------------------------
# RP2040-Zero 심볼 핀번호 -> GPIO, aux 보드 PAD_NET 과 조인한 결과.
for side in ("left", "right"):
    pins = project.pin_map(side)
    for i in range(5):
        check(f"{side} ROW{i}", pins.get(f"ROW{i}") == f"GP{i + 2}", str(pins.get(f"ROW{i}")))
    check(f"{side} TX0", pins.get("TX0") == "GP0", str(pins.get("TX0")))
    check(f"{side} RX0", pins.get("RX0") == "GP1", str(pins.get("RX0")))
    check(f"{side} 3V3", pins.get("3V3") == "3V3", str(pins.get("3V3")))
    check(f"{side} GND", pins.get("GND") == "GND", str(pins.get("GND")))

# 좌측은 COL0~6(7열)까지만 배선돼 있고, 우측은 COL0~8(9열)이다.
left_pins, right_pins = project.pin_map("left"), project.pin_map("right")
for i in range(7):
    check(f"left COL{i}", left_pins.get(f"COL{i}") == f"GP{i + 7}", str(left_pins.get(f"COL{i}")))
check("left COL7 미배선", "COL7" not in left_pins, str(left_pins.get("COL7")))
check("left COL8 미배선", "COL8" not in left_pins, str(left_pins.get("COL8")))
for i in range(9):
    check(f"right COL{i}", right_pins.get(f"COL{i}") == f"GP{i + 7}", str(right_pins.get(f"COL{i}")))

# ---- S4. 매트릭스 -------------------------------------------------------------
# 실측: 좌 30키 [7,6,6,6,5], 우 43키 [9,9,8,9,8]  (row0 -> row4)
EXPECT_ROWS = {"left": [7, 6, 6, 6, 5], "right": [9, 9, 8, 9, 8]}
for side, expect in EXPECT_ROWS.items():
    keys = project.matrix(side)
    check(f"{side} 키 수", len(keys) == sum(expect), f"{len(keys)} (기대 {sum(expect)})")
    per_row = [sum(1 for k in keys if k.row == r) for r in range(5)]
    check(f"{side} 행별 키 수", per_row == expect, f"{per_row} (기대 {expect})")
    # 같은 (row, col) 이 두 번 나오면 배선을 잘못 읽은 것이다.
    coords = [(k.row, k.col) for k in keys]
    check(f"{side} (row,col) 중복 없음", len(set(coords)) == len(coords))
    # row0 이 최상단이어야 한다 — 물리 y 가 row 번호와 역순.
    ys = [max(k.y for k in keys if k.row == r) for r in range(5)]
    check(f"{side} row0 이 최상단", ys == sorted(ys, reverse=True), str([round(v, 1) for v in ys]))

# 우측의 빈 자리는 row2 의 COL7, row4 의 COL2 뿐이다 — 이것이 gkey.h 가 어긋난 지점이다.
right_gaps = sorted(
    (r, c) for r in range(5) for c in range(9)
    if not any(k.row == r and k.col == c for k in project.matrix("right"))
)
check("우측 빈 자리", right_gaps == [(2, 7), (4, 2)], str(right_gaps))

# 좌측은 COL6 을 쓰는 행이 row0 하나뿐이다(ESC~6 의 7키 행).
left_gaps = sorted(
    (r, c) for r in range(5) for c in range(7)
    if not any(k.row == r and k.col == c for k in project.matrix("left"))
)
check("좌측 빈 자리", left_gaps == [(1, 6), (2, 6), (3, 6), (4, 5), (4, 6)], str(left_gaps))

# 실크 라벨 표본 — 배선을 키와 맞게 읽었는지 사람이 읽을 수 있는 형태로 확인한다.
left_by_rc = {(k.row, k.col): k.label for k in project.matrix("left")}
check("좌 (0,0) = ESC", left_by_rc.get((0, 0)) == "ESC", str(left_by_rc.get((0, 0))))
check("좌 (0,6) = 6", left_by_rc.get((0, 6)) == "6", str(left_by_rc.get((0, 6))))
check("좌 (4,0) = CTRL", left_by_rc.get((4, 0)) == "CTRL", str(left_by_rc.get((4, 0))))
right_by_rc = {(k.row, k.col): k.label for k in project.matrix("right")}
check("우 (0,0) = 6", right_by_rc.get((0, 0)) == "6", str(right_by_rc.get((0, 0))))
check("우 (0,8) = Home", right_by_rc.get((0, 8)) == "Home", str(right_by_rc.get((0, 8))))
check("우 (4,0) = R.ALT", right_by_rc.get((4, 0)) == "R.ALT", str(right_by_rc.get((4, 0))))

# 스위치는 납땜(스루홀 2핀)이고 핫스왑이 아니다 — 플레이트에 클립 릴리프가 필요없는 근거.
for side in ("left", "right"):
    check(f"{side} 스위치 납땜", project.main(side).switches_are_soldered)

# 다이오드는 전량 하면 — PCB 아래 간섭 계산의 근거.
for side, n in (("left", 30), ("right", 43)):
    diodes = project.main(side).diodes
    check(f"{side} 다이오드 수", len(diodes) == n, f"{len(diodes)} (기대 {n})")
    check(f"{side} 다이오드 하면", all(d.layer == "bottom" for d in diodes))

# ---- S6. aux 보드 배치 --------------------------------------------------------
# 16핀 헤더의 mate 로 aux 보드를 메인 PCB 좌표계에 놓는다. 메인 쪽 헤더는 하면
# (layer 2)이라 풋프린트가 미러되며, 그 결과 두 보드는 순수 평행이동으로 맞물린다.
for side in ("left", "right"):
    place = project.aux_placement(side)
    o = project.main(side).outline
    check(f"{side} aux 폭 보존", near(place.x_max - place.x_min, 40.0),
          f"{place.x_max - place.x_min:.2f}")
    check(f"{side} aux 깊이 보존", near(place.y_max - place.y_min, 55.0),
          f"{place.y_max - place.y_min:.2f}")
    # X 는 양쪽 모두 메인 PCB 안에 들어가야 한다(안 그러면 미러 방향을 잘못 잡은 것).
    check(f"{side} aux X 가 보드 안", place.x_min >= o.x_min - TOL and place.x_max <= o.x_max + TOL,
          f"{place.x_min:.2f}..{place.x_max:.2f} (보드 {o.x_min:.2f}..{o.x_max:.2f})")
    # 헤더 열이 aux 오른쪽 가장자리에서 약 3.3mm 안쪽이라는 관계가 보존돼야 한다.
    check(f"{side} 헤더-aux 우변 관계", place.x_max > place.x_min)

# 좌측 aux 는 후면을 1.66mm 넘어선다 — 3of4 의 OuterMargin 11.5 근거.
left_place = project.aux_placement("left")
left_overhang = left_place.y_max - project.main("left").outline.y_max
check("좌 aux 후면 오버행", near(left_overhang, 1.66, 0.1), f"{left_overhang:.2f} (기대 1.66)")

if failures:
    print(f"실패 {len(failures)}건")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print(f"통과 — 보드 4장, 좌 30키 / 우 43키, 핀맵·마운팅 홀·aux 배치 확인")
