<!-- forge-slug: drop-aux-board-floor-mount-modules -->
<!-- task: 17 -->
<!-- priority: high -->
<!-- tdd: on -->
# aux 보드를 폐기하고 RP2040-Zero·USB-C 브레이크아웃을 바디 바닥 크래들에 고정한다

## 목표 / 비목표

- **목표:** aux 보드 스택을 제거하고, RP2040-Zero(18×23.5, 총 5.1mm)와 USB-C 브레이크아웃(12×15, 1.6t)을 바디 바닥의 [[크래들]]에 고정한다. 두 커넥터를 공통 [[포트-축]] z=−7.25 에 정렬하고, [[포트-자리]]를 1mm 로 박막해 플러그가 끝까지 꽂히게 한다. 케이블을 꽂았을 때 보드가 안쪽으로 밀리지 않는 것이 이 작업의 목적이다. 펌웨어를 `MASTER_RIGHT` 로 되돌리고 문서를 정합시킨다.
- **비목표:**
  - **`OuterMargin 11.5` · `BodyHeight 14.0` 축소** — 근거가 무효화됐지만 유지한다. 8개 부품 전부의 출력성 검증과 슬라이서 프로젝트를 다시 돌려야 하고, 유지 형상의 실패와 축소의 실패가 한 커밋에서 구분되지 않는다. 별도 작업.
  - **`split keyboard.3mf` 갱신** — 사용자가 직접 한다(지난 작업과 동일).
  - **`verify_no_support.py` 의 4/8 파트 커버리지 확대** — 지난 회고 F3 에 기록된 사각지대. 이번 변경은 바디에만 들어가므로 커버리지는 맞는다.
  - **`image/wiring-left.png`·`wiring-right.png` 재작성** — 매트릭스 배선(넷↔GPIO)은 바뀌지 않는다. 물리적 운반체만 바뀐 것이라 배선표는 유효하다.
  - **README 에 aux 보드의 역사적 언급을 남기지 않는다** — 경위는 ADR `260824-224604` 에 있다. 그래서 아래 DoD 의 `grep -ci 'aux' README.md → 0` 이 이 비목표와 모순되지 않는다.
  - **`fg-merge` 로 브랜치 forge 통합 + `fg-cleanup` 으로 ADR 260824-003937 은퇴** — 별도 유틸리티 실행.

## 원천

- **용어집:** [[크래들]], [[포트-자리]], [[개구부]], [[포트-축]], [[호스트-포트]], [[분할-링크-포트]] — `.forge/CONTEXT.md`
- **관련 ADR:**
  - `.forge/adr/260824-224604-drop-aux-board-and-floor-mount-modules.md` — 이 작업의 결정 근거 전체
  - `.forge/branch/feature/20260919-pcb-body/adr/260824-001947-*` — epro 가 PCB 정합 수치의 원천 (유지)
  - `.forge/branch/feature/20260919-pcb-body/adr/260824-001950-*` — 분할 링크 3선 half-duplex, 두 포트 혼동 위험 (위험 유지 재확인)
  - `.forge/branch/feature/20260919-pcb-body/adr/260824-003937-*` — **폐기됨** (MASTER_LEFT → MASTER_RIGHT)
  - `.forge/branch/feature/20260919-pcb-body/adr/260824-001948-*` — OuterMargin 11.5 (근거는 224604 로 이관, 값은 유지)

