<!-- forge-slug: pcb-align-3of4 -->
<!-- task: 14 -->
<!-- part: 3/4 -->
<!-- tdd: off -->
# 케이스를 PCB에 정합시키고 바디 높이를 14mm로 낮춘다

## Goal / Non-goals
- Goal: `freecad/create_keyboard_parametric.py`가 PCB를 수납하는 케이스를 만들도록 고친다 — 캐비티가 PCB를 감싸고, 나사가 PCB 마운팅 홀을 관통하고, aux 보드가 들어갈 자리와 USB-C 개구부 2개가 생기고, 바디 높이가 18 → 14mm로 낮아진다.
- Non-goals: 플레이트 두께(4.0mm)와 스위치 컷아웃 형상을 바꾸지 않는다 — 스위치가 **납땜**(핫스왑 아님)이라 MX 클립 릴리프가 필요 없다. 배열·펌웨어를 건드리지 않는다(2of4). README를 고치지 않는다(4of4). TechDraw 시트(`create_techdraw_sheets.py`)는 이번 범위 밖이다. `MASTER_LEFT` 전환은 펌웨어 작업이므로 별도 task 16(`split-master-left`)이 담당한다.

## Source of truth
- Glossary terms: 메인 PCB · aux 보드 · AuxStack · 분할 링크 · 스위치 필드 · 자석 포켓 · 틸트 웨지 · 결합면 (`.forge/CONTEXT.md`)
- Related ADRs: `.forge/adr/260824-001948-case-wraps-the-pcb-not-skinned-by-it.md`(핵심), `.forge/adr/260824-003937-usb-host-is-the-left-half.md`(우측 호스트 USB-C 개구부를 내지 않는 근거), `.forge/adr/260824-001947-epro-is-the-source-of-pcb-geometry.md`, `.forge/adr/260824-001950-split-link-is-usb-c-three-wire-half-duplex.md`, `.forge/adr/260819-204944-*`(웨지 별개 부품)
- 전제: **FreeCAD GUI + MCP RPC가 켜져 있어야 한다.** `freecadcmd`로 저장하면 GuiDocument이 빠져 파트 색상이 사라진다(기존 메모).
- Definition of Done:
  1. 재생성된 외곽 XY bbox가 좌 `156.06 × 113.95`, 우 `208.45 × 113.95` (±0.05mm), 바디 높이 `14.0`.
  2. `python3 freecad/verify_no_support.py` 가 exit 0. **사전 상태: 이미 exit 0(4개 파트 PASS, tilt 5.34°) → 회귀 방지 검사.** 새 피처(PCB 안착 보스·aux 베이·USB-C 개구부 2개)가 서포트를 요구하지 않는지가 이번의 실질 관문이다.
  3. `freecadcmd freecad/verify_magnet_pockets.py` 가 exit 0이며, ⌀8 자석 기준으로 갱신된 기대값을 검사한다. **사전 상태: 이미 exit 0이지만 스크립트가 ⌀10을 하드코딩하고 있다 → 기대값 교체가 포함되므로 전진 검사.**
  4. 새 검사: 나사 4곳의 XY가 PCB 마운팅 홀 좌표와 ±0.1mm 일치하고, PCB 참조 솔리드 상면 Z가 `+4 − 5.0 = −1.0`이다.
  5. STL 8종(`freecad/parametric_stl/`)이 전부 재export된다.

