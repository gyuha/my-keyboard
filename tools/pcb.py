#!/usr/bin/env python3
"""pcb/split-keyboard.epro 에서 케이스·펌웨어가 쓰는 수치를 읽는다.

PCB 정합 수치(외곽·마운팅 홀·헤더)와 매트릭스 배선의 **원천은 이 epro 파일
하나**다. DXF 로 뽑아 커밋하거나 수치를 상수로 박는 대안을 버린 이유는
adr/260824-001947-epro-is-the-source-of-pcb-geometry.md 에 있다.

aux 보드는 제작하지 않는다 — 핀맵(넷 -> GPIO)의 원천으로만 존재한다.
근거: adr/260824-224604.

epro 는 zip 이고, 안의 `.epcb`/`.esym`/`.efoo` 는 한 줄에 JSON 배열 하나가 오는
포맷이다. 좌표 단위는 mil 이라 mm 로 쓸 때마다 MIL 을 곱한다.

    python3 tools/pcb.py --outline      # 외곽과 마운팅 홀
    python3 tools/pcb.py --pins         # RP2040-Zero 핀 배치
    python3 tools/pcb.py --matrix       # 키별 ROW/COL
"""
import json
import sys
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPRO = ROOT / "pcb" / "split-keyboard.epro"

MIL = 25.4 / 1000.0

# .epcb 레코드에서 쓰는 레이어 번호. 이름은 같은 파일의 LAYER 레코드에서 확인했다.
LAYER_TOP = 1
LAYER_BOTTOM = 2
LAYER_BOARD_OUTLINE = 11
LAYER_MULTI = 12

# RP2040-Zero 심볼의 핀번호 -> 핀 이름. 심볼 파일에서 읽으므로 여기 표는 없다.
RP2040_SYMBOL_TITLE = "RP2040-Zero"
SWITCH_FOOTPRINT = "cherry"
DIODE_FOOTPRINT_PREFIX = "SOD-"
HEADER_FOOTPRINT = "HDR-TH_16P-P2.54-V-M"


