<!-- forge-slug: freecad-5row-regenerate-model-2of2 -->
<!-- task: 11 -->
<!-- part: 2/2 -->
<!-- tdd: off -->
<!-- priority: high -->
# 5행 DXF로 FreeCAD 모델과 출력 STL을 재생성한다 (FreeCAD GUI 필요)

## Goal / Non-goals

- Goal: 1of2가 생성한 5행 DXF로 `keyboard_parametric.FCStd`를 재생성하고, 출력용 STL 8개를 다시 내보내고, 서포트·자석 포켓 검증을 통과시킨 뒤 README를 정리해 1of2가 남긴 불일치 경고를 지운다.
- **선행 조건 (사람이 해야 함)**: FreeCAD 를 **GUI 모드**로 실행하고 MCP RPC 애드온을 켜 둔다. 착수 시점에 `get_rpc_status`가 `Connection refused`였다. 헤드리스(`--console`)로 재생성하면 파트 색상이 빠진 채 저장되므로(README 명시) GUI가 필수다. **이 조건이 갖춰지지 않으면 이 작업은 시작할 수 없다.**
- Non-goals:
  - `create_keyboard_parametric.py`의 형상 로직·`PARAMS` 값을 바꾸지 않는다. `StabCutoutYOffset`(+0.2) 같은 값은 실물 테스트로 정착한 것이므로 이번 재생성에서 건드리지 않는다.
  - 낡은 갈래(`create_keyboard_plates.py` · `keyboard_switch_plates.FCStd` · `create_techdraw_sheets.py`)를 갱신·삭제하지 않는다. 1of2가 단 주석을 그대로 둔다.
  - `image/keyboard-layout.png`(KLE 스크린샷)과 `image/wiring-left/right.png`(배선도)는 갱신하지 않는다. 전자는 웹툴 수동 작업이고, 후자는 5행 실물 배선이 확정되기 전에는 정확해질 수 없다. 낡음 주석을 유지한다.
  - `parametric_stl/split keyboard.3mf`(Bambu Studio 프로젝트)는 갱신하지 않는다 — 슬라이서가 STL을 프로젝트 안으로 복사하므로 자동 갱신이 불가능하다(README 명시). 사람이 다시 불러와야 함을 안내만 한다.
  - `stab_test_coupon` 관련 파일은 배열과 무관하므로 손대지 않는다.

## Source of truth

- Glossary terms: **키 컷아웃**, **스위치 컷아웃**, **스테빌라이저 슬롯**, **자석 포켓**, **틸트 웨지**, **결합면** — 브랜치 `CONTEXT.md` 및 최상위 `.forge/CONTEXT.md`
- Related ADRs:
  - `adr/260821-202939-kle-is-the-only-layout-source-dxf-generated.md` — 이 part 분할의 근거(FreeCAD GUI 요구가 작업 경계다)
  - 최상위 `.forge/adr/260819-204944-tilt-wedge-as-separate-glued-part.md` — 웨지를 별도 부품으로 뽑는 이유. 서포트 검증의 기준이 이 결정에서 나온다.
  - 최상위 `.forge/adr/260812-224138-stab-wire-under-plate-assembly-order.md` — 슬롯 위치를 이번에 재조정하지 않는 근거
- 재생성 절차 (README 문서화된 것을 따른다):
  1. FreeCAD GUI + MCP RPC 연결 확인 (`get_rpc_status`)
  2. `create_keyboard_parametric.py` 를 GUI 컨텍스트에서 실행 → `keyboard_parametric.FCStd` 저장
  3. README의 STL 내보내기 스니펫으로 `freecad/parametric_stl/` 에 8개 export
  4. `python3 freecad/verify_no_support.py` (FreeCAD 불필요, STL 직독)
  5. `verify_magnet_pockets.py` (FCStd 를 읽으므로 FreeCAD 필요)