## Work slices
- [ ] S1. `PARAMS` 치수 교체 — `OuterMargin` 8.0→**11.5**, `BodyHeight` 18.0→**14.0**, `MagnetDiameter` 10.0→**8.0**, `MagnetCentreHeight` 9.0→**7.0**, `PalmRestRearHeight` 25.0→**21.0**, `PalmRestFrontHeight` 12.0→**8.0**. 신규 `AuxStackHeight`=**6.1**, `PcbThickness`=1.6, `PlateToPcb`=5.0, `PcbSeatClearance`=0.3 — 완료 기준: DoD 1. 팜레스트 두 값을 함께 4mm 내려 상면 기울기(80mm에 13mm)를 보존한다.
- [ ] S2. PCB 수치를 1of4의 파서에서 읽어 오기 — `create_keyboard_parametric.py`가 `tools/pcb.py`를 import해 외곽·홀·헤더·aux bbox를 얻는다(상수 하드코딩 금지, ADR `260824-001947-epro-is-the-source-of-pcb-geometry`) — 완료 기준: 스크립트 안에 146.21/198.60/3.55 같은 리터럴이 없다(`grep`으로 확인).
- [ ] S3. 나사 데이텀 이전 — `screw_xy`를 케이스 코너 오프셋(`ScrewCornerOffset`)에서 **PCB 마운팅 홀 좌표**로 교체. 보스 상면을 PCB 하면(z=−2.6)에 두고 인서트를 그 안에 둔다 — 완료 기준: DoD 4. (depends: S1, S2)
- [ ] S4. 플레이트 하면 클램프 칼라 — 나사 4곳에 ⌀6 × 높이 1.0mm 돌기를 플레이트 하면에 padding해 z=0에서 PCB 상면(−1.0)까지 닿게 한다. 이것이 없으면 나사가 PCB를 조이지 못한다(플레이트 하면과 PCB 상면 사이가 1.0mm 떠 있음). 나사 길이는 M3×12(4+1+1.6+5) — 완료 기준: 칼라 하면 Z = −1.0 ±0.05. (depends: S3)
- [ ] S5. PCB 참조 솔리드 — PCB 외곽 라운드 사각형을 1.6mm 두께로 압출, 상면 z=−1.0. 표시 전용(색상 지정, STL export 대상 아님) — 완료 기준: DoD 4.  (depends: S2)
- [ ] S6. 구 컨트롤러 피처 제거 — `Ctrl_Seat`(바닥에 눕히는 RP2040 포켓) · `Rp2040Stop` · 현재 높이의 `Jack_Stop` · TRS 원형 홀과 관련 `PARAMS`(`Rp2040*`, `TrsJack*`, `Usb*` 중 대체되는 것) — 완료 기준: `grep -c "Ctrl_Seat\|Jack_Hole\|Rp2040Stop" freecad/create_keyboard_parametric.py` → 0.
- [ ] S7. aux 보드 베이 — 1of4 S6이 확정한 메인 PCB 좌표계 bbox에 맞춰, aux 보드의 X/Y만 잡는 얕은 가이드 리브를 캐비티 바닥에 세운다(Z는 헤더가 결정). 바닥과의 간섭이 없는지 확인 — 완료 기준: aux bbox와 캐비티 벽 사이 최소 여유 ≥ 0.5mm. (depends: S1, S2)
- [ ] S8. 후면 벽 USB-C 개구부 — **좌우 비대칭이다.** aux 보드가 좌우에서 서로 다른 위치에 앉는다는 것이 1of4에서 확정됐다(후면 오버행 좌 +1.66mm / 우 −16.30mm). 그래서 **좌측은 호스트 USB-C + 분할 링크 2개, 우측은 분할 링크 1개**만 낸다. 우측 호스트 USB-C는 뒷벽에서 16.3mm 안쪽에 갇혀 개구부를 내도 플러그가 닿지 않으므로 **개구부를 내지 않는다**(플래싱은 플레이트 조립체를 떼고 접근 — ADR `260824-003937`). 분할 링크 브레이크아웃은 손배선 3가닥이라 위치가 자유로우므로 양쪽 모두 뒷벽에 낸다. 개구부 중심 Z는 aux 보드 상면 + 모듈/브레이크아웃 두께에서 도출한다. 분할 링크 쪽은 브레이크아웃 본체를 뒤에서 받치는 스톱을 함께 세워 케이블 삽입력이 헤더로 가지 않게 한다 — 완료 기준: 좌측 벽에 개구부 2개, 우측 벽에 1개가 관통하고 DoD 2를 깨지 않는다. (depends: S7)
- [ ] S9. `verify_magnet_pockets.py` 기대값을 ⌀8로 갱신 — 완료 기준: DoD 3.  (depends: S1)
- [ ] S10. FCStd 재생성(GUI/MCP) + STL 8종 재export — 완료 기준: DoD 1·2·3·5, 파트 색상 유지. (depends: S1..S9)
