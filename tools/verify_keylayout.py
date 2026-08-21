#!/usr/bin/env python3
"""배열 정보가 흩어져 있는 다섯 곳의 일치를 검사한다.

keyboard.json 에는 matrix 좌표가 없어 QMK 가 LAYOUT 매크로를 자동 생성하지
못하고, gkey.h 에 손으로 정의된 매크로가 쓰인다. 그래서 같은 배열이 다섯 곳에
중복 보관되며 손으로 동기화되어 왔고, 실제로 어긋난 적이 있다
(ADR 260821-171944). 이 스크립트가 그 어긋남을 빌드 전에 잡는다.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import kle

ROOT = Path(__file__).resolve().parent.parent
HALF_GAP = 8.25
MATRIX_COLS = 9

errors = []


def check(label, actual, expected):
    if actual != expected:
        errors.append(f"{label}: {actual} (기대 {expected})")


# 1. 원천 — 좌/우 분할본
left = kle.parse(ROOT / "keylayout-left.json")
right = kle.parse(ROOT / "keylayout-right.json")
check("행 수(좌)", len(left), len(right))
left_cols = [len(kle.keys(r)) for r in left]
right_cols = [len(kle.keys(r)) for r in right]
total = sum(left_cols) + sum(right_cols)
rows = len(left)

# 2. 통합본 — 분할본에서 파생됐는지 (행별 결합 간격까지)
merged = kle.parse(ROOT / "keylayout.json")
check("통합본 행 수", len(merged), rows)
check("통합본 키 수", sum(len(kle.keys(r)) for r in merged), total)
for i, (lrow, rrow, mrow) in enumerate(zip(left, right, merged)):
    want = HALF_GAP - kle.row_width(lrow) + kle.leading_x(rrow)
    # 통합 행에서 좌측 키 개수만큼 지난 직후의 속성 객체가 결합 간격을 들고 있다
    seen, gap = 0, None
    for item in mrow:
        if isinstance(item, str):
            seen += 1
        elif seen == len(kle.keys(lrow)) and "x" in item:
            gap = item["x"]
            break
    check(f"통합본 행{i} 결합 간격", gap, want)

# 3. keyboard.json
kb = json.loads((ROOT / "gkey/keyboard.json").read_text(encoding="utf-8"))
labels = [k["label"] for k in kb["layouts"]["LAYOUT"]["layout"]]
check("keyboard.json 키 수", len(labels), total)
for y, (nl, nr) in enumerate(zip(left_cols, right_cols)):
    check(f"keyboard.json 행{y} 좌", sum(1 for i in range(nl) if f"L{y}{i}" in labels), nl)
    check(f"keyboard.json 행{y} 우", sum(1 for i in range(nr) if f"R{y}{i}" in labels), nr)

# 4. gkey.h 의 LAYOUT 매크로
header = (ROOT / "gkey/gkey.h").read_text(encoding="utf-8")
args = re.search(r"#define LAYOUT\((.*?)\)\s*\\", header, re.DOTALL).group(1)
names = [a.strip() for a in args.replace("\\", "").split(",") if a.strip()]
check("gkey.h 인자 수", len(names), total)
body = header[header.index(") \\"):]
matrix = re.findall(r"\{ ((?:L|R|KC_NO)[^{}]*?) \}", body)
check("gkey.h 매트릭스 행 수", len(matrix), rows * 2)
for i, row in enumerate(matrix):
    check(f"gkey.h 매트릭스 행{i} 열 수", len(row.split(",")), MATRIX_COLS)
placed = [n for row in matrix for n in (x.strip() for x in row.split(",")) if n != "KC_NO"]
check("gkey.h 배치 수", len(placed), total)
if sorted(placed) != sorted(names):
    errors.append("gkey.h: 인자 목록과 매트릭스 배치가 불일치 (누락 또는 중복)")

# 5. keymap.c — 레이어마다 매크로 인자 수가 맞아야 한다
keymap = (ROOT / "gkey/keymaps/default/keymap.c").read_text(encoding="utf-8")
layers = re.findall(r"\[(\w+)\] = LAYOUT\((.*?)\)(?=,\n   \[|\n\};)", keymap, re.DOTALL)
check("keymap.c 레이어 수", len(layers), 3)
for name, layer_body in layers:
    count = len([a for a in layer_body.split(",") if a.strip()])
    check(f"keymap.c {name} 인자 수", count, total)

# 6. via.json
via = json.loads((ROOT / "gkey/via.json").read_text(encoding="utf-8"))
check("via.json matrix.rows", via["matrix"]["rows"], rows * 2)
via_rows = via["layouts"]["keymap"]
check("via.json 행 수", len(via_rows), rows)
check("via.json 키 수",
      sum(1 for r in via_rows for x in r if isinstance(x, str)), total)
for i, (row, nl, nr) in enumerate(zip(via_rows, left_cols, right_cols)):
    check(f"via.json 행{i} 키 수", sum(1 for x in row if isinstance(x, str)), nl + nr)

# config.h 의 매트릭스 크기도 원천과 맞아야 한다
config = (ROOT / "gkey/config.h").read_text(encoding="utf-8")
check("config.h MATRIX_ROWS",
      int(re.search(r"#define MATRIX_ROWS (\d+)", config).group(1)), rows * 2)
pins = re.search(r"#define MATRIX_ROW_PINS \{([^}]*)\}", config).group(1)
check("config.h MATRIX_ROW_PINS 개수", len(pins.split(",")), rows)

if errors:
    print(f"불일치 {len(errors)}건:")
    for e in errors:
        print("  ✗", e)
    sys.exit(1)

print(f"일치 확인 — {rows}행 {total}키 (좌 {sum(left_cols)} / 우 {sum(right_cols)})")
print(f"  행별 좌 {left_cols} / 우 {right_cols}")
print("  검사 대상: keylayout-left/right.json · keylayout.json · "
      "keyboard.json · gkey.h · keymap.c · via.json · config.h")