- **완료 기준 (Definition of Done).** 아래 명령은 전부 이 저장소 루트에서 그대로 실행되며, 계획 작성 시점에 한 번씩 돌려 사전 상태를 기록했다.

  **회귀 가드 — 지금도 통과한다. 통과해 있는 것이 정상이다:**
  1. `python3 tools/test_pcb.py` → 통과 *(현재 통과. S5 에서 S6 절을 삭제한 뒤에도 통과해야 한다)*
  2. `python3 tools/verify_keylayout.py` → 일치 *(현재 통과. 배열은 건드리지 않는다)*
  3. `python3 tools/verify_pcb_matrix.py` → 일치 *(현재 통과. 넷↔GPIO 는 바뀌지 않는다)*
  4. `python3 tools/test_gen_dxf.py` → 통과 *(현재 통과. DXF 생성기는 건드리지 않는다)*
  5. `FreeCAD -c freecad/verify_magnet_pockets.py` → `All checks passed` *(현재 통과. 자석 포켓은 건드리지 않는다)*
  6. `python3 freecad/verify_no_support.py` → 4파트 PASS, `support 0.0` *(현재 통과: bridged 좌 84.4 / 우 56.3, bed-tangent 29.0. 새 형상이 미지지 하향면을 만들지 않았음을 지키는 가드)*

  **전진 검사 — 지금 실패한다. 통과해야 끝난다:**
  7. `FreeCAD -c freecad/verify_port_mounts.py` → 전항목 PASS *(파일이 없어 현재 실패. S1 에서 작성)*
  8. `grep -c '^#define MASTER_RIGHT' gkey/keymaps/default/config.h` → `1` *(현재 `0`)*
  9. `grep -c '^#define MASTER_LEFT' gkey/keymaps/default/config.h` → `0` *(현재 `1`)*
  10. `grep -c 'aux_placement\|aux_connectors' tools/pcb.py freecad/create_keyboard_parametric.py` → 두 파일 모두 `0` *(현재 `pcb.py:4`, `create_keyboard_parametric.py:2`)*
  11. `grep -c 'Aux_Guide\|AuxStackHeight' freecad/create_keyboard_parametric.py` → `0` *(현재 `Aux_Guide:2`, `AuxStackHeight:4`)*
  12. `grep -ci 'aux' README.md` → `0` *(현재 `7`: 85, 88, 188, 197, 207, 208, 222행)*
  13. `grep -c 'MASTER_LEFT' README.md` → `0` *(현재 `1`, 136행)*

## 작업 슬라이스

