<!-- forge-slug: pcb-align-1of4 -->
<!-- task: 12 -->
<!-- part: 1/4 -->
<!-- tdd: on -->
<!-- priority: high -->
# epro 파서와 PCB 정합 검증기를 만든다

## Goal / Non-goals
- Goal: `pcb/split-keyboard.epro`에서 케이스·펌웨어가 필요한 모든 수치를 읽어내는 파서를 `tools/`에 만들고, 그 파서로 현재 `gkey/gkey.h`의 `LAYOUT` 매크로가 PCB 배선과 어긋난 지점을 지목하는 검증기를 만든다.
- Non-goals: 어긋남을 **고치지 않는다**(2of4의 일). FreeCAD 스크립트·README·`PARAMS`를 건드리지 않는다. 커밋된 `firmware/gkey_default.uf2`를 갱신하지 않는다.

## Source of truth
- Glossary terms: 메인 PCB · aux 보드 · 스위치 필드 (`.forge/CONTEXT.md`)
- Related ADRs: `.forge/adr/260824-001947-epro-is-the-source-of-pcb-geometry.md`
- Definition of Done:
  1. `python3 -m pytest tools/ -q` (또는 `python3 tools/test_pcb.py`)가 통과한다. **사전 상태: 해당 테스트 파일이 없다 → 전진 검사.**
  2. `python3 tools/pcb.py --outline` 이 좌 `146.21 x 103.35 r3.00`, 우 `198.60 x 103.35 r3.00`을 출력한다. **사전 상태: `tools/pcb.py`가 없다 → 전진 검사.**
  3. `python3 tools/verify_pcb_matrix.py` 가 **exit 1**로 종료하며 우측 row0 · row2 · row4 세 건의 불일치를 각각 한 줄로 보고한다. **사전 상태: 스크립트가 없다 → 전진 검사.** 이 파트에서 exit 1이 정상이다(버그의 증명이 산출물).
  4. `python3 tools/verify_keylayout.py` 가 여전히 exit 0이다. **사전 상태: 이미 exit 0 (`5행 72키 (좌 30 / 우 42)`) → 회귀 방지 검사.**

## Work slices
- [ ] S1. `tools/pcb.py` — epro(zip 안 줄 단위 JSON) 로더. 4개 보드를 `project.json`의 이름(`PCB2_1`=좌 메인, `PCB13`=우 메인, `PCB8_1`=좌 aux, `PCB8_2`=우 aux)으로 식별한다 — 완료 기준: 보드 4개를 이름으로 반환하고 각 보드의 컴포넌트 수가 63/90/3/3으로 나온다.
- [ ] S2. 외곽·마운팅 홀 추출 — `POLY` 중 `r[4]==11`(Board Outline Layer)의 `["R", x, y, w, h, 0, radius]`를 mil→mm(×0.0254)로 환산, layer 12 `PAD`를 홀로 수집 — 완료 기준: DoD 2의 값과, 홀 4개 ⌀3.55가 각 보드 가장자리에서 약 3.0mm 안쪽임을 테스트가 확인한다.
- [ ] S3. 핀맵 추출 — RP2040-Zero `.esym`의 핀번호→GPIO 이름 표(1=GP0 … 16=GP15, 21=3V3, 22=GND, 23=5V)와 aux 보드 `PAD_NET`을 조인 — 완료 기준: 테스트가 `ROW0..4 = GP2..GP6`, `COL0..8 = GP7..GP15`, `TX0=GP0`, `RX0=GP1`을 확인하고, 좌 aux는 COL6까지만 배선됨을 확인한다. (depends: S1)
- [ ] S4. 매트릭스 추출 — 스위치 컴포넌트(풋프린트 `cherry`)의 COL 넷과, 그 로컬 $1N 넷을 거친 다이오드(`SOD-323`)의 ROW 넷을 조인해 키별 (row, col, x, y, 실크 라벨)을 만든다 — 완료 기준: 좌 30키 · 우 43키가 나오고, 행별 키 수가 좌 `[7,6,6,6,5]` 우 `[9,9,8,9,8]`(row0→row4)로 확인된다. (depends: S1)
- [ ] S5. `tools/verify_pcb_matrix.py` — S4의 결과와 `gkey/gkey.h`의 `LAYOUT` 매크로 본문(행별 `KC_NO` 위치 포함)을 비교. `config.h`의 `MATRIX_ROW_PINS`/`MATRIX_COL_PINS`/`SERIAL_USART_TX_PIN`도 S3의 핀맵과 대조 — 완료 기준: DoD 3. 보고 형식은 `우 row2: 빈칸 C6 (PCB는 C7)` 처럼 어느 행·어느 열인지 특정한다. (depends: S3, S4)
- [ ] S6. `aux 보드` 배치 확정 — aux 외곽(40×55, R3.0)과 16핀 헤더의 mate 변환(메인은 layer 2 = 미러)을 계산해 메인 PCB 좌표계에서 aux 보드의 bbox를 낸다. X 방향 미러가 두 해석 중 어느 것인지 헤더 패드 좌표로 판정한다 — 완료 기준: 좌 기준 aux bbox가 출력되고, 후면 오버행이 `1.66mm ± 0.1`로 확인된다(3of4의 `OuterMargin` 11.5 근거). Y 방향은 이미 확정(오버행 쪽만 물리적으로 성립). (depends: S1)