- **알려진 함정**: MCP `execute_code` 는 스크린샷 때문에 출력이 잘린다. 조회·추출성 작업은 헤드리스 `freecadcmd` 로 따로 하고, GUI가 필요한 재생성만 MCP로 한다.
- Definition of Done:
  1. `keyboard_parametric.FCStd` 가 재생성되고 **8개 파트(좌/우 × 플레이트·바디·틸트웨지·팜레스트)가 모두 유효한 솔리드**다 — 스크립트가 파트별로 출력하는 `valid=True solids=1` 을 8개 전부 확인한다. 파트 색상이 살아 있는지도 확인한다(헤드리스 실행 시 빠지는 값).
  2. 플레이트의 스위치 컷아웃 수가 **좌 30 / 우 42**다. FCStd 를 읽어 세거나, 재생성 로그의 컷아웃 수로 확인한다. 착수 전에는 37 / 51이다.
  3. `freecad/parametric_stl/` 의 **8개 STL 이 모두 갱신**된다 (`stab_test_coupon` STL 은 제외 — 배열 무관). 파일 mtime 이 재생성 이후이고, 플레이트 STL 의 바운딩박스 y 치수가 구 버전보다 **약 19.05mm 줄어든다**(펑션 행 한 줄).
  4. `python3 freecad/verify_no_support.py` → **exit 0**, 즉 8개 부품 전부 서포트 없이 출력 가능. 착수 전 6행 STL 로 이 명령이 exit 0 임을 확인해 두었으므로, 실패하면 원인이 5행 형상임이 확정된다. 통과 기준(하향면 60mm² 이하)은 바꾸지 않는다 — 기준을 완화해 통과시키는 것은 검증 무력화다.
  5. `verify_magnet_pockets.py` 가 통과한다 — 좌우 반쪽마다 팜레스트 후면 1쌍 · 바디 전면벽 1쌍, 총 **4개소**가 마주 본다. 자석 개소는 배열과 무관하므로 개수는 변하지 않아야 한다.
  6. README 갱신: 1of2 가 단 불일치 경고가 제거된다 — `grep -c 'DXF 는 이미 5행' README.md` → **0** (1of2 완료 후 1). 그리고 `image/freecad-iso.png`·`image/freecad-top.png` 가 5행 모델로 재촬영된다(MCP `get_view` 로 가능). 두 이미지의 mtime 이 재생성 이후다.
  7. README 의 3mf 안내에 "형상이 5행으로 바뀌었으므로 프로젝트를 열어 8개 부품을 다시 불러와야 한다"는 한 줄이 있다.
  8. **수량 카탈로그 재확인**(회귀 가드): README 에서 배열 키 수를 뜻하는 `88`·`37`·`51` 이 새로 생기지 않는다. 부품 표의 스위치·다이오드는 이미 72로 고쳐져 있고, "출력물 8개"는 부품 종류 수이므로 배열과 무관하다.

## Work slices

- [ ] S1. FreeCAD GUI + MCP 연결을 확인하고, 재생성 전 상태를 기록한다 — 8개 STL 의 바운딩박스와 mtime, `verify_no_support.py` 기준선 — 완료 기준: `get_rpc_status` 가 정상이고, 8개 STL 의 y 치수가 기록되어 재생성 후 비교할 수 있다.
- [ ] S2. `create_keyboard_parametric.py` 를 GUI 컨텍스트에서 실행해 FCStd 를 재생성한다 — 완료 기준: DoD 1·2 가 성립한다(8개 파트 유효 솔리드, 색상 유지, 컷아웃 좌 30 / 우 42). (depends: S1)
- [ ] S3. STL 8개를 내보낸다 — 완료 기준: DoD 3 이 성립한다(8개 갱신, 플레이트 y 치수가 약 19.05mm 감소). (depends: S2)
- [ ] S4. 검증 두 개를 돌린다 — `verify_no_support.py`(exit 0)와 `verify_magnet_pockets.py`(자석 4개소). 실패하면 기준을 완화하지 말고 형상 문제로 보고한다 — 완료 기준: DoD 4·5 가 성립한다. (depends: S3)
- [ ] S5. README 를 정리한다 — 불일치 경고 제거, FreeCAD 이미지 2개 재촬영, 3mf 재불러오기 안내 추가 — 완료 기준: DoD 6·7·8 이 성립한다. (depends: S4)