- [ ] **S1. `freecad/verify_port_mounts.py` 를 먼저 쓴다 (TDD).** `verify_magnet_pockets.py` 와 같은 방식 — `FreeCAD -c` 로 `keyboard_parametric.FCStd` 의 형상을 직접 질의한다(STL 메시로는 포켓 내측 치수 정확도가 안 나온다). 지난 회고 교훈 6에 따라 10분짜리 GUI 재생성 밖에 두어 수 초에 끝나게 한다. 검사 항목: ① [[개구부]] 개수 우 2 / 좌 1 ② 개구부 축 z = −7.25 ± 0.05 ③ [[포트-자리]] 벽 두께 1.0 ± 0.05 ④ 브레이크아웃 [[크래들]] 내측 12.6 × 15.6 ⑤ 모듈 크래들 내측 18.6 × 24.1 ⑥ 두 크래들 사이 살 ≥ 1.5mm ⑦ 모듈 레일 상면 z = −9.80, 브레이크아웃 패드 상면 z = −10.40 ⑧ `Aux_Guide` 로 시작하는 오브젝트 부재 — **완료 기준:** `FreeCAD -c freecad/verify_port_mounts.py` 가 실행되고 위 8항목이 전부 FAIL 로 보고되며 exit code ≠ 0
- [ ] **S2. `PARAMS` 와 `stack_z()` 를 바닥 기준으로 재정의한다.** 삭제: `AuxStackHeight`·`AuxBoardThickness`·`AuxModuleThickness`·`AuxBayClearance`·`AuxGuideHeight`·`AuxGuideSize`. 추가: `PortAxisZ`, `PortWallThickness 1.0`, `ConnectorOverhang 1.0`, `ModuleWidth 18.0`·`ModuleDepth 23.5`·`ModulePcbThickness 1.0`·`ModuleUsbHeight 3.1`·`ModuleBottomChip 1.0`, `BreakoutWidth 12.0`·`BreakoutDepth 15.0`·`BreakoutThickness 1.6`, `CradleWallThickness 1.5`·`CradleClearance 0.3`·`CradleLipWidth 0.8`, `SplitPortInboardOffset`·`ModuleInboardOffset`. 좌면 높이는 `PortAxisZ` 에서 역산하고 절대값으로 박지 않는다 — **완료 기준:** `stack_z()` 가 `port_axis == -7.25`, `module_seat == -9.80`, `breakout_seat == -10.40` 을 반환하고, DoD 11 의 grep 이 `0` (depends: S1)
- [ ] **S3. `build_body()` 에서 aux 를 걷어내고 크래들·포트 자리·개구부를 세운다.** 제거: aux 가이드 포스트(§7a)와 aux 보드 참조 형상. 추가: 반쪽마다 브레이크아웃 크래들([[분할-링크-포트]] 자리), 모듈 크래들 — **우측은 뒷벽 밀착·중심 x ≈ 30.5**(옛 aux 유래 26.43 에서 +4.1: 브레이크아웃과 0.52mm 겹치므로 밀어야 한다), **좌측은 헤더(135.90, 74.22) 옆·뒷벽 비접촉**. 모듈 크래들은 바닥 칩 1mm 를 피하는 1.2mm 레일 2줄로 받친다. 포트 자리는 뒷벽 내측면을 2mm 깊이로 판 국부 패치. 개구부는 우 2([[호스트-포트]] + 분할) / 좌 1(분할) — **완료 기준:** `FreeCAD -c freecad/create_keyboard_parametric.py` 가 오류 없이 완주하고 진단 출력에 aux 가이드 포스트 줄이 사라지고 개구부 축이 −7.25 로 찍히며, DoD 10·11 의 grep 이 `0` (depends: S2)
- [ ] **S4. FreeCAD GUI(MCP)에서 재생성하고 STL 8개와 스크린샷을 내보낸다.** 헤드리스 생성은 파트 색상을 잃으므로 권위 있는 재생성은 GUI 에서 한다. `image/freecad-top.png`·`freecad-iso.png` 도 다시 찍는다 — aux 보드 참조가 사라져 기존 스크린샷이 README 서술과 어긋나기 때문 — **완료 기준:** DoD 7 전항목 PASS **그리고** DoD 6 이 4파트 PASS·`support 0.0` 유지 (depends: S3)
- [ ] **S5. `tools/pcb.py` 를 정리한다.** 삭제: `aux_placement()`, `aux_connectors()`, `_print_aux()`, `--aux` CLI, `tools/test_pcb.py` 의 S6 절(148–167행). **유지: `aux()` 와 `pin_map()`** — epro 의 aux 보드 회로도는 넷↔GPIO 의 유일한 원천이다. `pcb.py` 독스트링에 "aux 보드는 제작하지 않으며 핀맵 원천으로만 존재"를 명시한다 — **완료 기준:** DoD 10 의 `pcb.py` 항이 `0` 이고 DoD 1 이 통과 (depends: S3)
- [ ] **S6. 펌웨어를 `MASTER_RIGHT` 로 되돌린다.** `gkey/keymaps/default/config.h:30-31` 두 줄을 뒤집는다 — **완료 기준:** DoD 8 → `1`, DoD 9 → `0`, DoD 3 통과
- [ ] **S7. README 를 정합시킨다. 고칠 자리를 열거한다:** ① BOM 85행(aux 보드 ×2 삭제) ② BOM 88행(1×16 소켓/헤더 → 배선재; 좌 12+3 / 우 14+3 가닥) ③ 136행(`MASTER_LEFT` → `MASTER_RIGHT`, 근거를 ADR 224604 로 교체) ④ 148행 경고(두 USB-C 가 같은 벽에 남으므로 문구 유지, 포트 위치만 갱신) ⑤ 188행(aux 보드 참조 서술 삭제, S4 의 새 스크린샷 반영) ⑥ 197행(`BodyHeight = 7.7 + AuxStack` 근거를 바닥 고정 스택으로 교체) ⑦ 203–215행 조립 스택 블록(aux 상·하면 z 삭제, 크래들 좌면·포트 축 추가) ⑧ 218–226행 조립 순서(4번 "aux 보드를 헤더에 꽂는다" → 크래들 안착 + 손배선 납땜) ⑨ 415–417행 플래싱(우측이 호스트, 좌측은 케이스를 열어 플래시) ⑩ 「케이스 3D 출력」 절의 부품 표 — **완료 기준:** DoD 12 → `0`, DoD 13 → `0` (depends: S4, S6)

## 실행 전 전제

`S4` 는 **FreeCAD GUI 가 실행 중이고 MCP 애드온이 붙어 있어야** 한다(`freecad/keyboard_parametric.FCStd` 열린 상태). 재생성은 약 10분이며 GUI 에서 손으로 편집한 내용을 덮어쓴다 — 스크립트가 일회성 생성기이기 때문이다.
