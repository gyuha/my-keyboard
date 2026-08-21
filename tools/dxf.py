"""DXF 최소 읽기/쓰기.

읽기는 create_keyboard_parametric.py 의 dxf_line_loops() 와 **동등하게** 동작해야
한다 — 생성한 DXF 를 그 스크립트가 어떻게 보는지가 유일한 관심사이므로, 루프 조립
규칙(LINE 만 읽고 끝점 연속으로 잇는다)을 그대로 따른다.
"""

TOLERANCE = 0.001


def read_loops(path):
    """LINE 엔티티를 끝점 연속 기준으로 묶어 루프 리스트를 돌려준다."""
    with open(path, encoding="ascii", errors="ignore") as source:
        lines = [line.strip() for line in source]
    pairs = [(int(lines[i]), lines[i + 1]) for i in range(0, len(lines) - 1, 2)]

    segments, entity, values = [], None, {}
    for code, value in pairs:
        if code == 0:
            if entity == "LINE" and all(k in values for k in (10, 20, 11, 21)):
                segments.append(((float(values[10]), float(values[20])),
                                 (float(values[11]), float(values[21]))))
            entity, values = value, {}
        elif entity == "LINE" and code in (10, 20, 11, 21):
            values[code] = value

    loops, current, last_end = [], [], None
    for start, end in segments:
        if last_end is not None and (abs(start[0] - last_end[0]) > TOLERANCE or
                                     abs(start[1] - last_end[1]) > TOLERANCE):
            loops.append(current)
            current = []
        if not current:
            current.append(start)
        current.append(end)
        last_end = end
    if current:
        loops.append(current)
    return loops


def write_loops(path, loops):
    """닫힌 루프들을 LINE 엔티티만 쓰는 최소 DXF 로 내보낸다.

    각 루프는 점 리스트이며, 연속한 두 점이 한 LINE 이 된다. 루프의 마지막 점은
    첫 점과 같아야 한다(닫힘) — read_loops 가 끝점 연속으로 루프를 가르므로,
    닫히지 않으면 다음 루프와 이어져 버린다.
    """
    out = ["0", "SECTION", "2", "ENTITIES"]
    for loop in loops:
        for (x0, y0), (x1, y1) in zip(loop, loop[1:]):
            out += ["0", "LINE", "8", "0",
                    "10", "%.4f" % x0, "20", "%.4f" % y0, "30", "0.0",
                    "11", "%.4f" % x1, "21", "%.4f" % y1, "31", "0.0"]
    out += ["0", "ENDSEC", "0", "EOF"]
    with open(path, "w", encoding="ascii") as sink:
        sink.write("\n".join(out) + "\n")


def bbox(loop):
    xs = [p[0] for p in loop]
    ys = [p[1] for p in loop]
    return min(xs), min(ys), max(xs), max(ys)


def centre(loop):
    x0, y0, x1, y1 = bbox(loop)
    return (x0 + x1) / 2.0, (y0 + y1) / 2.0


def size(loop):
    x0, y0, x1, y1 = bbox(loop)
    return x1 - x0, y1 - y0
