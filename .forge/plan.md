<!-- forge-slug: case-hug-pcb-stepped-wall -->
<!-- task: 20 -->
<!-- tdd: off -->
# 케이스 외곽을 PCB에 밀착시키고 벽을 PCB 밑으로 들어가는 계단 벽으로 바꾸기

## 목표 / 비목표
- 목표: 케이스 외곽을 키 필드 + `OuterMargin`이 아니라 **PCB 외곽(epro `pcb_rect`)**에서 유도해 케이스를 최대한 작게 만든다. 단면은 [[계단 벽]]이다. PCB 높이 구간(z −2.6~0)은 PCB + 사방 0.3mm 틈 바깥에 1.2mm 링, 그 아래는 새 외곽에서 3.0mm 벽이 PCB 밑으로 1.5mm 들어가고 그 윗면 z −2.6이 PCB 둘레를 받친다. 외곽 모서리 반경 = PCB 반경 + 0.3 + 1.2(= 4.5, 동심원). 반쪽마다 한 변당 약 3.7mm(앞 4.5mm) 줄어든다.
- 비목표:
  - `split keyboard.3mf` 슬라이서 프로젝트 갱신(사용자가 Bambu Studio에서 다시 불러온다).
  - `verify_port_mounts.py` 항목 4~7(기준선부터 FAIL, 선행 실패)을 고치는 일.
  - Z 스택(PlateThickness, PCB 높이, BodyHeight, 포트 축) 변경.
  - 펌웨어·배열 파이프라인.

## 진실의 원천
- 용어: `.forge/CONTEXT.md`의 계단 벽, 크래들, 포트 자리, 자석 포켓
- 관련 ADR: `.forge/adr/261025-182809-case-outline-from-pcb-stepped-wall.md`(이번 결정), `.forge/adr/260824-224604-drop-aux-board-and-floor-mount-modules.md`(포트·모듈 오프셋이 벽 기준인 이유. 이번 작업에서 전제가 바뀜), `260824-001947`(epro가 수치 원천)
- 그릴링 시점 실측(`compute_layout()` 계산):
  - 캐비티 벽 ↔ PCB 틈: 좌 1.93, 우 1.92, 앞 2.68, 뒤 1.92(좌·우 반쪽 동일)
  - PCB: 좌 146.21×103.35, 우 198.60×103.35, r 3.0
  - 외곽: 좌 156.06×113.95, 우 208.45×113.95
  - PCB 밑면 부품 중 가장자리에서 가장 가까운 것: 16핀 헤더(좌 안쪽 가장자리에서 6.35, 우 8.41), 다이오드 8.36 이상
