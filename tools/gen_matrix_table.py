#!/usr/bin/env python3
"""PCB 배선에서 "키 ↔ ROW/COL" 표를 만들어 README 의 마커 구간에 심는다.

배선 그림(손배선 시절의 kbfirmware 출력)은 PCB 가 생긴 뒤로 틀린 정보가 됐고,
실제로 디버깅할 때 필요한 것은 어느 키가 어느 행·열에 붙어 있는지다. 그 표를
사람이 옮겨 적으면 또 어긋나므로 `pcb/split-keyboard.epro` 에서 생성한다.
근거: adr/260824-001947-epro-is-the-source-of-pcb-geometry.md

`gen_keylayout.py` 가 인라인 KLE 블록을 갱신하는 것과 같은 마커 방식이다.

실행: python3 tools/gen_matrix_table.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pcb

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
BEGIN = "<!-- BEGIN GENERATED: matrix-table -->"
END = "<!-- END GENERATED: matrix-table -->"


def table(project, side, title):
    keys = project.matrix(side)
    cols = max(k.col for k in keys) + 1
    by_rc = {(k.row, k.col): k.label for k in keys}
    lines = [f"**{title}**", ""]
    lines.append("|      | " + " | ".join(f"COL{c}" for c in range(cols)) + " |")
    lines.append("| :--: | " + " | ".join(":--:" for _ in range(cols)) + " |")
    for r in range(5):
        cells = [by_rc.get((r, c), "—") for c in range(cols)]
        lines.append(f"| ROW{r} | " + " | ".join(cells) + " |")
    return lines


def build():
    project = pcb.load()
    pins = project.pin_map("right")
    rows = ", ".join(f"ROW{i}=`{pins[f'ROW{i}']}`" for i in range(5))
    out = [
        BEGIN,
        "",
        "라벨은 PCB 실크스크린이고, `—` 는 그 자리에 스위치가 없다는 뜻입니다.",
        f"행 핀은 {rows} 이고, 열 핀은 COL0~COL8 = `GP7`~`GP15` 입니다.",
        "",
    ]
    out += table(project, "left", "좌측 (30키)")
    out.append("")
    out += table(project, "right", "우측 (43키)")
    out += ["", END]
    return "\n".join(out)


def main():
    text = README.read_text(encoding="utf-8")
    block = build()
    if BEGIN in text and END in text:
        head = text[: text.index(BEGIN)]
        tail = text[text.index(END) + len(END):]
        README.write_text(head + block + tail, encoding="utf-8")
        print("README 매트릭스 표 갱신")
    else:
        print(f"README 에 마커가 없다 — 아래 블록을 원하는 위치에 붙여라\n\n{block}")


if __name__ == "__main__":
    main()
