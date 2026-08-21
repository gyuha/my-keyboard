#!/usr/bin/env python3
"""좌/우 분할본에서 통합본과 README 인라인 블록을 생성한다.

배열의 원천은 keylayout-left.json / keylayout-right.json 뿐이다
(ADR 260821-171944). 통합본 keylayout.json 과 README 의 인라인 KLE 블록은
이 스크립트의 산출물이므로 손으로 편집하지 않는다.

좌/우 반쪽은 모든 행에서 8.25u 떨어져 있으므로, 통합 행의 우측 첫 키 앞
x 값은  8.25 - 좌측행폭 + 우측행 자체 x  로 정해진다.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import kle

HALF_GAP = 8.25
ROOT = Path(__file__).resolve().parent.parent
LEFT = ROOT / "keylayout-left.json"
RIGHT = ROOT / "keylayout-right.json"
MERGED = ROOT / "keylayout.json"
README = ROOT / "README.md"


def _fmt_num(value):
    """KLE 관용대로 정수는 정수로 쓴다 (2.0 -> 2)."""
    return str(int(value)) if float(value).is_integer() else str(round(value, 4))


def _fmt_attr(attrs):
    return "{" + ",".join(
        f'{k}:{_fmt_num(v) if isinstance(v, (int, float)) else chr(34) + v + chr(34)}'
        for k, v in attrs.items()
    ) + "}"


def _fmt_key(legend):
    """레전드를 KLE raw 표기로 되돌린다 (개행/따옴표/역슬래시 이스케이프)."""
    escaped = legend.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _fmt_row(row):
    return "[" + ",".join(
        _fmt_attr(item) if isinstance(item, dict) else _fmt_key(item) for item in row
    ) + "]"


def merge():
    left_rows = kle.parse(LEFT)
    right_rows = kle.parse(RIGHT)
    if len(left_rows) != len(right_rows):
        sys.exit(f"행 수 불일치: 좌 {len(left_rows)}행 / 우 {len(right_rows)}행")

    merged = []
    for left, right in zip(left_rows, right_rows):
        gap = HALF_GAP - kle.row_width(left) + kle.leading_x(right)
        right = [dict(item) if isinstance(item, dict) else item for item in right]
        if right and isinstance(right[0], dict):
            right[0]["x"] = gap                       # 자체 오프셋을 절대 간격으로 교체
        else:
            right.insert(0, {"x": gap})
        merged.append(list(left) + right)
    return merged


def write_merged(rows):
    MERGED.write_text(",\n".join(_fmt_row(r) for r in rows) + "\n", encoding="utf-8")


def write_readme():
    text = README.read_text(encoding="utf-8")
    for heading, path in (("좌측", LEFT), ("우측", RIGHT)):
        body = path.read_text(encoding="utf-8").strip()
        pattern = re.compile(
            r"(### " + heading + r"\n\n```json\n).*?(\n```)", re.DOTALL
        )
        if not pattern.search(text):
            sys.exit(f"README 에서 '### {heading}' 의 json 블록을 찾지 못했다")
        text = pattern.sub(lambda m: m.group(1) + body + m.group(2), text, count=1)
    README.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    rows = merge()
    write_merged(rows)
    write_readme()
    total = sum(len(kle.keys(r)) for r in rows)
    print(f"keylayout.json 생성: {len(rows)}행 {total}키")
    print("README 인라인 좌/우 블록 갱신")
