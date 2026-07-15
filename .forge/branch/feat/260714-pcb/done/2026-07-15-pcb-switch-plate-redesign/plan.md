<!-- forge-slug: pcb-switch-plate-redesign -->
<!-- task: 5 -->
<!-- tdd: off -->
# PCB 기준 좌우 스위치 상판 재설계

## Goal / Non-goals
- Goal: `left-pcb.dxf`/`right-pcb.dxf`를 원천으로 좌·우 스위치 상판을 새 파라메트릭 스크립트로 재설계한다. 외곽 = 키 배열 +8mm/코너 5R, 스위치 컷아웃 14.0mm, 접시머리 M3 나사홀(상면 flush), 1.5mm 평판. 기존 tub 케이스 설계는 무시한다.
- Non-goals: 케이스 바디·하판·팜레스트·웨지 틸트·펌웨어·조립 검증은 이번 범위 밖. 스위치 탑 분리용 노치 미포함. TechDraw 도면 미포함. PCB DXF는 원천 입력으로 수정하지 않는다.

## Source of truth
- Glossary terms: 상판, 상판 외곽, 코너 보스, 스위치 컷아웃, 컷아웃 오프셋 — `.forge/branch/feat/260714-pcb/CONTEXT.md`
- Related ADRs: `adr/0001-pcb-dxf-as-layout-source.md`, `adr/0002-plate-outline-cutout-union-offset-fillet.md`
- Definition of Done: 좌·우 상판이 PCB 기준으로 생성되어 STL+STEP+FCStd로 export되고, (a)외곽이 컷아웃에서 8mm·코너 R5, (b)컷아웃 수=스위치 수·개구부 ~14.0mm, (c)접시머리 M3 홀이 상면 flush·컷아웃과 미충돌, (d)두께 1.5mm가 모두 수치로 측정 확인된다.

## 확정된 설계 파라미터
- 키 피치 19.05mm(1u), 컬럼 스태거드 스플릿 ergo. 좌우 비대칭 → 각 PCB에서 독립 생성(미러 아님).
- 스위치 위치: PCB Multi-Layer의 Ø4 중심홀에서 추출(실행 시 좌/우 개수·좌표 정밀 재추출·검증 — 초기 추출에 노이즈 있었음).
- 나사 위치: PCB 기존 마운팅 홀 재사용 — Ø5 코너 4개 + Ø3 중앙부 전부. 좌표는 PCB에서 추출.
- 나사: M3 접시머리(Dk=6.0, k=1.75, 90°). 상판 홀 = 관통 Ø3.4(M3 normal clearance) + **상면** Ø6.2/90° 카운터싱크(깊이 ~1.4mm).
- 두께 1.5mm 평판. 코너홀(Ø5)만 하면으로 국부 보스(+1.5mm, 총 ~3.0mm, Ø9)를 둬 카운터싱크 여유 확보. 중앙부 홀은 보스 없음(1.5mm에 csink → 잔여 ~0.1mm, 빠듯하나 사용자 승인).
- 산출물: 새 파라메트릭 스크립트(예: `freecad/create_switch_plate.py`), 기존 `create_keyboard_plates.py`와 분리. 새 FCStd 또는 새 파트. export STL+STEP.
- 재생성은 FreeCAD MCP(GUI)에서 수행(메모리: freecadcmd 재생성 시 파트 색상 손실).

## Work slices
- [ ] S1. 좌·우 PCB DXF에서 지오메트리 추출: 스위치 중심(Ø4), 코너 홀(Ø5), 중앙 마운팅 홀(Ø3) 좌표·개수 확정 — completion: 좌·우 각각 스위치 개수·홀 개수·피치(19.05)가 수치로 출력·검증됨
- [ ] S2. 상판 외곽 생성: 14mm 컷아웃 합집합 → 가장자리 8mm 각진 확장 → 볼록·오목 코너 5R 필렛 — completion: 좌·우 단일 폐곡선 외곽이 생성되고, 가장자리가 컷아웃에서 8mm·코너 반경 R5임이 확인됨 (depends: S1)
- [ ] S3. 스위치 컷아웃 배치: 각 중심에 14.0mm 정사각 컷(SWITCH_CUTOUT_TARGET 파라미터 적용) — completion: 컷아웃 개수 = 스위치 개수, 목표 개구부 ~14.0mm 측정 (depends: S1)
- [ ] S4. 나사 홀+카운터싱크+코너 보스: 재사용 홀 중심에 Ø3.4 관통 + 상면 Ø6.2/90° 카운터싱크, 코너홀 하면 국부 보스. 홀별 컷아웃 충돌 검증 — completion: 모든 재사용 홀에 관통+상면 flush 자리 생성, 컷아웃과 겹치는 홀 없음(겹치면 그 자리만 반경 축소하고 기록) (depends: S1, S2)
- [ ] S5. 1.5mm 평판 솔리드화 + export: 좌·우 상판을 STL+STEP+FCStd로 저장 — completion: `left_switch_plate`/`right_switch_plate` STL+STEP 생성, 판 두께 1.5mm 측정 확인 (depends: S2, S3, S4)
