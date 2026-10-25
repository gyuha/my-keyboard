<!-- forge-slug: cradle-rail-glue-relief -->
<!-- task: 19 -->
<!-- tdd: off -->
<!-- retro-hint: optional -->
# 모듈 크래들 레일 윗면을 0.2mm 낮춰 납땜 덩어리와 글루 자리를 만든다

## 목표 / 비목표

- **목표:** 좌·우 반쪽의 RP2040-Zero [[크래들]] **레일 두 줄**의 윗면을 0.2mm 낮춘다. 모듈 바닥에 손배선 납땜 덩어리가 생겨 레일 위에 잘 앉지 않으므로, 레일과 모듈 사이에 0.2mm 틈을 만들어 덩어리를 받고 글루건으로 모듈을 고정한다.
- **모듈 높이는 유지한다(사용자 결정).** 모듈 바닥면·포트 축(`PortAxisZ -6.45`)·스위치 핀 여유 0.30mm는 그대로이고, 바닥 칩 여유(레일 1.2 − 칩 1.0 = 0.2mm)도 그대로다. 바뀌는 것은 레일 윗면 z(−9.0 → −9.2)뿐이다.
- **비목표:**
  - **USB-C 브레이크아웃 쪽 받침(0.6mm 패드) 변경** — 표시된 곳이 아니고 사용자가 모듈 레일만 지정했다.
  - **`PortAxisZ`·`BodyHeight`·모듈 위치 변경** — 모듈 높이를 유지하기로 했으므로 건드리지 않는다.
  - **`verify_port_mounts.py` 의 기존 실패 4건(항목 4~7) 수리** — 이번 작업 이전부터 실패하던 별건이다(아래 기준선 참고). 레일 높이 상수만 맞춘다.
  - **`split keyboard.3mf` 갱신** — 사용자가 직접 한다(지난 작업들과 동일).

## 원천

- **용어집:** [[크래들]], [[포트-축]] — `.forge/CONTEXT.md`
- **관련 ADR:** `.forge/adr/260824-224604-drop-aux-board-and-floor-mount-modules.md` — 크래들을 바닥에 두고 손배선하는 경위, 레일/칩 여유 설계의 원천
- **설계 결정(그릴링 합의):**
  - **범위:** 좌우 모듈 레일 모두. 레일은 `add_cradle(..., rail_width>0)` 한 곳에서 만들어지므로 파라미터 하나로 좌우에 동시에 적용된다.
  - **방식:** 레일 시트 패드의 높이만 `CradleRailRelief = 0.2` 만큼 줄인다. `stack_z()` 의 `module_seat` 는 모듈 바닥면으로 남기고, 레일 윗면만 `module_seat - CradleRailRelief` 가 된다. 끝 스토퍼(보드 윗면까지)는 그대로.
  - **안전 검사:** 기존 `rail_clear`(= 모듈 바닥면 − 바닥 − 칩 두께 > 0) 검사는 모듈 바닥면 기준이라 그대로 유효하다. 새 값 때문에 깨지는 검사는 없다.
- **기준선 (2026-10-19 실측, `FreeCAD -c freecad/verify_port_mounts.py`):** `keyboard_parametric.FCStd` 에서 모듈 시트 z == −9.0 검사는 PASS(좌우 각 1그룹, 18.60 × 24.10). 같은 스크립트의 항목 4(브레이크아웃 시트 4그룹)·5·6·7 은 **이미 FAIL** — 이번 작업과 무관한 선행 실패다. `verify_port_mounts_selftest.py` 는 PASS.
- **완료 기준 (Definition of Done).** 계획 작성 시점에 아래 ① 명령을 한 번 돌려 사전 상태를 기록했다. 헤드리스 FreeCAD 는 `/Applications/FreeCAD.app/Contents/MacOS/FreeCAD -c <스크립트>` 로 실행한다.

  **전진 검사 — 지금은 실패한다(= 작업 전 상태):**
  1. `freecad/verify_port_mounts.py` 의 모듈 시트 높이 항목이 `-9.2` 에서 PASS (좌 1·우 1 그룹, 18.60 × 24.10) → 현재는 `MODULE_SEAT_Z = -9.00` 이라 −9.2 를 기대하게 바꾸기 전엔 FAIL 이다. *(레일 윗면 −9.2 인지 ‘레일 값’을 직접 읽는 검사이며, 문자열 존재 확인이 아니다.)*
  2. 헤드리스로 `Left_Keyboard_Body`·`Right_Keyboard_Body` 의 모듈 레일 윗면 z 를 읽어 둘 다 `-9.20 ± 0.05` → 현재 −9.00 이므로 FAIL.
  3. 같은 측정에서 모듈 `ModuleSeat`(모듈 바닥면) 기준값이 `-9.00` 으로 **불변**임을 `stack_z()["module_seat"]` 로 확인.

  **회귀 가드 — 지금도 통과한다. 통과 유지가 정상이다:**
  4. `python3 freecad/verify_no_support.py` → 4파트 PASS, 순수 오버행 `0.0` *(현재 통과. 레일을 낮춰도 아래를 향하는 새 면이 생기지 않아야 한다)*
  5. `/Applications/FreeCAD.app/Contents/MacOS/FreeCAD -c freecad/verify_port_mounts_selftest.py` → `self-test passed` *(현재 통과. 검사기 자체가 깨지지 않았다는 가드)*
  6. 개구부 높이 검사(`verify_port_mounts.py` 의 `axis z == -6.45`, 좌 1·우 2 개구부)가 그대로 PASS *(현재 통과. 포트 축 불변 가드)*

## 작업 조각

- [ ] S1. `create_keyboard_parametric.py` 에 `PARAMS["CradleRailRelief"] = 0.2` 를 추가하고(`CradleRailWidth` 곁, 한두 줄 주석), `add_cradle` 의 시트 패드 길이를 `rail_width > 0` 일 때만 `seat_z - floor_z - CradleRailRelief` 로 만든다. — 완료 기준: 스크립트를 읽어 `rail_width == 0`(브레이크아웃 패드) 경로가 변하지 않았고, 레일 경로에서만 릴리프가 빠진다.
- [ ] S2. `verify_port_mounts.py` 의 `MODULE_SEAT_Z` 를 `-9.20` 으로 고치고 주석을 맞춘다(셀프테스트가 이 상수를 참조하므로 함께 따라간다). — 완료 기준: DoD 1·5 (depends: S1)
- [ ] S3. GUI 모드로 `keyboard_parametric.FCStd` 를 재생성하고(헤드리스로 돌리면 파트 색상이 사라진다 — 메모리 기록: MCP + `QTimer.singleShot` 예약, 실측 약 40초), 좌·우 `*_keyboard_body.stl` 만 다시 내보낸다. — 완료 기준: DoD 2·3·4·6 (depends: S1)
- [ ] S4. README 의 조립 스택 한 줄(`z = -9.0 모듈 크래들 좌면 …`)에 "레일 윗면은 −9.2, 모듈 바닥과 0.2mm 틈에 납땜 덩어리를 받고 글루로 고정" 취지를 보정한다. — 완료 기준: `grep -n "9.2" README.md` 가 해당 줄을 찾는다 (depends: S3)
