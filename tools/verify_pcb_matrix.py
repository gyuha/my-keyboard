#!/usr/bin/env python3
"""펌웨어가 PCB 실배선과 맞는지 검사한다 — gkey.h 의 LAYOUT 매크로와 config.h 의 핀.

verify_keylayout.py 는 배열 일곱 곳의 **키 개수**를 맞추지만 `KC_NO` 빈칸이 어느
열에 있는지는 보지 않는다. 그래서 우측 세 행의 빈칸이 PCB 와 어긋난 채로 통과했다.
이 스크립트가 그 구멍을 메운다 — 비교 대상은 KLE 가 아니라 **PCB 배선**이고,
원천은 pcb/split-keyboard.epro 다.
근거: adr/260824-001947-epro-is-the-source-of-pcb-geometry.md
      adr/260824-001950-split-link-is-usb-c-three-wire-half-duplex.md

실행: python3 tools/verify_pcb_matrix.py   (일치 시 exit 0)
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pcb

ROOT = Path(__file__).resolve().parent.parent
GKEY_H = ROOT / "gkey" / "gkey.h"
CONFIG_H = ROOT / "gkey" / "config.h"

errors = []


def layout_rows(text):
    """LAYOUT 매크로 본문의 `{ ... }` 행들을 열별 점유 여부로 읽는다.

    반환: [[bool, ...], ...]  — 행 0~4 가 좌측, 5~9 가 우측(행 이중화)."""
    body = text[text.index("#define LAYOUT"):]
    rows = []
    for group in re.findall(r"\{([^{}]*)\}", body):
        cells = [c.strip().rstrip("\\").strip() for c in group.split(",")]
        cells = [c for c in cells if c]
        if not cells or not all(re.fullmatch(r"KC_NO|[LR]\d\d", c) for c in cells):
            continue
        rows.append([c != "KC_NO" for c in cells])
    return rows


def defined_list(text, name):
    m = re.search(r"#define\s+" + name + r"\s*\{([^}]*)\}", text)
    return [t.strip() for t in m.group(1).split(",") if t.strip()] if m else None


def defined_value(text, name):
    m = re.search(r"^\s*#define\s+" + name + r"\s+(\S+)", text, re.M)
    return m.group(1) if m else None


project = pcb.load()
gkey_h = GKEY_H.read_text(encoding="utf-8")
config_h = CONFIG_H.read_text(encoding="utf-8")
rows = layout_rows(gkey_h)

# ---- 1. LAYOUT 매크로의 행별 점유 열이 PCB 배선과 같은가 -----------------------
if len(rows) != 10:
    errors.append(f"LAYOUT 매크로 행 수 {len(rows)} (기대 10 — 좌 5 + 우 5)")
else:
    for side, base in (("좌", 0), ("우", 5)):
        keys = project.matrix("left" if side == "좌" else "right")
        for r in range(5):
            want = {k.col for k in keys if k.row == r}
            have = {c for c, occupied in enumerate(rows[base + r]) if occupied}
            if want == have:
                continue
            detail = []
            extra = sorted(have - want)
            if extra:
                detail.append("여분 " + ", ".join(f"C{c}" for c in extra))
            missing = sorted(want - have)
            if missing:
                detail.append("누락 " + ", ".join(f"C{c}" for c in missing))
            gap_have = sorted(set(range(len(rows[base + r]))) - have)
            gap_want = sorted(set(range(len(rows[base + r]))) - want)
            errors.append(
                f"{side} row{r}: 빈칸 {gap_have or '없음'} (PCB는 {gap_want or '없음'})"
                f" — {' / '.join(detail)}")

# ---- 2. 핀 정의가 PCB 배선과 같은가 -------------------------------------------
pins = project.pin_map("right")      # 우측이 COL0~8 전부를 쓴다
row_pins = defined_list(config_h, "MATRIX_ROW_PINS")
col_pins = defined_list(config_h, "MATRIX_COL_PINS")
tx_pin = defined_value(config_h, "SERIAL_USART_TX_PIN")

want_rows = [pins[f"ROW{i}"] for i in range(5)]
want_cols = [pins[f"COL{i}"] for i in range(9)]
if row_pins != want_rows:
    errors.append(f"MATRIX_ROW_PINS {row_pins} (PCB는 {want_rows})")
if col_pins != want_cols:
    errors.append(f"MATRIX_COL_PINS {col_pins} (PCB는 {want_cols})")
if tx_pin != pins["TX0"]:
    errors.append(f"SERIAL_USART_TX_PIN {tx_pin} (PCB는 {pins['TX0']})")

# ---- 3. full-duplex 를 쓰고 있지 않은가 ---------------------------------------
# 좌우 커넥터 배선이 동일해 스트레이트 케이블이 TX0<->TX0 을 잇는다. full-duplex 는
# 이 하드웨어에서 성립하지 않는다 — half-duplex 단선만이 유효하다.
if "SERIAL_USART_FULL_DUPLEX" in config_h:
    errors.append("SERIAL_USART_FULL_DUPLEX 가 정의돼 있다 — 이 배선에서는 동작하지 않는다")
if defined_value(config_h, "SERIAL_USART_RX_PIN"):
    errors.append("SERIAL_USART_RX_PIN 이 정의돼 있다 — half-duplex 에서는 쓰지 않는다")

if errors:
    print(f"PCB 배선과 불일치 {len(errors)}건")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("일치 확인 — LAYOUT 매크로 10행의 점유 열, 행/열 핀, 시리얼 핀이 모두 PCB 배선과 같다")