# ---- 자료구조 -----------------------------------------------------------------
@dataclass
class Outline:
    """보드 외곽. epro 의 R 프리미티브는 좌상단 x,y 와 폭·높이로 적힌다 —
    y 는 위로 증가하므로 적힌 y 가 y_max 다."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    radius: float

    @property
    def width(self):
        return self.x_max - self.x_min

    @property
    def height(self):
        return self.y_max - self.y_min


@dataclass
class Hole:
    x: float
    y: float
    diameter: float


@dataclass
class Component:
    designator: str
    footprint: str
    x: float
    y: float
    rotation: float
    layer: str          # "top" | "bottom"
    cid: str


@dataclass
class Key:
    row: int
    col: int
    x: float
    y: float
    label: str


@dataclass
class Board:
    name: str
    components: list = field(default_factory=list)
    outline: Outline = None
    mounting_holes: list = field(default_factory=list)
    pad_nets: dict = field(default_factory=dict)   # cid -> {pad number: net}
    _footprint_pads: dict = field(default_factory=dict)

    def by_footprint(self, name):
        return [c for c in self.components if c.footprint == name]

    @property
    def switches(self):
        return self.by_footprint(SWITCH_FOOTPRINT)

    @property
    def diodes(self):
        return [c for c in self.components if c.footprint.startswith(DIODE_FOOTPRINT_PREFIX)]

    @property
    def switches_are_soldered(self):
        """스위치가 스루홀 납땜인가(핫스왑 소켓이 아닌가).

        핫스왑이면 스위치 풋프린트에 소켓용 SMD 패드가 붙는다. 여기서는 스위치
        풋프린트의 패드가 전부 멀티레이어(=스루홀)이고 2개뿐이면 납땜으로 본다.
        4mm 플레이트에 MX 클립 릴리프가 필요한지를 이 값이 가른다."""
        pads = self._footprint_pads.get(SWITCH_FOOTPRINT, [])
        return len(pads) == 2 and all(p["layer"] == LAYER_MULTI for p in pads)

    @property
    def side(self):
        """디자이너 접두어로 좌/우를 판정한다 — 보드 이름(PCB13 등)은 뜻이 없다."""
        for c in self.components:
            upper = c.designator.upper()
            if upper.startswith("LEFT"):
                return "left"
            if upper.startswith("RIGHT"):
                return "right"
        return None

    @property
    def is_main(self):
        """스위치를 실은 쪽이 메인 PCB 다."""
        return len(self.switches) > 0


# ---- 파싱 ---------------------------------------------------------------------
def _records(text):
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except ValueError:
            continue


def _pads_of_footprint(text):
    out = []
    for r in _records(text):
        if r and r[0] == "PAD":
            out.append({"number": str(r[5]), "layer": r[4],
                        "x": r[6] * MIL, "y": r[7] * MIL})
    return out


def _symbol_pin_names(text):
    """.esym 에서 핀번호 -> 핀 이름(GP0 / 3V3 / GND ...)."""
    names, numbers = {}, {}
    for r in _records(text):
        if r and r[0] == "ATTR" and len(r) > 4:
            pin, kind, value = r[2], r[3], r[4]
            if kind == "NAME":
                names[pin] = str(value).split("/")[0].strip()
            elif kind == "NUMBER":
                numbers[pin] = str(value)
    return {numbers[pin]: names[pin] for pin in numbers if pin in names}


class Project:
    def __init__(self, path=EPRO):
        self.path = Path(path)
        with zipfile.ZipFile(self.path) as zf:
            self._raw = {n: zf.read(n).decode("utf-8", "replace") for n in zf.namelist()
                         if not n.endswith("/")}
        meta = json.loads(self._raw["project.json"])
        self._footprint_titles = {k: v.get("title") for k, v in meta.get("footprints", {}).items()}
        self._symbol_titles = {k: v.get("title") for k, v in meta.get("symbols", {}).items()}
        self.boards = {}
        for uuid, name in meta.get("pcbs", {}).items():
            key = f"PCB/{uuid}.epcb"
            if key in self._raw:
                self.boards[name] = self._parse_board(name, self._raw[key])
        self._pin_names = self._load_rp2040_pin_names()

    # -- 보드 --
    def _parse_board(self, name, text):
        board = Board(name=name)
        attrs = defaultdict(dict)
        for r in _records(text):
            if not r:
                continue
            tag = r[0]
            if tag == "COMPONENT":
                attrs[r[1]]["_place"] = (r[4] * MIL, r[5] * MIL, r[6], r[3])
            elif tag == "ATTR" and len(r) > 8 and r[7] in ("Designator", "Footprint"):
                attrs[r[3]][r[7]] = r[8]
            elif tag == "POLY" and len(r) > 6 and r[4] == LAYER_BOARD_OUTLINE:
                board.outline = self._outline_from_poly(r[6])
            elif tag == "PAD" and r[4] == LAYER_MULTI:
                board.mounting_holes.append(
                    Hole(x=r[6] * MIL, y=r[7] * MIL, diameter=r[9][1] * MIL))
            elif tag == "PAD_NET":
                board.pad_nets.setdefault(r[1], {})[str(r[2])] = r[3]
        for cid, a in attrs.items():
            if "_place" not in a:
                continue
            x, y, rot, layer = a["_place"]
            title = self._footprint_titles.get(a.get("Footprint"), a.get("Footprint") or "")
            board.components.append(Component(
                designator=a.get("Designator", ""), footprint=title or "",
                x=x, y=y, rotation=rot,
                layer="bottom" if layer == LAYER_BOTTOM else "top", cid=cid))
        for title in (SWITCH_FOOTPRINT, HEADER_FOOTPRINT):
            uuid = next((k for k, v in self._footprint_titles.items() if v == title), None)
            key = f"FOOTPRINT/{uuid}.efoo" if uuid else None
            if key and key in self._raw:
                board._footprint_pads[title] = _pads_of_footprint(self._raw[key])
        return board

    @staticmethod
    def _outline_from_poly(geom):
        """["R", x, y, w, h, ?, radius] — 적힌 y 가 위쪽 변이다."""
        if not geom or geom[0] != "R":
            raise ValueError(f"외곽이 사각형이 아니다: {geom[0] if geom else geom}")
        x, y, w, h = (geom[1] * MIL, geom[2] * MIL, geom[3] * MIL, geom[4] * MIL)
        radius = geom[6] * MIL if len(geom) > 6 else 0.0
        return Outline(x_min=x, y_min=y - h, x_max=x + w, y_max=y, radius=radius)

    def _load_rp2040_pin_names(self):
        uuid = next((k for k, v in self._symbol_titles.items() if v == RP2040_SYMBOL_TITLE), None)
        key = f"SYMBOL/{uuid}.esym" if uuid else None
        return _symbol_pin_names(self._raw[key]) if key and key in self._raw else {}

    # -- 의미 기반 접근자 --
    def _pick(self, side, main):
        for board in self.boards.values():
            if board.side == side and board.is_main == main:
                return board
        return None

    def main(self, side):
        return self._pick(side, True)

    def aux(self, side):
        return self._pick(side, False)

    # -- S3. 핀맵 --
    def pin_map(self, side):
        """넷 이름 -> RP2040-Zero 핀 이름. aux 보드의 모듈 PAD_NET 을 심볼 핀표와 조인."""
        aux = self.aux(side)
        module = next((c for c in aux.components if c.footprint == RP2040_SYMBOL_TITLE), None)
        if module is None:
            raise ValueError(f"{side} aux 보드에 RP2040-Zero 가 없다")
        out = {}
        for pad, net in aux.pad_nets.get(module.cid, {}).items():
            if not net:
                continue
            name = self._pin_names.get(pad)
            if name:
                out[net] = name
        return out

    # -- S4. 매트릭스 --
    def matrix(self, side):
        """키별 (row, col, x, y, 실크 라벨).

        스위치 한쪽 패드는 COLn 넷에 붙고, 다른 쪽은 이름 없는 로컬 넷($1N...)을
        거쳐 다이오드를 통해 ROWn 으로 간다. 그 로컬 넷으로 둘을 이어 붙인다."""
        board = self.main(side)
        local_to_row = {}
        for diode in board.diodes:
            nets = list(board.pad_nets.get(diode.cid, {}).values())
            rows = [n for n in nets if n.startswith("ROW")]
            locals_ = [n for n in nets if n.startswith("$")]
            if rows and locals_:
                local_to_row[locals_[0]] = rows[0]
        keys = []
        for sw in board.switches:
            nets = list(board.pad_nets.get(sw.cid, {}).values())
            cols = [n for n in nets if n.startswith("COL")]
            locals_ = [n for n in nets if n.startswith("$")]
            if not cols or not locals_:
                continue
            row = local_to_row.get(locals_[0])
            if row is None:
                continue
            keys.append(Key(row=int(row[3:]), col=int(cols[0][3:]),
                            x=sw.x, y=sw.y, label=sw.designator))
        return sorted(keys, key=lambda k: (k.row, k.col))


def load(path=EPRO):
    return Project(path)


# ---- CLI ----------------------------------------------------------------------
def _print_outline(p):
    for side in ("left", "right"):
        b = p.main(side)
        o = b.outline
        print(f"{side} main  {o.width:.2f} x {o.height:.2f} r{o.radius:.2f}"
              f"  (x {o.x_min:.2f}..{o.x_max:.2f}  y {o.y_min:.2f}..{o.y_max:.2f})")
        for i, h in enumerate(b.mounting_holes):
            print(f"    hole{i}  d{h.diameter:.2f}  ({h.x:.2f}, {h.y:.2f})")
        a = p.aux(side).outline
        print(f"{side} aux   {a.width:.2f} x {a.height:.2f} r{a.radius:.2f}")


def _print_pins(p):
    left, right = p.pin_map("left"), p.pin_map("right")
    nets = sorted(set(left) | set(right),
                  key=lambda n: (not n.startswith("ROW"), not n.startswith("COL"), n))
    print(f"{'net':6} {'left':6} {'right':6}")
    for n in nets:
        print(f"{n:6} {left.get(n, '—'):6} {right.get(n, '—'):6}")


def _print_matrix(p):
    for side in ("left", "right"):
        keys = p.matrix(side)
        print(f"== {side}  {len(keys)}키")
        for r in range(5):
            row = [k for k in keys if k.row == r]
            print(f"  ROW{r} ({len(row)})  " +
                  "  ".join(f"C{k.col}:{k.label}" for k in row))


if __name__ == "__main__":
    project = load()
    what = sys.argv[1] if len(sys.argv) > 1 else "--outline"
    {"--outline": _print_outline, "--pins": _print_pins,
     "--matrix": _print_matrix}[what](project)
