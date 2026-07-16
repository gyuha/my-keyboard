<!-- forge-slug: gkey-firmware-pcb-wiring -->
<!-- task: 7 -->
<!-- tdd: off -->
# gkey 펌웨어를 v3 PCB 스키마 배선에 맞춰 업데이트

## Goal / Non-goals

- Goal: `pcb/split-keyboard.epro` 스키마의 실제 배선(ROW/COL 넷 ↔ RP2040 GP핀, 스위치별 매트릭스 셀)과 README 키배치에 맞춰 `gkey/` QMK 펌웨어를 재구성한다. 현재 6행(88키) 이전 세대 펌웨어를 **5행(≈73키)** v3 PCB에 정합시키고, 핀·시리얼 배선을 스키마에서 도출해 정확히 설정한다.
- Non-goals:
  - 실물 보드 플래시·타이핑 테스트(이 세션엔 보드 없음). 검증은 컴파일+정합성까지.
  - 키맵 기능 추가/재설계 — 5행 매트릭스에 맞추는 것 외 새 기능 없음. 기존 FN1/FN2·WINMAC 의도 보존.
  - FreeCAD 상판/body 작업(`freecad/`) 및 PCB 자체 재설계 — 무관, 건드리지 않음.
  - via.json 키맵 레이아웃의 미관 조정 — 정합성만 맞춤.

## Source of truth

- Glossary terms: `.forge/CONTEXT.md` — 배선 원천, 키 매트릭스, ROW/COL 넷, 시리얼 배선, 가운데 B / 한영키
- Related ADRs: `.forge/adr/260716-15a-firmware-wiring-source-schematic.md`(배선 원천=스키마), `.forge/adr/0001-pcb-dxf-as-layout-source.md`(기구 배열 원천=DXF, 대조)
- 원천 파일: `pcb/split-keyboard.epro`(ZIP; `SHEET/*.esch` = Left/Right top=매트릭스, Left/Right bottom=RP2040-Zero+TRRS). 보조: `README.md` KLE(베이스 키맵), `freecad/*-pcb.dxf`(물리 좌표 교차검증).
- **확정 사실**: 5행(ROW0~ROW4)·최대 9열(COL0~COL8)·COL2ROW·2×RP2040-Zero·TRRS(TX0/RX0/3V3/GND). 좌 30키/우 ≈43키.
- **실행 중 스키마에서 확정할 것**: (a) 각 ROW/COL 넷↔GP핀 정확 매핑, (b) 스위치별 (row,col), (c) 시리얼 half(GP15) vs full-duplex(TX0/RX0) — README는 GP15라 하나 스키마 넷은 2선.
- Definition of Done: `gkey`가 5행×9열 매트릭스로 `.uf2` 컴파일 성공하고, 스위치별 배선·GP핀 배치가 스키마와 일치하며, 베이스 키맵이 README KLE와 일치하고 FN1/FN2·WINMAC이 보존되며, README 핀 표·시리얼 설명이 스키마 기준으로 정정됨.

## Work slices

- [ ] S1. **스키마 넷 추출기 + 배선 표.** `.epro`를 파싱(부품 배치 변환→절대 핀 좌표→와이어/넷라벨 연결)해 좌·우 각각: 스위치별 (ROW넷, COL넷), 각 ROW/COL/시리얼 넷↔GP핀, 시리얼 duplex 방식을 산출한다. — completion criterion: 산출 표가 자기정합(좌 5행/≤7열·우 5행/≤9열, 각 키가 정확히 ROW 1개+COL 1개에 연결, 키 수=다이오드 수, 좌우 GP핀 매핑 일관), 결과를 사람이 검토 가능한 형태로 출력.
- [ ] S2. **config.h.** (depends: S1) `MATRIX_ROWS 10`·`MATRIX_COLS 9`, `MATRIX_ROW_PINS`/`MATRIX_COL_PINS`를 S1 GP핀으로, `DIODE_DIRECTION COL2ROW`, 시리얼 정의(half=GP15 또는 full-duplex TX/RX)를 S1대로 설정. — completion criterion: 핀·행열 수·시리얼이 S1 표와 일치, 구세대 6행 흔적 없음.
- [ ] S3. **gkey.h LAYOUT.** (depends: S1) 5행 물리→매트릭스 매핑 매크로 재작성(좌 rows0–4/cols0–6, 우 rows5–9/cols0–8, 미사용 셀 KC_NO). — completion criterion: LAYOUT 인자 수=실제 키 수, 매트릭스 초기화가 S1의 키별 (row,col)과 일치.
- [ ] S4. **keymap.c.** (depends: S3) 베이스 레이어를 README KLE로 재구성(최상단=ESC·1~6, F키는 레이어), 기존 `_FN1`/`_FN2` 의도와 `WINMAC`을 새 매트릭스로 이식. — completion criterion: 3개 레이어가 LAYOUT을 채우고, 베이스가 README KLE와 일치(가운데 B·한/영 포함), FN 레이어 의도 보존, 컴파일 가능한 keycode.
- [ ] S5. **keyboard.json + via.json.** (depends: S3) keyboard.json `layout`을 실제 물리 배치로, via.json `matrix rows:10/cols:9` 및 keymap 그리드를 gkey.h와 일치시킴. — completion criterion: keyboard.json 위치가 물리 배열과 대응, via.json 셀이 gkey.h LAYOUT 매트릭스와 정확 일치.
- [ ] S6. **README 정정.** (depends: S1) 핀 표를 5행·실제 GP핀으로, 시리얼 설명을 스키마(TX0/RX0 또는 GP15 확정값)로 정정. — completion criterion: 핀 표에 6행/미검증 GP15 드리프트 없음, 스키마와 일치.
- [ ] S7. **검증.** (depends: S2,S3,S4,S5) ARM 툴체인(README 경로)으로 `qmk compile -kb gkey -km default` 성공 + 정합성 체크(각 키 (row,col) 유일·키 수 일치·LAYOUT↔keyboard.json↔via.json 일치). — completion criterion: `.uf2` 생성, 정합성 체크 전부 통과.
