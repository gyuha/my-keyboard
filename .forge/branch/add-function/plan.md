<!-- forge-slug: freecad-keyboard-case -->
<!-- task: 1 -->
<!-- tdd: off -->
# DXF 스위치 레이아웃으로 3D 프린팅용 분할 키보드 풀 케이스를 FreeCAD로 설계

## Goal / Non-goals
- Goal: `freecad/left-switch.dxf`·`freecad/right-switch.dxf`를 입력으로 받아, 각 반쪽마다 **상판(1.5mm) + 케이스 바디(6° 웨지 벽체) + 하판(3mm)** 3부품을 생성하는 파라메트릭 FreeCAD Python 스크립트를 만들고, 좌·우 6개 STL을 내보낸다. 핸드와이어링 + RP2040-Zero 2개 + TRRS 구성을 담을 수 있는 내부 공간과 포트 컷아웃을 포함한다.
- Non-goals: RP2040용 QMK 펌웨어 포팅(기존 gkey는 atmega32u4), PCB 제작(`pcb/*.epro`), 팜레스트(`draw-dxf`에 별도 존재), 키캡, 열간 인서트·나사 부품 소싱(BOM), 키맵 변경. 케이스 분할(220×220 베드에 한 조각으로 들어감).

## Source of truth
- Glossary terms: 상판, 케이스 바디, 하판, 스위치 컷아웃, 컷아웃 오프셋, 웨지 틸트, 반쪽 (.forge/CONTEXT.md)
- Related ADRs: adr/0001-parametric-freecad-script.md, adr/0002-cutout-shape-with-parametric-offset.md
- 키 배치 원천: `freecad/left-switch.dxf`(외곽 148.2×129.2mm), `freecad/right-switch.dxf`(외곽 195.8×129.2mm). 두 DXF 모두 13.9mm 스위치 컷아웃 + 노치 포함.
- 확정 파라미터(스크립트 상단 변수로 노출):
  - `PLATE_T=1.5`, `WALL_T=3.0`, `BOTTOM_T=3.0` (mm)
  - `SWITCH_CUTOUT_TARGET=14.0` (mm, DXF 13.9에서 오프셋으로 확장; FDM 빡빡하면 14.1~14.15)
  - `TILT_DEG=6`, `FRONT_INT_H=12` (앞쪽 내부 여유 높이, 뒤는 실제 depth에 6° 적용해 파생)
  - 결합: M3 + 열간 인서트 (보스 OD ~7mm, 인서트 홀 Ø~4.0mm, 하판 나사 클리어런스 Ø3.4mm)
  - 컨트롤러: RP2040-Zero(≈23.5×18mm, USB-C 상단), 포켓/포스트는 뒷벽 중앙 인접
  - 포트: 각 반쪽 뒷벽에 USB-C 컷아웃(≈9.5×4mm) + TRRS(PJ-320A, Ø6mm) — 좌/우 미러
  - 출력 경로: `freecad/` (스크립트 `make_keyboard.py`, `keyboard.FCStd`, `*.stl`)
- Definition of Done: 스크립트를 FreeCAD에서 실행하면 좌·우 각 3부품(총 6 솔리드)이 오류 없이 생성되고 모두 `Shape.isValid()`, 조립 시 의도된 접촉면 외 간섭 없음, 상판 컷아웃 개구부가 목표치(~14.0mm)에 부합, 6개 STL이 `freecad/`에 내보내지며, 각 반쪽 풋프린트 ≤ 220×220mm.

## Work slices
- [ ] S1. DXF 인제스트 → 상판 평면 face: FreeCAD Python 스크립트 골격 + DXF를 읽어 외곽 경계 1개와 스위치 컷아웃 N개 와이어를 분리하고, 컷아웃을 뺀 닫힌 planar face를 좌·우 각각 생성 — 완료 기준: face 유효, bbox가 DXF와 일치(좌 148.2×129.2 / 우 195.8×129.2, ±0.2mm), 컷아웃 개수가 레이아웃 키 수와 일치, 오류 없음.
- [ ] S2. 상판 솔리드 + 컷아웃 오프셋: face를 `PLATE_T`로 압출하고, 컷아웃 와이어에 오프셋을 적용해 개구부를 `SWITCH_CUTOUT_TARGET`으로 확장(노치 유지, ADR-0002 폴백 포함) — 완료 기준: 상판 솔리드 `isValid()`, 두께 1.5mm, 표본 컷아웃 실측 ≈14.0mm, `left/right-plate.stl` 내보냄. (depends: S1)
- [ ] S3. 케이스 바디(6° 웨지 벽체 + 상단 lip + 인서트 보스): DXF 외곽선을 `WALL_T`만큼 안쪽 오프셋한 벽체를 세우고, 앞 `FRONT_INT_H`에서 뒤로 6° 상승시켜 바닥면은 평평하게, 상단에 상판 안착 단(lip), 모서리·필요 지점에 M3 열간 인서트 보스 생성 — 완료 기준: 바디 솔리드 `isValid()`, 최저면이 단일 평면(책상 접지), 상판이 lip에 안착, 보스에 인서트 홀 존재, `left/right-body.stl` 내보냄. (depends: S1)
- [ ] S4. 하판 + 포트 컷아웃 + 컨트롤러 마운트: 외곽선 기반 하판(`BOTTOM_T`)에 보스 정렬 나사 클리어런스 홀, 뒷벽에 USB-C·TRRS 컷아웃(좌/우 미러), RP2040-Zero 정렬 포스트 — 완료 기준: 하판 솔리드 `isValid()`, 3부품 조립 간섭 없음(common/section 체크), 포트 컷아웃이 올바른 높이에 위치, `left/right-bottom.stl` 내보냄. (depends: S3)
- [ ] S5. 조립·검증·내보내기: 반쪽별 3부품 조립, 지오메트리 검증(전 솔리드 유효, 의도 외 겹침 없음, 풋프린트 ≤220×220), 6개 STL을 `freecad/`에 내보내고 `keyboard.FCStd` 저장, RPC가 켜져 있으면 MCP `get_view`로 스크린샷 확인 — 완료 기준: 6개 STL 파일 생성 + 전 솔리드 유효 + 풋프린트 통과 + 시각 확인. (depends: S2, S3, S4)