- 포트·모듈 위치 결정: `SplitPortInboardOffset`·`ModuleInboardOffset`·`ModuleInboardOffsetWired`는 안쪽 벽 이동량(≈3.42, 정확한 값은 old/new 레이아웃 차이로 계산)만큼, `ModuleRearOffset`는 뒤 벽 이동량(≈3.42)만큼 줄여서 **PCB 기준 위치를 유지**한다. 뒤 벽에 붙는(rear-flush) 오른쪽 호스트 모듈만 벽을 따라 앞으로 이동한다.
- 완료 정의(DoD):
  1. `freecadcmd freecad/verify_pcb_fit.py` → exit 0. 검사 항목: 좌·우 바디 각각 (a) PCB 높이 구간(z −1.8)에서 PCB 가장자리 +0.15는 빈 공간, +0.45는 재료(네 변 모두), (b) 바디 bbox = PCB + 2×1.5(X·Y), (c) z −2.8에서 PCB 가장자리 안쪽 1.4mm 지점은 재료, z −2.4의 같은 XY는 빈 공간(턱), (d) 분할 포트 개구부 x와 좌측 유선 모듈 포켓 x/y의 PCB 기준 위치가 재생성 전 값과 ±0.05 이내, (e) 오른쪽 호스트 모듈 포켓의 XY가 PCB 밑면 부품(헤더·다이오드) 외곽과 겹치지 않음.
     - 사전 상태: 파일이 없어 실행 불가. 전방 검사이므로 지금 실패하는 게 맞다. (d)의 재생성 전 값은 fg-run이 S1 이전에 현재 FCStd에서 측정해 run.md에 기록한다.
  2. `python3 freecad/verify_no_support.py` → 4파트 PASS, "All parts print without support."
     - 사전 상태: PASS(바디 bridged 43.7/52.4). 회귀 방지 검사라 지금 통과하는 게 맞다.
  3. `freecadcmd freecad/verify_magnet_pockets.py` → 모든 항목 PASS(바디 자석 뒷면 두께 2.3 유지 포함).
     - 사전 상태: 전부 PASS. 회귀 방지 검사다.
  4. `freecadcmd freecad/verify_port_mounts.py` → 항목 1·2·3·8 PASS(4~7은 기준선과 같이 FAIL이어도 된다). `freecadcmd freecad/verify_port_mounts_selftest.py` → exit 0.
     - 사전 상태: 1·2·3·8 PASS / 4~7 FAIL, selftest exit 0. 회귀 방지 검사다.
  5. README 치수표가 새 바디 STL bbox와 일치. 사이트 탐색 명령: `git grep -n "156\.06\|208\.45\|113\.95" -- . ':!.forge'` → 0줄. 그리고 `README.md` 표의 두 값 = `parametric_stl/{left,right}_keyboard_body.stl` bbox(±0.01).
     - 사전 상태: README.md:195-196 두 줄이 걸린다. 전방 검사다.
  6. `git grep -n '"OuterMargin"\|PARAMS\["OuterMargin"\]' -- freecad` → 0줄(이 변경으로 쓰이지 않게 된 파라미터 제거).
     - 사전 상태: 2줄. 전방 검사다. 주석 속 언급(`:150`, `:670`, `verify_port_mounts.py:31`)은 내용이 틀려지면 고친다.

## 작업 조각
- [ ] S1. `create_keyboard_parametric.py`를 수정한다. ① `compute_layout()` 외곽을 `pcb_rect` ± (`PcbSeatClearance` + 새 `PcbRingThickness` 1.2)로 바꾸고 `OuterMargin`을 제거한다. ② 외곽 모서리 반경을 PCB 반경 + 0.3 + 1.2로 유도한다(플레이트·팜레스트·바디 공통). ③ 바디 캐비티를 계단으로 만든다: 기존 캐비티(외곽 − 3.0)에 더해 바디 윗면에서 PCB 밑면(z −2.6)까지 PCB + 0.3 사각(r = PCB r + 0.3) 포켓. ④ 포트·모듈 오프셋 4개를 이동량만큼 보정한다. ⑤ 주석·`print`를 정리한다. — 완료 기준: freecadcmd로 레이아웃 계산 시 좌·우 외곽 = PCB + 3.0(X·Y), 스크립트 import 에러 없음.
- [ ] S2. `freecad/verify_pcb_fit.py` 신설(기존 `verify_*.py` 관례: 헤드리스, PASS/FAIL 줄, 실패 시 exit 1). DoD 1의 (a)~(e)를 검사한다. — 완료 기준: 재생성 전 FCStd에 대해 (a)·(b)·(c)가 FAIL로 나와 검사가 실제로 동작함을 보인다. (depends: S1)
- [ ] S3. FreeCAD **GUI 모드**에서 FCStd를 재생성한다(freecadcmd로 돌리면 색상이 사라진다. MCP가 꺼져 있으면 GUI 직접 실행 + QTimer 예약 + 플래그 파일). STL 8개(좌·우 바디·플레이트·팜레스트·웨지)를 내보낸다. — 완료 기준: DoD 1~4 통과, FCStd 파트 색상 유지. (depends: S2)
- [ ] S4. README 치수표(`README.md:195-196`)를 새 bbox로 갱신하고, 스택 설명 중 벽·외곽 관련 문구가 있으면 계단 벽에 맞게 고친다. — 완료 기준: DoD 5 통과. (depends: S3)
