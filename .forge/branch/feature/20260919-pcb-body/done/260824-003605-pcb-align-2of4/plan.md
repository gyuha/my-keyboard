<!-- forge-slug: pcb-align-2of4 -->
<!-- task: 13 -->
<!-- part: 2/4 -->
<!-- tdd: on -->
<!-- priority: high -->
# 배열에 우측 6 키를 추가하고 펌웨어를 PCB 배선에 맞춘다

## Goal / Non-goals
- Goal: 우측 최상단 행에 PCB에 실재하는 `6` 키를 추가하고(72→73키), 핀 정의·`LAYOUT` 매크로·키맵·VIA를 PCB 배선의 진실에 맞춘다.
- Non-goals: FreeCAD 형상을 재생성하지 않는다(3of4). README 본문을 고치지 않는다(4of4) — 단 `gen_keylayout.py`가 자동 갱신하는 README 인라인 KLE 블록은 예외이며 생성물이므로 손대지 않는다. 키맵의 다른 키 배정을 바꾸지 않는다.

## Source of truth
- Glossary terms: 메인 PCB · 분할 링크 (`.forge/CONTEXT.md`)
- Related ADRs: `.forge/adr/260824-001947-epro-is-the-source-of-pcb-geometry.md`, `.forge/adr/260824-001950-split-link-is-usb-c-three-wire-half-duplex.md`. 배열 원천은 ADR `260821-171944`(좌/우 KLE) · `260821-202939`(DXF는 생성물)를 그대로 따르며, **이번 변경은 그 원천 자체를 PCB에 맞춰 고치는 것**이다.
- Definition of Done:
  1. `python3 tools/verify_keylayout.py` 가 exit 0이고 출력이 `5행 73키 (좌 30 / 우 43)`, 행별이 `좌 [7, 6, 6, 6, 5] / 우 [9, 9, 8, 9, 8]` 이다. **사전 상태: 지금은 exit 0이지만 `72키 / 우 [8, 9, 8, 9, 8]`을 출력한다 → 숫자를 명시했으므로 전진 검사.**
  2. `python3 tools/verify_pcb_matrix.py` 가 **exit 0**이다. **사전 상태: 1of4가 만든 직후 exit 1(불일치 3건) → 전진 검사.**
  3. `PATH=/Applications/ArmGNUToolchain/15.2.rel1/arm-none-eabi/bin:$PATH qmk compile -kb gkey -km default` 가 exit 0이다. **사전 상태: 이미 exit 0 → 회귀 방지 검사.** (brew의 `arm-none-eabi-gcc`로는 `nosys.specs` 부재로 실패하므로 PATH 선행이 필수)
  4. `python3 tools/gen_keylayout.py && python3 tools/gen_dxf.py` 재실행 후 `git diff --stat`이 비어 있다(생성물이 재현 가능). **사전 상태: 지금도 비어 있다 → 회귀 방지 검사.**
  5. `firmware/gkey_default.uf2`가 갱신되고 빌드 산출물과 바이트 단위로 같다. **사전 상태: 현재 커밋본이 현재 소스와 같은 크기(84,480) → 소스가 바뀌면 반드시 달라지므로 전진 검사.**

## Work slices
- [ ] S1. `keylayout-right.json` row0에 `6` 키 추가 — PCB 좌표상 새 키 중심이 행의 최좌단(x=0u)이고 기존 `7`이 x=1.0u로 밀린다. 좌측 `6`과 대칭인 중복 키이므로 `{c:"#ffe08d"}`(row3의 중복 `B`, row4의 중복 `한/영`과 같은 표시 규약)를 쓴다 — 완료 기준: `kle.parse`로 읽은 우측 행별 키 수가 `[9,9,8,9,8]`.
- [ ] S2. 생성물 재생성 — `tools/gen_keylayout.py`(→ `keylayout.json`, README 인라인 블록), `tools/gen_dxf.py`(→ `freecad/left-switch.dxf`, `right-switch.dxf`) — 완료 기준: `right-switch.dxf`의 14×14 컷아웃이 43개이고 스위치 필드 X 폭이 `180.69 → 185.45mm`로 변한다. (depends: S1)
- [ ] S3. `gkey/keyboard.json` 을 73키로 — 우 row0에 `R00` 신설, 기존 `R00..R07`을 `R01..R08`로 한 칸씩 밀고 x 좌표를 재계산 — 완료 기준: `layouts.LAYOUT.layout` 길이 73. (depends: S1)
- [ ] S4. `gkey/gkey.h` `LAYOUT` 매크로 교정 — 우 row0을 `R00..R08` 9키(빈칸 없음)로, **row2의 빈칸을 C6→C7**, **row4의 빈칸을 C1→C2**로 옮긴다. 좌측 5행은 이미 PCB와 일치하므로 건드리지 않는다 — 완료 기준: DoD 2. (depends: S3)
- [ ] S5. `gkey/keymaps/default/keymap.c` 3개 레이어에 새 키 추가 — `_QWERTY`=`KC_6`, `_FN1`=`KC_F6`, `_FN2`=`KC_KP_6`(좌측 `6`과 동일). 우 row0의 나머지 키코드는 순서만 한 칸 밀린다 — 완료 기준: DoD 1·3. (depends: S4)
- [ ] S6. `gkey/via.json` 을 73키로 동기화 — 완료 기준: DoD 1(verify_keylayout이 via.json도 검사 대상에 포함한다). (depends: S3)
- [ ] S7. `gkey/config.h` 핀·시리얼 교체 — `MATRIX_ROW_PINS { GP2, GP3, GP4, GP5, GP6 }`, `MATRIX_COL_PINS { GP7 … GP15 }`, `SERIAL_USART_TX_PIN GP0`. `MATRIX_ROWS 10`/`MATRIX_COLS 9`, VID/PID `0x1209/0x0001`, `GRAVE_ESC_*_OVERRIDE`, `BOOTMAGIC_*`는 **유지**한다 — `BOOTMAGIC_ROW_RIGHT 5`/`COLUMN_RIGHT 0`은 새로 생긴 우측 `6` 자리라 오히려 정상 동작하게 된다. GP5가 더 이상 여유 핀이 아니라는 주석 정정 포함 — 완료 기준: DoD 2·3. (depends: S1)
- [ ] S8. `firmware/gkey_default.uf2` 갱신 — 완료 기준: DoD 5. (depends: S5, S7)
